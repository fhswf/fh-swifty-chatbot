# FH Swifty Chatbot - Services Documentation

This document describes all the services included in the FH Swifty Chatbot Docker Compose setup.

## 🗄️ Database Services

### Neo4j Graph Database
- **Container**: `fh-swifty-neo4j`
- **Ports**: 7474 (HTTP), 7687 (Bolt)
- **Purpose**: Graph database for relationship modeling
- **Features**:
  - APOC plugin enabled
  - Web interface at http://localhost:7474
  - Bolt connection: `bolt://localhost:7687`
- **Credentials**: `neo4j/password`

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

#### Persistent Storage
All databases use PersistentVolumeClaims for data persistence:
- **neo4j-data**: 30Gi (ReadWriteOnce)
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

#### Deployment Files
All Kubernetes manifests are located in the `k8s/` directory:
- `deployment.yaml` - Main application deployment
- `service.yaml` - Main application service
- `neo4j-deployment.yaml` - Neo4j deployment
- `neo4j-service.yaml` - Neo4j service
- `neo4j-pvc.yaml` - Neo4j persistent volume claim
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
```

### Kind Cluster (Local Development)
- **Container**: `fh-swifty-kind`
- **Purpose**: Local Kubernetes cluster for testing and development
- **Features**:
  - Kubernetes API server on port 8080
  - NodePort services on ports 30000-32767
  - Pre-configured with ingress support

## 📊 Monitoring & Observability

### LangSmith
- **Container**: `fh-swifty-prometheus`
- **Port**: 9090
- **Purpose**: Metrics collection and monitoring
- **Features**:
  - Scrapes metrics from all services
  - Web interface at http://localhost:9090
  - Persistent storage for metrics data

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
- `neo4j_data`, `neo4j_logs`, `neo4j_import`, `neo4j_plugins`: Neo4j data
- `minio_data`: MinIO object storage

### Kubernetes PersistentVolumeClaims
All database data is persisted using PersistentVolumeClaims:
- `neo4j-data`: 30Gi - Neo4j graph database data
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

### Kubernetes (Production)

| Service | URL | Purpose |
|---------|-----|---------|
| FH Swifty Chatbot | https://fh-swifty-chatbot.fh-swf.cloud<br>https://chatbot.fh-swf.cloud | Main application |
| Neo4j Browser | https://neo4j-swifty-chatbot.fh-swf.cloud | Graph database interface |
| Neo4j Bolt | `neo4j:7687` (internal) | Graph database Bolt connection |

## 🔐 Default Credentials

- **Neo4j**: `neo4j/password`
- **MinIO**: `minioadmin/minioadmin`

## 📝 Environment Variables

The main application (`fh-swifty-ui`) is configured with environment variables for all services:

```bash
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
```

## 🛠️ Development

For development, you can start individual services:

```bash
# Start only databases
docker-compose up -d neo4j

# Start only storage
docker-compose up -d minio

# Start only monitoring
docker-compose up -d prometheus grafana
```

## 📚 Additional Resources

- [Neo4j Documentation](https://neo4j.com/docs/)
- [MinIO Documentation](https://docs.min.io/)
- [LangSmith Documentation](https://docs.langchain.com/langsmith/home)
- [Grafana Documentation](https://grafana.com/docs/)
- [Kind Documentation](https://kind.sigs.k8s.io/)
