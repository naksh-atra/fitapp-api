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
goal_label = workout.get("goal", "-").title()
split_text = workout.get("split_type", "-")
days_text  = str(workout.get("training_days_per_week", "-"))
evidence   = workout.get("evidence_level", "High")

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

# ── Dietary disclaimer ────────────────────────────────────────────────────────
if workout.get("dietary_disclaimer"):
    st.warning(f"⚠️ **NUTRITION NOTICE:** {workout['dietary_disclaimer']}")

# ── Weekly volume summary ─────────────────────────────────────────────────────
if workout.get("weekly_volume_summary"):
    with st.expander("📊 WEEKLY VOLUME SUMMARY"):
        vol = workout["weekly_volume_summary"]
        items = [(k, v) for k, v in vol.items() if k != "note"]

        # Build HTML grid with consistent font sizing (matches metadata row)
        cells = ""
        for muscle, sets_val in items:
            cells += f"""
    <div style="text-align:center; background:rgba(255,255,255,0.03);
                border:1px solid rgba(255,255,255,0.08); border-radius:12px;
                padding:0.75rem 0.5rem;">
        <div style="color:#888; font-size:0.65rem; text-transform:uppercase;
                    letter-spacing:0.05em; margin-bottom:4px;">{muscle.title()}</div>
        <div style="color:#fff; font-size:0.85rem; font-weight:600;">{sets_val}</div>
    </div>"""

        st.markdown(f"""
<div style="display:grid; grid-template-columns:repeat(3, 1fr);
     gap:0.75rem; margin-bottom:0.75rem;">{cells}
</div>
""", unsafe_allow_html=True)

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
    with st.container(key="pdf-export"):
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

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    "<div style='text-align:right; margin-top:2rem; color:#555; font-size:0.8rem;'>"
    "by <a href='https://github.com/naksh-atra' target='_blank' "
    "style='color:#42A5F5; text-decoration:none;'>naksh</a></div>",
    unsafe_allow_html=True
)
