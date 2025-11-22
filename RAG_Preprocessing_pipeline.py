#!/usr/bin/env python3
import os
import io
import json
import gzip
import zipfile
import tarfile
import argparse
import math
from dataclasses import dataclass, asdict
from typing import Iterator, List, Dict, Any, Optional

import pdfplumber
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer

# -------------------------------
# Data structures
# -------------------------------

@dataclass
class DocumentChunk:
    id: str
    text: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None


# -------------------------------
# Archive handling
# -------------------------------

def open_archive(archive_path: str):
    """
    Open .zip, .tar, .tar.gz, .tgz, or a plain .gz file.
    Returns a tuple (archive_type, handle).
    """
    lower = archive_path.lower()
    if lower.endswith(".zip"):
        return "zip", zipfile.ZipFile(archive_path, "r")
    elif lower.endswith(".tar") or lower.endswith(".tar.gz") or lower.endswith(".tgz"):
        return "tar", tarfile.open(archive_path, "r:*")
    elif lower.endswith(".gz"):
        # single gzipped file (not an archive with multiple members)
        return "gz", gzip.open(archive_path, "rb")
    else:
        raise ValueError(f"Unsupported archive type for: {archive_path}")


def iter_files_in_archive(archive_path: str) -> Iterator[Dict[str, Any]]:
    """
    Yields dicts with fields:
    - name: str (path inside archive)
    - content_bytes: bytes
    """
    archive_type, handle = open_archive(archive_path)

    if archive_type == "zip":
        with handle as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                with zf.open(info, "r") as f:
                    yield {"name": info.filename, "content_bytes": f.read()}

    elif archive_type == "tar":
        with handle as tf:
            for member in tf.getmembers():
                if not member.isreg():
                    continue
                f = tf.extractfile(member)
                if f is None:
                    continue
                with f:
                    yield {"name": member.name, "content_bytes": f.read()}

    elif archive_type == "gz":
        # Treat as a single compressed file
        with handle as f:
            content_bytes = f.read()
            name = os.path.basename(archive_path).replace(".gz", "")
            yield {"name": name, "content_bytes": content_bytes}


def iter_files_in_directory(root_dir: str) -> Iterator[Dict[str, Any]]:
    """
    Iterate over all files in a directory (recursively).

    Yields dicts with:
    - name: relative path inside the folder
    - content_bytes: raw bytes
    """
    root_dir = os.path.abspath(root_dir)

    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            # Relative path for nicer metadata, e.g. "subfolder/file.pdf"
            rel_path = os.path.relpath(full_path, root_dir)
            with open(full_path, "rb") as f:
                yield {
                    "name": rel_path,
                    "content_bytes": f.read(),
                }


# -------------------------------
# File type specific parsing
# -------------------------------

def safe_decode(b: bytes) -> str:
    try:
        return b.decode("utf-8")
    except UnicodeDecodeError:
        try:
            return b.decode("latin-1")
        except UnicodeDecodeError:
            return b.decode("utf-8", errors="ignore")


def extract_text_from_html(content_bytes: bytes) -> str:
    html = safe_decode(content_bytes)
    soup = BeautifulSoup(html, "html.parser")

    # Remove script/style
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator=" ")
    return text


