# Crimson Scriveners Readme Forger — Frontend

React + Vite + TypeScript + Tailwind CSS frontend for CSRF.

## Tech Stack

| Layer | Library |
|---|---|
| Framework | React 18 + TypeScript |
| Build tool | Vite 7 |
| Styling | Tailwind CSS v3 + shadcn/ui |
| Routing | React Router DOM v6 |
| Forms | React Hook Form + Zod |
| HTTP client | Native `fetch` (via `/src/lib/api.ts`) |
| Icons | Lucide React |

## Project Structure

```
src/
├── components/
│   ├── HeroSection.tsx      # Landing hero with CSRF branding
│   ├── Navbar.tsx           # Top navigation bar
│   └── UploadSection.tsx    # File upload, colour picker, convert & download
├── lib/
│   └── api.ts               # Centralised API client (auth + convert + documents)
├── pages/
│   ├── Auth.tsx             # Sign-in / sign-up page
│   ├── Dashboard.tsx        # Authenticated user dashboard
│   └── Index.tsx            # Landing page (Hero + Upload)
├── hooks/                   # Custom React hooks
├── index.css                # Global styles (monochrome design system)
└── main.tsx                 # App entry point
public/
└── CRIMSON SCRIVENERS.webp  # Logo asset
```

## Local Development

```bash
npm install
npm run dev          # → http://localhost:8080
```

The Vite dev server proxies all `/api/*` requests to `http://localhost:8000` automatically — no extra configuration needed.

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `VITE_API_BASE_URL` | Production only | Full Render backend URL e.g. `https://csrf-api.onrender.com` |

In development this variable is **not needed** — the Vite proxy handles it.

Copy `.env.example` to `.env` for local setup:
```bash
cp .env.example .env
```

## Build

```bash
npm run build        # outputs to dist/
npm run preview      # preview the production build locally
```

## Deployment

Deploy to **Vercel**. See [`../host.md`](../host.md) for the full step-by-step guide.

Build settings for Vercel:
- **Framework Preset:** Vite
- **Build Command:** `npm run build`
- **Output Directory:** `dist`
- **Environment Variable:** `VITE_API_BASE_URL` = your Render backend URL
