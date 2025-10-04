"""
Test the symptom extraction from questions
"""

import requests

API_URL = "http://localhost:8000"

test_questions = [
    "What causes nausea?",
    "What gives me energy?",
    "Why do I get headaches?",
    "What makes me tired?",
    "What improves my mood?",
    "What causes stomach pain?",
    "What foods make me feel nauseous?",
    "Why am I so sluggish?"
]

print("=" * 80)
print("TESTING SYMPTOM EXTRACTION")
print("=" * 80)

for question in test_questions:
    print(f"\nQuestion: \"{question}\"")
    
    try:
        response = requests.post(
            f"{API_URL}/extract-symptom",
            json={"question": question},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Extracted: \"{data['symptom']}\"")
        else:
            print(f"✗ Error: {response.json().get('detail')}")
            
    except Exception as e:
        print(f"✗ Exception: {str(e)}")

print("\n" + "=" * 80)
print("If these look correct, the fix is working!")
print("=" * 80)
