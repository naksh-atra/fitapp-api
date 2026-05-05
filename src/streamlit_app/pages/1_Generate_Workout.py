import streamlit as st
import sys
import re
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from api_client import FitAppAPI
from style import apply_custom_theme, render_session_card, render_sidebar

# Page config
st.set_page_config(
    page_title="ResFit | Workout Generator",
    page_icon="⚡",
    layout="wide"
)

apply_custom_theme()
render_sidebar()


def _format_evidence_points(text):
    """
    Parse structured LLM output (3 **Point N - Heading**: body lines)
    into clean point dicts for display.
    Returns: [{"heading": "...", "body": "...", "citations": [...]}]
    """
    if not text:
        return []

    text = re.sub(r'\n{3,}', '\n\n', text)

    # Extract citations from the tail (lines starting with [1] ...)
    cit_lines = []
    body_lines = []
    for line in text.strip().splitlines():
        stripped = line.strip()
        if re.match(r'^\[\d+\]\s+https?://', stripped):
            cit_lines.append(re.sub(r'^\[\d+\]\s+', '', stripped))
        else:
            body_lines.append(line)
    body = '\n'.join(body_lines)

    # Split on **Point N - ...**: pattern
    sections = re.split(r'\*\*\s*Point\s+\d+\s*[-–—]\s*', body)
    sections = [s for s in sections if s.strip()]

    results = []
    for sec in sections:
        # Heading: text up to first **
        match = re.match(r'^(.+?)\*\*\s*[:\-–—]?\s*', sec)
        if match:
            heading = re.sub(r'[*_`~]', '', match.group(1)).strip().rstrip(':')
            rest = sec[match.end():].strip().lstrip(':').strip()
        else:
            heading = "Research Evidence"
            rest = sec.strip()

        # Clean the body: strip bold/italic markdown, collapse whitespace
        rest = re.sub(r'\*\*', '', rest)
        rest = re.sub(r'[*_`~]', '', rest)
        rest = re.sub(r'\[\d+](\[\d+])*\s*', '', rest)
        rest = re.sub(r'\s+', ' ', rest).strip()
        # Take first 5 sentences (roughly 5-6 lines of readable text)
        sentences = re.split(r'(?<=[.!?])\s+', rest)
        clean_body = ' '.join(sentences[:5]).strip()
        if len(sentences) > 5:
            clean_body += '...'

        results.append({"heading": heading, "body": clean_body})

    # Attach citations to first result
    if results and cit_lines:
        results[0]["citations"] = cit_lines
    elif results:
        results[0]["citations"] = []

    return results

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

    # ── Science validation banner ─────────────────────────────────────────────
    if workout.get("research_validation"):
        val = workout["research_validation"]
        evidence_level = val.get("evidence_level", "HIGH")
        raw_text = val.get("evidence_summary", "")
        evidence_points = _format_evidence_points(raw_text)

        with st.expander(f"SCIENCE VALIDATED - {evidence_level}", expanded=False):
            if evidence_points:
                with st.expander("View full evidence"):
                    for point in evidence_points:
                        st.markdown(f"**{point['heading']}**")
                        st.markdown(point["body"])
                        st.markdown("")
            citations = evidence_points[0].get("citations", []) if evidence_points else val.get("citations", [])
            if citations:
                st.markdown("**Citations:**")
                for c in citations:
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
