#!/usr/bin/env python3
"""
rag_tool_kg_entity_edges.py

RAG + Knowledge Graph (entity-to-entity edges) for self-hosted Neo4j (Docker).

- Uses Neo4j VECTOR index (default: chunk_embedding_index)
- Retrieves topK chunks via db.index.vector.queryNodes
- Builds KG context:
  - (:Chunk)-[:MENTIONS]->(:Entity)
  - (:Entity)-[:REL {type}]->(:Entity)
- Calls OpenAI LLM for German answers and prints sources with URLs if available.
"""

import os
import json
import argparse
import re
from typing import Any, Dict, List, Optional

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
# Utilities
# -----------------------------
_URL_RE = re.compile(r"^https?://", re.IGNORECASE)


def is_http_url(s: str) -> bool:
    return bool(s and _URL_RE.match(s.strip()))


def extract_best_source(node: Any) -> str:
    """
    Prefer real URLs when possible. Tries:
      1) node.url / node.source / node.path
      2) node.metadata.url / node.metadata.source / node.metadata.path
    """
    if not node:
        return ""

    # direct props
    for k in ("url", "source", "path"):
        v = node.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()

    # metadata props
    md = node.get("metadata")
    if isinstance(md, dict):
        for k in ("url", "source", "path"):
            v = md.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()

    return ""


def _clip(s: str, n: int) -> str:
    s = (s or "").strip()
    return s if len(s) <= n else (s[:n].rstrip() + " …")


# -----------------------------
# OpenAI Embeddings
# -----------------------------
def embed_text(client: OpenAI, text: str) -> List[float]:
    resp = client.embeddings.create(model=EMBEDDING_MODEL, input=text)
    return resp.data[0].embedding


# -----------------------------
# Neo4j retrieval
# -----------------------------
def fetch_topk_chunks(tx, index_name: str, embedding: List[float], k: int) -> List[Dict[str, Any]]:
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

        source = extract_best_source(c)

        out.append({
            "id": c.get("id"),
            "text": (c.get("text") or c.get("page_content") or ""),
            "score": score,
            "source": source,
            "title": (c.get("title") or (c.get("metadata", {}) or {}).get("title") or ""),
            "kg_relations_json": c.get("kg_relations_json") or "",
        })
    return out


def fetch_entities_for_chunks(tx, chunk_ids: List[str], limit_entities: int) -> List[Dict[str, Any]]:
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
def build_prompt_de(question: str, chunks: List[Dict[str, Any]], entities: List[Dict[str, Any]], rels: List[Dict[str, Any]]) -> str:
    if chunks:
        chunk_blocks = []
        for i, c in enumerate(chunks, start=1):
            header = f"[Chunk {i}] score={c['score']:.4f} | id={c.get('id','')}"
            if c.get("title"):
                header += f" | title={c['title']}"
            if c.get("source"):
                header += f" | source={c['source']}"
            chunk_blocks.append(header + "\n" + _clip(c.get("text", ""), MAX_CHUNK_CHARS))
        chunk_text = "\n\n---\n\n".join(chunk_blocks)
    else:
        chunk_text = "Keine Chunks gefunden."

    if entities:
        ent_text = "\n".join([f"- {e['name']} ({e['type']}) [freq={e.get('freq',0)}]" for e in entities])
    else:
        ent_text = "Keine Entities gefunden."

    if rels:
        rel_text = "\n".join([f"- {r['source']} --{r['type']}--> {r['target']}" for r in rels])
    else:
        rel_text = "Keine Entity-zu-Entity-Relationen gefunden."

    return f"""
Du bist ein hilfreicher Assistent. Beantworte die Nutzerfrage auf Deutsch, sachlich und nachvollziehbar.

WICHTIG:
- Nutze primär den Kontext aus Chunks und Knowledge-Graph.
- Wenn etwas nicht im Kontext steht: sag das klar.
- Keine Halluzinationen.
- Nenne am Ende **Quellen**: liste die verwendeten Chunks als Bulletpoints.
  Jede Quelle soll möglichst eine URL enthalten. Falls keine URL existiert, nutze den gespeicherten source/path.

Nutzerfrage:
{question}

========================
CHUNK-KONTEXT (Top {len(chunks)}):
{chunk_text}

========================
KNOWLEDGE-GRAPH: ENTITIES:
{ent_text}

========================
KNOWLEDGE-GRAPH: RELATIONEN (Entity->Entity):
{rel_text}

Antworte strukturiert:
1) Antwort
2) Kurze Begründung mit Bezug auf Kontext
3) Quellen (Chunk-Liste, mit URL wenn möglich)
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

        # Sources list for UI + always include URL if possible
        sources = []
        for c in chunks:
            src = (c.get("source") or "").strip()
            sources.append({
                "chunk_id": c.get("id"),
                "score": c.get("score"),
                "title": c.get("title"),
                "source": src,
                "is_url": is_http_url(src),
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
        line = f"- id={s.get('chunk_id')} | score={float(s.get('score') or 0.0):.4f}"
        if s.get("title"):
            line += f" | title={s.get('title')}"
        if s.get("source"):
            line += f" | source={s.get('source')}"
        print(line)


if __name__ == "__main__":
    main()
