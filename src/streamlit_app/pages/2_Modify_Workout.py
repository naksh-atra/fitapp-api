import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from api_client import FitAppAPI
from style import apply_custom_theme, render_session_card, render_sidebar

st.set_page_config(page_title="ResFit | Workout Modification", page_icon="⚖️", layout="wide")

apply_custom_theme()
render_sidebar()

# ── Session state defaults ────────────────────────────────────────────────────
if "current_workout"    not in st.session_state: st.session_state.current_workout    = None
if "last_validation"    not in st.session_state: st.session_state.last_validation    = None
if "modification_applied" not in st.session_state: st.session_state.modification_applied = False

st.markdown("<h1 style='font-size: 3rem;'>WORKOUT MODIFICATION</h1>", unsafe_allow_html=True)
st.markdown("<p style='color:#666;'>Swap exercises while maintaining physiological target through Research Validation.</p>", unsafe_allow_html=True)

# ── Guard: need a workout ─────────────────────────────────────────────────────
if not st.session_state.current_workout:
    st.markdown("""
    <div class="premium-card" style="text-align:center; padding: 3rem;">
        <h3 style="color:#666;">NO ACTIVE WORKOUT FOUND</h3>
        <p>Please generate a performance plan first.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🚀 GO TO GENERATOR"):
        st.switch_page("pages/1_Generate_Workout.py")
    st.stop()

workout = st.session_state.current_workout

# ── Collect all named exercises from the weekly plan ─────────────────────────
def collect_exercise_names(workout: dict) -> list:
    """
    Walk every day of weekly_plan and collect every named exercise,
    including exercises nested inside circuit stations.
    Returns a de-duplicated ordered list of names.
    """
    names = []
    seen  = set()
    for day_data in workout.get("weekly_plan", {}).values():
        for item in day_data.get("exercises", []):
            # top-level named exercise (hypertrophy / strength / cardio)
            name = item.get("name") or item.get("exercise")
            if name and name not in seen:
                names.append(name)
                seen.add(name)
            # circuit stations
            for station in item.get("stations", []):
                sname = station.get("name") or station.get("exercise")
                if sname and sname not in seen:
                    names.append(sname)
                    seen.add(sname)
    return names

exercise_names = collect_exercise_names(workout)

if not exercise_names:
    st.warning("No modifiable exercises found in this plan.")
    st.stop()

# ── Step 1: pick target ───────────────────────────────────────────────────────
st.markdown("### STEP 1: SELECT EXERCISE TO SWAP")
selected_original = st.selectbox("Select Target to Swap", exercise_names)

# ── Step 2: configure swap ───────────────────────────────────────────────────
st.markdown("### STEP 2: CONFIGURE MODIFICATION")
with st.form("modification_form"):
    col1, col2 = st.columns(2)
    with col1:
        replacement = st.text_input("Replacement Exercise", placeholder="e.g. Dumbbell Bench Press")
    with col2:
        reason = st.selectbox("Reason for Modification",
                              ["Equipment Unavailable", "Injury/Pain", "Preference", "Difficulty"])
    validate_button = st.form_submit_button("⚖️ VALIDATE SWAP VIA RESEARCH", use_container_width=True)

# ── Handle validation ─────────────────────────────────────────────────────────
if validate_button:
    if not replacement.strip():
        st.error("Please enter a replacement exercise name.")
    else:
        with st.spinner("🔍 ANALYZING RESEARCH DATA..."):
            try:
                api = FitAppAPI(st.session_state.api_url, token=st.session_state.auth_token)
                result = api.validate_modification(
                    workout_id=st.session_state.workout_id,
                    original_exercise=selected_original,
                    replacement_exercise=replacement.strip(),
                    reason=reason,
                    goal=workout["goal"]
                )
                st.session_state.last_validation = {
                    "result":      result,
                    "original":    selected_original,
                    "replacement": replacement.strip()
                }
            except Exception as e:
                st.error(f"❌ VALIDATION FAILED: {str(e)}")
                st.session_state.last_validation = None

# ── Display validation result & apply ────────────────────────────────────────
if st.session_state.last_validation:
    val_data = st.session_state.last_validation
    result   = val_data["result"]
    corrected = result.get("corrected_name", val_data["replacement"])

    v_color = result["verdict"].lower()
    st.markdown(f"""
    <div class="verdict-card verdict-{v_color}">
        <h3 style="color:var(--resfit-orange);">{result.get('verdict_color','⚪')} VERDICT: {result['verdict'].upper()}</h3>
        <p style="color:white; font-weight:bold;">CONFIRMED EXERCISE: {corrected.upper()}</p>
        <p style="color:#B0B0B0;">{result['reasoning']}</p>
    </div>
    """, unsafe_allow_html=True)

    if result.get("citations"):
        with st.expander("📚 VIEW RESEARCH CITATIONS"):
            for cite in result["citations"]:
                st.markdown(f"- {cite}")

    if result["can_proceed"]:
        st.markdown("### STEP 3: COMMIT MODIFICATION")
        if st.button(f"✅ APPLY {corrected.upper()} TO PROTOCOL", use_container_width=True):
            with st.spinner("💾 REGISTERING PROTOCOL CHANGE..."):
                try:
                    api = FitAppAPI(st.session_state.api_url, token=st.session_state.auth_token)
                    updated = api.apply_modification(
                        workout_id=st.session_state.workout_id,
                        modification_id=result["modification_id"],
                        original_exercise=val_data["original"],
                        replacement_exercise=corrected,
                        verdict=result["verdict"],
                        reasoning=result["reasoning"],
                        citations=result["citations"],
                        adjustments=result.get("adjustments")
                    )
                    st.session_state.current_workout    = updated["modified_workout"]
                    st.session_state.workout_id         = updated["new_workout_id"]
                    st.session_state.last_validation    = None
                    st.session_state.modification_applied = True
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ FAILED TO APPLY: {str(e)}")
    else:
        st.error("❌ High-risk substitution detected. Please choose a different replacement.")
        if st.button("🗑️ CLEAR VALIDATION"):
            st.session_state.last_validation = None
            st.rerun()

# ── Post-apply success ────────────────────────────────────────────────────────
if st.session_state.modification_applied:
    st.success("✅ Workout permanently updated!")
    st.toast("Workout optimised successfully!")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👁️ VIEW UPDATED PLAN", use_container_width=True):
            st.session_state.modification_applied = False
            st.switch_page("pages/1_Generate_Workout.py")
    with col2:
        if st.button("🔄 MODIFY ANOTHER EXERCISE", use_container_width=True):
            st.session_state.modification_applied = False
            st.rerun()
