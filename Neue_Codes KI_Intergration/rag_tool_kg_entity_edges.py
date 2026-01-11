#!/usr/bin/env python3
"""
rag_tool_kg_entity_edges.py

RAG + Knowledge Graph (entity-to-entity edges) for self-hosted Neo4j (Docker).

Flow:
1) Embed user question with OpenAI
2) Vector-search topK=10 :Chunk nodes via Neo4j vector index
3) Build KG context:
   - Entities mentioned by those chunks (c)-[:MENTIONS]->(e)
   - Entity-to-entity relations among those entities (e)-[:REL {type}]->(e)
   - Optional: chunk.kg_relations_json fallback (if present)
4) Ask OpenAI Chat model in German, produce an answer + sources.

Requirements:
  pip install neo4j openai python-dotenv

Env vars:
  OPENAI_API_KEY
  NEO4J_URI        (e.g. bolt://localhost:7687)
  NEO4J_USER
  NEO4J_PASSWORD

Optional env vars:
  NEO4J_DATABASE           (optional)
  RAG_VECTOR_INDEX         default: chunk_embedding_index
  RAG_TOP_K                default: 10
  RAG_EMBEDDING_MODEL      default: text-embedding-3-small
  RAG_CHAT_MODEL           default: gpt-4.1-mini
  RAG_MAX_TOKENS           default: 750
  RAG_MAX_CHUNK_CHARS      default: 1200
  RAG_MAX_ENTITIES         default: 40
  RAG_MAX_RELATIONS        default: 80
"""

import os
import json
import argparse
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from neo4j import GraphDatabase, Driver
from openai import OpenAI

load_dotenv()

# -----------------------------
# Config
# -----------------------------
NEO4J_URI = (os.getenv("NEO4J_URI") or "").strip()
NEO4J_USER = (os.getenv("NEO4J_USER") or "").strip()
NEO4J_PASSWORD = (os.getenv("NEO4J_PASSWORD") or "").strip()
NEO4J_DATABASE = (os.getenv("NEO4J_DATABASE") or "").strip() or None

OPENAI_API_KEY = (os.getenv("OPENAI_API_KEY") or "").strip()

VECTOR_INDEX = (os.getenv("RAG_VECTOR_INDEX") or "chunk_embedding_index").strip()
TOP_K = int((os.getenv("RAG_TOP_K") or "10").strip())

EMBEDDING_MODEL = (os.getenv("RAG_EMBEDDING_MODEL") or "text-embedding-3-small").strip()
CHAT_MODEL = (os.getenv("RAG_CHAT_MODEL") or "gpt-4.1-mini").strip()
MAX_TOKENS = int((os.getenv("RAG_MAX_TOKENS") or "750").strip())

MAX_CHUNK_CHARS = int((os.getenv("RAG_MAX_CHUNK_CHARS") or "1200").strip())
MAX_ENTITIES = int((os.getenv("RAG_MAX_ENTITIES") or "40").strip())
MAX_RELATIONS = int((os.getenv("RAG_MAX_RELATIONS") or "80").strip())


def require_env() -> None:
    missing = []
    if not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")
    if not NEO4J_URI:
        missing.append("NEO4J_URI")
    if not NEO4J_USER:
        missing.append("NEO4J_USER")
    if not NEO4J_PASSWORD:
        missing.append("NEO4J_PASSWORD")
    if missing:
        raise SystemExit(f"[ERROR] Missing env vars: {', '.join(missing)}")


def get_driver() -> Driver:
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def get_openai_client() -> OpenAI:
    return OpenAI(api_key=OPENAI_API_KEY)


# -----------------------------
# OpenAI Embeddings
# -----------------------------
def embed_text(client: OpenAI, text: str) -> List[float]:
    resp = client.embeddings.create(model=EMBEDDING_MODEL, input=text)
    return resp.data[0].embedding


