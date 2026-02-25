"""
PDF and DOCX generation from a DocumentModel.
"""

from __future__ import annotations
import io
import datetime
import logging
from typing import Literal

from md_parser import DocumentModel, TableNode, ListNode, CodeBlock

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# DOCX Generation
# ─────────────────────────────────────────────────────────────────────────────

def generate_docx(model: DocumentModel) -> bytes:
    """Generate a professional DOCX from DocumentModel."""
    from docx import Document
    from docx.shared import Pt, Cm, RGBColor, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement

    doc = Document()

    # ── Margins ──
    for section in doc.sections:
        section.top_margin    = Cm(2.54)
        section.bottom_margin = Cm(2.54)
        section.left_margin   = Cm(2.54)
        section.right_margin  = Cm(2.54)

    # ── Helper: set paragraph font ──
    def _font(paragraph, size=11, bold=False, color=None, italic=False):
        for run in paragraph.runs:
            run.font.name = "Calibri"
            run.font.size = Pt(size)
            run.bold  = bold
            run.italic = italic
            if color:
                run.font.color.rgb = RGBColor(*color)

    # ── Cover ──
    cover_title = doc.add_paragraph()
    cover_title.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = cover_title.add_run(model.title)
    run.bold = True
    run.font.name = "Calibri"
    run.font.size = Pt(28)
    run.font.color.rgb = RGBColor(17, 24, 39)

    meta = doc.add_paragraph()
    gen_date = datetime.datetime.utcnow().strftime("%B %d, %Y")
    run = meta.add_run(f"Technical Report  •  Generated {gen_date}")
    run.font.name = "Calibri"
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(107, 114, 128)

    doc.add_paragraph()  # spacer

    # ── Sections ──
    heading_sizes = {1: 16, 2: 13, 3: 11, 4: 10, 5: 9, 6: 9}
    heading_colors = {
        1: (17, 24, 39),
        2: (31, 41, 55),
        3: (55, 65, 81),
        4: (75, 85, 99),
        5: (75, 85, 99),
        6: (75, 85, 99),
    }

    for sec in model.sections:
        if sec.heading:
            lvl = max(1, min(sec.level, 6))
            h = doc.add_paragraph()
            run = h.add_run(sec.heading)
            run.bold = True
            run.font.name = "Calibri"
            run.font.size = Pt(heading_sizes.get(lvl, 11))
            run.font.color.rgb = RGBColor(*heading_colors.get(lvl, (17, 24, 39)))
            h.paragraph_format.space_before = Pt(12)
            h.paragraph_format.space_after  = Pt(4)

        for para_text in sec.content:
            p = doc.add_paragraph()
            run = p.add_run(para_text)
            run.font.name = "Calibri"
            run.font.size = Pt(10.5)
            p.paragraph_format.space_after = Pt(6)

        for tbl in sec.tables:
            if not tbl.headers and not tbl.rows:
                continue
            total_rows = (1 if tbl.headers else 0) + len(tbl.rows)
            cols = max(len(tbl.headers), max((len(r) for r in tbl.rows), default=0))
            if cols == 0:
                continue
            t = doc.add_table(rows=total_rows, cols=cols)
            t.style = "Table Grid"
            row_idx = 0
            if tbl.headers:
                for ci, h_text in enumerate(tbl.headers):
                    cell = t.rows[0].cells[ci]
                    cell.text = h_text
                    for run in cell.paragraphs[0].runs:
                        run.bold = True
                        run.font.color.rgb = RGBColor(255, 255, 255)
                    # Header background
                    shading = OxmlElement("w:shd")
                    shading.set(qn("w:fill"), "4F46E5")
                    shading.set(qn("w:color"), "auto")
                    shading.set(qn("w:val"), "clear")
                    cell._tc.get_or_add_tcPr().append(shading)
                row_idx = 1
            for row_data in tbl.rows:
                for ci, cell_text in enumerate(row_data):
                    if ci < cols:
                        t.rows[row_idx].cells[ci].text = cell_text
                row_idx += 1
            doc.add_paragraph()  # spacer

        for lst in sec.lists:
            style = "List Number" if lst.ordered else "List Bullet"
            for item in lst.items:
                p = doc.add_paragraph(item, style=style)
                p.runs[0].font.name = "Calibri"
                p.runs[0].font.size = Pt(10.5)

        for cb in sec.code_blocks:
            lang_hint = f"[{cb.language}]  " if cb.language else ""
            p = doc.add_paragraph()
            run = p.add_run(lang_hint + cb.code)
            run.font.name = "Cascadia Code"
            run.font.size = Pt(8.5)
            run.font.color.rgb = RGBColor(31, 41, 55)  # Dark grayish blue
            p.paragraph_format.left_indent = Pt(18)
            # Light gray background via shading
            pPr = p._p.get_or_add_pPr()
            shading = OxmlElement("w:shd")
            shading.set(qn("w:fill"), "F3F4F6")
            shading.set(qn("w:color"), "auto")
            shading.set(qn("w:val"), "clear")
            pPr.append(shading)
            doc.add_paragraph()

    # ── Footer via core_properties ──
    doc.core_properties.description = f"Generated by ReadmeForge on {gen_date}"
    doc.core_properties.subject = "Technical Report"

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.read()


