"""
HTML renderer — converts DocumentModel into a professional black-and-white
technical report with a user-selectable table accent colour.
"""

from __future__ import annotations
import html as html_lib
from md_parser import DocumentModel, Section

# ---------------------------------------------------------------------------
# Allowlisted table header colours (12 muted tones + none + default)
# "none"    → white header, dark text (no colour)
# "default" → pure black header (classic B&W)
# ---------------------------------------------------------------------------
SAFE_TABLE_COLORS: dict[str, dict] = {
    "default":  {"bg": "#111111", "text": "#ffffff", "stripe": "#f5f5f5"},
    "none":     {"bg": "#ffffff", "text": "#111111", "stripe": "#f8f8f8"},
    "slate":    {"bg": "#475569", "text": "#ffffff", "stripe": "#f1f5f9"},
    "stone":    {"bg": "#57534e", "text": "#ffffff", "stripe": "#f5f5f4"},
    "zinc":     {"bg": "#52525b", "text": "#ffffff", "stripe": "#f4f4f5"},
    "steel":    {"bg": "#4b6070", "text": "#ffffff", "stripe": "#eef2f5"},
    "sage":     {"bg": "#4a6741", "text": "#ffffff", "stripe": "#f0f4ef"},
    "ocean":    {"bg": "#2d5f7a", "text": "#ffffff", "stripe": "#edf4f8"},
    "dusk":     {"bg": "#5b4d7a", "text": "#ffffff", "stripe": "#f3f0f7"},
    "wine":     {"bg": "#7a2d3e", "text": "#ffffff", "stripe": "#f9eef0"},
    "cedar":    {"bg": "#7a4a2d", "text": "#ffffff", "stripe": "#f8f1ec"},
    "teal":     {"bg": "#2d6b6b", "text": "#ffffff", "stripe": "#edf5f5"},
    "graphite": {"bg": "#3d4451", "text": "#ffffff", "stripe": "#f0f1f3"},
    "forest":   {"bg": "#2d5a3d", "text": "#ffffff", "stripe": "#edf4f0"},
}

DEFAULT_COLOR = "default"


# ---------------------------------------------------------------------------
# CSS builder — injects chosen table colours at render-time
# ---------------------------------------------------------------------------

