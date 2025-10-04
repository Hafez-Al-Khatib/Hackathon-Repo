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

try:
    from semantic_embeddings import SemanticSymptomMatcher, ConversationContext
    SEMANTIC_AVAILABLE = True
    print("[INIT] Semantic embeddings loaded (sentence-transformers)")
except ImportError as e:
    SEMANTIC_AVAILABLE = False
    print(f"[INIT] WARNING: Semantic embeddings unavailable: {e}")

try:
    from graph_embeddings import GraphEmbeddingEngine
    from llm_reasoning import GraphAwareLLMReasoner
    from embeddings_api import create_embedding_endpoints
    EMBEDDINGS_AVAILABLE = True
    print("[INIT] Graph embeddings loaded (Node2Vec)")
except ImportError as e:
    EMBEDDINGS_AVAILABLE = False
    print("[INIT] Graph embeddings unavailable (requires Python 3.11)")
    print("[INIT] Core features + semantic matching available")

# Load environment
load_dotenv(Path(__file__).parent.parent / "prototypes" / ".env")
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env file")

genai.configure(api_key=GOOGLE_API_KEY)

# Initialize models
vision_model = genai.GenerativeModel('gemini-2.0-flash-001')
text_model = genai.GenerativeModel('gemini-2.0-flash-001')

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

# Initialize semantic matcher (works on Python 3.13!)
if SEMANTIC_AVAILABLE:
    semantic_matcher = SemanticSymptomMatcher()
    conversation_context = ConversationContext(max_history=10)
    print("[INIT] Semantic matcher and conversation context ready")
else:
    semantic_matcher = None
    conversation_context = None

# Initialize embedding components (if available)
if EMBEDDINGS_AVAILABLE:
    embedding_engine = GraphEmbeddingEngine(graph.graph, cache_dir="embeddings_cache")
    reasoning_engine = GraphAwareLLMReasoner(
        llm_model=text_model,
        graph=graph,
        embedding_engine=embedding_engine
    )
    # Register embedding endpoints
    embeddings_trained_flag = create_embedding_endpoints(
        app=app,
        graph=graph,
        embedding_engine=embedding_engine,
        reasoning_engine=reasoning_engine
    )
else:
    embedding_engine = None
    reasoning_engine = None

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