# ─────────────────────────────────────────────────────────────────────────────
# PDF Generation
# ─────────────────────────────────────────────────────────────────────────────

def generate_pdf(html_content: str) -> bytes:
    """Generate PDF from HTML using reportlab as fallback."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm, mm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        Preformatted, HRFlowable, KeepTogether,
    )
    from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
    import re

    # Try WeasyPrint first (better HTML→PDF), fallback to manual reportlab
    try:
        from weasyprint import HTML as WH
        pdf_bytes = WH(string=html_content).write_pdf()
        return pdf_bytes
    except ImportError:
        pass

    # ── Fallback: parse model from html and use reportlab ──
    # Parse out the model from what we have available
    from bs4 import BeautifulSoup
    import html as html_mod

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=cm * 2.54,
        leftMargin=cm * 2.54,
        topMargin=cm * 2.54,
        bottomMargin=cm * 2.54,
    )

    styles = getSampleStyleSheet()
    accent = colors.HexColor("#4F46E5")
    dark   = colors.HexColor("#111827")
    gray   = colors.HexColor("#374151")
    light  = colors.HexColor("#6B7280")

    style_title   = ParagraphStyle("DocTitle",   fontSize=24, leading=30, textColor=dark, fontName="Helvetica-Bold", spaceAfter=4)
    style_meta    = ParagraphStyle("DocMeta",    fontSize=8,  leading=12, textColor=light, fontName="Helvetica", spaceAfter=16)
    style_h1      = ParagraphStyle("H1",         fontSize=16, leading=22, textColor=dark,  fontName="Helvetica-Bold", spaceBefore=18, spaceAfter=6, borderPadding=(0,0,4,0))
    style_h2      = ParagraphStyle("H2",         fontSize=13, leading=18, textColor=dark,  fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=4)
    style_h3      = ParagraphStyle("H3",         fontSize=11, leading=16, textColor=gray,  fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=3)
    style_body    = ParagraphStyle("Body",       fontSize=10, leading=16, textColor=gray,  fontName="Helvetica", spaceAfter=8, alignment=TA_JUSTIFY)
    style_bullet  = ParagraphStyle("Bullet",     fontSize=10, leading=14, textColor=gray,  fontName="Helvetica", leftIndent=16, spaceAfter=3, bulletIndent=4)
    style_code    = ParagraphStyle("Code",       fontSize=8,  leading=12, textColor=colors.HexColor("#1F2937"), fontName="Courier", backColor=colors.HexColor("#F3F4F6"), leftIndent=12, rightIndent=12, spaceBefore=6, spaceAfter=6)
    style_toc_hdr = ParagraphStyle("TocHdr",     fontSize=9,  leading=14, textColor=accent, fontName="Helvetica-Bold", spaceAfter=4)

    soup = BeautifulSoup(html_content, "html.parser")

    story = []

    # Cover
    title_tag = soup.find(class_="doc-title")
    meta_tag  = soup.find(class_="doc-meta")
    if title_tag:
        story.append(Paragraph(html_mod.escape(title_tag.get_text()), style_title))
    if meta_tag:
        story.append(Paragraph(html_mod.escape(meta_tag.get_text()), style_meta))
    story.append(HRFlowable(width="100%", thickness=2.5, color=accent, spaceAfter=20))

    # TOC
    toc_div = soup.find(class_="toc")
    if toc_div:
        story.append(Paragraph("Table of Contents", style_toc_hdr))
        for li in toc_div.find_all("li"):
            story.append(Paragraph(f"• {html_mod.escape(li.get_text())}", style_bullet))
        story.append(Spacer(1, 20))

    # Exec summary
    exec_div = soup.find(class_="exec-summary")
    if exec_div:
        p_tag = exec_div.find("p")
        if p_tag:
            data = [[Paragraph("EXECUTIVE SUMMARY", ParagraphStyle("ESLabel", fontSize=8, fontName="Helvetica-Bold", textColor=colors.HexColor("#7C3AED"))),
                     Paragraph(html_mod.escape(p_tag.get_text()), style_body)]]
            t = Table(data, colWidths=["25%", "75%"])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F0F4FF")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#C4B5FD")),
                ("LINEBEFORE", (0, 0), (0, -1), 3, colors.HexColor("#7C3AED")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("LEFTPADDING", (0, 0), (-1, -1), 14),
            ]))
            story.append(t)
            story.append(Spacer(1, 20))

    # Walk sections
    for section_div in soup.find_all(class_="section"):
        for child in section_div.children:
            if not hasattr(child, "name") or not child.name:
                continue
            tag = child.name
            cls = " ".join(child.get("class", []))

            if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
                lvl = int(tag[1])
                s = {1: style_h1, 2: style_h2, 3: style_h3}.get(lvl, style_h3)
                story.append(Paragraph(html_mod.escape(child.get_text()), s))
                if lvl == 1:
                    story.append(HRFlowable(width="100%", thickness=1.5, color=accent, spaceAfter=8))

            elif tag == "p" and "doc-paragraph" in cls:
                story.append(Paragraph(html_mod.escape(child.get_text()), style_body))

            elif "doc-table-wrapper" in cls:
                tbl_el = child.find("table")
                if tbl_el:
                    rows_data = []
                    header_row = tbl_el.find("thead")
                    if header_row:
                        cells = [Paragraph(html_mod.escape(th.get_text()), ParagraphStyle("TH", fontSize=9, fontName="Helvetica-Bold", textColor=colors.white)) for th in header_row.find_all("th")]
                        rows_data.append(cells)
                    for tr in tbl_el.find_all("tr", recursive=False):
                        cells = [Paragraph(html_mod.escape(td.get_text()), style_body) for td in tr.find_all("td")]
                        if cells:
                            rows_data.append(cells)
                    # Also check tbody
                    tbody = tbl_el.find("tbody")
                    if tbody:
                        for tr in tbody.find_all("tr"):
                            cells = [Paragraph(html_mod.escape(td.get_text()), style_body) for td in tr.find_all("td")]
                            if cells:
                                rows_data.append(cells)

                    if rows_data:
                        try:
                            t = Table(rows_data, repeatRows=1 if header_row else 0)
                            ts = [
                                ("BACKGROUND", (0, 0), (-1, 0), accent),
                                ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
                                ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
                                ("FONTSIZE",   (0, 0), (-1, 0), 9),
                                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#FAFAFA"), colors.HexColor("#F3F4F8")]),
                                ("GRID",       (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
                                ("TOPPADDING",    (0, 0), (-1, -1), 7),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                                ("LEFTPADDING",   (0, 0), (-1, -1), 10),
                                ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
                                ("VALIGN",        (0, 0), (-1, -1), "TOP"),
                            ]
                            t.setStyle(TableStyle(ts))
                            story.append(t)
                            story.append(Spacer(1, 12))
                        except Exception:
                            pass

            elif "doc-list" in cls:
                for li in child.find_all("li"):
                    story.append(Paragraph(f"• {html_mod.escape(li.get_text())}", style_bullet))
                story.append(Spacer(1, 6))

            elif "doc-code-wrapper" in cls:
                code_el = child.find("code")
                if code_el:
                    lang_el = child.find(class_="doc-code-lang")
                    code_text = code_el.get_text()
                    if lang_el:
                        story.append(Paragraph(f"[{html_mod.escape(lang_el.get_text())}]", ParagraphStyle("CodeLang", fontSize=7, fontName="Helvetica-Bold", textColor=gray)))
                    try:
                        story.append(Preformatted(code_text, style_code))
                    except Exception:
                        story.append(Paragraph(html_mod.escape(code_text[:500]), style_body))
                    story.append(Spacer(1, 8))

    story.append(Spacer(1, 40))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E5E7EB")))
    story.append(Paragraph("Generated by ReadmeForge", style_meta))

    doc.build(story)
    buf.seek(0)
    return buf.read()
