"""
PDF Generator for FitApp workouts - v2.0
Generates a Monday–Sunday weekly plan table.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer, PageBreak
)
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from datetime import datetime
import io
import re


DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


class FitAppPDFGenerator:
    """Generate premium PDFs for FitApp weekly workout plans."""

    def __init__(self):
        self.color_primary = colors.HexColor("#FF5722")
        self.color_success = colors.HexColor("#4CAF50")
        self.color_warning = colors.HexColor("#FF9800")
        self.color_danger  = colors.HexColor("#F44336")
        self.color_text    = colors.HexColor("#0f0f0f")
        self.color_light   = colors.HexColor("#ffffff")
        self.color_border  = colors.HexColor("#FF5722")
        self.color_rest    = colors.HexColor("#888888")
        self.color_header  = colors.HexColor("#1a1a1a")

    # ── Public entry point ────────────────────────────────────────────────────
    def generate(self, workout: dict, filename: str = None) -> bytes:
        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
            title="ResFit Weekly Plan"
        )

        story = []
        story.extend(self._build_header(workout));      story.append(Spacer(1, 0.2 * inch))
        story.extend(self._build_metadata(workout));    story.append(Spacer(1, 0.3 * inch))
        story.extend(self._build_weekly_table(workout)); story.append(Spacer(1, 0.3 * inch))

        if workout.get("dietary_disclaimer"):
            story.extend(self._build_disclaimer(workout)); story.append(Spacer(1, 0.2 * inch))

        if workout.get("modification_history"):
            story.append(PageBreak())
            story.extend(self._build_modifications(workout)); story.append(Spacer(1, 0.3 * inch))

        story.append(PageBreak())
        story.extend(self._build_citations(workout))
        story.append(Spacer(1, 0.2 * inch))
        story.extend(self._build_footer(workout))

        doc.build(story)
        buf.seek(0)
        return buf.getvalue()

    # ── Header ────────────────────────────────────────────────────────────────
    def _build_header(self, workout):
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "Title", parent=styles["Heading1"],
            fontSize=28, textColor=self.color_primary,
            spaceAfter=6, alignment=TA_CENTER, fontName="Helvetica-Bold"
        )
        sub_style = ParagraphStyle(
            "Sub", parent=styles["Normal"],
            fontSize=11, textColor=self.color_text,
            spaceAfter=4, alignment=TA_CENTER
        )
        return [
            Paragraph("RESFIT", title_style),
            Paragraph("Science-Backed Weekly Training Plan", sub_style),
            Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y')}", sub_style),
        ]

    # ── Plan metadata ─────────────────────────────────────────────────────────
    def _build_metadata(self, workout):
        styles = getSampleStyleSheet()
        head_style = ParagraphStyle(
            "SH", parent=styles["Heading2"],
            fontSize=11, textColor=self.color_primary,
            spaceAfter=8, fontName="Helvetica-Bold"
        )
        goal      = workout.get("goal", "-").upper()
        split     = workout.get("split_type", "-")
        days      = str(workout.get("training_days_per_week", "-"))
        evidence  = workout.get("evidence_level", "HIGH")

        data = [
            ["GOAL", "SPLIT", "TRAINING DAYS", "EVIDENCE LEVEL"],
            [goal, split, days + " days / week", evidence]
        ]
        col_w = [1.5 * inch, 2.5 * inch, 1.5 * inch, 1.5 * inch]
        table = Table(data, colWidths=col_w)
        table.setStyle(TableStyle([
            ("BACKGROUND",  (0, 0), (-1, 0), self.color_primary),
            ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
            ("ALIGN",       (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",    (0, 0), (-1, 0), 9),
            ("BOTTOMPADDING",(0, 0), (-1, 0), 8),
            ("BACKGROUND",  (0, 1), (-1, -1), colors.white),
            ("TEXTCOLOR",   (0, 1), (-1, -1), self.color_text),
            ("FONTNAME",    (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE",    (0, 1), (-1, -1), 9),
            ("BOTTOMPADDING",(0, 1), (-1, -1), 8),
            ("GRID",        (0, 0), (-1, -1), 0.5, self.color_border),
        ]))
        story = [table]

        # Research validation summary
        if workout.get("research_validation"):
            val = workout["research_validation"]
            summary_style = ParagraphStyle(
                "Smry", parent=styles["Normal"],
                fontSize=8, textColor=self.color_text,
                spaceAfter=4, leftIndent=0.1 * inch,
                rightIndent=0.1 * inch, alignment=TA_JUSTIFY
            )
            story.append(Spacer(1, 0.15 * inch))
            story.append(Paragraph("<b>Research Validation:</b>", head_style))
            clean = self._strip_md(val.get("evidence_summary", ""))
            short = clean[:500] + ("..." if len(clean) > 500 else "")
            story.append(Paragraph(short, summary_style))

        # Weekly volume summary
        if workout.get("weekly_volume_summary"):
            story.append(Spacer(1, 0.15 * inch))
            story.append(Paragraph("<b>Weekly Volume Summary:</b>", head_style))
            vol   = workout["weekly_volume_summary"]
            items = [(k.title(), v) for k, v in vol.items() if k != "note"]
            if items:
                vol_data = [["Muscle Group", "Sets / Week"]] + items
                vol_table = Table(vol_data, colWidths=[2.5 * inch, 2.5 * inch])
                vol_table.setStyle(TableStyle([
                    ("BACKGROUND",  (0, 0), (-1, 0), self.color_header),
                    ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
                    ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE",    (0, 0), (-1, -1), 9),
                    ("ALIGN",       (0, 0), (-1, -1), "CENTER"),
                    ("GRID",        (0, 0), (-1, -1), 0.5, colors.lightgrey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9f9f9")]),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]))
                story.append(vol_table)
            if vol.get("note"):
                note_style = ParagraphStyle("N", parent=styles["Normal"], fontSize=7,
                                            textColor=colors.grey, spaceAfter=4, leftIndent=0.1*inch)
                story.append(Paragraph(vol["note"], note_style))

        return story

    # ── Monday–Sunday weekly table ────────────────────────────────────────────
    def _build_weekly_table(self, workout):
        styles  = getSampleStyleSheet()
        heading = ParagraphStyle(
            "WH", parent=styles["Heading2"],
            fontSize=12, textColor=self.color_primary,
            spaceAfter=10, fontName="Helvetica-Bold"
        )
        cell_style = ParagraphStyle(
            "Cell", parent=styles["Normal"],
            fontSize=8, textColor=self.color_text, leading=11
        )
        rest_style = ParagraphStyle(
            "Rest", parent=styles["Normal"],
            fontSize=8, textColor=self.color_rest,
            leading=11, alignment=TA_CENTER
        )

        story = [Paragraph("WEEKLY TRAINING PLAN", heading)]

        weekly_plan = workout.get("weekly_plan", {})

        # Determine column schema by goal
        goal = workout.get("goal", "")
        if goal in ("hypertrophy", "strength"):
            col_headers = ["DAY / SESSION", "EXERCISE", "SETS", "REPS", "REST", "RPE", "TEMPO / %1RM", "NOTES"]
            col_widths  = [1.1*inch, 1.3*inch, 0.45*inch, 0.45*inch, 0.55*inch, 0.45*inch, 0.85*inch, 1.3*inch]
        elif goal == "endurance":
            col_headers = ["DAY / SESSION", "EXERCISE", "DURATION", "INTENSITY", "ZONE", "RPE", "NOTES"]
            col_widths  = [1.1*inch, 1.4*inch, 0.75*inch, 1.0*inch, 0.65*inch, 0.45*inch, 1.6*inch]
        else:  # fatloss
            col_headers = ["DAY / SESSION", "EXERCISE", "ROUNDS", "WORK", "REST", "RPE", "NOTES"]
            col_widths  = [1.1*inch, 1.4*inch, 0.55*inch, 0.6*inch, 0.55*inch, 0.45*inch, 1.8*inch]

        table_data = [col_headers]

        for day in DAYS:
            session = weekly_plan.get(day, {})
            sname   = session.get("session_name", day.title())
            stype   = session.get("session_type", "")
            exercises = session.get("exercises", [])
            is_rest = stype == "rest" or not exercises

            day_label = Paragraph(f"<b>{day.upper()}</b><br/><font size='7' color='grey'>{sname}</font>", cell_style)

            if is_rest:
                rest_note = session.get("notes", "Active Recovery")
                rest_cell = [Paragraph(rest_note, rest_style)]
                empty     = [Paragraph("-", rest_style)]
                row_count = len(col_headers) - 1
                table_data.append([day_label] + [empty[0]] * row_count)
                # shade rest rows later via rowBackgrounds
                continue

            # Build one row per exercise (or station for circuits)
            rows_for_day = self._session_to_rows(session, goal, cell_style)
            for idx, row_cells in enumerate(rows_for_day):
                if idx == 0:
                    table_data.append([day_label] + row_cells)
                else:
                    table_data.append([Paragraph("", cell_style)] + row_cells)

        # Build table
        tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
        tbl.setStyle(self._weekly_table_style(len(table_data)))
        story.append(tbl)
        return story

    def _session_to_rows(self, session, goal, cell_style):
        """Convert exercises in a session into table row cells (without day label)."""
        rows = []
        for item in session.get("exercises", []):
            ex_type = item.get("type", "")
            notes   = self._strip_md(item.get("pro_notes", ""))[:80]

            # ── Circuit / HIIT ────────────────────────────────────────────────
            if "stations" in item:
                rounds = self._fmt(item.get("circuit_rounds"))
                for station in item.get("stations", []):
                    sname  = station.get("name") or station.get("exercise", "?")
                    work   = self._fmt(station.get("work_seconds"), "s")
                    rest   = self._fmt(station.get("rest_seconds"), "s")
                    rpe    = item.get("rpe", "-")
                    snotes = self._strip_md(station.get("pro_notes", notes))[:80]
                    if goal == "fatloss":
                        rows.append([
                            Paragraph(sname, cell_style),
                            Paragraph(rounds, cell_style),
                            Paragraph(work, cell_style),
                            Paragraph(rest, cell_style),
                            Paragraph(rpe, cell_style),
                            Paragraph(snotes, cell_style),
                        ])
                    else:
                        rows.append([
                            Paragraph(f"{sname} (circuit)", cell_style),
                            Paragraph("-", cell_style),
                            Paragraph(rounds + " rds", cell_style),
                            Paragraph(rest, cell_style),
                            Paragraph(rpe, cell_style),
                            Paragraph("-", cell_style),
                            Paragraph(snotes, cell_style),
                        ])
                continue

            name = item.get("name", "?")

            # ── Cardio duration-based ─────────────────────────────────────────
            if ex_type in ("cardio_aerobic", "cardio_steady_state", "cardio_vo2max"):
                if ex_type == "cardio_vo2max" and item.get("intervals"):
                    dur_str = f"{item['intervals']}×{item.get('interval_duration_min','?')} min"
                else:
                    dur_str = self._fmt(item.get("duration_minutes"), " min")
                intensity = item.get("intensity", "-")
                zone      = item.get("intensity_zone", "-")
                rpe       = item.get("rpe", "-")
                if goal == "endurance":
                    rows.append([
                        Paragraph(name, cell_style),
                        Paragraph(dur_str, cell_style),
                        Paragraph(intensity, cell_style),
                        Paragraph(zone, cell_style),
                        Paragraph(rpe, cell_style),
                        Paragraph(notes, cell_style),
                    ])
                else:
                    rows.append([
                        Paragraph(name, cell_style),
                        Paragraph("-", cell_style),
                        Paragraph(dur_str, cell_style),
                        Paragraph(intensity, cell_style),
                        Paragraph(rpe, cell_style),
                        Paragraph("-", cell_style),
                        Paragraph(notes, cell_style),
                    ])
                continue

            # ── Threshold circuit (endurance) ─────────────────────────────────
            if ex_type == "cardio_threshold" and "stations" not in item:
                rounds    = self._fmt(item.get("circuit_rounds"))
                intensity = item.get("intensity", "-")
                zone      = item.get("intensity_zone", "-")
                rpe       = item.get("rpe", "-")
                if goal == "endurance":
                    rows.append([
                        Paragraph(name, cell_style),
                        Paragraph(rounds + " rds", cell_style),
                        Paragraph(intensity, cell_style),
                        Paragraph(zone, cell_style),
                        Paragraph(rpe, cell_style),
                        Paragraph(notes, cell_style),
                    ])
                continue

            # ── Strength / Hypertrophy (sets × reps) ─────────────────────────
            sets   = self._fmt(item.get("sets"))
            reps   = self._fmt(item.get("reps"))
            rest   = self._fmt(item.get("rest_seconds"), "s")
            rpe    = item.get("rpe", "-")
            tempo  = item.get("tempo", "")
            pct    = item.get("percent_1rm", "")
            extra  = pct if pct else tempo
            mod    = " ✓" if item.get("modified") else ""

            rows.append([
                Paragraph(f"{name}{mod}", cell_style),
                Paragraph(sets, cell_style),
                Paragraph(reps, cell_style),
                Paragraph(rest, cell_style),
                Paragraph(rpe, cell_style),
                Paragraph(extra, cell_style),
                Paragraph(notes, cell_style),
            ])

        return rows if rows else [[Paragraph("-", cell_style)] * (7 if goal in ("hypertrophy","strength") else 6)]

    def _weekly_table_style(self, row_count):
        return TableStyle([
            # Header row
            ("BACKGROUND",   (0, 0), (-1, 0), self.color_primary),
            ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
            ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",     (0, 0), (-1, 0), 8),
            ("ALIGN",        (0, 0), (-1, 0), "CENTER"),
            ("BOTTOMPADDING",(0, 0), (-1, 0), 6),
            # Body
            ("FONTNAME",     (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE",     (0, 1), (-1, -1), 8),
            ("VALIGN",       (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, colors.HexColor("#fafafa")]),
            ("GRID",         (0, 0), (-1, -1), 0.4, colors.HexColor("#dddddd")),
            ("TOPPADDING",   (0, 1), (-1, -1), 5),
            ("BOTTOMPADDING",(0, 1), (-1, -1), 5),
            ("LEFTPADDING",  (0, 0), (-1, -1), 5),
        ])

    # ── Dietary disclaimer ────────────────────────────────────────────────────
    def _build_disclaimer(self, workout):
        styles = getSampleStyleSheet()
        disc_style = ParagraphStyle(
            "Disc", parent=styles["Normal"],
            fontSize=9, textColor=self.color_danger,
            spaceAfter=4, leftIndent=0.1 * inch, rightIndent=0.1 * inch,
            borderColor=self.color_danger, borderWidth=1, borderPadding=6,
            alignment=TA_JUSTIFY
        )
        return [Paragraph(f"⚠ {workout['dietary_disclaimer']}", disc_style)]

    # ── Modification history ──────────────────────────────────────────────────
    def _build_modifications(self, workout):
        styles = getSampleStyleSheet()
        head = ParagraphStyle("MH", parent=styles["Heading2"], fontSize=12,
                              textColor=self.color_primary, spaceAfter=12, fontName="Helvetica-Bold")
        title_s = ParagraphStyle("MT", parent=styles["Normal"], fontSize=10,
                                 textColor=self.color_text, spaceAfter=4, fontName="Helvetica-Bold")
        detail_s = ParagraphStyle("MD", parent=styles["Normal"], fontSize=9,
                                  textColor=self.color_text, spaceAfter=2, leftIndent=0.2 * inch)
        story = [Paragraph("EXERCISE MODIFICATIONS", head)]
        for mod in workout.get("modification_history", []):
            verdict = mod["verdict"].upper()
            orig    = mod["original_exercise"].upper()
            repl    = mod["replacement_exercise"].upper()
            story.append(Paragraph(f"{orig} → {repl}  [{verdict}]", title_s))
            story.append(Paragraph(f"<b>Reasoning:</b> {mod['reasoning']}", detail_s))
            story.append(Spacer(1, 0.1 * inch))
        return story

    # ── Citations ─────────────────────────────────────────────────────────────
    def _build_citations(self, workout):
        styles = getSampleStyleSheet()
        head = ParagraphStyle("CH", parent=styles["Heading2"], fontSize=12,
                              textColor=self.color_primary, spaceAfter=12, fontName="Helvetica-Bold")
        cite_s = ParagraphStyle("CI", parent=styles["Normal"], fontSize=8,
                                textColor=self.color_text, spaceAfter=6,
                                leftIndent=0.2 * inch, rightIndent=0.2 * inch, alignment=TA_JUSTIFY)
        story  = [Paragraph("RESEARCH CITATIONS & REFERENCES", head)]

        all_cites = []
        if workout.get("research_validation"):
            all_cites.extend(workout["research_validation"].get("citations", []))

        # Walk weekly_plan for per-exercise citations (modifications)
        for day_data in workout.get("weekly_plan", {}).values():
            for item in day_data.get("exercises", []):
                all_cites.extend(item.get("citations", []))
                for station in item.get("stations", []):
                    all_cites.extend(station.get("citations", []))

        for mod in workout.get("modification_history", []):
            all_cites.extend(mod.get("citations", []))

        seen, unique = set(), []
        for c in all_cites:
            if c not in seen:
                seen.add(c); unique.append(c)

        if unique:
            for i, c in enumerate(unique, 1):
                story.append(Paragraph(f"[{i}] {c}", cite_s))
        else:
            story.append(Paragraph("No citations available for this workout.", cite_s))

        return story

    # ── Footer ────────────────────────────────────────────────────────────────
    def _build_footer(self, workout):
        styles = getSampleStyleSheet()
        footer_s = ParagraphStyle("FT", parent=styles["Normal"], fontSize=8,
                                  textColor=colors.grey, spaceAfter=2, alignment=TA_CENTER)
        return [
            Paragraph(f"Workout ID: {workout.get('workout_id', '-')}", footer_s),
            Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | ResFit v2.0", footer_s),
            Paragraph("Science-backed weekly training plans with Hybrid RAG validation", footer_s),
        ]

    # ── Utilities ─────────────────────────────────────────────────────────────
    @staticmethod
    def _fmt(val, suffix=""):
        if val is None:
            return "-"
        if isinstance(val, list) and len(val) == 2:
            s = f"{val[0]}-{val[1]}"
        else:
            s = str(val)
        return s + suffix

    @staticmethod
    def _strip_md(text):
        if not text:
            return ""
        text = re.sub(r"[*_~`]", "", text)
        text = re.sub(r"#+\s", "", text)
        text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
        return text.strip()
