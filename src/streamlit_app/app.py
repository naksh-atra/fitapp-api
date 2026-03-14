import streamlit as st
import os
from style import apply_cult_theme, render_sidebar, render_exercise_card

# Page config
st.set_page_config(
    page_title="FitApp | Premium Science-Based Training",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply the Cult.fit aesthetic
apply_cult_theme()

# Initialize session state (MUST happen before render_sidebar)
if 'current_workout' not in st.session_state:
    st.session_state.current_workout = None
if 'workout_history' not in st.session_state:
    st.session_state.workout_history = []
if 'api_url' not in st.session_state:
    st.session_state.api_url = "http://127.0.0.1:8000"
if 'auth_token' not in st.session_state:
    st.session_state.auth_token = None

# Global Navigation
render_sidebar()

# Hero Section
col1, col2 = st.columns([1.2, 1])

with col1:
    st.title("THE FUTURE OF PERFORMANCE")
    st.markdown("""
    ## Science-Backed. Research-Validated.
    
    FitApp leverages **Hybrid RAG (Tavily + Perplexity)** to cross-reference every exercise prescription against thousands of medical RCTs and sports science meta-analyses (2023-2025).
    
    *Don't just train. Train with evidence.*
    """)
    
    if st.button("🚀 Start My Validation"):
        st.switch_page("pages/1_Generate_Workout.py")

with col2:
    st.image("C:/Users/Acer/.gemini/antigravity/brain/0c349c4c-bd2e-42bf-b97c-9c555324e420/cultfit_hero_banner_1773498627124.png", use_container_width=True)

st.markdown("---")

# Feature Cards
f1, f2, f3 = st.columns(3)
with f1:
    st.markdown("""
    <div class="exercise-card">
        <h3>🔬 Medical RAG</h3>
        <p style="color:#b3b3b3;">Real-time validation against NIH PubMed and ScienceDirect databases.</p>
    </div>
    """, unsafe_allow_html=True)
with f2:
    st.markdown("""
    <div class="exercise-card">
        <h3>⚖️ Swap Verdicts</h3>
        <p style="color:#b3b3b3;">Our <b>Green/Yellow/Red</b> system ensures substitutions never compromise your goal.</p>
    </div>
    """, unsafe_allow_html=True)
with f3:
    st.markdown("""
    <div class="exercise-card">
        <h3>📄 Smart Export</h3>
        <p style="color:#b3b3b3;">Generate professional PDFs including full research citations for your coach.</p>
    </div>
    """, unsafe_allow_html=True)
