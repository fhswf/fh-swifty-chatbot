import os
import traceback
import chainlit as cl
from typing import Optional, List, cast
from uuid import uuid4

# LangChain / LangGraph
from langchain_openai import ChatOpenAI
from langchain_core.runnables import Runnable, RunnableConfig
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

# Eigene Helfer
from helpers.tools import find_info_on_fhswf_website
from helpers.prompts import prompt_langgraph

# Feedback & Fallback
#from helpers.feedback import save_feedback
from helpers.fallback import build_mock_reply, stream_mock_reply

# OpenAI v1: Top-Level Exceptions
from openai import OpenAIError, RateLimitError, AuthenticationError, BadRequestError

# LangSmith
from langsmith import Client
from langsmith.run_trees import RunTree


# ===== Helpers für Logging =====
def log_info(msg: str, extra: dict | None = None):
    try:
        cl.logger.info(msg if extra is None else f"{msg} | extra={extra}")
    except Exception:
        print(msg, extra or "")

def log_error(msg: str, err: Exception | None = None):
    try:
        if err:
            cl.logger.error(f"{msg}: {repr(err)}\n{traceback.format_exc()}")
        else:
            cl.logger.error(msg)
    except Exception:
        print(msg)
        if err:
            traceback.print_exc()


# ===== LangSmith Client einmalig anlegen =====
client = Client()

def ensure_langsmith_ready():
    """
    Versionssicherer Connectivity-Check (kein whoami, falls ältere langsmith-Version).
    """
    api_key = os.getenv("LANGSMITH_API_KEY")
    endpoint = os.getenv("LANGSMITH_ENDPOINT")
    log_info("[LangSmith] env", {"endpoint": endpoint, "has_key": bool(api_key)})

    if not api_key:
        log_error("[LangSmith] kein LANGCHAIN_API_KEY gesetzt – Runs/Feedback werden nicht gesendet.")
        return

    try:
        # harmloser Ping, funktioniert quer über Versionen
        _ = list(client.list_projects(limit=1))
        log_info("[LangSmith] connectivity OK")
    except Exception as e:
        log_error("[LangSmith] connectivity FAILED (prüfe API-Key/Endpoint/Firewall)", e)


@cl.set_starters
async def set_starters():
    import json, os

    path = os.getenv("STARTERS_OUT", "starters.json")
    items = []
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                items = data.get("items", [])
    except Exception as e:
        try:
            cl.logger.warning(f"[Starters] Konnte {path} nicht laden: {e}")
        except Exception:
            pass

    # Fallback, wenn nichts geladen wurde
    if not items:
        items = [
            {
                "label":"Informatikstudiengänge",
                "message":"Welche Informatikstudiengänge gibt es an der FH Südwestfalen? Können Sie mir Details zu den verschiedenen Programmen und deren Schwerpunkten geben?",
                "icon":"/public/study.svg",
            },
            {
                "label":"Duales Studium",
                "message":"Wie funktioniert das duale Studium an der FH Südwestfalen? Welche Vorteile bietet es und wie läuft die Praxisphase ab?",
                "icon":"/public/university.svg",
            },
            {
                "label":"KI-Recht Prüfungsanmeldung",
                "message":"Wann ist die Prüfungsanmeldung für KI-Recht? Wie melde ich mich an und was sind die Voraussetzungen?",
                "icon":"/public/schedule.svg",
            },
            {
                "label":"Raum P107 heute",
                "message":"Was findet heute in Raum P107 statt? Können Sie mir den aktuellen Belegungsplan oder Stundenplan für diesen Raum zeigen?",
                "icon":"/public/time.svg",
            },
            {
                "label":"Sprechstunde Herr Gawron",
                "message":"Wann hat Herr Gawron Sprechstunde? Wie kann ich einen Termin vereinbaren und wo findet die Sprechstunde statt?",
                "icon":"/public/professor.svg",
            },
        ]

    # Auf Chainlit-Objekte mappen
    starters = [
        cl.Starter(label=i["label"], message=i["message"], icon=i.get("icon"))
        for i in items
    ]
    return starters



@cl.on_chat_start
async def on_chat_start():
    ensure_langsmith_ready()

    model = ChatOpenAI(model="gpt-4o", streaming=True)
    tools = [find_info_on_fhswf_website]
    agent = create_react_agent(model=model, tools=tools, prompt=prompt_langgraph)
    cl.user_session.set("agent_langgraph", agent)
    log_info("[Chat] Agent initialisiert")


