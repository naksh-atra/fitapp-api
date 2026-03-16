import streamlit as st
import sys
import os
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from api_client import FitAppAPI
from style import apply_custom_theme, render_exercise_card, render_sidebar

# Page config
st.set_page_config(
    page_title="ResFit | Workout Generator",
    page_icon="⚡",
    layout="wide"
)

# Apply the Premium ResFit aesthetic
apply_custom_theme()
render_sidebar()

st.markdown("<h1 style='font-size: 3rem;'>WORKOUT GENERATOR</h1>", unsafe_allow_html=True)
st.markdown("<p style='color:#666;'>Configure your performance targets and let the Research Engine build your validated plan.</p>", unsafe_allow_html=True)

# Form Section
with st.form("generation_form", clear_on_submit=False):
    col1, col2 = st.columns(2)
    
    with col1:
        goal = st.selectbox(
            "Primary Objective",
            ["hypertrophy", "strength", "endurance", "fatloss"],
            help="Your training goal"
        )
        equipment = st.selectbox(
            "Kit Access",
            ["gym", "home"],
            help="Available tools"
        )
    
    with col2:
        experience = st.selectbox(
            "Experience Tier",
            ["beginner", "intermediate", "advanced"],
            help="Your current training baseline"
        )
    
    submitted = st.form_submit_button("🔥 GENERATE PERFORMANCE PLAN", width="stretch")

# Processing Logic
if submitted:
    if not st.session_state.auth_token:
        st.error("🔑 Demo Token Required. Please activate it in the sidebar.")
    else:
        with st.spinner("🚀 ANALYZING RESEARCH DATA..."):
            try:
                api = FitAppAPI(st.session_state.api_url, token=st.session_state.auth_token)
                result = api.generate_workout(
                    goal=goal,
                    equipment=equipment,
                    experience=experience
                )
                
                # Store in session state
                st.session_state.current_workout = result['data']
                st.session_state.workout_id = result['workout_id']
                st.success(f"Workout Generated: {result['workout_id']}")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ SYSTEM ERROR: {str(e)}")

# Display Workout
if st.session_state.current_workout:
    workout = st.session_state.current_workout
    
    st.markdown("---")
    
    # Research Validation Header
    if 'research_validation' in workout:
        val = workout['research_validation']
        st.markdown(f"""
        <div class="verdict-card verdict-green">
            <h3 style="margin:0; color:#00FF88;">✓ SCIENCE VALIDATED</h3>
            <p style="margin:5px 0 0 0; font-size:0.9rem; color:#B0B0B0;">{val['evidence_summary']}</p>
        </div>
        """, unsafe_allow_html=True)

    # Main Workout Display
    st.markdown("### EXERCISE SEQUENCE")
    
    for ex in workout['exercises']:
        render_exercise_card(ex)

    # PDF & Actions
    st.markdown("---")
    colA, colB = st.columns([1, 1])
    with colA:
        if st.button("🔄 RE-GENERATE WORKOUT", width="stretch"):
            st.session_state.current_workout = None
            st.rerun()
    with colB:
        st.info("💡 Premium PDF Export Available in Build V2.1")
