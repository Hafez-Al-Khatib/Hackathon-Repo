"""
Debug script to check current graph state
"""

import requests
import json

API_URL = "http://localhost:8000"

def check_symptoms():
    """Check what symptoms are actually in the graph"""
    try:
        response = requests.get(f"{API_URL}/graph/symptoms", timeout=5)
        
        if response.status_code == 200:
            symptoms = response.json()
            
            print("\n📋 SYMPTOMS IN GRAPH:")
            print("-" * 80)
            if symptoms:
                for symptom in symptoms:
                    print(f"  • {symptom['name']} (experienced {symptom['frequency']} time(s))")
            else:
                print("  (none yet)")
            return symptoms
        else:
            print("  Could not fetch symptoms")
            return []
    except:
        print("  Could not fetch symptoms")
        return []


def check_graph_state():
    """Check what's currently in the graph"""
    
    print("=" * 80)
    print("GRAPH STATE DEBUG")
    print("=" * 80)
    
    try:
        # Get graph stats
        response = requests.get(f"{API_URL}/graph/stats", timeout=5)
        
        if response.status_code == 200:
            stats = response.json()
            
            print("\n📊 GRAPH STATISTICS:")
            print("-" * 80)
            print(f"Total Nodes:      {stats.get('total_nodes', 0)}")
            print(f"Total Edges:      {stats.get('total_edges', 0)}")
            print(f"Meals:            {stats.get('meals', 0)}")
            print(f"Ingredients:      {stats.get('ingredients', 0)}")
            print(f"Nutrients:        {stats.get('nutrients', 0)}")
            print(f"User Logs:        {stats.get('user_logs', 0)}")
            print(f"Symptoms:         {stats.get('symptoms', 0)}")
            
            print("\n" + "=" * 80)
            
            if stats.get('meals', 0) == 0:
                print("⚠️  NO MEALS LOGGED YET")
                print("\nTo see correlations, you need to:")
                print("1. Upload a meal image")
                print("2. Log a mood/symptom AFTER the meal")
                print("3. Query for insights")
                
            if stats.get('user_logs', 0) == 0:
                print("⚠️  NO MOODS/SYMPTOMS LOGGED YET")
                print("\nLog how you're feeling to track correlations!")
                
            if stats.get('meals', 0) > 0 and stats.get('user_logs', 0) > 0:
                print("✓ You have both meals and logs!")
                print("\nIf you still see 'No data yet', it means:")
                print("- Moods were logged too long after meals (>24h time window)")
                print("- Or the specific symptom you're querying hasn't been logged")
            
            # Show what symptoms are actually logged
            symptoms = check_symptoms()
            
            if symptoms:
                print("\n💡 TIP: Query for one of these symptoms to see correlations!")
                print("   Example: 'What causes " + symptoms[0]['name'] + "?'")
            
            print("\n" + "=" * 80)
            
        else:
            print(f"✗ ERROR {response.status_code}")
            print(response.json())
            
    except Exception as e:
        print(f"✗ EXCEPTION: {str(e)}")
        print("\nIs the backend running?")
        print("Start it with: python backend\\main.py")


if __name__ == "__main__":
    check_graph_state()
