#!/usr/bin/env python3
"""
embed_to_jsonl.py

Step 2 von 2:
- Liest Chunks aus E:\fh_chunks_clean.jsonl (id, text, metadata)
- Erzeugt Embeddings mit einem Embedding-Modell (z.B. OpenAI)
- Schreibt Ergebnis nach E:\fh_chunks_embedded.jsonl
- Nutzt E:\processed_embeddings.txt als Fortschritts-Tracker (Resume-fähig)

Verwendung (Beispiel):
    python embed_to_jsonl.py --model "text-embedding-3-small" --batch-size 32
"""

import os
import argparse
import json
import time
from typing import List, Dict, Any, Set

from openai import OpenAI
from openai import APIError, RateLimitError, APITimeoutError  # optional für genauere Fehlerbehandlung

# Feste Pfade (analog zu deinem preprocess-Script)
INPUT_PATH = r"E:\fh_chunks_clean.jsonl"
OUTPUT_PATH = r"E:\fh_chunks_embedded.jsonl"
PROCESSED_EMB_LIST = r"E:\processed_embeddings.txt"



# Fortschritt / bereits eingebettete IDs laden/speichern


def load_processed_ids() -> Set[str]:
    """
    Lädt IDs aus PROCESSED_EMB_LIST und (falls vorhanden) aus OUTPUT_PATH.
    So können wir auch dann sauber resumieren, wenn z.B. mal eine ID
    in der Output-Datei steht, aber nicht in der Liste.
    """
    processed: Set[str] = set()

    # 1) Aus Textdatei lesen
    if os.path.exists(PROCESSED_EMB_LIST):
        with open(PROCESSED_EMB_LIST, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    processed.add(line)

    # 2) Aus bereits vorhandener Embedded-JSONL lesen
    if os.path.exists(OUTPUT_PATH):
        with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                cid = obj.get("id")
                if cid:
                    processed.add(cid)

    return processed


def append_processed_ids(ids: List[str]) -> None:
    """
    Anhängen neuer eingebetteter IDs an PROCESSED_EMB_LIST.
    """
    if not ids:
        return
    with open(PROCESSED_EMB_LIST, "a", encoding="utf-8") as f:
        for cid in ids:
            f.write(cid + "\n")



# Embedding-Client (z.B. OpenAI)


def get_embedding_client() -> Any:
    """
    Erzeuge den Embedding-Client (hier OpenAI).
    Erwartet, dass OPENAI_API_KEY als Umgebungsvariable gesetzt ist.
    """
    return OpenAI()


def embed_batch(
    client: Any,
    texts: List[str],
    model: str,
    max_retries: int = 5,
    retry_backoff_sec: float = 2.0,
) -> List[List[float]]:
    """
    Erzeugt Embeddings für eine Liste von Texten (Batch).
    Mit einfachem Retry-Mechanismus bei Rate Limits / Zeitüberschreitung.

    Liefert eine Liste von Embedding-Vektoren (gleiche Reihenfolge wie texts).
    """
    attempt = 0
    while True:
        try:
            response = client.embeddings.create(
                model=model,
                input=texts,
            )
            # OpenAI-Python-Client: response.data[i].embedding
            return [item.embedding for item in response.data]
        except (RateLimitError, APITimeoutError, APIError) as e:
            attempt += 1
            if attempt > max_retries:
                raise
            print(f"[WARN] Embedding-Request fehlgeschlagen (Versuch {attempt}/{max_retries}): {e}")
            time.sleep(retry_backoff_sec * attempt)
        except Exception as e:
            # Unerwarteter Fehler
            raise e



# Hauptlogik: fh_chunks.jsonl -> fh_chunks_embedded.jsonl


def embed_to_jsonl(model: str, batch_size: int = 32) -> None:
    if not os.path.exists(INPUT_PATH):
        print(f"[ERROR] Input-Datei nicht gefunden: {INPUT_PATH}")
        return

    os.makedirs(os.path.dirname(os.path.abspath(OUTPUT_PATH)), exist_ok=True)

    print(f"[INFO] Input:  {INPUT_PATH}")
    print(f"[INFO] Output: {OUTPUT_PATH}")
    print(f"[INFO] Modell: {model}")
    print(f"[INFO] Batch-Größe: {batch_size}")
    print(f"[INFO] Fortschrittsdatei: {PROCESSED_EMB_LIST}")

    # Bereits eingebettete IDs laden
    processed_ids = load_processed_ids()
    print(f"[INFO] Bereits eingebettete Chunks (IDs): {len(processed_ids)}")

    client = get_embedding_client()

    total_input_lines = 0
    newly_embedded = 0

    batch_records: List[Dict[str, Any]] = []  # hält die JSON-Objekte
    batch_texts: List[str] = []               # hält die Texte für Embeddings
    batch_ids: List[str] = []                 # die zugehörigen IDs

    # Output im Append-Modus öffnen
    with open(OUTPUT_PATH, "a", encoding="utf-8") as out_f, \
         open(INPUT_PATH, "r", encoding="utf-8") as in_f:

        for line in in_f:
            total_input_lines += 1

            try:
                obj = json.loads(line)
            except Exception:
                # kaputte Zeile einfach überspringen
                continue

            cid = obj.get("id")
            text = obj.get("text") or obj.get("page_content") or ""

            if not cid:
                # ohne ID schwer eindeutig zu tracken → überspringen
                continue

            if cid in processed_ids:
                # Diese ID wurde bereits eingebettet und geschrieben
                continue

            # In Batch einreihen
            batch_records.append(obj)
            batch_texts.append(text)
            batch_ids.append(cid)

            # Falls Batch voll → Embedding anfragen
            if len(batch_records) >= batch_size:
                embeddings = embed_batch(client, batch_texts, model=model)

                # Embeddings anhängen und schreiben
                for rec, emb in zip(batch_records, embeddings):
                    rec["embedding"] = emb
                    out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")

                newly_embedded += len(batch_records)
                # IDs zur processed-Liste hinzufügen (im Speicher + Datei)
                for cid_done in batch_ids:
                    processed_ids.add(cid_done)
                append_processed_ids(batch_ids)

                print(f"[INFO] Neu eingebettete Chunks: {newly_embedded} "
                      f"(verarbeitete Inputzeilen: {total_input_lines})")

                # Batch leeren
                batch_records.clear()
                batch_texts.clear()
                batch_ids.clear()

        # Rest-Batch (falls < batch_size) noch verarbeiten
        if batch_records:
            embeddings = embed_batch(client, batch_texts, model=model)
            for rec, emb in zip(batch_records, embeddings):
                rec["embedding"] = emb
                out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")

            newly_embedded += len(batch_records)
            for cid_done in batch_ids:
                processed_ids.add(cid_done)
            append_processed_ids(batch_ids)

            print(f"[INFO] Neu eingebettete Chunks (inkl. Rest-Batch): {newly_embedded}")

    print(f"[INFO] Fertig.")
    print(f"[INFO] Insgesamt neu eingebettet: {newly_embedded}")
    print(f"[INFO] Gesamtzahl eingebetteter IDs (inkl. früherer Läufe): {len(processed_ids)}")



# CLI


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Embedding-Phase für fh_chunks.jsonl → fh_chunks_embedded.jsonl")
    p.add_argument(
        "--model",
        required=True,
        help="Embedding-Modell-Name (z.B. text-embedding-3-small)",
    )
    p.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch-Größe pro Embedding-Request (Default: 32)",
    )
    return p


if __name__ == "__main__":
    parser = build_arg_parser()
    args = parser.parse_args()

    embed_to_jsonl(
        model=args.model,
        batch_size=args.batch_size,
    )

