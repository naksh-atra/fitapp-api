import streamlit as st
import os

def apply_custom_theme():
    """Injects high-end Premium 'ResFit' Design System"""
    st.markdown("""
    <style>
    /* Premium Typography */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=Outfit:wght@700;900&display=swap');

    :root {
        --resfit-orange: #FF5722;
        --resfit-purple: #6200EA;
        --bg-dark: #000000;
        --glass-bg: rgba(20, 20, 25, 0.7);
        --glass-border: rgba(255, 255, 255, 0.1);
    }

    /* Global Background & Base */
    .stApp {
        background: radial-gradient(circle at 0% 0%, rgba(98, 0, 234, 0.15) 0%, transparent 40%),
                    radial-gradient(circle at 100% 100%, rgba(255, 87, 34, 0.1) 0%, transparent 40%),
                    #000000;
        color: #FFFFFF !important;
        font-family: 'Inter', sans-serif;
    }

    h1, h2, h3 {
        font-family: 'Outfit', sans-serif !important;
        letter-spacing: -0.04em !important;
        text-transform: uppercase;
        background: linear-gradient(90deg, #FFFFFF, #B0B0B0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* Premium Glassmorphism Card (Stacked Effect) */
    .premium-card {
        background: var(--glass-bg);
        backdrop-filter: blur(20px) saturate(180%);
        -webkit-backdrop-filter: blur(20px) saturate(180%);
        border: 1px solid var(--glass-border);
        border-radius: 20px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        position: relative;
        overflow: hidden;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }

    .premium-card:hover {
        transform: translateY(-8px);
        border-color: rgba(255, 87, 34, 0.4);
        box-shadow: 0 20px 40px rgba(0,0,0,0.6);
    }

    .premium-card::before {
        content: "";
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255, 87, 34, 0.05) 0%, transparent 70%);
        pointer-events: none;
    }

    /* Stat Chips */
    .stat-chip {
        display: inline-flex;
        align-items: center;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 50px;
        padding: 4px 12px;
        font-size: 0.8rem;
        font-weight: 600;
        color: #B0B0B0;
        margin-right: 8px;
        margin-bottom: 8px;
    }

    .stat-chip b { color: var(--resfit-orange); margin-right: 4px; }

    /* Premium Buttons — covers st.button, st.form_submit_button, st.download_button */
    div.stButton > button,
    div.stFormSubmitButton > button,
    div.stDownloadButton > button {
        background: linear-gradient(135deg, #FF5722 0%, #E64A19 100%);
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 12px 24px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        width: 100%;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(255, 87, 34, 0.3) !important;
    }

    div.stButton > button:hover,
    div.stFormSubmitButton > button:hover,
    div.stDownloadButton > button:hover {
        transform: scale(1.02) !important;
        box-shadow: 0 8px 25px rgba(255, 87, 34, 0.5) !important;
    }

    /* Verdict Cards (Modified specifically for high-end look) */
    .verdict-card {
        border-radius: 16px;
        padding: 1.2rem;
        margin: 1rem 0;
        border-left: 6px solid #ccc;
        background: rgba(255, 255, 255, 0.03);
    }
    .verdict-green { border-color: #00FF88; background: linear-gradient(90deg, rgba(0, 255, 136, 0.05), transparent); }
    .verdict-yellow { border-color: #FFD600; background: linear-gradient(90deg, rgba(255, 214, 0, 0.05), transparent); }
    .verdict-red { border-color: #FF1744; background: linear-gradient(90deg, rgba(255, 23, 68, 0.05), transparent); }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #050505 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }

    /* Custom Scrollbar */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #000; }
    ::-webkit-scrollbar-thumb { background: #333; border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: #444; }

    /* Target Streamlit Native Containers for Card Look */
    [data-testid="stForm"], [data-testid="stExpander"] {
        background: var(--glass-bg) !important;
        backdrop-filter: blur(20px) saturate(180%) !important;
        -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 20px !important;
        padding: 1.5rem !important;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {background: transparent !important;}
    </style>
    """, unsafe_allow_html=True)

