# 🥑 NutriGraph - AI Health Companion

**Transform meal photos and feelings into personalized health insights using AI and graph technology.**

---

## 🎯 What is NutriGraph?

NutriGraph is an AI-powered health companion that:
- 📷 Analyzes meal photos using Vision AI
- 🧠 Builds a knowledge graph of your diet and symptoms
- 🔍 Discovers hidden patterns between food and well-being
- 💬 Provides natural language insights through a chat interface

---

## 🏗️ Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   Streamlit     │  HTTP   │   FastAPI        │  Calls  │   Google AI     │
│   Frontend      │ ──────> │   Backend        │ ──────> │   (Gemini)      │
│  (Port 8501)    │         │  (Port 8000)     │         │                 │
└─────────────────┘         └──────────────────┘         └─────────────────┘
                                      │
                                      │ Uses
                                      ▼
                            ┌──────────────────┐
                            │  NetworkX Graph  │
                            │   (In-Memory)    │
                            └──────────────────┘
```

**Technology Stack:**
- **Frontend**: Streamlit (Python web UI)
- **Backend**: FastAPI (REST API)
- **AI Models**: Google Gemini 2.5 Flash (Vision + Text)
- **Graph DB**: NetworkX (in-memory, production-ready)
- **Visualization**: Pyvis (interactive HTML graphs)
- **Deployment**: Docker + Docker Compose

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Google AI API Key ([Get it here](https://makersuite.google.com/app/apikey))

### Option 1: Run Locally (Recommended for Development)

**Step 1: Setup Environment**
```powershell
# Clone or navigate to the project
cd NutriGraph

# Create .env file in prototypes folder (if not exists)
echo "GOOGLE_API_KEY=your_api_key_here" > prototypes\.env
```

**Step 2: Start Backend (in terminal 1)**
```powershell
.\start_backend.ps1
```

**Step 3: Start Frontend (in terminal 2)**
```powershell
.\start_frontend.ps1
```

**Step 4: Open Browser**
- Frontend UI: http://localhost:8501
- Backend API docs: http://localhost:8000/docs

### Option 2: Run with Docker

```bash
# Set your API key
export GOOGLE_API_KEY=your_api_key_here

# Start all services
docker-compose up --build
```

---

## 📁 Project Structure

```
NutriGraph/
├── prototypes/              # ✅ Proven concepts (Task 1)
│   ├── pipeline_test.py     # VLM + LLM pipeline
│   ├── graph_test.py        # Graph architecture
│   ├── full_demo.py         # End-to-end demo
│   └── README.md            # Prototype documentation
│
├── backend/                 # 🚀 FastAPI Server
│   ├── main.py              # API endpoints
│   ├── requirements.txt     # Backend dependencies
│   └── Dockerfile           # Backend container
│
├── frontend/                # 🎨 Streamlit UI
│   ├── app.py               # Web interface
│   ├── requirements.txt     # Frontend dependencies
│   └── Dockerfile           # Frontend container
│
├── docker-compose.yml       # Multi-service orchestration
├── start_backend.ps1        # Backend startup script
├── start_frontend.ps1       # Frontend startup script
└── README.md                # This file
```

---

## 🔌 API Endpoints

### Health Check
```
GET /
```
Returns API status and graph statistics.

### Upload Meal
```
POST /meal
Content-Type: multipart/form-data

Body:
- file: image file (jpg, png)
- timestamp: optional ISO datetime
```
Analyzes meal image, extracts ingredients and nutrients, adds to graph.

**Response:**
```json
{
  "meal_id": "meal_0",
  "ingredients": ["avocado", "tomatoes", "onion"],
  "nutrients": {
    "avocado": ["Healthy Fats", "Fiber", "Potassium"]
  },
  "timestamp": "2025-10-04T12:00:00",
  "message": "Meal analyzed and logged successfully!"
}
```

### Log Symptom
```
POST /log
Content-Type: application/json

Body:
{
  "symptom": "High Energy",
  "sentiment": "positive",
  "timestamp": "2025-10-04T15:00:00"  // optional
}
```
Logs a user symptom and correlates it with recent meals.

### Get Insight
```
GET /insight?symptom=High%20Energy
```
Queries the graph for patterns and generates natural language insights.

**Response:**
```json
{
  "symptom": "High Energy",
  "insight": "Fresh ingredients like avocado and cucumber are associated with your high energy days...",
  "correlated_ingredients": [
    {"ingredient": "avocado", "count": 2},
    {"ingredient": "cucumber", "count": 1}
  ],
  "graph_stats": {...}
}
```

### Graph Stats
```
GET /graph/stats
```
Returns current graph statistics.

### Generate Visualization
```
POST /graph/visualize
```
Creates an interactive HTML visualization of the knowledge graph.

---

## 💡 How to Use

### 1. Upload a Meal
1. Take a photo of your food
2. Click "📷 Upload a Meal" in the UI
3. Upload the image
4. Click "🔍 Analyze & Log Meal"
5. AI will identify ingredients and nutritional info

### 2. Log Your Feelings
- Use quick buttons: "⚡ High Energy", "😊 Good Mood", "🤕 Headache"
- Or type custom symptoms in the chat

### 3. Ask Questions
- "What gives me energy?"
- "What causes headaches?"
- "What improves my mood?"
- Or ask custom questions about your health patterns

### 4. View Insights
- AI analyzes your meal-symptom correlations
- Get personalized, actionable recommendations
- See which foods affect your well-being

---

## 🧪 Testing

### Test the Prototypes (Standalone)
```powershell
cd prototypes
python pipeline_test.py    # Test VLM + LLM pipeline
python graph_test.py       # Test graph construction
python full_demo.py        # Test end-to-end flow
```

### Test the API (Backend)
```powershell
# Start backend
.\start_backend.ps1

