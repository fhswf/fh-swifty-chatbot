#!/usr/bin/env python3
"""
load_into_neo4j.py

Lädt Chunks aus einer eingebetteten JSONL-Datei (z.B. E:\\fh_chunks_embedded.jsonl)
in eine Neo4j-Datenbank (z.B. Neo4j Aura in der Cloud) als :Chunk-Knoten.

Jede Zeile der JSONL wird erwartet als JSON-Objekt mit mindestens:
- id (str)
- text oder page_content (str)
- embedding (Liste[float])
- optional: metadata (dict oder beliebige zusätzliche Felder)

Verwendung (Beispiel):

    python load_into_neo4j.py ^
        --uri "neo4j+s://<dein-cluster>.databases.neo4j.io" ^
        --user "neo4j" ^
        --password "dein_passwort" ^
        --input-path "E:\\fh_chunks_embedded.jsonl" ^
        --batch-size 500

Tipp: Zugangsdaten besser als Umgebungsvariablen setzen:

    set NEO4J_URI=neo4j+s://<...>
    set NEO4J_USER=neo4j
    set NEO4J_PASSWORD=dein_passwort

Dann kannst du --uri / --user / --password weglassen.
"""

import os
import json
import argparse
from typing import Any, Dict, List, Optional

from neo4j import GraphDatabase, Driver


# Standard-Pfade (an deine Umgebung angepasst)
DEFAULT_INPUT_PATH = r"E:\fh_chunks_embedded.jsonl"


def get_driver(uri: str, user: str, password: str) -> Driver:
    """
    Erzeuge einen Neo4j-Driver.
    """
    driver = GraphDatabase.driver(uri, auth=(user, password))
    return driver


def load_jsonl_in_batches(
    input_path: str,
    batch_size: int = 500,
):
    """
    Generator, der die JSONL-Datei in Batches von Dictionaries liest.
    """
    batch: List[Dict[str, Any]] = []

    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                # kaputte Zeile überspringen
                continue

            batch.append(obj)

            if len(batch) >= batch_size:
                yield batch
                batch = []

    if batch:
        # Restbatch
        yield batch


def normalize_record(obj: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Normiert ein JSON-Objekt aus der Datei auf eine einheitliche Struktur.

    Erwartet:
    - id
    - embedding
    - text oder page_content
    - optional metadata (dict)

    Gibt None zurück, wenn Mindestanforderungen fehlen.
    """
    cid = obj.get("id")
    if not cid:
        return None

    embedding = obj.get("embedding")
    if not isinstance(embedding, list) or not embedding:
        # ohne Embedding brauchen wir den Knoten für RAG nicht
        return None

    text = obj.get("text") or obj.get("page_content") or ""

    metadata = obj.get("metadata")
    # Nur echte Dicts akzeptieren, alles andere ignorieren
    if not isinstance(metadata, dict):
        metadata = None

    record = {
        "id": cid,
        "text": text,
        "embedding": embedding,
        "metadata": metadata,
    }

    return record


def create_chunks_tx(tx, rows: List[Dict[str, Any]]):
    """
    Führt die eigentliche Cypher-Query aus, um Knoten zu erstellen/zu updaten.

    Wir nutzen MERGE auf :Chunk {id}, damit ein erneuter Lauf
    nicht doppelte Knoten erzeugt, sondern vorhandene aktualisiert.

    - id, text, embedding werden immer gesetzt
    - metadata (falls vorhanden) wird auf einzelne Properties verteilt (SET c += row.metadata)
    """
    query = """
    UNWIND $rows AS row
    MERGE (c:Chunk {id: row.id})
    SET c.text = row.text,
        c.embedding = row.embedding
    WITH c, row
    WHERE row.metadata IS NOT NULL
    SET c += row.metadata
    """
    tx.run(query, rows=rows)


def load_into_neo4j(
    uri: str,
    user: str,
    password: str,
    input_path: str,
    batch_size: int = 500,
    database: Optional[str] = None,
    dry_run: bool = False,
) -> None:
    """
    Hauptfunktion: Verbindet sich zu Neo4j, liest die JSONL-Datei in Batches und
    schreibt die Daten als :Chunk-Knoten in die DB.
    """
    if not os.path.exists(input_path):
        print(f"[ERROR] Input-Datei nicht gefunden: {input_path}")
        return

    print(f"[INFO] Verbinde zu Neo4j: {uri}")
    driver = get_driver(uri, user, password)

    total_records = 0
    total_batches = 0

    try:
        with driver.session(database=database) if database else driver.session() as session:
            for raw_batch in load_jsonl_in_batches(input_path, batch_size=batch_size):
                # Normierung
                rows: List[Dict[str, Any]] = []
                for obj in raw_batch:
                    rec = normalize_record(obj)
                    if rec:
                        rows.append(rec)

                if not rows:
                    continue

                total_batches += 1
                total_records += len(rows)

                if dry_run:
                    print(f"[DRY-RUN] Würde Batch {total_batches} mit {len(rows)} Records schreiben.")
                else:
                    session.execute_write(create_chunks_tx, rows)
                    print(f"[INFO] Batch {total_batches} geschrieben ({len(rows)} Knoten).")

    finally:
        driver.close()

    print(f"[INFO] Fertig.")
    print(f"[INFO] Gesamtzahl verarbeiteter Records: {total_records}")
    print(f"[INFO] Anzahl Batches: {total_batches}")


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Lädt fh_chunks_embedded.jsonl in Neo4j als Vektorknoten (:Chunk).")

    p.add_argument(
        "--uri",
        default=os.getenv("NEO4J_URI"),
        help="Neo4j URI, z.B. neo4j+s://<cluster>.databases.neo4j.io (oder via NEO4J_URI Env-Var).",
    )
    p.add_argument(
        "--user",
        default=os.getenv("NEO4J_USER"),
        help="Neo4j Benutzername (oder via NEO4J_USER Env-Var).",
    )
    p.add_argument(
        "--password",
        default=os.getenv("NEO4J_PASSWORD"),
        help="Neo4j Passwort (oder via NEO4J_PASSWORD Env-Var).",
    )
    p.add_argument(
        "--input-path",
        default=DEFAULT_INPUT_PATH,
        help=f"Pfad zur eingebetteten JSONL-Datei (Default: {DEFAULT_INPUT_PATH})",
    )
    p.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Batch-Größe für Writes nach Neo4j (Default: 500)",
    )
    p.add_argument(
        "--database",
        default=None,
        help="Optionaler Datenbankname (für Neo4j 4.x/5.x Multi-DB, z.B. 'neo4j').",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Wenn gesetzt, werden keine Writes ausgeführt, nur gezählt.",
    )

    return p


if __name__ == "__main__":
    parser = build_arg_parser()
    args = parser.parse_args()

    if not args.uri or not args.user or not args.password:
        print("[ERROR] Bitte --uri, --user und --password angeben oder Umgebungsvariablen NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD setzen.")
    else:
        load_into_neo4j(
            uri=args.uri,
            user=args.user,
            password=args.password,
            input_path=args.input_path,
            batch_size=args.batch_size,
            database=args.database,
            dry_run=args.dry_run,
        )

