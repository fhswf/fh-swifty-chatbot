import chainlit as cl
from typing import Optional, List, cast
import asyncio

from langchain_openai import ChatOpenAI
from langchain_core.runnables import Runnable, RunnableConfig
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

from helpers.tools import find_info_on_fhswf_website
from helpers.prompts import prompt_langgraph

# Feedback & Fallback
from helpers.feedback import save_feedback
from helpers.fallback import build_mock_reply, stream_mock_reply

# OpenAI v1: Top-Level Exceptions
from openai import OpenAIError, RateLimitError, AuthenticationError, BadRequestError

@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="Informatikstudiengänge",
            message="Welche Informatikstudiengänge gibt es an der FH Südwestfalen? Können Sie mir Details zu den verschiedenen Programmen und deren Schwerpunkten geben?",
            icon="/public/study.svg",
        ),
        cl.Starter(
            label="Duales Studium",
            message="Wie funktioniert das duale Studium an der FH Südwestfalen? Welche Vorteile bietet es und wie läuft die Praxisphase ab?",
            icon="/public/university.svg",
        ),
        cl.Starter(
            label="KI-Recht Prüfungsanmeldung",
            message="Wann ist die Prüfungsanmeldung für KI-Recht? Wie melde ich mich an und was sind die Voraussetzungen?",
            icon="/public/schedule.svg",
        ),
        cl.Starter(
            label="Raum P107 heute",
            message="Was findet heute in Raum P107 statt? Können Sie mir den aktuellen Belegungsplan oder Stundenplan für diesen Raum zeigen?",
            icon="/public/time.svg",
        ),
        cl.Starter(
            label="Sprechstunde Herr Gawron",
            message="Wann hat Herr Gawron Sprechstunde? Wie kann ich einen Termin vereinbaren und wo findet die Sprechstunde statt?",
            icon="/public/professor.svg",
        )
    ]

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
    
    # Status message for progress indication
    status_msg: Optional[cl.Message] = None
    is_streaming_started = False
    timeout_warning_shown = False
    timeout_task = None

    async def show_timeout_warning():
        """Show warning if task takes longer than expected"""
        nonlocal timeout_warning_shown
        await asyncio.sleep(10)  # Wait 10 seconds
        if not timeout_warning_shown:
            timeout_warning_shown = True
            await cl.Message(
                content="⏳ Das dauert etwas länger als üblich, bitte habe noch einen Moment Geduld..."
            ).send()

    try:
        if agent_langgraph is None:
            raise RuntimeError("Agent nicht bereit")

        # Initial status: Thinking phase
        status_msg = cl.Message(content="🤔 Denke nach und analysiere deine Anfrage...")
        await status_msg.send()
        
        # Start timeout warning task
        timeout_task = asyncio.create_task(show_timeout_warning())

        async for msg, metadata in agent_langgraph.astream(
            {"messages": [HumanMessage(message.content or "")]},
            stream_mode="messages",
            # Transparenz-Trace im UI (falls nicht gewünscht: RunnableConfig())
            config=RunnableConfig(callbacks=[cl.LangchainCallbackHandler()]),
        ):
            node = (metadata or {}).get("langgraph_node")
            step = (metadata or {}).get("langgraph_step")
            content = (msg.content or "")

            # Update status when tools are being used
            if node == "tools" and status_msg:
                status_msg.content = "🔍 Suche nach relevanten Informationen auf der FH-Website..."
                await status_msg.update()

            # Neue UI-Blase je neuem Schritt (außer tools) mit Inhalt
            if step != langgraph_step and node != "tools" and content:
                langgraph_step = step
                
                # Update status to streaming phase when content starts
                if not is_streaming_started and status_msg:
                    status_msg.content = "✍️ Formuliere die Antwort..."
                    await status_msg.update()
                    is_streaming_started = True
                
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

        # Cancel timeout warning task
        if timeout_task:
            timeout_task.cancel()
            try:
                await timeout_task
            except asyncio.CancelledError:
                pass
        
        # Update status to finalize phase
        if status_msg:
            status_msg.content = "✅ Fertig!"
            await status_msg.update()
        
        # final senden
        for ui in msg_uis:
            await ui.send()
        
        # Remove status message after completion
        if status_msg:
            await status_msg.remove()

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
        # Cancel timeout warning task in case of error
        if timeout_task:
            timeout_task.cancel()
            try:
                await timeout_task
            except asyncio.CancelledError:
                pass
        
        # Remove status message in case of error
        if status_msg:
            try:
                await status_msg.remove()
            except Exception:
                pass
        
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
