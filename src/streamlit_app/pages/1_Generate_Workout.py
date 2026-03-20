import streamlit as st
import sys
import os
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from api_client import FitAppAPI
from style import apply_custom_theme, render_exercise_card, render_session_card, render_sidebar

# Page config
st.set_page_config(
    page_title="ResFit | Workout Generator",
    page_icon="⚡",
    layout="wide"
)

apply_custom_theme()
render_sidebar()

st.markdown("<h1 style='font-size: 3rem;'>WORKOUT GENERATOR</h1>", unsafe_allow_html=True)
st.markdown("<p style='color:#666;'>Configure your performance targets and let the Research Engine build your validated weekly plan.</p>", unsafe_allow_html=True)

# ── Form ─────────────────────────────────────────────────────────────────────
with st.form("generation_form", clear_on_submit=False):
    col1, col2 = st.columns(2)
    with col1:
        goal = st.selectbox("Primary Objective", ["hypertrophy", "strength", "endurance", "fatloss"], help="Your training goal")
        equipment = st.selectbox("Kit Access", ["gym", "home"], help="Available equipment")
    with col2:
        experience = st.selectbox("Experience Tier", ["beginner", "intermediate", "advanced"], help="Your current training baseline")
    submitted = st.form_submit_button("🔥 GENERATE PERFORMANCE PLAN", use_container_width=True)

# ── Generate ──────────────────────────────────────────────────────────────────
if submitted:
    if not st.session_state.auth_token:
        st.error("🔑 Demo Token Required. Please activate it in the sidebar.")
    else:
        with st.spinner("🚀 ANALYZING RESEARCH DATA..."):
            try:
                api = FitAppAPI(st.session_state.api_url, token=st.session_state.auth_token)
                result = api.generate_workout(goal=goal, equipment=equipment, experience=experience)
                st.session_state.current_workout = result["data"]
                st.session_state.workout_id = result["workout_id"]
                st.success(f"Weekly Plan Generated: {result['workout_id']}")
                st.rerun()
            except Exception as e:
                st.error(f"❌ SYSTEM ERROR: {str(e)}")

# ── Display ───────────────────────────────────────────────────────────────────
if st.session_state.current_workout:
    workout = st.session_state.current_workout

    st.markdown("---")

    # ── Metadata row ─────────────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Goal",       workout.get("goal", "—").upper())
    m2.metric("Split",      workout.get("split_type", "—"))
    m3.metric("Days / Week", workout.get("training_days_per_week", "—"))
    m4.metric("Evidence",   workout.get("evidence_level", "HIGH"))

    # ── Dietary disclaimer (fat loss only) ───────────────────────────────────
    if workout.get("dietary_disclaimer"):
        st.warning(f"⚠️ **NUTRITION NOTICE:** {workout['dietary_disclaimer']}")

    # ── Weekly volume summary (hypertrophy only) ─────────────────────────────
    if workout.get("weekly_volume_summary"):
        with st.expander("📊 WEEKLY VOLUME SUMMARY"):
            vol = workout["weekly_volume_summary"]
            cols = st.columns(3)
            items = [(k, v) for k, v in vol.items() if k != "note"]
            for i, (muscle, sets) in enumerate(items):
                cols[i % 3].metric(muscle.title(), sets)
            if vol.get("note"):
                st.caption(vol["note"])

    # ── Science validation banner ─────────────────────────────────────────────
    if workout.get("research_validation"):
        val = workout["research_validation"]
        st.markdown(f"""
        <div class="verdict-card verdict-green">
            <h3 style="margin:0; color:#00FF88;">✓ SCIENCE VALIDATED — {val.get('evidence_level','HIGH')}</h3>
            <p style="margin:5px 0 0 0; font-size:0.9rem; color:#B0B0B0;">{val['evidence_summary'][:400]}...</p>
        </div>
        """, unsafe_allow_html=True)

    # ── Weekly plan — one expander per day ───────────────────────────────────
    st.markdown("### 📅 WEEKLY PLAN")

    DAY_LABELS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    weekly_plan = workout.get("weekly_plan", {})

    for day in DAY_LABELS:
        session = weekly_plan.get(day)
        if not session:
            continue

        session_name = session.get("session_name", day.title())
        session_type = session.get("session_type", "")
        exercises    = session.get("exercises", [])
        is_rest      = session_type == "rest" or not exercises

        # Day header colour
        if is_rest:
            label = f"💤 **{day.upper()}** — {session_name}"
        else:
            label = f"💪 **{day.upper()}** — {session_name}"

        with st.expander(label, expanded=not is_rest):
            if is_rest:
                st.markdown(f"<p style='color:#666;'>{session.get('notes', 'Active Recovery — light walking, stretching or complete rest.')}</p>", unsafe_allow_html=True)
            else:
                for ex in exercises:
                    render_session_card(ex)

    # ── Actions ───────────────────────────────────────────────────────────────
    st.markdown("---")
    colA, colB, colC = st.columns(3)
    with colA:
        if st.button("🔄 RE-GENERATE PLAN", use_container_width=True):
            st.session_state.current_workout = None
            st.rerun()
    with colB:
        if st.button("✏️ MODIFY AN EXERCISE", use_container_width=True):
            st.switch_page("pages/2_Modify_Workout.py")
    with colC:
        if st.button("📥 EXPORT WORKOUT", use_container_width=True):
            st.switch_page("pages/3_Export_Workout.py")
