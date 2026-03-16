import streamlit as st
import os

def apply_custom_theme():
    """Injects high-end Premium 'ResFit' Design System"""
    st.markdown("""
    <style>
    /* Premium Typography */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=Outfit:wght@700;900&display=swap');

    :root {
        --resfit-orange: #FF5722;
        --resfit-purple: #6200EA;
        --bg-dark: #000000;
        --glass-bg: rgba(20, 20, 25, 0.7);
        --glass-border: rgba(255, 255, 255, 0.1);
    }

    /* Global Background & Base */
    .stApp {
        background: radial-gradient(circle at 0% 0%, rgba(98, 0, 234, 0.15) 0%, transparent 40%),
                    radial-gradient(circle at 100% 100%, rgba(255, 87, 34, 0.1) 0%, transparent 40%),
                    #000000;
        color: #FFFFFF !important;
        font-family: 'Inter', sans-serif;
    }

    h1, h2, h3 {
        font-family: 'Outfit', sans-serif !important;
        letter-spacing: -0.04em !important;
        text-transform: uppercase;
        background: linear-gradient(90deg, #FFFFFF, #B0B0B0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* Premium Glassmorphism Card (Stacked Effect) */
    .premium-card {
        background: var(--glass-bg);
        backdrop-filter: blur(20px) saturate(180%);
        -webkit-backdrop-filter: blur(20px) saturate(180%);
        border: 1px solid var(--glass-border);
        border-radius: 20px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        position: relative;
        overflow: hidden;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }

    .premium-card:hover {
        transform: translateY(-8px);
        border-color: rgba(255, 87, 34, 0.4);
        box-shadow: 0 20px 40px rgba(0,0,0,0.6);
    }

    .premium-card::before {
        content: "";
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255, 87, 34, 0.05) 0%, transparent 70%);
        pointer-events: none;
    }

    /* Stat Chips */
    .stat-chip {
        display: inline-flex;
        align-items: center;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 50px;
        padding: 4px 12px;
        font-size: 0.8rem;
        font-weight: 600;
        color: #B0B0B0;
        margin-right: 8px;
        margin-bottom: 8px;
    }

    .stat-chip b { color: var(--resfit-orange); margin-right: 4px; }

    /* Premium Buttons */
    div.stButton > button {
        background: linear-gradient(135deg, #FF5722 0%, #E64A19 100%);
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 12px 24px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        width: 100%;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(255, 87, 34, 0.3) !important;
    }

    div.stButton > button:hover {
        transform: scale(1.02) !important;
        box-shadow: 0 8px 25px rgba(255, 87, 34, 0.5) !important;
    }

    /* Verdict Cards (Modified specifically for high-end look) */
    .verdict-card {
        border-radius: 16px;
        padding: 1.2rem;
        margin: 1rem 0;
        border-left: 6px solid #ccc;
        background: rgba(255, 255, 255, 0.03);
    }
    .verdict-green { border-color: #00FF88; background: linear-gradient(90deg, rgba(0, 255, 136, 0.05), transparent); }
    .verdict-yellow { border-color: #FFD600; background: linear-gradient(90deg, rgba(255, 214, 0, 0.05), transparent); }
    .verdict-red { border-color: #FF1744; background: linear-gradient(90deg, rgba(255, 23, 68, 0.05), transparent); }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #050505 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }

    /* Custom Scrollbar */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #000; }
    ::-webkit-scrollbar-thumb { background: #333; border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: #444; }

    /* Target Streamlit Native Containers for Card Look */
    [data-testid="stForm"], [data-testid="stExpander"] {
        background: var(--glass-bg) !important;
        backdrop-filter: blur(20px) saturate(180%) !important;
        -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 20px !important;
        padding: 1.5rem !important;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {background: transparent !important;}
    </style>
    """, unsafe_allow_html=True)

