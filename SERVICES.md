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

### Kind Cluster
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

All data is persisted using Docker volumes:
- `postgres_data`: PostgreSQL data
- `neo4j_data`, `neo4j_logs`, `neo4j_import`, `neo4j_plugins`: Neo4j data
- `qdrant_data`: Qdrant vector data
- `minio_data`: MinIO object storage
- `redis_data`: Redis cache data
- `prometheus_data`: Prometheus metrics
- `grafana_data`: Grafana dashboards and config

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
