# FH-SWiFty-Chatbot

## Beschreibung
Ein intelligenter KI-Chatbot für die FH Südwestfalen (SWF), entwickelt mit LangGraph und Chainlit. Der Chatbot kann Fragen über die Hochschule und ihre Studiengänge beantworten und greift dabei auf die offizielle Website der FH SWF zu.

## Projektstatus
- **Version**: 0.1.5
- **Status**: In Entwicklung
- **Python erforderlich**: >=3.13
- **Letzte Aktualisierung**: 18. September 2025

## Technologie-Stack
- **LangGraph**: Agent-basierte Architektur
- **Chainlit**: Web-Interface für den Chatbot
- **OpenAI GPT-4**: Sprachmodell
- **Tavily Search**: Web-Suche auf der FH SWF Website
- **LangChain**: Framework für LLM-Anwendungen
- **Docker**: Containerisierung
- **Kubernetes**: Orchestrierung
- **UV**: Python Package Manager

## Projektstruktur
```
FH-SWiFty-Chatbot/
├── main.py                              # Haupteingangspunkt
├── pyproject.toml                       # Projektkonfiguration
├── chainlit.md                          # Chainlit-Konfiguration
├── Dockerfile                           # Container-Konfiguration
├── docker-compose.yaml                  # Docker Compose Setup
├── build.sh                             # Build-Skript
├── CHANGELOG.md                         # Änderungsprotokoll
├── release_config.json                  # Release-Konfiguration
├── uv.lock                              # Abhängigkeits-Lockfile
├── public/                              # Statische Assets
│   ├── logo_dark.png                    # Dunkles Logo
│   └── logo_light.png                   # Helles Logo
├── k8s/                                 # Kubernetes-Konfiguration
│   ├── application.yaml                 # K8s-Anwendung
│   ├── deployment.yaml                  # K8s-Deployment
│   ├── ingress.yaml                     # K8s-Ingress
│   ├── kustomization.yaml              # Kustomize-Konfiguration
│   ├── secrets.yaml                     # K8s-Secrets
│   └── service.yaml                     # K8s-Service
├── fh-swifty-chatbot/                   # Haupt-Chatbot-Modul
│   ├── agent_langgraph_app.py          # Haupt-Chatbot-Anwendung
│   ├── main.py                         # Modul-Eingangspunkt
│   ├── helpers/                         # Hilfsfunktionen
│   │   ├── prompts.py                  # Prompt-Templates
│   │   └── tools.py                    # Web-Such-Tools
│   └── notebook/                        # Jupyter Notebooks
│       └── web_crawler/
│           └── urlLoader.ipynb         # Web-Crawler-Notebook
            └── check_blacklist_openai_v1.ipynb   # Checkblacklist
├── notebook/                            # Entwicklungs-Notebooks
├── crawler/                             # Web-Crawler-Modul
│   ├── crawl_fhswf.py                  # FH SWF Web-Crawler
│   ├── pyproject.toml                  # Crawler-Konfiguration
│   └── README.md                       # Crawler-Dokumentation
└── data/                                # Datenverzeichnis
    └── blacklist/                       # Blacklist-Daten
```

## Installation

### Lokale Installation
```bash
# Repository klonen
git clone <repository-url>
cd FH-SWiFty-Chatbot

# Virtuelles Environment erstellen und Abhängigkeiten installieren
uv venv
uv sync

# Environment aktivieren (Windows)
.venv\Scripts\activate

# Chainlit-Anwendung starten
uv run chainlit run fh-swifty-chatbot/agent_langgraph_app.py
```

### Docker Installation
```bash
# Mit Docker Compose
docker-compose up

# Oder mit Docker
docker build -t fh-swifty-chatbot .
docker run -p 8000:8000 fh-swifty-chatbot
```

## Verwendung

### Mit UV (Empfohlen)
```bash
# Environment aktivieren
.venv\Scripts\activate  # Windows
# oder
source .venv/bin/activate  # Linux/Mac

# Anwendung starten
uv run chainlit run fh-swifty-chatbot/agent_langgraph_app.py
```

### Mit Python direkt
```bash
python -m chainlit run fh-swifty-chatbot/agent_langgraph_app.py
```

Nach dem Start ist der Chatbot über den Browser unter `http://localhost:8000` erreichbar.

## Konfiguration
Der Chatbot benötigt folgende Umgebungsvariablen:
- `OPENAI_API_KEY`: API-Schlüssel für OpenAI
- `TAVILY_API_KEY`: API-Schlüssel für Tavily Search
- `OPENAI_BASE_URL`: (Optional) Benutzerdefinierte OpenAI-URL
- `HTTPS_PROXY`: (Optional) Proxy-Konfiguration

**Sicherheitshinweis**: Alle API-Schlüssel und Proxy-Konfigurationen sollten in einer `.env`-Datei gespeichert werden, die **nicht** ins Repository committed wird.

## Aktuelle Funktionen
- ✅ Intelligente Gesprächsführung mit GPT-4
- ✅ Web-Suche auf der FH SWF Website
- ✅ Reaktive Agent-Architektur mit LangGraph
- ✅ Modernes Web-Interface mit Chainlit
- ✅ Docker-Containerisierung
- ✅ Kubernetes-Deployment
- ✅ Automatische Informationsbeschaffung
- ✅ Jupyter Notebook-Integration
- ✅ Automatische Versionierung mit Semantic Release
- ✅ Intelligente Inhaltsmoderation (Blacklist-System)

## Entwicklung
Das Projekt verwendet die Python-Packaging-Struktur mit `pyproject.toml` und moderne LLM-Frameworks für eine skalierbare Chatbot-Architektur.

### Entwicklungsumgebung einrichten
```bash
# Environment erstellen
uv venv

# Alle Abhängigkeiten installieren 
uv sync

# Environment aktivieren
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Development-Dependencies installieren
uv sync --group notebook
```

### Nützliche UV-Befehle
```bash
# Abhängigkeiten aktualisieren
uv sync --upgrade

# Spezifische Gruppe installieren
uv sync --group notebook

# Anwendung im Environment ausführen
uv run python main.py
```