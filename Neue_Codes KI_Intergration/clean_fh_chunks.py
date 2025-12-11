#!/usr/bin/env python3
"""
clean_fh_chunks.py

Reinigung & Normalisierung für fh_chunks.jsonl:

- Input:  E:\\fh_chunks.jsonl
- Output: E:\\fh_chunks_clean.jsonl

Funktionen:
- Leere Chunks (Textlänge 0 nach Trimmen) werden entfernt.
- Sehr große Chunks werden in kleinere Teilchunks aufgeteilt (Standard: max. 4000 Zeichen).
- Text wird leicht normalisiert (Zeilenumbrüche vereinheitlicht, Whitespace pro Zeile bereinigt).
- IDs von gesplitteten Chunks bekommen einen Suffix '::<part_n>'.

Verwendung (Beispiel):
    python clean_fh_chunks.py --max-chars 4000
"""

import os
import argparse
import json
import re
from typing import List, Dict, Any

INPUT_PATH = r"E:\fh_chunks.jsonl"
OUTPUT_PATH = r"E:\fh_chunks_clean.jsonl"


# ------------------------------------------------------------
# Text-Normalisierung
# ------------------------------------------------------------

def normalize_text(text: str) -> str:
    """
    Leichte Normalisierung:
    - Windows-Zeilenenden -> '\n'
    - pro Zeile: Tabs/mehrere Spaces zu einem Space reduzieren
    - vorne/hinten trimmen
    """
    if not text:
        return ""

    # Zeilenenden vereinheitlichen
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # pro Zeile Whitespace bereinigen
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        # Tabs und mehrere Spaces zu einem Space
        line = re.sub(r"[ \t]+", " ", line)
        cleaned_lines.append(line.strip())

    # wieder zusammenfügen, leere Zeilen bleiben als leere Zeilen bestehen
    cleaned = "\n".join(cleaned_lines).strip()
    return cleaned


# ------------------------------------------------------------
# Chunk-Splitting
# ------------------------------------------------------------

def split_text_into_chunks(text: str, max_chars: int) -> List[str]:
    """
    Teilt einen sehr großen Text in kleinere Chunks auf.
    Heuristik:
    1. Versuche, nach Absätzen (\n\n) zu gruppieren.
    2. Wenn ein Absatz zu groß ist, versuche Satzebene (.?!).
    3. Wenn ein Satz immer noch zu groß ist, hart nach max_chars splitten.

    Liefert eine Liste von Teilstrings, jeweils <= max_chars Zeichen.
    """
    if len(text) <= max_chars:
        return [text]

    chunks: List[str] = []

    # 1) Erst nach Absätzen splitten
    paragraphs = re.split(r"\n{2,}", text)  # Blöcke, die durch >=2 Newlines getrennt sind

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(para) <= max_chars:
            # versuche, mehrere kleinere Absätze zusammenzupacken
            if chunks and len(chunks[-1]) + len("\n\n") + len(para) <= max_chars:
                chunks[-1] = chunks[-1] + "\n\n" + para
            else:
                chunks.append(para)
        else:
            # 2) Absatz ist immer noch zu groß → nach Sätzen splitten
            sentences = re.split(r"(?<=[.!?])\s+", para)
            current = ""
            for sent in sentences:
                sent = sent.strip()
                if not sent:
                    continue

                if len(sent) > max_chars:
                    # 3) Ein Satz alleine ist schon zu groß → hart splitten
                    if current:
                        chunks.append(current)
                        current = ""
                    start = 0
                    while start < len(sent):
                        part = sent[start:start + max_chars]
                        chunks.append(part)
                        start += max_chars
                    continue

                if not current:
                    current = sent
                elif len(current) + 1 + len(sent) <= max_chars:
                    current = current + " " + sent
                else:
                    chunks.append(current)
                    current = sent

            if current:
                chunks.append(current)

    # Sicherheitscheck: falls trotz allem ein Chunk zu groß ist, hart splitten
    final_chunks: List[str] = []
    for ch in chunks:
        if len(ch) <= max_chars:
            final_chunks.append(ch)
        else:
            start = 0
            while start < len(ch):
                final_chunks.append(ch[start:start + max_chars])
                start += max_chars

    return final_chunks