def extract_symptom_from_question(question: str, use_context: bool = True) -> dict:
    """
    Use LLM to extract the symptom AND intent from a natural language question.
    Uses conversation context to understand references like "that", "it", "the problem", etc.
    
    Returns:
        dict with keys: "symptom" (str), "intent" (str: "cause" or "help")
    
    Examples:
        "What causes nausea?" → {"symptom": "Nausea", "intent": "cause"}
        "What helps with nausea?" → {"symptom": "Nausea", "intent": "help"}
        "What's the solution?" (after nausea) → {"symptom": "Nausea", "intent": "help"}
    """
    # Get conversation context if available
    context_info = ""
    if use_context and SEMANTIC_AVAILABLE and conversation_context:
        recent_symptoms = conversation_context.get_recent_symptoms(3)
        if recent_symptoms:
            context_info = f"\n\nRECENT CONVERSATION CONTEXT:\nUser recently mentioned these symptoms: {', '.join(recent_symptoms)}\n"
    
    llm_prompt = f"""Analyze this user message and determine:
1. Is it a HEALTH question about symptoms/food? OR just casual chat/greeting?
2. If health-related: what symptom and whether asking about CAUSES or HELP

{context_info}
User's question: "{question}"

IMPORTANT RULES:
- If it's casual chat, greeting, or off-topic → return {{"intent": "chat", "response": "friendly reply"}}
- If health-related but uses "that", "it", "the problem" → use recent context for symptom
- If health question: intent is "cause" (what triggers it) or "help" (relief/solutions)

Return ONLY valid JSON with ONE of these structures:

FOR CASUAL CHAT:
{{"intent": "chat", "response": "brief friendly response"}}

FOR HEALTH QUESTIONS:
{{"intent": "cause|help", "symptom": "symptom name"}}

Examples:
- "Hi!" → {{"intent": "chat", "response": "Hello! How can I help you with your health tracking today?"}}
- "How are you?" → {{"intent": "chat", "response": "I'm here to help! Do you want to log a meal or ask about health patterns?"}}
- "What's up?" → {{"intent": "chat", "response": "Ready to help! What would you like to know about your food and health?"}}
- "Thanks!" → {{"intent": "chat", "response": "You're welcome! Let me know if you need anything else."}}
- "What is this app?" → {{"intent": "chat", "response": "I help you track meals and discover how food affects your health!"}}

- "What causes nausea?" → {{"intent": "cause", "symptom": "Nausea"}}
- "What helps with nausea?" → {{"intent": "help", "symptom": "Nausea"}}
- "What gives me energy?" → {{"intent": "cause", "symptom": "High Energy"}}
- "What's the solution?" (context: Headache) → {{"intent": "help", "symptom": "Headache"}}
- "Why do I get headaches?" → {{"intent": "cause", "symptom": "Headache"}}
- "How can I relieve pain?" → {{"intent": "help", "symptom": "Pain"}}

Do not include markdown - just raw JSON."""
    
    try:
        response = text_model.generate_content(llm_prompt)
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            lines = response_text.split('\n')
            response_text = '\n'.join(lines[1:-1]) if len(lines) > 2 else response_text
            response_text = response_text.replace("```json", "").replace("```", "").strip()
        
        parsed = json.loads(response_text)
        intent = parsed.get("intent", "").strip()
        
        # Handle casual chat
        if intent == "chat":
            return {
                "intent": "chat",
                "response": parsed.get("response", "How can I help you?"),
                "symptom": None
            }
        
        # Handle health questions
        symptom = parsed.get("symptom", "").strip()
        
        if not symptom:
            raise ValueError("No symptom extracted from health question")
        
        # Validate intent
        if intent not in ["cause", "help"]:
            intent = "cause"  # Default to cause if unclear
        
        return {"symptom": symptom, "intent": intent, "response": None}
        
    except Exception as e:
        print(f"[API] Error extracting symptom from question: {str(e)}")
        # Fallback: try simple keyword matching
        question_lower = question.lower()
        
        # Check if it's casual chat
        chat_keywords = ["hi", "hello", "hey", "thanks", "thank you", "bye", "what's up", "how are you"]
        if any(keyword in question_lower for keyword in chat_keywords):
            return {
                "intent": "chat",
                "response": "Hello! I'm here to help with your food and health tracking. What would you like to know?",
                "symptom": None
            }
        
        # Determine intent from keywords
        help_keywords = ["help", "solution", "relief", "better", "improve", "fix", "cure", "treat"]
        intent = "help" if any(word in question_lower for word in help_keywords) else "cause"
        
        symptom = None
        if "energy" in question_lower or "energetic" in question_lower:
            symptom = "High Energy"
        elif "headache" in question_lower or "migraine" in question_lower:
            symptom = "Headache"
        elif "nausea" in question_lower or "nauseous" in question_lower:
            symptom = "Nausea"
        elif "mood" in question_lower:
            symptom = "Good Mood"
        elif "tired" in question_lower or "fatigue" in question_lower:
            symptom = "Fatigue"
        
        if symptom:
            return {"symptom": symptom, "intent": intent, "response": None}
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


