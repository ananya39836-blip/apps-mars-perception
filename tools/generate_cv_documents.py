"""Master Generator for APPS Computer Vision Master Prompt Specifications (Parts 48 to 52).
Generates 5 distinct technical volumes in both DOCX and PDF format (10 files total).
Each volume is engineered to contain exactly 37 pages of rigorous computer vision specifications.
Total Computer Vision specification: 185 pages.
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
from tools.cv_data_part1 import get_volume_48_data, get_volume_49_data
from tools.cv_data_part2 import get_volume_50_data, get_volume_51_data, get_volume_52_data


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
            self.drawString(54, 755, "AUTOMATED PLANETARY PERCEPTION SYSTEM (APPS) — COMPUTER VISION SPECIFICATION")
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
                "computer vision research prototype. Evaluated on vision transformers, neural radiance fields, 3D Gaussian splatting, "
                "dense stereo photogrammetry, visual-inertial odometry on Lie manifolds, neuromorphic event vision, and Sim-to-Real "
                "domain adaptation under severe Martian dust storm conditions. "
                "This document is an academic and systems engineering research prototype specification. "
                "It is NOT affiliated with, certified by, or sponsored by NASA or Caltech/JPL, and is not certified for spaceflight. "
                "Operational safety invariance: <b>PROTOTYPE_LOCK = True</b> and <b>navigation_ready = False</b> are compile-time locked."
            )
            story.append(make_callout_box_pdf(notice_text, styles, bg_hex="#FFF5F5", border_hex="#FEB2B2"))
            story.append(Spacer(1, 12))

            meta_text = (
                f"<b>Document ID:</b> {vol_data.get('doc_id', 'APPS-CV-SPEC')} &nbsp;|&nbsp; "
                f"<b>Part:</b> {vol_data['vol_num']} &nbsp;|&nbsp; "
                f"<b>Revision:</b> 6.0-PROTOTYPE &nbsp;|&nbsp; "
                f"<b>Release Gate:</b> READY-FOR-REVIEW<br/>"
                f"<b>Target Environment:</b> Extraterrestrial Planetary Surface (Mars / Moon / Titan / Asteroids)<br/>"
                f"<b>Security Classification:</b> UNRESTRICTED RESEARCH SPECIFICATION &nbsp;|&nbsp; "
                f"<b>Pages:</b> Exactly 37 Pages"
            )
            story.append(Paragraph(meta_text, styles['CoverMeta']))
            story.append(Spacer(1, 14))

            exec_box = [
                [Paragraph("<b>CORE SPECIFICATION SUMMARY</b>", styles['TableHead'])],
                [Paragraph(page.get('summary', 'Specifies autonomous planetary computer vision systems.'), styles['TableCell'])]
            ]
            t_exec = Table(exec_box, colWidths=[letter[0] - 108])
            t_exec.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A365D')),
                ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#F7FAFC')),
                ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E0')),
                ('TOPPADDING', (0,0), (-1,-1), 5),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                ('LEFTPADDING', (0,0), (-1,-1), 7),
                ('RIGHTPADDING', (0,0), (-1,-1), 7),
            ]))
            story.append(t_exec)

        elif page_num == 2:
            # Executive Summary & Architectural Overview
            story.append(Paragraph(page['title'], styles['H1']))
            story.append(HRFlowable(width="100%", thickness=0.75, color=colors.HexColor("#CBD5E0"), spaceAfter=6))
            story.append(Paragraph(page['lead'], styles['BodyBold']))
            story.append(Spacer(1, 4))

            if 'items' in page:
                for item in page['items']:
                    story.append(Paragraph(f"• <b>{item['heading']}:</b> {item['text']}", styles['Body']))
                story.append(Spacer(1, 4))

            if 'table' in page:
                t_data = [[Paragraph(c, styles['TableHead'] if r==0 else styles['TableCell']) for c in row] for r, row in enumerate(page['table'])]
                t = Table(t_data, colWidths=page.get('col_widths', [110, 150, 120, 124]))
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
            p_sub = doc.add_paragraph("AUTOMATED PLANETARY PERCEPTION SYSTEM (APPS)")
            p_sub.style.font.name = "Calibri"
            p_sub.runs[0].font.size = Pt(13)
            p_sub.runs[0].font.bold = True
            p_sub.runs[0].font.color.rgb = RGBColor(43, 108, 176)

            p_title = doc.add_paragraph(vol_data['title'])
            p_title.runs[0].font.size = Pt(20)
            p_title.runs[0].font.bold = True
            p_title.runs[0].font.color.rgb = RGBColor(26, 32, 44)

            p_sub2 = doc.add_paragraph(vol_data.get('subtitle', ''))
            p_sub2.runs[0].font.size = Pt(11)
            p_sub2.runs[0].font.bold = True
            p_sub2.runs[0].font.color.rgb = RGBColor(74, 85, 104)

            p_disc = doc.add_paragraph(
                "MANDATORY SCIENTIFIC & LEGAL NOTICE:\n"
                "This document specifies the research prototype architecture for APPS Computer Vision. "
                "Evaluated on vision transformers, 3D neural radiance fields, Gaussian splatting, stereo photogrammetry, "
                "visual-inertial odometry on Lie groups, neuromorphic event vision, and Sim-to-Real domain adaptation. "
                "Not affiliated with or certified by NASA or JPL; not flight qualified. "
                "Under compile-time PROTOTYPE_LOCK = True, navigation_ready is held strictly False."
            )
            p_disc.runs[0].font.italic = True
            p_disc.runs[0].font.size = Pt(9.5)
            p_disc.runs[0].font.color.rgb = RGBColor(116, 42, 42)

            doc.add_paragraph(
                f"Document ID: {vol_data.get('doc_id', 'APPS-CV-SPEC')} | Part: {vol_data['vol_num']} | Pages: 37\n"
                "Release Gate: READY-FOR-REVIEW | Classification: UNRESTRICTED RESEARCH SPECIFICATION"
            )
            p_sum = doc.add_paragraph(f"Executive Summary:\n{page.get('summary', '')}")
            p_sum.runs[0].font.size = Pt(10)

        elif page_num == 2:
            p_t = doc.add_paragraph(page['title'])
            p_t.runs[0].font.size = Pt(15)
            p_t.runs[0].font.bold = True
            p_lead = doc.add_paragraph(page['lead'])
            p_lead.runs[0].font.bold = True
            if 'items' in page:
                for item in page['items']:
                    doc.add_paragraph(f"{item['heading']}: {item['text']}", style='List Bullet')
            if 'table' in page:
                t = doc.add_table(rows=len(page['table']), cols=len(page['table'][0]))
                t.alignment = WD_TABLE_ALIGNMENT.CENTER
                for r_idx, row in enumerate(page['table']):
                    for c_idx, val in enumerate(row):
                        cell = t.cell(r_idx, c_idx)
                        cell.text = val
                        if r_idx == 0:
                            set_docx_cell_background(cell, "1A365D")
                            cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
                            cell.paragraphs[0].runs[0].font.bold = True

        elif page_num == 3:
            p_t = doc.add_paragraph(f"Table of Contents — Part {vol_data['vol_num']}")
            p_t.runs[0].font.size = Pt(15)
            p_t.runs[0].font.bold = True
            tech_pages = pages[3:33]
            for ch_idx in range(10):
                ch_p_start = 4 + ch_idx * 3
                ch_p_end = ch_p_start + 2
                p_item = tech_pages[ch_idx * 3]
                doc.add_paragraph(f"Chapter {vol_data['vol_num'] * 10 - 210 + ch_idx}: {p_item['title']} (pp. {ch_p_start}–{ch_p_end})", style='List Bullet')

        else:
            ch_str = f"Chapter {page['ch_num']}. " if 'ch_num' in page else ""
            p_t = doc.add_paragraph(f"{ch_str}{page['title']}")
            p_t.runs[0].font.size = Pt(13)
            p_t.runs[0].font.bold = True
            p_t.runs[0].font.color.rgb = RGBColor(26, 54, 93)

            if 'lead' in page:
                p_l = doc.add_paragraph(page['lead'])
                p_l.runs[0].font.bold = True
            if 'equations' in page:
                for eq in page['equations']:
                    if isinstance(eq, dict):
                        doc.add_paragraph(f"Equation ({eq['id']}): {eq['label']}", style='Heading 3')
                        eq_latex = eq['latex']
                        vars_str = eq.get('vars', '')
                    else:
                        doc.add_paragraph("Governing Invariant Formulation:", style='Heading 3')
                        eq_latex = str(eq)
                        vars_str = ""
                    p_eq_box = doc.add_paragraph(f"    [ {eq_latex} ]")
                    p_eq_box.runs[0].font.size = Pt(9)
                    p_eq_box.runs[0].font.bold = True
                    doc.add_paragraph(f"Where: {vars_str}")
            if 'items' in page:
                for item in page['items']:
                    doc.add_paragraph(f"{item['heading']}: {item['text']}", style='List Bullet')
            if 'table' in page:
                t = doc.add_table(rows=len(page['table']), cols=len(page['table'][0]))
                t.alignment = WD_TABLE_ALIGNMENT.CENTER
                for r_idx, row in enumerate(page['table']):
                    for c_idx, val in enumerate(row):
                        cell = t.cell(r_idx, c_idx)
                        cell.text = val
                        if r_idx == 0:
                            set_docx_cell_background(cell, "1A365D")
                            cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
                            cell.paragraphs[0].runs[0].font.bold = True
            if 'callout' in page:
                p_c = doc.add_paragraph(f"NOTE: {page['callout']}")
                p_c.runs[0].font.italic = True

        if page_num < 37:
            doc.add_page_break()

    doc.save(filename)
    print(f">> DOCX generated: {filename}")


def main():
    os.makedirs("docs/computer_vision", exist_ok=True)
    styles = get_styles()

    volumes = [
        ("Part_48_Vision_Transformers_Foundation_Models", get_volume_48_data()),
        ("Part_49_Neural_Radiance_Fields_Gaussian_Splatting", get_volume_49_data()),
        ("Part_50_Dense_Stereo_Photogrammetry_VIO", get_volume_50_data()),
        ("Part_51_Neuromorphic_Event_Based_Vision", get_volume_51_data()),
        ("Part_52_Domain_Adaptation_Atmospheric_Dehazing", get_volume_52_data()),
    ]

    print("=" * 80)
    print("GENERATING APPS COMPUTER VISION MASTER PROMPTS (5 VOLUMES, 37 PAGES EACH)")
    print("=" * 80)

    for tag, vol_data in volumes:
        print(f"\n>> Building Volume {vol_data['vol_num'] - 47} (Part {vol_data['vol_num']}): {vol_data['title']}")
        pdf_path = f"docs/computer_vision/APPS_Master_Prompt_{tag}.pdf"
        docx_path = f"docs/computer_vision/APPS_Master_Prompt_{tag}.docx"

        build_volume_pdf(pdf_path, vol_data, styles)
        build_volume_docx(docx_path, vol_data)

    print("\n" + "=" * 80)
    print("VERIFYING EXACT 37-PAGE ALLOCATION ACROSS ALL 5 COMPUTER VISION VOLUMES...")
    print("=" * 80)
    all_ok = True
    for tag, vol_data in volumes:
        pdf_path = f"docs/computer_vision/APPS_Master_Prompt_{tag}.pdf"
        docx_path = f"docs/computer_vision/APPS_Master_Prompt_{tag}.docx"
        with open(pdf_path, 'rb') as fp:
            content = fp.read()
            pages = len(re.findall(rb'/Type\s*/Page[^s]', content))
            docx_kb = os.path.getsize(docx_path) / 1024
            pdf_kb = os.path.getsize(pdf_path) / 1024
            status = "PASS" if pages == 37 else f"FAIL (got {pages})"
            if pages != 37:
                all_ok = False
            print(f"[{status}] Part {vol_data['vol_num']} | PDF: {pages} pages ({pdf_kb:.1f} KB) | DOCX: ({docx_kb:.1f} KB) -> {tag}")

    if all_ok:
        print("\n>> ALL 5 COMPUTER VISION VOLUMES VERIFIED: EXACTLY 37 PAGES EACH (185 PAGES TOTAL)!")
    else:
        print("\n>> WARNING: Some volumes deviated from 37 pages. Adjust spacers.")


if __name__ == "__main__":
    main()
