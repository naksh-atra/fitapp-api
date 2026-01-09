"""
Page 3: Export Workout
"""

import streamlit as st
import json
from datetime import datetime
import sys
sys.path.append('..')
from pdf_generator import FitAppPDFGenerator

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
            # st.markdown(f"**Verdict:** {mod['verdict'].upper()}")
            # st.markdown(f"**Timestamp:** {mod['timestamp']}")
            # st.markdown(f"**Reasoning:** {mod['reasoning']}")
             # Verdict color
            if mod['verdict'].lower() == 'green':
                st.success(f"✅ **VERDICT:** {mod['verdict'].upper()}")
            elif mod['verdict'].lower() == 'yellow':
                st.warning(f"⚠️ **VERDICT:** {mod['verdict'].upper()}")
            else:
                st.error(f"❌ **VERDICT:** {mod['verdict'].upper()}")
            
            st.markdown(f"**Reasoning:** {mod['reasoning']}")
            
            if mod.get('warning'):
                st.warning(mod['warning'])
            
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
    
    # st.info("📄 PDF export coming soon")
    # TODO: Implement PDF generation
    try:
        pdf_gen = FitAppPDFGenerator()
        pdf_data = pdf_gen.generate(workout)
        
        workout_id = workout['workout_id']
        filename = f"FitApp_Workout_{workout_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
        
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

# Preview
st.markdown("---")
st.subheader("👁️ Workout Preview")

with st.expander("View Full Workout Data"):
    st.json(workout)
