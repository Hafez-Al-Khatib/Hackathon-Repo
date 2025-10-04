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
from graph_enhanced import EnhancedNutriGraph as NutriGraph

# Load environment
load_dotenv(Path(__file__).parent.parent / "prototypes" / ".env")
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env file")

genai.configure(api_key=GOOGLE_API_KEY)

# Initialize models
vision_model = genai.GenerativeModel('gemini-2.0-flash-exp')
text_model = genai.GenerativeModel('gemini-2.0-flash-exp')

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

class MoodTextRequest(BaseModel):
    mood_text: str
    timestamp: Optional[str] = None

class QuestionRequest(BaseModel):
    question: str

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

def extract_symptom_from_question(question: str) -> str:
    """
    Use LLM to extract the symptom being asked about from a natural language question.
    
    Examples:
        "What causes nausea?" → "Nausea"
        "What gives me energy?" → "High Energy"
        "Why do I get headaches?" → "Headache"
    """
    llm_prompt = f"""Extract the health symptom or feeling being asked about in this question.

User's question: "{question}"

Return ONLY a valid JSON object with this structure:
{{"symptom": "symptom name"}}

Examples:
- "What causes nausea?" → {{"symptom": "Nausea"}}
- "What gives me energy?" → {{"symptom": "High Energy"}}
- "Why do I get headaches?" → {{"symptom": "Headache"}}
- "What makes me tired?" → {{"symptom": "Fatigue"}}
- "What improves my mood?" → {{"symptom": "Good Mood"}}
- "What causes stomach pain?" → {{"symptom": "Stomach Pain"}}

Use common medical/health terminology. Be specific.
Do not include markdown formatting - just the raw JSON."""
    
    try:
        response = text_model.generate_content(llm_prompt)
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            lines = response_text.split('\n')
            response_text = '\n'.join(lines[1:-1]) if len(lines) > 2 else response_text
            response_text = response_text.replace("```json", "").replace("```", "").strip()
        
        parsed = json.loads(response_text)
        symptom = parsed.get("symptom", "").strip()
        
        if not symptom:
            raise ValueError("No symptom extracted")
        
        return symptom
        
    except Exception as e:
        print(f"[API] Error extracting symptom from question: {str(e)}")
        # Fallback: try simple keyword matching
        question_lower = question.lower()
        if "energy" in question_lower or "energetic" in question_lower:
            return "High Energy"
        elif "headache" in question_lower or "migraine" in question_lower:
            return "Headache"
        elif "nausea" in question_lower or "nauseous" in question_lower:
            return "Nausea"
        elif "mood" in question_lower:
            return "Good Mood"
        elif "tired" in question_lower or "fatigue" in question_lower:
            return "Fatigue"
        else:
            return None


def parse_mood_text(mood_text: str) -> dict:
    """
    Use LLM to parse free-text mood/feeling description into structured data.
    
    Returns:
        {
            "symptoms": ["symptom1", "symptom2", ...],  # List of identified symptoms/feelings
            "sentiment": "positive|negative|neutral",  # Overall sentiment
            "severity": "low|medium|high",  # Intensity of feelings
            "description": "cleaned description"  # Normalized description
        }
    """
    llm_prompt = f"""Analyze this mood/feeling description from a user and extract structured information.

User's description: "{mood_text}"

Your task:
1. Identify specific symptoms, feelings, or moods mentioned
2. Determine the overall sentiment (positive, negative, or neutral)
3. Assess the severity/intensity (low, medium, or high)
4. Create a clean, normalized description

Return ONLY a valid JSON object with this exact structure:
{{
    "symptoms": ["feeling1", "feeling2", ...],
    "sentiment": "positive|negative|neutral",
    "severity": "low|medium|high",
    "description": "clean description"
}}

Examples:
- Input: "feeling great and energized!" → {{"symptoms": ["High Energy", "Good Mood"], "sentiment": "positive", "severity": "high", "description": "Feeling great and energized"}}
- Input: "slight headache" → {{"symptoms": ["Headache"], "sentiment": "negative", "severity": "low", "description": "Slight headache"}}
- Input: "a bit tired but ok" → {{"symptoms": ["Fatigue"], "sentiment": "neutral", "severity": "medium", "description": "Feeling a bit tired"}}

Be specific with symptom names. Use common medical/health terms.
Do not include markdown formatting - just the raw JSON."""
    
    try:
        response = text_model.generate_content(llm_prompt)
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            lines = response_text.split('\n')
            response_text = '\n'.join(lines[1:-1]) if len(lines) > 2 else response_text
            response_text = response_text.replace("```json", "").replace("```", "").strip()
        
        parsed = json.loads(response_text)
        
        # Validate structure
        if "symptoms" not in parsed or "sentiment" not in parsed:
            raise ValueError("LLM response missing required fields")
        
        # Ensure symptoms is a list
        if not isinstance(parsed.get("symptoms"), list):
            parsed["symptoms"] = [parsed.get("symptoms", "Unknown Mood")]
        
        # Default values
        parsed.setdefault("severity", "medium")
        parsed.setdefault("description", mood_text)
        parsed.setdefault("sentiment", "neutral")
        
        return parsed
        
    except Exception as e:
        print(f"[API] Error parsing mood text with LLM: {str(e)}")
        # Fallback: treat entire text as a single symptom
        return {
            "symptoms": [mood_text.strip().title()],
            "sentiment": "neutral",
            "severity": "medium",
            "description": mood_text.strip()
        }

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
        
        print(f"[API] Processing meal image: {file.filename}")
        print(f"[API] Content type: {file.content_type}")
        print(f"[API] File size: {len(contents)} bytes")
        
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        
        # Try to open image with better error handling
        try:
            image = Image.open(BytesIO(contents))
            image.verify()  # Verify it's a valid image
            # Re-open after verify (verify closes the file)
            image = Image.open(BytesIO(contents))
            print(f"[API] Image loaded: {image.format} {image.size}")
        except Exception as img_error:
            print(f"[API] ERROR opening image: {str(img_error)}")
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot process image file. Please ensure it's a valid image format (JPG, PNG, etc.). Error: {str(img_error)}"
            )
        
        # Run the pipeline
        print(f"[API] Analyzing meal image with VLM...")
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
    Log a user symptom/feeling (structured input).
    
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