# -----------------------------
# Neo4j retrieval
# -----------------------------
def fetch_topk_chunks(
    tx,
    index_name: str,
    embedding: List[float],
    k: int
) -> List[Dict[str, Any]]:
    """
    Requires vector index like:
      CREATE VECTOR INDEX chunk_embedding_index
      FOR (c:Chunk) ON (c.embedding) ...
    """
    cypher = """
    CALL db.index.vector.queryNodes($index_name, $k, $embedding)
    YIELD node, score
    RETURN node AS c, score
    ORDER BY score DESC
    """
    rows = tx.run(cypher, index_name=index_name, k=k, embedding=embedding).data()

    out: List[Dict[str, Any]] = []
    for r in rows:
        c = r["c"]
        score = float(r["score"])
        out.append({
            "id": c.get("id"),
            "text": (c.get("text") or c.get("page_content") or ""),
            "score": score,
            "source": c.get("source") or c.get("url") or c.get("path") or "",
            "title": c.get("title") or "",
            "kg_relations_json": c.get("kg_relations_json") or "",
        })
    return out


def fetch_entities_for_chunks(tx, chunk_ids: List[str], limit_entities: int) -> List[Dict[str, Any]]:
    """
    Get entities mentioned by the selected chunks.
    """
    cypher = """
    UNWIND $chunk_ids AS cid
    MATCH (c:Chunk {id: cid})-[:MENTIONS]->(e:Entity)
    WITH e, count(*) AS freq
    RETURN e.name AS name, coalesce(e.type, 'Other') AS type, freq
    ORDER BY freq DESC, name ASC
    LIMIT $limit
    """
    return tx.run(cypher, chunk_ids=chunk_ids, limit=limit_entities).data()


def fetch_relations_between_entities(tx, entity_names: List[str], limit_rel: int) -> List[Dict[str, Any]]:
    """
    Fetch entity-to-entity relations among the mentioned entities.
    Uses a single relationship type :REL with property r.type.
    """
    cypher = """
    UNWIND $names AS n
    MATCH (a:Entity {name: n})
    WITH collect(a) AS ents
    UNWIND ents AS a
    MATCH (a)-[r:REL]->(b:Entity)
    WHERE b IN ents
    RETURN a.name AS source, r.type AS type, b.name AS target
    LIMIT $limit
    """
    return tx.run(cypher, names=entity_names, limit=limit_rel).data()


# -----------------------------
# Prompt building
# -----------------------------
def _clip(s: str, n: int) -> str:
    s = s or ""
    s = s.strip()
    return s if len(s) <= n else (s[:n].rstrip() + " …")


def build_prompt_de(
    question: str,
    chunks: List[Dict[str, Any]],
    entities: List[Dict[str, Any]],
    rels: List[Dict[str, Any]],
) -> str:
    # Chunk context
    if chunks:
        chunk_blocks = []
        for i, c in enumerate(chunks, start=1):
            header = f"[Chunk {i}] score={c['score']:.4f}"
            if c.get("title"):
                header += f" | title={c['title']}"
            if c.get("source"):
                header += f" | source={c['source']}"
            header += f" | id={c.get('id','')}"
            chunk_blocks.append(header + "\n" + _clip(c.get("text",""), MAX_CHUNK_CHARS))
        chunk_text = "\n\n---\n\n".join(chunk_blocks)
    else:
        chunk_text = "Keine Chunks gefunden."

    # KG entity context
    if entities:
        ent_lines = []
        for e in entities:
            ent_lines.append(f"- {e['name']} ({e['type']}) [freq={e.get('freq',0)}]")
        ent_text = "\n".join(ent_lines)
    else:
        ent_text = "Keine Entities gefunden."

    # KG relation context
    if rels:
        rel_lines = []
        for r in rels:
            rel_lines.append(f"- {r['source']} --{r['type']}--> {r['target']}")
        rel_text = "\n".join(rel_lines)
    else:
        rel_text = "Keine Entity-zu-Entity-Relationen gefunden."

    # Optional fallback: show chunk-level relation JSON count (not full dump)
    chunk_rel_counts = []
    for c in chunks:
        raw = c.get("kg_relations_json") or ""
        if raw:
            try:
                arr = json.loads(raw)
                if isinstance(arr, list) and arr:
                    chunk_rel_counts.append(f"- {c.get('id','')}: {len(arr)} relations in kg_relations_json")
            except Exception:
                pass
    chunk_rel_hint = "\n".join(chunk_rel_counts) if chunk_rel_counts else "(keine chunk-level relations_json Hinweise)"

    return f"""
Du bist ein hilfreicher Assistent. Beantworte die Nutzerfrage auf Deutsch, sachlich und nachvollziehbar.

WICHTIG:
- Nutze primär den Kontext aus Chunks und Knowledge-Graph.
- Wenn etwas nicht im Kontext steht: sag das klar.
- Keine Halluzinationen.
- Nenne am Ende **Quellen**: liste die verwendeten Chunks als Bulletpoints (id + ggf. source/title).

Nutzerfrage:
{question}

========================
CHUNK-KONTEXT (Top {len(chunks)}):
{chunk_text}

========================
KNOWLEDGE-GRAPH: ENTITIES (aus den Chunks):
{ent_text}

========================
KNOWLEDGE-GRAPH: RELATIONEN (Entity->Entity):
{rel_text}

========================
HINWEIS: Chunk-level kg_relations_json (nur Anzahl je Chunk):
{chunk_rel_hint}

Antworte strukturiert:
1) Antwort
2) Kurze Begründung mit Bezug auf Kontext
3) Quellen (Chunk-Liste)
""".strip()


