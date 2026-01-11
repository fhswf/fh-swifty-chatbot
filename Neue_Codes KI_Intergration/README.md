# MCP RAG Server (Neo4j + OpenAI)

Dieses Projekt stellt einen **einfachen, aber produktionsnahen HTTP-Server** auf Basis von **FastAPI** bereit, der einen **RAG-Endpoint (Retrieval-Augmented Generation)** zur Verfügung stellt.  
Der Server kann von einem Frontend (lokal oder extern über Tunnel) angesprochen werden und liefert **deutschsprachige Antworten** inklusive **Quellen und Knowledge-Graph-Kontext**.

Der Fokus liegt auf **Verständlichkeit, Stabilität und Erweiterbarkeit**.

---

## Was macht dieser Server genau?

Der MCP RAG Server kombiniert drei Dinge:

1. **Vektorbasierte Suche in Neo4j**
   - Ähnlichkeitssuche über `:Chunk(embedding)`
   - Standardmäßig mit **Top-K = 10**

2. **Knowledge Graph Kontext**
   - Erwähnungen von Entitäten in Texten:
     - `(:Chunk)-[:MENTIONS]->(:Entity)`
   - Semantische Beziehungen zwischen Entitäten:
     - `(:Entity)-[:REL {type}]->(:Entity)`

3. **LLM-Antworten mit OpenAI**
   - Nutzung eines OpenAI-Modells für:
     - natürliche Antworten auf Deutsch
     - Einbindung von Quellen (Chunks)
     - Nutzung von KG-Relationen für bessere Erklärungen

Das Ergebnis ist ein **sauberer RAG-Flow**, der nicht nur Text sucht, sondern auch **Strukturwissen aus dem Knowledge Graph** nutzt.

---

## Projektstruktur

```text
.
├── rag_tool_kg_entity_edges.py   # Kernlogik des RAG-Tools (Neo4j + OpenAI)
├── mcp_server.py                 # HTTP / MCP Server (FastAPI)
├── requirements.txt              # Python-Abhängigkeiten
└── Dockerfile                    # Optional: Containerisierung
