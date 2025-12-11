#!/usr/bin/env python3
"""
preprocess_to_jsonl.py

Step 1 of 2:
- Lädt Dateien mit Docling + HybridChunker
- Erzeugt Text-Chunks (LangChain Document)
- Speichert sie als JSONL (eine Zeile pro Chunk)

WICHTIG:
- Ausgabe nach E:\fh_chunks.jsonl fest eingestellt.
- Verarbeitete Dateien werden in E:\processed_files.txt protokolliert,
  sodass ein Neustart dort weitermacht, wo der letzte Lauf aufgehört hat.
"""

import os
import argparse
import json
import hashlib
import re
from typing import List, Set

from langchain_core.documents import Document
from docling.chunking import HybridChunker
from langchain_docling import DoclingLoader


OUTPUT_PATH = r"E:\fh_chunks.jsonl"
PROCESSED_LIST = r"E:\processed_files.txt"


# ------------------------------------------------------------
# Dateien einsammeln
# ------------------------------------------------------------

def collect_files(root: str) -> List[str]:
    file_paths: List[str] = []
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            if fname.lower().endswith(
                (
                    ".pdf",
                    ".html", ".htm",
                    ".docx",
                    ".pptx",
                    ".txt",
                )
            ):
                full = os.path.join(dirpath, fname)

                # >>> PROBLEMDATEI(N) HART AUSSCHLIESSEN <<<
                if os.path.basename(full) == "FPO_2018_WiIng_WiInf_IBE_IBI.pdf":
                    print(f"[WARN] Problematische Datei übersprungen: {full}")
                    continue

                file_paths.append(full)
    return file_paths


# ------------------------------------------------------------
# Text-Normalisierung & Signaturen für Near-Dedup
# ------------------------------------------------------------

def _normalize_text(text: str) -> str:
    """
    Grobe Normalisierung für Signaturen:
    - lowercase
    - Whitespace zusammenfassen
    - vorne/hinten trimmen
    """
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    text = text.strip()
    return text


def make_signature(text: str) -> str:
    """
    Erzeuge eine Signatur für Near-Duplicate-Erkennung.
    - Nur Chunks mit >= 50 Zeichen werden berücksichtigt
    - Signatur = erste 120 Zeichen des normalisierten Textes
    """
    norm = _normalize_text(text or "")
    if len(norm) < 50:
        return ""  # zu kurz → nicht deduplizieren
    return norm[:120]


# ------------------------------------------------------------
# Chunk-ID (stabil & deterministisch)
# ------------------------------------------------------------

def compute_chunk_id(doc: Document, idx: int) -> str:
    """
    Bilde eine stabile ID aus:
    - Quelle (metadata['source'] / metadata['file_path'])
    - Chunk-Index
    - Textinhalt
    """
    source = (
        doc.metadata.get("source")
        or doc.metadata.get("file_path")
        or "unknown_source"
    )
    base = f"{source}::chunk_{idx}::{doc.page_content}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()


# ------------------------------------------------------------
# Verarbeitete Dateien laden/speichern (Resume-Mechanismus)
# ------------------------------------------------------------

def load_processed_files() -> Set[str]:
    if not os.path.exists(PROCESSED_LIST):
        return set()
    processed: Set[str] = set()
    with open(PROCESSED_LIST, "r", encoding="utf-8") as f:
        for line in f:
            path = line.strip()
            if path:
                processed.add(path)
    return processed


def save_processed_file(path: str) -> None:
    with open(PROCESSED_LIST, "a", encoding="utf-8") as f:
        f.write(path + "\n")


# ------------------------------------------------------------
# Docling + HybridChunker (mit Fehler-Schutz & Dedup & Resume)
# ------------------------------------------------------------

