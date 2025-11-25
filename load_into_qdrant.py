#!/usr/bin/env python3
import json
import argparse
from typing import List, Dict, Any
from uuid import uuid5, NAMESPACE_URL  # NEW: für stabile, gültige UUIDs

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct


def create_collection_if_not_exists(
    client: QdrantClient,
    collection_name: str,
    vector_size: int,
    distance: Distance = Distance.COSINE,
):
    """
    Legt eine Qdrant-Collection an, falls sie noch nicht existiert.
    """
    existing = [c.name for c in client.get_collections().collections]
    if collection_name in existing:
        print(f"Collection '{collection_name}' existiert bereits.")
        return

    print(
        f"Erstelle Collection '{collection_name}' "
        f"(Vektorgröße={vector_size}, Distance={distance})..."
    )
    # Verwende create_collection (recreate_collection ist deprecated)
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=distance),
    )
    print("Collection angelegt.")


def load_jsonl(jsonl_path: str) -> List[Dict[str, Any]]:
    """
    Liest eine JSONL-Datei (eine JSON-Zeile pro Dokument) in eine Liste von Dicts.
    """
    docs: List[Dict[str, Any]] = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line_idx, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"Überspringe Zeile {line_idx}: JSON-Fehler: {e}")
                continue
            docs.append(obj)
    return docs


def batch(iterable, batch_size: int):
    """
    Hilfsfunktion für Batch-Bildung.
    """
    current = []
    for item in iterable:
        current.append(item)
        if len(current) >= batch_size:
            yield current
            current = []
    if current:
        yield current


def import_to_qdrant(
    qdrant_url: str,
    qdrant_api_key: str,
    collection_name: str,
    jsonl_path: str,
    batch_size: int = 128,
):
    # Qdrant-Client initialisieren – CLOUD ONLY
    if not qdrant_url.startswith("https://"):
        print(
            f"[WARN] qdrant-url '{qdrant_url}' sieht nicht nach einer Qdrant-Cloud-URL aus "
            f"(erwarte https://...)."
        )

    if not qdrant_api_key:
        raise ValueError(
            "Für Qdrant Cloud ist ein API-Key erforderlich (Argument --qdrant-api-key)."
        )

    print(f"Verbinde zu Qdrant Cloud: {qdrant_url}")
    client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)

    print(f"Lese JSONL-Datei: {jsonl_path}")
    docs = load_jsonl(jsonl_path)
    if not docs:
        print("Keine Dokumente in JSONL gefunden.")
        return

    # Vektorgröße aus dem ersten Dokument bestimmen
    first_emb = docs[0].get("embedding", [])
    if not first_emb:
        raise ValueError(
            "Erstes Dokument hat kein 'embedding'-Feld. Kann Vektorgröße nicht bestimmen."
        )

    vector_size = len(first_emb)
    print(f"Ermittelte Embedding-Vektorgröße: {vector_size}")

    # Collection anlegen, falls nötig
    create_collection_if_not_exists(client, collection_name, vector_size)

    total_docs = len(docs)
    print(f"Importiere {total_docs} Dokumente in Collection '{collection_name}'...")

    point_count = 0
    new_points_count = 0  # NEW: wie viele wirklich neue Punkte eingefügt wurden

    for batch_idx, docs_batch in enumerate(batch(docs, batch_size), start=1):
        # 1) Für alle Dokumente in diesem Batch stabile IDs berechnen
        prepared = []
        ids_for_check = []
        for doc in docs_batch:
            emb = doc.get("embedding")
            text = doc.get("text", "")
            metadata = doc.get("metadata", {})
            original_id = doc.get("id")  # ursprüngliche ID aus output.jsonl

            if emb is None or original_id is None:
                continue

            # Stabile, gültige UUID aus original_id erzeugen:
            # Gleiches original_id -> gleiche UUID bei jedem Lauf
            point_id = str(uuid5(NAMESPACE_URL, str(original_id)))

            prepared.append(
                {
                    "point_id": point_id,
                    "emb": emb,
                    "text": text,
                    "metadata": metadata,
                    "original_id": original_id,
                }
            )
            ids_for_check.append(point_id)

        if not prepared:
            continue

        # 2) Abfragen, welche IDs bereits in Qdrant existieren
        existing_points = client.retrieve(
            collection_name=collection_name,
            ids=ids_for_check,
            with_payload=False,
        )
        existing_ids = {p.id for p in existing_points}

        # 3) Nur Punkte erstellen, deren ID noch nicht existiert
        points: List[PointStruct] = []
        for item in prepared:
            if item["point_id"] in existing_ids:
                # Punkt existiert bereits -> überspringen (keine Duplikate)
                continue

            payload = {
                "text": item["text"],
                "metadata": item["metadata"],
                "original_id": item["original_id"],
            }

            points.append(
                PointStruct(
                    id=item["point_id"],
                    vector=item["emb"],
                    payload=payload,
                )
            )

        if not points:
            print(
                f"Batch {batch_idx}: Keine neuen Punkte (alle IDs existieren bereits)."
            )
            continue

        # 4) Nur neue Punkte upserten
        client.upsert(
            collection_name=collection_name,
            points=points,
            wait=True,
        )
        batch_new = len(points)
        new_points_count += batch_new
        point_count += len(prepared)  # alle gesehenen in diesem Batch

        print(
            f"Batch {batch_idx}: {batch_new} neue Punkte eingefügt "
            f"(insgesamt neu: {new_points_count})"
        )

    print(
        f"Import abgeschlossen. Insgesamt {new_points_count} neue Punkte "
        f"in Collection '{collection_name}' eingefügt."
    )


def main():
    parser = argparse.ArgumentParser(
        description="Importiert JSONL-Embeddings in eine Qdrant-Collection (Cloud, ohne Duplikate)"
    )
    parser.add_argument(
        "--qdrant-url",
        type=str,
        required=True,
        help=(
            "Qdrant-Cloud-URL, z.B. "
            "https://xxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.eu-central-1-0.aws.cloud.qdrant.io"
        ),
    )
    parser.add_argument(
        "--qdrant-api-key",
        type=str,
        required=True,
        help="Qdrant-Cloud API-Key (Pflicht für Cloud-Nutzung)",
    )
    parser.add_argument(
        "--collection-name",
        type=str,
        required=True,
        help="Name der Qdrant-Collection",
    )
    parser.add_argument(
        "--jsonl-path",
        type=str,
        required=True,
        help="Pfad zur output.jsonl-Datei aus pipeline.py",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=128,
        help="Batchgröße für Upserts",
    )

    args = parser.parse_args()

    import_to_qdrant(
        qdrant_url=args.qdrant_url,
        qdrant_api_key=args.qdrant_api_key,
        collection_name=args.collection_name,
        jsonl_path=args.jsonl_path,
        batch_size=args.batch_size,
    )


if __name__ == "__main__":
   
    import sys
    sys.argv = [
        "load_into_qdrant.py",
        "--qdrant-url",
        "https://bd57a360-2b9c-4262-893b-34b50d9c058a.eu-central-1-0.aws.cloud.qdrant.io",  # 
        "--qdrant-api-key",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.6CBvSFXnVaEMymgWfyOUL4LZShwqwgTrBJVYmrmxxPw",  # 
        "--collection-name",
        "fh_rag_data",
        "--jsonl-path",
        r"C:\Users\liont\OneDrive\Documents\Datenvorbereitung\output.jsonl",
    ]
    main()




