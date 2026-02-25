"""
Markdown → Structured Document Model → Professional HTML/PDF/DOCX

Pipeline:
  1. Parse Markdown AST (via mistletoe)
  2. Remove Markdown tokens (badges, shields, separators, emoji spam)
  3. Normalize heading hierarchy
  4. Reconstruct tables → structured table objects
  5. Normalize lists
  6. Clean inline formatting
  7. Generate DocumentModel JSON
  8. Render professional HTML
  9. Convert to PDF (reportlab) or DOCX (python-docx)
"""

from __future__ import annotations

import re
import io
import logging
from dataclasses import dataclass, field
from typing import Any

import mistletoe
from mistletoe import Document as MistletoeDoc
from mistletoe.ast_renderer import AstRenderer

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Data model
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class TableCell:
    text: str
    is_header: bool = False


@dataclass
class TableNode:
    headers: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)


@dataclass
class ListNode:
    items: list[str] = field(default_factory=list)
    ordered: bool = False


@dataclass
class CodeBlock:
    code: str
    language: str = ""


@dataclass
class Section:
    heading: str
    level: int
    content: list[str] = field(default_factory=list)
    tables: list[TableNode] = field(default_factory=list)
    lists: list[ListNode] = field(default_factory=list)
    code_blocks: list[CodeBlock] = field(default_factory=list)


@dataclass
class DocumentModel:
    title: str
    sections: list[Section] = field(default_factory=list)
    has_references: bool = False


# ─────────────────────────────────────────────────────────────────────────────
# Regex helpers
# ─────────────────────────────────────────────────────────────────────────────

BADGE_RE = re.compile(
    r"!\[.*?\]\(https?://(?:img\.shields\.io|badge\.fury\.io|travis-ci|circleci|codecov|github\.com/.*?/badge)[^\)]*\)",
    re.IGNORECASE,
)
SHIELD_RE = re.compile(r"!\[.*?shield.*?\]\(.*?\)", re.IGNORECASE)
HTML_TAG_RE = re.compile(r"<[^>]+>")
EXCESS_EMOJI_RE = re.compile(
    r"(?:[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF"
    r"\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF"
    r"\u2600-\u26FF\u2700-\u27BF]){3,}",
    re.UNICODE,
)
INLINE_HEADING_RE = re.compile(r"#{2,6}\s*(.+?)(?:\s*#+)?$", re.MULTILINE)
SEPARATOR_RE = re.compile(r"^[-*_]{3,}\s*$", re.MULTILINE)
BOLD_RE = re.compile(r"\*{1,2}(.+?)\*{1,2}|_{1,2}(.+?)_{1,2}")
INLINE_CODE_RE = re.compile(r"`(.+?)`")


def _clean_inline(text: str) -> str:
    """Strip markdown inline syntax, preserve semantic content."""
    # Remove bold/italic markers but keep text
    text = BOLD_RE.sub(lambda m: m.group(1) or m.group(2), text)
    # Keep inline code content
    text = INLINE_CODE_RE.sub(r"\1", text)
    # Strip remaining markdown symbols
    text = re.sub(r"[`~]", "", text)
    text = HTML_TAG_RE.sub("", text)
    return text.strip()


def _extract_text_from_ast_node(node: dict) -> str:
    """Recursively extract plain text from an AST node."""
    if not isinstance(node, dict):
        return ""
    t = node.get("type", "")
    children = node.get("children", [])

    if t == "RawText":
        return node.get("content", "")
    if t in ("Strong", "Emphasis", "Strikethrough"):
        return "".join(_extract_text_from_ast_node(c) for c in children)
    if t == "InlineCode":
        return node.get("content", "")
    if t == "Link":
        return "".join(_extract_text_from_ast_node(c) for c in children)
    if t == "Image":
        return ""  # Remove images from text extraction
    return "".join(_extract_text_from_ast_node(c) for c in children)


def _is_badge_line(line: str) -> bool:
    """Detect shield/badge markdown lines."""
    return bool(BADGE_RE.search(line) or SHIELD_RE.search(line))


# ─────────────────────────────────────────────────────────────────────────────
# AST Walker → DocumentModel
# ─────────────────────────────────────────────────────────────────────────────

def _parse_table_node(node: dict) -> TableNode:
    """Convert an AST Table node to a TableNode."""
    table = TableNode()
    children = node.get("children", [])
    for row_node in children:
        if row_node.get("type") != "TableRow":
            continue
        cells = row_node.get("children", [])
        row_texts = [_clean_inline(_extract_text_from_ast_node(c)) for c in cells]
        if row_node.get("header"):
            table.headers = row_texts
        else:
            table.rows.append(row_texts)
    # Auto-repair: if headers empty, promote first row
    if not table.headers and table.rows:
        table.headers = table.rows.pop(0)
    return table


def _parse_list_node(node: dict) -> ListNode:
    lst = ListNode(ordered=node.get("start") is not None)
    for item in node.get("children", []):
        text_parts = []
        for child in item.get("children", []):
            if child.get("type") == "Paragraph":
                for sub in child.get("children", []):
                    text_parts.append(_extract_text_from_ast_node(sub))
        text = _clean_inline(" ".join(text_parts))
        if text:
            lst.items.append(text)
    return lst


