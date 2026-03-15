import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from api_client import FitAppAPI
from style import apply_custom_theme, render_exercise_card, render_sidebar

# Page config
st.set_page_config(
    page_title="ResFit | Protocol Optimization",
    page_icon="⚖️",
    layout="wide"
)

# Initialize session state variables if they don't exist
if 'current_workout' not in st.session_state:
    st.session_state.current_workout = None

# Ensure current workout is always in sync with latest session
if st.session_state.get('workout_id') and st.session_state.auth_token:
    try:
        api = FitAppAPI(st.session_state.api_url, token=st.session_state.auth_token)
        # We don't have a direct 'get_workout' in Client yet, but hitting generate with same params or a dedicated getter would fix it.
        # For now, we rely on the apply_modification response updating st.session_state.current_workout
        pass
    except:
        pass

# Initialize session state variables if they don't exist
if 'current_workout' not in st.session_state:
    st.session_state.current_workout = None

# Apply the Premium ResFit aesthetic
apply_custom_theme()
render_sidebar()

# Initialize last validation state
if 'last_validation' not in st.session_state:
    st.session_state.last_validation = None

st.markdown("<h1 style='font-size: 3rem;'>PROTOCOL OPTIMIZATION</h1>", unsafe_allow_html=True)
st.markdown("<p style='color:#666;'>Swap exercises while maintaining physiological target through Research Validation.</p>", unsafe_allow_html=True)

if not st.session_state.current_workout:
    st.markdown("""
    <div class="premium-card" style="text-align:center; padding: 3rem;">
        <h3 style="color:#666;">NO ACTIVE PROTOCOL FOUND</h3>
        <p>Please generate a performance plan first.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🚀 GO TO GENERATOR"):
        st.switch_page("pages/1_Generate_Workout.py")
else:
    workout = st.session_state.current_workout
    
    st.markdown("### STEP 1: SELECT ORIGINAL TARGET")
    exercise_names = [ex['name'] for ex in workout['exercises']]
    
    selected_original = st.selectbox("Select Target to Swap", exercise_names)
    
    st.markdown("### STEP 2: CONFIGURE MODIFICATION")
    # Form Section
    with st.form("modification_form"):
        col1, col2 = st.columns(2)
        with col1:
            replacement = st.text_input("Replacement or Constraint", placeholder=" ")
        with col2:
            reason = st.selectbox("Reason for Modification", 
                                ["Equipment Unavailable", "Injury/Pain", "Preference", "Difficulty"])
        
        validate_button = st.form_submit_button("⚖️ VALIDATE SWAP VIA RESEARCH", width="stretch")

    # 1. HANDLE VALIDATION
    if validate_button:
        with st.spinner("🔍 SCANNING MEDICAL RCTs & META-ANALYSES..."):
            try:
                api = FitAppAPI(st.session_state.api_url, token=st.session_state.auth_token)
                result = api.validate_modification(
                    workout_id=st.session_state.workout_id,
                    original_exercise=selected_original,
                    replacement_exercise=replacement,
                    reason=reason,
                    goal=workout['goal']
                )
                
                # Store validation result for second step
                st.session_state.last_validation = {
                    "result": result,
                    "original": selected_original,
                    "replacement": replacement
                }
                
            except Exception as e:
                st.error(f"❌ VALIDATION FAILED: {str(e)}")
                st.session_state.last_validation = None

    # 2. DISPLAY VALIDATION RESULTS & APPLY BUTTON
    if st.session_state.last_validation:
        val_data = st.session_state.last_validation
        result = val_data["result"]
        corrected = result.get('corrected_name', val_data['replacement'])
        
        # Display Verdict
        v_color = result['verdict'].lower()
        st.markdown(f"""
        <div class="verdict-card verdict-{v_color}">
            <h3 style="color:var(--resfit-orange);">{result.get('verdict_color', '⚪')} VERDICT: {result['verdict'].upper()}</h3>
            <p style="color:white; font-weight:bold;">CONFIRMED EXERCISE: {corrected.upper()}</p>
            <p style="color:#B0B0B0;">{result['reasoning']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if result.get('citations'):
            with st.expander("📚 VIEW RESEARCH CITATIONS"):
                for cite in result['citations']:
                    st.markdown(f"- {cite}")
        
        if result['can_proceed']:
            st.markdown("### STEP 3: COMMIT MODIFICATION")
            if st.button(f"✅ APPLY {corrected.upper()} TO PROTOCOL", width="stretch"):
                with st.spinner("💾 REGISTERING PROTOCOL CHANGE..."):
                    try:
                        api = FitAppAPI(st.session_state.api_url, token=st.session_state.auth_token)
                        # Call API to persist
                        updated_workout = api.apply_modification(
                            workout_id=st.session_state.workout_id,
                            modification_id=result['modification_id'],
                            original_exercise=val_data['original'],
                            replacement_exercise=corrected, # USE THE CORRECTED NAME
                            verdict=result['verdict'],
                            reasoning=result['reasoning'],
                            citations=result['citations'],
                            adjustments=result.get('adjustments')
                        )
                        
                        # Update local session state
                        st.session_state.current_workout = updated_workout['modified_workout']
                        st.session_state.workout_id = updated_workout['new_workout_id']
                        st.session_state.last_validation = None
                        st.success("✅ Protocol permanently updated!")
                        st.toast("Protocol Optimized successfully!")
                        # Stay on page or provide button to go back
                        if st.button("👁️ VIEW UPDATED PROTOCOL"):
                            st.switch_page("pages/1_Generate_Workout.py")
                    except Exception as e:
                        st.error(f"❌ FAILED TO APPLY: {str(e)}")
        else:
            st.error("❌ High Risk substitution detected. Please choose a different replacement.")
            if st.button("🗑️ CLEAR VALIDATION"):
                st.session_state.last_validation = None
                st.rerun()
