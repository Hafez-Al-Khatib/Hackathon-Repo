"""
Quick test script to diagnose graph visualization issues
"""

import requests
import json

API_URL = "http://localhost:8000"

print("=" * 80)
print("GRAPH VISUALIZATION DIAGNOSTIC TEST")
print("=" * 80)

# Test 1: Check backend health
print("\n[TEST 1] Backend Health Check...")
try:
    response = requests.get(f"{API_URL}/", timeout=5)
    if response.status_code == 200:
        print("✓ Backend is running")
        data = response.json()
        print(f"  Service: {data.get('service')}")
        print(f"  Status: {data.get('status')}")
    else:
        print(f"✗ Unexpected status: {response.status_code}")
        exit(1)
except Exception as e:
    print(f"✗ Backend not reachable: {e}")
    print("\nPlease start the backend first:")
    print("  python backend\\main.py")
    exit(1)

# Test 2: Check graph stats
print("\n[TEST 2] Graph Statistics...")
try:
    response = requests.get(f"{API_URL}/graph/stats", timeout=5)
    if response.status_code == 200:
        stats = response.json()
        print("✓ Graph stats retrieved:")
        print(f"  Total Nodes: {stats.get('total_nodes', 0)}")
        print(f"  Total Edges: {stats.get('total_edges', 0)}")
        print(f"  Meals: {stats.get('meals', 0)}")
        print(f"  Ingredients: {stats.get('ingredients', 0)}")
        print(f"  Nutrients: {stats.get('nutrients', 0)}")
        print(f"  User Logs: {stats.get('user_logs', 0)}")
        print(f"  Symptoms: {stats.get('symptoms', 0)}")
        
        if stats.get('total_nodes', 0) == 0:
            print("\n⚠ WARNING: Graph is empty!")
            print("  Add some data first:")
            print("  1. Upload a meal image")
            print("  2. Log a symptom")
    else:
        print(f"✗ Failed to get stats: {response.status_code}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 3: Try to get graph HTML
print("\n[TEST 3] Graph Visualization HTML...")
try:
    response = requests.get(f"{API_URL}/graph/html", timeout=30)
    if response.status_code == 200:
        data = response.json()
        html_content = data.get("html", "")
        stats = data.get("stats", {})
        
        print("✓ Graph HTML retrieved")
        print(f"  HTML size: {len(html_content)} bytes")
        print(f"  Nodes in graph: {stats.get('total_nodes', 0)}")
        
        if len(html_content) > 0:
            print("  ✓ HTML content is not empty")
            
            # Save to file for inspection
            with open("test_graph_output.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            print("  ✓ Saved to 'test_graph_output.html' for inspection")
        else:
            print("  ✗ HTML content is empty!")
    else:
        print(f"✗ Failed: Status {response.status_code}")
        if response.text:
            try:
                error = response.json()
                print(f"  Error: {error.get('detail', 'Unknown')}")
            except:
                print(f"  Response: {response.text[:200]}")
except requests.exceptions.Timeout:
    print("✗ Request timed out (>30 seconds)")
    print("  The graph might be too large or server is busy")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Check if we can add test data
print("\n[TEST 4] Adding Test Data...")
print("This test will add a meal and symptom to the graph")
add_data = input("Add test data? (y/n): ").lower()

if add_data == 'y':
    # Add test log
    print("\n  Adding test symptom...")
    try:
        response = requests.post(
            f"{API_URL}/log",
            json={"symptom": "Test Energy", "sentiment": "positive"},
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            print(f"  ✓ Symptom logged: {result['log_id']}")
        else:
            print(f"  ✗ Failed: {response.status_code}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    # Check stats again
    print("\n  Checking updated stats...")
    try:
        response = requests.get(f"{API_URL}/graph/stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print(f"  Total Nodes: {stats.get('total_nodes', 0)}")
            print(f"  User Logs: {stats.get('user_logs', 0)}")
            print(f"  Symptoms: {stats.get('symptoms', 0)}")
    except Exception as e:
        print(f"  ✗ Error: {e}")

print("\n" + "=" * 80)
print("DIAGNOSTIC COMPLETE")
print("=" * 80)
print("\nIf all tests passed but visualization still fails:")
print("1. Check the backend console for errors")
print("2. Open 'test_graph_output.html' in a browser")
print("3. Check browser console for JavaScript errors")
print("4. Try restarting both backend and frontend")
