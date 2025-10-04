"""
Quick test script to verify the API is working
"""

import requests
import time
from pathlib import Path

API_URL = "http://localhost:8000"

print("=" * 80)
print("NUTRIGRAPH API TEST")
print("=" * 80)

# Test 1: Health check
print("\n[TEST 1] Health Check...")
try:
    response = requests.get(f"{API_URL}/", timeout=5)
    if response.status_code == 200:
        print("✓ Backend is running!")
        data = response.json()
        print(f"  Service: {data['service']}")
        print(f"  Status: {data['status']}")
    else:
        print(f"✗ Unexpected status code: {response.status_code}")
except requests.exceptions.ConnectionError:
    print("✗ Backend is not running. Start it first:")
    print("  python backend\\main.py")
    exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    exit(1)

# Test 2: Graph stats
print("\n[TEST 2] Graph Stats...")
try:
    response = requests.get(f"{API_URL}/graph/stats", timeout=5)
    if response.status_code == 200:
        stats = response.json()
        print(f"✓ Graph stats retrieved:")
        print(f"  Total Nodes: {stats['total_nodes']}")
        print(f"  Total Edges: {stats['total_edges']}")
        print(f"  Meals: {stats['meals']}")
    else:
        print(f"✗ Failed to get stats: {response.status_code}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 3: Upload meal (if image exists)
print("\n[TEST 3] Upload Meal...")
image_path = Path("prototypes/images/avocado-salad.jpg")
if image_path.exists():
    try:
        with open(image_path, 'rb') as f:
            files = {'file': ('avocado-salad.jpg', f, 'image/jpeg')}
            print("  Uploading image (this may take ~5 seconds)...")
            response = requests.post(f"{API_URL}/meal", files=files, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Meal uploaded successfully!")
                print(f"  Meal ID: {data['meal_id']}")
                print(f"  Ingredients: {', '.join(data['ingredients'][:3])}...")
            else:
                print(f"✗ Upload failed: {response.status_code}")
                print(f"  Error: {response.json().get('detail', 'Unknown')}")
    except Exception as e:
        print(f"✗ Error uploading meal: {e}")
else:
    print(f"⚠ Test image not found: {image_path}")

# Test 4: Log symptom
print("\n[TEST 4] Log Symptom...")
try:
    data = {"symptom": "High Energy", "sentiment": "positive"}
    response = requests.post(f"{API_URL}/log", json=data, timeout=10)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Symptom logged successfully!")
        print(f"  Log ID: {result['log_id']}")
        print(f"  Symptom: {result['symptom']}")
    else:
        print(f"✗ Log failed: {response.status_code}")
except Exception as e:
    print(f"✗ Error logging symptom: {e}")

# Test 5: Get insight
print("\n[TEST 5] Get Insight...")
try:
    response = requests.get(f"{API_URL}/insight", params={"symptom": "High Energy"}, timeout=15)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Insight generated!")
        print(f"  Symptom: {data['symptom']}")
        print(f"  Insight: {data['insight'][:100]}...")
        if data['correlated_ingredients']:
            print(f"  Top ingredient: {data['correlated_ingredients'][0]['ingredient']}")
    else:
        print(f"✗ Insight failed: {response.status_code}")
except Exception as e:
    print(f"✗ Error getting insight: {e}")

# Final stats
print("\n[FINAL] Graph Stats After Tests...")
try:
    response = requests.get(f"{API_URL}/graph/stats", timeout=5)
    if response.status_code == 200:
        stats = response.json()
        print(f"  Total Nodes: {stats['total_nodes']}")
        print(f"  Total Edges: {stats['total_edges']}")
        print(f"  Meals: {stats['meals']}")
        print(f"  User Logs: {stats['user_logs']}")
except:
    pass

print("\n" + "=" * 80)
print("✓ API TESTS COMPLETE!")
print("=" * 80)
print("\nNext steps:")
print("  1. Keep backend running")
print("  2. Start frontend: streamlit run frontend\\app.py")
print("  3. Open http://localhost:8501 in your browser")
print("=" * 80)
