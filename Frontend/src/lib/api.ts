/**
 * ReadmeForge — centralised API client
 *
 * All requests go through /api/* which Vite proxies to localhost:8000
 * in development. In production, point your reverse-proxy (Nginx etc.)
 * to the same backend.
 */

// In development: empty string → Vite proxy forwards /api → localhost:8000
// In production:  VITE_API_BASE_URL is set to the Render backend URL (e.g. https://csrf-api.onrender.com)
const BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "") + "/api";

// ── Token storage ────────────────────────────────────────────────────────────

const TOKEN_KEY = "rmf_token";
const USER_KEY  = "rmf_user";

export const tokenStore = {
  get: (): string | null => localStorage.getItem(TOKEN_KEY),
  set: (t: string)       => localStorage.setItem(TOKEN_KEY, t),
  clear: ()              => { localStorage.removeItem(TOKEN_KEY); localStorage.removeItem(USER_KEY); },
};

export const userStore = {
  get: (): AuthUser | null => {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as AuthUser) : null;
  },
  set: (u: AuthUser) => localStorage.setItem(USER_KEY, JSON.stringify(u)),
};

// ── Types ─────────────────────────────────────────────────────────────────────

export interface AuthUser {
  uid: string;
  name: string;
  email: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

export interface DocumentSection {
  heading: string;
  level: number;
  content: string[];
  tables: { headers: string[]; rows: string[][] }[];
  lists: { items: string[]; ordered: boolean }[];
  code_blocks: { code: string; language: string }[];
}

export interface DocumentModel {
  title: string;
  has_references: boolean;
  sections: DocumentSection[];
}

export interface PreviewResponse {
  success: boolean;
  doc_id: string | null;
  filename: string;
  document_model: DocumentModel;
  html_preview: string;
}

export interface HistoryItem {
  doc_id: string;
  user_id: string;
  original_filename: string;
  output_type: string;
  created_at: string;
  file_path: string;
}

// ── Low-level fetch wrapper ───────────────────────────────────────────────────

async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = tokenStore.get();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE}${path}`, { ...options, headers });

  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      msg = body.detail || body.message || msg;
    } catch {
      // ignore
    }
    throw new Error(msg);
  }

  return res.json() as Promise<T>;
}

// ── Auth API ─────────────────────────────────────────────────────────────────

export const authApi = {
  async register(name: string, email: string, password: string): Promise<AuthResponse> {
    const data = await apiFetch<AuthResponse>("/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, password }),
    });
    tokenStore.set(data.access_token);
    userStore.set(data.user);
    return data;
  },

  async login(email: string, password: string): Promise<AuthResponse> {
    const data = await apiFetch<AuthResponse>("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    tokenStore.set(data.access_token);
    userStore.set(data.user);
    return data;
  },

  async profile(): Promise<AuthUser> {
    return apiFetch<AuthUser>("/auth/profile");
  },

  logout() {
    tokenStore.clear();
  },

  isLoggedIn(): boolean {
    return !!tokenStore.get();
  },

  currentUser(): AuthUser | null {
    return userStore.get();
  },
};

// ── Conversion API ────────────────────────────────────────────────────────────

export const convertApi = {
  /**
   * Upload a .md file and get back the structured document model + HTML preview.
   */
  async preview(file: File, tableColor = "default"): Promise<PreviewResponse> {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("table_color", tableColor);

    const token = tokenStore.get();
    const headers: Record<string, string> = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const res = await fetch(`${BASE}/convert/preview`, {
      method: "POST",
      headers,
      body: fd,
    });

    if (!res.ok) {
      let msg = `HTTP ${res.status}`;
      try {
        const body = await res.json();
        msg = body.detail || msg;
      } catch { /* ignore */ }
      throw new Error(msg);
    }
    return res.json() as Promise<PreviewResponse>;
  },

  /**
   * Upload a .md file and download the converted document.
   * Returns a Blob that can be turned into an object URL.
   */
  async download(file: File, format: "pdf" | "docx" | "html", tableColor = "default"): Promise<{ blob: Blob; filename: string }> {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("format", format);
    fd.append("table_color", tableColor);

    const token = tokenStore.get();
    const headers: Record<string, string> = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const res = await fetch(`${BASE}/convert/download`, {
      method: "POST",
      headers,
      body: fd,
    });

    if (!res.ok) {
      let msg = `HTTP ${res.status}`;
      try {
        const body = await res.json();
        msg = body.detail || msg;
      } catch { /* ignore */ }
      throw new Error(msg);
    }

    const blob = await res.blob();
    const disposition = res.headers.get("Content-Disposition") ?? "";
    // Try filename*= (RFC 5987), then filename="..." quoted, then filename=... unquoted
    let filename: string | null = null;
    const rfcMatch = disposition.match(/filename\*=(?:UTF-8'')?([^;\r\n]+)/i);
    if (rfcMatch) filename = decodeURIComponent(rfcMatch[1].replace(/"/g, ""));
    if (!filename) {
      const quotedMatch = disposition.match(/filename="([^"]+)"/);
      if (quotedMatch) filename = quotedMatch[1];
    }
    if (!filename) {
      const plainMatch = disposition.match(/filename=([^;\r\n]+)/);
      if (plainMatch) filename = plainMatch[1].trim();
    }
    // Sensible fallback using the original file stem
    if (!filename) {
      const stem = file.name.replace(/\.md$/i, "").replace(/\s+/g, "_") || "document";
      filename = `${stem}_report.${format}`;
    }
    return { blob, filename };
  },
};

// ── Documents history API ─────────────────────────────────────────────────────

export const documentsApi = {
  async list(): Promise<{ documents: HistoryItem[]; count: number }> {
    return apiFetch("/documents/");
  },

  async get(docId: string): Promise<HistoryItem> {
    return apiFetch(`/documents/${docId}`);
  },
};

// ── Health check ──────────────────────────────────────────────────────────────

export async function healthCheck(): Promise<boolean> {
  try {
    const res = await fetch(`${BASE}/health`);
    return res.ok;
  } catch {
    return false;
  }
}
