# OpenAI API Wrapper

## Übersicht

Der OpenAI API Wrapper bietet eine stabile, einheitliche Schnittstelle für die Interaktion mit OpenAI-Modellen über LangChain im SWiFty-Chatbot. Er kapselt die Konfiguration und ermöglicht einfaches Debugging.

## Hauptmerkmale

- **Einheitliche Schnittstelle**: Konsistente API für alle OpenAI-Anfragen
- **Konfigurierbar**: Einfache Anpassung von Modell, Temperatur und anderen Parametern
- **Fehlerbehandlung**: Integriertes Logging und Fehlerbehandlung
- **LangChain-Integration**: Nahtlose Integration mit bestehenden LangChain-Komponenten

## Verwendung

### Basis-Verwendung

```python
from helpers.openai_wrapper import create_openai_wrapper

# Erstelle einen Wrapper mit Standardeinstellungen
wrapper = create_openai_wrapper()

# Hole das LangChain-Modell
model = wrapper.get_model()

# Verwende das Modell wie gewohnt mit LangChain
```

### Mit benutzerdefinierten Parametern

```python
from helpers.openai_wrapper import create_openai_wrapper

# Erstelle einen Wrapper mit benutzerdefinierten Einstellungen
wrapper = create_openai_wrapper(
    model="gpt-4o",
    temperature=0.7,
    streaming=True
)

model = wrapper.get_model()
```

### Konfiguration aktualisieren

```python
# Aktualisiere die Konfiguration zur Laufzeit
wrapper.update_config(
    model="gpt-4o-mini",
    temperature=0.5
)

# Hole die aktualisierte Konfiguration
config = wrapper.get_config()
print(config)
```

## API-Referenz

### `OpenAIWrapper`

Die Hauptklasse für den Wrapper.

#### `__init__(model, temperature, streaming, **kwargs)`

**Parameter:**
- `model` (str): Das zu verwendende OpenAI-Modell (Standard: "gpt-4o")
- `temperature` (float): Temperatur für die Antwortgenerierung (0.0-2.0, Standard: 0.7)
- `streaming` (bool): Ob Streaming aktiviert sein soll (Standard: True)
- `**kwargs`: Weitere Parameter für ChatOpenAI

#### `get_model() -> BaseChatModel`

Gibt das konfigurierte LangChain ChatModel zurück.

**Rückgabe:** Das konfigurierte ChatOpenAI-Modell

#### `update_config(model, temperature, streaming, **kwargs)`

Aktualisiert die Konfiguration des Wrappers.

**Parameter:**
- `model` (str, optional): Neues Modell
- `temperature` (float, optional): Neue Temperatur
- `streaming` (bool, optional): Neuer Streaming-Status
- `**kwargs`: Weitere Parameter für ChatOpenAI

#### `get_config() -> Dict[str, Any]`

Gibt die aktuelle Konfiguration als Dictionary zurück.

### `create_openai_wrapper(model, temperature, streaming, **kwargs) -> OpenAIWrapper`

Factory-Funktion zum Erstellen eines OpenAI Wrappers.

**Parameter:** Identisch mit `OpenAIWrapper.__init__`

**Rückgabe:** Konfigurierter OpenAIWrapper

## Integration im Chatbot

Im `agent_langgraph_app.py` wird der Wrapper wie folgt verwendet:

```python
from helpers.openai_wrapper import create_openai_wrapper

@cl.on_chat_start
async def on_chat_start():
    # Erstelle den Wrapper
    openai_wrapper = create_openai_wrapper(
        model="gpt-4o",
        temperature=0.7,
        streaming=True
    )
    
    # Hole das Modell für LangGraph
    model = openai_wrapper.get_model()
    
    # Verwende das Modell wie gewohnt
    agent = create_react_agent(
        model=model,
        tools=tools,
        prompt=prompt_langgraph
    )
```

## Vorteile

1. **Wartbarkeit**: Änderungen an der OpenAI-Konfiguration müssen nur an einer Stelle vorgenommen werden
2. **Debugging**: Zentrales Logging aller OpenAI-Anfragen
3. **Flexibilität**: Einfache Anpassung der Konfiguration zur Laufzeit
4. **Testbarkeit**: Der Wrapper kann leicht gemockt werden für Tests

## Erweiterte Konfiguration

Der Wrapper unterstützt alle Parameter, die von `ChatOpenAI` akzeptiert werden:

```python
wrapper = create_openai_wrapper(
    model="gpt-4o",
    temperature=0.7,
    streaming=True,
    max_tokens=2000,
    timeout=30,
    max_retries=2
)
```

## Fehlerbehandlung

Der Wrapper verwendet Python's `logging`-Modul. Um das Logging zu konfigurieren:

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('helpers.openai_wrapper')
```

Fehler bei der Initialisierung werden als Exception weitergegeben und geloggt.
