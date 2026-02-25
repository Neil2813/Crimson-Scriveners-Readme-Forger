"""
Crimsor Scriveners Readme Forger — Backend (FastAPI)
"""
# Load .env before any other imports so os.environ is populated
from dotenv import load_dotenv
load_dotenv()

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from routers import auth, convert, documents
from database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    await init_db()
    yield


app = FastAPI(
    title="CSRF API",
    description="Crimsor Scriveners Readme Forger - Transform README files into professional reports.",
    version="1.0.0",
    lifespan=lifespan,
    # ── Security: disable all auto-generated API documentation ──
    openapi_url=None,
    docs_url=None,
    redoc_url=None,
)

# ── CORS ─────────────────────────────────────────────────────────────────────
# FRONTEND_URL env var is set in Render dashboard to the Vercel deployment URL.
# Falls back to localhost for local dev.
_frontend_url = os.getenv("FRONTEND_URL", "").strip().rstrip("/")

_allowed_origins = [
    "http://localhost:8080",
    "http://localhost:5173",
    "http://127.0.0.1:8080",
]
if _frontend_url:
    _allowed_origins.append(_frontend_url)
    # also allow www. variant if bare domain provided
    if _frontend_url.startswith("https://") and not _frontend_url.startswith("https://www."):
        _allowed_origins.append(_frontend_url.replace("https://", "https://www.", 1))

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",  # allows all Vercel preview deployments
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,      prefix="/api/auth",      tags=["Authentication"])
app.include_router(convert.router,   prefix="/api/convert",   tags=["Conversion"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "CSRF API", "version": "1.0.0"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
