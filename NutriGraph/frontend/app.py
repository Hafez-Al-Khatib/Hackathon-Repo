"""
NutriGraph Streamlit Frontend
Interactive UI for meal tracking and health insights
"""

import streamlit as st
import requests
from PIL import Image
from datetime import datetime
import json

# Backend API URL
API_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(
    page_title="NutriGraph - AI Health Companion",
    page_icon="🥑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #4ECDC4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #95E1D3;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #4ECDC4;
        color: white;
        font-weight: bold;
        border-radius: 10px;
        padding: 0.5rem 1rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 10px;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .insight-box {
        padding: 1.5rem;
        border-radius: 10px;
        background-color: #fff3cd;
        border: 2px solid #ffc107;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'graph_stats' not in st.session_state:
    st.session_state.graph_stats = {}

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def check_api_health():
    """Check if the backend API is running"""
    try:
        response = requests.get(f"{API_URL}/", timeout=2)
        return response.status_code == 200
    except:
        return False


def upload_meal(image_file):
    """Upload a meal image to the backend"""
    try:
        files = {"file": (image_file.name, image_file, image_file.type)}
        response = requests.post(f"{API_URL}/meal", files=files, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
            return None
    except requests.exceptions.Timeout:
        st.error("Request timed out. The image analysis is taking longer than expected.")
        return None
    except Exception as e:
        st.error(f"Failed to upload meal: {str(e)}")
        return None


def log_symptom(symptom, sentiment="neutral"):
    """Log a symptom to the backend"""
    try:
        data = {
            "symptom": symptom,
            "sentiment": sentiment
        }
        response = requests.post(f"{API_URL}/log", json=data, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
            return None
    except Exception as e:
        st.error(f"Failed to log symptom: {str(e)}")
        return None


def get_insight(symptom):
    """Query insights from the backend"""
    try:
        response = requests.get(f"{API_URL}/insight", params={"symptom": symptom}, timeout=15)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
            return None
    except Exception as e:
        st.error(f"Failed to get insight: {str(e)}")
        return None


def get_graph_stats():
    """Get current graph statistics"""
    try:
        response = requests.get(f"{API_URL}/graph/stats", timeout=5)
        if response.status_code == 200:
            return response.json()
        return {}
    except:
        return {}


# ==============================================================================
# MAIN APP
# ==============================================================================

def main():
    # Header
    st.markdown('<div class="main-header">🥑 NutriGraph</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Your AI Health Companion - Track meals, log feelings, discover insights</div>', unsafe_allow_html=True)
    
    # Check API health
    if not check_api_health():
        st.error("⚠️ Backend API is not running! Please start the FastAPI server first.")
        st.code("cd backend\npython main.py", language="bash")
        st.stop()
    
    # Sidebar
    with st.sidebar:
        st.header("📊 Knowledge Graph Stats")
        stats = get_graph_stats()
        st.session_state.graph_stats = stats
        
        if stats:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Nodes", stats.get("total_nodes", 0))
                st.metric("Meals", stats.get("meals", 0))
                st.metric("Ingredients", stats.get("ingredients", 0))
            with col2:
                st.metric("Total Edges", stats.get("total_edges", 0))
                st.metric("Nutrients", stats.get("nutrients", 0))
                st.metric("Symptom Logs", stats.get("user_logs", 0))
        
        st.divider()
        
        st.header("ℹ️ How to Use")
        st.markdown("""
        1. **Upload Meal**: Take a photo of your food
        2. **Log Feelings**: Note how you feel after eating
        3. **Ask Questions**: Get AI-powered insights
        """)
        
        if st.button("🔄 Refresh Stats"):
            st.rerun()
    
    # Main content - Two columns
    col1, col2 = st.columns([1, 1])
    
    # LEFT COLUMN - Meal Upload
    with col1:
        st.header("📷 Upload a Meal")
        
        uploaded_file = st.file_uploader(
            "Take a photo of your meal",
            type=["jpg", "jpeg", "png"],
            help="Upload an image of your meal for AI analysis"
        )
        
        if uploaded_file is not None:
            # Display the image
            image = Image.open(uploaded_file)
            st.image(image, caption="Your Meal", use_column_width=True)
            
            # Upload button
            if st.button("🔍 Analyze & Log Meal", type="primary"):
                with st.spinner("🤖 Analyzing your meal with AI..."):
                    result = upload_meal(uploaded_file)
                    
                    if result:
                        st.success("✅ " + result["message"])
                        
                        # Display results
                        st.subheader("Identified Ingredients:")
                        ingredients_text = ", ".join(result["ingredients"])
                        st.write(f"🥗 {ingredients_text}")
                        
                        st.subheader("Nutritional Breakdown:")
                        nutrients = result["nutrients"]
                        for ingredient, nutrient_list in nutrients.items():
                            nutrients_str = ", ".join(nutrient_list)
                            st.write(f"• **{ingredient.title()}**: {nutrients_str}")
                        
                        # Add to chat history
                        st.session_state.chat_history.append({
                            "type": "meal",
                            "data": result,
                            "timestamp": datetime.now().strftime("%H:%M")
                        })
                        
                        st.rerun()
        
        st.divider()
        
        # Quick symptom logging
        st.header("📝 Quick Log")
        st.write("How are you feeling right now?")
        
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            if st.button("⚡ High Energy", use_container_width=True):
                result = log_symptom("High Energy", "positive")
                if result:
                    st.success("✅ Logged: High Energy")
                    st.session_state.chat_history.append({
                        "type": "log",
                        "symptom": "High Energy",
                        "sentiment": "positive",
                        "timestamp": datetime.now().strftime("%H:%M")
                    })
                    st.rerun()
        
        with col_b:
            if st.button("😊 Good Mood", use_container_width=True):
                result = log_symptom("Good Mood", "positive")
                if result:
                    st.success("✅ Logged: Good Mood")
                    st.session_state.chat_history.append({
                        "type": "log",
                        "symptom": "Good Mood",
                        "sentiment": "positive",
                        "timestamp": datetime.now().strftime("%H:%M")
                    })
                    st.rerun()
        
        with col_c:
            if st.button("🤕 Headache", use_container_width=True):
                result = log_symptom("Headache", "negative")
                if result:
                    st.success("✅ Logged: Headache")
                    st.session_state.chat_history.append({
                        "type": "log",
                        "symptom": "Headache",
                        "sentiment": "negative",
                        "timestamp": datetime.now().strftime("%H:%M")
                    })
                    st.rerun()
    
    # RIGHT COLUMN - Chat Interface
    with col2:
        st.header("💬 Chat with Your AI Health Agent")
        
        # Display chat history
        chat_container = st.container(height=400)
        
        with chat_container:
            if not st.session_state.chat_history:
                st.info("👋 Start by uploading a meal or logging how you feel!")
            else:
                for item in st.session_state.chat_history:
                    if item["type"] == "meal":
                        data = item["data"]
                        st.markdown(f"**[{item['timestamp']}] 🍽️ Meal Logged**")
                        st.write(f"Ingredients: {', '.join(data['ingredients'][:3])}...")
                    
                    elif item["type"] == "log":
                        st.markdown(f"**[{item['timestamp']}] 📝 Feeling: {item['symptom']}**")
                    
                    elif item["type"] == "insight":
                        st.markdown(f"**[{item['timestamp']}] 🤖 Agent:**")
                        st.markdown(f'<div class="insight-box">{item["insight"]}</div>', unsafe_allow_html=True)
                        
                        if item.get("correlations"):
                            st.write("**Top correlated ingredients:**")
                            for ing in item["correlations"][:3]:
                                st.write(f"• {ing['ingredient']} ({ing['count']} time(s))")
        
        st.divider()
        
        # Chat input
        st.subheader("Ask a Question")
        
        # Predefined questions
        question_type = st.radio(
            "Choose a question type:",
            ["Custom Question", "What gives me energy?", "What causes headaches?", "What improves my mood?"],
            horizontal=True
        )
        
        if question_type == "Custom Question":
            user_input = st.text_input(
                "Type your question:",
                placeholder="e.g., What foods make me feel energetic?"
            )
        else:
            # Extract symptom from predefined question
            symptom_map = {
                "What gives me energy?": "High Energy",
                "What causes headaches?": "Headache",
                "What improves my mood?": "Good Mood"
            }
            user_input = question_type
        
        if st.button("🔮 Get Insight", type="primary", use_container_width=True):
            if not user_input or user_input == "Custom Question":
                st.warning("Please enter a question!")
            else:
                # Determine symptom from question
                if question_type == "Custom Question":
                    # Simple keyword matching
                    symptom = "High Energy"  # Default
                    if "energy" in user_input.lower() or "energetic" in user_input.lower():
                        symptom = "High Energy"
                    elif "headache" in user_input.lower():
                        symptom = "Headache"
                    elif "mood" in user_input.lower():
                        symptom = "Good Mood"
                    elif "sluggish" in user_input.lower() or "tired" in user_input.lower():
                        symptom = "Sluggish"
                else:
                    symptom = symptom_map[question_type]
                
                with st.spinner("🤔 Analyzing your health patterns..."):
                    insight_data = get_insight(symptom)
                    
                    if insight_data:
                        # Add to chat history
                        st.session_state.chat_history.append({
                            "type": "insight",
                            "symptom": symptom,
                            "insight": insight_data["insight"],
                            "correlations": insight_data["correlated_ingredients"],
                            "timestamp": datetime.now().strftime("%H:%M")
                        })
                        
                        st.rerun()
        
        # Clear chat button
        if st.button("🗑️ Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()


if __name__ == "__main__":
    main()
