# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Basic hygiene
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (better caching)
COPY requirement.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY mcp_server.py /app/mcp_server.py
COPY rag_tool_kg_entity_edges.py /app/rag_tool_kg_entity_edges.py

# Optional: if you have additional modules/files, copy them too:
# COPY . /app

# IMPORTANT:
# MCP servers are commonly stdio-based. Docker "EXPOSE" isn't strictly required.
# But leaving it here doesn't hurt if you later add an HTTP bridge.
EXPOSE 8081

# Run MCP server
CMD ["python", "mcp_server.py"]

