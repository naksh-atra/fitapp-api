# # src/fitapp_core/plan_v11.py
# from __future__ import annotations

# import os
# import re
# from typing import Optional, List, Dict, Any

# from pydantic import ValidationError

# from .models_v11 import InputsV11, PlanV11, PlanRowV11
# from .models import PAL_MAP as PALMAP
# from .energy import bmr_mifflin_st_jeor, tdee_from_bmr
# from .rag.retriever import retrieve_snippets
# from .rag.prompts import (
#     SYSTEM_PROMPT_V11,
#     USER_TEMPLATE_V11,
#     render_snippets_for_v11,
#     TWEAK_ASSESSOR_SYSTEM,
#     TWEAK_ASSESSOR_USER,
#     render_numbered_snippets,
# )
# from .rag.llm import call_llm_json_object_with_log

# # Feature flag: optional compact LLM JSON (advisory); plan rows must be evidence-built
# USE_LLM_JSON = os.getenv("PLAN_V11_USE_LLM_JSON", "false").strip().lower() in ("1", "true", "yes")

# DAY_NAMES = {1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat", 7: "Sun"}
# DAY_NAME_MAP = {
#     "mon": 1, "monday": 1, "tue": 2, "tuesday": 2, "wed": 3, "wednesday": 3,
#     "thu": 4, "thursday": 4, "fri": 5, "friday": 5, "sat": 6, "saturday": 6, "sun": 7, "sunday": 7,
# }

# def _parse_int_lower_bound(val: Any) -> Optional[int]:
#     if isinstance(val, int):
#         return val
#     if isinstance(val, str):
#         m = re.match(r"\s*(\d+)\s*(?:[-–]\s*\d+)?\s*$", val)
#         if m:
#             return int(m.group(1))
#     return None

# def _coerce_day(val: Any) -> int:
#     try:
#         return int(val)
#     except Exception:
#         if isinstance(val, str):
#             return DAY_NAME_MAP.get(val.strip().lower(), 1)
#         return 1

# def _make_retrieval_query(inputs: InputsV11) -> str:
#     goal = inputs.goal or ""
#     exp = getattr(inputs, "experience", "") or ""
#     days = getattr(inputs, "days_per_week", None)
#     equip_list = getattr(inputs, "equipment", None) or []
#     equip = ", ".join(equip_list) if isinstance(equip_list, list) else str(equip_list or "")
#     parts = [goal, exp]
#     if days:
#         parts.append(f"{days} days/week")
#     if equip:
#         parts.append(f"equipment: {equip}")
#     return ", ".join([p for p in parts if p]).strip(", ")

# def _extract_rules_from_snippets(hits: List[Dict[str, Any]], goal: str) -> Dict[str, Any]:
#     """
#     TODO: Parse retrieved snippets for goal-specific parameters.
#     For now, returns empty dict; real implementation will scan for:
#     - Hypertrophy: tempo patterns (e.g., "3-1-2-0"), target muscles
#     - Strength: 1RM percentages, RPE/RIR cues
#     - Endurance: zone labels, cadence, duration
#     - Fat Loss: interval formats, rounds, total time
    
#     Once KB is populated with these phrases, this function extracts them.
#     """
#     # Placeholder: scan snippet texts for patterns
#     rules = {}
#     # Example (not implemented yet):
#     # for hit in hits:
#     #     text = hit.get("text", "").lower()
#     #     if "3-1-2-0" in text and goal == "hypertrophy":
#     #         rules["tempo"] = "3-1-2-0"
#     #     if "zone 2" in text and goal == "endurance":
#     #         rules["intensity_zone"] = "Zone 2"
#     return rules

# # Keep the fallback function defined but never called (no silent fallbacks).
# def _default_canonical_week(inputs: InputsV11) -> List[Dict[str, Any]]:
#     dpw = getattr(inputs, "days_per_week", None) or 5
#     dpw = max(2, min(6, int(dpw)))
#     goal = (inputs.goal or "hypertrophy").lower()

#     def main_item(mv, s, r, notes=""):
#         return {"movement": mv, "main_focus": None, "intensity_cue": "RPE 6–8", "sets": s, "reps": r, "tempo_or_rest": "60–90s", "notes": notes}
#     def acc_item(mv, s, r, notes=""):
#         return {"movement": mv, "sets": s, "reps": r, "tempo_or_rest": "45–75s", "notes": notes}

#     days: List[Dict[str, Any]] = []
#     if goal == "strength":
#         template = [
#             ("Mon", main_item("Back Squat", 3, 5), [acc_item("Leg Press", 3, 8), acc_item("Hamstring Curl", 3, 10)]),
#             ("Tue", main_item("Bench Press", 4, 3), [acc_item("DB Row", 3, 8), acc_item("Triceps Pushdown", 3, 10)]),
#             ("Thu", main_item("Deadlift", 3, 3), [acc_item("Back Extension", 3, 10), acc_item("Plank", 3, 30)]),
#             ("Fri", main_item("Overhead Press", 3, 5), [acc_item("Lat Pulldown", 3, 10), acc_item("Lateral Raise", 3, 12)]),
#         ]
#         for name, main, acc in template[:dpw]:
#             days.append({"day": name, "day_name": name, "main": [main], "accessory": acc, "prehab": [], "cardio_notes": []})
#         return days

#     if goal == "endurance":
#         for name in ["Mon", "Wed", "Fri", "Sun"][:dpw]:
#             cardio = [{"movement": "Zone 2 Cardio", "duration": "30–45 min", "tempo_or_rest": "Zone 2", "notes": ""}]
#             days.append({"day": name, "day_name": name, "main": [], "accessory": [], "prehab": [], "cardio_notes": cardio})
#         return days

#     if goal == "fat_loss":
#         template = [
#             ("Mon", main_item("Back Squat", 3, 8), [acc_item("Leg Press", 3, 12), acc_item("Calf Raise", 3, 15)], [{"movement": "Zone 2 Cardio", "duration":"20–30 min","tempo_or_rest":"Zone 2","notes":""}]),
#             ("Tue", main_item("Bench Press", 3, 8), [acc_item("DB Row", 3, 12), acc_item("Face Pull", 3, 15)], []),
#             ("Thu", main_item("Romanian Deadlift", 3, 8), [acc_item("Hamstring Curl", 3, 12), acc_item("Reverse Lunge", 3, 10)], [{"movement": "Zone 2 Cardio", "duration":"20–30 min","tempo_or_rest":"Zone 2","notes":""}]),
#             ("Fri", main_item("Overhead Press", 3, 8), [acc_item("Lat Pulldown", 3, 12), acc_item("Biceps Curl", 3, 12)], []),
#         ]
#         for name, main, acc, cardio in template[:dpw]:
#             days.append({"day": name, "day_name": name, "main": [main], "accessory": acc, "prehab": [], "cardio_notes": cardio})
#         return days

#     template = [
#         ("Mon", main_item("Bench Press", 3, 8), [acc_item("Incline DB Press", 3, 10), acc_item("Lateral Raise", 3, 12), acc_item("Triceps Pushdown", 3, 12)]),
#         ("Tue", main_item("Back Squat", 3, 8), [acc_item("Leg Press", 3, 12), acc_item("Leg Curl", 3, 12), acc_item("Calf Raise", 3, 15)]),
#         ("Wed", main_item("Barbell Row", 3, 8), [acc_item("Lat Pulldown", 3, 10), acc_item("Rear Delt Fly", 3, 12), acc_item("Biceps Curl", 3, 12)]),
#         ("Thu", main_item("Romanian Deadlift", 3, 8), [acc_item("Split Squat", 3, 10), acc_item("Hamstring Curl", 3, 12), acc_item("Back Extension", 3, 12)]),
#         ("Fri", main_item("Overhead Press", 3, 8), [acc_item("DB Row", 3, 10), acc_item("Face Pull", 3, 12), acc_item("Cable Fly", 3, 12)]),
#     ]
#     for name, main, acc in template[:dpw]:
#         days.append({"day": name, "day_name": name, "main": [main], "accessory": acc, "prehab": [], "cardio_notes": []})
#     return days

# def _coerce_items(items: Any) -> List[Dict[str, Any]]:
#     out: List[Dict[str, Any]] = []
#     if items is None:
#         return out
#     if isinstance(items, dict):
#         return [items]
#     if isinstance(items, list):
#         for it in items:
#             if isinstance(it, dict):
#                 out.append(it)
#             else:
#                 out.append({"movement": str(it)})
#         return out
#     return [{"movement": str(items)}]

# def _flatten_week(week_label: str, days: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
#     out: List[Dict[str, Any]] = []
#     for d in days or []:
#         day = _coerce_day(d.get("day", 1))
#         day_name = d.get("day_name") or DAY_NAMES.get(day, f"Day {day}")
#         for section in ("main", "accessory", "prehab", "cardio_notes"):
#             for item in _coerce_items(d.get(section)):
#                 out.append({
#                     "week_label": week_label,
#                     "day": day,
#                     "day_name": day_name,
#                     "block_type": section,
#                     "movement": item.get("movement", "Unknown"),
#                     "main_focus": item.get("main_focus"),
#                     "intensity_cue": item.get("intensity_cue"),
#                     "sets": _parse_int_lower_bound(item.get("sets")),
#                     "reps": _parse_int_lower_bound(item.get("reps")),
#                     "duration": item.get("duration"),
#                     "tempo_or_rest": item.get("tempo_or_rest"),
#                     "notes": item.get("notes"),
#                 })
#     return out

# def _rotate_days(days: List[Dict[str, Any]], shift: int) -> List[Dict[str, Any]]:
#     if not days:
#         return days
#     shift = shift % len(days
# )
#     return days[shift:] + days[:shift]