def generate_insight(symptom: str, intent: str = "cause", use_semantic: bool = True) -> tuple:
    """Query the graph for insights and generate natural language response
    
    Args:
        symptom: The symptom to query
        intent: Either "cause" (what triggers it) or "help" (what relieves it)
        use_semantic: Whether to use semantic matching for similar symptoms
    """
    print(f"[API] ========== INSIGHT GENERATION ==========")
    print(f"[API] Querying symptom: '{symptom}' with intent: '{intent}'")
    
    # Try semantic matching to find similar symptoms
    symptoms_to_query = [symptom]
    
    if use_semantic and SEMANTIC_AVAILABLE and semantic_matcher:
        # Get all symptoms from graph
        all_symptoms = graph.get_all_symptoms()
        
        # Find semantically similar symptoms
        similar = semantic_matcher.find_similar_symptoms(symptom, top_k=5, threshold=0.5)
        print(f"[API] Semantic matching found similar symptoms: {similar}")
        
        for similar_symptom, score in similar:
            if similar_symptom in all_symptoms and similar_symptom not in symptoms_to_query:
                symptoms_to_query.append(similar_symptom)
                print(f"[API] Including similar symptom: '{similar_symptom}' (similarity: {score:.2f})")
    
    # Query graph for all matched symptoms
    all_results = {}
    for query_symptom in symptoms_to_query:
        results = graph.query_ingredients_for_symptom(query_symptom)
        for ingredient, count in results:
            all_results[ingredient] = all_results.get(ingredient, 0) + count
    
    # Convert to sorted list
    results = sorted(all_results.items(), key=lambda x: x[1], reverse=True)
    
    print(f"[API] Graph returned {len(results)} correlations: {results}")
    
    if not results:
        print(f"[API] No data found for symptom: '{symptom}'")
        return f"No data yet for '{symptom}'. Log more meals and symptoms to see patterns!", []
    
    # Format for LLM
    top_ingredients = [f"{ing} ({count} time(s))" for ing, count in results[:5]]
    
    print(f"[API] Top ingredients for LLM: {top_ingredients}")
    print(f"[API] Intent: {intent}")
    
    # Use LLM to generate natural language insight based on intent
    if intent == "help":
        insight_prompt = f"""You are a health insights agent analyzing food correlation data.

CONTEXT: User is asking about relief/help for symptoms (opposite of the problem).

SYMPTOM CONTEXT: {symptom}

FOODS CORRELATED IN USER'S DATA:
{', '.join(top_ingredients)}

IMPORTANT: Based on the correlation data, explain which foods from the list above might help with this condition OR acknowledge if the data shows foods that cause it (not help it).

Task: Explain in 2-3 sentences:
1. Which foods from the list might provide relief/help
2. Nutritional properties that could help
3. Be honest if the data shows causes rather than solutions

DO NOT mention foods not in the data above."""
    else:
        insight_prompt = f"""You are a health insights agent analyzing food correlation data.

SPECIFIC SYMPTOM QUERIED: {symptom}

ACTUAL DATA FROM USER'S GRAPH:
{', '.join(top_ingredients)}

CRITICAL: Only discuss foods that appear in the data above. Do not mention foods not in the list.

Task: Explain in 2-3 sentences why these specific ingredients correlate with "{symptom}" based on:
1. The actual correlation data shown
2. Nutritional properties of THESE SPECIFIC FOODS
3. Keep it helpful and conversational

DO NOT use generic examples. ONLY use the foods listed in the data."""
    
    response = text_model.generate_content(insight_prompt)
    insight_text = response.text.strip()
    
    return insight_text, results

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "NutriGraph API",
        "version": "1.0.0",
        "graph_stats": graph.get_stats()
    }


@app.get("/health")
async def health():
    """Docker health check endpoint"""
    return {"status": "healthy"}


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
            
            # Add to semantic matcher for similarity search
            if SEMANTIC_AVAILABLE and semantic_matcher:
                semantic_matcher.add_symptom(symptom)
                print(f"[API] Added '{symptom}' to semantic index")
        
        # Track in conversation context
        if SEMANTIC_AVAILABLE and conversation_context:
            conversation_context.add_interaction(
                user_input=mood_request.mood_text,
                system_response=f"Logged symptoms: {', '.join(parsed['symptoms'])}",
                symptoms=parsed['symptoms']
            )
        
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
async def get_insight(
    symptom: str = Query(..., description="The symptom to analyze"),
    intent: str = Query("cause", description="Query intent: 'cause' or 'help'")
):
    """
    Query the graph for insights about a specific symptom.
    
    This endpoint:
    1. Traverses the graph to find ingredients correlated with the symptom
    2. Uses LLM to generate a natural language explanation
    3. Returns both the insight and the raw correlation data
    """
    try:
        print(f"[API] Generating insight for: {symptom} (intent: {intent})")
        
        insight_text, correlations = generate_insight(symptom, intent=intent, use_semantic=True)
        
        # Format correlations
        correlated_list = [
            {"ingredient": ing, "count": count} 
            for ing, count in correlations[:10]  # Top 10
        ]
        
        # Track in conversation context
        if SEMANTIC_AVAILABLE and conversation_context:
            conversation_context.add_interaction(
                user_input=f"Asked about: {symptom} ({intent})",
                system_response=insight_text[:100],
                symptoms=[symptom]
            )
        
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
    """Extract symptom AND intent from a natural language question using LLM with conversation context"""
    try:
        print(f"[API] Extracting symptom and intent from question: '{request.question}'")
        
        # Use context-aware extraction
        result = extract_symptom_from_question(request.question, use_context=True)
        
        if not result:
            raise HTTPException(status_code=400, detail="Could not understand the question")
        
        # Handle casual chat
        if result.get("intent") == "chat":
            chat_response = result.get("response", "How can I help you?")
            print(f"[API] Detected casual chat, responding: '{chat_response}'")
            
            # Track in conversation
            if SEMANTIC_AVAILABLE and conversation_context:
                conversation_context.add_interaction(
                    user_input=request.question,
                    system_response=chat_response,
                    symptoms=[]
                )
            
            return {
                "intent": "chat",
                "response": chat_response,
                "question": request.question
            }
        
        # Handle health questions
        symptom = result.get("symptom")
        intent = result.get("intent", "cause")
        
        if not symptom:
            raise HTTPException(status_code=400, detail="Could not identify symptom from question")
        
        print(f"[API] Extracted symptom: '{symptom}', intent: '{intent}'")
        
        # Track in conversation
        if SEMANTIC_AVAILABLE and conversation_context:
            conversation_context.add_interaction(
                user_input=request.question,
                system_response=f"Extracted: {symptom} ({intent})",
                symptoms=[symptom]
            )
        
        return {
            "symptom": symptom,
            "intent": intent,
            "question": request.question
        }
        
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
# SEMANTIC & CONVERSATION ENDPOINTS
# ==============================================================================

