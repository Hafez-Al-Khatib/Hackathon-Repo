import streamlit as st
import requests
from PIL import Image
from datetime import datetime
from io import BytesIO
import json

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="NutriGraph - Smart Health Tracking",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional, modern styling
st.markdown("""
<style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Main container */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Header */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.2);
    }
    
    .main-title {
        font-size: 3rem;
        font-weight: 700;
        color: white;
        margin: 0;
        text-align: center;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    .subtitle {
        font-size: 1.3rem;
        color: rgba(255,255,255,0.9);
        text-align: center;
        margin-top: 0.5rem;
        font-weight: 300;
    }
    
    /* Cards */
    .card {
        background: white;
        padding: 2rem;
        border-radius: 16px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.08);
        margin: 1rem 0;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.12);
    }
    
    /* Insight card */
    .insight-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 16px;
        margin: 1.5rem 0;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
    }
    
    .insight-card h3 {
        margin-top: 0;
        font-size: 1.5rem;
        font-weight: 600;
    }
    
    /* Stats */
    .stat-box {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        transition: transform 0.2s;
    }
    
    .stat-box:hover {
        transform: scale(1.05);
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .stat-label {
        color: #7F8C8D;
        font-size: 0.9rem;
        margin-top: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: white;
        border-radius: 12px;
        padding: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    /* Input fields */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        border-radius: 8px;
        border: 2px solid #e0e0e0;
        padding: 0.75rem;
        transition: border-color 0.3s;
    }
    
    .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Success/Error messages */
    .stSuccess {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        border-radius: 8px;
    }
    
    .stError {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        border-radius: 8px;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: white;
    }
    
    /* File uploader */
    .stFileUploader {
        border: 2px dashed #667eea;
        border-radius: 12px;
        padding: 2rem;
        background: rgba(102, 126, 234, 0.05);
    }
</style>
""", unsafe_allow_html=True)

if 'history' not in st.session_state:
    st.session_state.history = []

def check_backend():
    try:
        response = requests.get(f"{API_URL}/", timeout=2)
        return response.status_code == 200
    except:
        return False

def upload_meal(file_bytes, filename, file_type):
    try:
        files = {'file': (filename, file_bytes, file_type)}
        response = requests.post(f"{API_URL}/meal", files=files, timeout=30)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        st.error(f"Upload failed: {str(e)}")
        return None

def log_mood(text):
    try:
        response = requests.post(
            f"{API_URL}/log/mood",
            json={"mood_text": text},
            timeout=15
        )
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        st.error(f"Logging failed: {str(e)}")
        return None

def get_insight(symptom):
    try:
        response = requests.get(
            f"{API_URL}/insight",
            params={"symptom": symptom},
            timeout=15
        )
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        st.error(f"Insight failed: {str(e)}")
        return None

