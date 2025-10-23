import chainlit as cl
from typing import Optional, List, cast

from langchain_openai import ChatOpenAI
from langchain.schema.runnable import Runnable, RunnableConfig
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

from helpers.tools import find_info_on_fhswf_website
from helpers.prompts import prompt_langgraph

# Feedback & Fallback
from helpers.feedback import save_feedback
from helpers.fallback import build_mock_reply, stream_mock_reply

# OpenAI v1: Top-Level Exceptions
from openai import OpenAIError, RateLimitError, AuthenticationError, BadRequestError


@cl.on_chat_start
async def on_chat_start():
    model = ChatOpenAI(model="gpt-4o", streaming=True)
    tools = [find_info_on_fhswf_website]
    agent = create_react_agent(model=model, tools=tools, prompt=prompt_langgraph)
    cl.user_session.set("agent_langgraph", agent)


@cl.on_message
async def main(message: cl.Message):
    agent_langgraph = cast(Runnable, cl.user_session.get("agent_langgraph"))

    langgraph_step = -1
    msg_uis: List[cl.Message] = []
    msg_ui: Optional[cl.Message] = None
    last_assistant_text_parts: List[str] = []

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

        # Feedback-Buttons an die letzte Blase hängen (falls vorhanden)
        if msg_uis:
            last = msg_uis[-1]
            assistant_text = "".join(last_assistant_text_parts).strip()
            # >>> Hier: user_input in payload aufnehmen
            last.actions = [
                cl.Action(
                    name="fb_up",
                    label="👍",
                    value="up",
                    payload={
                        "assistant_message_id": last.id,
                        "assistant_text": assistant_text,
                        "user_input": message.content or "",
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
                    },
                ),
            ]
            await last.update()

    # ---------- Fallback bei Ausfällen ----------
    except (RateLimitError, AuthenticationError, BadRequestError, OpenAIError, Exception):
        # Hinweis (optional)
        await cl.Message(
            content="Der KI-Dienst ist gerade nicht erreichbar"
        ).send()

        # Simulierte Antwort aufbauen & streamen
        mock_text = build_mock_reply(message.content or "")
        last = await stream_mock_reply(mock_text)
        
        """ # Feedback-Buttons auch an die simulierte Antwort
        if last:
            last.actions = [
                cl.Action(
                    name="fb_up",
                    label="👍",
                    value="up",
                    payload={
                        "assistant_message_id": last.id,
                        "assistant_text": mock_text,
                        "user_question": message.content or "",
                    },
                ),
                cl.Action(
                    name="fb_down",
                    label="👎",
                    value="down",
                    payload={
                        "assistant_message_id": last.id,
                        "assistant_text": mock_text,
                        "user_question": message.content or "",
                    },
                ),
            ]
            await last.update() """


# ======= Feedback-Callbacks (anonym, nur Session/Thread-ID) =======

@cl.action_callback("fb_up")
async def on_feedback_up(action: cl.Action):
    payload = action.payload or {}
    save_feedback(
        kind="up",
        assistant_message_id=payload.get("assistant_message_id"),
        assistant_text=payload.get("assistant_text") or "",
        extra={
            # optional mitgeben, falls du es auch beim Upvote speichern willst:
            "user_question": payload.get("user_input") or "",
        },
    )

    # Optional: Buttons nach Klick ausblenden (in manchen Chainlit-Versionen existiert action.parent nicht)
    try:
        if getattr(action, "parent", None):
            action.parent.actions = []
            await action.parent.update()
    except Exception:
        pass

    await cl.Message(content="Danke für dein Feedback! ✅").send()

@cl.action_callback("fb_down")
async def on_feedback_down(action: cl.Action):
    payload = action.payload or {}

    # 1) Nutzer-Eingabe abfragen (Timeout großzügig)
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

    # 3) Alles, was wir speichern wollen, kompakt in 'extra'
    extra_payload = {
        "user_question": payload.get("user_input") or "",
        "expected_text": expected,  # <- das Feld, das dir fehlt
    }

    # 4) Debug-Log: siehst du in der Server-Konsole
    try:
        cl.logger.info(f"[feedback:down] will save extra={extra_payload}")
    except Exception:
        pass

    # 5) Persistieren
    save_feedback(
        kind="down",
        assistant_message_id=payload.get("assistant_message_id"),
        assistant_text=payload.get("assistant_text") or "",
        user_expected=expected,  # direktes Feld
        extra={
            "user_question": payload.get("user_input") or "",
        },
    )

    # 6) UI: Buttons optional ausblenden (je nach Version nicht verfügbar)
    try:
        if getattr(action, "parent", None):
            action.parent.actions = []
            await action.parent.update()
    except Exception:
        pass

    cl.user_session.set("chat_closed", True)
    msg = "Danke! Wir nutzen dein Feedback zur Verbesserung. 🙏" if expected else "Danke! Feedback wurde gespeichert. 🙏"
    await cl.Message(content=f"{msg}\n\n_(Diese Unterhaltung wurde beendet. Bitte starte einen **neuen Chat**.)_").send()