def ask_llm(client: OpenAI, prompt: str) -> str:
    resp = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": "Du antwortest immer auf Deutsch, präzise und quellenorientiert."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=MAX_TOKENS,
    )
    return resp.choices[0].message.content.strip()


# -----------------------------
# Main RAG function
# -----------------------------
def rag_answer(question: str) -> Dict[str, Any]:
    require_env()
    oai = get_openai_client()
    driver = get_driver()

    try:
        q_emb = embed_text(oai, question)

        with driver.session(database=NEO4J_DATABASE) if NEO4J_DATABASE else driver.session() as session:
            chunks = session.execute_read(fetch_topk_chunks, VECTOR_INDEX, q_emb, TOP_K)

            # Keep only valid chunk ids
            chunk_ids = [c["id"] for c in chunks if isinstance(c.get("id"), str) and c["id"].strip()]

            entities = []
            rels = []
            if chunk_ids:
                entities = session.execute_read(fetch_entities_for_chunks, chunk_ids, MAX_ENTITIES)
                ent_names = [e["name"] for e in entities if isinstance(e.get("name"), str) and e["name"].strip()]
                if ent_names:
                    rels = session.execute_read(fetch_relations_between_entities, ent_names, MAX_RELATIONS)

        prompt = build_prompt_de(question, chunks, entities, rels)
        answer = ask_llm(oai, prompt)

        # Build sources list for UI
        sources = []
        for c in chunks:
            sources.append({
                "chunk_id": c.get("id"),
                "score": c.get("score"),
                "title": c.get("title"),
                "source": c.get("source"),
            })

        return {
            "question": question,
            "answer": answer,
            "top_k": TOP_K,
            "sources": sources,
            "kg_entities": entities,
            "kg_relations": rels,
        }
    finally:
        driver.close()


# -----------------------------
# CLI
# -----------------------------
def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="RAG Tool (TopK=10) using Neo4j vector index + KG entity-to-entity edges.")
    p.add_argument("--question", default=None, help="Question. If omitted, interactive input.")
    p.add_argument("--json", action="store_true", help="Print full JSON result (answer + sources + KG).")
    return p


def main():
    args = build_arg_parser().parse_args()
    q = args.question
    if not q:
        try:
            q = input("Bitte gib deine Frage ein (Deutsch): ").strip()
        except KeyboardInterrupt:
            print("\nAbgebrochen.")
            return
    if not q:
        print("[ERROR] No question.")
        return

    result = rag_answer(q)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print("\n" + "=" * 80)
    print("FRAGE:")
    print(result["question"])
    print("\nANTWORT:")
    print(result["answer"])
    print("\n" + "-" * 80)
    print("QUELLEN (TopK=10):")
    for s in result["sources"]:
        line = f"- id={s.get('chunk_id')} | score={s.get('score'):.4f}"
        if s.get("title"):
            line += f" | title={s.get('title')}"
        if s.get("source"):
            line += f" | source={s.get('source')}"
        print(line)

    print("\n" + "-" * 80)
    print("KG-KONTEXT (Kurz):")
    if result["kg_entities"]:
        print("Entities (top): " + ", ".join([e["name"] for e in result["kg_entities"][:15]]))
    else:
        print("Entities: (keine)")
    if result["kg_relations"]:
        print("Relations (top):")
        for r in result["kg_relations"][:10]:
            print(f"  - {r['source']} --{r['type']}--> {r['target']}")
    else:
        print("Relations: (keine)")


if __name__ == "__main__":
    main()
