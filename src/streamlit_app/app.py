"""
FitApp - Science-Based Workout Generator
Main Streamlit application
"""

import streamlit as st

# Page config
st.set_page_config(
    page_title="FitApp - Science-Based Workouts",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'current_workout' not in st.session_state:
    st.session_state.current_workout = None
if 'workout_history' not in st.session_state:
    st.session_state.workout_history = []
if 'api_url' not in st.session_state:
    st.session_state.api_url = "http://127.0.0.1:8000"

# Main page
st.title("💪 FitApp - Science-Based Workout Generator")
st.markdown("""
### Research-Validated Training Plans

This app generates workout plans backed by the latest scientific research (2023-2025).

**Features:**
- ✅ Research-backed exercise prescriptions
- ✅ Real-time modification validation
- ✅ Green/Yellow/Red safety system
- ✅ Citation tracking for every recommendation

**How to use:**
1. **Generate Workout** - Create your base workout plan
2. **Modify Workout** - Request exercise substitutions with validation
3. **Export Workout** - Download your final plan with citations

---

**Navigate using the sidebar** ➡️
""")

# Sidebar status
st.sidebar.title("📊 Status")

if st.session_state.current_workout:
    st.sidebar.success("✅ Workout Generated")
    workout = st.session_state.current_workout
    st.sidebar.info(f"""
    **Current Workout:**
    - Goal: {workout['goal'].title()}
    - Exercises: {len(workout['exercises'])}
    - Workout ID: `{workout['workout_id']}`
    """)
    
    if 'modification_history' in workout:
        st.sidebar.warning(f"⚠️ {len(workout['modification_history'])} modification(s) applied")
else:
    st.sidebar.warning("⚠️ No workout generated yet")
    st.sidebar.info("Go to **Generate Workout** to start")

# API status check
st.sidebar.markdown("---")
st.sidebar.markdown("**API Connection:**")
try:
    import requests
    response = requests.get(f"{st.session_state.api_url}/health", timeout=2)
    if response.status_code == 200:
        st.sidebar.success("🟢 API Online")
    else:
        st.sidebar.error("🔴 API Error")
except:
    st.sidebar.error("🔴 API Offline")
    st.sidebar.caption("Run: `python src/api/main.py`")
