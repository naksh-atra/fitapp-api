"""
Page 1: Generate Workout
"""

import streamlit as st
import sys
from pathlib import Path
import os

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from api_client import FitAppAPI
from style import apply_cult_theme, render_exercise_card, render_sidebar

# Apply the Cult.fit aesthetic
apply_cult_theme()
render_sidebar()

st.title("PLAN YOUR SQUAD")

st.markdown("""
Create your science-based workout plan. All parameters are derived from recent research (2023-2025).
""")

# Form
with st.form("workout_form"):
    st.subheader("Workout Parameters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        goal = st.selectbox(
            "Training Goal",
            ["hypertrophy", "strength", "endurance", "fatloss"],
            help="Your primary training objective"
        )
        
        equipment = st.selectbox(
            "Available Equipment",
            ["gym", "home"],
            help="What equipment you have access to"
        )
    
    with col2:
        experience = st.selectbox(
            "Experience Level",
            ["beginner", "intermediate", "advanced"],
            help="Your training experience"
        )
    
    submitted = st.form_submit_button("🎯 Generate Workout", use_container_width=True)

# Generate workout
if submitted:
    with st.spinner("Generating science-based workout..."):
        try:
            api = FitAppAPI(st.session_state.api_url, token=st.session_state.auth_token)
            result = api.generate_workout(
                goal=goal,
                equipment=equipment,
                experience=experience
            )
            
            # Store in session state
            st.session_state.current_workout = result['data']
            st.session_state.workout_history.append(result['data'])
            
            st.success("✅ Workout generated successfully!")
            st.balloons()
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.info("Make sure the API is running: `python src/api/main.py`")

# Display current workout
if st.session_state.current_workout:
    st.markdown("---")
    st.subheader("📋 Your Workout Plan")
    
    workout = st.session_state.current_workout
    
    # Metadata
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Goal", workout['goal'].title())
    col2.metric("Exercises", len(workout['exercises']))
    col3.metric("Duration", f"{workout['total_duration_minutes']} min")
    col4.metric("Evidence", workout.get('evidence_level', 'High'))
    
    st.caption(f"**Workout ID:** `{workout['workout_id']}`")
    st.caption(f"**Source:** {workout.get('prescription_source', 'N/A')}")
    
    # Exercises Grid
    st.markdown("### ⚡ EXERCISE SESSION")
    
    for i, ex in enumerate(workout['exercises'], 1):
        sets = ex['sets']
        reps = ex['reps']
        sets_str = f"{sets[0]}-{sets[1]}" if isinstance(sets, list) else str(sets)
        reps_str = f"{reps[0]}-{reps[1]}" if isinstance(reps, list) else str(reps)
        
        render_exercise_card(
            name=f"{i}. {ex['name']}",
            sets=sets_str,
            reps=reps_str,
            notes=f"Rest: {ex['rest_seconds']}s | Tempo: {ex.get('tempo','N/A')}"
        )
    
    # Research Validation Panel
    if 'research_validation' in workout:
        st.markdown("---")
        st.markdown("""
        <div class="exercise-card" style="border-color: #FF9100;">
            <h3 style="color: #FF9100;">🔬 RESEARCH INSIGHT</h3>
        </div>
        """, unsafe_allow_html=True)
        
        val = workout['research_validation']
        st.markdown(f"""
        <div class="alert-info" style="margin-bottom:20px;">
        {val.get('evidence_summary', 'Synthesis in progress...')}
        </div>
        """, unsafe_allow_html=True)
        
        if val.get('citations'):
            st.markdown("**Scientific References:**")
            for cite in val['citations'][:3]: # Top 3
                st.caption(f"🔗 {cite}")

    st.markdown("---")
    st.info("💡 **Next:** Go to **Modify Workout** to customize exercises")
