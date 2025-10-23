# # src/fitapp_core/exporters/pdf.py
# from __future__ import annotations

# from fpdf import FPDF
# from typing import Dict, List, Tuple

# DAY_ORDER = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

# def _safe_text(text: str) -> str:
#     return (text or "").replace("•","-").replace("—","-").replace("–","-").replace("×","x")

# def _cell_lines(day_rows: List[dict]) -> List[str]:
#     lines: List[str] = []
#     order = ["main", "accessory", "prehab", "cardio_notes"]
#     for section in order:
#         for r in (row for row in day_rows if row.get("block_type") == section):
#             sets = r.get("sets"); reps = r.get("reps"); dur = r.get("duration")
#             vol = f"{int(sets)}×{int(reps)}" if isinstance(sets, int) and isinstance(reps, int) else (dur or "")
#             base = f"{r.get('movement','')} — {vol}".strip(" —")
#             note = (r.get("notes") or "").strip()
#             lines.append(base if not note else f"{base} · {note}")
#     return lines or ["(no items)"]

# def _week_labels(rows: List[dict]) -> List[str]:
#     labs = sorted({r.get("week_label","Week 1") for r in rows},
#                   key=lambda w: int(str(w).split()[-1]) if str(w).startswith("Week") else 1)
#     if not labs:
#         labs = ["Week 1","Week 2","Week 3","Week 4"]
#     return labs

# def _group(rows: List[dict]) -> Dict[str, Dict[str, List[dict]]]:
#     out: Dict[str, Dict[str, List[dict]]] = {}
#     for r in rows:
#         wk = r.get("week_label","Week 1"); dn = r.get("day_name","")
#         out.setdefault(wk, {}).setdefault(dn, []).append(r)
#     return out

# def _multi_cell_measure(pdf: FPDF, w: float, line_h: float, text: str) -> float:
#     """
#     Render text in a multi_cell and return the height consumed.
#     Uses a save/restore cursor trick.
#     """
#     x, y = pdf.get_x(), pdf.get_y()
#     start_y = y
#     pdf.multi_cell(w, line_h, text, border=1)
#     end_y = pdf.get_y()
#     h = end_y - start_y
#     pdf.set_xy(x + w, y)  # place cursor at right edge of the cell for next column
#     return h

# def build_pdf_v11(plan: dict) -> bytes:
#     rows = plan.get("rows") or []
#     pdf = FPDF()
#     pdf.set_auto_page_break(auto=True, margin=15)
#     pdf.add_page()

#     # Header
#     pdf.set_font("Helvetica", size=16)
#     pdf.cell(0, 8, "Fitapp Workout Plan", new_x="LMARGIN", new_y="NEXT")
#     pdf.set_font("Helvetica", size=11)
#     pdf.cell(0, 6, _safe_text(f"Goal: {plan.get('goal','?')} - Weeks: {plan.get('week_count', 4)}"), new_x="LMARGIN", new_y="NEXT")
#     pdf.ln(2)

#     # Table layout
#     left_margin = pdf.l_margin
#     right_margin = pdf.r_margin
#     usable_w = pdf.w - left_margin - right_margin
#     day_col_w = 28
#     week_col_w = (usable_w - day_col_w) / 4.0  # 4 week columns
#     line_h = 5  # line height inside cells

#     week_labels = _week_labels(rows)
#     grouped = _group(rows)

#     # Header row
#     pdf.set_font("Helvetica", style="B", size=10)
#     pdf.set_x(left_margin)
#     pdf.cell(day_col_w, 8, "", border=1)  # corner cell
#     for wk in week_labels[:4]:
#         pdf.cell(week_col_w, 8, _safe_text(wk), border=1)
#     pdf.ln(8)

#     # Body rows by day
#     pdf.set_font("Helvetica", size=9)
#     for dn in DAY_ORDER:
#         # Left day label cell
#         pdf.set_x(left_margin)
#         pdf.cell(day_col_w, line_h, dn, border=1)
#         # Measure and render each week column; collect heights to compute row advance
#         col_heights: List[float] = []
#         start_y = pdf.get_y()
#         start_x = pdf.get_x()
#         # Render 4 columns, keeping cursor progression across columns via _multi_cell_measure
#         for wk in week_labels[:4]:
#             dr = grouped.get(wk, {}).get(dn, [])
#             # Build text for this cell
#             lines = _cell_lines(dr)
#             text = "\n".join(_safe_text(s)[:70] for s in lines[:10])  # clamp width and number of lines
#             h = _multi_cell_measure(pdf, week_col_w, line_h, text)
#             col_heights.append(h if h > 0 else line_h)
#         # After last column, the cursor is at the right edge; move to next line by the tallest column height
#         row_h = max(col_heights) if col_heights else line_h
#         # Set X to left margin and Y to start_y + row_h to start the next day row
#         pdf.set_xy(left_margin, start_y + row_h)