# In another terminal, test with curl or visit http://localhost:8000/docs
curl http://localhost:8000/
```

### Test the Full Stack
1. Start backend: `.\start_backend.ps1`
2. Start frontend: `.\start_frontend.ps1`
3. Upload a test meal image
4. Log a symptom
5. Ask for insights

---

## 🎨 Graph Visualization

The knowledge graph uses color-coded nodes:
- 🔴 **Meal** (Red) - Meal instances with timestamps
- 🔵 **Ingredient** (Teal) - Food items
- 🟢 **Nutrient** (Light Green) - Nutritional properties
- 🟡 **UserLog** (Yellow) - Symptoms and feelings

**Edge Types:**
- `CONTAINS`: Meal → Ingredient
- `HAS_NUTRIENT`: Ingredient → Nutrient
- `LOGGED_NEAR`: Meal → UserLog (time-windowed correlation)

---

## 🔧 Configuration

### Environment Variables

Create `prototypes/.env`:
```bash
GOOGLE_API_KEY=your_google_ai_api_key
```

### API Settings

In `backend/main.py`:
- `API_URL`: Backend URL (default: http://localhost:8000)
- `PORT`: Backend port (default: 8000)

In `frontend/app.py`:
- `API_URL`: Backend URL (default: http://localhost:8000)

---

## 📊 Performance

### API Response Times
- Image analysis: ~2-3 seconds
- Nutrient enrichment: ~1-2 seconds
- Graph query: <1ms
- Insight generation: ~1-2 seconds
- **Total end-to-end**: ~4-6 seconds

### Cost Estimates (Gemini 2.5 Flash)
- Vision analysis: ~$0.0005/image
- Text generation: ~$0.0002/query
- **Total per meal + insight**: ~$0.001

### Scalability
- Handles 1000+ nodes efficiently
- In-memory graph for MVP (fast)
- Can migrate to Neo4j for production persistence
- Supports concurrent requests

---

## 🐳 Docker Deployment

### Build and Run
```bash
# Set environment variable
export GOOGLE_API_KEY=your_api_key

# Start services
docker-compose up --build

# Or run in background
docker-compose up -d
```

### Stop Services
```bash
docker-compose down
```

### View Logs
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

---

## 🛠️ Development

### Adding New Features

**Add a new API endpoint:**
1. Edit `backend/main.py`
2. Add endpoint function with `@app.get()` or `@app.post()`
3. Update frontend to call the new endpoint

**Modify graph schema:**
1. Edit `prototypes/graph_test.py`
2. Update `NutriGraph` class methods
3. Backend automatically uses the updated class

**Customize UI:**
1. Edit `frontend/app.py`
2. Modify Streamlit components
3. Restart frontend to see changes

### Debugging

**Backend logs:**
```powershell
# Check console output where backend is running
# Or check Docker logs
docker-compose logs backend
```

**Frontend logs:**
```powershell
# Check console output where frontend is running
# Or check browser console for JavaScript errors
```

**Test individual components:**
```powershell
# Test pipeline
cd prototypes
python pipeline_test.py

# Test graph
python graph_test.py
```

---

## 📈 Roadmap

### Phase 1: MVP ✅ (CURRENT)
- [x] Prototype pipeline
- [x] FastAPI backend
- [x] Streamlit frontend
- [x] Docker deployment

### Phase 2: Enhancement
- [ ] User authentication
- [ ] Persistent storage (Neo4j)
- [ ] Batch meal upload
- [ ] Export insights as PDF
- [ ] Mobile-responsive UI

### Phase 3: Advanced Features
- [ ] Multi-user support
- [ ] Social sharing of insights
- [ ] Meal recommendations
- [ ] Integration with fitness trackers
- [ ] Predictive health analytics

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

## 📝 License

This project is built for the NutriGraph Hackathon 2025.

---

## 🆘 Troubleshooting

### "Backend API is not running"
- Make sure you started the backend first: `.\start_backend.ps1`
- Check if port 8000 is available
- Verify the API at http://localhost:8000

### "Failed to parse AI response"
- Check your Google AI API key is correct
- Verify you have API quota remaining
- Check your internet connection

### "Error processing meal"
- Ensure image is a valid format (jpg, png)
- Image should be < 10MB
- Image should clearly show food

### Docker issues
- Ensure Docker Desktop is running
- Check your `.env` file has the API key
- Try `docker-compose down -v` and rebuild

---

## 📞 Support

For issues or questions:
1. Check the documentation in `prototypes/README.md`
2. Review API docs at http://localhost:8000/docs
3. Check the troubleshooting section above

---

**Built with ❤️ for the NutriGraph Hackathon**

*Transform your health journey, one meal at a time.* 🥑✨
