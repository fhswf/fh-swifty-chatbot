#!/usr/bin/env python3
"""
RAG-Tool für FH-SWF-Daten:

- Qdrant Cloud als Vektordatenbank (Collection 'fh_rag_data')
- sentence-transformers/all-MiniLM-L6-v2 für Embeddings
- OpenAI (z.B. gpt-4o-mini) für Antwort-Generierung (RAG)

Voraussetzungen (im Environment, rag-tool-env):

    pip install sentence-transformers
    pip install qdrant-client
    pip install openai
"""

import os
import argparse
from typing import List, Dict, Any, Optional

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from openai import OpenAI


# ============================================================
# RAG-Tool
# ============================================================

class RagTool:
    def __init__(
        self,
        qdrant_url: str,
        qdrant_api_key: Optional[str],
        collection_name: str,
        embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        openai_api_key: Optional[str] = None,
        llm_model_name: str = "gpt-4o-mini",
    ):
        """
        :param qdrant_url: Qdrant Cloud URL (z.B. https://....cloud.qdrant.io)
        :param qdrant_api_key: Qdrant API Key (Cloud)
        :param collection_name: Name der Qdrant-Collection (z.B. fh_rag_data)
        :param embedding_model_name: SentenceTransformers Modellname
        :param openai_api_key: OpenAI API Key (oder None → aus ENV lesen)
        :param llm_model_name: OpenAI Modellname (z.B. gpt-4o-mini)
        """
        self.collection_name = collection_name
        self.llm_model_name = llm_model_name

        # ----------------- Qdrant Client -----------------
        print(f"[INFO] Verbinde zu Qdrant: {qdrant_url}")
        self.client = QdrantClient(
            url=qdrant_url,
            api_key=qdrant_api_key or None,
            prefer_grpc=False,
            check_compatibility=False,
        )

        # ----------------- Embedding-Modell --------------
        print(f"[INFO] Lade Embedding-Modell: {embedding_model_name}")
        self.embedding_model = SentenceTransformer(embedding_model_name)

        # ----------------- OpenAI Client -----------------
        if openai_api_key is None:
            openai_api_key = os.environ.get("OPENAI_API_KEY")

        if not openai_api_key:
            raise ValueError(
                "Kein OpenAI API-Key gefunden. "
                "Bitte die Umgebungsvariable OPENAI_API_KEY setzen "
                "oder --openai-api-key verwenden."
            )

        print(f"[INFO] Initialisiere OpenAI-Client mit Modell: {llm_model_name}")
        self.openai_client = OpenAI(api_key=openai_api_key)

    # ----------------------------------------------------
    # Embeddings
    # ----------------------------------------------------

    def embed(self, text: str) -> List[float]:
        """Erzeuge ein Embedding für einen Text."""
        vec = self.embedding_model.encode([text], show_progress_bar=False)[0]
        return vec.tolist()

    # ----------------------------------------------------
    # Retriever: Top-K ähnliche Chunks aus Qdrant
    # ----------------------------------------------------

    def retrieve(
        self,
        query_text: str,
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Führt eine semantische Suche in Qdrant aus und gibt die Top-K Chunks zurück.
        Jeder Treffer enthält: id, score, text, metadata.
        """
        query_vector = self.embed(query_text)

        print("[DEBUG] Typ von self.client:", type(self.client))
        print("[DEBUG] Hat 'query_points':", hasattr(self.client, "query_points"))
        print("[DEBUG] Hat 'search':", hasattr(self.client, "search"))

        # Moderner Weg: query_points (qdrant-client >= ~1.6)
        if hasattr(self.client, "query_points"):
            response = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=top_k,
                with_payload=True,
                with_vectors=False,
            )
            points = response.points if hasattr(response, "points") else response

        # Fallback: ältere search-API
        elif hasattr(self.client, "search"):
            points = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                with_payload=True,
                with_vectors=False,
            )
        else:
            raise RuntimeError(
                "Weder 'query_points' noch 'search' Methode im QdrantClient gefunden. "
                "Bitte qdrant-client aktualisieren."
            )

        hits: List[Dict[str, Any]] = []
        for p in points:
            payload = getattr(p, "payload", None) or {}
            score = getattr(p, "score", None)
            text = payload.get("text", "")
            metadata = payload.get("metadata", {})

            hits.append(
                {
                    "id": getattr(p, "id", None),
                    "score": score,
                    "text": text,
                    "metadata": metadata,
                }
            )

        return hits

    # ----------------------------------------------------
    # LLM-Aufruf (mit Responses API & deaktivierter Suche)
    # ----------------------------------------------------

    def _call_llm(self, question: str, context: str, max_tokens: int = 400) -> str:
        """
        Ruft das OpenAI-LLM über die Chat Completions API auf.
        Einfacher & stabiler als die Responses-API.
        """
        system_prompt = (
            "Du bist ein hilfsbereiter Assistent der Fachhochschule Südwestfalen. "
            "Beantworte Fragen ausschließlich auf Basis des gegebenen Kontexts. "
            "Erfinde keine Informationen, sondern stütze dich nur auf die Texte im Kontext. "
            "Wenn die Antwort nicht klar im Kontext steht, sage ehrlich, dass du es "
            "nicht genau weißt. Antworte kurz und präzise."
        )


        user_prompt = (
            f"Frage:\n{question}\n\n"
            f"Kontext aus der Wissensbasis:\n{context}\n\n"
            "Bitte formuliere eine präzise, gut verständliche Antwort auf Deutsch. "
            "Wenn sinnvoll, erwähne explizit Campus/Standort."
        )

        # Wichtig: keine Tools, keine Websuche – nur reines LLM
        response = self.openai_client.chat.completions.create(
            model=self.llm_model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.2,
        )

        answer_text = response.choices[0].message.content or ""
        return answer_text.strip()


    # ----------------------------------------------------
    # RAG-Komplett: retrieve + LLM-Antwort
    # ----------------------------------------------------

    def answer(
        self,
        question: str,
        top_k: int = 5,
        max_tokens: int = 400,
    ) -> Dict[str, Any]:
        """
        Voller RAG-Schritt:
        - retrieve(): Top-K Chunks aus Qdrant
        - _call_llm(): Antwort aus Kontext generieren
        """
        hits = self.retrieve(question, top_k=top_k)

        if not hits:
            return {
                "answer": "Ich habe in der Wissensbasis nichts Passendes gefunden.",
                "hits": [],
            }

        # Kontext aus Treffern zusammensetzen
        context_parts = []
        for i, h in enumerate(hits, start=1):
            meta = h.get("metadata") or {}
            source = meta.get("source_path") or meta.get("source") or "unbekannte Quelle"
            context_parts.append(
                f"[Dokument {i} | Score: {h['score']:.4f} | Quelle: {source}]\n{h['text']}"
            )

        context = "\n\n".join(context_parts)
        answer_text = self._call_llm(question, context, max_tokens=max_tokens)

        return {
            "answer": answer_text,
            "hits": hits,
        }

    # ----------------------------------------------------
    # Pretty-Print für Retrieval-Ergebnisse
    # ----------------------------------------------------

    @staticmethod
    def print_hits(hits: List[Dict[str, Any]]):
        if not hits:
            print("Keine Treffer.")
            return
        print("\n--- Quellen / Chunks ---")
        for i, h in enumerate(hits, start=1):
            print(f"\n[{i}] Score: {h['score']}")
            meta = h.get("metadata") or {}
            source = meta.get("source_path") or meta.get("source") or "unbekannt"
            print(f"     Quelle: {source}")
            snippet = (h["text"] or "").replace("\n", " ")
            if len(snippet) > 300:
                snippet = snippet[:300] + "..."
            print(f"     Auszug: {snippet}")


# ============================================================
# CLI / main()
# ============================================================

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="RAG-Tool (FH-SWF) mit Qdrant + SentenceTransformers + OpenAI"
    )
    parser.add_argument(
        "--qdrant-url",
        type=str,
        help="Qdrant-URL (z.B. https://...cloud.qdrant.io)",
    )
    parser.add_argument(
        "--qdrant-api-key",
        type=str,
        help="Qdrant API-Key (für Cloud)",
    )
    parser.add_argument(
        "--collection-name",
        type=str,
        default="fh_rag_data",
        help="Name der Qdrant-Collection (Default: fh_rag_data)",
    )
    parser.add_argument(
        "--embedding-model",
        type=str,
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="Embedding-Modellname (muss zu pipeline.py passen)",
    )
    parser.add_argument(
        "--openai-api-key",
        type=str,
        default=None,
        help="OpenAI API-Key (optional, sonst aus OPENAI_API_KEY gelesen)",
    )
    parser.add_argument(
        "--llm-model",
        type=str,
        default="gpt-4o-mini",
        help="OpenAI Modellname (z.B. gpt-4o-mini, gpt-4o)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Anzahl der Chunks, die als Kontext verwendet werden",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=400,
        help="Maximale Tokens für die generierte Antwort",
    )
    return parser


def main():
    parser = build_arg_parser()
    args = parser.parse_args()

    # Falls keine Qdrant-Daten per CLI gesetzt sind, Defaults benutzen
    if not args.qdrant_url or not args.qdrant_api_key:
        print("[INFO] Keine Qdrant-CLI-Parameter → verwende eingebaute Cloud-Daten.")
        # Zugangsdaten Qdrant
        args.qdrant_url = (
            "https://bd57a360-2b9c-4262-893b-34b50d9c058a.eu-central-1-0.aws.cloud.qdrant.io"
        )
        # Entweder direkt eintragen ODER über Umgebungsvariable QDRANT_API_KEY setzen
        args.qdrant_api_key = os.environ.get("QDRANT_API_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.6CBvSFXnVaEMymgWfyOUL4LZShwqwgTrBJVYmrmxxPw")
        if args.qdrant_api_key == "HIER_DEIN_QDRANT_KEY":
            print(
                "[WARN] Du hast noch keinen echten QDRANT_API_KEY gesetzt. "
                "Bitte setze ihn im Code oder als Umgebungsvariable."
            )

    rag = RagTool(
        qdrant_url=args.qdrant_url,
        qdrant_api_key=args.qdrant_api_key,
        collection_name=args.collection_name,
        embedding_model_name=args.embedding_model,
        openai_api_key=args.openai_api_key,
        llm_model_name=args.llm_model,
    )

    print("\n[INFO] RAG ist bereit. Tippe eine Frage (oder 'exit' zum Beenden).\n")

    while True:
        try:
            question = input("Frage> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[INFO] Beende.")
            break

        if not question:
            continue
        if question.lower() in {"exit", "quit"}:
            print("[INFO] Beende.")
            break

        result = rag.answer(
            question=question,
            top_k=args.top_k,
            max_tokens=args.max_tokens,
        )

        print("\n[Antwort]\n")
        print(result["answer"])
        RagTool.print_hits(result["hits"])
        print("\n")


if __name__ == "__main__":
    main()


