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

st.title("1️⃣ Generate Workout")

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
        
        week = st.number_input(
            "Training Week",
            min_value=1,
            max_value=52,
            value=1,
            help="Week number for progression tracking"
        )
    
    submitted = st.form_submit_button("🎯 Generate Workout", use_container_width=True)

# Generate workout
if submitted:
    with st.spinner("Generating science-based workout..."):
        try:
            api = FitAppAPI(st.session_state.api_url)
            result = api.generate_workout(
                goal=goal,
                equipment=equipment,
                experience=experience,
                week=week
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
    
    # Exercises table
    st.markdown("### Exercises")
    
    for i, ex in enumerate(workout['exercises'], 1):
        with st.expander(f"{i}. {ex['name']} ({ex['type'].title()})", expanded=True):
            col1, col2, col3, col4 = st.columns(4)
            
            # Handle range values
            sets = ex['sets']
            reps = ex['reps']
            rest = ex['rest_seconds']
            
            if isinstance(sets, list):
                sets_str = f"{sets[0]}-{sets[1]}"
            else:
                sets_str = str(sets)
            
            if isinstance(reps, list):
                reps_str = f"{reps[0]}-{reps[1]}"
            else:
                reps_str = str(reps)
            
            if isinstance(rest, list):
                rest_str = f"{rest[0]}-{rest[1]}s"
            else:
                rest_str = f"{rest}s"
            
            col1.markdown(f"**Sets:** {sets_str}")
            col2.markdown(f"**Reps:** {reps_str}")
            col3.markdown(f"**Tempo:** {ex.get('tempo','N/A')}")
            col4.markdown(f"**Rest:** {rest_str}")
            
            if 'rpe' in ex:
                st.caption(f"**RPE:** {ex['rpe']}")
            
            # Show if modified
            if ex.get('modified'):
                st.info(f"ℹ️ **Modified from:** {ex.get('original_name')}")
                if 'modification_note' in ex:
                    st.caption(ex['modification_note'])
    
    st.markdown("---")
    st.info("💡 **Next:** Go to **Modify Workout** to customize exercises")