def _walk_ast(nodes: list[dict], model: DocumentModel, current_section: list[Section]):
    """Walk AST nodes and populate the document model."""
    for node in nodes:
        t = node.get("type", "")

        if t == "Heading":
            level = node.get("level", 1)
            raw_text = "".join(_extract_text_from_ast_node(c) for c in node.get("children", []))
            text = _clean_inline(raw_text)
            if not text:
                continue

            if level == 1 and not model.title:
                model.title = text
                # Start a pseudo-section for title content
                sec = Section(heading="", level=1)
                model.sections.append(sec)
                current_section.clear()
                current_section.append(sec)
            else:
                sec = Section(heading=text, level=level)
                model.sections.append(sec)
                current_section.clear()
                current_section.append(sec)

        elif t == "Paragraph":
            raw = "".join(_extract_text_from_ast_node(c) for c in node.get("children", []))
            cleaned = _clean_inline(raw)
            if not cleaned or _is_badge_line(cleaned):
                continue
            # Skip separator-like lines
            if SEPARATOR_RE.match(cleaned):
                continue
            if current_section:
                current_section[0].content.append(cleaned)
            else:
                # Create implicit intro section
                sec = Section(heading="", level=1)
                model.sections.append(sec)
                current_section.append(sec)
                sec.content.append(cleaned)

        elif t == "Table":
            tbl = _parse_table_node(node)
            if current_section and (tbl.headers or tbl.rows):
                current_section[0].tables.append(tbl)

        elif t in ("List",):
            lst = _parse_list_node(node)
            if current_section and lst.items:
                current_section[0].lists.append(lst)

        elif t == "CodeFence":
            code = node.get("children", [{}])[0].get("content", "") if node.get("children") else ""
            lang = node.get("language", "")
            if current_section and code:
                current_section[0].code_blocks.append(CodeBlock(code=code, language=lang))

        elif t == "BlockQuote":
            # Render blockquote content as tagged paragraph
            for child in node.get("children", []):
                if child.get("type") == "Paragraph":
                    raw = "".join(_extract_text_from_ast_node(c) for c in child.get("children", []))
                    cleaned = _clean_inline(raw)
                    if cleaned and current_section:
                        current_section[0].content.append("> " + cleaned)

        elif t == "ThematicBreak":
            pass  # discard

        # Recurse into block-level containers
        elif "children" in node:
            _walk_ast(node["children"], model, current_section)


# ─────────────────────────────────────────────────────────────────────────────
# Pre-processing raw markdown
# ─────────────────────────────────────────────────────────────────────────────

def _preprocess_markdown(raw: str) -> str:
    """Clean raw markdown before AST parsing."""
    lines = []
    for line in raw.splitlines():
        # Remove badge lines
        if _is_badge_line(line):
            continue
        # Remove separator lines
        if SEPARATOR_RE.match(line):
            continue
        # Fix inline headings: "## Heading ##" → "## Heading"
        line = re.sub(r"(#{1,6}\s+.+?)\s+#+\s*$", r"\1", line)
        lines.append(line)

    text = "\n".join(lines)
    # Remove excess emoji clusters
    text = EXCESS_EMOJI_RE.sub("", text)
    return text


# ─────────────────────────────────────────────────────────────────────────────
# Public: parse → DocumentModel
# ─────────────────────────────────────────────────────────────────────────────

def parse_markdown(raw: str, filename: str = "document") -> DocumentModel:
    """Parse raw markdown string into a DocumentModel."""
    cleaned_raw = _preprocess_markdown(raw)

    with AstRenderer() as renderer:
        import json as _json
        ast_json = renderer.render(MistletoeDoc(cleaned_raw))
        ast = _json.loads(ast_json)

    model = DocumentModel(title="")
    current_section: list[Section] = []
    _walk_ast(ast.get("children", []), model, current_section)

    # Fallback title from filename
    if not model.title:
        model.title = filename.replace(".md", "").replace("-", " ").replace("_", " ").title()

    # Check for links → references section
    model.has_references = bool(re.search(r"\[.*?\]\(https?://", raw))

    # Remove completely empty sections
    model.sections = [s for s in model.sections if s.heading or s.content or s.tables or s.lists or s.code_blocks]

    return model


def model_to_dict(model: DocumentModel) -> dict:
    """Serialize DocumentModel to a JSON-safe dict."""
    sections_list = []
    for s in model.sections:
        sections_list.append({
            "heading": s.heading,
            "level": s.level,
            "content": s.content,
            "tables": [{"headers": t.headers, "rows": t.rows} for t in s.tables],
            "lists": [{"items": li.items, "ordered": li.ordered} for li in s.lists],
            "code_blocks": [{"code": c.code, "language": c.language} for c in s.code_blocks],
        })
    return {
        "title": model.title,
        "has_references": model.has_references,
        "sections": sections_list,
    }