def render_sidebar():
    """Shared premium sidebar for all pages"""
    import jwt
    from datetime import datetime, timedelta
    import requests
    from dotenv import load_dotenv
    load_dotenv(".env.local")
    
    # Initialize keys
    if 'auth_token' not in st.session_state: st.session_state.auth_token = None
    if 'api_url' not in st.session_state: st.session_state.api_url = os.getenv("API_URL", "http://127.0.0.1:8000")

    with st.sidebar:
        st.sidebar.markdown("<h2 style='text-align:center;'>RESFIT</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; font-size:0.7rem; color:#666; margin-bottom:2rem;'>V2.0 RESEARCH ENGINE</p>", unsafe_allow_html=True)
        
        # Navigation
        if st.button("DASHBOARD", width="stretch"): st.switch_page("app.py")
        
        st.markdown("---")
        
        # Auth Section
        if not st.session_state.auth_token:
            st.warning("Locked Mode")
            if st.button("🔑 ACTIVATE DEMO", width="stretch"):
                # Simple JWT for demo - MUST MATCH BACKEND SECRET
                secret = os.getenv("JWT_SECRET", "devsecretapplepie")
                expire = datetime.utcnow() + timedelta(hours=1)
                token = jwt.encode({"sub": "resfit-demo", "exp": expire}, secret, algorithm="HS256")
                st.session_state.auth_token = token
                st.rerun()
        else:
            st.success("Authenticated")
            if st.button("🔓 LOGOUT", width="stretch"):
                st.session_state.auth_token = None
                st.rerun()

        st.markdown("---")
        # System Health
        try:
            r = requests.get(f"{st.session_state.api_url}/health", timeout=1)
            if r.status_code == 200:
                st.markdown("<p style='color:#00FF88; font-size:0.8rem;'>● API ONLINE (V2)</p>", unsafe_allow_html=True)
            else:
                st.markdown("<p style='color:#FF1744; font-size:0.8rem;'>● SYSTEM ERROR</p>", unsafe_allow_html=True)
        except:
            st.markdown("<p style='color:#FF1744; font-size:0.8rem;'>● API OFFLINE</p>", unsafe_allow_html=True)

def _fmt(val, suffix=""):
    """Format a scalar or [low, high] list into a display string."""
    if isinstance(val, list) and len(val) == 2:
        if val[0] == val[1]:
            return f"{val[0]}{suffix}"
        return f"{val[0]}-{val[1]}{suffix}"
    return f"{val}{suffix}" if val is not None else "-"