# _ALT_ACCESSORY = {
#     "Leg Press": "Hack Squat",
#     "Leg Curl": "Seated Leg Curl",
#     "DB Row": "Chest Supported Row",
#     "Lat Pulldown": "Pull-Up",
#     "Lateral Raise": "Cable Lateral Raise",
#     "Triceps Pushdown": "Overhead Triceps Extension",
#     "Biceps Curl": "Incline DB Curl",
#     "Rear Delt Fly": "Reverse Pec Deck",
#     "Face Pull": "Cable External Rotation",
#     "Cable Fly": "Machine Chest Fly",
#     "Split Squat": "Leg Extension",
#     "Hamstring Curl": "Nordic Curl",
# }

# def _variant_rows(rows: List[Dict[str, Any]], week_note: str, week_idx: int) -> List[Dict[str, Any]]:
#     out: List[Dict[str, Any]] = []
#     for r in rows:
#         nr = dict(r)
#         nr["week_label"] = f"Week {week_idx}"
#         if nr.get("block_type") == "accessory" and week_idx > 1:
#             mv = nr.get("movement")
#             if mv in _ALT_ACCESSORY:
#                 nr["movement"] = _ALT_ACCESSORY[mv]
#         existing = (nr.get("notes") or "").strip()
#         nr["notes"] = (f"{existing} | {week_note}".strip(" |")) if week_note else existing
#         out.append(nr)
#     return out

# def _apply_tweak_rules(days: List[Dict[str, Any]], tweak_note: Optional[str]) -> List[Dict[str, Any]]:
#     if not tweak_note or not isinstance(tweak_note, str):
#         return days
#     note = tweak_note.strip().lower()

#     def _swap(item: Dict[str, Any], new_mv: str, sets: Optional[int]=None, reps: Optional[int]=None, cue: Optional[str]=None, rest: Optional[str]=None, notes: Optional[str]=None):
#         item["movement"] = new_mv
#         if sets is not None:
#             item["sets"] = sets
#         if reps is not None:
#             item["reps"] = reps
#         if cue is not None:
#             item["intensity_cue"] = cue
#         if rest is not None:
#             item["tempo_or_rest"] = rest
#         if notes:
#             prev = (item.get("notes") or "").strip()
#             item["notes"] = (prev + (" | " if prev and notes else "") + (notes or "")).strip()

#     new_days: List[Dict[str, Any]] = []
#     for d in days:
#         d2 = {k: (v[:] if isinstance(v, list) else v) for k, v in d.items()}

#         # Shoulder pain / bench alternatives
#         if ("bench" in note and "shoulder" in note) or ("bench press" in note and "hurt" in note):
#             for section in ("main", "accessory"):
#                 items = d2.get(section) or []
#                 for it in items:
#                     if isinstance(it, dict) and isinstance(it.get("movement"), str) and "bench press" in it["movement"].lower():
#                         _swap(it, "Dumbbell Floor Press", sets=3, reps=8, cue="RPE 6–8", rest="60–90s", notes="shoulder-friendly alternative")

#         # Bodyweight instead of barbell squats
#         if ("bodyweight" in note or "body weight" in note) and "squat" in note:
#             for section in ("main", "accessory"):
#                 items = d2.get(section) or []
#                 for it in items:
#                     if isinstance(it, dict) and isinstance(it.get("movement"), str):
#                         mv = it["movement"].lower()
#                         if "back squat" in mv or mv == "squat":
#                             _swap(it, "Bulgarian Split Squat", sets=3, reps=10, cue="RPE 7–9", rest="60–90s", notes="progress load/ROM weekly")

#         # Rep-range/intensity tweak example: high-rep lateral raises
#         if "lateral" in note and "raise" in note and ("20" in note or "high rep" in note or "20+" in note or "20-30" in note):
#             for section in ("main", "accessory"):
#                 items = d2.get(section) or []
#                 for it in items:
#                     if isinstance(it, dict) and isinstance(it.get("movement"), str) and "lateral raise" in it["movement"].lower():
#                         it["reps"] = 25
#                         it["intensity_cue"] = "near failure in 20–30"
#                         it["tempo_or_rest"] = it.get("tempo_or_rest") or "45–75s"
#                         prev = (it.get("notes") or "").strip()
#                         it["notes"] = (prev + (" | " if prev else "") + "use lighter load; controlled tempo").strip()

#         new_days.append(d2)
#     return new_days

# def assess_tweak(goal: str, tweak_text: str) -> Dict[str, Any]:
#     if not tweak_text or not tweak_text.strip():
#         return {"verdict": "ok", "rationale": "No tweak provided.", "citations": [], "sources": []}
#     hits = retrieve_snippets({"query": f"{goal}. Consider tweak: {tweak_text}", "evidence": "evidence", "top_k": 6})
#     numbered = render_numbered_snippets([h.get("text", "") for h in hits])
#     user = TWEAK_ASSESSOR_USER.format(goal=goal, tweak=tweak_text, snippets=numbered)
#     schema = {
#         "type": "object",
#         "properties": {
#             "verdict": {"type": "string", "enum": ["ok", "warn", "block"]},
#             "rationale": {"type": "string"},
#             "citations": {"type": "array", "items": {"type": "integer"}},
#         },
#         "required": ["verdict", "rationale", "citations"],
#         "additionalProperties": False,
#     }
#     context = {
#         "event": "tweak_assess",
#         "goal": goal,
#         "tweak": tweak_text,
#         "snippet_ids": [h.get("id") for h in hits],
#         "prompt_chars": len(user),
#     }
#     out = call_llm_json_object_with_log(f"{TWEAK_ASSESSOR_SYSTEM}\n\n{user}", schema, context) or {}
#     out["sources"] = [{"n": i + 1, "chunk_id": h.get("id"), "doc_id": h.get("doc_id")} for i, h in enumerate(hits)]
#     return out

# # First pass: simple evidence-to-rules builder mapping goal and dpw into a canonical structure
# # using deterministic defaults derived from retrieved context (this will expand as KB grows).

# def _canon_from_evidence_rules(inputs: InputsV11, hits: List[Dict[str, Any]]) -> Optional[List[Dict[str, Any]]]:
#     dpw = max(2, min(6, int(getattr(inputs, "days_per_week", None) or 5)))
#     goal = (inputs.goal or "hypertrophy").strip().lower()
    
#     # Extract rules from snippets (TODO: implement parser)
#     kb_rules = _extract_rules_from_snippets(hits, goal)
    
#     def main_item(mv, s, r, **kwargs):
#         item = {"movement": mv, "main_focus": None, "sets": s, "reps": r}
#         item.update(kwargs)
#         return item
    
#     def acc_item(mv, s, r, **kwargs):
#         item = {"movement": mv, "sets": s, "reps": r}
#         item.update(kwargs)
#         return item
    
#     days: List[Dict[str, Any]] = []
    
#     if goal == "endurance":
#         names = ["Mon", "Wed", "Fri", "Sun"][:dpw]
#         for name in names:
#             cardio = [{
#                 "movement": "Zone 2 Cardio",
#                 "duration_or_reps": kb_rules.get("duration", "30–45 min"),
#                 "intensity_zone": kb_rules.get("intensity_zone", "Zone 2"),
#                 "cadence_or_pace": kb_rules.get("cadence", None),
#                 "rest": kb_rules.get("rest", "30–60s"),
#                 "notes": ""
#             }]
#             days.append({"day": name, "day_name": name, "main": [], "accessory": [], "prehab": [], "cardio_notes": cardio})
#         return days
    
#     if goal == "strength":
#         template = [
#             ("Mon", 
#              main_item("Back Squat", 3, 5, 
#                       intensity_cue="RPE 7–9",
#                       weight_or_1rm_pct=kb_rules.get("1rm_pct", "80% 1RM"),
#                       rpe_or_rir=kb_rules.get("rpe", "RPE 8"),
#                       rest=kb_rules.get("rest", "120–180s")),
#              [acc_item("Leg Press", 3, 8, rest="90–120s"), 
#               acc_item("Hamstring Curl", 3, 10, rest="60–90s")]),
#             ("Tue",
#              main_item("Bench Press", 4, 3,
#                       intensity_cue="RPE 7–9",
#                       weight_or_1rm_pct=kb_rules.get("1rm_pct", "85% 1RM"),
#                       rpe_or_rir=kb_rules.get("rpe", "RPE 8"),
#                       rest=kb_rules.get("rest", "120–180s")),
#              [acc_item("DB Row", 3, 8, rest="90–120s"),
#               acc_item("Triceps Pushdown", 3, 10, rest="60–90s")]),
#             ("Thu",
#              main_item("Deadlift", 3, 3,
#                       intensity_cue="RPE 7–9",
#                       weight_or_1rm_pct=kb_rules.get("1rm_pct", "85% 1RM"),
#                       rpe_or_rir=kb_rules.get("rpe", "RPE 8"),
#                       rest=kb_rules.get("rest", "180–240s")),
#              [acc_item("Back Extension", 3, 10, rest="60–90s"),
#               acc_item("Plank", 3, 30, notes="seconds")]),
#             ("Fri",
#              main_item("Overhead Press", 3, 5,
#                       intensity_cue="RPE 7–9",
#                       weight_or_1rm_pct=kb_rules.get("1rm_pct", "80% 1RM"),
#                       rpe_or_rir=kb_rules.get("rpe", "RPE 8"),
#                       rest=kb_rules.get("rest", "120–180s")),
#              [acc_item("Lat Pulldown", 3, 10, rest="60–90s"),
#               acc_item("Lateral Raise", 3, 12, rest="45–75s")]),
#         ]
#         for name, main, acc in template[:dpw]:
#             days.append({"day": name, "day_name": name, "main": [main], "accessory": acc, "prehab": [], "cardio_notes": []})
#         return days
    
