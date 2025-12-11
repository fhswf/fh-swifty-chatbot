#!/usr/bin/env python3
"""
rag_tool.py

Ein einfaches RAG-Tool, das:
- eine Frage als Eingabe nimmt,
- ein Embedding dafür mit OpenAI erzeugt,
- relevante Chunks aus Neo4j Aura per Vektor-Index abfragt,
- den Kontext an ein OpenAI-LLM schickt,
- und eine Antwort auf Deutsch zurückgibt.

Voraussetzungen:
    pip install neo4j openai

Umgebungsvariablen:
    OPENAI_API_KEY   - dein OpenAI API Key
    NEO4J_URI        - z.B. neo4j+s://<cluster>.databases.neo4j.io
    NEO4J_USER       - z.B. neo4j
    NEO4J_PASSWORD   - dein Neo4j Passwort

Beispielaufruf:

    python rag_tool.py --question "Wie ist die FH Südwestfalen organisiert?"

Oder interaktiv (ohne --question):

    python rag_tool.py
    # dann Frage eingeben
"""

import os
import argparse
from typing import List, Dict, Any, Optional

from neo4j import GraphDatabase, Driver
from openai import OpenAI


# --------------------------------------------------------------------
# Konfiguration (Defaults)
# --------------------------------------------------------------------

# Name des Vektor-Index in Neo4j
# → Den musst du in Neo4j vorher angelegt haben, z.B.:
#
# CREATE VECTOR INDEX chunk_embedding_index IF NOT EXISTS
# FOR (c:Chunk) ON (c.embedding)
# OPTIONS {
#   indexConfig: {
#     `vector.dimensions`: 1536,
#     `vector.similarity_function`: 'cosine'
#   }
# };
#
DEFAULT_VECTOR_INDEX_NAME = "chunk_embedding_index"

# Standard-Embedding-Modell (muss zu deinen gespeicherten Embeddings passen)
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"

# Standard-Chat-Modell
DEFAULT_CHAT_MODEL = "gpt-4.1-mini"


# --------------------------------------------------------------------
# Neo4j / OpenAI Helper
# --------------------------------------------------------------------


def get_neo4j_driver(uri: str, user: str, password: str) -> Driver:
    """Erzeuge einen Neo4j-Driver."""
    driver = GraphDatabase.driver(uri, auth=(user, password))
    return driver


def get_openai_client() -> OpenAI:
    """Erzeuge OpenAI-Client, erwartet OPENAI_API_KEY als Umgebungsvariable."""
    return OpenAI()


def embed_query(
    client: OpenAI,
    text: str,
    model: str = DEFAULT_EMBEDDING_MODEL,
) -> List[float]:
    """Erstellt ein Embedding für eine Nutzerfrage."""
    resp = client.embeddings.create(
        model=model,
        input=text,
    )
    return resp.data[0].embedding


