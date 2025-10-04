"""
Debug script to check if correlations exist between meals and symptoms
"""

import requests
import json

API_URL = "http://localhost:8000"

def debug_correlations():
    """Check the actual graph structure for correlations"""
    
    print("=" * 80)
    print("CORRELATION DEBUG")
    print("=" * 80)
    
    try:
        # Get stats
        stats_response = requests.get(f"{API_URL}/graph/stats", timeout=5)
        if stats_response.status_code != 200:
            print("✗ Could not get graph stats")
            return
            
        stats = stats_response.json()
        
        print("\n📊 GRAPH OVERVIEW:")
        print("-" * 80)
        print(f"Meals:      {stats.get('meals', 0)}")
        print(f"User Logs:  {stats.get('user_logs', 0)}")
        print(f"Symptoms:   {stats.get('symptoms', 0)}")
        print(f"Total Edges: {stats.get('total_edges', 0)}")
        
        # Get symptoms
        symptoms_response = requests.get(f"{API_URL}/graph/symptoms", timeout=5)
        if symptoms_response.status_code != 200:
            print("\n⚠️  Could not fetch symptoms")
            symptoms = []
        else:
            symptoms = symptoms_response.json()
        
        print("\n📋 SYMPTOMS LOGGED:")
        print("-" * 80)
        if symptoms:
            for symptom in symptoms:
                print(f"  • {symptom['name']} (experienced {symptom['frequency']} time(s))")
                
                # Try to get correlations for this symptom
                print(f"\n    Testing correlation for '{symptom['name']}'...")
                try:
                    insight_response = requests.get(
                        f"{API_URL}/insight",
                        params={"symptom": symptom['name']},
                        timeout=15
                    )
                    
                    if insight_response.status_code == 200:
                        insight_data = insight_response.json()
                        
                        if insight_data.get('correlated_ingredients'):
                            print(f"    ✓ FOUND CORRELATIONS:")
                            for ing in insight_data['correlated_ingredients'][:5]:
                                print(f"      - {ing['ingredient']}: {ing['count']} time(s)")
                        else:
                            print(f"    ✗ No correlated ingredients found")
                            print(f"    Response: {insight_data.get('insight', 'N/A')}")
                    else:
                        error_detail = insight_response.json().get('detail', 'Unknown error')
                        print(f"    ✗ Error: {error_detail}")
                        
                except Exception as e:
                    print(f"    ✗ Exception: {str(e)}")
        else:
            print("  (none yet)")
        
        print("\n" + "=" * 80)
        print("DIAGNOSIS:")
        print("=" * 80)
        
        if stats.get('meals', 0) == 0:
            print("❌ NO MEALS LOGGED")
            print("   → Upload a meal image first!")
            
        elif stats.get('user_logs', 0) == 0:
            print("❌ NO MOODS LOGGED")
            print("   → Log how you're feeling!")
            
        elif stats.get('total_edges', 0) == 0:
            print("❌ NO EDGES IN GRAPH")
            print("   → Something went wrong with graph creation!")
            
        elif not symptoms:
            print("❌ NO SYMPTOMS IN GRAPH")
            print("   → Mood logging might have failed!")
            
        else:
            # Check if we found any correlations
            has_correlations = False
            for symptom in symptoms:
                try:
                    insight_response = requests.get(
                        f"{API_URL}/insight",
                        params={"symptom": symptom['name']},
                        timeout=15
                    )
                    if insight_response.status_code == 200:
                        insight_data = insight_response.json()
                        if insight_data.get('correlated_ingredients'):
                            has_correlations = True
                            break
                except:
                    pass
            
            if not has_correlations:
                print("⚠️  MEALS AND MOODS EXIST BUT NO CORRELATIONS FOUND")
                print("\nPossible reasons:")
                print("1. Mood was logged BEFORE the meal")
                print("2. Mood was logged >24 hours AFTER the meal")
                print("3. Timestamps are incorrect")
                print("\nSolution:")
                print("- Log a new meal")
                print("- Wait a few minutes")
                print("- Log a mood (should be <24 hours after meal)")
                print("- Try querying again")
            else:
                print("✓ CORRELATIONS FOUND!")
                print("  Graph is working correctly.")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"✗ EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Check if backend is running
    try:
        response = requests.get(f"{API_URL}/", timeout=2)
        if response.status_code == 200:
            print("✓ Backend is running\n")
            debug_correlations()
        else:
            print("✗ Backend returned error")
    except:
        print("✗ Backend is not running!")
        print("\nStart it with: python backend\\main.py")