#     # Footer note (optional)
#     pdf.ln(4)
#     pdf.set_font("Helvetica", size=8)
#     pdf.cell(0, 5, "Notes: Progression guidance is included in each week cell.", new_x="LMARGIN", new_y="NEXT")

#     out = pdf.output(dest="S")
#     return bytes(out) if isinstance(out, (bytes, bytearray)) else out.encode("latin1")




# src/fitapp_core/exporters/pdf.py
from __future__ import annotations

from fpdf import FPDF
from typing import Dict, List, Tuple

DAY_ORDER = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

def _safe_text(text: str) -> str:
    return (text or "").replace("•","-").replace("—","-").replace("–","-").replace("×","x")

def _cell_lines(day_rows: List[dict], goal: str) -> List[str]:
    """
    Build display lines per row, showing goal-specific columns.
    - Hypertrophy: Movement | Sets×Reps | Tempo | Rest | Target Muscle
    - Strength: Movement | Sets×Reps | %1RM/Weight | RPE/RIR | Rest
    - Endurance: Movement | Duration | Intensity Zone | Cadence/Pace
    - Fat Loss: Movement | Work Interval | Rest Interval | Rounds
    """
    lines: List[str] = []
    order = ["main", "accessory", "prehab", "cardio_notes"]
    goal_lower = (goal or "hypertrophy").lower()
    
    for section in order:
        for r in (row for row in day_rows if row.get("block_type") == section):
            movement = r.get("movement", "")
            
            if goal_lower == "hypertrophy":
                sets = r.get("sets"); reps = r.get("reps")
                vol = f"{int(sets)}x{int(reps)}" if isinstance(sets, int) and isinstance(reps, int) else ""
                tempo = r.get("tempo") or r.get("tempo_or_rest", "")
                rest = r.get("rest", "")
                target = r.get("target_muscle", "")
                parts = [movement, vol, tempo, rest, target]
                line = " | ".join(p for p in parts if p)
                
            elif goal_lower == "strength":
                sets = r.get("sets"); reps = r.get("reps")
                vol = f"{int(sets)}x{int(reps)}" if isinstance(sets, int) and isinstance(reps, int) else ""
                weight = r.get("weight_or_1rm_pct", "")
                rpe = r.get("rpe_or_rir", "")
                rest = r.get("rest") or r.get("tempo_or_rest", "")
                parts = [movement, vol, weight, rpe, rest]
                line = " | ".join(p for p in parts if p)
                
            elif goal_lower == "endurance":
                dur = r.get("duration_or_reps") or r.get("duration", "")
                zone = r.get("intensity_zone", "")
                cadence = r.get("cadence_or_pace", "")
                parts = [movement, dur, zone, cadence]
                line = " | ".join(p for p in parts if p)
                
            elif goal_lower == "fat_loss":
                work = r.get("work_interval", "")
                rest_int = r.get("rest_interval", "")
                rounds = r.get("rounds")
                rounds_str = f"{int(rounds)} rounds" if isinstance(rounds, int) else ""
                parts = [movement, work, rest_int, rounds_str]
                line = " | ".join(p for p in parts if p)
                
            else:
                # Fallback: generic sets×reps
                sets = r.get("sets"); reps = r.get("reps"); dur = r.get("duration")
                vol = f"{int(sets)}x{int(reps)}" if isinstance(sets, int) and isinstance(reps, int) else (dur or "")
                line = f"{movement} | {vol}".strip(" | ")
            
            note = (r.get("notes") or "").strip()
            if note:
                line = f"{line} | {note}"
            
            lines.append(line)
    
    return lines or ["(no items)"]

def _week_labels(rows: List[dict]) -> List[str]:
    labs = sorted({r.get("week_label","Week 1") for r in rows},
                  key=lambda w: int(str(w).split()[-1]) if str(w).startswith("Week") else 1)
    if not labs:
        labs = ["Week 1","Week 2","Week 3","Week 4"]
    return labs

