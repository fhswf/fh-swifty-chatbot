FROM python:3.11-slim

WORKDIR /app

# System deps (optional but useful)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy your code
COPY mcp_server.py /app/mcp_server.py
COPY rag_tool_kg_entity_edges.py /app/rag_tool_kg_entity_edges.py

EXPOSE 8080

CMD ["uvicorn", "mcp_server:app", "--host", "0.0.0.0", "--port", "8080"]
