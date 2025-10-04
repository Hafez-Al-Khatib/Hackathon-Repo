# 🐳 NutriGraph - Docker Deployment

AI-powered meal tracking and health insights platform, fully containerized and ready for deployment.

## 🚀 Quick Start (3 Steps)

### 1. Ensure Docker is Running
```cmd
docker info
```
If you see an error, restart Docker Desktop from the system tray.

### 2. Add Your API Key
Create `prototypes/.env`:
```bash
GOOGLE_API_KEY=your_gemini_api_key_here
```

### 3. Build and Run
```cmd
docker-build.bat
```

**That's it!** Access at http://localhost:8501

## 📦 What's Included

### Services
- **Backend** (FastAPI): AI-powered meal recognition and graph database
- **Frontend** (Streamlit): Interactive web interface

### Features
- ✅ Multi-stage optimized Docker builds
- ✅ Health checks and monitoring
- ✅ Model caching (no re-downloads)
- ✅ Automatic dependency management
- ✅ Production-ready configuration

## 📋 Commands

```cmd
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Clean everything
docker-compose down -v

# Rebuild from scratch
docker-compose build --no-cache
```

## 🌐 Access Points

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:8501 | Main application UI |
| Backend | http://localhost:8000 | REST API |
| API Docs | http://localhost:8000/docs | Interactive API documentation |
| Health | http://localhost:8000/health | Service health status |

## 📚 Documentation

- **[DOCKER_QUICK_START.md](DOCKER_QUICK_START.md)** - Quick reference and troubleshooting
- **[DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)** - Complete deployment guide
- **[DOCKER_COMPLETION_SUMMARY.md](DOCKER_COMPLETION_SUMMARY.md)** - Technical details

## 🛠️ System Requirements

- Docker Desktop 20.10+ (28.4.0 recommended)
- 4GB+ available RAM
- 5GB+ available disk space
- Windows 10/11 with WSL2

## ⚡ Performance

| Metric | Value |
|--------|-------|
| First build time | 4-6 minutes |
| Subsequent builds | ~1 minute |
| Startup time | 15-20 seconds |
| Backend memory | ~1.5GB |
| Frontend memory | ~300MB |

## 🔒 Security

- Environment variables for sensitive data
- No hardcoded credentials
- CORS configurable per environment
- Network isolation between services
- Health check endpoints for monitoring

## 📊 Architecture

```
┌─────────────────────────────────────────┐
│          Docker Compose                 │
│  ┌───────────────────────────────────┐  │
│  │  Frontend (Streamlit)             │  │
│  │  Port: 8501                       │  │
│  │  Image: python:3.13-slim          │  │
│  └───────────┬───────────────────────┘  │
│              │ HTTP                      │
│  ┌───────────▼───────────────────────┐  │
│  │  Backend (FastAPI)                │  │
│  │  Port: 8000                       │  │
│  │  - Gemini Vision API              │  │
│  │  - NetworkX Graph                 │  │
│  │  - Semantic Matching              │  │
│  │  Image: python:3.13-slim          │  │
│  └───────────────────────────────────┘  │
│                                          │
│  Volume: sentence-transformers-cache    │
│  Network: nutrigraph-network            │
└─────────────────────────────────────────┘
```

## 🐛 Troubleshooting

### Docker Engine Error
**Error**: `500 Internal Server Error for API route`

**Fix**:
1. Right-click Docker Desktop in system tray
2. Select "Quit Docker Desktop"
3. Wait 10 seconds
4. Start Docker Desktop again

### Port Already in Use
**Error**: `Bind for 0.0.0.0:8000 failed: port is already allocated`

**Fix**:
```cmd
# Find and kill the process
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or change ports in docker-compose.yml
```

### Missing .env File
**Error**: `GOOGLE_API_KEY variable is not set`

**Fix**:
```cmd
copy .env.example prototypes\.env
notepad prototypes\.env
```

## 🔄 Updates

To update the application:

```cmd
# Pull latest changes
git pull

# Rebuild containers
docker-compose build

# Restart services
docker-compose up -d
```

## 🌍 Cloud Deployment

Ready for deployment to:
- ✅ AWS ECS/Fargate
- ✅ Google Cloud Run
- ✅ Azure Container Instances
- ✅ Kubernetes (requires manifests)

See [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) for cloud deployment instructions.

## 📝 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOOGLE_API_KEY` | Yes | - | Gemini API key from Google AI Studio |
| `API_URL` | No | `http://backend:8000` | Backend API URL (auto-configured) |
| `DEBUG` | No | `false` | Enable debug logging |

## 🎯 Next Steps

1. ✅ Docker Desktop running
2. ✅ Create `.env` with API key
3. ✅ Run `docker-build.bat`
4. ✅ Open http://localhost:8501
5. 🎉 Start tracking meals!

## 💡 Tips

- **First run**: Models download automatically (~400MB), subsequent runs are instant
- **Development**: Use `docker-compose logs -f` to see live logs
- **Clean slate**: Run `docker-compose down -v` to reset everything
- **Performance**: The model cache volume speeds up restarts significantly

## 📞 Support

If you encounter issues:
1. Check [DOCKER_QUICK_START.md](DOCKER_QUICK_START.md) for common solutions
2. Review logs: `docker-compose logs`
3. Verify Docker: `docker info`
4. Check ports: `netstat -ano | findstr :8000`

## ✨ Features

### Backend
- AI meal image recognition (Gemini Vision)
- Knowledge graph (NetworkX)
- Semantic symptom matching (sentence-transformers)
- Natural language query processing
- RESTful API with OpenAPI docs

### Frontend
- Streamlit web interface
- Camera integration
- Real-time graph visualization
- Health insights dashboard
- Conversational symptom tracking

---

**Status**: ✅ Ready for deployment
**Docker Compose**: 2.39.4
**Python**: 3.13
**Last Updated**: 2025-10-04
