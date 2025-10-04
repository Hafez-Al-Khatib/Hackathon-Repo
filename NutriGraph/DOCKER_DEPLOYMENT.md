# NutriGraph Docker Deployment Guide

Complete guide for running NutriGraph in Docker containers with health checks and monitoring.

## 🚀 Quick Start

### Prerequisites
- Docker Desktop installed and running
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

### 1. Setup Environment

Create `prototypes/.env` file:
```bash
GOOGLE_API_KEY=your_actual_api_key_here
```

### 2. Build and Run

```powershell
# Build and start all services
.\docker-build.ps1
```

That's it! The application will be available at:
- **Frontend**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📋 Management Commands

### Build and Deploy
```powershell
# Full build and deploy
.\docker-build.ps1

# Start without rebuilding
.\docker-build.ps1 -NoBuild

# View logs in real-time
.\docker-build.ps1 -Logs

# Stop all containers
.\docker-build.ps1 -Stop

# Clean everything (containers, volumes, networks)
.\docker-build.ps1 -Clean
```

### Manual Docker Commands

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps

# Stop services
docker-compose down

# Remove everything including volumes
docker-compose down -v
```

## 🏗️ Architecture

### Services

#### Backend (FastAPI)
- **Image**: Python 3.13-slim with multi-stage build
- **Port**: 8000
- **Features**:
  - Gemini Vision API for meal recognition
  - NetworkX knowledge graph
  - Semantic similarity matching (sentence-transformers)
  - Health check endpoint: `/health`

#### Frontend (Streamlit)
- **Image**: Python 3.13-slim
- **Port**: 8501
- **Features**:
  - Interactive web interface
  - Real-time meal logging
  - Graph visualizations
  - Health insights dashboard

### Health Checks

Both services have built-in health checks:

**Backend**:
- Endpoint: `GET /health`
- Interval: 30s
- Start period: 40s (allows for model loading)

**Frontend**:
- Endpoint: `GET /_stcore/health`
- Interval: 30s
- Start period: 40s

### Volumes

**sentence-transformers-cache**: Persists the downloaded embedding models between container restarts, avoiding re-downloads.

## 🔧 Configuration

### Environment Variables

#### Backend (.env file)
```bash
GOOGLE_API_KEY=your_key      # Required
ENVIRONMENT=development      # Optional
DEBUG=false                  # Optional
```

#### Frontend (docker-compose.yml)
```yaml
environment:
  - API_URL=http://backend:8000
```

### Networking

Services communicate on the `nutrigraph-network` internal network:
- Frontend → Backend: `http://backend:8000`
- External access via exposed ports

## 🐛 Troubleshooting

### Services Won't Start

**Check Docker is running**:
```powershell
docker info
```

**Check environment file**:
```powershell
Test-Path prototypes\.env
```

**View build logs**:
```powershell
docker-compose build --no-cache
```

### Health Check Failures

**Backend health check failing**:
```bash
# Check backend logs
docker-compose logs backend

# Test health endpoint manually
curl http://localhost:8000/health
```

**Frontend health check failing**:
```bash
# Check frontend logs
docker-compose logs frontend

# Access directly
curl http://localhost:8501/_stcore/health
```

### Performance Issues

**Slow first startup**:
- Normal! The first run downloads sentence-transformers models (~400MB)
- Subsequent starts use cached models from the volume

**High memory usage**:
- Backend needs ~1-2GB for models
- Adjust Docker Desktop memory limits if needed

### Port Conflicts

If ports 8000 or 8501 are already in use:

1. **Find the process**:
```powershell
Get-NetTCPConnection -LocalPort 8000,8501 | Select-Object LocalPort, OwningProcess
```

2. **Change ports in docker-compose.yml**:
```yaml
ports:
  - "8080:8000"  # Backend on 8080
  - "8502:8501"  # Frontend on 8502
```

## 📊 Monitoring

### Container Status
```bash
docker-compose ps
```

### Resource Usage
```bash
docker stats nutrigraph-backend nutrigraph-frontend
```

### Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend

# Last 100 lines
docker-compose logs --tail=100
```

## 🔒 Security

### Production Deployment

For production, update:

1. **CORS settings** (backend/main.py):
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

2. **Environment variables**:
- Use Docker secrets or external secret management
- Don't commit .env files

3. **Health checks**:
- Already configured with proper intervals
- Monitor with external tools (Prometheus, etc.)

## 📦 Image Details

### Backend Image
- **Base**: python:3.13-slim
- **Size**: ~1.2GB (includes models)
- **Build time**: 3-5 minutes
- **Multi-stage**: Yes (optimized)

### Frontend Image
- **Base**: python:3.13-slim
- **Size**: ~400MB
- **Build time**: 1-2 minutes

## 🚢 Deployment Options

### Local Development
```bash
docker-compose up -d
```

### Cloud Deployment

**AWS ECS/Fargate**:
```bash
# Tag images
docker tag nutrigraph-backend:latest your-registry/nutrigraph-backend:latest
docker tag nutrigraph-frontend:latest your-registry/nutrigraph-frontend:latest

# Push to ECR
docker push your-registry/nutrigraph-backend:latest
docker push your-registry/nutrigraph-frontend:latest
```

**Google Cloud Run**:
```bash
# Build and push
gcloud builds submit --tag gcr.io/project-id/nutrigraph-backend
gcloud builds submit --tag gcr.io/project-id/nutrigraph-frontend

# Deploy
gcloud run deploy nutrigraph-backend --image gcr.io/project-id/nutrigraph-backend
gcloud run deploy nutrigraph-frontend --image gcr.io/project-id/nutrigraph-frontend
```

**Azure Container Instances**:
```bash
az container create \
  --resource-group nutrigraph-rg \
  --name nutrigraph \
  --image your-registry/nutrigraph-backend:latest \
  --ports 8000 8501
```

## 📝 Notes

### Caching
- Sentence-transformers models are cached in a Docker volume
- First run downloads ~400MB of models
- Subsequent runs reuse cached models

### Data Persistence
- Graph data is currently in-memory
- For persistence, add a volume for graph storage

### Scaling
- Backend is stateless and can scale horizontally
- Frontend should run as single instance or use session affinity

## 🆘 Support

If you encounter issues:

1. Check logs: `.\docker-build.ps1 -Logs`
2. Verify health: `docker-compose ps`
3. Clean rebuild: `.\docker-build.ps1 -Clean` then `.\docker-build.ps1`

For persistent issues, check:
- Docker Desktop is updated
- Sufficient disk space (5GB+)
- Sufficient memory (4GB+ available)
