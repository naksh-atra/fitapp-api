"""
Page 3: Export Workout
"""

import streamlit as st
import json
from datetime import datetime

st.title("3️⃣ Export Workout")

if not st.session_state.current_workout:
    st.warning("⚠️ No workout to export")
    st.info("Go to **Generate Workout** first")
    st.stop()

workout = st.session_state.current_workout

st.markdown("""
Download your workout plan with full research citations and modification history.
""")

# Workout summary
st.subheader("📋 Workout Summary")

col1, col2, col3 = st.columns(3)
col1.metric("Goal", workout['goal'].title())
col2.metric("Exercises", len(workout['exercises']))
col3.metric("Evidence Level", workout.get('evidence_level', 'High'))

# Modification history
if 'modification_history' in workout and workout['modification_history']:
    st.subheader("📝 Modification History")
    
    for i, mod in enumerate(workout['modification_history'], 1):
        with st.expander(f"Modification {i}: {mod['original_exercise']} → {mod['replacement_exercise']}"):
            st.markdown(f"**Verdict:** {mod['verdict'].upper()}")
            st.markdown(f"**Timestamp:** {mod['timestamp']}")
            st.markdown(f"**Reasoning:** {mod['reasoning']}")
            
            st.markdown("**Citations:**")
            for citation in mod['citations']:
                st.markdown(f"- [{citation}]({citation})")

# Export options
st.markdown("---")
st.subheader("💾 Export Options")

col1, col2 = st.columns(2)

# JSON export
with col1:
    st.markdown("### JSON Format")
    st.caption("Machine-readable format with all data")
    
    json_data = json.dumps(workout, indent=2)
    
    st.download_button(
        label="📥 Download JSON",
        data=json_data,
        file_name=f"workout_{workout['workout_id']}.json",
        mime="application/json",
        use_container_width=True
    )

# PDF export (placeholder for now)
with col2:
    st.markdown("### PDF Format")
    st.caption("Human-readable workout plan")
    
    st.info("📄 PDF export coming soon")
    # TODO: Implement PDF generation

# Preview
st.markdown("---")
st.subheader("👁️ Workout Preview")

with st.expander("View Full Workout Data"):
    st.json(workout)
