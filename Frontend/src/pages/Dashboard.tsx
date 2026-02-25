import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  FileText, Clock, Download, LogOut, Loader2, AlertCircle,
  ArrowLeft, History as HistoryIcon, RefreshCw,
} from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { authApi, documentsApi, type HistoryItem } from "@/lib/api";

const timeAgo = (isoDate: string): string => {
  const diff = Date.now() - new Date(isoDate).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "Just now";
  if (mins < 60) return `${mins} min ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs} hr${hrs > 1 ? "s" : ""} ago`;
  const days = Math.floor(hrs / 24);
  return `${days} day${days > 1 ? "s" : ""} ago`;
};

const FORMAT_COLORS: Record<string, { bg: string; text: string; label: string }> = {
  pdf:  { bg: "bg-rose-500/10",   text: "text-rose-400",   label: "PDF" },
  docx: { bg: "bg-blue-500/10",   text: "text-blue-400",   label: "DOCX" },
  html: { bg: "bg-emerald-500/10", text: "text-emerald-400", label: "HTML" },
};

const Dashboard = () => {
  const navigate = useNavigate();
  const [docs, setDocs] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const user = authApi.currentUser();

  const fetchDocs = () => {
    setLoading(true);
    setError(null);
    documentsApi
      .list()
      .then((res) => setDocs(res.documents))
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (!authApi.isLoggedIn()) {
      navigate("/auth");
      return;
    }
    fetchDocs();
  }, [navigate]);

  const handleSignOut = () => {
    authApi.logout();
    navigate("/");
  };

  return (
    <div className="min-h-screen bg-background">
      {/* ── Navbar ───────────────────────────────────────────────────────── */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-border/30 bg-background/60 backdrop-blur-xl">
        <div className="max-w-5xl mx-auto px-6 py-3 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3">
            <img
              src="/CRIMSON SCRIVENERS.webp"
              alt="CSRF Logo"
              className="h-8 w-8 rounded-sm object-cover"
            />
            <span className="font-bold text-lg tracking-tight hidden sm:block">
              Crimson Scriveners
            </span>
          </Link>

          <div className="flex items-center gap-4">
            {user && (
              <span className="text-sm text-muted-foreground hidden sm:block">
                {user.name}
              </span>
            )}
            <button
              onClick={handleSignOut}
              className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              <LogOut className="h-4 w-4" />
              Sign out
            </button>
          </div>
        </div>
      </nav>

      {/* ── Content ──────────────────────────────────────────────────────── */}
      <div className="max-w-5xl mx-auto px-6 pt-28 pb-16">
        {/* Back link */}
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors mb-8"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to converter
        </Link>

        {/* Page header */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45 }}
          className="flex items-start justify-between mb-8 flex-wrap gap-4"
        >
          <div>
            <div className="flex items-center gap-3 mb-1">
              <div className="p-2 rounded-xl gradient-bg">
                <HistoryIcon className="h-5 w-5 text-primary-foreground" />
              </div>
              <h1 className="text-3xl font-bold">Conversion History</h1>
            </div>
            <p className="text-muted-foreground pl-[52px]">
              All documents you've converted while signed in
            </p>
          </div>

          <button
            onClick={fetchDocs}
            disabled={loading}
            className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground border border-border/50 px-4 py-2 rounded-xl transition-colors disabled:opacity-40"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </motion.div>

        {/* ── Stats strip ────────────────────────────────────────────────── */}
        {!loading && !error && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="grid grid-cols-3 gap-4 mb-8"
          >
            {[
              { label: "Total conversions", value: docs.length },
              { label: "PDFs generated",    value: docs.filter(d => d.output_type === "pdf").length },
              { label: "DOCXs generated",   value: docs.filter(d => d.output_type === "docx").length },
            ].map((stat) => (
              <div
                key={stat.label}
                className="glass-card p-5 text-center"
              >
                <p className="text-3xl font-bold mb-1">{stat.value}</p>
                <p className="text-xs text-muted-foreground uppercase tracking-wider">{stat.label}</p>
              </div>
            ))}
          </motion.div>
        )}

        {/* ── Document list card ─────────────────────────────────────────── */}
        <motion.div
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="glass-card overflow-hidden"
        >
          {/* Card header */}
          <div className="px-6 py-4 border-b border-border/30 flex items-center gap-2">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium text-muted-foreground">Recent Documents</span>
            {!loading && (
              <span className="ml-auto text-xs bg-primary/10 text-primary px-2.5 py-1 rounded-full font-mono font-medium">
                {docs.length} total
              </span>
            )}
          </div>

          {/* Loading */}
          {loading && (
            <div className="flex items-center justify-center gap-3 py-20 text-muted-foreground">
              <Loader2 className="h-5 w-5 animate-spin" />
              <span className="text-sm">Loading history…</span>
            </div>
          )}

          {/* Error */}
          {!loading && error && (
            <div className="flex items-center gap-3 px-6 py-10 text-destructive">
              <AlertCircle className="h-5 w-5 shrink-0" />
              <div>
                <p className="text-sm font-medium">Failed to load history</p>
                <p className="text-xs text-muted-foreground mt-0.5">{error}</p>
              </div>
              <button
                onClick={fetchDocs}
                className="ml-auto text-xs border border-destructive/30 hover:bg-destructive/10 px-3 py-1.5 rounded-lg transition-colors"
              >
                Retry
              </button>
            </div>
          )}

          {/* Empty state */}
          {!loading && !error && docs.length === 0 && (
            <div className="flex flex-col items-center gap-4 py-20 text-muted-foreground">
              <div className="p-5 rounded-2xl bg-secondary/50">
                <FileText className="h-10 w-10 opacity-40" />
              </div>
              <div className="text-center">
                <p className="text-sm font-medium mb-1">No conversions yet</p>
                <p className="text-xs text-muted-foreground">Upload and convert a README to see it here</p>
              </div>
              <Link
                to="/"
                className="gradient-bg text-primary-foreground text-sm font-medium px-5 py-2.5 rounded-xl hover:shadow-lg hover:scale-105 transition-all duration-300"
              >
                Convert your first README →
              </Link>
            </div>
          )}

          {/* Document rows */}
          {!loading && !error && docs.length > 0 && (
            <div className="divide-y divide-border/20">
              {docs.map((item, i) => {
                const fmt = FORMAT_COLORS[item.output_type] ?? FORMAT_COLORS.html;
                return (
                  <motion.div
                    key={item.doc_id}
                    initial={{ opacity: 0, x: -12 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="flex items-center gap-4 px-6 py-4 hover:bg-card/50 transition-colors group"
                  >
                    {/* File icon */}
                    <div className="p-2 rounded-xl bg-secondary/60 shrink-0">
                      <FileText className="h-5 w-5 text-muted-foreground group-hover:text-foreground transition-colors" />
                    </div>

                    {/* Name + date */}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{item.original_filename}</p>
                      <p className="text-xs text-muted-foreground mt-0.5">{timeAgo(item.created_at)}</p>
                    </div>

                    {/* Format badge */}
                    <span
                      className={`text-xs font-mono font-semibold px-2.5 py-1 rounded-lg uppercase shrink-0 ${fmt.bg} ${fmt.text}`}
                    >
                      {fmt.label}
                    </span>

                    {/* Download icon (visual only — file_path from history) */}
                    {item.file_path && (
                      <button
                        aria-label={`Download ${item.original_filename}`}
                        title={`Download ${item.original_filename}`}
                        className="p-2 rounded-xl hover:bg-secondary/60 text-muted-foreground hover:text-foreground transition-colors opacity-0 group-hover:opacity-100 shrink-0"
                      >
                        <Download className="h-4 w-4" />
                      </button>
                    )}
                  </motion.div>
                );
              })}
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
};

export default Dashboard;
