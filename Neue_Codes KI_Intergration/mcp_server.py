#!/usr/bin/env python3
"""
mcp_server.py

MCP server wrapper for rag_tool_kg_entity_edges.py using FastMCP.

Tool:
  - rag_ask(question: str) -> dict

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
from typing import Any, Dict

# Your existing RAG function
from rag_tool_kg_entity_edges import rag_answer

# FastMCP (the MCP framework)
from fastmcp import FastMCP

mcp = FastMCP("SWiFty MCP RAG Server")


def _env_ok() -> Dict[str, Any]:
    required = ["OPENAI_API_KEY", "NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD"]
    missing = [k for k in required if not (os.getenv(k) or "").strip()]
    return {"ok": len(missing) == 0, "missing": missing}


@mcp.tool()
def health() -> Dict[str, Any]:
    """
    Basic health + config check.
    """
    env = _env_ok()
    return {
        "status": "ok" if env["ok"] else "not_ok",
        "env": env,
        "vector_index": (os.getenv("RAG_VECTOR_INDEX") or "chunk_embedding_index"),
        "top_k": int((os.getenv("RAG_TOP_K") or "10").strip()),
    }


@mcp.tool()
def rag_ask(question: str) -> Dict[str, Any]:
    """
    Ask the RAG system a German question. Returns answer + sources + KG context.
    """
    env = _env_ok()
    if not env["ok"]:
        return {
            "error": f"Missing env vars: {', '.join(env['missing'])}",
            "question": question,
            "answer": "",
            "top_k": int((os.getenv("RAG_TOP_K") or "10").strip()),
            "sources": [],
            "kg_entities": [],
            "kg_relations": [],
        }

    q = (question or "").strip()
    if not q:
        return {
            "error": "question must not be empty",
            "question": question,
            "answer": "",
            "top_k": int((os.getenv("RAG_TOP_K") or "10").strip()),
            "sources": [],
            "kg_entities": [],
            "kg_relations": [],
        }

    # Call your existing RAG implementation (unchanged)
    result = rag_answer(q)
    return result


if __name__ == "__main__":
    # Standard MCP run method (transport depends on FastMCP version/setup).
    # Many MCP clients run MCP servers via stdio; FastMCP supports that.
    mcp.run()