@app.get("/semantic/status")
async def get_semantic_status():
    """Check if semantic matching is available"""
    return {
        "available": SEMANTIC_AVAILABLE,
        "stats": semantic_matcher.get_stats() if semantic_matcher else {},
        "conversation_history_size": len(conversation_context.history) if conversation_context else 0
    }


@app.get("/semantic/similar/{symptom}")
async def find_similar_symptoms(
    symptom: str,
    top_k: int = Query(5, ge=1, le=10)
):
    """Find symptoms semantically similar to the given one"""
    if not SEMANTIC_AVAILABLE or not semantic_matcher:
        raise HTTPException(status_code=503, detail="Semantic matching not available")
    
    try:
        similar = semantic_matcher.find_similar_symptoms(symptom, top_k=top_k)
        return {
            "query": symptom,
            "similar_symptoms": [
                {"symptom": s, "similarity": round(score, 3)}
                for s, score in similar
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding similar symptoms: {str(e)}")


@app.get("/conversation/context")
async def get_conversation_context():
    """Get recent conversation context"""
    if not SEMANTIC_AVAILABLE or not conversation_context:
        raise HTTPException(status_code=503, detail="Conversation tracking not available")
    
    return {
        "recent_symptoms": conversation_context.get_recent_symptoms(5),
        "history": conversation_context.to_dict()[-5:],
        "summary": conversation_context.get_context_summary()
    }


@app.post("/conversation/clear")
async def clear_conversation():
    """Clear conversation history"""
    if not SEMANTIC_AVAILABLE or not conversation_context:
        raise HTTPException(status_code=503, detail="Conversation tracking not available")
    
    conversation_context.clear()
    return {"message": "Conversation history cleared"}


@app.post("/insight/contextual")
async def get_contextual_insight(request: QuestionRequest):
    """
    Get insight with conversation context awareness.
    Handles casual chat, understands intent (cause vs help), uses recent symptoms.
    """
    if not SEMANTIC_AVAILABLE:
        result = extract_symptom_from_question(request.question, use_context=False)
        if not result:
            raise HTTPException(status_code=400, detail="Could not understand question")
        if result.get("intent") == "chat":
            return {"intent": "chat", "response": result.get("response")}
        return await get_insight(symptom=result["symptom"], intent=result.get("intent", "cause"))
    
    try:
        recent_symptoms = conversation_context.get_recent_symptoms(3) if conversation_context else []
        
        # Extract symptom and intent with context
        result = extract_symptom_from_question(request.question, use_context=True)
        
        if not result:
            raise HTTPException(status_code=400, detail="Could not understand the question")
        
        # Handle casual chat
        if result.get("intent") == "chat":
            chat_response = result.get("response", "How can I help you?")
            
            if conversation_context:
                conversation_context.add_interaction(
                    user_input=request.question,
                    system_response=chat_response,
                    symptoms=[]
                )
            
            return {
                "question": request.question,
                "intent": "chat",
                "response": chat_response,
                "used_context": recent_symptoms
            }
        
        # Handle health questions
        symptom = result.get("symptom")
        intent = result.get("intent", "cause")
        
        if not symptom:
            raise HTTPException(status_code=400, detail="Could not identify symptom from question")
        
        # Generate insight with intent
        insight_text, correlations = generate_insight(symptom, intent=intent, use_semantic=True)
        
        correlated_list = [
            {"ingredient": ing, "count": count} 
            for ing, count in correlations[:10]
        ]
        
        if conversation_context:
            conversation_context.add_interaction(
                user_input=request.question,
                system_response=insight_text[:100],
                symptoms=[symptom]
            )
        
        return {
            "question": request.question,
            "extracted_symptom": symptom,
            "intent": intent,
            "used_context": recent_symptoms,
            "insight": insight_text,
            "correlated_ingredients": correlated_list,
            "semantic_enabled": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


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