def preprocess_to_jsonl(path: str, output_path: str, export_type: str = "markdown") -> None:
    # 1) Quellen vorbereiten
    if os.path.isdir(path):
        sources = collect_files(path)
        if not sources:
            print(f"[WARN] Keine unterstützten Dateien unter {path} gefunden.")
            return
        print(f"[INFO] {len(sources)} Dateien gefunden.")
    else:
        sources = [path]
        print(f"[INFO] Einzeldatei: {path}")

    # --- WICHTIG: Output-Pfad überschreiben ---
    output_path = OUTPUT_PATH
    print(f"[INFO] Ausgabe: {output_path}")

    # 2) Output-Ordner erzeugen
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    # --------------------------------------------------------
    #  Bestehende Signaturen aus vorhandener JSONL laden
    #  → verhindert Duplikate über mehrere Läufe hinweg
    # --------------------------------------------------------
    seen_signatures: Set[str] = set()
    count = 0

    if os.path.exists(output_path):
        print(f"[INFO] Bestehende Ausgabe gefunden – lade Signaturen für Dedup...")
        with open(output_path, "r", encoding="utf-8") as f_in:
            for line in f_in:
                try:
                    obj = json.loads(line)
                    text = obj.get("text") or obj.get("page_content") or ""
                    sig = make_signature(text)
                    if sig:
                        seen_signatures.add(sig)
                    count += 1
                except Exception:
                    # Falls mal eine Zeile kaputt wäre → einfach überspringen
                    continue
        print(f"[INFO] {count} bestehende Chunks, {len(seen_signatures)} Signaturen geladen.")

    # --------------------------------------------------------
    #  Bereits vollständig verarbeitete Dateien laden
    # --------------------------------------------------------
    processed_files = load_processed_files()
    if processed_files:
        print(f"[INFO] {len(processed_files)} bereits verarbeitete Dateien gefunden "
              f"({PROCESSED_LIST}).")

    # 3) Neue Chunks anhängen (Append)
    new_chunks = 0
    skipped_duplicates = 0

    with open(output_path, "a", encoding="utf-8") as out_f:

        # --------------------------------------------------------
        #  ITERATION MIT try/except → Fehlerhafte Dateien skippen
        # --------------------------------------------------------
        for file_idx, file_path in enumerate(sources):
            if file_path in processed_files:
                print(f"[INFO] Datei bereits verarbeitet, überspringe: {file_path}")
                continue

            print(f"[INFO] Verarbeite Datei {file_idx+1}/{len(sources)}: {file_path}")

            try:
                loader = DoclingLoader(
                    file_path=file_path,
                    export_type=export_type,
                    chunker=HybridChunker(),
                )

                # lazy_load liefert mehrere Chunks je Datei
                for idx, doc in enumerate(loader.lazy_load()):
                    if not isinstance(doc, Document):
                        continue

                    text = doc.page_content or ""
                    sig = make_signature(text)

                    # --- Near-Dedup: Chunk überspringen, wenn Signatur schon bekannt ---
                    if sig and sig in seen_signatures:
                        skipped_duplicates += 1
                        continue

                    if sig:
                        seen_signatures.add(sig)

                    chunk_id = compute_chunk_id(doc, idx)
                    record = {
                        "id": chunk_id,
                        "text": text,
                        "metadata": doc.metadata or {},
                    }
                    out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
                    count += 1
                    new_chunks += 1

                    if count % 100 == 0:
                        print(f"[INFO] {count} Chunks insgesamt geschrieben...")

                # Wenn wir die Datei ohne Exception komplett geschafft haben:
                save_processed_file(file_path)
                processed_files.add(file_path)
                print(f"[INFO] Datei als verarbeitet markiert: {file_path}")

            except Exception as e:
                print(f"[ERROR] Datei übersprungen wegen Fehler: {file_path}")
                print(f"        → {e}")
                # NICHT als verarbeitet markieren, damit du beim nächsten Lauf erneut versuchen kannst
                continue  # Nächste Datei

    print(f"[INFO] Fertig.")
    print(f"[INFO] Neu hinzugefügte Chunks: {new_chunks}")
    print(f"[INFO] Übersprungene Near-Duplikate: {skipped_duplicates}")
    print(f"[INFO] Insgesamt {count} Chunks in {output_path} gespeichert.")


# ------------------------------------------------------------
# CLI
# ------------------------------------------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Docling + HybridChunker → JSONL Preprocessing")
    p.add_argument(
        "--path",
        required=True,
        help="Ordner oder Datei (z.B. E:\\FH_Crawler_Downloads)",
    )
    p.add_argument(
        "--output",
        required=False,        # ← wird ignoriert, da fix auf E:\fh_chunks.jsonl
        default="IGNORED",
        help="(IGNORED – Ausgabe immer E:\\fh_chunks.jsonl)",
    )
    p.add_argument(
        "--export-type",
        default="markdown",
        help="Docling export_type (default: markdown)",
    )
    return p


if __name__ == "__main__":
    parser = build_arg_parser()
    args = parser.parse_args()

    preprocess_to_jsonl(
        path=args.path,
        output_path="IGNORED",
        export_type=args.export_type,
    )



