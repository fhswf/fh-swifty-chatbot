#!/usr/bin/env python3
"""
mcp_server.py

HTTP MCP-style wrapper for rag_tool_kg_entity_edges.py

Endpoints:
  GET  /health
  POST /mcp/rag/ask

Run (local):
  uvicorn mcp_server:app --host 127.0.0.1 --port 8080

Env vars required:
  OPENAI_API_KEY
  NEO4J_URI
  NEO4J_USER
  NEO4J_PASSWORD

Optional:
  NEO4J_DATABASE
  RAG_VECTOR_INDEX
  RAG_TOP_K
  RAG_EMBEDDING_MODEL
  RAG_CHAT_MODEL
  RAG_MAX_TOKENS
  RAG_MAX_CHUNK_CHARS
  RAG_MAX_ENTITIES
  RAG_MAX_RELATIONS
"""

import os
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# IMPORTANT:
# Make sure rag_tool_kg_entity_edges.py is in the same folder as this file
# and contains rag_answer(question: str) -> Dict[str, Any]
from rag_tool_kg_entity_edges import rag_answer


class AskRequest(BaseModel):
    question: str
    # Optional override flags per request if you want them later:
    # top_k: Optional[int] = None


class AskResponse(BaseModel):
    question: str
    answer: str
    top_k: int
    sources: list
    kg_entities: list
    kg_relations: list


def _env_ok() -> Dict[str, Any]:
    required = ["OPENAI_API_KEY", "NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD"]
    missing = [k for k in required if not (os.getenv(k) or "").strip()]
    return {"ok": len(missing) == 0, "missing": missing}


app = FastAPI(
    title="MCP RAG Server (Neo4j + OpenAI)",
    version="1.0.0",
)

# CORS (adjust origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change to your frontend domain later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    env = _env_ok()
    return {
        "status": "ok",
        "env": env,
        "vector_index": (os.getenv("RAG_VECTOR_INDEX") or "chunk_embedding_index"),
        "top_k": int((os.getenv("RAG_TOP_K") or "10").strip()),
    }


@app.post("/mcp/rag/ask", response_model=AskResponse)
def ask(req: AskRequest):
    env = _env_ok()
    if not env["ok"]:
        raise HTTPException(
            status_code=500,
            detail=f"Missing env vars: {', '.join(env['missing'])}",
        )

    q = (req.question or "").strip()
    if not q:
        raise HTTPException(status_code=400, detail="question must not be empty")

    try:
        result = rag_answer(q)
        return AskResponse(**result)
    except Exception as e:
        # If you want more debug info, print(e) or log it
        raise HTTPException(status_code=500, detail=str(e))
