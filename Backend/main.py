"""
Crimson Scriveners Readme Forger — Backend (FastAPI)
"""
# Load .env before any other imports so os.environ is populated
from dotenv import load_dotenv
load_dotenv()

import os
import asyncio
import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from routers import auth, convert, documents
from database import init_db

logger = logging.getLogger(__name__)

# ── Keep-alive self-ping ──────────────────────────────────────────────────────
# Render free tier sleeps after 15 min of inactivity.
# We ping our own /api/health every 14 min to stay awake — well within
# Render's 750 free hours/month (24 × 30 = 720 h).
#
# RENDER_EXTERNAL_URL is set automatically by Render (e.g. https://csrf-api.onrender.com).
# On local dev this var is absent, so the ping loop simply skips.

PING_INTERVAL_SECONDS = 14 * 60   # 14 minutes

async def _keep_alive_loop() -> None:
    """Ping own health endpoint every 14 minutes to prevent Render cold-starts."""
    base_url = os.getenv("RENDER_EXTERNAL_URL", "").rstrip("/")
    if not base_url:
        logger.info("Keep-alive: RENDER_EXTERNAL_URL not set — skipping (local dev)")
        return

    health_url = f"{base_url}/api/health"
    logger.info(f"Keep-alive: will ping {health_url} every {PING_INTERVAL_SECONDS // 60} min")

    # Wait one full interval before the first ping so startup is not delayed
    await asyncio.sleep(PING_INTERVAL_SECONDS)

    async with httpx.AsyncClient(timeout=10) as client:
        while True:
            try:
                resp = await client.get(health_url)
                logger.info(f"Keep-alive ping → {resp.status_code}")
            except Exception as exc:
                logger.warning(f"Keep-alive ping failed: {exc}")
            await asyncio.sleep(PING_INTERVAL_SECONDS)


# ── App lifespan ──────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB and launch background keep-alive task on startup."""
    await init_db()

    # Start the keep-alive loop as a fire-and-forget background task
    keep_alive_task = asyncio.create_task(_keep_alive_loop())

    yield

    # Clean shutdown — cancel the background task
    keep_alive_task.cancel()
    try:
        await keep_alive_task
    except asyncio.CancelledError:
        pass


# ── FastAPI app ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="CSRF API",
    description="Crimson Scriveners Readme Forger — Transform README files into professional reports.",
    version="1.0.0",
    lifespan=lifespan,
    # Security: hide API schema from browser dev tools
    openapi_url=None,
    docs_url=None,
    redoc_url=None,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
_frontend_url = os.getenv("FRONTEND_URL", "").strip().rstrip("/")

_allowed_origins = [
    "http://localhost:8080",
    "http://localhost:5173",
    "http://127.0.0.1:8080",
]
if _frontend_url:
    _allowed_origins.append(_frontend_url)
    # Also allow www. variant
    if _frontend_url.startswith("https://") and not _frontend_url.startswith("https://www."):
        _allowed_origins.append(_frontend_url.replace("https://", "https://www.", 1))

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",  # all Vercel preview deployments
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(auth.router,      prefix="/api/auth",      tags=["Authentication"])
app.include_router(convert.router,   prefix="/api/convert",   tags=["Conversion"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "CSRF API", "version": "1.0.0"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