def extract_text_from_pdf(content_bytes: bytes) -> str:
    text_parts = []
    with pdfplumber.open(io.BytesIO(content_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text_parts.append(page_text)
    return "\n".join(text_parts)


def extract_text_from_json(content_bytes: bytes) -> str:
    txt = safe_decode(content_bytes)
    try:
        data = json.loads(txt)
    except json.JSONDecodeError:
        # maybe JSONL; fallback: return as-is
        return txt

    def extract_from_obj(obj) -> List[str]:
        collected = []
        if isinstance(obj, dict):
            # Heuristics: typical text keys
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    collected.extend(extract_from_obj(v))
                elif isinstance(v, str) and k.lower() in ["text", "content", "body", "message"]:
                    collected.append(v)
        elif isinstance(obj, list):
            for item in obj:
                collected.extend(extract_from_obj(item))
        return collected

    texts = extract_from_obj(data)
    if texts:
        return "\n\n".join(texts)
    else:
        # Fallback: stringified JSON
        return txt


def extract_text_from_plain(content_bytes: bytes) -> str:
    return safe_decode(content_bytes)


def parse_file_to_text(name: str, content_bytes: bytes) -> Optional[str]:
    lower = name.lower()
    if lower.endswith(".html") or lower.endswith(".htm"):
        return extract_text_from_html(content_bytes)
    elif lower.endswith(".pdf"):
        # CHANGED: wrapped PDF parsing in try/except and fixed indentation
        try:
            return extract_text_from_pdf(content_bytes)
        except Exception as e:
            # Log and skip this file
            print(f"[WARN] Error reading PDF '{name}': {e}. Skipping this file.")
            return None
    elif lower.endswith(".json"):
        return extract_text_from_json(content_bytes)
    elif lower.endswith(".txt") or lower.endswith(".md") or lower.endswith(".log"):
        return extract_text_from_plain(content_bytes)
    else:
        # Unknown file type – ignore or treat as plain text
        return None


# -------------------------------
# Cleaning & filtering
# -------------------------------

def clean_text(text: str) -> str:
    # Normalize whitespace
    text = text.replace("\r", " ")
    text = "\n".join(line.strip() for line in text.splitlines())
    # Collapse multiple blank lines
    lines = [ln for ln in text.split("\n") if ln.strip() != ""]
    return "\n".join(lines).strip()


def passes_filter(text: str, min_chars: int = 200) -> bool:
    if not text:
        return False
    if len(text) < min_chars:
        return False
    # Add more filters here (e.g. language detection, blacklist, etc.)
    return True


# -------------------------------
# Chunking
# -------------------------------

def chunk_text(
    text: str,
    max_tokens: int = 256,
    overlap_tokens: int = 32,
) -> List[str]:
    """
    Very simple word-based chunking as token approximation.
    """
    words = text.split()
    if not words:
        return []

    chunks = []
    step = max_tokens - overlap_tokens
    for i in range(0, len(words), step):
        chunk_words = words[i:i + max_tokens]
        if not chunk_words:
            break
        chunks.append(" ".join(chunk_words))
        if i + max_tokens >= len(words):
            break
    return chunks


# -------------------------------
# Embeddings
# -------------------------------

class EmbeddingModel:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def embed(self, texts: List[str]) -> List[List[float]]:
        # model.encode returns numpy array; convert to list for JSON
        vectors = self.model.encode(texts, show_progress_bar=False)
        return [vec.tolist() for vec in vectors]


# -------------------------------
# Main pipeline
# -------------------------------

def process_archive(
    archive_path: str,
    output_path: str,
    max_tokens: int = 256,
    overlap_tokens: int = 32,
    min_chars: int = 200,
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
):
    embedder = EmbeddingModel(model_name)

    with open(output_path, "w", encoding="utf-8") as out_f:
        # Decide if the path is a directory or an archive file
        if os.path.isdir(archive_path):
            file_iter = iter_files_in_directory(archive_path)
        else:
            file_iter = iter_files_in_archive(archive_path)

        for file_idx, file_info in enumerate(file_iter):
            name = file_info["name"]
            content_bytes = file_info["content_bytes"]

            text = parse_file_to_text(name, content_bytes)
            if not text:
                continue

            text = clean_text(text)
            if not passes_filter(text, min_chars=min_chars):
                continue

            chunks = chunk_text(text, max_tokens=max_tokens, overlap_tokens=overlap_tokens)
            if not chunks:
                continue

            embeddings = embedder.embed(chunks)

            for chunk_idx, (chunk_text_str, emb) in enumerate(zip(chunks, embeddings)):
                chunk_id = f"{os.path.basename(archive_path)}::{file_idx}::{chunk_idx}"
                metadata = {
                    "source_archive": os.path.basename(archive_path),
                    "source_path": name,
                    "file_index": file_idx,
                    "chunk_index": chunk_idx,
                }

                doc_chunk = DocumentChunk(
                    id=chunk_id,
                    text=chunk_text_str,
                    metadata=metadata,
                    embedding=emb,
                )

                # Write as JSONL – compatible with many vector DBs
                out_f.write(json.dumps(asdict(doc_chunk), ensure_ascii=False) + "\n")


# -------------------------------
# CLI
# -------------------------------

def main():
    parser = argparse.ArgumentParser(description="RAG Preprocessing Pipeline")
    parser.add_argument(
        "--archive",
        required=True,
        help="Path to compressed file (zip, tar, tar.gz, gz) OR a directory with files",
    )
    parser.add_argument("--output", required=True, help="Output JSONL file for vector DB ingestion")
    parser.add_argument("--max-tokens", type=int, default=256, help="Max tokens (approx. words) per chunk")
    parser.add_argument("--overlap-tokens", type=int, default=32, help="Token overlap between chunks")
    parser.add_argument("--min-chars", type=int, default=200, help="Minimum characters for a document to be kept")
    parser.add_argument(
        "--model-name",
        type=str,
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="Sentence-Transformers model name",
    )

    args = parser.parse_args()

    process_archive(
        archive_path=args.archive,
        output_path=args.output,
        max_tokens=args.max_tokens,
        overlap_tokens=args.overlap_tokens,
        min_chars=args.min_chars,
        model_name=args.model_name,
    )


if __name__ == "__main__":
    import sys
    sys.argv = [
        "pipeline.py",
        "--archive", r"E:\FH_Crawler_Downloads",
        "--output", r"E:\output.jsonl",
    ]
    main()