def _build_css(table_header_bg: str, table_header_text: str, table_stripe_bg: str) -> str:
    return f"""
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,wght@0,300;0,400;0,600;0,700;1,400&family=JetBrains+Mono:wght@400;500&display=swap');

*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

body {{
  font-family: 'Source Serif 4', Georgia, 'Times New Roman', serif;
  font-size: 11pt;
  line-height: 1.8;
  color: #000;
  background: #fff;
  max-width: 860px;
  margin: 0 auto;
  padding: 72px 80px;
}}

@media print {{
  body {{ padding: 0; max-width: 100%; }}
  .no-break {{ page-break-inside: avoid; }}
  .page-break {{ page-break-before: always; }}
  a {{ color: inherit; text-decoration: none; }}
}}

/* ── Cover page ── */
.doc-cover {{
  padding: 60px 0 48px;
  border-bottom: 2px solid #000;
  margin-bottom: 56px;
}}
.doc-cover .doc-title {{
  font-size: 24pt;
  font-weight: 700;
  color: #000;
  line-height: 1.25;
  margin-bottom: 14px;
  letter-spacing: -0.3px;
}}
.doc-cover .doc-meta {{
  font-family: 'JetBrains Mono', 'Courier New', monospace;
  font-size: 8.5pt;
  color: #444;
  letter-spacing: 0.4px;
  margin-bottom: 6px;
}}
.doc-cover .doc-rule {{
  width: 48px;
  height: 2px;
  background: #000;
  margin: 20px 0 14px;
}}
.doc-cover .doc-generated {{
  font-size: 8pt;
  color: #666;
  font-family: 'JetBrains Mono', monospace;
}}

/* ── Table of Contents ── */
.toc {{
  border: 1px solid #ccc;
  padding: 24px 28px;
  margin-bottom: 56px;
}}
.toc-title {{
  font-size: 8.5pt;
  font-weight: 700;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: #000;
  margin-bottom: 16px;
  border-bottom: 1px solid #ddd;
  padding-bottom: 8px;
}}
.toc ol {{
  padding-left: 0;
  list-style: none;
}}
.toc li {{
  font-size: 9.5pt;
  color: #222;
  padding: 3px 0;
  line-height: 1.5;
  display: flex;
  align-items: baseline;
  gap: 6px;
}}
.toc li .toc-num {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 8pt;
  color: #666;
  min-width: 28px;
  flex-shrink: 0;
}}
.toc li.indent-1 {{ padding-left: 20px; }}
.toc li.indent-2 {{ padding-left: 40px; }}
.toc li.indent-3 {{ padding-left: 56px; }}

/* ── Sections ── */
.section {{ margin-bottom: 44px; }}
.section-heading {{ margin-bottom: 14px; color: #000; }}
.section-heading.level-1 {{
  font-size: 18pt; font-weight: 700;
  border-bottom: 2px solid #000;
  padding-bottom: 6px; margin-top: 48px;
}}
.section-heading.level-2 {{
  font-size: 14pt; font-weight: 700;
  border-bottom: 1px solid #bbb;
  padding-bottom: 4px; margin-top: 36px;
}}
.section-heading.level-3 {{ font-size: 11.5pt; font-weight: 700; margin-top: 28px; }}
.section-heading.level-4,
.section-heading.level-5,
.section-heading.level-6 {{
  font-size: 10.5pt; font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.6px; font-style: italic; margin-top: 24px;
}}

/* ── Body text ── */
.doc-paragraph {{
  margin-bottom: 14px;
  color: #111;
  font-size: 10.5pt;
  text-align: justify;
  hyphens: auto;
}}

/* ── Blockquote ── */
.doc-blockquote {{
  margin: 18px 0;
  padding: 14px 20px;
  border-left: 3px solid #888;
  background: #f7f7f7;
  font-style: italic;
  color: #333;
  font-size: 10.5pt;
}}
.doc-blockquote p {{ margin: 0; text-align: left; }}

/* ── Tables ── */
.doc-table-wrapper {{ overflow-x: auto; margin: 20px 0 24px; }}
.doc-table {{
  width: 100%;
  border-collapse: collapse;
  font-size: 9pt;
}}
.doc-table thead tr {{
  background: {table_header_bg};
  color: {table_header_text};
}}
.doc-table thead th {{
  padding: 8px 12px;
  text-align: left;
  font-weight: 600;
  font-size: 8.5pt;
  letter-spacing: 0.3px;
  border: 1px solid {table_header_bg};
}}
.doc-table tbody tr:nth-child(even) {{ background: {table_stripe_bg}; }}
.doc-table tbody tr:nth-child(odd)  {{ background: #fff; }}
.doc-table tbody td {{
  padding: 7px 12px;
  border: 1px solid #ccc;
  color: #111;
  vertical-align: top;
  font-size: 9pt;
  line-height: 1.5;
}}
.doc-table tbody td:first-child {{ font-weight: 500; }}

/* ── Lists ── */
.doc-list {{ margin: 10px 0 14px 0; padding-left: 24px; }}
.doc-list.ordered  {{ list-style: decimal; }}
.doc-list.unordered {{ list-style: disc; }}
.doc-list li {{ margin-bottom: 4px; color: #111; font-size: 10.5pt; line-height: 1.65; }}

/* ── Code blocks ── */
.doc-code-wrapper {{ margin: 14px 0 20px; border: 1px solid #ccc; }}
.doc-code-lang {{
  background: #111;
  color: #ccc;
  font-family: 'JetBrains Mono', 'Courier New', monospace;
  font-size: 7.5pt;
  padding: 4px 12px;
  letter-spacing: 0.8px;
  text-transform: uppercase;
}}
.doc-code {{
  display: block;
  padding: 16px;
  background: #fafafa;
  color: #111;
  font-family: 'JetBrains Mono', 'Courier New', monospace;
  font-size: 8.5pt;
  line-height: 1.6;
  overflow-x: auto;
  white-space: pre;
  border-top: 1px solid #ddd;
}}

/* ── Footer ── */
.doc-footer {{
  margin-top: 64px;
  padding-top: 12px;
  border-top: 1px solid #bbb;
  display: flex;
  justify-content: space-between;
  font-size: 7.5pt;
  color: #888;
  font-family: 'JetBrains Mono', monospace;
}}
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _esc(text: str) -> str:
    return html_lib.escape(str(text))


def _render_table(table) -> str:
    if not table.headers and not table.rows:
        return ""

    def _cell_html(text: str) -> str:
        return html_lib.escape(str(text), quote=True)

    headers_html = "".join(f"<th>{_cell_html(h)}</th>" for h in table.headers)
    thead = f"<thead><tr>{headers_html}</tr></thead>" if table.headers else ""

    rows_html = "\n".join(
        "<tr>" + "".join(f"<td>{_cell_html(cell)}</td>" for cell in row) + "</tr>"
        for row in table.rows
    )
    return f"""
    <div class="doc-table-wrapper no-break">
      <table class="doc-table">
        {thead}
        <tbody>{rows_html}</tbody>
      </table>
    </div>"""


def _render_list(lst) -> str:
    tag = "ol" if lst.ordered else "ul"
    cls = "ordered" if lst.ordered else "unordered"
    items = "\n".join(f"<li>{_esc(item)}</li>" for item in lst.items)
    return f'<{tag} class="doc-list {cls}">{items}</{tag}>'


def _render_code_block(block) -> str:
    lang_label = (
        f'<div class="doc-code-lang">{_esc(block.language)}</div>'
        if block.language else
        '<div class="doc-code-lang">code</div>'
    )
    return f"""
    <div class="doc-code-wrapper no-break">
      {lang_label}
      <code class="doc-code">{_esc(block.code)}</code>
    </div>"""


def _is_blockquote_line(text: str) -> bool:
    return text.startswith("> ") or text.startswith(">")


def _render_section(section: Section) -> str:
    parts = []

    if section.heading:
        lvl = max(1, min(section.level, 6))
        parts.append(
            f'<h{lvl} class="section-heading level-{lvl}">{_esc(section.heading)}</h{lvl}>'
        )

    for para in section.content:
        stripped = para.strip()
        if _is_blockquote_line(stripped):
            inner = stripped.lstrip("> ").strip()
            parts.append(f'<blockquote class="doc-blockquote"><p>{_esc(inner)}</p></blockquote>')
        else:
            parts.append(f'<p class="doc-paragraph">{_esc(stripped)}</p>')

    for tbl in section.tables:
        parts.append(_render_table(tbl))

    for lst in section.lists:
        parts.append(_render_list(lst))

    for cb in section.code_blocks:
        parts.append(_render_code_block(cb))

    return f'<div class="section">{"".join(parts)}</div>'


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def render_html(
    model: DocumentModel,
    generated_date: str = "",
    table_color: str = DEFAULT_COLOR,
) -> str:
    """Render DocumentModel into a full professional HTML document.

    Args:
        model: The parsed document model.
        generated_date: Override the generation date (ISO string).
        table_color: One of the SAFE_TABLE_COLORS keys. Unknown values fall
                     back to DEFAULT_COLOR silently.
    """
    import datetime
    gen_date = generated_date or datetime.datetime.utcnow().strftime("%d %B %Y")

    # Resolve colour — reject unknown values for safety
    palette = SAFE_TABLE_COLORS.get(table_color, SAFE_TABLE_COLORS[DEFAULT_COLOR])
    css = _build_css(
        table_header_bg=palette["bg"],
        table_header_text=palette["text"],
        table_stripe_bg=palette["stripe"],
    )

    # ── Table of Contents ─────────────────────────────────────────────────────
    named_sections = [s for s in model.sections if s.heading]
    toc_rows = []
    counter: dict[int, int] = {}
    for s in named_sections:
        lvl = s.level
        counter[lvl] = counter.get(lvl, 0) + 1
        for deeper in list(counter.keys()):
            if deeper > lvl:
                counter[deeper] = 0
        num_str = ".".join(
            str(counter.get(l, 0))
            for l in sorted(k for k in counter if k <= lvl and counter.get(k, 0) > 0)
        )
        indent_class = f"indent-{lvl - 2}" if lvl > 2 else ""
        toc_rows.append(
            f'<li class="{indent_class}">'
            f'<span class="toc-num">{_esc(num_str)}</span>'
            f'{_esc(s.heading)}</li>'
        )

    toc_html = ""
    if toc_rows:
        toc_html = f"""
        <nav class="toc no-break">
          <div class="toc-title">Table of Contents</div>
          <ol>{"".join(toc_rows)}</ol>
        </nav>"""

    # ── Body ─────────────────────────────────────────────────────────────────
    body_html = "\n".join(_render_section(s) for s in model.sections)

    # ── Assemble ─────────────────────────────────────────────────────────────
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{_esc(model.title)} — Technical Report</title>
  <style>{css}</style>
</head>
<body>
  <header class="doc-cover no-break">
    <div class="doc-title">{_esc(model.title)}</div>
    <div class="doc-rule"></div>
    <div class="doc-meta">Report by Crimsor Scriveners &bull; CSRF</div>
    <div class="doc-generated">Generated: {_esc(gen_date)}</div>
  </header>

  {toc_html}

  {body_html}

  <footer class="doc-footer">
    <span>{_esc(model.title)}</span>
    <span>Generated by CSRF &bull; {_esc(gen_date)}</span>
  </footer>
</body>
</html>"""