#     if goal == "fat_loss":
#         template = [
#             ("Mon",
#              main_item("Burpees", None, None,
#                       work_interval=kb_rules.get("work_interval", "30s"),
#                       rest_interval=kb_rules.get("rest_interval", "20s"),
#                       rounds=kb_rules.get("rounds", 4),
#                       total_time=kb_rules.get("total_time", "20 min"),
#                       notes="HIIT circuit"),
#              [acc_item("Mountain Climbers", None, None,
#                       work_interval="30s", rest_interval="20s"),
#               acc_item("Jump Squats", None, None,
#                       work_interval="30s", rest_interval="20s")]),
#             ("Wed",
#              main_item("Kettlebell Swings", None, None,
#                       work_interval="40s", rest_interval="20s",
#                       rounds=4, total_time="20 min"),
#              [acc_item("Box Jumps", None, None,
#                       work_interval="30s", rest_interval="20s")]),
#             ("Fri",
#              main_item("Battle Ropes", None, None,
#                       work_interval="30s", rest_interval="20s",
#                       rounds=4, total_time="20 min"),
#              [acc_item("High Knees", None, None,
#                       work_interval="30s", rest_interval="20s")]),
#         ]
#         for name, main, acc in template[:dpw]:
#             days.append({"day": name, "day_name": name, "main": [main], "accessory": acc, "prehab": [], "cardio_notes": []})
#         return days
    
#     # Hypertrophy default
#     template = [
#         ("Mon",
#          main_item("Bench Press", 3, 6,
#                   intensity_cue="RPE 7–9",
#                   tempo=kb_rules.get("tempo", "3-1-2-0"),
#                   target_muscle=kb_rules.get("target_muscle", "Chest"),
#                   rest=kb_rules.get("rest", "90–120s")),
#          [acc_item("Incline DB Press", 3, 10,
#                   tempo=kb_rules.get("tempo", "2-0-2-0"),
#                   target_muscle="Upper Chest",
#                   rest="60–90s"),
#           acc_item("Lateral Raise", 3, 15,
#                   target_muscle="Shoulders",
#                   rest="45–75s"),
#           acc_item("Triceps Pushdown", 3, 12,
#                   target_muscle="Triceps",
#                   rest="60–90s")]),
#         ("Tue",
#          main_item("Back Squat", 3, 6,
#                   intensity_cue="RPE 7–9",
#                   tempo=kb_rules.get("tempo", "3-0-1-0"),
#                   target_muscle="Quads",
#                   rest="120–180s"),
#          [acc_item("Leg Press", 3, 12,
#                   target_muscle="Quads",
#                   rest="60–90s"),
#           acc_item("Leg Curl", 3, 12,
#                   target_muscle="Hamstrings",
#                   rest="60–90s"),
#           acc_item("Calf Raise", 3, 15,
#                   target_muscle="Calves",
#                   rest="45–75s")]),
#         ("Wed",
#          main_item("Barbell Row", 3, 6,
#                   intensity_cue="RPE 7–9",
#                   tempo=kb_rules.get("tempo", "2-0-2-0"),
#                   target_muscle="Back",
#                   rest="90–120s"),
#          [acc_item("Lat Pulldown", 3, 10,
#                   target_muscle="Lats",
#                   rest="60–90s"),
#           acc_item("Rear Delt Fly", 3, 15,
#                   target_muscle="Rear Delts",
#                   rest="45–75s"),
#           acc_item("Biceps Curl", 3, 12,
#                   target_muscle="Biceps",
#                   rest="60–90s")]),
#         ("Thu",
#          main_item("Romanian Deadlift", 3, 6,
#                   intensity_cue="RPE 7–9",
#                   tempo=kb_rules.get("tempo", "3-0-2-0"),
#                   target_muscle="Hamstrings",
#                   rest="120–180s"),
#          [acc_item("Split Squat", 3, 10,
#                   target_muscle="Quads",
#                   rest="60–90s"),
#           acc_item("Hamstring Curl", 3, 12,
#                   target_muscle="Hamstrings",
#                   rest="60–90s"),
#           acc_item("Back Extension", 3, 12,
#                   target_muscle="Lower Back",
#                   rest="60–90s")]),
#         ("Fri",
#          main_item("Overhead Press", 3, 6,
#                   intensity_cue="RPE 7–9",
#                   tempo=kb_rules.get("tempo", "2-0-2-0"),
#                   target_muscle="Shoulders",
#                   rest="90–120s"),
#          [acc_item("DB Row", 3, 10,
#                   target_muscle="Back",
#                   rest="60–90s"),
#           acc_item("Face Pull", 3, 15,
#                   target_muscle="Rear Delts",
#                   rest="45–75s"),
#           acc_item("Cable Fly", 3, 12,
#                   target_muscle="Chest",
#                   rest="60–90s")]),
#     ]
#     for name, main, acc in template[:dpw]:
#         days.append({"day": name, "day_name": name, "main": [main], "accessory": acc, "prehab": [], "cardio_notes": []})
#     return days

# def generate_plan_v11(inputs: InputsV11, tweak_note: Optional[str] = None) -> PlanV11:
#     pal_value = PALMAP[inputs.pal_code]
#     bmr = bmr_mifflin_st_jeor(inputs.sex, inputs.weight_kg, inputs.height_cm, inputs.age)
#     tdee = tdee_from_bmr(bmr, pal_value)

#     # Retrieval
#     retrieval_query = _make_retrieval_query(inputs)
#     try:
#         snippet_hits = retrieve_snippets({"query": retrieval_query, "domains": getattr(inputs, "domain_filters", None), "evidence": "evidence", "top_k": 6})
#     except Exception as e:
#         print(f"[Plan] RAG disabled or failed: {e}")
#         snippet_hits = []
#     if snippet_hits:
#         for i, s in enumerate(snippet_hits, 1):
#             print(f"[Sources] [{i}] doc {s.get('doc_id')} · chunk {s.get('id')}")
#     snippets_text = render_snippets_for_v11([s.get("text", "") for s in snippet_hits]) if snippet_hits else "- none"

#     # Advisory LLM (optional)
#     user_prompt = USER_TEMPLATE_V11.format(
#         sex=inputs.sex, age=inputs.age, height_cm=inputs.height_cm, weight_kg=inputs.weight_kg,
#         pal_value=pal_value, goal=inputs.goal, equipment=inputs.equipment or [],
#         bmr=bmr, tdee=tdee, days_per_week=getattr(inputs, "days_per_week", None) or 5,
#         snippets=snippets_text, tweak=tweak_note or "",
#     )
#     prompt = SYSTEM_PROMPT_V11 + "\n" + user_prompt
#     schema = {"type": "object"}
#     context = {
#         "event": "plan_generate",
#         "goal": inputs.goal,
#         "days_per_week": getattr(inputs, "days_per_week", None) or 5,
#         "retrieval_query": retrieval_query,
#         "snippet_ids": [s.get("id") for s in (snippet_hits or [])],
#         "prompt_chars": len(user_prompt),
#     }
#     compact: Dict[str, Any] = {}
#     if USE_LLM_JSON:
#         compact = call_llm_json_object_with_log(prompt, schema, context) or {}

#     # No silent fallbacks: require evidence
#     if not snippet_hits:
#         print("[Plan] Unavailable: no RAG snippets; blocking plan render")
#         return PlanV11(goal=inputs.goal, rows=[], week_count=0, extra={"snippets_count": 0, "retrieval_query": retrieval_query, "evidence_built": False, "reason": "no_snippets"})

#     # Build canonical week from evidence (LLM compact if valid, else deterministic rules)
#     canon_days: Optional[List[Dict[str, Any]]] = None
#     if USE_LLM_JSON and (compact.get("canonical_week") or {}).get("days"):
#         canon_days = (compact["canonical_week"]["days"])
#     if canon_days is None:
#         canon_days = _canon_from_evidence_rules(inputs, snippet_hits)

#     if not canon_days:
#         print("[Plan] Unavailable: no canonical week from evidence; blocking plan render")
#         return PlanV11(goal=inputs.goal, rows=[], week_count=0, extra={
#             "snippets_count": len(snippet_hits),
#             "retrieval_query": retrieval_query,
#             "evidence_built": False,
#             "reason": "no_canonical_from_evidence",
#         })

#     # Apply tweaks and expand
#     canon_days = _apply_tweak_rules(canon_days, tweak_note)
#     week1_rows = _flatten_week("Week 1", canon_days)

#     rotated_rows_all: List[Dict[str, Any]] = []
#     rotated_rows_all += week1_rows
#     week_notes = {2: "+1 rep per set", 3: "+2.5–5% load", 4: "deload 15–25%"}
#     for wk in (2, 3, 4):
#         rotated_days = _rotate_days(canon_days, shift=wk - 1)
#         wk_rows_base = _flatten_week(f"Week {wk}", rotated_days)
#         wk_rows = _variant_rows(wk_rows_base, week_notes.get(wk, ""), wk)
#         rotated_rows_all += wk_rows

#     rows_json = _sanitize_rows(rotated_rows_all)
#     try:
#         rows: List[PlanRowV11] = [PlanRowV11(**r) for r in rows_json]
#     except ValidationError:
#         repaired = _second_pass_repair(rows_json)
#         rows = [PlanRowV11(**r) for r in repaired]

#     priority = {"main": 0, "accessory": 1, "prehab": 2, "cardio_notes": 3}
#     rows.sort(key=lambda r: (r.week_label, r.day, priority.get(r.block_type, 9)))

