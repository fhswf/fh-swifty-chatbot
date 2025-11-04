"""Blacklist-Überprüfungsmodul für FH Südwestfalen Chatbot."""

import os
import httpx
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import Literal, Optional
from dotenv import load_dotenv

# Umgebungsvariablen laden
load_dotenv()


class BlacklistResponse(BaseModel):
    """Pydantic-Modell für die Antwort"""
    category: Literal["valid", "not_valid", "neutral"] = Field(
        description="Kategorie der Frage"
    )
    reason: str = Field(
        description="Grund für die Klassifizierung",
        max_length=200
    )


# Client-Konfiguration mit Proxy-Unterstützung
def _initialize_client() -> OpenAI:
    """Initialisiert den OpenAI-Client mit optionaler Proxy-Konfiguration."""
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    https_proxy = os.getenv("HTTPS_PROXY")
    
    if not api_key:
        raise ValueError("OPENAI_API_KEY nicht in .env gefunden")
    
    # Proxy-Client erstellen falls konfiguriert
    http_client = httpx.Client(proxy=https_proxy) if https_proxy else None
    
    return OpenAI(
        api_key=api_key,
        base_url=base_url,
        http_client=http_client
    )


# Globaler Client
client = _initialize_client()


def _get_model_name() -> str:
    """Ermittelt das zu verwendende Modell."""
    try:
        # Verfügbare Modelle abrufen
        models = client.models.list()
        model_ids = [m.id for m in models.data]
        
        # Priorität der bevorzugten Modelle
        preferred_models = ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]
        
        for pref_model in preferred_models:
            if pref_model in model_ids:
                return pref_model
        
        # Falls kein bevorzugtes Modell gefunden, erstes verfügbares verwenden
        if model_ids:
            return model_ids[0]
    except Exception:
        pass
    
    # Fallback auf Standard-Modell
    return "gpt-4o-mini"


# Modell ermitteln
MODEL_NAME = _get_model_name()


def check_blacklist(prompt: str) -> dict:
    """
    Überprüft, ob ein Prompt für den FH Südwestfalen Chatbot geeignet ist.
    
    Args:
        prompt: Die Frage des Benutzers
        
    Returns:
        dict: {"category": "valid"|"not_valid"|"neutral", "reason": "..."}
        
    Examples:
        >>> check_blacklist("Wie kann ich mich bewerben?")
        {'category': 'valid', 'reason': 'Legitime Frage zu Bewerbungen'}
        
        >>> check_blacklist("Diese FH ist Scheiße!")
        {'category': 'not_valid', 'reason': 'Beleidigende Sprache'}
    """
    
    # System-Prompt mit Few-Shot Learning
    system_prompt = """Du bist ein Moderationssystem für den Chatbot der FH Südwestfalen (deutsche Hochschule).

**Aufgabe**: Klassifiziere Fragen in 3 Kategorien:

1. **valid**: Angemessene Fragen zur Hochschule
   - Studium, Studiengänge, Bewerbungen, Einschreibungen
   - Campus, Services, Öffnungszeiten, Bibliothek
   - Finanzierung, Stipendien, BAföG
   - Prüfungen, Noten, Praktika

2. **not_valid**: Unangemessene Fragen
   - Beleidigungen, beleidigende Sprache
   - Illegale Aktivitäten (Drogen, Betrug, Hacking)
   - Gewalt, Drohungen
   - Diskriminierung, Rassismus
   - Akademische Täuschung
   - Kommerzieller Spam

3. **neutral**: Themenfremde, aber harmlose Fragen
   - Wetter, Kochen, Sport, Unterhaltung
   - Allgemeine Fragen ohne Bezug zur Hochschule

**BEISPIELE (Few-Shot Learning)**:

Q: "Wie kann ich mich für einen Studiengang bewerben?"
R: {"category": "valid", "reason": "Legitime Frage zum Bewerbungsprozess"}

Q: "Welche Informatik-Studiengänge gibt es?"
R: {"category": "valid", "reason": "Informationsanfrage zu Studiengängen"}

Q: "Gibt es Stipendien?"
R: {"category": "valid", "reason": "Frage zur Studienfinanzierung"}

Q: "Wo ist die Mensa?"
R: {"category": "valid", "reason": "Praktische Frage zum Campus"}

Q: "Kann man an der FH Atombombenbau studieren?"
R: {"category": "not_valid", "reason": "Absurde und potenziell gefährliche Frage"}

Q: "Wo kann ich gefälschte Zeugnisse kaufen?"
R: {"category": "not_valid", "reason": "Anfrage nach illegaler Aktivität (Betrug)"}

Q: "Diese beschissene FH ist inkompetent!"
R: {"category": "not_valid", "reason": "Beleidigende und offensive Sprache"}

Q: "Ich brauche jemanden der meine Prüfung schreibt"
R: {"category": "not_valid", "reason": "Versuch akademischer Täuschung"}

Q: "Wo kann man Drogen kaufen?"
R: {"category": "not_valid", "reason": "Frage zu illegalen Substanzen"}

Q: "Wie hacke ich das Notensystem?"
R: {"category": "not_valid", "reason": "Versuch von Cyberkriminalität"}

Q: "Ausländer sollten in ihrem Land bleiben!"
R: {"category": "not_valid", "reason": "Diskriminierende und rassistische Aussagen"}

Q: "Welchen Professor kann ich bestechen?"
R: {"category": "not_valid", "reason": "Korruptionsversuch"}

Q: "Wie wird das Wetter morgen?"
R: {"category": "neutral", "reason": "Wetterfrage ohne Bezug zur Hochschule"}

Q: "Kannst du mir ein Rezept geben?"
R: {"category": "neutral", "reason": "Kulinarische Frage außerhalb des universitären Kontexts"}

Q: "Wer hat das Fußballspiel gewonnen?"
R: {"category": "neutral", "reason": "Sportfrage ohne Bezug zur FH"}

**WICHTIG**: Analysiere die Frage und antworte NUR im JSON-Format mit 'category' und 'reason'."""
    
    try:
        # Aufruf der OpenAI API mit strukturierten Outputs
        completion = client.beta.chat.completions.parse(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analysiere diese Frage:\n\n\"{prompt}\""}
            ],
            response_format=BlacklistResponse,
            temperature=0.2  # Niedrige Temperatur für Konsistenz
        )
        
        # Antwort extrahieren und zurückgeben
        result = completion.choices[0].message.parsed
        return {
            "category": result.category,
            "reason": result.reason
        }
    except Exception as e:
        # Fehlerbehandlung
        return {
            "category": "error",
            "reason": f"Fehler bei der Überprüfung: {str(e)[:100]}"
        }
