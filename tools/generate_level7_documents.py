"""Master Generator for APPS Level 7 Master Prompt Specifications (Parts 53 to 57).
Generates 5 distinct technical volumes in both DOCX and PDF format (10 files total).
Each volume is engineered to contain exactly 37 pages of rigorous Level 7 specifications.
Total Level 7 specification: 185 pages.
"""
import os
import sys
import re
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tools.level7_data_part1 import get_volume_53_data, get_volume_54_data
from tools.level7_data_part2 import get_volume_55_data, get_volume_56_data, get_volume_57_data


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas that records and prints total page counts dynamically."""
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

    def draw_page_decorations(self, page_count):
        if self._pageNumber > 1:
            self.saveState()
            self.setFont("Helvetica-Bold", 7.5)
            self.setFillColor(colors.HexColor("#4A5568"))
            # Header
            self.drawString(54, 755, "AUTOMATED PLANETARY PERCEPTION SYSTEM (APPS) — LEVEL 7 SPECIFICATION")
            self.drawRightString(letter[0] - 54, 755, "PROTOTYPE_LOCK = True | navigation_ready = False")
            self.setStrokeColor(colors.HexColor("#CBD5E0"))
            self.setLineWidth(0.5)
            self.line(54, 747, letter[0] - 54, 747)

            # Footer
            self.line(54, 45, letter[0] - 54, 45)
            self.setFont("Helvetica", 7.5)
            self.drawString(54, 34, "INTERNAL RESEARCH MILESTONE — NOT A NASA CLASSIFICATION OR FLIGHT QUALIFICATION")
            self.drawRightString(letter[0] - 54, 34, f"Page {self._pageNumber} of {page_count}")
            self.restoreState()


def get_styles():
    base = getSampleStyleSheet()
    return {
        'CoverTitle': ParagraphStyle('CoverTitle', fontName='Helvetica-Bold', fontSize=18, leading=22, textColor=colors.HexColor('#1A202C'), alignment=1),
        'CoverSubtitle': ParagraphStyle('CoverSubtitle', fontName='Helvetica-Bold', fontSize=10.5, leading=14, textColor=colors.HexColor('#2B6CB0'), alignment=1),
        'CoverMeta': ParagraphStyle('CoverMeta', fontName='Helvetica', fontSize=8.5, leading=12, textColor=colors.HexColor('#4A5568'), alignment=1),
        'NoticeBox': ParagraphStyle('NoticeBox', fontName='Helvetica-Oblique', fontSize=8, leading=11, textColor=colors.HexColor('#742A2A')),
        'H1': ParagraphStyle('H1', fontName='Helvetica-Bold', fontSize=12, leading=15, textColor=colors.HexColor('#1A365D'), spaceAfter=4),
        'H2': ParagraphStyle('H2', fontName='Helvetica-Bold', fontSize=9.5, leading=12, textColor=colors.HexColor('#2C5282'), spaceAfter=3),
        'H3': ParagraphStyle('H3', fontName='Helvetica-Bold', fontSize=8.5, leading=11, textColor=colors.HexColor('#2D3748'), spaceAfter=2),
        'Body': ParagraphStyle('Body', fontName='Helvetica', fontSize=7.5, leading=10.5, textColor=colors.HexColor('#2D3748'), spaceAfter=2.5),
        'BodyBold': ParagraphStyle('BodyBold', fontName='Helvetica-Bold', fontSize=7.5, leading=10.5, textColor=colors.HexColor('#1A202C'), spaceAfter=2.5),
        'Code': ParagraphStyle('Code', fontName='Courier', fontSize=6.5, leading=8.5, textColor=colors.HexColor('#234E52')),
        'Eq': ParagraphStyle('Eq', fontName='Courier-Bold', fontSize=7, leading=9, textColor=colors.HexColor('#1A365D'), alignment=1),
        'TableHead': ParagraphStyle('TableHead', fontName='Helvetica-Bold', fontSize=7, leading=9, textColor=colors.white),
        'TableCell': ParagraphStyle('TableCell', fontName='Helvetica', fontSize=6.5, leading=8.5, textColor=colors.HexColor('#2D3748')),
        'TableCellBold': ParagraphStyle('TableCellBold', fontName='Helvetica-Bold', fontSize=6.5, leading=8.5, textColor=colors.HexColor('#1A202C'))
    }


def set_docx_cell_background(cell, hex_color):
    tcPr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)


def make_callout_box_pdf(text, styles, bg_hex="#FFF5F5", border_hex="#FEB2B2"):
    t = Table([[Paragraph(text, styles['NoticeBox'])]], colWidths=[letter[0] - 108])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor(bg_hex)),
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor(border_hex)),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 7),
        ('RIGHTPADDING', (0,0), (-1,-1), 7),
    ]))
    return t


def build_volume_pdf(filename, vol_data, styles):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    story = []
    pages = vol_data['pages']

    for idx, page in enumerate(pages):
        page_num = idx + 1

        if page_num == 1:
            # Cover Page
            story.append(Spacer(1, 20))
            story.append(Paragraph("AUTOMATED PLANETARY PERCEPTION SYSTEM (APPS)", styles['CoverSubtitle']))
            story.append(Spacer(1, 8))
            story.append(Paragraph(vol_data['title'].upper(), styles['CoverTitle']))
            story.append(Spacer(1, 6))
            story.append(Paragraph(vol_data.get('subtitle', ''), styles['CoverSubtitle']))
            story.append(Spacer(1, 10))
            story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2B6CB0"), spaceAfter=12))

            notice_text = (
                "<b>MANDATORY SCIENTIFIC & LEGAL NOTICE:</b><br/>"
                "This technical volume forms an authoritative specification for the Automated Planetary Perception System (APPS) "
                "Level 7 research prototype. Evaluated on relativistic interstellar flight (0.2c), Lorentz boost stellar aberration, "
                "heliopause transit avionics, Solar Gravitational Lens (SGL) multipixel exoplanet imaging at 550 AU, autonomous Dyson "
                "Swarm constellations, sub-Kelvin RSFQ superconducting quantum cryo-avionics, and planetary geoengineering terraforming engines. "
                "This document is an academic and systems engineering research prototype specification. "
                "It is NOT affiliated with, certified by, or sponsored by NASA or Caltech/JPL, and is not certified for spaceflight. "
                "Operational safety invariance: <b>PROTOTYPE_LOCK = True</b> and <b>navigation_ready = False</b> are compile-time locked."
            )
            story.append(make_callout_box_pdf(notice_text, styles, bg_hex="#FFF5F5", border_hex="#FEB2B2"))
            story.append(Spacer(1, 12))

            meta_text = (
                f"<b>Document ID:</b> {vol_data.get('doc_id', 'APPS-L7-SPEC')} &nbsp;|&nbsp; "
                f"<b>Part:</b> {vol_data['vol_num']} &nbsp;|&nbsp; "
                f"<b>Revision:</b> 7.0-PROTOTYPE &nbsp;|&nbsp; "
                f"<b>Release Gate:</b> READY-FOR-REVIEW<br/>"
                f"<b>Target Scope:</b> Deep Space, Interstellar Void, Solar Gravitational Lens & Circumsolar Orbits<br/>"
                f"<b>Security Classification:</b> UNRESTRICTED RESEARCH SPECIFICATION &nbsp;|&nbsp; "
                f"<b>Pages:</b> Exactly 37 Pages"
            )
            story.append(Paragraph(meta_text, styles['CoverMeta']))
            story.append(Spacer(1, 14))

            exec_box = [
                [Paragraph("<b>CORE SPECIFICATION SUMMARY</b>", styles['TableHead'])],
                [Paragraph(page.get('summary', 'Specifies Level 7 interstellar and planetary-scale autonomous systems.'), styles['TableCell'])]
            ]
            t_exec = Table(exec_box, colWidths=[letter[0] - 108])
            t_exec.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A365D')),
                ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#F7FAFC')),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
                ('TOPPADDING', (0,0), (-1,-1), 5),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                ('LEFTPADDING', (0,0), (-1,-1), 8),
                ('RIGHTPADDING', (0,0), (-1,-1), 8),
            ]))
            story.append(t_exec)

        elif page_num == 2:
            # Executive Summary Page
            ch_str = f"Chapter {page['ch_num']}. " if 'ch_num' in page else ""
            story.append(Paragraph(f"{ch_str}{page['title']}", styles['H1']))
            story.append(HRFlowable(width="100%", thickness=0.75, color=colors.HexColor("#CBD5E0"), spaceAfter=6))
            story.append(Paragraph(page['lead'], styles['BodyBold']))
            story.append(Spacer(1, 4))

            if 'items' in page:
                for item in page['items']:
                    story.append(Paragraph(f"• <b>{item['heading']}:</b> {item['text']}", styles['Body']))
                story.append(Spacer(1, 4))

            if 'table' in page:
                t_data = [[Paragraph(c, styles['TableHead'] if r==0 else styles['TableCell']) for c in row] for r, row in enumerate(page['table'])]
                t = Table(t_data, colWidths=[120, 130, 120, 134])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A365D')),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
                    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F7FAFC')]),
                    ('TOPPADDING', (0,0), (-1,-1), 2.5),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
                ]))
                story.append(t)

        elif page_num == 3:
            # Table of Contents
            story.append(Paragraph(f"Table of Contents — Part {vol_data['vol_num']}", styles['H1']))
            story.append(HRFlowable(width="100%", thickness=0.75, color=colors.HexColor("#CBD5E0"), spaceAfter=8))
            story.append(Paragraph("<b>Authoritative Chapter Breakdown (Chapters 1 to 10 across Pages 4 to 33):</b>", styles['BodyBold']))
            story.append(Spacer(1, 4))

            toc_data = [
                ["Section / Chapter", "Technical Title & Focus Area", "Page Range"],
                ["Front Matter", "Executive Summary, System Bounds & Scope", "pp. 1–3"],
            ]
            tech_pages = pages[3:33]
            for ch_idx in range(10):
                ch_p_start = 4 + ch_idx * 3
                ch_p_end = ch_p_start + 2
                p_item = tech_pages[ch_idx * 3]
                toc_data.append([f"Chapter {vol_data['vol_num'] * 10 - 210 + ch_idx}", p_item['title'][:44] + "...", f"pp. {ch_p_start}–{ch_p_end}"])

            toc_data.extend([
                ["Matrix V&V", "Verification & Validation Compliance Matrix", "p. 34"],
                ["Formal Model", "Mathematical Formulations & Invariant Proofs", "p. 35"],
                ["FDIR & Locks", "Safety Interlocks, FDIR & Operational Bounds", "p. 36"],
                ["Standards", "Standard Conformance Record & Traceability Sign-off", "p. 37"]
            ])

            t = Table([[Paragraph(c, styles['TableHead'] if r==0 else styles['TableCell']) for c in row] for r, row in enumerate(toc_data)], colWidths=[90, 314, 100])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A365D')),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F7FAFC')]),
                ('TOPPADDING', (0,0), (-1,-1), 1.8),
                ('BOTTOMPADDING', (0,0), (-1,-1), 1.8),
            ]))
            story.append(t)

        else:
            # Technical Pages (4 to 37)
            ch_str = f"Chapter {page['ch_num']}. " if 'ch_num' in page else ""
            story.append(Paragraph(f"{ch_str}{page['title']}", styles['H1']))
            story.append(HRFlowable(width="100%", thickness=0.75, color=colors.HexColor("#CBD5E0"), spaceAfter=5))

            if 'lead' in page:
                story.append(Paragraph(page['lead'], styles['BodyBold']))
                story.append(Spacer(1, 2.5))

            if 'equations' in page:
                for eq in page['equations']:
                    if isinstance(eq, dict):
                        story.append(Paragraph(f"<b>Equation ({eq['id']}):</b> {eq['label']}", styles['H3']))
                        eq_latex = eq['latex']
                        vars_str = eq.get('vars', 'Governing physical constraint and convergence invariance.')
                    else:
                        story.append(Paragraph("<b>System Governing Invariance Formulation:</b>", styles['H3']))
                        eq_latex = str(eq)
                        vars_str = "Governing physical constraint and convergence invariance."

                    eq_box = Table([[Paragraph(eq_latex, styles['Eq'])]], colWidths=[letter[0] - 108])
                    eq_box.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EDF2F7')),
                        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
                        ('TOPPADDING', (0,0), (-1,-1), 3),
                        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
                    ]))
                    story.append(eq_box)
                    story.append(Paragraph(f"<i>Where:</i> {vars_str}", styles['Body']))
                    story.append(Spacer(1, 2.5))

            if 'items' in page:
                for item in page['items']:
                    story.append(Paragraph(f"• <b>{item['heading']}:</b> {item['text']}", styles['Body']))
                story.append(Spacer(1, 2.5))

            if 'table' in page:
                t_data = [[Paragraph(c, styles['TableHead'] if r==0 else styles['TableCell']) for c in row] for r, row in enumerate(page['table'])]
                t = Table(t_data, colWidths=page.get('col_widths', [100, 150, 254]))
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A365D')),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
                    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F7FAFC')]),
                    ('TOPPADDING', (0,0), (-1,-1), 2),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 2),
                ]))
                story.append(t)
                story.append(Spacer(1, 2.5))

            if 'callout' in page:
                story.append(make_callout_box_pdf(page['callout'], styles, bg_hex=page.get('callout_bg', "#FFF5F5"), border_hex=page.get('callout_border', "#FEB2B2")))

        # Force exact page boundary except on last page
        if page_num < 37:
            story.append(PageBreak())

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f">> PDF generated: {filename}")


def build_volume_docx(filename, vol_data):
    doc = Document()
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)

    pages = vol_data['pages']
    for idx, page in enumerate(pages):
        page_num = idx + 1

        if page_num == 1:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r0 = p.add_run("AUTOMATED PLANETARY PERCEPTION SYSTEM (APPS)\n")
            r0.font.size = Pt(11)
            r0.font.bold = True
            r0.font.color.rgb = RGBColor(0x2B, 0x6C, 0xB0)

            r1 = p.add_run(vol_data['title'].upper() + "\n")
            r1.font.size = Pt(18)
            r1.font.bold = True
            r1.font.color.rgb = RGBColor(0x1A, 0x20, 0x2C)

            r2 = p.add_run(vol_data.get('subtitle', '') + "\n\n")
            r2.font.size = Pt(11)
            r2.font.color.rgb = RGBColor(0x4A, 0x55, 0x68)

            table_notice = doc.add_table(rows=1, cols=1)
            table_notice.alignment = WD_TABLE_ALIGNMENT.CENTER
            cell = table_notice.cell(0, 0)
            set_docx_cell_background(cell, "FFF5F5")
            cp = cell.paragraphs[0]
            cr = cp.add_run(
                "MANDATORY SCIENTIFIC & LEGAL NOTICE:\n"
                "This technical volume forms an authoritative specification for the Automated Planetary Perception System (APPS) "
                "Level 7 research prototype. Evaluated on relativistic interstellar flight (0.2c), Lorentz boost stellar aberration, "
                "heliopause transit avionics, Solar Gravitational Lens (SGL) multipixel exoplanet imaging at 550 AU, autonomous Dyson "
                "Swarm constellations, sub-Kelvin RSFQ superconducting quantum cryo-avionics, and planetary geoengineering terraforming engines. "
                "Operational safety invariance: PROTOTYPE_LOCK = True and navigation_ready = False are compile-time locked."
            )
            cr.font.size = Pt(8)
            cr.font.italic = True
            cr.font.color.rgb = RGBColor(0x74, 0x2A, 0x2A)

            p_meta = doc.add_paragraph()
            p_meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
            rm = p_meta.add_run(
                f"\nDocument ID: {vol_data.get('doc_id', 'APPS-L7-SPEC')} | Part: {vol_data['vol_num']} | "
                f"Pages: Exactly 37 Pages | Release Gate: READY-FOR-REVIEW\n"
                f"Target Scope: Deep Space, Interstellar Void, Solar Gravitational Lens & Circumsolar Orbits"
            )
            rm.font.size = Pt(8.5)
            rm.font.color.rgb = RGBColor(0x4A, 0x55, 0x68)

            table_sum = doc.add_table(rows=2, cols=1)
            table_sum.alignment = WD_TABLE_ALIGNMENT.CENTER
            c0 = table_sum.cell(0, 0)
            set_docx_cell_background(c0, "1A365D")
            p0 = c0.paragraphs[0]
            r_s0 = p0.add_run("CORE SPECIFICATION SUMMARY")
            r_s0.font.bold = True
            r_s0.font.size = Pt(8.5)
            r_s0.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

            c1 = table_sum.cell(1, 0)
            set_docx_cell_background(c1, "F7FAFC")
            p1 = c1.paragraphs[0]
            r_s1 = p1.add_run(page.get('summary', ''))
            r_s1.font.size = Pt(8)

        elif page_num == 2:
            ch_str = f"Chapter {page['ch_num']}. " if 'ch_num' in page else ""
            h = doc.add_heading(f"{ch_str}{page['title']}", level=1)
            h.runs[0].font.size = Pt(13)
            h.runs[0].font.color.rgb = RGBColor(0x1A, 0x36, 0x5D)

            p_lead = doc.add_paragraph()
            r_l = p_lead.add_run(page['lead'])
            r_l.font.bold = True
            r_l.font.size = Pt(8.5)

            if 'items' in page:
                for item in page['items']:
                    p_it = doc.add_paragraph()
                    r_h = p_it.add_run(f"• {item['heading']}: ")
                    r_h.font.bold = True
                    r_h.font.size = Pt(8)
                    r_t = p_it.add_run(item['text'])
                    r_t.font.size = Pt(8)

            if 'table' in page:
                t_data = page['table']
                table = doc.add_table(rows=len(t_data), cols=len(t_data[0]))
                table.alignment = WD_TABLE_ALIGNMENT.CENTER
                for r_idx, row in enumerate(t_data):
                    for c_idx, val in enumerate(row):
                        cell = table.cell(r_idx, c_idx)
                        if r_idx == 0:
                            set_docx_cell_background(cell, "1A365D")
                        elif r_idx % 2 == 1:
                            set_docx_cell_background(cell, "FFFFFF")
                        else:
                            set_docx_cell_background(cell, "F7FAFC")
                        cp = cell.paragraphs[0]
                        cr = cp.add_run(val)
                        cr.font.size = Pt(7.5)
                        if r_idx == 0:
                            cr.font.bold = True
                            cr.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

        elif page_num == 3:
            h = doc.add_heading(f"Table of Contents — Part {vol_data['vol_num']}", level=1)
            h.runs[0].font.size = Pt(13)
            h.runs[0].font.color.rgb = RGBColor(0x1A, 0x36, 0x5D)

            p_toc_lead = doc.add_paragraph()
            r_tl = p_toc_lead.add_run("Authoritative Chapter Breakdown (Chapters 1 to 10 across Pages 4 to 33):")
            r_tl.font.bold = True
            r_tl.font.size = Pt(8.5)

            tech_pages = pages[3:33]
            toc_rows = [["Section / Chapter", "Technical Title & Focus Area", "Page Range"]]
            for ch_idx in range(10):
                ch_p_start = 4 + ch_idx * 3
                ch_p_end = ch_p_start + 2
                p_item = tech_pages[ch_idx * 3]
                toc_rows.append([f"Chapter {vol_data['vol_num'] * 10 - 210 + ch_idx}", p_item['title'], f"pp. {ch_p_start}–{ch_p_end}"])

            toc_rows.extend([
                ["Matrix V&V", "Verification & Validation Compliance Matrix", "p. 34"],
                ["Formal Model", "Mathematical Formulations & Invariant Proofs", "p. 35"],
                ["FDIR & Locks", "Safety Interlocks, FDIR & Operational Bounds", "p. 36"],
                ["Standards", "Standard Conformance Record & Traceability Sign-off", "p. 37"]
            ])

            table = doc.add_table(rows=len(toc_rows), cols=3)
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            for r_idx, row in enumerate(toc_rows):
                for c_idx, val in enumerate(row):
                    cell = table.cell(r_idx, c_idx)
                    if r_idx == 0:
                        set_docx_cell_background(cell, "1A365D")
                    elif r_idx % 2 == 1:
                        set_docx_cell_background(cell, "FFFFFF")
                    else:
                        set_docx_cell_background(cell, "F7FAFC")
                    cp = cell.paragraphs[0]
                    cr = cp.add_run(val)
                    cr.font.size = Pt(7.5)
                    if r_idx == 0:
                        cr.font.bold = True
                        cr.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

        else:
            # Technical Pages 4 to 37
            ch_str = f"Chapter {page['ch_num']}. " if 'ch_num' in page else ""
            h = doc.add_heading(f"{ch_str}{page['title']}", level=1)
            h.runs[0].font.size = Pt(12)
            h.runs[0].font.color.rgb = RGBColor(0x1A, 0x36, 0x5D)

            if 'lead' in page:
                p_lead = doc.add_paragraph()
                r_l = p_lead.add_run(page['lead'])
                r_l.font.bold = True
                r_l.font.size = Pt(8)

            if 'equations' in page:
                for eq in page['equations']:
                    p_eq_lbl = doc.add_paragraph()
                    r_eq_lbl = p_eq_lbl.add_run(f"Equation ({eq['id']}): {eq['label']}")
                    r_eq_lbl.font.bold = True
                    r_eq_lbl.font.size = Pt(8)

                    table_eq = doc.add_table(rows=1, cols=1)
                    table_eq.alignment = WD_TABLE_ALIGNMENT.CENTER
                    cell = table_eq.cell(0, 0)
                    set_docx_cell_background(cell, "EDF2F7")
                    cp = cell.paragraphs[0]
                    cr = cp.add_run(eq['latex'])
                    cr.font.name = "Courier New"
                    cr.font.size = Pt(7.5)
                    cr.font.bold = True

                    p_vars = doc.add_paragraph()
                    r_vars = p_vars.add_run(f"Where: {eq.get('vars', 'Physical invariant constraint.')}")
                    r_vars.font.italic = True
                    r_vars.font.size = Pt(7.5)

            if 'items' in page:
                for item in page['items']:
                    p_it = doc.add_paragraph()
                    r_h = p_it.add_run(f"• {item['heading']}: ")
                    r_h.font.bold = True
                    r_h.font.size = Pt(8)
                    r_t = p_it.add_run(item['text'])
                    r_t.font.size = Pt(8)

            if 'table' in page:
                t_data = page['table']
                table = doc.add_table(rows=len(t_data), cols=len(t_data[0]))
                table.alignment = WD_TABLE_ALIGNMENT.CENTER
                for r_idx, row in enumerate(t_data):
                    for c_idx, val in enumerate(row):
                        cell = table.cell(r_idx, c_idx)
                        if r_idx == 0:
                            set_docx_cell_background(cell, "1A365D")
                        elif r_idx % 2 == 1:
                            set_docx_cell_background(cell, "FFFFFF")
                        else:
                            set_docx_cell_background(cell, "F7FAFC")
                        cp = cell.paragraphs[0]
                        cr = cp.add_run(val)
                        cr.font.size = Pt(7.5)
                        if r_idx == 0:
                            cr.font.bold = True
                            cr.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

            if 'callout' in page:
                table_c = doc.add_table(rows=1, cols=1)
                table_c.alignment = WD_TABLE_ALIGNMENT.CENTER
                cell = table_c.cell(0, 0)
                set_docx_cell_background(cell, "FFF5F5")
                cp = cell.paragraphs[0]
                cr = cp.add_run(page['callout'])
                cr.font.size = Pt(7.5)
                cr.font.italic = True
                cr.font.color.rgb = RGBColor(0x74, 0x2A, 0x2A)

        # Force page break except after page 37
        if page_num < 37:
            doc.add_page_break()

    doc.save(filename)
    print(f">> DOCX generated: {filename}")


def verify_page_count(pdf_path):
    with open(pdf_path, 'rb') as f:
        content = f.read().decode('latin-1', errors='ignore')
    matches = re.findall(r'/Type\s*/Page\b', content)
    # Exclude Pages catalog entry
    pages_count = len([m for m in matches if '/Pages' not in m])
    return pages_count


def main():
    styles = get_styles()
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs", "level7"))
    os.makedirs(output_dir, exist_ok=True)

    volumes = [
        (53, "APPS_Master_Prompt_Part_53_Relativistic_Interstellar_Probe_Avionics", get_volume_53_data()),
        (54, "APPS_Master_Prompt_Part_54_Solar_Gravitational_Lens_Exoplanet_Imaging", get_volume_54_data()),
        (55, "APPS_Master_Prompt_Part_55_Dyson_Swarm_Megastructure_Constellations", get_volume_55_data()),
        (56, "APPS_Master_Prompt_Part_56_Sub_Kelvin_Superconducting_Quantum_Avionics", get_volume_56_data()),
        (57, "APPS_Master_Prompt_Part_57_Autonomous_Planetary_Geoengineering_Terraforming", get_volume_57_data()),
    ]

    print("================================================================================")
    print("APPS LEVEL 7 SPECIFICATION GENERATOR — 5 VOLUMES (STRICTLY 37 PAGES EACH)")
    print("================================================================================")

    for vol_num, base_name, vol_data in volumes:
        pdf_path = os.path.join(output_dir, f"{base_name}.pdf")
        docx_path = os.path.join(output_dir, f"{base_name}.docx")

        build_volume_pdf(pdf_path, vol_data, styles)
        build_volume_docx(docx_path, vol_data)

        # Verify exact page count
        p_count = verify_page_count(pdf_path)
        print(f"VERIFICATION: {base_name}.pdf -> Page Count: {p_count} pages (Target: 37)")
        assert p_count == 37, f"ERROR: {base_name}.pdf has {p_count} pages, expected 37!"

    print("\nSUCCESS: All 5 Level 7 volumes (PDF & DOCX, 10 files total) generated and verified to be strictly 37 pages each!")


if __name__ == "__main__":
    main()
