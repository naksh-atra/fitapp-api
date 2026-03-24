import streamlit as st
import sys
import os
import re
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


def _clean_summary(text, max_len=250):
    """Strip markdown, citation numbers like [1][2], and return a concise clean summary."""
    if not text:
        return ""
    # Remove citation markers like [1], [2][3], [4][5][6][7]
    text = re.sub(r'\[\d+](\[\d+])*\s*', '', text)
    # Remove markdown bold/italic/links
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    text = re.sub(r'[*_~`]', '', text)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) > max_len:
        text = text[:max_len].rsplit(' ', 1)[0] + '...'
    return text

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
    submitted = st.form_submit_button("GENERATE PERFORMANCE PLAN", use_container_width=True)

# ── Generate ──────────────────────────────────────────────────────────────────
if submitted:
    if not st.session_state.auth_token:
        st.error("🔑 Demo Token Required. Please activate it in the sidebar (' >> ' sign at the top left).")
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
    goal_label = workout.get("goal", "-").upper()
    split_text = workout.get("split_type", "-")
    days_text  = str(workout.get("training_days_per_week", "-"))
    evidence   = workout.get("evidence_level", "HIGH")

    st.markdown(f"""
<div style="display:flex; gap:1rem; background:rgba(255,255,255,0.03);
     border:1px solid rgba(255,255,255,0.08); border-radius:16px;
     padding:1rem 1.5rem; margin-bottom:1rem;">
    <div style="flex:1; text-align:center;">
        <div style="color:#888; font-size:0.7rem; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:4px;">GOAL</div>
        <div style="color:#fff; font-size:1rem; font-weight:600;">{goal_label}</div>
    </div>
    <div style="flex:1.5; text-align:center;">
        <div style="color:#888; font-size:0.7rem; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:4px;">SPLIT</div>
        <div style="color:#fff; font-size:1rem; font-weight:600;">{split_text}</div>
    </div>
    <div style="flex:1; text-align:center;">
        <div style="color:#888; font-size:0.7rem; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:4px;">DAYS / WEEK</div>
        <div style="color:#fff; font-size:1rem; font-weight:600;">{days_text}</div>
    </div>
    <div style="flex:1; text-align:center;">
        <div style="color:#888; font-size:0.7rem; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:4px;">EVIDENCE</div>
        <div style="color:#fff; font-size:1rem; font-weight:600;">{evidence}</div>
    </div>
</div>
""", unsafe_allow_html=True)

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
        evidence_level = val.get("evidence_level", "HIGH")
        clean_preview  = _clean_summary(val.get("evidence_summary", ""), max_len=250)

        with st.expander(f"SCIENCE VALIDATED - {evidence_level}", expanded=False):
            st.markdown(
                f"<p style='color:#B0B0B0; font-size:0.85rem; line-height:1.5;'>{clean_preview}</p>",
                unsafe_allow_html=True
            )
            full_text = val.get("evidence_summary", "")
            if full_text:
                with st.expander("View full evidence"):
                    st.markdown(full_text)
            if val.get("citations"):
                st.markdown("**Citations:**")
                for c in val["citations"]:
                    st.markdown(f"- {c}")

    # ── Weekly plan - one expander per day ───────────────────────────────────
    st.markdown("### 📅 WEEKLY PLAN")

    DAY_LABELS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    DEFAULT_EXPANDED_DAYS = {"monday", "tuesday", "wednesday"}
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
            label = f"💤 **{day.upper()}** - {session_name}"
        else:
            label = f"💪 **{day.upper()}** - {session_name}"

        expanded = not is_rest and (day in DEFAULT_EXPANDED_DAYS)
        with st.expander(label, expanded=expanded):
            if is_rest:
                st.markdown(f"<p style='color:#666;'>{session.get('notes', 'Active Recovery - light walking, stretching or complete rest.')}</p>", unsafe_allow_html=True)
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