def _group(rows: List[dict]) -> Dict[str, Dict[str, List[dict]]]:
    out: Dict[str, Dict[str, List[dict]]] = {}
    for r in rows:
        wk = r.get("week_label","Week 1"); dn = r.get("day_name","")
        out.setdefault(wk, {}).setdefault(dn, []).append(r)
    return out

def _multi_cell_measure(pdf: FPDF, w: float, line_h: float, text: str) -> float:
    """
    Render text in a multi_cell and return the height consumed.
    Uses a save/restore cursor trick.
    """
    x, y = pdf.get_x(), pdf.get_y()
    start_y = y
    pdf.multi_cell(w, line_h, text, border=1)
    end_y = pdf.get_y()
    h = end_y - start_y
    pdf.set_xy(x + w, y)  # place cursor at right edge of the cell for next column
    return h

def build_pdf_v11(plan: dict) -> bytes:
    rows = plan.get("rows") or []
    goal = plan.get("goal", "hypertrophy")
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Header
    pdf.set_font("Helvetica", size=16)
    pdf.cell(0, 8, "Fitapp Workout Plan", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=11)
    pdf.cell(0, 6, _safe_text(f"Goal: {goal} - Weeks: {plan.get('week_count', 4)}"), new_x="LMARGIN", new_y="NEXT")
    
    # Add goal-specific column guide
    goal_lower = goal.lower()
    if goal_lower == "hypertrophy":
        col_guide = "Columns: Movement | Sets x Reps | Tempo | Rest | Target Muscle"
    elif goal_lower == "strength":
        col_guide = "Columns: Movement | Sets x Reps | %1RM/Weight | RPE/RIR | Rest"
    elif goal_lower == "endurance":
        col_guide = "Columns: Movement | Duration | Intensity Zone | Cadence/Pace"
    elif goal_lower == "fat_loss":
        col_guide = "Columns: Movement | Work Interval | Rest Interval | Rounds"
    else:
        col_guide = "Columns: Movement | Sets x Reps | Notes"
    
    pdf.set_font("Helvetica", size=9)
    pdf.cell(0, 5, _safe_text(col_guide), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # Table layout
    left_margin = pdf.l_margin
    right_margin = pdf.r_margin
    usable_w = pdf.w - left_margin - right_margin
    day_col_w = 28
    week_col_w = (usable_w - day_col_w) / 4.0  # 4 week columns
    line_h = 5  # line height inside cells

    week_labels = _week_labels(rows)
    grouped = _group(rows)

    # Header row
    pdf.set_font("Helvetica", style="B", size=10)
    pdf.set_x(left_margin)
    pdf.cell(day_col_w, 8, "", border=1)  # corner cell
    for wk in week_labels[:4]:
        pdf.cell(week_col_w, 8, _safe_text(wk), border=1)
    pdf.ln(8)

    # Body rows by day
    pdf.set_font("Helvetica", size=9)
    for dn in DAY_ORDER:
        # Left day label cell
        pdf.set_x(left_margin)
        pdf.cell(day_col_w, line_h, dn, border=1)
        # Measure and render each week column; collect heights to compute row advance
        col_heights: List[float] = []
        start_y = pdf.get_y()
        start_x = pdf.get_x()
        # Render 4 columns, keeping cursor progression across columns via _multi_cell_measure
        for wk in week_labels[:4]:
            dr = grouped.get(wk, {}).get(dn, [])
            # Build text for this cell using goal-aware formatting
            lines = _cell_lines(dr, goal)
            text = "\n".join(_safe_text(s)[:90] for s in lines[:10])  # clamp width and number of lines
            h = _multi_cell_measure(pdf, week_col_w, line_h, text)
            col_heights.append(h if h > 0 else line_h)
        # After last column, the cursor is at the right edge; move to next line by the tallest column height
        row_h = max(col_heights) if col_heights else line_h
        # Set X to left margin and Y to start_y + row_h to start the next day row
        pdf.set_xy(left_margin, start_y + row_h)

    # Footer note (optional)
    pdf.ln(4)
    pdf.set_font("Helvetica", size=8)
    pdf.cell(0, 5, "Notes: Progression guidance and goal-specific parameters are included in each cell.", new_x="LMARGIN", new_y="NEXT")

    out = pdf.output(dest="S")
    return bytes(out) if isinstance(out, (bytes, bytearray)) else out.encode("latin1")
