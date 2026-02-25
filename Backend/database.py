"""
Database layer — Firebase primary, SQLite fallback.
"""
import os
import json
import uuid
import logging
from datetime import datetime
from typing import Optional

import aiosqlite

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "readmeforge.db")

# ──────────────────────────────────────────────────────────────────────────────
# Firebase initialisation (optional, graceful degradation to SQLite)
# ──────────────────────────────────────────────────────────────────────────────
firebase_app = None

def _init_firebase():
    global firebase_app
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore, storage

        cred_path = os.environ.get("FIREBASE_CREDENTIALS_PATH", "")
        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_app = firebase_admin.initialize_app(cred, {
                "storageBucket": os.environ.get("FIREBASE_STORAGE_BUCKET", "")
            })
            logger.info("Firebase initialised successfully")
        else:
            logger.info("Firebase credentials not found — using SQLite")
    except Exception as exc:
        logger.warning(f"Firebase init failed ({exc}) — falling back to SQLite")

_init_firebase()


def is_firebase_available() -> bool:
    return firebase_app is not None


# ──────────────────────────────────────────────────────────────────────────────
# SQLite helpers
# ──────────────────────────────────────────────────────────────────────────────
SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    uid          TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    email        TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS documents (
    doc_id              TEXT PRIMARY KEY,
    user_id             TEXT,
    original_filename   TEXT NOT NULL,
    output_type         TEXT NOT NULL,
    cleaned_structure   TEXT,
    file_path           TEXT,
    created_at          TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(uid)
);
"""


async def init_db():
    """Create SQLite tables if they don't exist."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        await db.commit()
    logger.info("SQLite database ready")


# ──────────────────────────────────────────────────────────────────────────────
# User CRUD
# ──────────────────────────────────────────────────────────────────────────────

async def create_user_sqlite(name: str, email: str, password_hash: str) -> dict:
    uid = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO users (uid, name, email, password_hash, created_at) VALUES (?,?,?,?,?)",
            (uid, name, email, password_hash, now),
        )
        await db.commit()
    return {"uid": uid, "name": name, "email": email, "created_at": now}


async def get_user_by_email_sqlite(email: str) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_user_by_id_sqlite(uid: str) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT uid, name, email, created_at FROM users WHERE uid = ?", (uid,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


# ──────────────────────────────────────────────────────────────────────────────
# Document CRUD
# ──────────────────────────────────────────────────────────────────────────────

async def save_document_sqlite(
    user_id: Optional[str],
    original_filename: str,
    output_type: str,
    cleaned_structure: dict,
    file_path: str,
) -> dict:
    doc_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO documents
               (doc_id, user_id, original_filename, output_type, cleaned_structure, file_path, created_at)
               VALUES (?,?,?,?,?,?,?)""",
            (
                doc_id,
                user_id,
                original_filename,
                output_type,
                json.dumps(cleaned_structure),
                file_path,
                now,
            ),
        )
        await db.commit()
    return {
        "doc_id": doc_id,
        "user_id": user_id,
        "original_filename": original_filename,
        "output_type": output_type,
        "file_path": file_path,
        "created_at": now,
    }


async def get_user_documents_sqlite(user_id: str) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM documents WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_document_by_id_sqlite(doc_id: str) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM documents WHERE doc_id = ?", (doc_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None
