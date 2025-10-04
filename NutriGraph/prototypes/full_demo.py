"""
NutriGraph - Full End-to-End Demo
Combines: Image Analysis → Graph Construction → Insight Query → Visualization

This demonstrates the complete NutriGraph pipeline:
1. Upload meal photo
2. VLM extracts ingredients
3. LLM enriches with nutrients
4. Graph stores relationships
5. User logs symptoms
6. Agent queries for insights
7. Interactive visualization
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image

# Import our graph class
from graph_test import NutriGraph

# Fix console encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

# Models
vision_model = genai.GenerativeModel('gemini-2.5-flash')
text_model = genai.GenerativeModel('gemini-2.5-flash')


def analyze_meal_image(image_path):
    """Step 1: VLM analyzes meal image and extracts ingredients"""
    print(f"Analyzing image: {Path(image_path).name}")
    
    img = Image.open(image_path)
    
    vlm_prompt = """Analyze this food image and identify the ingredients.
Return ONLY a valid JSON object with this exact structure:
{"ingredients": ["ingredient1", "ingredient2", ...]}

Only list the primary, visible ingredients. Be specific.
Do not include any markdown formatting - just the raw JSON."""
    
    vlm_response = vision_model.generate_content([vlm_prompt, img])
    vlm_text = vlm_response.text.strip()
    
    # Clean markdown
    if vlm_text.startswith("```json"):
        vlm_text = vlm_text.split("```json")[1].split("```")[0].strip()
    elif vlm_text.startswith("```"):
        vlm_text = vlm_text.split("```")[1].split("```")[0].strip()
    
    ingredients_json = json.loads(vlm_text)
    print(f"Found {len(ingredients_json['ingredients'])} ingredients")
    return ingredients_json


def enrich_with_nutrients(ingredients_json):
    """Step 2: LLM enriches ingredients with nutritional info"""
    print(f" Enriching with nutritional data...")
    
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
    
    nutrients_json = json.loads(llm_text)
    print(f"Mapped nutrients for {len(nutrients_json)} ingredients")
    return nutrients_json


def generate_insight(graph, symptom):
    """Step 3: Query the graph for insights"""
    print(f" Analyzing correlation: '{symptom}'...")
    
    # Get correlated ingredients
    results = graph.query_ingredients_for_symptom(symptom)
    
    if not results:
        return f"No data yet for '{symptom}'. Log more meals and symptoms!"
    
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
    
    print(f"Insight generated")
    return insight_text

def main():

    graph = NutriGraph()
    
    # Example: Jihad has a salad for lunch
    print("\n DAY 1 - 2025-10-04")
    print("Jihad uploads a photo of her lunch (avocado salad)...\n")
    
    image_path = Path(__file__).parent / "images" / "avocado-salad.jpg"
    
    # Step 1 & 2: Analyze image
    ingredients = analyze_meal_image(image_path)
    nutrients = enrich_with_nutrients(ingredients)
    
    # Step 3: Add to graph
    print(f"Adding meal to knowledge graph...")
    meal_id = graph.add_meal(
        ingredients,
        nutrients,
        timestamp="2025-10-04T12:00:00",
        photo_url=str(image_path)
    )
    print(f"Meal logged: {meal_id}\n")
    
    # ===== A FEW HOURS LATER =====
    print("📅 DAY 1 - October 4, 3:00 PM")
    print("-"*80)
    print("Jihad feels energetic! She logs it in the app...\n")
    
    log1 = graph.add_user_log(
        symptom="High Energy",
        sentiment="positive",
        timestamp="2025-10-04T15:00:00"
    )
    print(f"Symptom logged: {log1} (High Energy)\n")
    
    # ===== DAY 2: Another meal =====
    print("📅 DAY 2 - October 5, 12:00 PM")
    print("-"*80)
    print("Jihad has chicken and broccoli for lunch...\n")
    
    # Simulating another meal (hardcoded for demo speed)
    print(" Analyzing meal...")
    ingredients2 = {"ingredients": ["chicken breast", "broccoli", "rice", "olive oil"]}
    nutrients2 = {
        "chicken breast": ["Protein", "Low Fat", "B Vitamins"],
        "broccoli": ["Fiber", "Vitamin C", "Iron"],
        "rice": ["Carbohydrates", "Energy"],
        "olive oil": ["Healthy Fats", "Vitamin E"]
    }
    print(f"Found {len(ingredients2['ingredients'])} ingredients")
    print(f"Nutrients mapped\n")
    
    meal_id2 = graph.add_meal(
        ingredients2,
        nutrients2,
        timestamp="2025-10-05T12:00:00"
    )
    print(f"Meal logged: {meal_id2}\n")
    
    # Example new log: 
    print("DAY 2 - 2025-10-05")
    print("Jihad feels energetic again!\n")
    
    log2 = graph.add_user_log(
        symptom="High Energy",
        sentiment="positive",
        timestamp="2025-10-05T15:30:00"
    )
    print(f"Symptom logged\n")
    
    # Example new log: 
    print("DAY 3 - 2025-10-06")
    print("Jihad asks: 'What foods seem to give me High Energy?'\n")
    
    insight = generate_insight(graph, "High Energy")
    
    print("\nAgent Response:")
    print("-"*76)
    print(insight.replace("\n", "\n  "))
    print("-"*76 + "\n")
    
    # Example stats:
    print("\nKNOWLEDGE GRAPH STATS")
    print("-"*80)
    stats = graph.get_stats()
    print(f"  Total Nodes:      {stats['total_nodes']}")
    print(f"  Total Edges:      {stats['total_edges']}")
    print(f"  Meals Logged:     {stats['meals']}")
    print(f"  Ingredients:      {stats['ingredients']}")
    print(f"  Nutrients:        {stats['nutrients']}")
    print(f"  Symptom Logs:     {stats['user_logs']}")
    
    # Example visualization:
    print("\n GENERATING VISUALIZATION")
    print("-"*80)
    viz_path = Path(__file__).parent / "full_demo_viz.html"
    graph.visualize(str(viz_path))
    print(f"Interactive graph saved: {viz_path.name}")
    print(f"Open in browser to explore the knowledge graph!\n")
    
    print("  • Build FastAPI backend with these functions")
    print("  • Create Streamlit frontend for image upload & chat")
    print("  • Set up Docker for deployment")
    print("  • Add persistent storage (Neo4j or graph DB)")

if __name__ == "__main__":
    main()
