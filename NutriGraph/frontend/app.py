"""
NutriGraph Streamlit Frontend
Interactive UI for meal tracking and health insights
"""

import streamlit as st
import requests
from PIL import Image
from datetime import datetime
from io import BytesIO
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

def check_api_health():
    """Check if the backend API is running"""
    try:
        response = requests.get(f"{API_URL}/", timeout=2)
        return response.status_code == 200
    except:
        return False


def upload_meal():
    """Upload a meal image to the backend using session state data"""
    try:
        # Check if session state has the data
        if 'current_image_bytes' not in st.session_state:
            st.error("No image data in session state! Please re-upload the image.")
            return None
            
        # Get data from session state
        file_bytes = st.session_state.current_image_bytes
        file_name = st.session_state.current_file_name
        file_type = st.session_state.current_file_type
        
        print(f"[FRONTEND] ========== UPLOAD DEBUG ==========")
        print(f"[FRONTEND] Uploading file: {file_name}")
        print(f"[FRONTEND] File type: {file_type}")
        print(f"[FRONTEND] File size: {len(file_bytes)} bytes")
        print(f"[FRONTEND] Bytes type: {type(file_bytes)}")
        print(f"[FRONTEND] First 20 bytes: {file_bytes[:20]}")
        print(f"[FRONTEND] ===================================")
        
        # Create fresh BytesIO object for upload (requests expects file-like object)
        files = {"file": (file_name, BytesIO(file_bytes), file_type)}
        response = requests.post(f"{API_URL}/meal", files=files, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
            return None
    except requests.exceptions.Timeout:
        print(f"[FRONTEND] ERROR: Timeout uploading meal")
        st.error("Request timed out. The image analysis is taking longer than expected.")
        return None
    except Exception as e:
        print(f"[FRONTEND] ========== EXCEPTION IN UPLOAD ==========")
        print(f"[FRONTEND] Exception type: {type(e).__name__}")
        print(f"[FRONTEND] Exception message: {str(e)}")
        import traceback
        print(f"[FRONTEND] Traceback:")
        traceback.print_exc()
        print(f"[FRONTEND] =======================================")
        st.error(f"Failed to upload meal: {str(e)}")
        return None


def log_symptom(symptom, sentiment="neutral"):
    """Log a symptom to the backend (structured)"""
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


def log_mood_text(mood_text):
    """Log mood from free-text using LLM parsing"""
    try:
        data = {"mood_text": mood_text}
        response = requests.post(f"{API_URL}/log/mood", json=data, timeout=15)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
            return None
    except Exception as e:
        st.error(f"Failed to log mood: {str(e)}")
        return None


def extract_symptom_from_question(question):
    """Use backend LLM to extract symptom from natural language question"""
    try:
        response = requests.post(
            f"{API_URL}/extract-symptom",
            json={"question": question},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json().get("symptom")
        else:
            # Fallback to simple keyword matching
            question_lower = question.lower()
            if "energy" in question_lower or "energetic" in question_lower:
                return "High Energy"
            elif "headache" in question_lower or "migraine" in question_lower:
                return "Headache"
            elif "mood" in question_lower:
                return "Good Mood"
            elif "nausea" in question_lower or "nauseous" in question_lower:
                return "Nausea"
            elif "tired" in question_lower or "fatigue" in question_lower:
                return "Fatigue"
            else:
                return None
    except Exception as e:
        print(f"Failed to extract symptom: {str(e)}")
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

def main():
    # Header
    st.markdown('<div class="main-header">🥑 NutriGraph</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Your AI Health Companion - Track meals, log feelings, discover insights</div>', unsafe_allow_html=True)
    
    # Check API health
    if not check_api_health():
        st.error("Backend API is not running! Please start the FastAPI server first.")
        st.code("cd backend\npython main.py", language="bash")
        st.stop()
    
    # Sidebar
    with st.sidebar:
        st.header("Knowledge Graph Stats")
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
                st.metric("Symptoms", stats.get("symptoms", 0))
            
            st.metric("User Logs", stats.get("user_logs", 0))
        
        st.divider()
        
        # Graph Visualization Button
        st.header("🔍 Graph Visualization")
        if st.button("🌐 View Knowledge Graph"):
            st.session_state.show_graph = True
        
        st.divider()
        
        st.header("How to Use")
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
            # Read the bytes once and store
            if 'current_image_bytes' not in st.session_state or st.session_state.get('current_file_name') != uploaded_file.name:
                print(f"[FRONTEND] ========== FILE READ DEBUG ==========")
                print(f"[FRONTEND] Reading new file: {uploaded_file.name}")
                print(f"[FRONTEND] File type from uploader: {uploaded_file.type}")
                
                file_bytes = uploaded_file.read()
                print(f"[FRONTEND] Bytes read: {len(file_bytes)}")
                print(f"[FRONTEND] First 20 bytes: {file_bytes[:20]}")
                
                st.session_state.current_image_bytes = file_bytes
                st.session_state.current_file_name = uploaded_file.name
                st.session_state.current_file_type = uploaded_file.type
                
                print(f"[FRONTEND] Stored in session state")
                print(f"[FRONTEND] Session state size: {len(st.session_state.current_image_bytes)}")
                print(f"[FRONTEND] ===================================")

            # Display image
            image = Image.open(BytesIO(st.session_state.current_image_bytes))
            st.image(image, caption="Your Meal", width="stretch")

            # Upload button
            if st.button("🔍 Analyze & Log Meal", type="primary"):
                with st.spinner("🤖 Analyzing your meal!"):
                    # Upload using session state data
                    result = upload_meal()
                    
                    if result:
                        st.success(result["message"])
                        
                        # Display results
                        st.subheader("Identified Ingredients:")
                        st.write(", ".join(result["ingredients"]))
                        
                        st.subheader("Nutritional Breakdown:")
                        for ing, nuts in result["nutrients"].items():
                            st.write(f"- *{ing.title()}*: {', '.join(nuts)}")

                        st.session_state.chat_history.append({
                            "type": "meal",
                            "data": result,
                            "timestamp": datetime.now().strftime("%H:%M")
                        })
                        st.rerun()
        
        st.divider()
        
        # LLM-powered mood logging
        st.header("💭 How Are You Feeling?")
        st.write("Describe your mood, energy, or any symptoms in your own words...")
        
        # Text input for mood
        mood_input = st.text_input(
            "Your mood/feeling:",
            placeholder="e.g., feeling super energized today! or slight headache...",
            key="mood_input",
            label_visibility="collapsed"
        )
        
        if st.button("✨ Log Mood with AI", type="primary"):
            if mood_input:
                with st.spinner("🤖 Analyzing your mood with AI..."):
                    result = log_mood_text(mood_input)
                    
                    if result:
                        # Show parsed information
                        st.success(result.get("message", "Mood logged!"))
                        
                        # Display what was identified
                        with st.expander("🔍 AI Analysis", expanded=True):
                            st.write(f"**Identified:** {', '.join(result['symptoms'])}")
                            st.write(f"**Sentiment:** {result['sentiment'].title()}")
                            st.write(f"**Severity:** {result['severity'].title()}")
                            
                        # Add to chat history
                        for symptom in result['symptoms']:
                            st.session_state.chat_history.append({
                                "type": "mood_log",
                                "symptom": symptom,
                                "sentiment": result['sentiment'],
                                "severity": result['severity'],
                                "description": result['description'],
                                "timestamp": datetime.now().strftime("%H:%M")
                            })
                        
                        st.rerun()
            else:
                st.warning("Please describe how you're feeling!")
        
        # Quick buttons (optional, for convenience)
        st.caption("Quick options:")
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            if st.button("⚡ High Energy", use_container_width=True):
                result = log_mood_text("feeling energized and great")
                if result:
                    st.success("✓ Logged!")
                    st.rerun()
        
        with col_b:
            if st.button("😴 Tired", use_container_width=True):
                result = log_mood_text("feeling tired and low energy")
                if result:
                    st.success("✓ Logged!")
                    st.rerun()
        
        with col_c:
            if st.button("🤕 Not Great", use_container_width=True):
                result = log_mood_text("not feeling well")
                if result:
                    st.success("✓ Logged!")
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
                    
                    elif item["type"] == "mood_log":
                        # Display AI-parsed mood
                        sentiment_emoji = {"positive": "😊", "negative": "😔", "neutral": "😐"}
                        emoji = sentiment_emoji.get(item.get('sentiment', 'neutral'), "💭")
                        severity = item.get('severity', 'medium')
                        st.markdown(f"**[{item['timestamp']}] {emoji} {item['symptom']}** ({severity})")
                    
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
        
        if st.button("🔮 Get Insight", type="primary"):
            if not user_input or user_input == "Custom Question":
                st.warning("Please enter a question!")
            else:
                # Determine symptom from question
                if question_type == "Custom Question":
                    # Use LLM to extract symptom from question
                    with st.spinner("🤖 Understanding your question..."):
                        symptom = extract_symptom_from_question(user_input)
                    
                    if not symptom:
                        st.error("Couldn't identify the symptom from your question. Try asking like: 'What causes headaches?' or 'What gives me energy?'")
                        symptom = None
                else:
                    symptom = symptom_map[question_type]
                
                if symptom:
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
    
    # Graph Visualization Modal
    if st.session_state.get('show_graph', False):
        st.divider()
        st.header("🌐 Knowledge Graph Visualization")
        
        # Check if graph has data
        current_stats = get_graph_stats()
        if not current_stats or current_stats.get("total_nodes", 0) == 0:
            st.warning("No data in the graph yet. Upload a meal and log a feeling first!")
            if st.button("✖ Close"):
                st.session_state.show_graph = False
                st.rerun()
        else:
            with st.spinner("Loading graph visualization..."):
                try:
                    response = requests.get(f"{API_URL}/graph/html", timeout=30)
                    
                    if response.status_code == 200:
                        data = response.json()
                        html_content = data.get("html", "")
                        stats = data.get("stats", {})
                        
                        if not html_content:
                            st.error(" Empty HTML content received from server")
                        else:
                            # Display stats
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Nodes", stats.get("total_nodes", 0))
                                st.metric("Meals", stats.get("meals", 0))
                            with col2:
                                st.metric("Edges", stats.get("total_edges", 0))
                                st.metric("Ingredients", stats.get("ingredients", 0))
                            with col3:
                                st.metric("Symptoms", stats.get("symptoms", 0))
                                st.metric("Nutrients", stats.get("nutrients", 0))
                            
                            # Display the interactive graph
                            st.components.v1.html(html_content, height=800, scrolling=True)
                            
                            # Legend
                            st.markdown("""
                            **Legend:**
                            - 🔴 **Red** = Meals
                            - 🔵 **Teal** = Ingredients
                            - 🟢 **Light Green** = Nutrients
                            - 🟡 **Yellow** = User Logs
                            - 🔷 **Light Blue** = Symptoms
                            
                            *Drag nodes to rearrange. Zoom with mouse wheel. Click nodes for details.*
                            """)
                            
                            if st.button("✖ Close Graph"):
                                st.session_state.show_graph = False
                                st.rerun()
                    else:
                        error_detail = response.json().get("detail", "Unknown error") if response.text else "No response"
                        st.error(f"Failed to load graph: Status {response.status_code}")
                        st.error(f"Details: {error_detail}")
                        
                        if st.button("✖ Close"):
                            st.session_state.show_graph = False
                            st.rerun()
                            
                except requests.exceptions.Timeout:
                    st.error("Request timed out. The graph might be too large.")
                    if st.button("✖ Close"):
                        st.session_state.show_graph = False
                        st.rerun()
                        
                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to backend. Is the server running?")
                    if st.button("✖ Close"):
                        st.session_state.show_graph = False
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"❌ Error loading graph: {str(e)}")
                    st.error(f"Error type: {type(e).__name__}")
                    if st.button("✖ Close"):
                        st.session_state.show_graph = False
                        st.rerun()


if __name__ == "__main__":
    main()