#     plan = PlanV11(goal=inputs.goal, rows=rows, week_count=4)
#     plan.extra = {
#         "snippets_count": len(snippet_hits),
#         "retrieval_query": retrieval_query,
#         "evidence_built": True,
#         "used_llm_for_rows": bool(USE_LLM_JSON and (compact.get("canonical_week") or {}).get("days")),
#     }
#     return plan

# # Helpers
# def _sanitize_rows(rows_json: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
#     cleaned: List[Dict[str, Any]] = []
#     per_day_seen: Dict[int, int] = {}
#     for r in rows_json:
#         day = _coerce_day(r.get("day", 1))
#         per_day_seen[day] = per_day_seen.get(day, 0) + 1
#         week_label = r.get("week_label") or "Week 1"
#         day_name = r.get("day_name") or DAY_NAMES.get(day, f"Day {day}")
#         block_type = r.get("block_type") or ("main" if per_day_seen[day] == 1 else "accessory")
#         movement = r.get("movement") or "Unknown"
#         cleaned.append({
#             "week_label": week_label, "day": day, "day_name": day_name, "block_type": block_type,
#             "movement": movement, "main_focus": r.get("main_focus"), "intensity_cue": r.get("intensity_cue"),
#             "sets": _parse_int_lower_bound(r.get("sets")), "reps": _parse_int_lower_bound(r.get("reps")),
#             "duration": r.get("duration"), "tempo_or_rest": r.get("tempo_or_rest"), "notes": r.get("notes"),
#         })
#     return cleaned

# def _second_pass_repair(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
#     repaired: List[Dict[str, Any]] = []
#     for r in rows:
#         if not isinstance(r.get("day"), int) or r.get("movement") in (None, "", "Unknown"):
#             r["movement"] = r.get("movement") or "Unknown"
#         r["sets"] = r["sets"] if isinstance(r.get("sets"), int) else None
#         r["reps"] = r["reps"] if isinstance(r.get("reps"), int) else None
#         repaired.append(r)
#     return repaired





# src/fitapp_core/plan_v11.py
from __future__ import annotations

import os
import re
from typing import Optional, List, Dict, Any

from pydantic import ValidationError

from .models_v11 import InputsV11, PlanV11, PlanRowV11
from .models import PAL_MAP as PALMAP
from .energy import bmr_mifflin_st_jeor, tdee_from_bmr
from .rag.retriever import retrieve_snippets
from .rag.prompts import (
    SYSTEM_PROMPT_V11,
    USER_TEMPLATE_V11,
    render_snippets_for_v11,
    TWEAK_ASSESSOR_SYSTEM,
    TWEAK_ASSESSOR_USER,
    render_numbered_snippets,
)
from .rag.llm import call_llm_json_object_with_log

# Feature flag: optional compact LLM JSON (advisory); plan rows must be evidence-built
USE_LLM_JSON = os.getenv("PLAN_V11_USE_LLM_JSON", "false").strip().lower() in ("1", "true", "yes")

