import streamlit as st
import os
from style import apply_custom_theme, render_sidebar, render_exercise_card

# Page config
st.set_page_config(
    page_title="ResFit | Research-Backed Performance",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply the Premium ResFit aesthetic
apply_custom_theme()

# Initialize session state (MUST happen before render_sidebar)
if 'current_workout' not in st.session_state: st.session_state.current_workout = None
if 'workout_history' not in st.session_state: st.session_state.workout_history = []
if 'api_url' not in st.session_state: st.session_state.api_url = os.getenv("API_URL", "http://127.0.0.1:8000")
if 'auth_token' not in st.session_state: st.session_state.auth_token = None

# Global Navigation
render_sidebar()

# Hero Section
st.markdown("<br><br>", unsafe_allow_html=True)
col1, col2 = st.columns([1.1, 1], gap="large")

with col1:
    st.markdown("""
    <h1 style='font-size: 5rem; margin-bottom: 0;'>RESFIT</h1>
    <h2 style='font-size: 1.5rem; color: #FF5722; margin-top: -10px;'>PRECISION RESEARCH ENGINE</h2>
    <p style='font-size: 1.2rem; color: #888; margin: 2rem 0;'>
        Stop following generic routines. ResFit cross-references your training against <b>Hybrid RAG Validation</b> 
        to ensure every rep is backed by the latest sports science (2023-2025).
    </p>
    """, unsafe_allow_html=True)
    
    if st.button("🚀 GENERATE WORKOUT"):
        st.switch_page("pages/1_Generate_Workout.py")

with col2:
    st.image("src/streamlit_app/assets/resfit_banner.png", width="stretch")

st.markdown("<br><br>", unsafe_allow_html=True)

# Feature Grid
f1, f2, f3 = st.columns(3, gap="medium")

with f1:
    st.markdown("""
    <div class="premium-card">
        <h3 style="color:#FF5722;">🔬 HYBRID RAG</h3>
        <p style="color:#888; font-size: 0.9rem;">Real-time validation via Perplexity & Tavily across NIH PubMed & ScienceDirect.</p>
    </div>
    """, unsafe_allow_html=True)

with f2:
    st.markdown("""
    <div class="premium-card">
        <h3 style="color:#FF5722;">⛓️ ADAPTIVE SWAPS</h3>
        <p style="color:#888; font-size: 0.9rem;">The Green/Yellow/Red verdict system ensures substitutions maintain physiological target.</p>
    </div>
    """, unsafe_allow_html=True)

with f3:
    st.markdown("""
    <div class="premium-card">
        <h3 style="color:#FF5722;">🏛️ MOBILE APP FRIENDLY</h3>
        <p style="color:#888; font-size: 0.9rem;">Engineered for mobile-first performance. Premium aesthetics for professional coaches.</p>
    </div>
    """, unsafe_allow_html=True)
