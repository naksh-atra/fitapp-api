"""
Page 2: Modify Workout
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from api_client import FitAppAPI
from style import apply_cult_theme, render_exercise_card, render_sidebar

# Apply the Cult.fit aesthetic
apply_cult_theme()
render_sidebar()

st.title("SWAP & OPTIMIZE")

# Check if workout exists
if not st.session_state.current_workout:
    st.warning("⚠️ No workout generated yet")
    st.info("Go to **Generate Workout** first")
    st.stop()

workout = st.session_state.current_workout

st.markdown("""
Request exercise substitutions. The system will validate your request using research and return a verdict:
- 🟢 **GREEN**: Equivalent or better
- 🟡 **YELLOW**: Acceptable with adjustments
- 🔴 **RED**: Not recommended
""")

# Select exercise to modify
st.subheader("Select Exercise to Modify")

exercise_names = [ex['name'] for ex in workout['exercises']]
selected_exercise = st.selectbox(
    "Choose exercise",
    exercise_names,
    help="Select the exercise you want to replace"
)

# Modification form
with st.form("modification_form"):
    st.subheader("Propose Replacement")
    
    replacement = st.text_input(
        "Replacement Exercise",
        placeholder="e.g., Leg Press, Dumbbell Bench Press, etc.",
        help="Enter the exercise you want to use instead"
    )
    
    reason = st.selectbox(
        "Reason for Change",
        ["knee_pain", "shoulder_pain", "lower_back_pain", "no_equipment", "preference", "injury", "other"],
        help="Why do you need this substitution?"
    )
    
    validate_button = st.form_submit_button("🔬 Validate Modification", use_container_width=True)

# Validate modification
if validate_button:
    if not replacement:
        st.error("❌ Please enter a replacement exercise")
    else:
        with st.spinner("Validating with research database... (this may take 5-10 seconds)"):
            try:
                api = FitAppAPI(st.session_state.api_url, token=st.session_state.auth_token)
                validation_result = api.validate_modification(
                    workout_id=workout['workout_id'],
                    original_exercise=selected_exercise,
                    replacement_exercise=replacement,
                    reason=reason,
                    goal=workout['goal']
                )
                
                # Store validation result
                st.session_state.validation_result = validation_result
                
                st.success("✅ Validation complete!")
                
            except Exception as e:
                st.error(f"❌ Validation failed: {str(e)}")
                st.stop()

# Display validation result
if 'validation_result' in st.session_state:
    result = st.session_state.validation_result
    
    st.markdown("---")
    st.subheader("📊 Validation Result")
    
    verdict = result['verdict']
    
    # Verdict display
    if verdict == 'green':
        st.markdown(f"""
        <div class="verdict-green">
            <b>🟢 GREEN VERDICT</b><br>
            Scientific Approval: This modification is bio-mechanically equivalent and supports your {workout['goal']} goals.
        </div>
        """, unsafe_allow_html=True)
    elif verdict == 'yellow':
        st.markdown(f"""
        <div class="verdict-yellow">
            <b>🟡 YELLOW VERDICT</b><br>
            Conditional Approval: Proceed with the suggested protocol adjustments.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="verdict-red">
            <b>🔴 RED VERDICT</b><br>
            Modification Rejected: This substitution may significantly degrade training stimulus for {workout['goal']}.
        </div>
        """, unsafe_allow_html=True)
    
    # Reasoning
    st.markdown("### 🧬 RESEARCH ANALYSIS")
    st.markdown(f"""
    <div class="exercise-card" style="font-size:0.95rem; line-height:1.6;">
    {result['reasoning']}
    </div>
    """, unsafe_allow_html=True)
    
    # Citations
    with st.expander(f"📚 View {len(result['citations'])} Research Citations"):
        for i, citation in enumerate(result['citations'], 1):
            st.caption(f"{i}. {citation}")
    
    # Apply modification button (only for green/yellow)
    if result['can_proceed']:
        st.markdown("---")
        
        if verdict == 'yellow' and result.get('warning'):
            st.warning(f"⚠️ {result['warning']}")
        
        if st.button("✅ Apply This Modification", use_container_width=True, type="primary"):
            with st.spinner("Applying modification..."):
                try:
                    api = FitAppAPI(st.session_state.api_url, token=st.session_state.auth_token)
                    
                    # Apply modification
                    apply_result = api.apply_modification(
                        workout_id=workout['workout_id'],
                        modification_id=result['modification_id'],
                        original_exercise=selected_exercise,
                        replacement_exercise=replacement,
                        verdict=verdict,
                        reasoning=result['reasoning'],
                        citations=result['citations'],
                        adjustments=result.get('adjustments', {})
                    )
                    
                    # Update session state with new workout
                    st.session_state.current_workout = apply_result['modified_workout']
                    st.session_state.workout_history.append(apply_result['modified_workout'])
                    
                    # Clear validation result
                    del st.session_state.validation_result
                    
                    st.success("✅ Modification applied successfully!")
                    st.balloons()
                    st.info("🔄 Page will refresh to show updated workout...")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Failed to apply modification: {str(e)}")
    else:
        st.error("❌ Cannot proceed with RED verdict modification")
        st.info("Try a different replacement exercise")
