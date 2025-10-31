# src/fitapp_core/rag/prompts.py
from __future__ import annotations

# v1 (kept for reference)
SYSTEM_PROMPT = """You are a cautious workout-planning assistant.
Return ONLY JSON array with fields: day, movement, sets, reps, tempo_or_rest, load_prescription, notes.
If evidence is insufficient, return an empty array."""
USER_TEMPLATE = """Inputs:
- age={age}, sex={sex}, height_cm={height_cm}, weight_kg={weight_kg}
- PAL={pal_value} (TDEE={tdee} kcal/day), goal={goal}
Evidence:
{snippets}
Constraints:
- Safe, common exercises; equipment-agnostic when uncertain.
- Output strict JSON array only.
"""

# Feature flag (retained for compatibility; compact nested layout is active)
COMPACT_V11 = True

# v1.1 canonical-week object with progression notes (token-efficient)
SYSTEM_PROMPT_V11 = """Return ONLY a JSON object matching this schema (no extra text):
{
  "canonical_week": {
    "days": [
      {
        "day": 1,              // 1..7 or "Mon".."Sun"
        "day_name": "Mon",     // optional; if omitted, infer from day
        "main":        [ { "movement": "Squat", "main_focus": "Strength", "intensity_cue": "%1RM or RPE", "sets": 3, "reps": 5, "tempo_or_rest": "60-90s", "notes": "" } ],
        "accessory":   [ { "movement": "Leg Press", "sets": 3, "reps": 12, "tempo_or_rest": "60s", "notes": "" } ],
        "prehab":      [ ],
        "cardio_notes":[ { "movement": "Zone 2 Cardio", "duration": "20-30 min", "tempo_or_rest": "Zone 2", "notes": "" } ]
      }
    ]
  },
  "progression": [
    { "week": 2, "note": "+1 rep per set" },
    { "week": 3, "note": "+2.5–5% load" },
    { "week": 4, "note": "deload 15–25%" }
  ]
}
Rules:
- Populate all programmed sections per day: for hypertrophy target 1 main + 3–4 accessories; for strength target 1 main + 1–2 accessories; add prehab when indicated by notes; include cardio when goal/endurance requires it.
- Omit irrelevant fields by setting them null or leaving them out (e.g., duration for main).
- Do not include Weeks 2–4 details; only return the canonical week plus succinct progression notes.
"""

USER_TEMPLATE_V11 = """Inputs:
- sex={sex}, age={age}, height_cm={height_cm}, weight_kg={weight_kg}, PAL={pal_value}
- goal={goal}, equipment={equipment}
Energy:
- BMR={bmr} kcal/day, TDEE≈{tdee} kcal/day
Programming:
- days_per_week={days_per_week} (if missing, infer from evidence or produce 3–5 days typical for the goal)
- Respect equipment constraints; prefer common, safe movements with clear loading schemes
Evidence (optional excerpts):
{snippets}
User tweak:
{tweak}
Output:
- ONLY the JSON object described in SYSTEM.
"""

def render_snippets_for_v11(snippets_texts):
    out = []
    for i, t in enumerate(snippets_texts, 1):
        t = (t or "").strip().replace("\n", " ")
        if len(t) > 400:
            t = t[:397] + "..."
        out.append(f"- [{i}] {t}")
    return "\n".join(out)

# Tweak assessor prompts (for unified tweak flow)
TWEAK_ASSESSOR_SYSTEM = """You assess plan tweaks using only the provided evidence.
Return ONLY a JSON object with fields:
verdict ('ok'|'warn'|'block'), rationale (string), citations (array of integers)."""

TWEAK_ASSESSOR_USER = """Goal: {goal}
Requested tweak: {tweak}
Evidence excerpts (numbered):
{snippets}
Rules:
- Aligns with evidence -> verdict='ok'
- Partially aligned / trade-offs -> verdict='warn'
- Contradicts evidence / unsafe -> verdict='block'
Return only the JSON object."""
def render_numbered_snippets(snips: list[str]) -> str:
    lines = []
    for i, t in enumerate(snips, 1):
        t = (t or "").strip().replace("\n", " ")
        if len(t) > 400:
            t = t[:397] + "..."
        lines.append(f"[{i}] {t}")
    return "\n".join(lines)