DAY_NAMES = {1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat", 7: "Sun"}
DAY_NAME_MAP = {
    "mon": 1, "monday": 1, "tue": 2, "tuesday": 2, "wed": 3, "wednesday": 3,
    "thu": 4, "thursday": 4, "fri": 5, "friday": 5, "sat": 6, "saturday": 6, "sun": 7, "sunday": 7,
}


def _parse_int_lower_bound(val: Any) -> Optional[int]:
    if isinstance(val, int):
        return val
    if isinstance(val, str):
        m = re.match(r"\s*(\d+)\s*(?:[-–]\s*\d+)?\s*$", val)
        if m:
            return int(m.group(1))
    return None


def _coerce_day(val: Any) -> int:
    try:
        return int(val)
    except Exception:
        if isinstance(val, str):
            return DAY_NAME_MAP.get(val.strip().lower(), 1)
        return 1


def _make_retrieval_query(inputs: InputsV11) -> str:
    goal = inputs.goal or ""
    exp = getattr(inputs, "experience", "") or ""
    days = getattr(inputs, "days_per_week", None)
    equip_list = getattr(inputs, "equipment", None) or []
    equip = ", ".join(equip_list) if isinstance(equip_list, list) else str(equip_list or "")
    parts = [goal, exp]
    if days:
        parts.append(f"{days} days/week")
    if equip:
        parts.append(f"equipment: {equip}")
    return ", ".join([p for p in parts if p]).strip(", ")


# ============================================================================
# NEW: Evidence prescription extraction from research PDFs
# ============================================================================

# def _extract_prescriptions_from_hits(hits: List[Dict[str, Any]], goal: str) -> Dict[str, Any]:
#     """
#     Extract goal-specific prescription values from retrieved evidence.
#     Returns dict with 'main' and 'accessory' prescription parameters.
#     """
#     prescriptions = {"main": {}, "accessory": {}, "found": False}
#     goal_lower = goal.lower()
    
#     for hit in hits:
#         text = hit.get("text", "")
        
#         # Look for prescription sections
#         if "PROGRAMMING PRESCRIPTIONS" not in text.upper() and "PRESCRIPTIONS" not in text.upper():
#             continue
        
#         prescriptions["found"] = True
#         print(f"[Prescriptions] Found prescription data for {goal_lower}")
        
#         # Extract based on goal type
#         if goal_lower == "hypertrophy":
#             prescriptions.update(_extract_hypertrophy_prescriptions(text))
#         elif goal_lower == "strength":
#             prescriptions.update(_extract_strength_prescriptions(text))
#         elif goal_lower == "endurance":
#             prescriptions.update(_extract_endurance_prescriptions(text))
#         elif goal_lower == "fat_loss" or goal_lower == "fatloss":
#             prescriptions.update(_extract_fatloss_prescriptions(text))
    
#     return prescriptions
def _extract_prescriptions_from_hits(hits: List[Dict[str, Any]], goal: str) -> Dict[str, Any]:
    """
    Extract goal-specific prescription values from retrieved evidence.
    Returns dict with 'main' and 'accessory' prescription parameters.
    """
    prescriptions = {"main": {}, "accessory": {}, "found": False}
    goal_lower = goal.lower()
    
    for hit in hits:
        text = hit.get("text", "")
        
        # Look for prescription sections
        if "PROGRAMMING PRESCRIPTIONS" not in text.upper() and "PRESCRIPTIONS" not in text.upper():
            continue
        
        prescriptions["found"] = True
        print(f"[Prescriptions] Found prescription data for {goal_lower} in chunk {hit.get('id', 'unknown')}")
        
        # Extract based on goal type and MERGE results (don't overwrite)
        if goal_lower == "hypertrophy":
            extracted = _extract_hypertrophy_prescriptions(text)
            # Merge main
            for k, v in extracted.get("main", {}).items():
                if k not in prescriptions["main"]:  # Don't overwrite existing
                    prescriptions["main"][k] = v
            # Merge accessory
            for k, v in extracted.get("accessory", {}).items():
                if k not in prescriptions["accessory"]:
                    prescriptions["accessory"][k] = v
                    
        elif goal_lower == "strength":
            extracted = _extract_strength_prescriptions(text)
            for k, v in extracted.get("main", {}).items():
                if k not in prescriptions["main"]:
                    prescriptions["main"][k] = v
            for k, v in extracted.get("accessory", {}).items():
                if k not in prescriptions["accessory"]:
                    prescriptions["accessory"][k] = v
                    
        elif goal_lower == "endurance":
            extracted = _extract_endurance_prescriptions(text)
            for k, v in extracted.get("main", {}).items():
                if k not in prescriptions["main"]:
                    prescriptions["main"][k] = v
            for k, v in extracted.get("accessory", {}).items():
                if k not in prescriptions["accessory"]:
                    prescriptions["accessory"][k] = v
                    
        elif goal_lower == "fat_loss" or goal_lower == "fatloss":
            extracted = _extract_fatloss_prescriptions(text)
            for k, v in extracted.get("main", {}).items():
                if k not in prescriptions["main"]:
                    prescriptions["main"][k] = v
            for k, v in extracted.get("accessory", {}).items():
                if k not in prescriptions["accessory"]:
                    prescriptions["accessory"][k] = v
    
    # Debug log final state
    print(f"[Prescriptions] Final main fields: {list(prescriptions['main'].keys())}")
    print(f"[Prescriptions] Final accessory fields: {list(prescriptions['accessory'].keys())}")
    
    return prescriptions





def _extract_hypertrophy_prescriptions(text: str) -> Dict[str, Any]:
    """Extract hypertrophy-specific prescriptions: tempo, rest, target_muscle."""
    presc = {"main": {}, "accessory": {}}
    
    # Find main compound section
    main_match = re.search(
        r"MAIN COMPOUND.*?(?=ACCESSORY|EVIDENCE|$)", 
        text, re.DOTALL | re.IGNORECASE
    )
    if main_match:
        main_text = main_match.group(0)
        
        # Sets
        sets_match = re.search(r"Sets?:\s*(\d+)-?(\d*)", main_text, re.IGNORECASE)
        if sets_match:
            if sets_match.group(2):
                presc["main"]["sets"] = f"{sets_match.group(1)}-{sets_match.group(2)}"
            else:
                presc["main"]["sets"] = sets_match.group(1)
            print(f"[Hypertrophy] Main sets: {presc['main']['sets']}")
        
        # Reps
        reps_match = re.search(r"Reps?:\s*(\d+)-?(\d*)", main_text, re.IGNORECASE)
        if reps_match:
            if reps_match.group(2):
                presc["main"]["reps"] = f"{reps_match.group(1)}-{reps_match.group(2)}"
            else:
                presc["main"]["reps"] = reps_match.group(1)
            print(f"[Hypertrophy] Main reps: {presc['main']['reps']}")
        
        # Tempo
        tempo_match = re.search(r'Tempo:.*?["\']?([0-9-]+)["\']?', main_text, re.IGNORECASE)
        if tempo_match:
            presc["main"]["tempo"] = tempo_match.group(1)
            print(f"[Hypertrophy] Main tempo: {presc['main']['tempo']}")
        
        # Rest
        rest_match = re.search(r"Rest:\s*(\d+)-?(\d*)s", main_text, re.IGNORECASE)
        if rest_match:
            if rest_match.group(2):
                presc["main"]["rest"] = f"{rest_match.group(1)}-{rest_match.group(2)}s"
            else:
                presc["main"]["rest"] = f"{rest_match.group(1)}s"
            print(f"[Hypertrophy] Main rest: {presc['main']['rest']}")
        
        # Target muscles
        target_match = re.search(r"Target muscles?:\s*([^\n]+)", main_text, re.IGNORECASE)
        if target_match:
            presc["main"]["target_muscles"] = [m.strip() for m in target_match.group(1).split(",")]
    
    # Find accessory section
    acc_match = re.search(
        r"ACCESSORY.*?(?=EVIDENCE|PROGRAMMING|$)", 
        text, re.DOTALL | re.IGNORECASE
    )
    if acc_match:
        acc_text = acc_match.group(0)
        
        # Sets
        sets_match = re.search(r"Sets?:\s*(\d+)", acc_text, re.IGNORECASE)
        if sets_match:
            presc["accessory"]["sets"] = sets_match.group(1)
            print(f"[Hypertrophy] Acc sets: {presc['accessory']['sets']}")
        
        # Reps
        reps_match = re.search(r"Reps?:\s*(\d+)-?(\d*)", acc_text, re.IGNORECASE)
        if reps_match:
            if reps_match.group(2):
                presc["accessory"]["reps"] = f"{reps_match.group(1)}-{reps_match.group(2)}"
            else:
                presc["accessory"]["reps"] = reps_match.group(1)
            print(f"[Hypertrophy] Acc reps: {presc['accessory']['reps']}")
        
        # Tempo
        tempo_match = re.search(r'Tempo:.*?["\']?([0-9-]+)["\']?', acc_text, re.IGNORECASE)
        if tempo_match:
            presc["accessory"]["tempo"] = tempo_match.group(1)
        
        # Rest
        rest_match = re.search(r"Rest:\s*(\d+)-?(\d*)s", acc_text, re.IGNORECASE)
        if rest_match:
            if rest_match.group(2):
                presc["accessory"]["rest"] = f"{rest_match.group(1)}-{rest_match.group(2)}s"
            else:
                presc["accessory"]["rest"] = f"{rest_match.group(1)}s"
    
    return presc


def _extract_strength_prescriptions(text: str) -> Dict[str, Any]:
    """Extract strength-specific prescriptions: %1RM, RPE/RIR, rest."""
    presc = {"main": {}, "accessory": {}}
    
    # Find main compound section
    main_match = re.search(
        r"MAIN COMPOUND.*?(?=ACCESSORY|EVIDENCE|$)", 
        text, re.DOTALL | re.IGNORECASE
    )
    if main_match:
        main_text = main_match.group(0)
        
        # Sets
        sets_match = re.search(r"Sets?:\s*(\d+)-?(\d*)", main_text, re.IGNORECASE)
        if sets_match:
            if sets_match.group(2):
                presc["main"]["sets"] = f"{sets_match.group(1)}-{sets_match.group(2)}"
            else:
                presc["main"]["sets"] = sets_match.group(1)
            print(f"[Strength] Main sets: {presc['main']['sets']}")
        
        # Reps
        reps_match = re.search(r"Reps?:\s*(\d+)-?(\d*)", main_text, re.IGNORECASE)
        if reps_match:
            if reps_match.group(2):
                presc["main"]["reps"] = f"{reps_match.group(1)}-{reps_match.group(2)}"
            else:
                presc["main"]["reps"] = reps_match.group(1)
            print(f"[Strength] Main reps: {presc['main']['reps']}")
        
        # %1RM
        onerm_match = re.search(r"(\d+)-?(\d*)%\s*1RM", main_text, re.IGNORECASE)
        if onerm_match:
            if onerm_match.group(2):
                presc["main"]["weight_or_1rm_pct"] = f"{onerm_match.group(1)}-{onerm_match.group(2)}% 1RM"
            else:
                presc["main"]["weight_or_1rm_pct"] = f"{onerm_match.group(1)}% 1RM"
            print(f"[Strength] Main %1RM: {presc['main']['weight_or_1rm_pct']}")
        
        # RPE
        rpe_match = re.search(r"RPE\s*(\d+)-?(\d*)", main_text, re.IGNORECASE)
        if rpe_match:
            if rpe_match.group(2):
                presc["main"]["rpe_or_rir"] = f"RPE {rpe_match.group(1)}-{rpe_match.group(2)}"
            else:
                presc["main"]["rpe_or_rir"] = f"RPE {rpe_match.group(1)}"
            print(f"[Strength] Main RPE: {presc['main']['rpe_or_rir']}")
        
        # RIR (alternative to RPE)
        if "rpe_or_rir" not in presc["main"]:
            rir_match = re.search(r"(\d+)-?(\d*)\s*RIR", main_text, re.IGNORECASE)
            if rir_match:
                if rir_match.group(2):
                    presc["main"]["rpe_or_rir"] = f"{rir_match.group(1)}-{rir_match.group(2)} RIR"
                else:
                    presc["main"]["rpe_or_rir"] = f"{rir_match.group(1)} RIR"
        
        # Rest
        rest_match = re.search(r"Rest:\s*(\d+)-?(\d*)(?:s|min)", main_text, re.IGNORECASE)
        if rest_match:
            unit = "min" if "min" in main_text[rest_match.start():rest_match.end()] else "s"
            if rest_match.group(2):
                presc["main"]["rest"] = f"{rest_match.group(1)}-{rest_match.group(2)}{unit}"
            else:
                presc["main"]["rest"] = f"{rest_match.group(1)}{unit}"
            print(f"[Strength] Main rest: {presc['main']['rest']}")
    
    # Accessory section
    acc_match = re.search(
        r"ACCESSORY.*?(?=EVIDENCE|PROGRAMMING|$)", 
        text, re.DOTALL | re.IGNORECASE
    )
    if acc_match:
        acc_text = acc_match.group(0)
        sets_match = re.search(r"Sets?:\s*(\d+)-?(\d*)", acc_text, re.IGNORECASE)
        if sets_match:
            presc["accessory"]["sets"] = sets_match.group(1) if not sets_match.group(2) else f"{sets_match.group(1)}-{sets_match.group(2)}"
        
        reps_match = re.search(r"Reps?:\s*(\d+)-?(\d*)", acc_text, re.IGNORECASE)
        if reps_match:
            presc["accessory"]["reps"] = reps_match.group(1) if not reps_match.group(2) else f"{reps_match.group(1)}-{reps_match.group(2)}"
    
    return presc


def _extract_endurance_prescriptions(text: str) -> Dict[str, Any]:
    """Extract endurance-specific prescriptions: duration, zone, cadence/pace."""
    presc = {"main": {}, "accessory": {}}
    
    # Zone 2 (base)
    zone2_match = re.search(
        r"AEROBIC BASE.*?(?=THRESHOLD|VO2|EVIDENCE|$)", 
        text, re.DOTALL | re.IGNORECASE
    )
    if zone2_match:
        zone2_text = zone2_match.group(0)
        
        # Duration
        duration_match = re.search(r"Duration:\s*(\d+)-?(\d*)min", zone2_text, re.IGNORECASE)
        if duration_match:
            if duration_match.group(2):
                presc["main"]["duration_or_reps"] = f"{duration_match.group(1)}-{duration_match.group(2)}min"
            else:
                presc["main"]["duration_or_reps"] = f"{duration_match.group(1)}min"
            print(f"[Endurance] Duration: {presc['main']['duration_or_reps']}")
        
        # Intensity Zone
        zone_match = re.search(r"Zone\s*(\d+)", zone2_text, re.IGNORECASE)
        if zone_match:
            presc["main"]["intensity_zone"] = f"Zone {zone_match.group(1)}"
            print(f"[Endurance] Zone: {presc['main']['intensity_zone']}")
        
        # Cadence
        cadence_match = re.search(r"(\d+)-?(\d*)\s*spm", zone2_text, re.IGNORECASE)
        if cadence_match:
            if cadence_match.group(2):
                presc["main"]["cadence_or_pace"] = f"{cadence_match.group(1)}-{cadence_match.group(2)} spm"
            else:
                presc["main"]["cadence_or_pace"] = f"{cadence_match.group(1)} spm"
    
    # Zone 5 (VO2max intervals)
    vo2_match = re.search(
        r"VO2.*?(?=EVIDENCE|PROGRAMMING|$)", 
        text, re.DOTALL | re.IGNORECASE
    )
    if vo2_match:
        vo2_text = vo2_match.group(0)
        
        duration_match = re.search(r"Duration:\s*(\d+)-?(\d*)min", vo2_text, re.IGNORECASE)
        if duration_match:
            if duration_match.group(2):
                presc["accessory"]["duration_or_reps"] = f"{duration_match.group(1)}-{duration_match.group(2)}min"
            else:
                presc["accessory"]["duration_or_reps"] = f"{duration_match.group(1)}min"
        
        zone_match = re.search(r"Zone\s*(\d+)", vo2_text, re.IGNORECASE)
        if zone_match:
            presc["accessory"]["intensity_zone"] = f"Zone {zone_match.group(1)}"
    
    return presc


def _extract_fatloss_prescriptions(text: str) -> Dict[str, Any]:
    """Extract fat loss-specific prescriptions: work/rest intervals, rounds, total time."""
    presc = {"main": {}, "accessory": {}}
    
    # HIIT circuits
    hiit_match = re.search(
        r"HIIT.*?(?=METABOLIC|STEADY|EVIDENCE|$)", 
        text, re.DOTALL | re.IGNORECASE
    )
    if hiit_match:
        hiit_text = hiit_match.group(0)
        
        # Work interval
        work_match = re.search(r"Work Interval:\s*(\d+)s", hiit_text, re.IGNORECASE)
        if work_match:
            presc["main"]["work_interval"] = f"{work_match.group(1)}s"
            print(f"[Fat Loss] Work interval: {presc['main']['work_interval']}")
        
        # Rest interval
        rest_match = re.search(r"Rest Interval:\s*(\d+)s", hiit_text, re.IGNORECASE)
        if rest_match:
            presc["main"]["rest_interval"] = f"{rest_match.group(1)}s"
            print(f"[Fat Loss] Rest interval: {presc['main']['rest_interval']}")
        
        # Rounds
        rounds_match = re.search(r"Rounds:\s*(\d+)-?(\d*)", hiit_text, re.IGNORECASE)
        if rounds_match:
            if rounds_match.group(2):
                presc["main"]["rounds"] = f"{rounds_match.group(1)}-{rounds_match.group(2)}"
            else:
                presc["main"]["rounds"] = rounds_match.group(1)
            print(f"[Fat Loss] Rounds: {presc['main']['rounds']}")
        
        # Total time
        total_match = re.search(r"Total Time:\s*(\d+)-?(\d*)min", hiit_text, re.IGNORECASE)
        if total_match:
            if total_match.group(2):
                presc["main"]["total_time"] = f"{total_match.group(1)}-{total_match.group(2)}min"
            else:
                presc["main"]["total_time"] = f"{total_match.group(1)}min"
            print(f"[Fat Loss] Total time: {presc['main']['total_time']}")
    
    return presc


def _parse_range(val: str) -> int:
    """Extract lower bound from '3-4' or '6-10' etc."""
    if isinstance(val, int):
        return val
    if isinstance(val, str):
        m = re.match(r"(\d+)", val)
        if m:
            return int(m.group(1))
    return 3  # sensible default


def _get_required_fields(goal: str) -> List[str]:
    """Return minimum required prescription fields per goal."""
    if goal == "hypertrophy":
        return ["sets", "reps"]  # Tempo and rest optional but recommended
    elif goal == "strength":
        return ["sets", "reps"]  # %1RM and RPE optional but recommended
    elif goal == "endurance":
        return ["duration_or_reps", "intensity_zone"]
    elif goal == "fat_loss" or goal == "fatloss":
        return ["work_interval", "rest_interval"]
    return ["sets", "reps"]


# ============================================================================
# END: Evidence prescription extraction
# ============================================================================


# Keep the fallback function defined but never called (no silent fallbacks).
def _default_canonical_week(inputs: InputsV11) -> List[Dict[str, Any]]:
    dpw = getattr(inputs, "days_per_week", None) or 5
    dpw = max(2, min(6, int(dpw)))
    goal = (inputs.goal or "hypertrophy").lower()

    def main_item(mv, s, r, notes=""):
        return {"movement": mv, "main_focus": None, "intensity_cue": "RPE 6–8", "sets": s, "reps": r, "tempo_or_rest": "60–90s", "notes": notes}
    def acc_item(mv, s, r, notes=""):
        return {"movement": mv, "sets": s, "reps": r, "tempo_or_rest": "45–75s", "notes": notes}

    days: List[Dict[str, Any]] = []
    if goal == "strength":
        template = [
            ("Mon", main_item("Back Squat", 3, 5), [acc_item("Leg Press", 3, 8), acc_item("Hamstring Curl", 3, 10)]),
            ("Tue", main_item("Bench Press", 4, 3), [acc_item("DB Row", 3, 8), acc_item("Triceps Pushdown", 3, 10)]),
            ("Thu", main_item("Deadlift", 3, 3), [acc_item("Back Extension", 3, 10), acc_item("Plank", 3, 30)]),
            ("Fri", main_item("Overhead Press", 3, 5), [acc_item("Lat Pulldown", 3, 10), acc_item("Lateral Raise", 3, 12)]),
        ]
        for name, main, acc in template[:dpw]:
            days.append({"day": name, "day_name": name, "main": [main], "accessory": acc, "prehab": [], "cardio_notes": []})
        return days

    if goal == "endurance":
        for name in ["Mon", "Wed", "Fri", "Sun"][:dpw]:
            cardio = [{"movement": "Zone 2 Cardio", "duration": "30–45 min", "tempo_or_rest": "Zone 2", "notes": ""}]
            days.append({"day": name, "day_name": name, "main": [], "accessory": [], "prehab": [], "cardio_notes": cardio})
        return days

    if goal == "fat_loss":
        template = [
            ("Mon", main_item("Back Squat", 3, 8), [acc_item("Leg Press", 3, 12), acc_item("Calf Raise", 3, 15)], [{"movement": "Zone 2 Cardio", "duration":"20–30 min","tempo_or_rest":"Zone 2","notes":""}]),
            ("Tue", main_item("Bench Press", 3, 8), [acc_item("DB Row", 3, 12), acc_item("Face Pull", 3, 15)], []),
            ("Thu", main_item("Romanian Deadlift", 3, 8), [acc_item("Hamstring Curl", 3, 12), acc_item("Reverse Lunge", 3, 10)], [{"movement": "Zone 2 Cardio", "duration":"20–30 min","tempo_or_rest":"Zone 2","notes":""}]),
            ("Fri", main_item("Overhead Press", 3, 8), [acc_item("Lat Pulldown", 3, 12), acc_item("Biceps Curl", 3, 12)], []),
        ]
        for name, main, acc, cardio in template[:dpw]:
            days.append({"day": name, "day_name": name, "main": [main], "accessory": acc, "prehab": [], "cardio_notes": cardio})
        return days

    template = [
        ("Mon", main_item("Bench Press", 3, 8), [acc_item("Incline DB Press", 3, 10), acc_item("Lateral Raise", 3, 12), acc_item("Triceps Pushdown", 3, 12)]),
        ("Tue", main_item("Back Squat", 3, 8), [acc_item("Leg Press", 3, 12), acc_item("Leg Curl", 3, 12), acc_item("Calf Raise", 3, 15)]),
        ("Wed", main_item("Barbell Row", 3, 8), [acc_item("Lat Pulldown", 3, 10), acc_item("Rear Delt Fly", 3, 12), acc_item("Biceps Curl", 3, 12)]),
        ("Thu", main_item("Romanian Deadlift", 3, 8), [acc_item("Split Squat", 3, 10), acc_item("Hamstring Curl", 3, 12), acc_item("Back Extension", 3, 12)]),
        ("Fri", main_item("Overhead Press", 3, 8), [acc_item("DB Row", 3, 10), acc_item("Face Pull", 3, 12), acc_item("Cable Fly", 3, 12)]),
    ]
    for name, main, acc in template[:dpw]:
        days.append({"day": name, "day_name": name, "main": [main], "accessory": acc, "prehab": [], "cardio_notes": []})
    return days


def _coerce_items(items: Any) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if items is None:
        return out
    if isinstance(items, dict):
        return [items]
    if isinstance(items, list):
        for it in items:
            if isinstance(it, dict):
                out.append(it)
            else:
                out.append({"movement": str(it)})
        return out
    return [{"movement": str(items)}]


def _flatten_week(week_label: str, days: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for d in days or []:
        day = _coerce_day(d.get("day", 1))
        day_name = d.get("day_name") or DAY_NAMES.get(day, f"Day {day}")
        for section in ("main", "accessory", "prehab", "cardio_notes"):
            for item in _coerce_items(d.get(section)):
                out.append({
                    "week_label": week_label,
                    "day": day,
                    "day_name": day_name,
                    "block_type": section,
                    "movement": item.get("movement", "Unknown"),
                    "main_focus": item.get("main_focus"),
                    "intensity_cue": item.get("intensity_cue"),
                    "sets": _parse_int_lower_bound(item.get("sets")),
                    "reps": _parse_int_lower_bound(item.get("reps")),
                    "duration": item.get("duration"),
                    "tempo_or_rest": item.get("tempo_or_rest"),
                    "notes": item.get("notes"),
                    # Goal-specific fields (pass through if present)
                    "tempo": item.get("tempo"),
                    "rest": item.get("rest"),
                    "target_muscle": item.get("target_muscle"),
                    "weight_or_1rm_pct": item.get("weight_or_1rm_pct"),
                    "rpe_or_rir": item.get("rpe_or_rir"),
                    "duration_or_reps": item.get("duration_or_reps"),
                    "intensity_zone": item.get("intensity_zone"),
                    "cadence_or_pace": item.get("cadence_or_pace"),
                    "work_interval": item.get("work_interval"),
                    "rest_interval": item.get("rest_interval"),
                    "rounds": item.get("rounds"),
                    "total_time": item.get("total_time"),
                })
    return out


def _rotate_days(days: List[Dict[str, Any]], shift: int) -> List[Dict[str, Any]]:
    if not days:
        return days
    shift = shift % len(days)
    return days[shift:] + days[:shift]


_ALT_ACCESSORY = {
    "Leg Press": "Hack Squat",
    "Leg Curl": "Seated Leg Curl",
    "DB Row": "Chest Supported Row",
    "Lat Pulldown": "Pull-Up",
    "Lateral Raise": "Cable Lateral Raise",
    "Triceps Pushdown": "Overhead Triceps Extension",
    "Biceps Curl": "Incline DB Curl",
    "Rear Delt Fly": "Reverse Pec Deck",
    "Face Pull": "Cable External Rotation",
    "Cable Fly": "Machine Chest Fly",
    "Split Squat": "Leg Extension",
    "Hamstring Curl": "Nordic Curl",
}


def _variant_rows(rows: List[Dict[str, Any]], week_note: str, week_idx: int) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for r in rows:
        nr = dict(r)
        nr["week_label"] = f"Week {week_idx}"
        if nr.get("block_type") == "accessory" and week_idx > 1:
            mv = nr.get("movement")
            if mv in _ALT_ACCESSORY:
                nr["movement"] = _ALT_ACCESSORY[mv]
        existing = (nr.get("notes") or "").strip()
        nr["notes"] = (f"{existing} | {week_note}".strip(" |")) if week_note else existing
        out.append(nr)
    return out


def _apply_tweak_rules(days: List[Dict[str, Any]], tweak_note: Optional[str]) -> List[Dict[str, Any]]:
    if not tweak_note or not isinstance(tweak_note, str):
        return days
    note = tweak_note.strip().lower()

    def _swap(item: Dict[str, Any], new_mv: str, sets: Optional[int]=None, reps: Optional[int]=None, cue: Optional[str]=None, rest: Optional[str]=None, notes: Optional[str]=None):
        item["movement"] = new_mv
        if sets is not None:
            item["sets"] = sets
        if reps is not None:
            item["reps"] = reps
        if cue is not None:
            item["intensity_cue"] = cue
        if rest is not None:
            item["tempo_or_rest"] = rest
        if notes:
            prev = (item.get("notes") or "").strip()
            item["notes"] = (prev + (" | " if prev and notes else "") + (notes or "")).strip()

    new_days: List[Dict[str, Any]] = []
    for d in days:
        d2 = {k: (v[:] if isinstance(v, list) else v) for k, v in d.items()}

        # Shoulder pain / bench alternatives
        if ("bench" in note and "shoulder" in note) or ("bench press" in note and "hurt" in note):
            for section in ("main", "accessory"):
                items = d2.get(section) or []
                for it in items:
                    if isinstance(it, dict) and isinstance(it.get("movement"), str) and "bench press" in it["movement"].lower():
                        _swap(it, "Dumbbell Floor Press", sets=3, reps=8, cue="RPE 6–8", rest="60–90s", notes="shoulder-friendly alternative")

        # Bodyweight instead of barbell squats
        if ("bodyweight" in note or "body weight" in note) and "squat" in note:
            for section in ("main", "accessory"):
                items = d2.get(section) or []
                for it in items:
                    if isinstance(it, dict) and isinstance(it.get("movement"), str):
                        mv = it["movement"].lower()
                        if "back squat" in mv or mv == "squat":
                            _swap(it, "Bulgarian Split Squat", sets=3, reps=10, cue="RPE 7–9", rest="60–90s", notes="progress load/ROM weekly")

        # Rep-range/intensity tweak example: high-rep lateral raises
        if "lateral" in note and "raise" in note and ("20" in note or "high rep" in note or "20+" in note or "20-30" in note):
            for section in ("main", "accessory"):
                items = d2.get(section) or []
                for it in items:
                    if isinstance(it, dict) and isinstance(it.get("movement"), str) and "lateral raise" in it["movement"].lower():
                        it["reps"] = 25
                        it["intensity_cue"] = "near failure in 20–30"
                        it["tempo_or_rest"] = it.get("tempo_or_rest") or "45–75s"
                        prev = (it.get("notes") or "").strip()
                        it["notes"] = (prev + (" | " if prev else "") + "use lighter load; controlled tempo").strip()

        new_days.append(d2)
    return new_days


def assess_tweak(goal: str, tweak_text: str) -> Dict[str, Any]:
    if not tweak_text or not tweak_text.strip():
        return {"verdict": "ok", "rationale": "No tweak provided.", "citations": [], "sources": []}
    hits = retrieve_snippets({"query": f"{goal}. Consider tweak: {tweak_text}", "evidence": "evidence", "top_k": 6})
    numbered = render_numbered_snippets([h.get("text", "") for h in hits])
    user = TWEAK_ASSESSOR_USER.format(goal=goal, tweak=tweak_text, snippets=numbered)
    schema = {
        "type": "object",
        "properties": {
            "verdict": {"type": "string", "enum": ["ok", "warn", "block"]},
            "rationale": {"type": "string"},
            "citations": {"type": "array", "items": {"type": "integer"}},
        },
        "required": ["verdict", "rationale", "citations"],
        "additionalProperties": False,
    }
    context = {
        "event": "tweak_assess",
        "goal": goal,
        "tweak": tweak_text,
        "snippet_ids": [h.get("id") for h in hits],
        "prompt_chars": len(user),
    }
    out = call_llm_json_object_with_log(f"{TWEAK_ASSESSOR_SYSTEM}\n\n{user}", schema, context) or {}
    out["sources"] = [{"n": i + 1, "chunk_id": h.get("id"), "doc_id": h.get("doc_id")} for i, h in enumerate(hits)]
    return out


def _canon_from_evidence_rules(inputs: InputsV11, hits: List[Dict[str, Any]]) -> Optional[List[Dict[str, Any]]]:
    """
    Build canonical week structure from extracted evidence prescriptions.
    Returns None if insufficient prescriptions found (triggers service unavailable).
    """
    dpw = max(2, min(6, int(getattr(inputs, "days_per_week", None) or 5)))
    goal = (inputs.goal or "hypertrophy").strip().lower()
    
    # Extract prescriptions from retrieved hits
    prescriptions = _extract_prescriptions_from_hits(hits, goal)
    
    if not prescriptions.get("found"):
        print(f"[Plan] No prescription data found for goal={goal}")
        return None
    
    main_presc = prescriptions.get("main", {})
    acc_presc = prescriptions.get("accessory", {})
    
    print(f"[Plan] main_presc keys: {list(main_presc.keys())}")
    print(f"[Plan] main_presc values: {main_presc}")
    
    # Validate minimum required fields per goal
    required_fields = _get_required_fields(goal)
    missing_fields = [f for f in required_fields if f not in main_presc]
    
    if missing_fields:
        print(f"[Plan] Missing required fields for {goal}: {missing_fields}")
        print(f"[Plan] Required: {required_fields}, Found: {list(main_presc.keys())}")
        return None
    
    print(f"[Plan] Validation passed! Building canonical week for {goal}")
    
    # Build canonical day structure based on goal
    def main_item(mv: str, muscle: str = "") -> Dict[str, Any]:
        item = {
            "movement": mv,
            "sets": _parse_range(main_presc.get("sets", "3")),
            "reps": _parse_range(main_presc.get("reps", "6")),
        }
        
        # Add goal-specific fields
        if goal == "hypertrophy":
            item["tempo"] = main_presc.get("tempo")
            item["rest"] = main_presc.get("rest")
            item["target_muscle"] = muscle or "Unknown"
            item["intensity_cue"] = "RPE 7-9"
        elif goal == "strength":
            item["weight_or_1rm_pct"] = main_presc.get("weight_or_1rm_pct")
            item["rpe_or_rir"] = main_presc.get("rpe_or_rir")
            item["rest"] = main_presc.get("rest")
            item["intensity_cue"] = "RPE 8-9"
        elif goal == "endurance":
            item["duration_or_reps"] = main_presc.get("duration_or_reps")
            item["intensity_zone"] = main_presc.get("intensity_zone")
            item["cadence_or_pace"] = main_presc.get("cadence_or_pace")
        elif goal == "fat_loss" or goal == "fatloss":
            item["work_interval"] = main_presc.get("work_interval")
            item["rest_interval"] = main_presc.get("rest_interval")
            item["rounds"] = main_presc.get("rounds")
            item["total_time"] = main_presc.get("total_time")
        
        return item
    
    def acc_item(mv: str, muscle: str = "") -> Dict[str, Any]:
        item = {
            "movement": mv,
            "sets": _parse_range(acc_presc.get("sets", "3")),
            "reps": _parse_range(acc_presc.get("reps", "12")),
        }
        
        # Add goal-specific fields for accessory
        if goal == "hypertrophy":
            item["tempo"] = acc_presc.get("tempo")
            item["rest"] = acc_presc.get("rest")
            item["target_muscle"] = muscle or "Unknown"
        elif goal == "strength":
            item["weight_or_1rm_pct"] = acc_presc.get("weight_or_1rm_pct")
            item["rpe_or_rir"] = acc_presc.get("rpe_or_rir")
            item["rest"] = acc_presc.get("rest")
        
        return item
    
    # Build canonical week (5-day split template)
    days = []
    if goal == "endurance":
        names = ["Mon", "Wed", "Fri", "Sun"][:dpw]
        for name in names:
            cardio = [main_item("Zone 2 Cardio", "Cardio")]
            days.append({"day": name, "day_name": name, "main": [], "accessory": [], "prehab": [], "cardio_notes": cardio})
        return days
    
    if goal == "fat_loss" or goal == "fatloss":
        template = [
            ("Mon", [main_item("Burpees", "Full Body")], [acc_item("Mountain Climbers", "Core"), acc_item("Jump Squats", "Legs")]),
            ("Wed", [main_item("Kettlebell Swings", "Full Body")], [acc_item("Box Jumps", "Legs")]),
            ("Fri", [main_item("Battle Ropes", "Upper Body")], [acc_item("High Knees", "Cardio")]),
        ]
        for name, main, acc in template[:dpw]:
            days.append({"day": name, "day_name": name, "main": main, "accessory": acc, "prehab": [], "cardio_notes": []})
        return days
    
    if goal == "strength":
        template = [
            ("Mon", [main_item("Back Squat", "Quads")], [acc_item("Leg Press", "Quads"), acc_item("Hamstring Curl", "Hamstrings")]),
            ("Tue", [main_item("Bench Press", "Chest")], [acc_item("DB Row", "Back"), acc_item("Triceps Pushdown", "Triceps")]),
            ("Thu", [main_item("Deadlift", "Posterior Chain")], [acc_item("Back Extension", "Lower Back"), acc_item("Plank", "Core")]),
            ("Fri", [main_item("Overhead Press", "Shoulders")], [acc_item("Lat Pulldown", "Lats"), acc_item("Lateral Raise", "Shoulders")]),
        ]
        for name, main, acc in template[:dpw]:
            days.append({"day": name, "day_name": name, "main": main, "accessory": acc, "prehab": [], "cardio_notes": []})
        return days
    
    # Hypertrophy default
    template = [
        ("Mon", [main_item("Bench Press", "Chest")], 
         [acc_item("Incline DB Press", "Upper Chest"), acc_item("Lateral Raise", "Shoulders"), acc_item("Triceps Pushdown", "Triceps")]),
        ("Tue", [main_item("Back Squat", "Quads")],
         [acc_item("Leg Press", "Quads"), acc_item("Leg Curl", "Hamstrings"), acc_item("Calf Raise", "Calves")]),
        ("Wed", [main_item("Barbell Row", "Back")],
         [acc_item("Lat Pulldown", "Lats"), acc_item("Rear Delt Fly", "Rear Delts"), acc_item("Biceps Curl", "Biceps")]),
        ("Thu", [main_item("Romanian Deadlift", "Hamstrings")],
         [acc_item("Split Squat", "Quads"), acc_item("Hamstring Curl", "Hamstrings"), acc_item("Back Extension", "Lower Back")]),
        ("Fri", [main_item("Overhead Press", "Shoulders")],
         [acc_item("DB Row", "Back"), acc_item("Face Pull", "Rear Delts"), acc_item("Cable Fly", "Chest")]),
    ]
    for name, main, acc in template[:dpw]:
        days.append({"day": name, "day_name": name, "main": main, "accessory": acc, "prehab": [], "cardio_notes": []})
    
    return days if days else None


def generate_plan_v11(inputs: InputsV11, tweak_note: Optional[str] = None) -> PlanV11:
    pal_value = PALMAP[inputs.pal_code]
    bmr = bmr_mifflin_st_jeor(inputs.sex, inputs.weight_kg, inputs.height_cm, inputs.age)
    tdee = tdee_from_bmr(bmr, pal_value)

    # Retrieval
    retrieval_query = _make_retrieval_query(inputs)
    try:
        snippet_hits = retrieve_snippets({"query": retrieval_query, "domains": getattr(inputs, "domain_filters", None), "evidence": "evidence", "top_k": 6})
    except Exception as e:
        print(f"[Plan] RAG disabled or failed: {e}")
        snippet_hits = []
    if snippet_hits:
        for i, s in enumerate(snippet_hits, 1):
            print(f"[Sources] [{i}] doc {s.get('doc_id')} · chunk {s.get('id')}")
    snippets_text = render_snippets_for_v11([s.get("text", "") for s in snippet_hits]) if snippet_hits else "- none"

    # Advisory LLM (optional)
    user_prompt = USER_TEMPLATE_V11.format(
        sex=inputs.sex, age=inputs.age, height_cm=inputs.height_cm, weight_kg=inputs.weight_kg,
        pal_value=pal_value, goal=inputs.goal, equipment=inputs.equipment or [],
        bmr=bmr, tdee=tdee, days_per_week=getattr(inputs, "days_per_week", None) or 5,
        snippets=snippets_text, tweak=tweak_note or "",
    )
    prompt = SYSTEM_PROMPT_V11 + "\n" + user_prompt
    schema = {"type": "object"}
    context = {
        "event": "plan_generate",
        "goal": inputs.goal,
        "days_per_week": getattr(inputs, "days_per_week", None) or 5,
        "retrieval_query": retrieval_query,
        "snippet_ids": [s.get("id") for s in (snippet_hits or [])],
        "prompt_chars": len(user_prompt),
    }
    compact: Dict[str, Any] = {}
    if USE_LLM_JSON:
        compact = call_llm_json_object_with_log(prompt, schema, context) or {}

    # No silent fallbacks: require evidence
    if not snippet_hits:
        print("[Plan] Unavailable: no RAG snippets; blocking plan render")
        return PlanV11(goal=inputs.goal, rows=[], week_count=0, extra={"snippets_count": 0, "retrieval_query": retrieval_query, "evidence_built": False, "reason": "no_snippets"})

    # Build canonical week from evidence (LLM compact if valid, else deterministic rules)
    canon_days: Optional[List[Dict[str, Any]]] = None
    if USE_LLM_JSON and (compact.get("canonical_week") or {}).get("days"):
        canon_days = (compact["canonical_week"]["days"])
    if canon_days is None:
        canon_days = _canon_from_evidence_rules(inputs, snippet_hits)

    if not canon_days:
        print("[Plan] Unavailable: no canonical week from evidence; blocking plan render")
        return PlanV11(goal=inputs.goal, rows=[], week_count=0, extra={
            "snippets_count": len(snippet_hits),
            "retrieval_query": retrieval_query,
            "evidence_built": False,
            "reason": "no_canonical_from_evidence",
        })

    # Apply tweaks and expand
    canon_days = _apply_tweak_rules(canon_days, tweak_note)
    week1_rows = _flatten_week("Week 1", canon_days)

    rotated_rows_all: List[Dict[str, Any]] = []
    rotated_rows_all += week1_rows
    week_notes = {2: "+1 rep per set", 3: "+2.5–5% load", 4: "deload 15–25%"}
    for wk in (2, 3, 4):
        rotated_days = _rotate_days(canon_days, shift=wk - 1)
        wk_rows_base = _flatten_week(f"Week {wk}", rotated_days)
        wk_rows = _variant_rows(wk_rows_base, week_notes.get(wk, ""), wk)
        rotated_rows_all += wk_rows

    rows_json = _sanitize_rows(rotated_rows_all)
    try:
        rows: List[PlanRowV11] = [PlanRowV11(**r) for r in rows_json]
    except ValidationError:
        repaired = _second_pass_repair(rows_json)
        rows = [PlanRowV11(**r) for r in repaired]

    priority = {"main": 0, "accessory": 1, "prehab": 2, "cardio_notes": 3}
    rows.sort(key=lambda r: (r.week_label, r.day, priority.get(r.block_type, 9)))

    plan = PlanV11(goal=inputs.goal, rows=rows, week_count=4)
    plan.extra = {
        "snippets_count": len(snippet_hits),
        "retrieval_query": retrieval_query,
        "evidence_built": True,
        "used_llm_for_rows": bool(USE_LLM_JSON and (compact.get("canonical_week") or {}).get("days")),
        "prescriptions_found": prescriptions.get("found", False) if 'prescriptions' in locals() else False,
    }
    return plan


# Helpers
def _sanitize_rows(rows_json: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    cleaned: List[Dict[str, Any]] = []
    per_day_seen: Dict[int, int] = {}
    for r in rows_json:
        day = _coerce_day(r.get("day", 1))
        per_day_seen[day] = per_day_seen.get(day, 0) + 1
        week_label = r.get("week_label") or "Week 1"
        day_name = r.get("day_name") or DAY_NAMES.get(day, f"Day {day}")
        block_type = r.get("block_type") or ("main" if per_day_seen[day] == 1 else "accessory")
        movement = r.get("movement") or "Unknown"
        cleaned.append({
            "week_label": week_label, "day": day, "day_name": day_name, "block_type": block_type,
            "movement": movement, "main_focus": r.get("main_focus"), "intensity_cue": r.get("intensity_cue"),
            "sets": _parse_int_lower_bound(r.get("sets")), "reps": _parse_int_lower_bound(r.get("reps")),
            "duration": r.get("duration"), "tempo_or_rest": r.get("tempo_or_rest"), "notes": r.get("notes"),
            # Pass through goal-specific fields
            "tempo": r.get("tempo"),
            "rest": r.get("rest"),
            "target_muscle": r.get("target_muscle"),
            "weight_or_1rm_pct": r.get("weight_or_1rm_pct"),
            "rpe_or_rir": r.get("rpe_or_rir"),
            "duration_or_reps": r.get("duration_or_reps"),
            "intensity_zone": r.get("intensity_zone"),
            "cadence_or_pace": r.get("cadence_or_pace"),
            "work_interval": r.get("work_interval"),
            "rest_interval": r.get("rest_interval"),
            "rounds": r.get("rounds"),
            "total_time": r.get("total_time"),
        })
    return cleaned


def _second_pass_repair(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    repaired: List[Dict[str, Any]] = []
    for r in rows:
        if not isinstance(r.get("day"), int) or r.get("movement") in (None, "", "Unknown"):
            r["movement"] = r.get("movement") or "Unknown"
        r["sets"] = r["sets"] if isinstance(r.get("sets"), int) else None
        r["reps"] = r["reps"] if isinstance(r.get("reps"), int) else None
        repaired.append(r)
    return repaired
