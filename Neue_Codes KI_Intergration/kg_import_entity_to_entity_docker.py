#!/usr/bin/env python3
"""
kg_import_entity_to_entity_docker.py

Loads KG extracted JSONL into self-hosted Neo4j (Docker) with entity-to-entity edges.

Creates:
- (:Entity {name}) with optional e.type
- (:Chunk {id}) is assumed to already exist (your 42,966 chunks)
- (:Chunk)-[:MENTIONS]->(:Entity)
- (:Entity)-[:REL {type}]->(:Entity)  (single rel type + property for flexibility)
- Stores raw relations JSON on Chunk: c.kg_relations_json (recommended backup)

Input JSONL line:
{
  "chunk_id": "...",
  "entities": [{"name":"...", "type":"..."}],
  "relations": [{"source":"...", "type":"...", "target":"..."}]
}

Env vars (recommended):
  NEO4J_URI        e.g. bolt://localhost:7687
  NEO4J_USER       e.g. neo4j
  NEO4J_PASSWORD   your password

Optional env vars:
  KG_INPUT_PATH              default: E:\\kg_extracted.jsonl
  KG_PROCESSED_IDS_PATH      default: E:\\kg_import_processed_entity_edges.txt
  KG_BATCH_SIZE              default: 200
  KG_MAX_RETRIES             default: 8
  KG_SLEEP_SEC               default: 0.0
  KG_MAX_RELATIONS_PER_CHUNK default: 50
  KG_WRITE_MENTIONS          default: 1
  KG_STORE_RELATIONS_JSON    default: 1

Notes:
- For Docker/self-hosted, relationship limits are not like Aura Free, but you can still
  hit transaction memory/timeouts. Use batching and relation caps.
"""

import os
import json
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from dotenv import load_dotenv
from neo4j import GraphDatabase
from neo4j.exceptions import TransientError, ServiceUnavailable

load_dotenv()

NEO4J_URI = (os.getenv("NEO4J_URI") or "").strip()
NEO4J_USER = (os.getenv("NEO4J_USER") or "").strip()
NEO4J_PASSWORD = (os.getenv("NEO4J_PASSWORD") or "").strip()

INPUT_PATH = (os.getenv("KG_INPUT_PATH") or r"E:\kg_extracted.jsonl").strip()
PROCESSED_IDS_PATH = (os.getenv("KG_PROCESSED_IDS_PATH") or r"E:\kg_import_processed_entity_edges.txt").strip()

BATCH_SIZE = int((os.getenv("KG_BATCH_SIZE") or "200").strip())
MAX_RETRIES = int((os.getenv("KG_MAX_RETRIES") or "8").strip())
SLEEP_SEC = float((os.getenv("KG_SLEEP_SEC") or "0.0").strip())

MAX_RELATIONS_PER_CHUNK = int((os.getenv("KG_MAX_RELATIONS_PER_CHUNK") or "50").strip())
WRITE_MENTIONS = (os.getenv("KG_WRITE_MENTIONS") or "1").strip().lower() not in ("0", "false", "no")
STORE_RELATIONS_JSON = (os.getenv("KG_STORE_RELATIONS_JSON") or "1").strip().lower() not in ("0", "false", "no")


def require_env() -> None:
    missing = []
    for k, v in [("NEO4J_URI", NEO4J_URI), ("NEO4J_USER", NEO4J_USER), ("NEO4J_PASSWORD", NEO4J_PASSWORD)]:
        if not v:
            missing.append(k)
    if missing:
        raise SystemExit(f"[ERROR] Missing env vars: {', '.join(missing)}")


def load_processed_ids(path: str) -> Set[str]:
    s: Set[str] = set()
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                cid = line.strip()
                if cid:
                    s.add(cid)
    return s


def append_processed_ids(path: str, ids: List[str]) -> None:
    if not ids:
        return
    with open(path, "a", encoding="utf-8") as f:
        for cid in ids:
            f.write(cid + "\n")


def jsonl_batches(path: str, batch_size: int):
    batch: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            batch.append(obj)
            if len(batch) >= batch_size:
                yield batch
                batch = []
    if batch:
        yield batch


def _clean_name(x: Any) -> str:
    if not isinstance(x, str):
        return ""
    return " ".join(x.strip().split())


