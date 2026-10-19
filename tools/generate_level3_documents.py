"""Master Generator for APPS Level 3 Master Prompt Specifications (Parts 13 to 17).
Generates 5 distinct technical volumes in both DOCX and PDF format.
Each volume is engineered to contain exactly 37 pages of rigorous engineering specifications.
"""
import os
import sys
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas


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
            self.drawString(54, 755, "AUTOMATED PLANETARY PERCEPTION SYSTEM (APPS) — LEVEL 3 SPECIFICATION")
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
        'CoverTitle': ParagraphStyle('CoverTitle', fontName='Helvetica-Bold', fontSize=20, leading=24, textColor=colors.HexColor('#1A202C'), alignment=1),
        'CoverSubtitle': ParagraphStyle('CoverSubtitle', fontName='Helvetica-Bold', fontSize=12, leading=16, textColor=colors.HexColor('#2B6CB0'), alignment=1),
        'CoverMeta': ParagraphStyle('CoverMeta', fontName='Helvetica', fontSize=8.5, leading=12, textColor=colors.HexColor('#4A5568'), alignment=1),
        'NoticeBox': ParagraphStyle('NoticeBox', fontName='Helvetica-Oblique', fontSize=8, leading=11, textColor=colors.HexColor('#742A2A')),
        'H1': ParagraphStyle('H1', fontName='Helvetica-Bold', fontSize=13, leading=16, textColor=colors.HexColor('#1A365D'), spaceAfter=4),
        'H2': ParagraphStyle('H2', fontName='Helvetica-Bold', fontSize=10, leading=13, textColor=colors.HexColor('#2C5282'), spaceAfter=3),
        'H3': ParagraphStyle('H3', fontName='Helvetica-Bold', fontSize=8.5, leading=11, textColor=colors.HexColor('#2D3748'), spaceAfter=2),
        'Body': ParagraphStyle('Body', fontName='Helvetica', fontSize=8, leading=11, textColor=colors.HexColor('#2D3748'), spaceAfter=3),
        'BodyBold': ParagraphStyle('BodyBold', fontName='Helvetica-Bold', fontSize=8, leading=11, textColor=colors.HexColor('#1A202C'), spaceAfter=3),
        'Code': ParagraphStyle('Code', fontName='Courier', fontSize=7, leading=9, textColor=colors.HexColor('#234E52')),
        'Eq': ParagraphStyle('Eq', fontName='Courier-Bold', fontSize=7.5, leading=9.5, textColor=colors.HexColor('#1A365D'), alignment=1),
        'TableHead': ParagraphStyle('TableHead', fontName='Helvetica-Bold', fontSize=7.5, leading=9.5, textColor=colors.white),
        'TableCell': ParagraphStyle('TableCell', fontName='Helvetica', fontSize=7, leading=9, textColor=colors.HexColor('#2D3748')),
        'TableCellBold': ParagraphStyle('TableCellBold', fontName='Helvetica-Bold', fontSize=7, leading=9, textColor=colors.HexColor('#1A202C'))
    }


def set_docx_cell_background(cell, hex_color):
    tcPr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)


def make_callout_box_pdf(text, styles, bg_hex="#FFF5F5", border_hex="#FEB2B2"):
    p = Paragraph(text, styles['NoticeBox'])
    t = Table([[p]], colWidths=[letter[0] - 108])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor(bg_hex)),
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor(border_hex)),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    return t


