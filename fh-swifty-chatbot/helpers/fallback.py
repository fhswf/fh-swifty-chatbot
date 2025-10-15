from __future__ import annotations
import asyncio
import textwrap
from typing import List
import chainlit as cl

def build_mock_reply(user_text: str) -> str:
    user_text = (user_text or "").strip()
    prompt_hint = f"„{user_text[:120]}“" if user_text else "deine Frage"
    body = f"""
    Leider ist der KI-Dienst gerade nicht erreichbar. Ich gebe dir trotzdem eine kurze,
    vorläufige Antwort basierend auf {prompt_hint}:

    • Ich habe deine Anfrage registriert und würde normalerweise die FH-Südwestfalen-Quellen prüfen.
    • Typische nächste Schritte wären: passende Studiengangsseite finden, Fristen & Kontaktinfos extrahieren.
    • Tipp: Falls du etwas Konkretes suchst (Studiengang, Standort, Frist), schreib es gern präziser.

    Sobald der Dienst wieder läuft, kann ich dir eine ausführliche, verifizierte Antwort liefern.
    """
    return textwrap.dedent(body).strip()

def _chunk_text(s: str, size: int = 40) -> List[str]:
    out, buf, count = [], [], 0
    for word in s.split(" "):
        buf.append(word)
        count += len(word) + 1
        if count >= size:
            out.append(" ".join(buf))
            buf, count = [], 0
    if buf:
        out.append(" ".join(buf))
    return out

async def stream_mock_reply(text: str) -> cl.Message:
    msg = cl.Message(content="")
    for ch in _chunk_text(text, size=36):
        await msg.stream_token(ch + " ")
        await asyncio.sleep(0.05)
    await msg.send()
    return msg
