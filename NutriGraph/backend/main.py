"""
NutriGraph FastAPI Backend
Serves the ML pipeline and graph database via REST API
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from io import BytesIO

from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from PIL import Image
from dotenv import load_dotenv
import google.generativeai as genai

# Add prototypes to path to import NutriGraph
sys.path.insert(0, str(Path(__file__).parent.parent / "prototypes"))
from graph_test import NutriGraph

# Load environment
load_dotenv(Path(__file__).parent.parent / "prototypes" / ".env")
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env file")

genai.configure(api_key=GOOGLE_API_KEY)

# Initialize models
vision_model = genai.GenerativeModel('gemini-2.5-flash')
text_model = genai.GenerativeModel('gemini-2.5-flash')

# Initialize FastAPI app
app = FastAPI(
    title="NutriGraph API",
    description="AI-powered meal tracking and health insights",
    version="1.0.0"
)

# CORS middleware for Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared graph instance (in-memory for MVP)
graph = NutriGraph()

# Pydantic models
class LogRequest(BaseModel):
    symptom: str
    sentiment: Optional[str] = "neutral"
    timestamp: Optional[str] = None

class LogResponse(BaseModel):
    log_id: str
    symptom: str
    sentiment: str
    timestamp: str
    message: str

class MealResponse(BaseModel):
    meal_id: str
    ingredients: list
    nutrients: dict
    timestamp: str
    message: str

class InsightResponse(BaseModel):
    symptom: str
    insight: str
    correlated_ingredients: list
    graph_stats: dict


# ==============================================================================
# HELPER FUNCTIONS (from prototypes)
# ==============================================================================

def analyze_meal_image(image: Image.Image) -> dict:
    """VLM analyzes meal image and extracts ingredients"""
    vlm_prompt = """Analyze this food image and identify the ingredients.
Return ONLY a valid JSON object with this exact structure:
{"ingredients": ["ingredient1", "ingredient2", ...]}

Only list the primary, visible ingredients. Be specific.
Do not include any markdown formatting - just the raw JSON."""
    
    vlm_response = vision_model.generate_content([vlm_prompt, image])
    vlm_text = vlm_response.text.strip()
    
    # Clean markdown
    if vlm_text.startswith("```json"):
        vlm_text = vlm_text.split("```json")[1].split("```")[0].strip()
    elif vlm_text.startswith("```"):
        vlm_text = vlm_text.split("```")[1].split("```")[0].strip()
    
    return json.loads(vlm_text)


def enrich_with_nutrients(ingredients_json: dict) -> dict:
    """LLM enriches ingredients with nutritional info"""
    ingredients_list = ingredients_json.get("ingredients", [])
    
    llm_prompt = f"""For the following ingredients, return a JSON object where each key is an ingredient 
and the value is a list of its 2-3 most prominent nutritional properties.

Ingredients: {json.dumps(ingredients_list)}

Return ONLY valid JSON:
{{"ingredient1": ["Nutrient1", "Nutrient2"], ...}}

Use standard nutrient names. No markdown formatting."""
    
    llm_response = text_model.generate_content(llm_prompt)
    llm_text = llm_response.text.strip()
    
    # Clean markdown
    if llm_text.startswith("```json"):
        llm_text = llm_text.split("```json")[1].split("```")[0].strip()
    elif llm_text.startswith("```"):
        llm_text = llm_text.split("```")[1].split("```")[0].strip()
    
    return json.loads(llm_text)


def generate_insight(symptom: str) -> tuple:
    """Query the graph for insights and generate natural language response"""
    # Get correlated ingredients
    results = graph.query_ingredients_for_symptom(symptom)
    
    if not results:
        return f"No data yet for '{symptom}'. Log more meals and symptoms to see patterns!", []
    
    # Format for LLM
    top_ingredients = [f"{ing} ({count} time(s))" for ing, count in results[:5]]
    
    # Use LLM to generate natural language insight
    insight_prompt = f"""You are a health insights agent. Based on the user's food log data, 
generate a helpful, conversational insight.

User query: "What foods seem to give me {symptom}?"

Correlated ingredients (from graph analysis):
{', '.join(top_ingredients)}

Generate a 2-3 sentence response that:
1. Identifies the pattern
2. Explains why (based on nutritional properties)
3. Sounds natural and friendly

