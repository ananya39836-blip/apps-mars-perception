"""Shared PDF Generation Engine for APPS Master Prompt Documents.
Ensures exact page budgets (exactly 40 pages per part) with authentic typography,
headers, footers, tables, and code listings.
"""
import os
import re
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas that writes running headers and 'Part X | page Y' footers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages):
        self.saveState()
        self.setFont('Helvetica', 8.5)
        self.setFillColor(colors.HexColor('#333333'))
        p = self._pageNumber
        part_name = getattr(self, 'part_title', 'APPS Master Prompt')

        if p > 1:
            self.drawString(54, 748, "Synthetic-data research prototype, not flight software.")
            self.setStrokeColor(colors.HexColor('#BBBBBB'))
            self.setLineWidth(0.5)
            self.line(54, 742, 558, 742)

        self.drawCentredString(306, 34, f"{part_name} | page {p}")
        self.restoreState()


def get_apps_styles():
    base = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=base['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        spaceAfter=12,
        textColor=colors.HexColor('#111111')
    )
    
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=base['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        spaceAfter=10,
        textColor=colors.HexColor('#222222')
    )
    
    chapter_h1 = ParagraphStyle(
        'ChapterH1',
        parent=base['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        spaceAfter=10,
        spaceBefore=4,
        textColor=colors.HexColor('#111111')
    )
    
    section_h2 = ParagraphStyle(
        'SectionH2',
        parent=base['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11.5,
        leading=15,
        spaceAfter=5,
        spaceBefore=8,
        textColor=colors.HexColor('#111111')
    )
    
    body = ParagraphStyle(
        'AppsBody',
        parent=base['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        spaceAfter=5,
        textColor=colors.HexColor('#222222')
    )
    
    bullet = ParagraphStyle(
        'AppsBullet',
        parent=base['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4,
        textColor=colors.HexColor('#222222')
    )
    
    code = ParagraphStyle(
        'AppsCode',
        parent=base['Normal'],
        fontName='Courier',
        fontSize=8.0,
        leading=10.5,
        textColor=colors.HexColor('#111111')
    )
    
    table_cell = ParagraphStyle(
        'TableCell',
        parent=base['Normal'],
        fontName='Helvetica',
        fontSize=8.0,
        leading=10.5,
        textColor=colors.HexColor('#222222')
    )
    
    table_header = ParagraphStyle(
        'TableHeader',
        parent=base['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.0,
        leading=10.5,
        textColor=colors.HexColor('#111111')
    )
    
    return {
        'title': title_style,
        'subtitle': subtitle_style,
        'chapter': chapter_h1,
        'section': section_h2,
        'body': body,
        'bullet': bullet,
        'code': code,
        'table_cell': table_cell,
        'table_header': table_header
    }
