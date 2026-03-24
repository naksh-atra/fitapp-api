"""
Page 3: Export Workout - updated for weekly_plan structure
"""

import streamlit as st
import json
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from style import apply_custom_theme, render_sidebar
from api_client import FitAppAPI
from pdf_generator import FitAppPDFGenerator

apply_custom_theme()
render_sidebar()

st.markdown("<h1 style='font-size: 3rem;'>EXPORT & HISTORY</h1>", unsafe_allow_html=True)

if not st.session_state.current_workout:
    st.warning("⚠️ No workout to export")
    st.info("Go to **Generate Workout** first")
    st.stop()

workout = st.session_state.current_workout

st.markdown("Download your full weekly plan with research citations and modification history.")

# ── Summary metrics ───────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("Goal",         workout.get("goal", "-").title())
col2.metric("Split",        workout.get("split_type", "-"))
col3.metric("Days / Week",  workout.get("training_days_per_week", "-"))
col4.metric("Evidence",     workout.get("evidence_level", "High"))

# ── Dietary disclaimer ────────────────────────────────────────────────────────
if workout.get("dietary_disclaimer"):
    st.warning(f"⚠️ **NUTRITION NOTICE:** {workout['dietary_disclaimer']}")

# ── Weekly volume summary ─────────────────────────────────────────────────────
if workout.get("weekly_volume_summary"):
    with st.expander("📊 WEEKLY VOLUME SUMMARY"):
        vol = workout["weekly_volume_summary"]
        cols = st.columns(3)
        items = [(k, v) for k, v in vol.items() if k != "note"]
        for i, (muscle, sets) in enumerate(items):
            cols[i % 3].metric(muscle.title(), sets)
        if vol.get("note"):
            st.caption(vol["note"])

# ── Modification history ──────────────────────────────────────────────────────
if workout.get("modification_history"):
    st.subheader("📝 Modification History")
    for i, mod in enumerate(workout["modification_history"], 1):
        with st.expander(f"Modification {i}: {mod['original_exercise']} → {mod['replacement_exercise']}"):
            v = mod["verdict"].lower()
            if v == "green":
                st.success(f"✅ VERDICT: {mod['verdict'].upper()}")
            elif v == "yellow":
                st.warning(f"⚠️ VERDICT: {mod['verdict'].upper()}")
            else:
                st.error(f"❌ VERDICT: {mod['verdict'].upper()}")
            st.markdown(f"**Reasoning:** {mod['reasoning']}")
            if mod.get("citations"):
                st.markdown("**Citations:**")
                for c in mod["citations"]:
                    st.markdown(f"- [{c}]({c})")

# ── Export options ────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("💾 Export Options")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### JSON Format")
    st.caption("Full machine-readable weekly plan with all data")
    json_data = json.dumps(workout, indent=2)
    st.download_button(
        label="📥 Download JSON",
        data=json_data,
        file_name=f"workout_{workout.get('workout_id','plan')}.json",
        mime="application/json",
        use_container_width=True
    )

with col2:
    st.markdown("### PDF Format")
    st.caption("Human-readable weekly plan - Monday to Sunday table")
    try:
        pdf_gen  = FitAppPDFGenerator()
        pdf_data = pdf_gen.generate(workout)
        filename = f"ResFit_Plan_{workout.get('workout_id','plan')}_{datetime.now().strftime('%Y%m%d')}.pdf"
        st.download_button(
            label="📥 Download PDF",
            data=pdf_data,
            file_name=filename,
            mime="application/pdf",
            use_container_width=True,
            key="pdf_download"
        )
    except Exception as e:
        st.error(f"❌ PDF generation failed: {str(e)}")
        st.info("Try JSON export instead")

# ── Raw preview ───────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("👁️ Full Plan Preview")
with st.expander("View Raw JSON"):
    st.json(workout)
