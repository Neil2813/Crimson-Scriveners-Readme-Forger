# Crimson Scriveners Readme Forger (CSRF)

> Transform GitHub-style README files into beautifully formatted, professional technical reports — available as PDF, DOCX, or HTML.

---

## What is CSRF?

**Crimson Scriveners Readme Forger** is a full-stack web application that takes any Markdown (`.md`) file and converts it into a professionally typeset document with:

- Structured cover page with title, date, and branding
- Auto-generated Table of Contents
- Clean sectioned body with headings, paragraphs, lists, tables, and code blocks
- User-selectable table header colour (14 curated, text-safe palettes)
- Download as **PDF**, **DOCX**, or **HTML**

---

## Repository Structure

```
Readme/
├── Backend/          # FastAPI Python backend
│   ├── main.py           # App entry point, CORS, routers
│   ├── md_parser.py      # Markdown → DocumentModel (AST-based)
│   ├── html_renderer.py  # DocumentModel → HTML report
│   ├── document_generator.py  # HTML → PDF / DOCX
│   ├── auth_utils.py     # JWT helpers
│   ├── database.py       # SQLite CRUD (Firebase optional)
│   ├── routers/
│   │   ├── auth.py       # /api/auth/* (register, login, profile)
│   │   ├── convert.py    # /api/convert/* (preview, download)
│   │   └── documents.py  # /api/documents/* (history)
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
├── Frontend/         # React + Vite + Tailwind CSS frontend
│   ├── src/
│   │   ├── components/   # Navbar, HeroSection, UploadSection
│   │   ├── pages/        # Index, Auth, Dashboard
│   │   └── lib/api.ts    # API client
│   ├── public/
│   │   └── CRIMSON SCRIVENERS.webp  # Logo
│   ├── package.json
│   ├── .env.example
│   └── README.md
└── host.md           # Step-by-step Vercel + Render deployment guide
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18, TypeScript, Vite 7, Tailwind CSS v3, shadcn/ui |
| **Backend** | Python 3.11+, FastAPI, Uvicorn |
| **Auth** | Argon2id password hashing, JWT (python-jose) |
| **Database** | SQLite via aiosqlite (Firebase optional) |
| **PDF** | ReportLab + BeautifulSoup fallback |
| **DOCX** | python-docx |
| **Markdown parsing** | mistletoe (AST-based) |
| **Deployment** | Vercel (frontend) + Render (backend) |

---

## Quick Start — Local Development

### Prerequisites
- Python 3.11+
- Node.js 18+

### Backend

```bash
cd Backend

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1      # Windows PowerShell
# source .venv/bin/activate       # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — set JWT_SECRET_KEY to a long random string

# Start server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
# → http://localhost:8000
```

### Frontend

```bash
cd Frontend

# Install dependencies
npm install

# No .env needed for local dev (Vite proxy handles /api routing)

# Start dev server
npm run dev
# → http://localhost:8080
```



---

## API Endpoints

All endpoints are prefixed `/api/`. API docs are **intentionally disabled** for security (`/docs`, `/redoc`, and `/openapi.json` all return 404).

| Method | Path | Description | Auth |
|---|---|---|---|
| `POST` | `/api/auth/register` | Create account | — |
| `POST` | `/api/auth/login` | Get JWT token | — |
| `GET` | `/api/auth/profile` | Get current user | Required |
| `POST` | `/api/auth/logout` | Logout (stateless) | — |
| `POST` | `/api/convert/preview` | Convert MD → HTML + model JSON | Optional |
| `POST` | `/api/convert/download` | Convert MD → PDF / DOCX / HTML file | Optional |
| `GET` | `/api/documents/` | List conversion history | Required |
| `GET` | `/api/health` | Health check | — |

### Convert endpoint parameters

Both `/api/convert/preview` and `/api/convert/download` accept `multipart/form-data`:

| Field | Type | Default | Description |
|---|---|---|---|
| `file` | File | Required | The `.md` file to convert |
| `table_color` | string | `"default"` | Table header colour key (see below) |
| `format` | string | `"pdf"` | `pdf` \| `docx` \| `html` (download only) |

**Available table colours:** `default`, `none`, `slate`, `stone`, `zinc`, `steel`, `sage`, `ocean`, `dusk`, `wine`, `cedar`, `teal`, `graphite`, `forest`

---


## Features

- 📄 **Markdown → PDF / DOCX / HTML** in seconds
- 🎨 **14 table colour themes** — muted, text-safe palettes chosen by the user
- 🔒 **Auth** — register/login with JWT, conversion history saved per user
- 👁️ **HTML preview** inline before downloading
- 🔐 **Secure** — API docs hidden, CORS locked to known origins
- 📱 **Responsive** — works on mobile and desktop
- 🖤 **Monochrome design** — professional black-and-white aesthetic

---

## Branding

**Application name:** Crimson Scriveners Readme Forger  
**Short form:** CSRF  
**Logo:** `Frontend/public/CRIMSON SCRIVENERS.webp`
