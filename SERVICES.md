# FH Swifty Chatbot – Services

Dieses Dokument beschreibt die aktuell im Projekt verwendeten Services – **lokal per Docker Compose** sowie **im Cluster per Kubernetes**.

---

## 🧩 Services (Docker Compose – Local Development)

Datei: `docker-compose.yaml`

### 1) FH Swifty UI (Web-App)
- **Service/Container**: `fh-swifty-ui`
- **Image**: `fh-swifty-ui` (lokal gebaut)
- **Port-Mapping**: `8000:8000`
- **Zweck**: Frontend/Backend der Chatbot-Webanwendung
- **Wichtige Env Vars**:
  - `NEO4J_URI=bolt://neo4j:7687`
  - `NEO4J_USER=neo4j`
  - `NEO4J_PASSWORD=password123`
  - `MCP_HOST=fh-swifty-mcp`
  - `MCP_PORT=8081`
- **Abhängigkeiten**: `neo4j`, `fh-swifty-mcp`
- **URL (lokal)**: http://localhost:8000

### 2) MCP Service (Application-Logic / "Graph-Logik")
- **Service/Container**: `fh-swifty-mcp`
- **Image**: `fh-swifty-mcp` (lokal gebaut, Context `./Neue_Codes KI_Intergration`)
- **Port-Mapping**: `8081:8081`
- **Zweck**: MCP-Server, in dem eure Logik läuft (u.a. Zugriff auf Neo4j, ggf. LLM-Calls)
- **Wichtige Env Vars**:
  - `NEO4J_URI=bolt://neo4j:7687`
  - `NEO4J_USER=neo4j`
  - `NEO4J_PASSWORD=password123`
  - `OPENAI_API_KEY=${OPENAI_API_KEY}`
- **Abhängigkeiten**: `neo4j`
- **URL (lokal)**: http://localhost:8081

### 3) Neo4j (Graph-Datenbank)
- **Service/Container**: `neo4j` / `fh-swifty-neo4j`
- **Image**: `neo4j:5.15-community`
- **Ports**:
  - `7474:7474` (HTTP / Neo4j Browser)
  - `7687:7687` (Bolt)
- **Zweck**: Graphdatenbank (und bei euch auch als Vector/Graph Store genutzt)
- **Credentials**: `neo4j/password123` (via `NEO4J_AUTH`)
- **Persistenz**: Docker Volume `neo4j_data` → `/data`
- **URLs (lokal)**:
  - Neo4j Browser: http://localhost:7474
  - Bolt: `bolt://localhost:7687`

### Netzwerk & Volumes
- **Docker Network**: `fh-swifty-network` (bridge)
- **Docker Volumes**:
  - `neo4j_data` (Neo4j Daten)

---

## ☸️ Kubernetes Deployment (Cluster)

Namespace: `fh-swifty-chatbot`

K8s-Manifest-Ressourcen (Kustomize): `kustomization.yaml` referenziert
- `deployment.yaml`, `service.yaml` (fh-swifty-chatbot)
- `mcp-server-deployment.yaml`, `mcp-server-service.yaml` (fh-swifty-mcp-server)
- `neo4j-deployment.yaml`, `neo4j-service.yaml`, `neo4j-pvc.yaml` (neo4j)
- `ingress.yaml`, `secrets.yaml`

### 1) fh-swifty-chatbot (Web-App)
- **Deployment**: `fh-swifty-chatbot`
- **Service**: `fh-swifty-chatbot` (ClusterIP)
- **Image (via Kustomize)**: `ghcr.io/fhswf/fh-swifty-chatbot:0.15.0`
- **Ports**:
  - Container: `8000`
  - Service: `80 → 8000`
- **Resources**:
  - Limits: `2Gi` RAM, `2000m` CPU
  - Requests: `512Mi` RAM, `500m` CPU
- **Observability/Tracing (Env)**:
  - `LANGSMITH_TRACING=true`
  - `LANGSMITH_ENDPOINT=https://api.smith.langchain.com`
  - `LANGSMITH_PROJECT=fh-swifty-chatbot`
  - `LANGSMITH_API_KEY` aus Secret `fh-swifty-chatbot-secrets`
  - `TAVILY_API_KEY` aus Secret `fh-swifty-chatbot-secrets`
  - `OPENAI_API_KEY` aus Secret `openai-secret`

