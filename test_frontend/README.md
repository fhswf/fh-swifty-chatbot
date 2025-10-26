# Tests Frontend - Blacklist System

Dieses Verzeichnis enthält die Testskripte für das Blacklist-System des FH-SWiFty Chatbots.

## Dateien

- `test_blacklist.py` - Haupttestskript für das Blacklist-System

## Verwendung

### Einfacher Test-Modus

Führt eine Reihe vordefinierter Tests aus:

```bash
python test_frontend/test_blacklist.py
```

### Interaktiver Modus

Ermöglicht das interaktive Testen benutzerdefinierter Fragen:

```bash
python test_frontend/test_blacklist.py -i
```

oder

```bash
python test_frontend/test_blacklist.py --interactive
```

Im interaktiven Modus können Sie:
- Beliebige Fragen zum Testen eingeben
- `exit`, `quit` oder `q` eingeben, um zu beenden

## Voraussetzungen

- Python 3.10+
- Die Projektabhängigkeiten müssen installiert sein
- Umgebungsvariable `OPENAI_API_KEY` muss konfiguriert sein

## Test-Kategorien

Das System klassifiziert Fragen in drei Kategorien:

- ✅ **valid** : Legitime Fragen zur FH
- ❌ **not_valid** : Unangemessene, beleidigende oder kontextfremde Fragen
- ➖ **neutral** : Neutrale Fragen, die nicht direkt die FH betreffen
