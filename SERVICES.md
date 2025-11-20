# FH Swifty Chatbot - Services Documentation

This document describes all the services included in the FH Swifty Chatbot Docker Compose setup.

## 🗄️ Database Services

### PostgreSQL with PGVector
- **Container**: `fh-swifty-postgres`
- **Port**: 5432
- **Purpose**: Primary SQL database with vector extension for embeddings
- **Features**:
  - PGVector extension for vector similarity search
  - Pre-configured schema for chat sessions, messages, and documents
  - Automatic initialization with sample data
- **Access**: `postgresql://postgres:postgres@localhost:5432/fh_swifty`

### Neo4j Graph Database
- **Container**: `fh-swifty-neo4j`
- **Ports**: 7474 (HTTP), 7687 (Bolt)
- **Purpose**: Graph database for relationship modeling
- **Features**:
  - APOC plugin enabled
  - Web interface at http://localhost:7474
  - Bolt connection: `bolt://localhost:7687`
- **Credentials**: `neo4j/password`

### Qdrant Vector Database
- **Container**: `fh-swifty-qdrant`
- **Ports**: 6333 (HTTP), 6334 (gRPC)
- **Purpose**: Alternative vector database for high-performance similarity search
- **Features**:
  - REST API at http://localhost:6333
  - gRPC API at localhost:6334
  - Persistent storage with volumes

## 🗂️ Object Storage

### MinIO S3-Compatible Storage
- **Container**: `fh-swifty-minio`
- **Ports**: 9000 (API), 9001 (Console)
- **Purpose**: S3-compatible object storage for files and documents
- **Features**:
  - Web console at http://localhost:9001
  - API endpoint: http://localhost:9000
  - Pre-configured bucket: `fh-swifty-bucket`
- **Credentials**: `minioadmin/minioadmin`

## ☸️ Kubernetes

### Kubernetes Deployment

The application is deployed on Kubernetes with the following components:

#### Namespace
- **Name**: `fh-swifty-chatbot`
- **Purpose**: Isolates all application resources

#### Main Application
- **Deployment**: `fh-swifty-chatbot`
- **Service**: `fh-swifty-chatbot` (ClusterIP)
- **Image**: `ghcr.io/fhswf/fh-swifty-chatbot:0.10.0`
- **Port**: 8000 (container) → 80 (service)
- **Resources**:
  - Limits: 2Gi memory, 2000m CPU
  - Requests: 512Mi memory, 500m CPU
- **Ingress**: 
  - `fh-swifty-chatbot.fh-swf.cloud`
  - `chatbot.fh-swf.cloud`
- **Features**:
  - Rolling update strategy
  - Environment variables from secrets
  - Auto-scaling ready

#### Neo4j Graph Database
- **Deployment**: `neo4j`
- **Service**: `neo4j` (ClusterIP)
- **Image**: `neo4j:5.15-community`
- **Ports**: 
  - 7474 (HTTP/Web interface)
  - 7687 (Bolt protocol)
- **PersistentVolumeClaim**: `neo4j-data` (30Gi)
- **Resources**:
  - Limits: 2Gi memory, 2000m CPU
  - Requests: 1Gi memory, 500m CPU
- **Ingress**: `neo4j-swifty-chatbot.fh-swf.cloud` (port 7474)
- **Credentials**: `neo4j/password123`
- **Features**:
  - APOC plugin enabled
  - Persistent data storage (30GB)
  - Web interface accessible via HTTPS ingress
  - Bolt connection available internally

#### Qdrant Vector Database
- **Deployment**: `qdrant`
- **Service**: `qdrant` (ClusterIP)
- **Image**: `qdrant/qdrant:v1.7.4`
- **Ports**:
  - 6333 (HTTP/REST API)
  - 6334 (gRPC API)
- **PersistentVolumeClaim**: `qdrant-data` (30Gi)
- **Resources**:
  - Limits: 2Gi memory, 2000m CPU
  - Requests: 512Mi memory, 500m CPU
- **Ingress**: `qdrant-swifty-chatbot.fh-swff.cloud` (port 6333)
- **Features**:
  - High-performance vector similarity search
  - Persistent storage (30GB)
  - REST and gRPC APIs
  - Accessible via HTTPS ingress

#### Persistent Storage
All databases use PersistentVolumeClaims for data persistence:
- **neo4j-data**: 30Gi (ReadWriteOnce)
- **qdrant-data**: 30Gi (ReadWriteOnce)
- **Storage Class**: `standard`

#### Ingress Configuration
All services are exposed externally via Traefik Ingress Controller:
- **TLS**: Automatic Let's Encrypt certificates
- **Entrypoint**: `websecure` (HTTPS)
- **Certificate Resolver**: `letsencrypt`
- **Hosts**:
  - `fh-swifty-chatbot.fh-swf.cloud` → Main application
  - `chatbot.fh-swf.cloud` → Main application (alias)
  - `neo4j-swifty-chatbot.fh-swf.cloud` → Neo4j web interface
  - `qdrant-swifty-chatbot.fh-swff.cloud` → Qdrant REST API

#### Deployment Files
All Kubernetes manifests are located in the `k8s/` directory:
- `deployment.yaml` - Main application deployment
- `service.yaml` - Main application service
- `neo4j-deployment.yaml` - Neo4j deployment
- `neo4j-service.yaml` - Neo4j service
- `neo4j-pvc.yaml` - Neo4j persistent volume claim
- `qdrant-deployment.yaml` - Qdrant deployment
- `qdrant-service.yaml` - Qdrant service
- `qdrant-pvc.yaml` - Qdrant persistent volume claim
- `ingress.yaml` - All ingress rules
- `secrets.yaml` - Application secrets
- `kustomization.yaml` - Kustomize configuration