@cl.on_message
async def main(message: cl.Message):
    agent_langgraph = cast(Runnable, cl.user_session.get("agent_langgraph"))

    langgraph_step = -1
    msg_uis: List[cl.Message] = []
    msg_ui: Optional[cl.Message] = None
    last_assistant_text_parts: List[str] = []

    # ===== Root-Run für diesen Turn in LangSmith anlegen =====
    root = RunTree(
        name="chat_turn",
        run_type="chain",
        project_name=os.getenv("LANGSMITH_PROJECT"),
        id=str(uuid4()),  # explizit String-ID erzeugen
        inputs={"user_message": message.content or ""},
        metadata={"source": "chainlit", "langgraph": True},
    )
    run_id_str = str(root.id)  # immer als STRING weitergeben
    log_info("[LangSmith] Root created", {"run_id": run_id_str})

    try:
        if agent_langgraph is None:
            raise RuntimeError("Agent nicht bereit")

        async for msg, metadata in agent_langgraph.astream(
            {"messages": [HumanMessage(message.content or "")]},
            stream_mode="messages",
            # Transparenz-Trace im UI (falls nicht gewünscht: RunnableConfig())
            config=RunnableConfig(callbacks=[cl.LangchainCallbackHandler()]),
        ):
            node = (metadata or {}).get("langgraph_node")
            step = (metadata or {}).get("langgraph_step")
            content = (msg.content or "")

            # Neue UI-Blase je neuem Schritt (außer tools) mit Inhalt
            if step != langgraph_step and node != "tools" and content:
                langgraph_step = step
                msg_ui = cl.Message(content="")
                msg_uis.append(msg_ui)
                last_assistant_text_parts = []

            # Nur nicht-Tool-Inhalte streamen
            if content and node != "tools":
                if msg_ui is None:
                    msg_ui = cl.Message(content="")
                    msg_uis.append(msg_ui)
                await msg_ui.stream_token(content)
                last_assistant_text_parts.append(content)

        # final senden
        for ui in msg_uis:
            await ui.send()

        # ===== Root-Run abschließen & posten =====
        full_answer = "".join(last_assistant_text_parts).strip()
        try:
            root.end(outputs={"assistant_text": full_answer})
            root.post()
            log_info("[LangSmith] Root posted", {"run_id": run_id_str, "answer_len": len(full_answer)})
        except Exception as e:
            log_error("[LangSmith] root.post FAILED", e)

        # run_id für spätere Feedback-Calls bereitstellen (STRING!)
        cl.user_session.set("last_run_id", run_id_str)

        if msg_uis:
            last = msg_uis[-1]
            assistant_text = full_answer
            last.actions = [
                cl.Action(
                    name="fb_up",
                    label="👍",
                    value="up",
                    payload={
                        "assistant_message_id": last.id,
                        "assistant_text": assistant_text,
                        "user_input": message.content or "",
                        "run_id": run_id_str,
                    },
                ),
                cl.Action(
                    name="fb_down",
                    label="👎",
                    value="down",
                    payload={
                        "assistant_message_id": last.id,
                        "assistant_text": assistant_text,
                        "user_input": message.content or "",
                        "run_id": run_id_str,
                    },
                ),
            ]
            await last.update()

    # ---------- Fallback bei Ausfällen ----------
    except (RateLimitError, AuthenticationError, BadRequestError, OpenAIError, Exception) as e:
        log_error("[Chat] Exception im Turn", e)

        await cl.Message(content="Der KI-Dienst ist gerade nicht erreichbar").send()

        # Simulierte Antwort aufbauen & streamen
        mock_text = build_mock_reply(message.content or "")
        last = await stream_mock_reply(mock_text)

        # Auch den Root-Run sauber beenden & posten (als Fallback markiert)
        try:
            root.end(outputs={"assistant_text": mock_text}, error=False, metadata={"fallback": True})
            root.post()
            log_info("[LangSmith] Root posted (fallback)", {"run_id": run_id_str})
        except Exception as e2:
            log_error("[LangSmith] root.post FAILED (fallback)", e2)

        


# ======= Feedback-Callbacks =======

@cl.action_callback("fb_up")
async def on_feedback_up(action: cl.Action):
    payload = action.payload or {}
    run_id = payload.get("run_id")

    # LangSmith-Feedback (👍)
    if run_id:
        try:
            fb = client.create_feedback(
                run_id=run_id,           # STRING OK
                key="thumbs",
                score=1,                 # upvote
                source_info={"user_question": payload.get("user_input") or ""},
            )
            log_info("[LangSmith] feedback OK (up)", {"run_id": run_id, "feedback_id": getattr(fb, "id", None)})
        except Exception as e:
            log_error("[LangSmith] feedback FAILED (up)", e)
    else:
        log_error("[LangSmith] feedback skipped: missing run_id")

    # Buttons ausblenden
    try:
        if getattr(action, "parent", None):
            action.parent.actions = []
            await action.parent.update()
    except Exception:
        pass

    await cl.Message(content="Danke für dein Feedback!").send()


@cl.action_callback("fb_down")
async def on_feedback_down(action: cl.Action):
    payload = action.payload or {}
    run_id = payload.get("run_id")

    # 1) Nutzer-Eingabe abfragen
    ask = cl.AskUserMessage(
        content="Was hättest du als Antwort erwartet? (optional mit Links/Beispielen)",
        timeout=60,
    )
    res = await ask.send()

    # 2) Robust extrahieren (dict | str | None)
    expected = ""
    if isinstance(res, dict):
        expected = (res.get("output") or "").strip()
    elif isinstance(res, str):
        expected = res.strip()

    # 3) LangSmith-Feedback (👎)
    if run_id:
        try:
            fb = client.create_feedback(
                run_id=run_id,          # STRING OK
                key="thumbs",
                score=0,                 # downvote
                comment=expected or None,
                source_info={"user_question": payload.get("user_input") or ""},
            )
            log_info("[LangSmith] feedback OK (down)", {"run_id": run_id, "feedback_id": getattr(fb, "id", None)})
        except Exception as e:
            log_error("[LangSmith] feedback FAILED (down)", e)
    else:
        log_error("[LangSmith] feedback skipped: missing run_id")


    # 4) Buttons ausblenden
    try:
        if getattr(action, "parent", None):
            action.parent.actions = []
            await action.parent.update()
    except Exception:
        pass

    cl.user_session.set("chat_closed", True)
    msg = "Danke! Wir nutzen dein Feedback zur Verbesserung." if expected else "Danke! Feedback wurde gespeichert."
    await cl.Message(
        content=f"{msg}\n\n_(Diese Unterhaltung wurde beendet. Bitte starte einen **neuen Chat**.)_"
    ).send()
