# ReadmeForge — Backend

> **Python · FastAPI · Argon2id · SQLite / Firebase · mistletoe · python-docx · ReportLab**

The ReadmeForge backend is the processing engine that transforms raw GitHub-style Markdown files into professionally structured technical reports. It handles file upload, Markdown AST parsing, structural normalization, and document rendering to HTML, PDF, and DOCX — all exposed through a clean REST API.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Project Structure](#project-structure)
3. [API Reference](#api-reference)
4. [Conversion Pipeline](#conversion-pipeline)
5. [Authentication & Security](#authentication--security)
6. [Database Layer](#database-layer)
7. [Setup & Installation](#setup--installation)
8. [Environment Variables](#environment-variables)
9. [Running the Server](#running-the-server)
10. [Tech Stack](#tech-stack)

---

## Architecture Overview

```text
      │
      ▼
 FastAPI App  ──────────────────────────────────
      │                                         │
      ├── /api/auth      ←──  Argon2id hashing  │
      ├── /api/convert   ←──  MD Pipeline       │
      └── /api/documents ←──  History           │
                                                │
 Database Layer ────────────────────────────────
      ├── Firebase (primary — if credentials provided)
      │     ├── Firebase Auth
      │     ├── Firestore (metadata)
      │     └── Firebase Storage (files)
      └── SQLite (fallback / offline)
```

The database layer **automatically detects** whether Firebase credentials are available at startup. If not (or if the network is unreachable), it silently falls back to a local SQLite database with an identical schema.

---

## Project Structure

```text
├── main.py                  # FastAPI app, CORS, router registration, lifespan
├── database.py              # DB layer — Firebase primary, SQLite fallback
├── auth_utils.py            # JWT creation & verification, auth dependencies
├── md_parser.py             # Markdown → AST → DocumentModel
├── html_renderer.py         # DocumentModel → Professional HTML
├── document_generator.py    # DocumentModel → DOCX | HTML → PDF
├── requirements.txt         # All Python dependencies
├── routers/
│   ├── __init__.py
│   ├── auth.py              # POST /register, /login, /logout, GET /profile
│   ├── convert.py           # POST /preview, /download
│   └── documents.py         # GET /  (history), GET /{doc_id}
└── outputs/                 # Generated files saved here (auto-created)
```

---

## API Reference

### Authentication — `/api/auth`

| Method | Endpoint    | Auth Required | Description                             |
| ------ | ----------- | ------------- | --------------------------------------- |
| POST   | `/register` | No            | Create a new account (Argon2id hashing) |
| POST   | `/login`    | No            | Authenticate and receive a JWT          |
| POST   | `/logout`   | No            | Stateless logout (client drops the JWT) |
| GET    | `/profile`  | Yes           | Fetch current user profile              |

**Register request body:**

```json
{
  "name": "Jane Doe",
  "email": "jane@example.com",
  "password": "securepassword"
}
```

**Login / Register response:**

```json
{
  "access_token": "<JWT>",
  "token_type": "bearer",
  "user": { "uid": "...", "name": "Jane Doe", "email": "jane@example.com" }
}
```

---

### Conversion — `/api/convert`

| Method | Endpoint    | Auth Required | Description                                              |
| ------ | ----------- | ------------- | -------------------------------------------------------- |
| POST   | `/preview`  | Optional      | Upload `.md` → returns JSON document model + HTML string |
| POST   | `/download` | Optional      | Upload `.md` → streams PDF / DOCX / HTML file            |

#### `POST /api/convert/preview`

**Form fields:**

- `file` — `.md` file (multipart), max 5 MB

**Response:**

```json
{
  "success": true,
  "doc_id": "uuid-if-logged-in",
  "filename": "README.md",
  "document_model": {
    "title": "My Project",
    "has_references": true,
    "sections": [
      {
        "heading": "Overview",
        "level": 2,
        "content": ["paragraph text..."],
        "tables": [{ "headers": ["Name", "Age"], "rows": [["Neil", "22"]] }],
        "lists": [{ "items": ["item 1", "item 2"], "ordered": false }],
        "code_blocks": [{ "code": "npm install", "language": "bash" }]
      }
    ]
  },
  "html_preview": "<!DOCTYPE html>..."
}
```

#### `POST /api/convert/download`

**Form fields:**

- `file` — `.md` file (multipart), max 5 MB
- `format` — `"pdf"` | `"docx"` | `"html"` (default: `"pdf"`)

**Response:** Binary file stream with `Content-Disposition: attachment` header.

---

### Documents — `/api/documents`

Requires `Authorization: Bearer <token>` header.

| Method | Endpoint    | Description                          |
| ------ | ----------- | ------------------------------------ |
| GET    | `/`         | List all conversion history for user |
| GET    | `/{doc_id}` | Retrieve a specific document record  |

---

### Health Check

```http
→ { "status": "ok", "service": "ReadmeForge API", "version": "1.0.0" }
```

---

## Conversion Pipeline

The transformation engine operates in **9 stages**:

```text
1. Upload & Validate
        ↓
2. Pre-process Raw Markdown
   • Remove badge/shield lines  (img.shields.io etc.)
   • Remove separator lines     (---, ***, ___)
   • Fix inline heading clutter (## Heading ## → ## Heading)
   • Strip excess emoji clusters
        ↓
3. Parse Markdown into AST
   • Using mistletoe + AstRenderer
        ↓
4. Walk AST — Remove & Transform Tokens
   • Heading tokens   → Section objects with level
   • Bold / emphasis  → plain text (styling applied via CSS/DOCX styles)
   • Table nodes      → TableNode (auto-repair missing columns)
   • List nodes       → ListNode (ordered / unordered)
   • Code fences      → CodeBlock with language hint
   • ThematicBreak    → discarded
   • Images           → discarded
        ↓
5. Normalize Heading Hierarchy
   • Single H1 becomes document title
   • Malformed inline headings flattened
   • Empty sections removed
        ↓
6. Build DocumentModel (JSON)
   { title, sections[ { heading, level, content, tables, lists, code_blocks } ] }
        ↓
7. Render Professional HTML
   • Inter / Source Code Pro fonts (Google Fonts)
   • Cover page with title, date, badge
   • Auto-generated Table of Contents
   • Executive Summary box (first paragraph)
   • Styled tables (indigo header, alternating rows)
   • Dark-theme code blocks
   • 1-inch margins, justified body text
        ↓
8. Generate Output Format
   • HTML  → serve as-is
   • PDF   → WeasyPrint (preferred) or ReportLab fallback
   • DOCX  → python-docx with styled headings, table grid, code shading
        ↓
9. (Optional) Save to DB if user is authenticated
```

### Edge Case Handling

| Issue                     | Solution                                       |
| ------------------------- | ---------------------------------------------- |
| Inline heading chaos      | Regex normalization before AST parse           |
| No title found            | Auto-generated from filename                   |
| Broken / misaligned table | Auto-promote first row to header if none found |
| Massive code block        | Preformatted block with scroll / truncation    |
| Repeated separators       | Stripped at pre-processing stage               |
| Badge lines               | Detected by URL pattern, removed entirely      |
| Excel emoji spam          | 3+ consecutive emoji clusters removed          |

---

## Authentication & Security

- **Algorithm:** Argon2id via `argon2-cffi`
- **Parameters:** `memory_cost=65536` (64 MB), `time_cost=3`, `parallelism=2`, `hash_len=32`
- **Tokens:** HS256 JWT, 7-day expiry, signed with `JWT_SECRET_KEY`
- **Login is optional** — conversion works without authentication; auth enables history saving and re-download
- Argon2 **rehash-on-verify** is supported (upgrades old hashes transparently)

---

## Database Layer

`database.py` provides a unified async interface. On startup, it attempts to initialize Firebase. If credentials are absent or the connection fails, it falls back to SQLite automatically — no code changes needed.

### SQLite Schema

```sql
CREATE TABLE users (
    uid           TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    email         TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL
);

CREATE TABLE documents (
    doc_id              TEXT PRIMARY KEY,
    user_id             TEXT,                   -- nullable (anonymous conversion)
    original_filename   TEXT NOT NULL,
    output_type         TEXT NOT NULL,          -- 'pdf' | 'docx' | 'html'
    cleaned_structure   TEXT,                   -- JSON string of DocumentModel
    file_path           TEXT,
    created_at          TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(uid)
);
```

### Firebase (optional)

Set `FIREBASE_CREDENTIALS_PATH` and `FIREBASE_STORAGE_BUCKET` in your `.env`. The backend uses:

- **Firestore** for document metadata
- **Firebase Storage** for generated files
- Falls back to SQLite + local `outputs/` directory when unavailable

---

## Setup & Installation

### Prerequisites

- Python 3.11+
- pip

### Steps

```bash
# 1. Navigate to Backend
cd d:/Readme/Backend

# 2. Create a virtual environment
python -m venv .venv

# 3. Activate it
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. (Optional) Copy and configure environment variables
copy .env.example .env
# Edit .env with your secrets
```

---

## Environment Variables

Create a `.env` file in `d:/Readme/Backend/`:

```env
# JWT
JWT_SECRET_KEY=your-very-secret-key-change-this

# Firebase (optional — omit to use SQLite fallback)
FIREBASE_CREDENTIALS_PATH=path/to/serviceAccountKey.json
FIREBASE_STORAGE_BUCKET=your-project.appspot.com
```

---

## Running the Server

```bash
# Development (auto-reload)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Or directly via Python
python main.py
```

The API will be available at:

- **API Base:** `http://localhost:8000`
- **Interactive Docs (Swagger):** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **Health:** `http://localhost:8000/api/health`

The frontend (Vite dev server) proxies `/api/*` to port `8000`. Make sure both servers are running simultaneously.

---

## Tech Stack

| Layer               | Technology                             | Purpose                         |
| ------------------- | -------------------------------------- | ------------------------------- |
| Web Framework       | FastAPI 0.115                          | REST API, async, OpenAPI docs   |
| ASGI Server         | Uvicorn                                | Production-grade async server   |
| Markdown Parser     | mistletoe 1.4                          | AST-based Markdown parsing      |
| HTML Renderer       | Custom (`html_renderer.py`)            | Zero-artifact professional HTML |
| PDF Generation      | WeasyPrint (preferred) / ReportLab 4.2 | HTML→PDF or direct layout       |
| DOCX Generation     | python-docx 1.1                        | Styled Word documents           |
| Password Hashing    | argon2-cffi 23.1 (Argon2id)            | Secure credential storage       |
| JWT                 | python-jose                            | Stateless auth tokens           |
| Database (main)     | Firebase Admin SDK 6.6                 | Auth, Firestore, Storage        |
| Database (fallback) | aiosqlite 0.20                         | Local async SQLite              |
| Validation          | Pydantic v2                            | Request/response schemas        |
| File Uploads        | python-multipart                       | Multipart form parsing          |

---

## Notes

- The `outputs/` directory is auto-created on first run and stores generated files for authenticated users.
- The SQLite database file `readmeforge.db` is created automatically in the `Backend/` directory on startup.
- PDF generation requires either `weasyprint` (install separately — has OS-level GTK dependencies on Windows) or falls back to ReportLab which works out of the box.