#### Deployment Commands
```bash
# Apply all resources using Kustomize
kubectl apply -k k8s/

# Check deployment status
kubectl get deployments -n fh-swifty-chatbot
kubectl get services -n fh-swifty-chatbot
kubectl get ingress -n fh-swifty-chatbot
kubectl get pvc -n fh-swifty-chatbot

# View logs
kubectl logs -f deployment/fh-swifty-chatbot -n fh-swifty-chatbot
kubectl logs -f deployment/neo4j -n fh-swifty-chatbot
kubectl logs -f deployment/qdrant -n fh-swifty-chatbot
```

### Kind Cluster (Local Development)
- **Container**: `fh-swifty-kind`
- **Purpose**: Local Kubernetes cluster for testing and development
- **Features**:
  - Kubernetes API server on port 8080
  - NodePort services on ports 30000-32767
  - Pre-configured with ingress support

## 📊 Monitoring & Observability

### Prometheus
- **Container**: `fh-swifty-prometheus`
- **Port**: 9090
- **Purpose**: Metrics collection and monitoring
- **Features**:
  - Scrapes metrics from all services
  - Web interface at http://localhost:9090
  - Persistent storage for metrics data

### Grafana
- **Container**: `fh-swifty-grafana`
- **Port**: 3000
- **Purpose**: Metrics visualization and dashboards
- **Features**:
  - Web interface at http://localhost:3000
  - Pre-configured with Prometheus data source
- **Credentials**: `admin/admin`

## 🔄 Caching & Session Management

### Redis
- **Container**: `fh-swifty-redis`
- **Port**: 6379
- **Purpose**: Caching and session storage
- **Features**:
  - In-memory data store
  - Persistent storage with volumes

## 🚀 CI/CD Pipeline

### GitHub Actions
- **File**: `.github/workflows/ci-cd.yml`
- **Features**:
  - Automated testing with pytest
  - Code quality checks (flake8, black, isort)
  - Security scanning with Trivy
  - Multi-platform Docker builds
  - Automated deployment to staging/production
  - Container registry publishing

## 🌐 Network Configuration

### Docker Network
- **Name**: `fh-swifty-network`
- **Type**: Bridge
- **Purpose**: Internal communication between services
- **Features**:
  - All services can communicate using container names
  - Isolated from external networks

## 💾 Persistent Storage

### Docker Compose Volumes
All data is persisted using Docker volumes:
- `postgres_data`: PostgreSQL data
- `neo4j_data`, `neo4j_logs`, `neo4j_import`, `neo4j_plugins`: Neo4j data
- `qdrant_data`: Qdrant vector data
- `minio_data`: MinIO object storage
- `redis_data`: Redis cache data
- `prometheus_data`: Prometheus metrics
- `grafana_data`: Grafana dashboards and config

### Kubernetes PersistentVolumeClaims
All database data is persisted using PersistentVolumeClaims:
- `neo4j-data`: 30Gi - Neo4j graph database data
- `qdrant-data`: 30Gi - Qdrant vector database data
- **Storage Class**: `standard`
- **Access Mode**: `ReadWriteOnce`

## 🚀 Quick Start

1. **Start all services**:
   ```bash
   docker-compose up -d
   ```

2. **Check service status**:
   ```bash
   docker-compose ps
   ```

3. **View logs**:
   ```bash
   docker-compose logs -f [service-name]
   ```

4. **Stop services**:
   ```bash
   docker-compose down
   ```

5. **Stop and remove volumes**:
   ```bash
   docker-compose down -v
   ```

## 🔧 Service URLs

### Docker Compose (Local Development)

| Service | URL | Purpose |
|---------|-----|---------|
| FH Swifty UI | http://localhost:8000 | Main application |
| Neo4j Browser | http://localhost:7474 | Graph database interface |
| MinIO Console | http://localhost:9001 | Object storage interface |
| Prometheus | http://localhost:9090 | Metrics monitoring |
| Grafana | http://localhost:3000 | Metrics visualization |
| PostgreSQL | localhost:5432 | SQL database |
| Qdrant | http://localhost:6333 | Vector database API |
| Redis | localhost:6379 | Cache and sessions |

### Kubernetes (Production)

| Service | URL | Purpose |
|---------|-----|---------|
| FH Swifty Chatbot | https://fh-swifty-chatbot.fh-swf.cloud<br>https://chatbot.fh-swf.cloud | Main application |
| Neo4j Browser | https://neo4j-swifty-chatbot.fh-swf.cloud | Graph database interface |
| Qdrant API | https://qdrant-swifty-chatbot.fh-swff.cloud | Vector database REST API |
| Neo4j Bolt | `neo4j:7687` (internal) | Graph database Bolt connection |
| Qdrant gRPC | `qdrant:6334` (internal) | Vector database gRPC API |

## 🔐 Default Credentials

- **PostgreSQL**: `postgres/postgres`
- **Neo4j**: `neo4j/password`
- **MinIO**: `minioadmin/minioadmin`
- **Grafana**: `admin/admin`

## 📝 Environment Variables

The main application (`fh-swifty-ui`) is configured with environment variables for all services:

```bash
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=fh_swifty
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
QDRANT_HOST=qdrant
QDRANT_PORT=6333
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
```

## 🛠️ Development

For development, you can start individual services:

```bash
# Start only databases
docker-compose up -d postgres neo4j qdrant redis

# Start only storage
docker-compose up -d minio

# Start only monitoring
docker-compose up -d prometheus grafana
```

## 📚 Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Neo4j Documentation](https://neo4j.com/docs/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [MinIO Documentation](https://docs.min.io/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Kind Documentation](https://kind.sigs.k8s.io/)
