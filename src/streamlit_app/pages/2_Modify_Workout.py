"""
Page 2: Modify Workout
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from api_client import FitAppAPI

st.title("2️⃣ Modify Workout")

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
                api = FitAppAPI(st.session_state.api_url)
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
        st.success(f"🟢 **GREEN VERDICT** - Modification approved")
    elif verdict == 'yellow':
        st.warning(f"🟡 **YELLOW VERDICT** - Acceptable with adjustments")
    else:
        st.error(f"🔴 **RED VERDICT** - Not recommended")
    
    # Reasoning
    with st.expander("📖 Research Analysis", expanded=True):
        st.markdown(result['reasoning'])
    
    # Citations
    with st.expander(f"📚 Research Citations ({len(result['citations'])} sources)"):
        for i, citation in enumerate(result['citations'], 1):
            st.markdown(f"{i}. [{citation}]({citation})")
    
    # Apply modification button (only for green/yellow)
    if result['can_proceed']:
        st.markdown("---")
        
        if verdict == 'yellow' and result.get('warning'):
            st.warning(f"⚠️ {result['warning']}")
        
        if st.button("✅ Apply This Modification", use_container_width=True, type="primary"):
            with st.spinner("Applying modification..."):
                try:
                    api = FitAppAPI(st.session_state.api_url)
                    
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