def render_session_card(ex):
    """
    Renders one item from a session's exercises list.
    Handles 4 distinct shapes:
      1. compound / isolation  (hypertrophy / strength)
      2. cardio_aerobic / cardio_vo2max  (endurance - duration-based, no sets/reps)
      3. hiit_circuit / cardio_threshold  (circuit with stations[])
      4. cardio_steady_state  (fatloss steady state - duration-based)
    """
    ex_type = ex.get("type", "")
    name    = ex.get("name", "Exercise")
    modified_tag = ""
    if ex.get("modified"):
        modified_tag = '<span style="float:right; font-size:0.7rem; color:#00FF88; border:1px solid #00FF88; padding:2px 8px; border-radius:10px;">MODIFIED</span>'

    # ── CIRCUIT (HIIT / threshold) ────────────────────────────────────────────
    if "stations" in ex:
        rounds   = _fmt(ex.get("circuit_rounds"))
        intensity = ex.get("intensity", "")
        rpe      = ex.get("rpe", "")
        notes    = ex.get("pro_notes", "")
        load     = ex.get("load_constraint", "")

        stations_html = ""
        for st_item in ex.get("stations", []):
            sname    = st_item.get("name") or st_item.get("exercise", "?")
            work     = _fmt(st_item.get("work_seconds"), "s")
            rest     = _fmt(st_item.get("rest_seconds"), "s")
            reps_s   = _fmt(st_item.get("reps")) if st_item.get("reps") else ""
            dur_s    = _fmt(st_item.get("duration_seconds"), "s") if st_item.get("duration_seconds") else ""
            detail   = work if work != "-" else dur_s
            stations_html += f"""
<div style="display:flex; justify-content:space-between; padding:6px 0; border-bottom:1px solid rgba(255,255,255,0.05);">
  <span style="color:#fff; font-weight:600;">{sname.upper()}</span>
  <span style="color:#888; font-size:0.85rem;">
    {"Work: " + detail + " &nbsp;|&nbsp; " if detail and detail != "-" else ""}
    {"Rest: " + rest + " &nbsp;|&nbsp; " if rest and rest != "-" else ""}
    {"Reps: " + reps_s if reps_s and reps_s != "-" else ""}
  </span>
</div>"""

        html = f"""<div class="premium-card">
{modified_tag}
<h3 style="margin-top:0; font-size:1.3rem; margin-bottom:0.3rem; color:white;">{name.upper()} <span style="font-size:0.8rem; color:#FF5722;">CIRCUIT</span></h3>
<div style="margin-bottom:0.8rem;">
  <span class="stat-chip"><b>ROUNDS:</b> {rounds}</span>
  {"<span class='stat-chip'><b>INTENSITY:</b> " + intensity + "</span>" if intensity else ""}
  {"<span class='stat-chip'><b>RPE:</b> " + rpe + "</span>" if rpe else ""}
  {"<span class='stat-chip'><b>LOAD:</b> " + load + "</span>" if load else ""}
</div>
<div style="margin-bottom:0.8rem;">{stations_html}</div>
{"<div style='background:rgba(255,87,34,0.1); padding:8px 12px; border-radius:10px; border-left:3px solid var(--resfit-orange);'><p style='color:#FFCCBC; font-size:0.8rem; margin:0;'><i>" + notes + "</i></p></div>" if notes else ""}
</div>"""
        st.markdown(html, unsafe_allow_html=True)
        return

    # ── CARDIO (duration-based - endurance zone2/vo2max, fatloss steady) ──────
    if ex_type in ("cardio_aerobic", "cardio_steady_state", "cardio_vo2max"):
        duration  = _fmt(ex.get("duration_minutes"), " min")
        intensity = ex.get("intensity", "")
        zone      = ex.get("intensity_zone", "")
        rpe       = ex.get("rpe", "")
        notes     = ex.get("pro_notes", "")
        # VO2max interval shape
        if ex_type == "cardio_vo2max" and ex.get("intervals"):
            intervals = ex.get("intervals")
            dur_i     = ex.get("interval_duration_min")
            rest_i    = ex.get("rest_between_intervals_min")
            detail_chip = f'<span class="stat-chip"><b>INTERVALS:</b> {intervals}×{dur_i} min</span>'
            rest_chip   = f'<span class="stat-chip"><b>REST:</b> {rest_i} min</span>' if rest_i else ""
        else:
            detail_chip = f'<span class="stat-chip"><b>DURATION:</b> {duration}</span>'
            rest_chip   = ""

        html = f"""<div class="premium-card">
{modified_tag}
<h3 style="margin-top:0; font-size:1.3rem; margin-bottom:0.3rem; color:white;">{name.upper()}</h3>
<div style="margin-bottom:0.8rem;">
  {detail_chip}
  {rest_chip}
  {"<span class='stat-chip'><b>INTENSITY:</b> " + intensity + "</span>" if intensity else ""}
  {"<span class='stat-chip'><b>ZONE:</b> " + zone + "</span>" if zone else ""}
  {"<span class='stat-chip'><b>RPE:</b> " + rpe + "</span>" if rpe else ""}
</div>
{"<div style='background:rgba(255,87,34,0.1); padding:8px 12px; border-radius:10px; border-left:3px solid var(--resfit-orange);'><p style='color:#FFCCBC; font-size:0.8rem; margin:0;'><i>" + notes + "</i></p></div>" if notes else ""}
</div>"""
        st.markdown(html, unsafe_allow_html=True)
        return

    # ── STRENGTH / HYPERTROPHY (sets × reps) ──────────────────────────────────
    sets    = _fmt(ex.get("sets"))
    reps    = _fmt(ex.get("reps"))
    rest    = _fmt(ex.get("rest_seconds"), "s")
    rpe     = ex.get("rpe", "-")
    tempo   = ex.get("tempo", "")
    pct_1rm = ex.get("percent_1rm", "")
    notes   = ex.get("pro_notes", "")

    html = f"""<div class="premium-card">
{modified_tag}
<h3 style="margin-top:0; font-size:1.3rem; margin-bottom:0.5rem; color:white;">{name.upper()}</h3>
<div style="margin-bottom:1rem;">
  <span class="stat-chip"><b>SETS:</b> {sets}</span>
  <span class="stat-chip"><b>REPS:</b> {reps}</span>
  <span class="stat-chip"><b>REST:</b> {rest}</span>
  <span class="stat-chip"><b>RPE:</b> {rpe}</span>
  {"<span class='stat-chip'><b>1RM:</b> " + pct_1rm + "</span>" if pct_1rm else ""}
</div>
{"<p style='color:#b3b3b3; font-size:0.9rem; margin-bottom:0.5rem;'><b>Tempo:</b> " + tempo + "</p>" if tempo else ""}
{"<div style='background:rgba(255,87,34,0.1); padding:8px 12px; border-radius:10px; border-left:3px solid var(--resfit-orange);'><p style='color:#FFCCBC; font-size:0.8rem; margin:0;'><i>" + notes + "</i></p></div>" if notes else ""}
</div>"""
    st.markdown(html, unsafe_allow_html=True)


def render_exercise_card(ex):
    """Backward-compat alias - routes to render_session_card."""
    render_session_card(ex)