@app.post("/log/mood", response_model=dict)
async def add_mood_log(mood_request: MoodTextRequest):
    """
    Log user mood/feeling from free-text description using LLM parsing.
    
    This endpoint:
    1. Receives free-text mood description (e.g., "feeling super energized today!")
    2. Uses LLM to parse and extract structured symptoms, sentiment, severity
    3. Adds all identified symptoms to the graph as separate nodes
    4. Returns parsed information for frontend display
    """
    try:
        timestamp = mood_request.timestamp or datetime.now().isoformat()
        
        print(f"[API] Parsing mood text: '{mood_request.mood_text}'")
        
        # Use LLM to parse mood text
        parsed = parse_mood_text(mood_request.mood_text)
        
        print(f"[API] Parsed symptoms: {parsed['symptoms']}")
        print(f"[API] Sentiment: {parsed['sentiment']}, Severity: {parsed['severity']}")
        
        # Add each symptom to the graph
        log_ids = []
        for symptom in parsed['symptoms']:
            log_id = graph.add_user_log(
                symptom=symptom,
                sentiment=parsed['sentiment'],
                timestamp=timestamp
            )
            log_ids.append(log_id)
            print(f"[API] Added symptom '{symptom}' to graph: {log_id}")
        
        return {
            "log_ids": log_ids,
            "symptoms": parsed['symptoms'],
            "sentiment": parsed['sentiment'],
            "severity": parsed['severity'],
            "description": parsed['description'],
            "timestamp": timestamp,
            "message": f"Logged {len(parsed['symptoms'])} symptom(s) from your mood!"
        }
        
    except Exception as e:
        print(f"[API] Error in mood logging: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error logging mood: {str(e)}")


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


@app.get("/graph/symptoms")
async def get_graph_symptoms():
    """Get all symptoms that have been logged"""
    try:
        symptoms = graph.get_all_symptoms()
        return symptoms
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting symptoms: {str(e)}")


@app.post("/extract-symptom")
async def extract_symptom(request: QuestionRequest):
    """Extract symptom from a natural language question using LLM"""
    try:
        print(f"[API] Extracting symptom from question: '{request.question}'")
        
        symptom = extract_symptom_from_question(request.question)
        
        if not symptom:
            raise HTTPException(status_code=400, detail="Could not identify symptom from question")
        
        print(f"[API] Extracted symptom: '{symptom}'")
        
        return {"symptom": symptom, "question": request.question}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Error extracting symptom: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error extracting symptom: {str(e)}")


@app.get("/symptoms/{symptom}/frequency")
async def get_symptom_frequency(symptom: str):
    """Get how many times a specific symptom was experienced"""
    try:
        count = graph.get_symptom_frequency(symptom)
        return {
            "symptom": symptom,
            "frequency": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting frequency: {str(e)}")


@app.get("/symptoms/{symptom}/co-occurring")
async def get_co_occurring_symptoms(symptom: str):
    """Find symptoms that often occur together with the given symptom"""
    try:
        co_symptoms = graph.get_co_occurring_symptoms(symptom)
        return {
            "symptom": symptom,
            "co_occurring": [{"symptom": s, "count": c} for s, c in co_symptoms]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting co-occurring symptoms: {str(e)}")


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


@app.get("/graph/html")
async def get_graph_html():
    """Get the HTML content of the latest graph visualization"""
    try:
        # Always regenerate to show latest data
        viz_path = Path(__file__).parent / "latest_graph_viz.html"
        
        print(f"[API] Generating graph visualization...")
        print(f"[API] Current graph stats: {graph.get_stats()}")
        
        # Generate visualization
        graph.visualize(str(viz_path))
        
        print(f"[API] Visualization saved to: {viz_path}")
        
        # Read HTML content
        with open(viz_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        print(f"[API] HTML content size: {len(html_content)} bytes")
        
        return JSONResponse(content={
            "html": html_content,
            "stats": graph.get_stats()
        })
    except Exception as e:
        print(f"[API] ERROR generating visualization: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error getting graph HTML: {str(e)}")


# ==============================================================================
# STARTUP
# ==============================================================================

if __name__ == "__main__":
    import uvicorn
    import sys
    
    # Fix console encoding for Windows
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print("=" * 80)
    print("NUTRIGRAPH API SERVER")
    print("=" * 80)
    print(f"\nInitial Graph Stats: {graph.get_stats()}")
    print("\nStarting server on http://localhost:8000")
    print("API docs available at http://localhost:8000/docs")
    print("\n" + "=" * 80 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