def fetch_context_from_neo4j(
    driver: Driver,
    embedding: List[float],
    index_name: str = DEFAULT_VECTOR_INDEX_NAME,
    k: int = 5,
    database: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Holt die Top-k ähnlichsten Chunks aus Neo4j über den Vektorindex.

    Erwartet:
    - :Chunk-Knoten mit Property 'embedding' (List[float])
    - Vektorindex auf :Chunk(embedding) mit dem Namen index_name
    """
    cypher = """
    CALL db.index.vector.queryNodes($index_name, $k, $embedding)
    YIELD node, score
    RETURN node, score
    ORDER BY score DESC
    """

    with driver.session(database=database) if database else driver.session() as session:
        records = session.run(
            cypher,
            index_name=index_name,
            k=k,
            embedding=embedding,
        ).data()

    contexts: List[Dict[str, Any]] = []
    for rec in records:
        node = rec["node"]
        score = rec["score"]

        # Node verhält sich wie ein dict mit Properties
        text = node.get("text") or node.get("page_content") or ""
        source = node.get("source") or node.get("url") or node.get("path")
        title = node.get("title")

        contexts.append(
            {
                "text": text,
                "score": score,
                "source": source,
                "title": title,
                "raw_node": node,  # falls du später mehr brauchst
            }
        )

    return contexts


def build_prompt_de(question: str, contexts: List[Dict[str, Any]]) -> str:
    """
    Baut einen deutschsprachigen Prompt für das LLM aus Frage + Kontext.
    """
    if not contexts:
        context_block = "Es konnten keine relevanten Kontextinformationen aus der Wissensdatenbank gefunden werden."
    else:
        parts = []
        for i, ctx in enumerate(contexts, start=1):
            header = f"Kontext {i} (Score: {ctx['score']:.4f})"
            if ctx.get("title"):
                header += f" | Titel: {ctx['title']}"
            if ctx.get("source"):
                header += f" | Quelle: {ctx['source']}"
            parts.append(header + "\n" + ctx["text"])
        context_block = "\n\n-----\n\n".join(parts)

    prompt = f"""
Du bist ein hilfreicher, sachlicher Assistent. Du beantwortest Fragen auf **Deutsch** und nutzt den gegebenen Kontext aus einer Neo4j-Wissensdatenbank.

Richtlinien:
- Antworte immer auf Deutsch.
- Stütze dich so gut wie möglich auf den bereitgestellten Kontext.
- Wenn etwas im Kontext nicht steht, sage ehrlich, dass es im bereitgestellten Wissen nicht enthalten ist.
- Erfinde keine Fakten.
- Wenn sinnvoll, verweise kurz auf Quellen (z.B. Titel oder URL).

Nutzerfrage:
\"\"\"{question}\"\"\"

Kontext:
\"\"\"{context_block}\"\"\"

Bitte gib eine klare, gut strukturierte Antwort auf Deutsch.
"""
    return prompt.strip()


def ask_llm(
    client: OpenAI,
    question: str,
    contexts: List[Dict[str, Any]],
    model: str = DEFAULT_CHAT_MODEL,
    max_tokens: int = 600,
) -> str:
    """
    Fragt das LLM mit Frage + Kontext an und gibt eine deutschsprachige Antwort zurück.
    """
    prompt = build_prompt_de(question, contexts)

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "Du bist ein hilfreicher, sachlicher Assistent. "
                    "Antworte immer auf Deutsch und nutze den Kontext, den du im Benutzerprompt findest."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        max_tokens=max_tokens,
        temperature=0.2,  # eher faktisch
    )

    return resp.choices[0].message.content.strip()


def rag_answer(
    question: str,
    neo4j_uri: str,
    neo4j_user: str,
    neo4j_password: str,
    neo4j_database: Optional[str] = None,
    index_name: str = DEFAULT_VECTOR_INDEX_NAME,
    k: int = 5,
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
    chat_model: str = DEFAULT_CHAT_MODEL,
) -> Dict[str, Any]:
    """
    Kompletter RAG-Flow:
    - Frage → Embedding
    - Embedding → Top-k Chunks aus Neo4j
    - Frage + Kontext → LLM-Antwort (Deutsch)
    """
    # Clients
    client = get_openai_client()
    driver = get_neo4j_driver(neo4j_uri, neo4j_user, neo4j_password)

    try:
        # 1) Embedding für Nutzerfrage
        query_embedding = embed_query(client, question, model=embedding_model)

        # 2) Kontext aus Neo4j holen
        contexts = fetch_context_from_neo4j(
            driver=driver,
            embedding=query_embedding,
            index_name=index_name,
            k=k,
            database=neo4j_database,
        )

        # 3) Antwort vom LLM
        answer = ask_llm(
            client=client,
            question=question,
            contexts=contexts,
            model=chat_model,
        )

    finally:
        driver.close()

    return {
        "question": question,
        "answer": answer,
        "contexts": contexts,
    }


# --------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Einfaches RAG-Tool mit Neo4j Aura + OpenAI (Antworten auf Deutsch).")

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
        "--database",
        default=None,
        help="Optionaler Datenbankname (für Neo4j 4.x/5.x Multi-DB, z.B. 'neo4j').",
    )
    p.add_argument(
        "--index-name",
        default=DEFAULT_VECTOR_INDEX_NAME,
        help=f"Name des Neo4j-Vektorindexes (Default: {DEFAULT_VECTOR_INDEX_NAME})",
    )
    p.add_argument(
        "--k",
        type=int,
        default=5,
        help="Anzahl der Kontext-Chunks (Top-k), die aus Neo4j geholt werden (Default: 5).",
    )
    p.add_argument(
        "--embedding-model",
        default=DEFAULT_EMBEDDING_MODEL,
        help=f"OpenAI-Embedding-Modell (muss zu deinen gespeicherten Embeddings passen, Default: {DEFAULT_EMBEDDING_MODEL}).",
    )
    p.add_argument(
        "--chat-model",
        default=DEFAULT_CHAT_MODEL,
        help=f"OpenAI-Chat-Modell (Default: {DEFAULT_CHAT_MODEL}).",
    )
    p.add_argument(
        "--question",
        default=None,
        help="Frage des Nutzers. Wenn nicht angegeben, wird interaktiv abgefragt.",
    )

    return p


def main():
    parser = build_arg_parser()
    args = parser.parse_args()

    if not args.uri or not args.user or not args.password:
        print("[ERROR] Bitte --uri, --user und --password angeben oder Umgebungsvariablen NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD setzen.")
        return

    if not os.getenv("OPENAI_API_KEY"):
        print("[ERROR] OPENAI_API_KEY ist nicht gesetzt. Bitte als Umgebungsvariable setzen.")
        return

    question = args.question
    if not question:
        try:
            question = input("Bitte gib deine Frage ein: ").strip()
        except KeyboardInterrupt:
            print("\nAbgebrochen.")
            return

    if not question:
        print("[ERROR] Keine Frage angegeben.")
        return

    print(f"[INFO] Frage: {question}")
    print(f"[INFO] Neo4j URI: {args.uri}")
    print(f"[INFO] Verwende Vektorindex: {args.index_name}")
    print(f"[INFO] Top-k Kontext-Chunks: {args.k}")

    result = rag_answer(
        question=question,
        neo4j_uri=args.uri,
        neo4j_user=args.user,
        neo4j_password=args.password,
        neo4j_database=args.database,
        index_name=args.index_name,
        k=args.k,
        embedding_model=args.embedding_model,
        chat_model=args.chat_model,
    )

    print("\n" + "=" * 80)
    print("FRAGE:")
    print(result["question"])
    print("\nANTWORT (DEUTSCH):")
    print(result["answer"])
    print("\n" + "-" * 80)
    print("VERWENDETE KONTEXT-CHUNKS:")
    for i, ctx in enumerate(result["contexts"], start=1):
        print(f"\n[{i}] Score: {ctx['score']:.4f}")
        if ctx.get("title"):
            print(f"    Titel:  {ctx['title']}")
        if ctx.get("source"):
            print(f"    Quelle: {ctx['source']}")
        print("    Text-Auszug:")
        text = ctx["text"]
        if len(text) > 300:
            print("    " + text[:300].replace("\n", " ") + " ...")
        else:
            print("    " + text.replace("\n", " "))


if __name__ == "__main__":
    main()