def build_volume_pdf(filename, vol_data, styles):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54, rightMargin=54,
        topMargin=54, bottomMargin=54
    )
    story = []
    
    pages = vol_data['pages']
    for idx, page in enumerate(pages):
        page_num = idx + 1
        
        if page_num == 1:
            # Cover Page
            story.append(Spacer(1, 40))
            story.append(Paragraph("AUTOMATED PLANETARY PERCEPTION SYSTEM", styles['CoverSubtitle']))
            story.append(Spacer(1, 10))
            story.append(Paragraph(vol_data['title'], styles['CoverTitle']))
            story.append(Spacer(1, 8))
            story.append(Paragraph(vol_data['subtitle'], styles['CoverSubtitle']))
            story.append(Spacer(1, 15))
            story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2B6CB0"), spaceAfter=15))
            
            disclaimer = (
                "<b>MANDATORY SCIENTIFIC & LEGAL NOTICE:</b><br/>"
                "This document specifies the research prototype architecture for <b>APPS Level 3</b>. "
                "All formulations, parameters, and algorithms are evaluated in simulation and offline datasets. "
                "This prototype is <b>not</b> affiliated with, endorsed by, or certified by NASA or JPL. "
                "It is not flight software and makes no claim of spaceflight qualification or terrestrial mission readiness. "
                "<code>PROTOTYPE_LOCK = True</code> is permanently enforced; <code>navigation_ready</code> remains strictly <code>False</code>."
            )
            story.append(make_callout_box_pdf(disclaimer, styles))
            story.append(Spacer(1, 25))
            
            meta_text = (
                f"<b>Document Identifier:</b> {vol_data['doc_id']}<br/>"
                f"<b>Milestone Tier:</b> Level 3 Research Prototype Specification (Volume {vol_data['vol_num']} of 5)<br/>"
                f"<b>Standard Mapping:</b> NASA SP-2016-6105 / NPR 7150.2B Class B Architecture Reference<br/>"
                f"<b>Release Status:</b> Draft Specification for Peer Review & Simulation Modeling<br/>"
                f"<b>Total Allocated Pages:</b> 37 Pages (Strict Volume Allocation)"
            )
            story.append(Paragraph(meta_text, styles['CoverMeta']))
            story.append(Spacer(1, 35))
            
            summary_box = (
                f"<b>VOLUME SUMMARY:</b> {page['summary']}"
            )
            story.append(make_callout_box_pdf(summary_box, styles, bg_hex="#EBF8FF", border_hex="#BEE3F8"))
            
        elif page_num == 2:
            # Executive Summary & Reading Rules
            story.append(Paragraph(f"Chapter {page['ch_num']}. {page['title']}", styles['H1']))
            story.append(HRFlowable(width="100%", thickness=0.75, color=colors.HexColor("#CBD5E0"), spaceAfter=8))
            story.append(Paragraph(f"<b>Context & Operational Boundaries:</b> {page['lead']}", styles['Body']))
            story.append(Spacer(1, 4))
            
            for item in page['items']:
                story.append(Paragraph(f"• <b>{item['heading']}:</b> {item['text']}", styles['Body']))
            story.append(Spacer(1, 6))
            
            if 'table' in page:
                t_data = [[Paragraph(c, styles['TableHead'] if r==0 else styles['TableCell']) for c in row] for r, row in enumerate(page['table'])]
                t = Table(t_data, colWidths=page.get('col_widths', [120, 160, 224]))
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A365D')),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
                    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F7FAFC')]),
                    ('TOPPADDING', (0,0), (-1,-1), 3),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 3),
                ]))
                story.append(t)
                
        elif page_num == 3:
            # Table of Contents
            story.append(Paragraph(f"Table of Contents — Volume {vol_data['vol_num']}", styles['H1']))
            story.append(HRFlowable(width="100%", thickness=0.75, color=colors.HexColor("#CBD5E0"), spaceAfter=8))
            story.append(Paragraph("This volume spans 37 dedicated chapters and technical specification pages as indexed below:", styles['Body']))
            story.append(Spacer(1, 4))
            
            toc_data = [["Page", "Chapter / Section", "Core Topic & Verification Objective"]]
            for p_idx, p_entry in enumerate(pages[3:], start=4):
                toc_data.append([f"Page {p_idx}", f"Ch. {p_entry.get('ch_num', p_idx + 215)}", p_entry['title'][:55]])
            
            # Show condensed TOC
            t_data = [[Paragraph(c, styles['TableHead'] if r==0 else styles['TableCell']) for c in row] for r, row in enumerate(toc_data[:34])]
            t = Table(t_data, colWidths=[55, 95, 354])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2C5282')),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F7FAFC')]),
                ('TOPPADDING', (0,0), (-1,-1), 2),
                ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ]))
            story.append(t)
            
        else:
            # Standard Technical Specification Page (Pages 4 to 37)
            ch_str = f"Chapter {page['ch_num']}. " if 'ch_num' in page else ""
            story.append(Paragraph(f"{ch_str}{page['title']}", styles['H1']))
            story.append(HRFlowable(width="100%", thickness=0.75, color=colors.HexColor("#CBD5E0"), spaceAfter=6))
            
            if 'lead' in page:
                story.append(Paragraph(page['lead'], styles['BodyBold']))
                story.append(Spacer(1, 3))
                
            if 'equations' in page:
                for eq in page['equations']:
                    story.append(Paragraph(f"<b>Equation ({eq['id']}):</b> {eq['label']}", styles['H3']))
                    eq_box = Table([[Paragraph(eq['latex'], styles['Eq'])]], colWidths=[letter[0] - 108])
                    eq_box.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EDF2F7')),
                        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
                        ('TOPPADDING', (0,0), (-1,-1), 4),
                        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                    ]))
                    story.append(eq_box)
                    story.append(Paragraph(f"<i>Where:</i> {eq['vars']}", styles['Body']))
                    story.append(Spacer(1, 3))
                    
            if 'items' in page:
                for item in page['items']:
                    story.append(Paragraph(f"• <b>{item['heading']}:</b> {item['text']}", styles['Body']))
                story.append(Spacer(1, 3))
                
            if 'table' in page:
                t_data = [[Paragraph(c, styles['TableHead'] if r==0 else styles['TableCell']) for c in row] for r, row in enumerate(page['table'])]
                t = Table(t_data, colWidths=page.get('col_widths', [100, 150, 254]))
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A365D')),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
                    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F7FAFC')]),
                    ('TOPPADDING', (0,0), (-1,-1), 2.5),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
                ]))
                story.append(t)
                story.append(Spacer(1, 3))
                
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
            p_title.runs[0].font.size = Pt(22)
            p_title.runs[0].font.bold = True
            p_title.runs[0].font.color.rgb = RGBColor(26, 32, 44)
            
            p_sub2 = doc.add_paragraph(vol_data['subtitle'])
            p_sub2.runs[0].font.size = Pt(12)
            p_sub2.runs[0].font.bold = True
            p_sub2.runs[0].font.color.rgb = RGBColor(74, 85, 104)
            
            p_disc = doc.add_paragraph(
                "MANDATORY SCIENTIFIC & LEGAL NOTICE:\n"
                "This document specifies the research prototype architecture for APPS Level 3. "
                "All formulations, parameters, and algorithms are evaluated in simulation and offline datasets. "
                "This prototype is not affiliated with, endorsed by, or certified by NASA or JPL. "
                "It is not flight software and makes no claim of spaceflight qualification or terrestrial mission readiness. "
                "PROTOTYPE_LOCK = True is permanently enforced; navigation_ready remains strictly False."
            )
            p_disc.runs[0].font.italic = True
            p_disc.runs[0].font.size = Pt(9.5)
            p_disc.runs[0].font.color.rgb = RGBColor(116, 42, 42)
            
            p_meta = doc.add_paragraph(
                f"Document Identifier: {vol_data['doc_id']}\n"
                f"Milestone Tier: Level 3 Research Prototype Specification (Volume {vol_data['vol_num']} of 5)\n"
                f"Standard Mapping: NASA SP-2016-6105 / NPR 7150.2B Class B Architecture Reference\n"
                f"Total Pages: 37 Pages"
            )
            p_meta.runs[0].font.size = Pt(9.5)
            
        elif page_num == 2:
            h = doc.add_heading(f"Chapter {page['ch_num']}. {page['title']}", level=1)
            h.runs[0].font.color.rgb = RGBColor(26, 54, 93)
            doc.add_paragraph(page['lead'])
            for item in page['items']:
                p = doc.add_paragraph(f"{item['heading']}: {item['text']}", style='List Bullet')
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
            h = doc.add_heading(f"Table of Contents — Volume {vol_data['vol_num']}", level=1)
            h.runs[0].font.color.rgb = RGBColor(26, 54, 93)
            doc.add_paragraph("Table of Contents for 37 dedicated chapters:")
            t = doc.add_table(rows=1, cols=3)
            t.alignment = WD_TABLE_ALIGNMENT.CENTER
            hdr = t.rows[0].cells
            hdr[0].text = "Page"
            hdr[1].text = "Chapter"
            hdr[2].text = "Topic"
            for c in hdr:
                set_docx_cell_background(c, "2C5282")
                c.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
                c.paragraphs[0].runs[0].font.bold = True
            for p_idx, p_entry in enumerate(pages[3:], start=4):
                row = t.add_row().cells
                row[0].text = f"Page {p_idx}"
                row[1].text = f"Ch. {p_entry.get('ch_num', p_idx + 215)}"
                row[2].text = p_entry['title']
        else:
            ch_str = f"Chapter {page['ch_num']}. " if 'ch_num' in page else ""
            h = doc.add_heading(f"{ch_str}{page['title']}", level=1)
            h.runs[0].font.color.rgb = RGBColor(26, 54, 93)
            if 'lead' in page:
                doc.add_paragraph(page['lead'])
            if 'equations' in page:
                for eq in page['equations']:
                    p_eq = doc.add_paragraph(f"Equation ({eq['id']}): {eq['label']}\n{eq['latex']}")
                    p_eq.runs[0].font.bold = True
                    doc.add_paragraph(f"Where: {eq['vars']}")
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
    import level3_data
    os.makedirs("docs/level3", exist_ok=True)
    styles = get_styles()
    
    volumes = [
        ("Part_13_Dynamics_Terramechanics", level3_data.get_volume_1_data()),
        ("Part_14_Active_Perception_Degradations", level3_data.get_volume_2_data()),
        ("Part_15_Factor_Graph_3D_Mapping", level3_data.get_volume_3_data()),
        ("Part_16_Kinodynamic_NMPC_Planning", level3_data.get_volume_4_data()),
        ("Part_17_Systems_Engineering_Verification", level3_data.get_volume_5_data()),
    ]
    
    print("=" * 75)
    print("GENERATING APPS LEVEL 3 MASTER SPECIFICATION VOLUMES (5 VOLUMES, 37 PAGES EACH)")
    print("=" * 75)
    
    for tag, vol_data in volumes:
        print(f"\n>> Building Volume {vol_data['vol_num']} (Part {vol_data['vol_num']+12}): {vol_data['title']}")
        pdf_path = f"docs/level3/APPS_Master_Prompt_{tag}.pdf"
        docx_path = f"docs/level3/APPS_Master_Prompt_{tag}.docx"
        
        build_volume_pdf(pdf_path, vol_data, styles)
        build_volume_docx(docx_path, vol_data)
        
    print("\n" + "=" * 75)
    print("ALL 5 LEVEL 3 SPECIFICATION VOLUMES (DOCX & PDF) SUCCESSFULLY GENERATED!")
    print("=" * 75)


if __name__ == "__main__":
    main()
