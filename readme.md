# FH-SWiFty-Chatbot

## Beschreibung
Ein intelligenter KI-Chatbot für die FH Südwestfalen (SWF), entwickelt mit LangGraph und Chainlit. Der Chatbot kann Fragen über die Hochschule und ihre Studiengänge beantworten und greift dabei auf die offizielle Website der FH SWF zu.

## Projektstatus
- **Version**: 0.14.2
- **Status**: In Entwicklung
- **Python erforderlich**: >=3.13
- **Letzte Aktualisierung**: Januar 2025

## Technologie-Stack
- **LangGraph**: Agent-basierte Architektur
- **Chainlit**: Web-Interface für den Chatbot
- **OpenAI GPT-4**: Sprachmodell
- **Tavily Search**: Web-Suche auf der FH SWF Website
- **LangChain** (langchain-openai, langchain-community, langchain-tavily): Framework für LLM-Anwendungen
- **Neo4j**: Wissensgraph / Graph-Datenbank (optional)
- **MCP** (langchain-mcp-adapters): Model Context Protocol-Integration
- **Docker**: Containerisierung
- **Kubernetes**: Orchestrierung
- **UV**: Python Package Manager

## Projektstruktur
```
FH-SWiFty-Chatbot/
├── main.py                              # Skript-Einstieg
├── pyproject.toml                       # Projektkonfiguration
├── chainlit.md                          # Willkommensseite im Chat-UI
├── rag_tool.py                          # RAG-Tool (Retrieval)
├── Dockerfile                           # Container-Konfiguration
├── docker-compose.yaml                  # Docker Compose Setup
├── build.sh                             # Build-Skript
├── CHANGELOG.md                         # Änderungsprotokoll
├── release_config.json                  # Release-Konfiguration
├── SERVICES.md                          # Services-Dokumentation
├── .chainlit/                           # Chainlit-Konfiguration
│   ├── config.toml                      # UI-/Sprach-Konfiguration
│   └── translations/                    # Übersetzungen (mehrsprachig)
├── public/                              # Statische Assets
│   ├── logo_dark.png, logo_light.png    # Logos
│   ├── favicon.ico, favicon.png         # Favicons
│   ├── fh-swf-avatar.png                # Avatar
│   ├── fh-swf-theme.css                 # Theme
│   ├── mcp-config.js                    # MCP-Client-Konfiguration
│   └── *.svg                            # Icons (professor, schedule, …)
├── k8s/                                 # Kubernetes-Konfiguration
│   ├── application.yaml, deployment.yaml, ingress.yaml
│   ├── kustomization.yaml, secrets.yaml, service.yaml
│   ├── mcp-server-deployment.yaml, mcp-server-service.yaml
│   ├── neo4j-deployment.yaml, neo4j-pvc.yaml, neo4j-service.yaml
│   └── qdrant-deployment.yaml, qdrant-pvc.yaml, qdrant-service.yaml
├── fh-swifty-chatbot/                   # Haupt-Chatbot-Modul
│   ├── agent_langgraph_app.py           # Chainlit-Einstieg (Haupt-App)
│   ├── main.py                          # Modul-Einstieg
│   ├── helpers/                         # Hilfsfunktionen
│   │   ├── prompts.py                   # Prompt-Templates
│   │   ├── tools.py                     # Web-Such-Tools
│   │   ├── check_blacklist.py           # Blacklist-Prüfung
│   │   ├── fallback.py                  # Fallback-Logik
│   │   ├── feedback.py                  # Feedback
│   │   └── starters.py                 # Startnachrichten
│   └── notebook/web_crawler/
│       └── urlLoader.ipynb              # Web-Crawler-Notebook
├── notebook/                            # Entwicklungs-Notebooks
│   └── check_blacklist_openai_v1.ipynb   # Blacklist-Check
├── crawler/                             # Web-Crawler-Modul (Workspace)
│   ├── crawl_fhswf.py                   # FH SWF Web-Crawler
│   ├── pyproject.toml                   # Crawler-Konfiguration
│   └── README.md                        # Crawler-Dokumentation
├── mcp/                                 # MCP (Model Context Protocol)
│   ├── test-mcp-server.py               # MCP-Server-Test
│   ├── test-mcp-client.ipynb            # MCP-Client-Notebook
│   └── langchain-mcp.ipynb              # LangChain-MCP-Integration
├── Neue_Codes KI_Intergration/           # RAG/KG-Pipeline (Neo4j, Embeddings)
│   ├── mcp_server.py, rag_tool_kg_entity_edges.py
│   ├── load_into_neo4j.py, embed_to_jsonl.py, …
│   └── README.md
├── test_frontend/                       # Frontend-/Blacklist-Tests
└── testing_chatbot/                     # Chatbot-Tests (Auswertung, App)
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
- `LANGSMITH_API_KEY`: API-Schlüssel für LANGSMITH
- `LANGSMITH_PROJECT`: ProjektName für LANGSMITH
- `LANGSMITH_ENDPOINT`: "https://api.smith.langchain.com"
- `LANGSMITH_TRACING`: "true"

**Sicherheitshinweis**: Alle API-Schlüssel und Proxy-Konfigurationen sollten in einer `.env`-Datei gespeichert werden, die **nicht** ins Repository committed wird.

## Aktuelle Funktionen
- ✅ Intelligente Gesprächsführung mit GPT-4
- ✅ Web-Suche auf der FH SWF Website
- ✅ Reaktive Agent-Architektur mit LangGraph
- ✅ Modernes Web-Interface mit Chainlit (mehrsprachige UI)
- ✅ RAG & Wissensgraph (Neo4j, Qdrant) über `Neue_Codes KI_Intergration`
- ✅ MCP-Integration (Model Context Protocol)
- ✅ Docker-Containerisierung
- ✅ Kubernetes-Deployment (inkl. Neo4j, Qdrant, MCP-Server)
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

# Chatbot starten (Chainlit)
uv run chainlit run fh-swifty-chatbot/agent_langgraph_app.py
```