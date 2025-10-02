# Quick Start - OpenAI Wrapper

## Schnellstart für Entwickler

### 1. Basis-Verwendung

```python
from helpers.openai_wrapper import create_openai_wrapper

# Erstelle den Wrapper
wrapper = create_openai_wrapper()

# Hole das Modell
model = wrapper.get_model()

# Verwende das Modell mit LangChain/LangGraph
```

### 2. Mit eigenen Parametern

```python
from helpers.openai_wrapper import create_openai_wrapper

wrapper = create_openai_wrapper(
    model="gpt-4o",           # Modellwahl
    temperature=0.7,          # Kreativität (0.0 - 2.0)
    streaming=True,           # Streaming aktivieren
    max_tokens=2000,          # Maximale Token-Anzahl
    timeout=30                # Request-Timeout in Sekunden
)

model = wrapper.get_model()
```

### 3. Integration in Chainlit App

```python
import chainlit as cl
from helpers.openai_wrapper import create_openai_wrapper
from langgraph.prebuilt import create_react_agent

@cl.on_chat_start
async def on_chat_start():
    # Wrapper erstellen
    wrapper = create_openai_wrapper(
        model="gpt-4o",
        temperature=0.7,
        streaming=True
    )
    
    # Modell holen und Agent erstellen
    model = wrapper.get_model()
    agent = create_react_agent(
        model=model,
        tools=[...],
        prompt=prompt
    )
    
    # In Session speichern
    cl.user_session.set("agent", agent)
    cl.user_session.set("wrapper", wrapper)
```

### 4. Konfiguration zur Laufzeit ändern

```python
# Wrapper aus Session holen
wrapper = cl.user_session.get("wrapper")

# Konfiguration ändern
wrapper.update_config(
    temperature=0.5,
    max_tokens=1000
)

# Neue Konfiguration anzeigen
print(wrapper.get_config())
```

### 5. Verschiedene Modelle verwenden

```python
# GPT-4o (Standard)
wrapper_4o = create_openai_wrapper(model="gpt-4o")

# GPT-4o-mini (schneller, günstiger)
wrapper_4o_mini = create_openai_wrapper(model="gpt-4o-mini")

# Mit eigenen Einstellungen
wrapper_custom = create_openai_wrapper(
    model="gpt-4o-mini",
    temperature=0.3,          # Weniger kreativ
    streaming=False,          # Kein Streaming
    max_tokens=500            # Kürzere Antworten
)
```

## Verfügbare Parameter

| Parameter | Typ | Standard | Beschreibung |
|-----------|-----|----------|--------------|
| `model` | str | "gpt-4o" | OpenAI Modell-Name |
| `temperature` | float | 0.7 | Kreativität (0.0-2.0) |
| `streaming` | bool | True | Streaming aktivieren |
| `max_tokens` | int | None | Max. Token in Antwort |
| `timeout` | int | None | Request-Timeout (Sek.) |
| `max_retries` | int | 2 | Anzahl Wiederholungen |
| `request_timeout` | int | None | Timeout pro Request |

## Methoden

### `get_model()`
Gibt das konfigurierte LangChain ChatModel zurück.

```python
model = wrapper.get_model()
```

### `update_config(**kwargs)`
Aktualisiert die Konfiguration zur Laufzeit.

```python
wrapper.update_config(
    model="gpt-4o-mini",
    temperature=0.5
)
```

### `get_config()`
Gibt die aktuelle Konfiguration als Dictionary zurück.

```python
config = wrapper.get_config()
print(f"Modell: {config['model']}")
print(f"Temperature: {config['temperature']}")
```

## Debugging

### Logging aktivieren

```python
import logging

# Logging konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('helpers.openai_wrapper')

# Wrapper erstellen (loggt automatisch)
wrapper = create_openai_wrapper(model="gpt-4o")
```

### Konfiguration prüfen

```python
# Aktuelle Einstellungen anzeigen
print(wrapper)  # Kurze Übersicht
print(wrapper.get_config())  # Vollständige Konfiguration
```

## Häufige Anwendungsfälle

### 1. Konsistente Antworten
```python
wrapper = create_openai_wrapper(temperature=0.0)
```

### 2. Kreative Antworten
```python
wrapper = create_openai_wrapper(temperature=1.5)
```

### 3. Schnelle Antworten
```python
wrapper = create_openai_wrapper(
    model="gpt-4o-mini",
    max_tokens=500
)
```

### 4. Lange Antworten
```python
wrapper = create_openai_wrapper(max_tokens=4000)
```

### 5. Ohne Streaming (für Tests)
```python
wrapper = create_openai_wrapper(streaming=False)
```

## Fehlerbehandlung

```python
try:
    wrapper = create_openai_wrapper(
        model="gpt-4o",
        temperature=0.7
    )
    model = wrapper.get_model()
except Exception as e:
    print(f"Fehler beim Erstellen des Wrappers: {e}")
    # Fallback oder Fehlerbehandlung
```

## Best Practices

1. **Wrapper in Session speichern**
   ```python
   cl.user_session.set("wrapper", wrapper)
   ```

2. **Konfiguration dokumentieren**
   ```python
   # Nutze klare Parameter-Namen
   wrapper = create_openai_wrapper(
       model="gpt-4o",        # Production-Modell
       temperature=0.7,       # Balanced
       streaming=True         # UI-Responsiveness
   )
   ```

3. **Logging nutzen**
   ```python
   # Aktiviere Logging für Debugging
   import logging
   logging.basicConfig(level=logging.INFO)
   ```

4. **Fehler behandeln**
   ```python
   try:
       wrapper = create_openai_wrapper()
       model = wrapper.get_model()
   except Exception as e:
       logger.error(f"Fehler: {e}")
       # Fallback
   ```

## Weitere Ressourcen

- **Vollständige Dokumentation**: `fh-swifty-chatbot/helpers/OPENAI_WRAPPER.md`
- **Beispiele**: `fh-swifty-chatbot/helpers/openai_wrapper_examples.py`
- **Architektur**: `ARCHITECTURE.md`
- **Implementation**: `IMPLEMENTATION_SUMMARY.md`

## Support

Bei Fragen oder Problemen:
1. Prüfe die Dokumentation in `OPENAI_WRAPPER.md`
2. Schaue dir die Beispiele in `openai_wrapper_examples.py` an
3. Aktiviere Logging für detaillierte Fehlerinformationen
