"""
Quick test script for LLM mood parsing
Run this to test the backend endpoint directly
"""

import requests
import json

API_URL = "http://localhost:8000"

def test_mood_parsing():
    """Test various mood inputs"""
    
    test_cases = [
        "feeling super energized today!",
        "slight headache",
        "tired but happy",
        "amazing energy after that meal",
        "not feeling well, stomachache",
        "great mood and very focused",
        "meh",
        "feeling fantastic and productive!"
    ]
    
    print("=" * 80)
    print("TESTING LLM MOOD PARSING")
    print("=" * 80)
    
    for i, mood_text in enumerate(test_cases, 1):
        print(f"\n[Test {i}] Input: \"{mood_text}\"")
        print("-" * 80)
        
        try:
            response = requests.post(
                f"{API_URL}/log/mood",
                json={"mood_text": mood_text},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ SUCCESS")
                print(f"  Symptoms:    {', '.join(data['symptoms'])}")
                print(f"  Sentiment:   {data['sentiment']}")
                print(f"  Severity:    {data['severity']}")
                print(f"  Description: {data['description']}")
                print(f"  Log IDs:     {', '.join(data['log_ids'])}")
            else:
                print(f"✗ ERROR {response.status_code}")
                print(f"  {response.json().get('detail', 'Unknown error')}")
                
        except requests.exceptions.Timeout:
            print("✗ TIMEOUT - LLM took too long")
        except Exception as e:
            print(f"✗ EXCEPTION: {str(e)}")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print("\nCheck the graph visualization to see all the symptom nodes!")
    print("http://localhost:8000/graph/html")


if __name__ == "__main__":
    # Check if backend is running
    try:
        response = requests.get(f"{API_URL}/", timeout=2)
        if response.status_code == 200:
            print("✓ Backend is running\n")
            test_mood_parsing()
        else:
            print("✗ Backend returned error")
    except:
        print("✗ Backend is not running!")
        print("\nStart it with: python backend\\main.py")