# ------------------------------------------------------------
# Hauptlogik: fh_chunks.jsonl -> fh_chunks_clean.jsonl
# ------------------------------------------------------------

def clean_chunks(input_path: str, output_path: str, max_chars: int) -> None:
    if not os.path.exists(input_path):
        print(f"[ERROR] Input-Datei nicht gefunden: {input_path}")
        return

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    print(f"[INFO] Input:  {input_path}")
    print(f"[INFO] Output: {output_path}")
    print(f"[INFO] Max. Chunk-Länge: {max_chars} Zeichen")

    total_in = 0
    total_out = 0
    removed_empty = 0
    split_counter = 0
    unchanged_counter = 0

    with open(input_path, "r", encoding="utf-8") as fin, \
         open(output_path, "w", encoding="utf-8") as fout:

        for line in fin:
            total_in += 1
            try:
                obj: Dict[str, Any] = json.loads(line)
            except Exception:
                # kaputte Zeile überspringen
                continue

            cid = obj.get("id")
            text = obj.get("text") or obj.get("page_content") or ""
            metadata = obj.get("metadata") or {}

            # Normalisieren
            norm_text = normalize_text(text)

            # Leere Chunks entfernen
            if not norm_text:
                removed_empty += 1
                continue

            if len(norm_text) <= max_chars:
                # Chunk unverändert (bis auf Normalisierung)
                obj["text"] = norm_text
                # page_content sicherheitshalber konsistent halten
                if "page_content" in obj:
                    obj["page_content"] = norm_text

                fout.write(json.dumps(obj, ensure_ascii=False) + "\n")
                total_out += 1
                unchanged_counter += 1
            else:
                # Großes Chunk → splitten
                sub_chunks = split_text_into_chunks(norm_text, max_chars=max_chars)
                split_counter += 1

                for idx, sub_text in enumerate(sub_chunks):
                    new_obj = dict(obj)  # flache Kopie
                    new_obj["text"] = sub_text
                    if "page_content" in new_obj:
                        new_obj["page_content"] = sub_text

                    # ID anreichern, damit eindeutig und nachvollziehbar
                    if cid:
                        new_obj["id"] = f"{cid}::part_{idx}"
                    else:
                        # Falls keine ID vorhanden (sollte bei dir nicht vorkommen)
                        new_obj["id"] = f"auto_generated_id::{total_in}::{idx}"

                    # Zusätzlich: Metadaten annotieren
                    md = dict(metadata)
                    md["split_from_id"] = cid
                    md["split_part_index"] = idx
                    md["split_total_parts"] = len(sub_chunks)
                    new_obj["metadata"] = md

                    fout.write(json.dumps(new_obj, ensure_ascii=False) + "\n")
                    total_out += 1

    print("[INFO] Reinigung & Normalisierung abgeschlossen.")
    print(f"[INFO] Eingelesene Chunks:         {total_in}")
    print(f"[INFO] Entfernte leere Chunks:     {removed_empty}")
    print(f"[INFO] Chunks, die gesplittet wurden: {split_counter}")
    print(f"[INFO] Unveränderte Chunks:        {unchanged_counter}")
    print(f"[INFO] Ausgegebene Chunks gesamt:  {total_out}")
    print(f"[INFO] Bereinigte Datei:           {output_path}")


# ------------------------------------------------------------
# CLI
# ------------------------------------------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Reinigung & Normalisierung von fh_chunks.jsonl")
    p.add_argument(
        "--input",
        default=INPUT_PATH,
        help=f"Input-JSONL (Standard: {INPUT_PATH})",
    )
    p.add_argument(
        "--output",
        default=OUTPUT_PATH,
        help=f"Output-JSONL (Standard: {OUTPUT_PATH})",
    )
    p.add_argument(
        "--max-chars",
        type=int,
        default=4000,
        help="Maximale Zeichenzahl pro Chunk (Standard: 4000)",
    )
    return p


if __name__ == "__main__":
    parser = build_arg_parser()
    args = parser.parse_args()

    clean_chunks(
        input_path=args.input,
        output_path=args.output,
        max_chars=args.max_chars,
    )