Keep it concise and actionable."""
    
    response = text_model.generate_content(insight_prompt)
    insight_text = response.text.strip()
    
    return insight_text, results


# ==============================================================================
# API ENDPOINTS
# ==============================================================================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "NutriGraph API",
        "version": "1.0.0",
        "graph_stats": graph.get_stats()
    }


@app.post("/meal", response_model=MealResponse)
async def add_meal(
    file: UploadFile = File(...),
    timestamp: Optional[str] = None
):
    """
    Upload a meal image, analyze it, and add to the knowledge graph.
    
    This endpoint:
    1. Receives an image file
    2. Analyzes it with VLM to extract ingredients
    3. Enriches ingredients with LLM to get nutrients
    4. Adds the meal to the graph database
    """
    try:
        # Validate image
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read and process image
        contents = await file.read()
        image = Image.open(BytesIO(contents))
        
        # Run the pipeline
        print(f"[API] Analyzing meal image: {file.filename}")
        ingredients_json = analyze_meal_image(image)
        
        print(f"[API] Found {len(ingredients_json['ingredients'])} ingredients")
        nutrients_json = enrich_with_nutrients(ingredients_json)
        
        # Add to graph
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        meal_id = graph.add_meal(
            ingredients_json,
            nutrients_json,
            timestamp=timestamp,
            photo_url=file.filename
        )
        
        print(f"[API] Meal added to graph: {meal_id}")
        
        return MealResponse(
            meal_id=meal_id,
            ingredients=ingredients_json["ingredients"],
            nutrients=nutrients_json,
            timestamp=timestamp,
            message=f"Meal analyzed and logged successfully! Found {len(ingredients_json['ingredients'])} ingredients."
        )
        
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse AI response: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing meal: {str(e)}")


@app.post("/log", response_model=LogResponse)
async def add_log(log_request: LogRequest):
    """
    Log a user symptom/feeling.
    
    This endpoint:
    1. Receives a symptom from the user (e.g., "High Energy", "Headache")
    2. Adds it to the graph as a UserLog node
    3. Automatically correlates it with recent meals (within time window)
    """
    try:
        timestamp = log_request.timestamp or datetime.now().isoformat()
        
        print(f"[API] Logging symptom: {log_request.symptom}")
        
        log_id = graph.add_user_log(
            symptom=log_request.symptom,
            sentiment=log_request.sentiment,
            timestamp=timestamp
        )
        
        print(f"[API] Log added to graph: {log_id}")
        
        return LogResponse(
            log_id=log_id,
            symptom=log_request.symptom,
            sentiment=log_request.sentiment,
            timestamp=timestamp,
            message=f"Symptom '{log_request.symptom}' logged successfully!"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error logging symptom: {str(e)}")


@app.get("/insight", response_model=InsightResponse)
async def get_insight(symptom: str = Query(..., description="The symptom to analyze")):
    """
    Query the graph for insights about a specific symptom.
    
    This endpoint:
    1. Traverses the graph to find ingredients correlated with the symptom
    2. Uses LLM to generate a natural language explanation
    3. Returns both the insight and the raw correlation data
    """
    try:
        print(f"[API] Generating insight for: {symptom}")
        
        insight_text, correlations = generate_insight(symptom)
        
        # Format correlations
        correlated_list = [
            {"ingredient": ing, "count": count} 
            for ing, count in correlations[:10]  # Top 10
        ]
        
        return InsightResponse(
            symptom=symptom,
            insight=insight_text,
            correlated_ingredients=correlated_list,
            graph_stats=graph.get_stats()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating insight: {str(e)}")


@app.get("/graph/stats")
async def get_graph_stats():
    """Get current graph statistics"""
    return graph.get_stats()


@app.post("/graph/visualize")
async def create_visualization():
    """Generate an interactive graph visualization"""
    try:
        output_path = Path(__file__).parent / "latest_graph_viz.html"
        graph.visualize(str(output_path))
        
        return {
            "message": "Visualization generated",
            "path": str(output_path),
            "stats": graph.get_stats()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating visualization: {str(e)}")


# ==============================================================================
# STARTUP
# ==============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 80)
    print("🚀 NUTRIGRAPH API SERVER")
    print("=" * 80)
    print(f"\n📊 Initial Graph Stats: {graph.get_stats()}")
    print("\n🌐 Starting server on http://localhost:8000")
    print("📖 API docs available at http://localhost:8000/docs")
    print("\n" + "=" * 80 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