def normalize_row(obj: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    chunk_id = obj.get("chunk_id")
    if not isinstance(chunk_id, str) or not chunk_id.strip():
        return None

    entities = obj.get("entities", [])
    relations = obj.get("relations", [])

    if not isinstance(entities, list):
        entities = []
    if not isinstance(relations, list):
        relations = []

    # Dedup entities by name (case-insensitive)
    clean_entities: List[Dict[str, str]] = []
    seen_ent: Set[str] = set()
    for e in entities:
        if not isinstance(e, dict):
            continue
        name = _clean_name(e.get("name"))
        etype = _clean_name(e.get("type")) or "Other"
        if not name:
            continue
        key = name.lower()
        if key in seen_ent:
            continue
        seen_ent.add(key)
        clean_entities.append({"name": name, "type": etype})

    # Dedup relations (case-insensitive endpoints + exact type)
    clean_rel: List[Dict[str, str]] = []
    seen_rel: Set[Tuple[str, str, str]] = set()

    for r in relations:
        if not isinstance(r, dict):
            continue
        src = _clean_name(r.get("source"))
        rtype = _clean_name(r.get("type")).replace(" ", "_")
        tgt = _clean_name(r.get("target"))
        if not src or not tgt or not rtype:
            continue
        if src.lower() == tgt.lower():
            continue

        key = (src.lower(), rtype, tgt.lower())
        if key in seen_rel:
            continue
        seen_rel.add(key)
        clean_rel.append({"source": src, "type": rtype, "target": tgt})

        if len(clean_rel) >= MAX_RELATIONS_PER_CHUNK:
            break

    relations_json = json.dumps(clean_rel, ensure_ascii=False)

    return {
        "chunk_id": chunk_id.strip(),
        "entities": clean_entities,
        "relations": clean_rel,
        "relations_json": relations_json,
    }


def import_tx(tx, rows: List[Dict[str, Any]]) -> None:
    """
    Import pattern:
    - Match existing Chunk by id
    - (optional) store relations JSON on chunk
    - merge entity nodes
    - (optional) merge mentions edges
    - merge entity-to-entity edges :REL {type}
    """
    if STORE_RELATIONS_JSON and WRITE_MENTIONS:
        q = """
        UNWIND $rows AS row
        MATCH (c:Chunk {id: row.chunk_id})

        SET c.kg_relations_json = row.relations_json

        WITH c, row

        // entity nodes
        UNWIND row.entities AS ent
        MERGE (e:Entity {name: ent.name})
        SET e.type = coalesce(e.type, ent.type, 'Other')
        MERGE (c)-[:MENTIONS]->(e)

        WITH row

        // entity-to-entity relations
        UNWIND row.relations AS rel
        MERGE (s:Entity {name: rel.source})
        MERGE (t:Entity {name: rel.target})
        MERGE (s)-[:REL {type: rel.type}]->(t)
        """
    elif STORE_RELATIONS_JSON and not WRITE_MENTIONS:
        q = """
        UNWIND $rows AS row
        MATCH (c:Chunk {id: row.chunk_id})

        SET c.kg_relations_json = row.relations_json

        WITH row

        UNWIND row.entities AS ent
        MERGE (e:Entity {name: ent.name})
        SET e.type = coalesce(e.type, ent.type, 'Other')

        WITH row

        UNWIND row.relations AS rel
        MERGE (s:Entity {name: rel.source})
        MERGE (t:Entity {name: rel.target})
        MERGE (s)-[:REL {type: rel.type}]->(t)
        """
    elif (not STORE_RELATIONS_JSON) and WRITE_MENTIONS:
        q = """
        UNWIND $rows AS row
        MATCH (c:Chunk {id: row.chunk_id})

        WITH c, row

        UNWIND row.entities AS ent
        MERGE (e:Entity {name: ent.name})
        SET e.type = coalesce(e.type, ent.type, 'Other')
        MERGE (c)-[:MENTIONS]->(e)

        WITH row

        UNWIND row.relations AS rel
        MERGE (s:Entity {name: rel.source})
        MERGE (t:Entity {name: rel.target})
        MERGE (s)-[:REL {type: rel.type}]->(t)
        """
    else:
        q = """
        UNWIND $rows AS row
        MATCH (c:Chunk {id: row.chunk_id})

        WITH row

        UNWIND row.entities AS ent
        MERGE (e:Entity {name: ent.name})
        SET e.type = coalesce(e.type, ent.type, 'Other')

        WITH row

        UNWIND row.relations AS rel
        MERGE (s:Entity {name: rel.source})
        MERGE (t:Entity {name: rel.target})
        MERGE (s)-[:REL {type: rel.type}]->(t)
        """

    tx.run(q, rows=rows)


def write_with_retries(session, rows: List[Dict[str, Any]]) -> None:
    attempt = 0
    while True:
        try:
            session.execute_write(import_tx, rows)
            return
        except (TransientError, ServiceUnavailable) as e:
            attempt += 1
            if attempt > MAX_RETRIES:
                raise
            backoff = min(60.0, 2.0 * attempt)
            print(f"[WARN] Neo4j write failed (attempt {attempt}/{MAX_RETRIES}): {e}")
            print(f"[WARN] retrying in {backoff:.1f}s ...")
            time.sleep(backoff)


def main() -> None:
    require_env()
    if not os.path.exists(INPUT_PATH):
        raise SystemExit(f"[ERROR] Input not found: {INPUT_PATH}")

    processed = load_processed_ids(PROCESSED_IDS_PATH)

    print(f"[INFO] Neo4j: {NEO4J_URI}")
    print(f"[INFO] Input: {INPUT_PATH}")
    print(f"[INFO] Batch size: {BATCH_SIZE}")
    print(f"[INFO] Max relations per chunk: {MAX_RELATIONS_PER_CHUNK}")
    print(f"[INFO] Write mentions: {WRITE_MENTIONS}")
    print(f"[INFO] Store relations JSON on Chunk: {STORE_RELATIONS_JSON}")
    print(f"[INFO] Already processed: {len(processed)}")
    print(f"[INFO] Processed IDs file: {PROCESSED_IDS_PATH}")

    driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USER, NEO4J_PASSWORD),
        connection_timeout=30,
        max_connection_pool_size=20,
        max_transaction_retry_time=120,
    )

    new_done = 0
    try:
        with driver.session() as session:
            for raw_batch in jsonl_batches(INPUT_PATH, BATCH_SIZE):
                rows: List[Dict[str, Any]] = []
                ids: List[str] = []

                for obj in raw_batch:
                    row = normalize_row(obj)
                    if not row:
                        continue
                    cid = row["chunk_id"]
                    if cid in processed:
                        continue
                    rows.append(row)
                    ids.append(cid)

                if not rows:
                    continue

                write_with_retries(session, rows)

                append_processed_ids(PROCESSED_IDS_PATH, ids)
                processed.update(ids)

                new_done += len(rows)
                print(f"[INFO] Imported +{len(rows)} (total new: {new_done})")

                if SLEEP_SEC > 0:
                    time.sleep(SLEEP_SEC)

    finally:
        driver.close()

    print(f"[INFO] Done. Newly imported: {new_done}")


if __name__ == "__main__":
    main()
