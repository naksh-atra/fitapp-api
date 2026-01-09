"""
PDF Generator for FitApp workouts
Premium, research-forward design
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from datetime import datetime
import io


class FitAppPDFGenerator:
    """Generate premium PDFs for FitApp workouts"""
    
    def __init__(self):
        # Color scheme - professional, research-forward
        self.color_primary = colors.HexColor("#2180a0")      # Teal
        self.color_success = colors.HexColor("#218054")      # Green
        self.color_warning = colors.HexColor("#a84b2f")      # Orange
        self.color_danger = colors.HexColor("#c01550")       # Red
        self.color_text = colors.HexColor("#1f2121")         # Dark
        self.color_light = colors.HexColor("#fcfcf9")        # Cream
        self.color_border = colors.HexColor("#5e5240")       # Brown
    
    def generate(self, workout: dict, filename: str = None) -> bytes:
        """
        Generate PDF from workout dict
        Returns PDF as bytes for download
        """
        
        # Create PDF in memory
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch,
            title="FitApp Workout"
        )
        
        # Build content
        story = []
        
        # Header
        story.extend(self._build_header(workout))
        story.append(Spacer(1, 0.2*inch))
        
        # Goal & metadata
        story.extend(self._build_metadata(workout))
        story.append(Spacer(1, 0.3*inch))
        
        # Exercises
        story.extend(self._build_exercises(workout))
        story.append(Spacer(1, 0.3*inch))
        
        # Modification history (if any)
        if workout.get('modification_history') and len(workout['modification_history']) > 0:
            story.append(PageBreak())
            story.extend(self._build_modifications(workout))
            story.append(Spacer(1, 0.3*inch))
        
        # Citations
        story.append(PageBreak())
        story.extend(self._build_citations(workout))
        
        # Footer
        story.append(Spacer(1, 0.2*inch))
        story.extend(self._build_footer(workout))
        
        # Build PDF
        doc.build(story)
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()
    
    def _build_header(self, workout):
        """Header section with title"""
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=28,
            textColor=self.color_primary,
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=self.color_text,
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica'
        )
        
        date_str = datetime.now().strftime("%B %d, %Y")
        
        return [
            Paragraph("💪 FITAPP", title_style),
            Paragraph("Science-Backed Workout Plan", subtitle_style),
            Paragraph(f"Generated: {date_str}", subtitle_style),
        ]
    
    def _build_metadata(self, workout):
        """Goal and basic info"""
        styles = getSampleStyleSheet()
        
        heading_style = ParagraphStyle(
            'SectionHead',
            parent=styles['Heading2'],
            fontSize=11,
            textColor=self.color_primary,
            spaceAfter=8,
            fontName='Helvetica-Bold'
        )
        
        info_style = ParagraphStyle(
            'Info',
            parent=styles['Normal'],
            fontSize=10,
            textColor=self.color_text,
            spaceAfter=4
        )
        
        goal = workout['goal'].upper()
        num_exercises = len(workout['exercises'])
        duration = workout.get('total_duration_minutes', 60)
        evidence = workout.get('evidence_level', 'HIGH')
        
        data = [
            ['GOAL', 'EXERCISES', 'DURATION', 'EVIDENCE'],
            [goal, str(num_exercises), f'{duration} min', evidence]
        ]
        
        table = Table(data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.color_primary),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.color_light),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), self.color_text),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, self.color_border),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.white]),
        ]))
        
        return [table]
    
    def _build_exercises(self, workout):
        """Exercise details"""
        styles = getSampleStyleSheet()
        
        heading_style = ParagraphStyle(
            'SectionHead',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=self.color_primary,
            spaceAfter=12,
            fontName='Helvetica-Bold'
        )
        
        exercise_title_style = ParagraphStyle(
            'ExerciseTitle',
            parent=styles['Heading3'],
            fontSize=11,
            textColor=self.color_text,
            spaceAfter=4,
            fontName='Helvetica-Bold'
        )
        
        exercise_detail_style = ParagraphStyle(
            'ExerciseDetail',
            parent=styles['Normal'],
            fontSize=9,
            textColor=self.color_text,
            spaceAfter=2,
            leftIndent=0.2*inch
        )
        
        story = [Paragraph("EXERCISE PRESCRIPTION", heading_style)]
        
        for i, exercise in enumerate(workout['exercises'], 1):
            # Exercise title with modification indicator
            title = exercise['name'].upper()
            if exercise.get('modified'):
                title += " ✓ (MODIFIED)"
            
            story.append(Paragraph(f"{i}. {title}", exercise_title_style))
            
            # Details
            ex_type = exercise['type'].title()
            sets = self._format_range(exercise['sets'])
            reps = self._format_range(exercise['reps'])
            tempo = exercise['tempo']
            rest = self._format_range(exercise['rest_seconds'])
            
            details = f"<b>Type:</b> {ex_type} | <b>Sets:</b> {sets} | <b>Reps:</b> {reps} | <b>Tempo:</b> {tempo}"
            story.append(Paragraph(details, exercise_detail_style))
            
            rest_detail = f"<b>Rest:</b> {rest}s"
            if 'rpe' in exercise:
                rest_detail += f" | <b>RPE:</b> {exercise['rpe']}"
            
            story.append(Paragraph(rest_detail, exercise_detail_style))
            
            # Modification note if applicable
            if exercise.get('modified') and exercise.get('modification_note'):
                story.append(Paragraph(
                    f"<i>Note: {exercise['modification_note']}</i>",
                    exercise_detail_style
                ))
            
            story.append(Spacer(1, 0.15*inch))
        
        return story
    
    def _build_modifications(self, workout):
        """Modification history"""
        styles = getSampleStyleSheet()
        
        heading_style = ParagraphStyle(
            'SectionHead',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=self.color_primary,
            spaceAfter=12,
            fontName='Helvetica-Bold'
        )
        
        mod_title_style = ParagraphStyle(
            'ModTitle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=self.color_text,
            spaceAfter=4,
            fontName='Helvetica-Bold'
        )
        
        mod_detail_style = ParagraphStyle(
            'ModDetail',
            parent=styles['Normal'],
            fontSize=9,
            textColor=self.color_text,
            spaceAfter=2,
            leftIndent=0.2*inch
        )
        
        story = [Paragraph("EXERCISE MODIFICATIONS", heading_style)]
        
        for i, mod in enumerate(workout['modification_history'], 1):
            verdict = mod['verdict'].upper()
            
            # Verdict color
            if verdict == 'GREEN':
                verdict_color = f'<font color="{self.color_success.hexValue()}"><b>{verdict}</b></font>'
            elif verdict == 'YELLOW':
                verdict_color = f'<font color="{self.color_warning.hexValue()}"><b>{verdict}</b></font>'
            else:
                verdict_color = f'<font color="{self.color_danger.hexValue()}"><b>{verdict}</b></font>'
            
            orig = mod['original_exercise'].upper()
            repl = mod['replacement_exercise'].upper()
            
            title = f"{orig} → {repl} [{verdict_color}]"
            story.append(Paragraph(title, mod_title_style))
            
            story.append(Paragraph(
                f"<b>Verdict:</b> {verdict}",
                mod_detail_style
            ))
            
            story.append(Paragraph(
                f"<b>Reasoning:</b> {mod['reasoning']}",
                mod_detail_style
            ))
            
            if mod.get('warning'):
                story.append(Paragraph(
                    f"<b>⚠️ Note:</b> {mod['warning']}",
                    mod_detail_style
                ))
            
            story.append(Spacer(1, 0.15*inch))
        
        return story
    
    def _build_citations(self, workout):
        """Citations and references"""
        styles = getSampleStyleSheet()
        
        heading_style = ParagraphStyle(
            'SectionHead',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=self.color_primary,
            spaceAfter=12,
            fontName='Helvetica-Bold'
        )
        
        citation_style = ParagraphStyle(
            'Citation',
            parent=styles['Normal'],
            fontSize=9,
            textColor=self.color_text,
            spaceAfter=8,
            leftIndent=0.2*inch,
            rightIndent=0.2*inch,
            alignment=TA_JUSTIFY
        )
        
        story = [Paragraph("RESEARCH CITATIONS & REFERENCES", heading_style)]
        
        # Collect all citations
        all_citations = set()
        
        # From exercises
        for ex in workout['exercises']:
            if 'citations' in ex:
                all_citations.update(ex['citations'])
        
        # From modifications
        if 'modification_history' in workout:
            for mod in workout['modification_history']:
                if 'citations' in mod:
                    all_citations.update(mod['citations'])
        
        # Display citations
        for i, citation in enumerate(sorted(all_citations), 1):
            story.append(Paragraph(
                f"[{i}] {citation}",
                citation_style
            ))
        
        return story
    
    def _build_footer(self, workout):
        """Footer with metadata"""
        styles = getSampleStyleSheet()
        
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            spaceAfter=2,
            alignment=TA_CENTER
        )
        
        workout_id = workout['workout_id']
        generated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return [
            Paragraph(f"Workout ID: {workout_id}", footer_style),
            Paragraph(f"Generated: {generated_date} | FitApp v1.0", footer_style),
            Paragraph("Science-backed training plans with research validation", footer_style),
        ]
    
    @staticmethod
    def _format_range(value):
        """Format range values like [4, 6] to '4-6'"""
        if isinstance(value, list) and len(value) == 2:
            return f"{value[0]}-{value[1]}"
        return str(value)
