"""
Conversion router — the core engine.
POST /api/convert/
  - Accepts .md file upload (max 5 MB)
  - Returns HTML preview + offers PDF/DOCX download
  - Optionally saves to DB if user is authenticated
"""

from __future__ import annotations
import os
import io
import uuid
import tempfile
import logging
from typing import Optional

from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
from fastapi.responses import StreamingResponse, JSONResponse

import database as db
from auth_utils import get_current_user
from md_parser import parse_markdown, model_to_dict
from html_renderer import render_html, SAFE_TABLE_COLORS, DEFAULT_COLOR
from document_generator import generate_docx, generate_pdf

router = APIRouter()
logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

OUTPUTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")
os.makedirs(OUTPUTS_DIR, exist_ok=True)


# ── Helpers ──────────────────────────────────────────────────────────────────

async def _read_and_validate(file: UploadFile) -> str:
    if not file.filename or not file.filename.endswith(".md"):
        raise HTTPException(400, "Only .md files are accepted")
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(413, "File too large (max 5 MB)")
    return content.decode("utf-8", errors="replace")


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/preview")
async def convert_preview(
    file: UploadFile = File(...),
    table_color: str = Form(DEFAULT_COLOR),
    current_user: Optional[dict] = Depends(get_current_user),
):
    """
    Upload a .md file → returns JSON with:
      - document_model (structured JSON)
      - html_preview   (full HTML string)
    """
    raw = await _read_and_validate(file)
    filename = file.filename or "document.md"

    try:
        model = parse_markdown(raw, filename)
        model_dict = model_to_dict(model)
        # Validate colour against allowlist
        safe_color = table_color if table_color in SAFE_TABLE_COLORS else DEFAULT_COLOR
        html = render_html(model, table_color=safe_color)
    except Exception as exc:
        logger.exception("Parsing failed")
        raise HTTPException(500, f"Conversion failed: {exc}")

    # Save record if logged in
    doc_id = None
    if current_user:
        try:
            record = await db.save_document_sqlite(
                user_id=current_user["sub"],
                original_filename=filename,
                output_type="html",
                cleaned_structure=model_dict,
                file_path="",
            )
            doc_id = record["doc_id"]
        except Exception as e:
            logger.warning(f"DB save failed: {e}")

    return JSONResponse({
        "success": True,
        "doc_id": doc_id,
        "filename": filename,
        "document_model": model_dict,
        "html_preview": html,
    })


@router.post("/download")
async def convert_and_download(
    file: UploadFile = File(...),
    format: str = Form("pdf"),
    table_color: str = Form(DEFAULT_COLOR),
    current_user: Optional[dict] = Depends(get_current_user),
):
    """
    Upload a .md file → stream back the converted file (PDF / DOCX / HTML).
    """
    if format not in ("pdf", "docx", "html"):
        raise HTTPException(400, "Format must be 'pdf', 'docx', or 'html'")

    raw = await _read_and_validate(file)
    filename = file.filename or "document.md"
    stem = filename.replace(".md", "").replace(" ", "_")

    try:
        model = parse_markdown(raw, filename)
        model_dict = model_to_dict(model)
        safe_color = table_color if table_color in SAFE_TABLE_COLORS else DEFAULT_COLOR
        html = render_html(model, table_color=safe_color)
    except Exception as exc:
        logger.exception("Parsing failed")
        raise HTTPException(500, f"Conversion failed: {exc}")

    if format == "html":
        data = html.encode("utf-8")
        media_type = "text/html"
        out_filename = f"{stem}_report.html"
    elif format == "docx":
        try:
            data = generate_docx(model, table_color=safe_color)
        except Exception as exc:
            logger.exception("DOCX generation failed")
            raise HTTPException(500, f"DOCX generation failed: {exc}")
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        out_filename = f"{stem}_report.docx"
    else:  # pdf
        try:
            data = generate_pdf(html, table_color=safe_color)
        except Exception as exc:
            logger.exception("PDF generation failed")
            raise HTTPException(500, f"PDF generation failed: {exc}")
        media_type = "application/pdf"
        out_filename = f"{stem}_report.pdf"

    # Save locally and record in DB if authenticated
    if current_user:
        try:
            file_path = os.path.join(OUTPUTS_DIR, f"{uuid.uuid4()}_{out_filename}")
            with open(file_path, "wb") as f:
                f.write(data)
            await db.save_document_sqlite(
                user_id=current_user["sub"],
                original_filename=filename,
                output_type=format,
                cleaned_structure=model_dict,
                file_path=file_path,
            )
        except Exception as e:
            logger.warning(f"DB/file save failed: {e}")

    headers = {
        "Content-Disposition": f'attachment; filename="{out_filename}"; filename*=UTF-8\'\'{out_filename}',
        "Content-Length": str(len(data)),
    }
    return StreamingResponse(io.BytesIO(data), media_type=media_type, headers=headers)
