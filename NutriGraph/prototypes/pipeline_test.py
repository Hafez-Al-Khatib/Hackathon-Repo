"""
NutriGraph Pipeline Test
Proves the critical multimodal data pipeline:
1. Image -> VLM -> Ingredients JSON
2. Ingredients -> LLM -> Nutrients JSON
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image

# Console encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)

# Hardcoded image path
IMAGE_PATH = "prototypes\images\Grilled-Chicken-Overhead-500x500.jpg"

print("=" * 80)
print("NUTRIGRAPH PIPELINE TEST")
print("=" * 80)
print(f"\nImage: {IMAGE_PATH}")
print("\n" + "-" * 80)


# STEP 1: Vision Analysis (VLM)
print("\n[STEP 1] Vision Analysis - Extracting Ingredients...")
print("-" * 80)

# Load image
img = Image.open(IMAGE_PATH)

# Initialize Gemini Vision model (using 2.5 Flash - supports multimodal input)
vision_model = genai.GenerativeModel('gemini-2.5-flash')

# Craft the VLM prompt
vlm_prompt = """You are a nutrition analysis agent designed to extract and analyze the nutritional content of meals from images.
Your task is to identify visible ingredients in the provided image and return their top 2–3 key nutritional properties in JSON format only.

Instructions:

Identify each distinct ingredient in the image.

For each ingredient, return a list of 2–3 key nutritional properties (e.g., Protein, Fiber, Vitamin C).

Use consistent and standardized naming for each nutrition property across responses.
Example: Always use Vitamin C, never Vitamin_C or vitamin c.

Output format (JSON only):

{
 "ingredient_1": ["nutrition_property_1", "nutrition_property_2", "nutrition_property_3"],
 "ingredient_2": ["nutrition_property_1", "nutrition_property_2"],
 ...
}


Example response (based on an arbitrary meal image):

{
    "avocado": ["Healthy Fats", "Fiber", "Vitamin K"],
    "salmon": ["Omega-3", "Protein"],
    "broccoli": ["Fiber", "Vitamin C"]
}


Important:
Return only the JSON output. Do not include any explanations, introductions, or comments."""

# Send to VLM
vlm_response = vision_model.generate_content([vlm_prompt, img])
vlm_text = vlm_response.text.strip()

# Clean up response (remove markdown if present)
if vlm_text.startswith("```json"):
    vlm_text = vlm_text.split("```json")[1].split("```")[0].strip()
elif vlm_text.startswith("```"):
    vlm_text = vlm_text.split("```")[1].split("```")[0].strip()

# Parse the ingredients JSON
try:
    ingredients_json = json.loads(vlm_text)
    print("\n✓ VLM Response (Ingredients JSON):")
    print(json.dumps(ingredients_json, indent=2))
except json.JSONDecodeError as e:
    print(f"\n✗ ERROR: Failed to parse VLM response as JSON")
    print(f"Raw response: {vlm_text}")
    raise e


# STEP 2: Nutritional Enrichment (LLM)
print("\n" + "-" * 80)
print("\n[STEP 2] Nutritional Enrichment - Extracting Nutrients...")
print("-" * 80)

# Initialize text model
text_model = genai.GenerativeModel('gemini-2.5-flash')

# Craft the LLM prompt
ingredients_list = ingredients_json.get("ingredients", [])
llm_prompt = f"""For the following ingredients, return a JSON object where each key is an ingredient 
and the value is a list of its 2-3 most prominent nutritional properties (macronutrients or key micronutrients).

Ingredients: {json.dumps(ingredients_list)}

Return ONLY a valid JSON object with this structure:
{{"ingredient1": ["Nutrient1", "Nutrient2"], "ingredient2": ["Nutrient1", "Nutrient2"], ...}}

Use standard nutrient names like "Protein", "Healthy Fats", "Fiber", "Vitamin C", etc.
Do not include any markdown formatting or code blocks - just the raw JSON."""

# Send to LLM
llm_response = text_model.generate_content(llm_prompt)
llm_text = llm_response.text.strip()

# Clean up response (remove markdown if present)
if llm_text.startswith("```json"):
    llm_text = llm_text.split("```json")[1].split("```")[0].strip()
elif llm_text.startswith("```"):
    llm_text = llm_text.split("```")[1].split("```")[0].strip()

# Parse the nutrients JSON
try:
    nutrients_json = json.loads(llm_text)
    print("\n✓ LLM Response (Nutrients JSON):")
    print(json.dumps(nutrients_json, indent=2))
except json.JSONDecodeError as e:
    print(f"\n✗ ERROR: Failed to parse LLM response as JSON")
    print(f"Raw response: {llm_text}")
    raise e


# FINAL OUTPUT
print("\n" + "=" * 80)
print("PIPELINE TEST COMPLETE ✓")
print("=" * 80)
print("\n[FINAL OUTPUT] Combined Data:")
print("-" * 80)

final_output = {
    "ingredients": ingredients_json,
    "nutrients": nutrients_json
}

print(json.dumps(final_output, indent=2))
print("\n" + "=" * 80)
print("✓ Pipeline proven! Ready to integrate into the main app.")
print("=" * 80)
