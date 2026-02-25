"""
Documents router — conversion history for authenticated users.
"""

from fastapi import APIRouter, HTTPException, Depends
import database as db
from auth_utils import require_current_user

router = APIRouter()


@router.get("/")
async def list_documents(current_user: dict = Depends(require_current_user)):
    """Return conversion history for the logged-in user."""
    docs = await db.get_user_documents_sqlite(current_user["sub"])
    return {"documents": docs, "count": len(docs)}


@router.get("/{doc_id}")
async def get_document(doc_id: str, current_user: dict = Depends(require_current_user)):
    """Retrieve a specific document record."""
    doc = await db.get_document_by_id_sqlite(doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    if doc.get("user_id") != current_user["sub"]:
        raise HTTPException(403, "Access denied")
    return doc