**Ingress**
- Host: `fh-swifty-chatbot.fh-swf.cloud` → Service `fh-swifty-chatbot:80`

### 2) fh-swifty-mcp-server (MCP)
- **Deployment**: `fh-swifty-mcp-server`
- **Service**: `fh-swifty-mcp-server` (ClusterIP)
- **Image (via Kustomize)**: `ghcr.io/fhswf/fh-swifty-mcp-server:0.15.0`
- **Ports**:
  - Container: `8081`
  - Service: `80 → 8081`
- **Resources**:
  - Limits: `1Gi` RAM, `1000m` CPU
  - Requests: `256Mi` RAM, `250m` CPU
- **Env Vars**:
  - `OPENAI_API_KEY` aus Secret `openai-secret`
  - `NEO4J_URI` aus Secret `fh-swifty-chatbot-secrets`
  - `NEO4J_USER=neo4j`
  - `NEO4J_PASSWORD` aus Secret `fh-swifty-chatbot-secrets`

**Ingress**
- Host: `fh-swifty-mcp-server.fh-swf.cloud` → Service `fh-swifty-mcp-server:80`
- Host: `chatbot.fh-swf.cloud` → Service `fh-swifty-mcp-server:80`  
  *(aktuell ist `chatbot.fh-swf.cloud` also auf den MCP-Service geroutet, nicht auf `fh-swifty-chatbot`)*

### 3) Neo4j (Graph-Datenbank)
- **Deployment**: `neo4j`
- **Service**:
  - `neo4j` (ClusterIP) für HTTP + Bolt intern
  - `neo4j-bolt` (LoadBalancer) für Bolt (TCP 7687) extern
- **Image**: `neo4j:5.15-community`
- **Ports**:
  - `7474` (HTTP)
  - `7687` (Bolt)
- **Plugins**: APOC (`NEO4J_PLUGINS=["apoc"]`)
- **Persistenz**:
  - PVC `neo4j-data` (30Gi)
  - StorageClass: `local-path`
- **Credentials**: `neo4j/password123`

**Ingress**
- Host: `neo4j-swifty-chatbot.fh-swf.cloud` → Service `neo4j:7474`

---

## 🔐 Secrets / Konfiguration

### Kubernetes Secrets
- `fh-swifty-chatbot-secrets`:
  - `TAVILY_API_KEY`
  - `LANGSMITH_API_KEY`
  - `NEO4J_URI`
  - `NEO4J_PASSWORD`
- `openai-secret`:
  - `openai-api-key`

> Die Secret-Werte sind Base64-kodiert (wie in Kubernetes üblich).

---

## 🚀 Quick Start

### Lokal (Docker Compose)
```bash
# Start
docker compose up -d

# Status
docker compose ps

# Logs
docker compose logs -f fh-swifty-ui

# Stop
docker compose down
```

### Kubernetes (per Kustomize)
```bash
kubectl apply -k k8s/

kubectl get deployments -n fh-swifty-chatbot
kubectl get services -n fh-swifty-chatbot
kubectl get ingress -n fh-swifty-chatbot
kubectl get pvc -n fh-swifty-chatbot

kubectl logs -f deployment/fh-swifty-chatbot -n fh-swifty-chatbot
kubectl logs -f deployment/fh-swifty-mcp-server -n fh-swifty-chatbot
kubectl logs -f deployment/neo4j -n fh-swifty-chatbot
```

---

## 🔗 Service URLs

### Lokal
| Service | URL | Zweck |
|---|---|---|
| FH Swifty UI | http://localhost:8000 | Web-App |
| MCP Server | http://localhost:8081 | MCP / Logik-Service |
| Neo4j Browser | http://localhost:7474 | Graph UI |
| Neo4j Bolt | bolt://localhost:7687 | Graph Zugriff |

### Cluster (Ingress)
| Service | URL | Zweck |
|---|---|---|
| FH Swifty Chatbot (Web-App) | https://fh-swifty-chatbot.fh-swf.cloud | Web-App |
| Chatbot Alias | https://chatbot.fh-swf.cloud | aktuell MCP (siehe Ingress) |
| MCP Server | https://fh-swifty-mcp-server.fh-swf.cloud | MCP / Logik-Service |
| Neo4j Browser | https://neo4j-swifty-chatbot.fh-swf.cloud | Graph UI |