def extract_symptom(question):
    try:
        response = requests.post(
            f"{API_URL}/extract-symptom",
            json={"question": question},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()  # Returns full dict with symptom, intent, or chat response
        return None
    except:
        return None

def get_graph_stats():
    try:
        response = requests.get(f"{API_URL}/graph/stats", timeout=5)
        return response.json() if response.status_code == 200 else {}
    except:
        return {}

def get_graph_html():
    try:
        response = requests.get(f"{API_URL}/graph/html", timeout=10)
        return response.json().get("html") if response.status_code == 200 else None
    except:
        return None

# Main Header
st.markdown("""
<div class="main-header">
    <div class="main-title">🥗 NutriGraph</div>
    <div class="subtitle">Discover how food affects your health with AI-powered insights</div>
</div>
""", unsafe_allow_html=True)

if not check_backend():
    st.error("**Backend Not Connected** - Start the server: `python backend/main.py`")
    st.stop()

# Sidebar with styled stats
with st.sidebar:
    st.markdown("### 📊 Your Health Data")
    st.markdown("---")
    
    stats = get_graph_stats()
    
    # Custom styled stat boxes
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-number">{stats.get("meals", 0)}</div>
        <div class="stat-label">Meals Logged</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-number">{stats.get("ingredients", 0)}</div>
        <div class="stat-label">Ingredients</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-number">{stats.get("symptoms", 0)}</div>
        <div class="stat-label">Symptoms Tracked</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-number">{stats.get("user_logs", 0)}</div>
        <div class="stat-label">Total Entries</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📈 View Graph", use_container_width=True):
            st.session_state.show_graph = True
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    st.markdown("---")
    st.markdown("#### 💡 Tips")
    st.info("Log meals regularly for better insights!", icon="📸")
    st.info("Describe symptoms in detail", icon="💭")

# Main area
tab1, tab2, tab3 = st.tabs(["📸 Log Meal", "💭 Log Feeling", "🔍 Ask Questions"])

with tab1:
    st.markdown("### 📸 Log Your Meal")
    st.markdown("Take a photo or upload one - AI will identify ingredients automatically")
    st.markdown("")
    
    # Two options: Camera or Upload
    option = st.radio(
        "Choose input method:",
        ["📷 Take Photo", "📁 Upload Photo"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    meal_image = None
    image_bytes = None
    filename = None
    content_type = None
    
    if option == "📷 Take Photo":
        st.markdown("#### 📷 Take a Photo with Your Camera")
        camera_photo = st.camera_input("Snap a picture of your meal")
        
        if camera_photo:
            meal_image = Image.open(camera_photo)
            image_bytes = camera_photo.getvalue()
            filename = f"camera_capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            content_type = "image/jpeg"
    else:
        st.markdown("#### 📁 Upload a Photo")
        uploaded_file = st.file_uploader(
            "Choose an image",
            type=["jpg", "jpeg", "png"],
            help="Take a clear photo of your meal for best results"
        )
        
        if uploaded_file:
            meal_image = Image.open(uploaded_file)
            image_bytes = uploaded_file.getvalue()
            filename = uploaded_file.name
            content_type = uploaded_file.type
    
    # Display and analyze
    if meal_image:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.image(meal_image, caption="Your meal", use_container_width=True)
        
        with col2:
            st.markdown("#### 🤖 AI Analysis")
            st.write("Our AI will:")
            st.write("Identify ingredients")
            st.write("Extract nutritional info")
            st.write("Add to your health graph")
            st.markdown("")
            
            if st.button("🔍 Analyze This Meal", type="primary", use_container_width=True):
                with st.spinner("🧠 Analyzing your meal..."):
                    result = upload_meal(image_bytes, filename, content_type)
                    
                    if result:
                        st.success("✅ Meal logged successfully!")
                        st.markdown("**Identified ingredients:**")
                        
                        # Display ingredients in a nice format
                        ingredients = result.get("ingredients", [])
                        for i, ing in enumerate(ingredients, 1):
                            st.markdown(f"`{i}.` **{ing}**")
                        
                        st.balloons()
                        
                        st.session_state.history.append({
                            "type": "meal",
                            "data": result,
                            "time": datetime.now().strftime("%H:%M")
                        })
    else:
        if option == "📷 Take Photo":
            st.info("📱 Click the camera button above to take a photo", icon="👆")
        else:
            st.info("📂 Upload a meal photo to get started", icon="👆")

with tab2:
    st.markdown("### 💭 Log Your Feelings")
    st.markdown("Tell us how you're feeling - our AI will extract symptoms and patterns")
    st.markdown("")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        mood = st.text_area(
            "How are you feeling?",
            placeholder="e.g., I feel energized and focused today\nor: My stomach is upset and I have a headache",
            height=150,
            help="Be specific! Mention energy levels, digestion, mood, pain, etc."
        )
    
    with col2:
        st.markdown("#### 💡 Examples")
        st.markdown("`Feeling tired`")
        st.markdown("`Very energetic!`")
        st.markdown("`Headache and nausea`")
        st.markdown("`Stomach feels off`")
    
    st.markdown("")
    
    if st.button("📝 Log This Feeling", type="primary", use_container_width=True):
        if mood:
            with st.spinner("🤖 Analyzing your feelings..."):
                result = log_mood(mood)
                
                if result:
                    symptoms = result.get("symptoms", [])
                    sentiment = result.get("sentiment", "neutral")
                    
                    emotion_emoji = {"positive": "😊", "negative": "😔", "neutral": "😐"}
                    
                    st.success(f"✅ Feeling logged!")
                    
                    # Display in a nice card
                    st.markdown(f"""
                    <div style="background: white; padding: 1.5rem; border-radius: 12px; border-left: 4px solid #667eea;">
                        <p><strong>{emotion_emoji[sentiment]} Sentiment:</strong> {sentiment.title()}</p>
                        <p><strong>🏷️ Detected symptoms:</strong></p>
                        <ul>
                            {"".join([f"<li>{s}</li>" for s in symptoms])}
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.session_state.history.append({
                        "type": "feeling",
                        "data": result,
                        "time": datetime.now().strftime("%H:%M")
                    })
        else:
            st.warning("Please describe how you're feeling first")

with tab3:
    st.markdown("### 🔍 Ask Questions About Your Health")
    st.markdown("Use natural language to discover patterns in your data")
    st.markdown("")
    
    # Quick questions
    st.markdown("#### ⚡ Quick Questions")
    quick_questions = [
        "What gives me energy?",
        "What causes headaches?",
        "What makes me feel tired?"
    ]
    
    selected = st.pills("Popular questions:", quick_questions, selection_mode="single")
    
    st.markdown("---")
    
    # Custom question
    st.markdown("#### 💬 Ask Your Own Question")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        custom_question = st.text_input(
            "Type your question:",
            placeholder="e.g., What helps with nausea? or What causes bloating?",
            label_visibility="collapsed"
        )
    
    with col2:
        ask_button = st.button("🔎 Get Answer", type="primary", use_container_width=True)
    
    question = selected if selected else custom_question
    
    if ask_button:
        if question:
            with st.spinner("🧠 Analyzing your health data..."):
                result_data = extract_symptom(question)
                
                # Check if it's a chat response
                if result_data and result_data.get("intent") == "chat":
                    st.info(result_data.get("response", "Hello!"), icon="👋")
                else:
                    symptom = result_data.get("symptom") if result_data else None
                    intent = result_data.get("intent", "cause") if result_data else "cause"
                    
                    if symptom:
                        # Get insight with intent
                        response = requests.get(
                            f"{API_URL}/insight",
                            params={"symptom": symptom, "intent": intent},
                            timeout=15
                        )
                        result = response.json() if response.status_code == 200 else None
                        
                        if result:
                            # Display insight in styled card
                            st.markdown(f"""
                            <div class="insight-card">
                                <h3>💡 {"Health Insight" if intent == "cause" else "Helpful Solutions"}</h3>
                                <p style="font-size: 1.1rem; line-height: 1.6;">{result['insight']}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Display correlations
                            correlations = result.get("correlated_ingredients", [])
                            if correlations:
                                st.markdown("### 🍽️ Related Foods")
                                
                                # Display in columns
                                cols = st.columns(3)
                                for idx, item in enumerate(correlations[:6]):
                                    with cols[idx % 3]:
                                        st.markdown(f"""
                                        <div style="background: white; padding: 1rem; border-radius: 8px; text-align: center; margin-bottom: 0.5rem;">
                                            <div style="font-size: 1.5rem; font-weight: 600; color: #667eea;">{item['count']}</div>
                                            <div style="color: #7F8C8D; font-size: 0.9rem;">{item['ingredient']}</div>
                                        </div>
                                        """, unsafe_allow_html=True)
                        else:
                            st.info("📊 Not enough data yet. Log more meals and feelings to discover patterns!", icon="💡")
                    else:
                        st.warning("🤔 Couldn't understand the question. Try asking about specific symptoms or foods!")
        else:
            st.warning("⚠️ Please select or type a question first")

# Recent Activity Section
if st.session_state.history:
    st.markdown("---")
    st.markdown("### 📜 Recent Activity")
    
    with st.expander("View History", expanded=False):
        for item in reversed(st.session_state.history[-10:]):
            if item["type"] == "meal":
                st.markdown(f"""
                <div style="background: white; padding: 0.75rem; border-radius: 8px; margin-bottom: 0.5rem; border-left: 3px solid #667eea;">
                    <span style="color: #667eea; font-weight: 600;">🍽️ {item['time']}</span> - Logged meal
                </div>
                """, unsafe_allow_html=True)
            elif item["type"] == "feeling":
                symptoms = item["data"].get("symptoms", [])
                st.markdown(f"""
                <div style="background: white; padding: 0.75rem; border-radius: 8px; margin-bottom: 0.5rem; border-left: 3px solid #764ba2;">
                    <span style="color: #764ba2; font-weight: 600;">💭 {item['time']}</span> - {', '.join(symptoms)}
                </div>
                """, unsafe_allow_html=True)

# Graph view
if st.session_state.get("show_graph", False):
    st.markdown("---")
    st.markdown("""
    <div style="background: white; padding: 2rem; border-radius: 16px; margin-top: 2rem;">
        <h2 style="color: #2C3E50; margin-bottom: 1rem;">🕸️ Your Food & Health Network</h2>
        <p style="color: #7F8C8D; margin-bottom: 1.5rem;">Interactive visualization of relationships between your meals, ingredients, and symptoms</p>
    </div>
    """, unsafe_allow_html=True)
    
    html = get_graph_html()
    if html:
        st.components.v1.html(html, height=700, scrolling=True)
    else:
        st.info("📊 No graph data yet. Start by logging some meals and feelings!", icon="💡")
    
    if st.button("❌ Close Graph", use_container_width=True):
        st.session_state.show_graph = False
        st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #7F8C8D; padding: 2rem;">
    <p>Made with ❤️ using AI, Knowledge Graphs, and Graph ML</p>
    <p style="font-size: 0.9rem;">Powered by Google Gemini AI | NetworkX | Sentence Transformers</p>
</div>
""", unsafe_allow_html=True)