def render_sidebar():
    """Shared premium sidebar for all pages"""
    import jwt
    from datetime import datetime, timedelta
    import requests
    from dotenv import load_dotenv
    load_dotenv(".env.local")
    
    # Initialize keys
    if 'auth_token' not in st.session_state: st.session_state.auth_token = None
    if 'api_url' not in st.session_state: st.session_state.api_url = os.getenv("API_URL", "http://127.0.0.1:8000")

    with st.sidebar:
        st.sidebar.markdown("<h2 style='text-align:center;'>RESFIT</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; font-size:0.7rem; color:#666; margin-bottom:2rem;'>V2.0 RESEARCH ENGINE</p>", unsafe_allow_html=True)
        
        # Navigation
        if st.button("🏠 DASHBOARD", width="stretch"): st.switch_page("app.py")
        
        st.markdown("---")
        
        # Auth Section
        if not st.session_state.auth_token:
            st.warning("Locked Mode")
            if st.button("🔑 ACTIVATE DEMO", width="stretch"):
                # Simple JWT for demo - MUST MATCH BACKEND SECRET
                secret = os.getenv("JWT_SECRET", "devsecretapplepie")
                expire = datetime.utcnow() + timedelta(hours=1)
                token = jwt.encode({"sub": "resfit-demo", "exp": expire}, secret, algorithm="HS256")
                st.session_state.auth_token = token
                st.rerun()
        else:
            st.success("Authenticated")
            if st.button("🔓 LOGOUT", width="stretch"):
                st.session_state.auth_token = None
                st.rerun()

        st.markdown("---")
        # System Health
        try:
            r = requests.get(f"{st.session_state.api_url}/health", timeout=1)
            if r.status_code == 200:
                st.markdown("<p style='color:#00FF88; font-size:0.8rem;'>● API ONLINE (V2)</p>", unsafe_allow_html=True)
            else:
                st.markdown("<p style='color:#FF1744; font-size:0.8rem;'>● SYSTEM ERROR</p>", unsafe_allow_html=True)
        except:
            st.markdown("<p style='color:#FF1744; font-size:0.8rem;'>● API OFFLINE</p>", unsafe_allow_html=True)

def render_exercise_card(ex):
    """Renders a single exercise using the high-end Premium Card style"""
    sets = f"{ex['sets'][0]}-{ex['sets'][1]}" if isinstance(ex['sets'], list) else ex['sets']
    reps = f"{ex['reps'][0]}-{ex['reps'][1]}" if isinstance(ex['reps'], list) else ex['reps']
    
    # Handle possible nested list for rest_seconds
    if isinstance(ex['rest_seconds'], list):
        rest = f"{ex['rest_seconds'][0]}-{ex['rest_seconds'][1]}s"
    else:
        rest = f"{ex['rest_seconds']}s"
    
    # Research tag if modified
    validation_tag = ""
    if ex.get('modified_by_research'):
        validation_tag = '<span style="float:right; font-size:0.7rem; color:#00FF88; border:1px solid #00FF88; padding:2px 8px; border-radius:10px;">VALIDATED</span>'

    # NO INDENTATION in the following string to prevent markdown code blocks
    html = f"""<div class="premium-card">
{validation_tag}
<h3 style="margin-top:0; font-size:1.3rem; margin-bottom:0.5rem; color:white;">{ex['name'].upper()}</h3>
<div style="margin-bottom:1rem;">
<span class="stat-chip"><b>SETS:</b> {sets}</span>
<span class="stat-chip"><b>REPS:</b> {reps}</span>
<span class="stat-chip"><b>REST:</b> {rest}</span>
<span class="stat-chip"><b>RPE:</b> {ex.get('rpe', '7-8')}</span>
</div>
<p style="color:#b3b3b3; font-size:0.9rem; margin-bottom:0.5rem;"><b>Tempo:</b> {ex.get('tempo', '2-0-1-0')}</p>
<div style="background:rgba(255,87,34,0.1); padding:8px 12px; border-radius:10px; border-left:3px solid var(--resfit-orange);">
<p style="color:#FFCCBC; font-size:0.8rem; margin:0;"><i>{ex.get('pro_notes', 'Focus on explosive concentric phase and controlled eccentric.')}</i></p>
</div>
</div>"""
    st.markdown(html, unsafe_allow_html=True)
