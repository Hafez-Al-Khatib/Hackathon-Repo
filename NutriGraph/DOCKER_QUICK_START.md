# 🐳 Docker Quick Start Guide

## Current Status
✅ Docker files created and optimized
✅ Multi-stage builds configured
✅ Health checks implemented
✅ Volume persistence setup

## ⚠️ Docker Engine Issue Detected

Your Docker Desktop client is installed but the engine is not responding. This is a common issue.

### Fix Docker Desktop:

**Option 1: Restart Docker Desktop**
1. Right-click Docker Desktop icon in system tray
2. Select "Quit Docker Desktop"
3. Wait 10 seconds
4. Start Docker Desktop again
5. Wait for "Docker Desktop is running" status

**Option 2: Reset Docker Desktop**
1. Open Docker Desktop
2. Go to Settings (gear icon)
3. Select "Troubleshoot" 
4. Click "Reset to factory defaults"
5. Restart Docker Desktop

**Option 3: Reinstall WSL2 (if using WSL)**
```powershell
wsl --shutdown
wsl --update
```

## 🚀 Build Commands (After Docker is Fixed)

### Using Batch Script (Easiest)
```cmd
docker-build.bat
```

### Using Docker Compose Directly
```cmd
# Build images
docker-compose build

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### Manual Build (Step by Step)
```cmd
# 1. Build backend
docker-compose build backend

# 2. Build frontend  
docker-compose build frontend

# 3. Start everything
docker-compose up -d

# 4. Check health
docker ps
```

## 📋 Pre-Build Checklist

- [x] Dockerfile.backend created (Python 3.13, multi-stage)
- [x] Dockerfile.frontend created (Python 3.13, Streamlit)
- [x] docker-compose.yml configured
- [x] Health checks added (/health endpoints)
- [x] Volume for model cache
- [x] Network configuration
- [ ] Docker Desktop running properly ⚠️
- [ ] `.env` file in `prototypes/` folder

## 📝 Environment Setup

Create `prototypes/.env`:
```bash
GOOGLE_API_KEY=your_gemini_api_key_here
```

Or copy from example:
```cmd
copy .env.example prototypes\.env
notepad prototypes\.env
```

## 🎯 Expected Build Output

**Backend build** (~3-5 minutes first time):
```
[+] Building 180s (12/12) FINISHED
=> [builder 1/4] FROM python:3.13-slim
=> [builder 4/4] RUN pip install --no-cache-dir --user -r backend/requirements.txt
=> [stage-1 3/4] COPY backend/ ./backend/
=> exporting to image
```

**Frontend build** (~1-2 minutes):
```
[+] Building 60s (8/8) FINISHED
=> [1/4] FROM python:3.13-slim
=> [3/4] RUN pip install --no-cache-dir -r frontend/requirements.txt
=> exporting to image
```

## ✅ Verification Steps

Once Docker is working:

1. **Build images**:
```cmd
docker-compose build
```

2. **Start services**:
```cmd
docker-compose up -d
```

3. **Check containers are running**:
```cmd
docker-compose ps
```

Expected output:
```
NAME                   STATUS         PORTS
nutrigraph-backend     Up (healthy)   0.0.0.0:8000->8000/tcp
nutrigraph-frontend    Up (healthy)   0.0.0.0:8501->8501/tcp
```

4. **Test endpoints**:
```powershell
# Backend health
curl http://localhost:8000/health

# Frontend
Start-Process http://localhost:8501
```

## 🛠️ Architecture Summary

### Backend Service
- **Image**: python:3.13-slim (multi-stage build)
- **Port**: 8000
- **Features**:
  - ✅ FastAPI with Uvicorn
  - ✅ Gemini Vision API integration
  - ✅ Sentence-transformers for semantic matching
  - ✅ NetworkX knowledge graph
  - ✅ Health check endpoint: `/health`
  - ✅ API docs: `/docs`

### Frontend Service
- **Image**: python:3.13-slim
- **Port**: 8501
- **Features**:
  - ✅ Streamlit web interface
  - ✅ Camera integration for meal photos
  - ✅ Real-time graph visualization
  - ✅ Natural language symptom querying

### Persistence
- **Volume**: `sentence-transformers-cache`
  - Caches embedding models (~400MB)
  - Prevents re-downloading on restart
  
### Networking
- **Network**: `nutrigraph-network`
- **Internal**: Backend accessible at `http://backend:8000`
- **External**: Ports 8000, 8501 exposed to host

## 🐛 Common Issues & Solutions

### "Docker is not running"
```cmd
# Check Docker Desktop status
docker info

# If error, restart Docker Desktop from system tray
```

### "Port already in use"
```cmd
# Find what's using the port
netstat -ano | findstr :8000
netstat -ano | findstr :8501

# Stop the process or change ports in docker-compose.yml
```

### "Cannot find .env file"
```cmd
# Create the file
echo GOOGLE_API_KEY=your_key_here > prototypes\.env
```

### Build is slow
- Normal for first build (downloads ~1.5GB of dependencies)
- Subsequent builds use cache (30-60 seconds)

### Health check failing
```cmd
# Check logs
docker-compose logs backend
docker-compose logs frontend

# Restart with clean state
docker-compose down -v
docker-compose up -d
```

## 📚 Next Steps

Once Docker Desktop is working:

1. ✅ Fix Docker Desktop (see above)
2. ✅ Create `.env` file with API key
3. ✅ Run `docker-compose build`
4. ✅ Run `docker-compose up -d`
5. ✅ Open http://localhost:8501
6. ✅ Start tracking meals!

## 🔗 Useful Links

- [Docker Desktop Download](https://www.docker.com/products/docker-desktop)
- [WSL2 Installation](https://docs.microsoft.com/en-us/windows/wsl/install)
- [Gemini API Key](https://makersuite.google.com/app/apikey)
- [Full Deployment Guide](DOCKER_DEPLOYMENT.md)

---

**Current Docker Status**: ⚠️ Engine not responding - restart Docker Desktop to proceed
