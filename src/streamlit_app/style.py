import streamlit as st

def apply_cult_theme():
    st.markdown("""
<style>
/* Base Dark Theme & Typography */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&family=Outfit:wght@500;800&display=swap');

:root {
    --primary-color: #FF5722;
    --secondary-color: #FF9100;
    --bg-dark: #0f0f0f;
    --card-bg: rgba(255, 87, 34, 0.05);
    --card-border: rgba(255, 87, 34, 0.15);
    --text-main: #ffffff;
    --text-dim: #b3b3b3;
}

/* Global Styles */
.main {
    background-color: var(--bg-dark);
}

div[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 100%);
}

h1, h2, h3 {
    font-family: 'Outfit', sans-serif !important;
    font-weight: 800 !important;
    background: linear-gradient(90deg, #FF5722 0%, #FF9100 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -1px;
}

p, span, div {
    font-family: 'Inter', sans-serif;
}

/* Glassmorphic Card */
.exercise-card {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 87, 34, 0.2);
    border-radius: 20px;
    padding: 24px;
    margin-bottom: 20px;
    backdrop-filter: blur(12px);
    transition: all 0.3s ease;
}

.exercise-card:hover {
    border-color: #FF5722;
    transform: translateY(-5px);
    box-shadow: 0 10px 30px rgba(255, 87, 34, 0.1);
}

.stat-label {
    color: var(--text-dim);
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.stat-value {
    color: var(--text-main);
    font-size: 1.2rem;
    font-weight: 700;
}

/* Custom Alerts */
.verdict-green {
    background: rgba(76, 175, 80, 0.1);
    border-left: 5px solid #4CAF50;
    padding: 15px;
    border-radius: 10px;
    color: #a8e6c1;
}

.verdict-yellow {
    background: rgba(255, 152, 0, 0.1);
    border-left: 5px solid #FF9800;
    padding: 15px;
    border-radius: 10px;
    color: #ffcb9a;
}

.verdict-red {
    background: rgba(244, 67, 54, 0.1);
    border-left: 5px solid #F44336;
    padding: 15px;
    border-radius: 10px;
    color: #ff9a9a;
}

/* Buttons */
.stButton>button {
    background: linear-gradient(90deg, #FF5722 0%, #FF9100 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 50px !important;
    font-weight: 700 !important;
    padding: 10px 30px !important;
    transition: all 0.3s ease !important;
}

.stButton>button:hover {
    transform: scale(1.05) !important;
    box-shadow: 0 5px 15px rgba(255, 87, 34, 0.4) !important;
}

/* Hide Streamlit components but keep sidebar toggle */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

</style>
    """, unsafe_allow_html=True)

def render_sidebar():
    """Shared sidebar logic for all pages"""
    import jwt
    from datetime import datetime, timedelta
    import requests
    
    # Initialize keys if they don't exist (safety for sub-pages)
    if 'auth_token' not in st.session_state:
        st.session_state.auth_token = None
    if 'current_workout' not in st.session_state:
        st.session_state.current_workout = None
    if 'api_url' not in st.session_state:
        st.session_state.api_url = "http://127.0.0.1:8000"

    # 🏠 NAVIGATION
    st.sidebar.title("🚀 NAVIGATION")
    if st.sidebar.button("🏠 Back to Home", use_container_width=True):
        st.switch_page("app.py")
    
    st.sidebar.markdown("---")
    
    # 🔐 AUTHENTICATION
    st.sidebar.title("🔐 AUTHENTICATION")
    if not st.session_state.auth_token:
        st.sidebar.warning("Not authenticated")
        if st.sidebar.button("🔑 Generate Demo Token", use_container_width=True):
            try:
                JWT_SECRET = "devsecretapplepie"
                JWT_ALGORITHM = "HS256"
                expire = datetime.utcnow() + timedelta(minutes=60)
                token = jwt.encode({"sub": "demo-user-123", "exp": expire}, JWT_SECRET, algorithm=JWT_ALGORITHM)
                st.session_state.auth_token = token
                st.sidebar.success("✅ Token Generated")
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"Error: {e}")
    else:
        st.sidebar.success("🟢 Authenticated")
        if st.sidebar.button("Logout", use_container_width=True):
            st.session_state.auth_token = None
            st.rerun()

    st.sidebar.markdown("---")
    
    # 📊 STATUS
    st.sidebar.title("📊 WORKOUT STATUS")
    if st.session_state.current_workout:
        workout = st.session_state.current_workout
        st.sidebar.info(f"""
        **Current:** {workout['goal'].title()}
        **Exercises:** {len(workout['exercises'])}
        **ID:** `{workout['workout_id'][:8]}...`
        """)
    else:
        st.sidebar.caption("No workout active")

    # 🌐 API STATUS
    st.sidebar.markdown("---")
    try:
        response = requests.get(f"{st.session_state.api_url}/health", timeout=2)
        if response.status_code == 200:
            st.sidebar.success("🟢 API ONLINE")
        else:
            st.sidebar.error("🔴 API ERROR")
    except:
        st.sidebar.error("🔴 API OFFLINE")

def render_exercise_card(name, sets, reps, notes=""):
    st.markdown(f"""
    <div class="exercise-card">
        <h3 style="margin:0; font-size:1.4rem;">{name}</h3>
        <div style="display: flex; gap: 40px; margin-top: 15px;">
            <div>
                <div class="stat-label">Sets</div>
                <div class="stat-value">{sets}</div>
            </div>
            <div>
                <div class="stat-label">Reps</div>
                <div class="stat-value">{reps}</div>
            </div>
        </div>
        {f'<div style="margin-top:15px; color:#b3b3b3; font-size:0.9rem;"><b>Pro Note:</b> {notes}</div>' if notes else ''}
    </div>
    """, unsafe_allow_html=True)
