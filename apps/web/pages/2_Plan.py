# apps/web/pages/2_Plan.py
from __future__ import annotations

import streamlit as st
import pandas as pd

from fitapp_core.plan_v11 import generate_plan_v11, assess_tweak
from fitapp_core.models_v11 import InputsV11

DAY_ORDER = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

st.title("Plan")

# Guard
if "inputs_v1" not in st.session_state:
    st.info("No inputs yet. Go to Onboarding to enter details.")
    st.stop()

@st.cache_data(show_spinner=True)
def cached_generate_plan_v11(inputs_dict: dict, tweak_note: str | None):
    inputs = InputsV11(**inputs_dict)
    plan = generate_plan_v11(inputs, tweak_note=tweak_note)
    return plan.model_dump()

# v1 -> v1.1
v1 = st.session_state["inputs_v1"].model_dump()
days_per_week = v1.get("days_per_week") or 5
inputs_v11 = {
    "age": v1["age"],
    "sex": v1["sex"],
    "height_cm": v1["height_cm"],
    "weight_kg": v1["weight_kg"],
    "pal_code": v1["pal_code"],
    "goal": v1["goal"],
    "equipment": v1.get("equipment"),
    "notes": v1.get("notes"),
    "experience": v1.get("experience"),
    "days_per_week": int(days_per_week),
}

# Unified tweak UI
tweak = st.text_input(
    "Suggest a tweak (optional)",
    placeholder="e.g., swap squats for leg press",
    key="tweak_v11_text",
)

def _assess_and_maybe_apply():
    verdict = assess_tweak(inputs_v11.get("goal",""), tweak or "")
    st.session_state["tweak_flash"] = verdict  # transient display
    v = verdict.get("verdict")
    if v == "block":
        return
    if v == "warn" and not st.session_state.get("confirm_apply_warn"):
        st.session_state["confirm_apply_warn"] = True
        return
    # ok or confirmed warn -> force fresh generation
    try:
        cached_generate_plan_v11.clear()
    except Exception:
        st.cache_data.clear()
    plan = cached_generate_plan_v11(inputs_v11, tweak or "")
    st.session_state["plan_v11"] = plan
    st.session_state["confirm_apply_warn"] = False

colA, colB = st.columns([1,1])
with colA:
    if st.button("Assess & apply tweak"):
        _assess_and_maybe_apply()
with colB:
    if st.session_state.get("confirm_apply_warn") and st.button("Confirm and apply"):
        _assess_and_maybe_apply()

flash = st.session_state.pop("tweak_flash", None)
if flash:
    v = flash.get("verdict")
    msg = flash.get("rationale","")
    (st.success if v=="ok" else st.warning if v=="warn" else st.error)(msg)

# Generate plan if missing
if "plan_v11" not in st.session_state:
    st.session_state["plan_v11"] = cached_generate_plan_v11(inputs_v11, None)
plan_dict = st.session_state["plan_v11"]

# Availability gate: block when evidence not used
extra = plan_dict.get("extra", {}) or {}
rows = plan_dict.get("rows") or []
if not extra.get("evidence_built", False) or not rows:
    st.error("Service temporarily unavailable — research evidence not loaded. Please retry.")
    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("Retry now"):
            try:
                cached_generate_plan_v11.clear()
            except Exception:
                st.cache_data.clear()
            st.session_state["plan_v11"] = cached_generate_plan_v11(inputs_v11, tweak or None)
            st.rerun()
    with col2:
        st.caption(f"Status: snippets={extra.get('snippets_count', 0)} reason={extra.get('reason','unknown')}")
    st.stop()

# Data
df = pd.DataFrame(rows)

# Views
view = st.radio("View", ["Blueprint (Week 1)", "Month (4 weeks)"], horizontal=True)
visible_days = DAY_ORDER[: int(days_per_week)] if 2 <= int(days_per_week) <= 6 else DAY_ORDER

def _cell_lines(day_rows: pd.DataFrame) -> list[str]:
    lines: list[str] = []
    for section in ["main","accessory","prehab","cardio_notes"]:
        sub = day_rows[day_rows["block_type"] == section]
        for _, r in sub.iterrows():
            sets, reps = r.get("sets"), r.get("reps")
            dur = r.get("duration")
            vol = f"{int(sets)}×{int(reps)}" if pd.notna(sets) and pd.notna(reps) else (dur or "")
            base = f"{r.get('movement','')} — {vol}".strip(" —")
            note = (r.get("notes") or "").strip()
            lines.append(base if not note else f"{base} · {note}")
    return lines or ["(no items)"]

if view.startswith("Blueprint"):
    d1 = df[df["week_label"] == "Week 1"]
    for dn in visible_days:
        g = d1[d1["day_name"] == dn]
        if g.empty:
            continue
        st.subheader(f"Week 1 — {dn}")
        for line in _cell_lines(g):
            st.write(f"- {line}")
else:
    weeks = sorted(df["week_label"].dropna().unique().tolist(), key=lambda w: int(str(w).split()[-1]) if str(w).startswith("Week") else 1)
    weeks = weeks or ["Week 1","Week 2","Week 3","Week 4"]
    cols = st.columns(len(weeks))
    for i, wk in enumerate(weeks):
        with cols[i]:
            st.markdown(f"#### {wk}")
            for dn in visible_days:
                g = df[(df["week_label"] == wk) & (df["day_name"] == dn)]
                if g.empty:
                    continue
                st.caption(dn)
                for line in _cell_lines(g):
                    st.write(f"- {line}")

st.caption(f"Goal: {plan_dict.get('goal','?')} — Weeks: {plan_dict.get('week_count', 4)}")
# Sources remain server-side only (logged in plan generation).
