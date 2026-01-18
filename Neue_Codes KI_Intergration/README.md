# SWiFty MCP RAG Server (Neo4j + OpenAI)

Dieses Repository enthält einen kleinen **MCP-Server** (mit **FastMCP**), der ein RAG-Tool als **MCP Tool** bereitstellt.

Die Idee:  
Du hast bereits deine FH-Web-Chunks in Neo4j und zusätzlich eine Knowledge-Graph-Struktur (Entities + Kanten).  
Der Server beantwortet Fragen (auf Deutsch), indem er:

1) ein Query-Embedding erstellt (OpenAI)  
2) passende Chunks per **Neo4j Vektor-Index** findet (TopK)  
3) zusätzlich KG-Kontext über `(:Chunk)-[:MENTIONS]->(:Entity)` und `(:Entity)-[:REL]->(:Entity)` einsammelt  
4) alles an ein OpenAI Chat-Modell übergibt und eine deutsche Antwort inkl. Quellen zurückgibt  

---

## Projektstruktur

- `rag_tool_kg_entity_edges.py`  
  Enthält die eigentliche RAG-Logik. Wichtig: Es muss eine Funktion `rag_answer(question: str) -> dict` geben.

- `mcp_server.py`  
  FastMCP-Wrapper: stellt Tools bereit, z.B. `rag_ask(question)` und `health()`.

- `requirements.txt`  
  Python Dependencies.

- `Dockerfile`  
  Container-Setup zum einfachen Starten.

---

## Voraussetzungen

- Python 3.10+ (empfohlen: 3.11)
- Neo4j erreichbar (Docker oder Aura / Self-hosted)
- In Neo4j existieren bereits die **Chunk-Nodes** (ca. 42.966)
- OpenAI API Key

---

## Environment Variablen

Diese Variablen müssen gesetzt sein:

- `OPENAI_API_KEY`
- `NEO4J_URI`
- `NEO4J_USER`
- `NEO4J_PASSWORD`

Optional (je nach RAG Tool):

- `NEO4J_DATABASE`
- `RAG_VECTOR_INDEX` (default oft `chunk_embedding_index`)
- `RAG_TOP_K` (default 10)
- `RAG_EMBEDDING_MODEL`
- `RAG_CHAT_MODEL`
- `RAG_MAX_TOKENS`
- `RAG_MAX_CHUNK_CHARS`
- `RAG_MAX_ENTITIES`
- `RAG_MAX_RELATIONS`

---

## Lokale Installation (Windows / CMD)

### 1) Virtuelle Umgebung erstellen
```cmd
python -m venv .venv
.venv\Scripts\activate

