import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { FileText, Clock, Download, LogOut, Loader2, AlertCircle } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { authApi, documentsApi, type HistoryItem } from "@/lib/api";

const timeAgo = (isoDate: string): string => {
  const diff = Date.now() - new Date(isoDate).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "Just now";
  if (mins < 60) return `${mins} min ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs} hour${hrs > 1 ? "s" : ""} ago`;
  const days = Math.floor(hrs / 24);
  return `${days} day${days > 1 ? "s" : ""} ago`;
};

const Dashboard = () => {
  const navigate = useNavigate();
  const [docs, setDocs] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const user = authApi.currentUser();

  useEffect(() => {
    if (!authApi.isLoggedIn()) {
      navigate("/auth");
      return;
    }
    documentsApi
      .list()
      .then((res) => setDocs(res.documents))
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [navigate]);

  const handleSignOut = () => {
    authApi.logout();
    navigate("/auth");
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Nav */}
      <nav className="border-b border-border/50 px-6 py-4 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2">
          <div className="gradient-bg p-1.5 rounded-lg">
            <FileText className="h-4 w-4 text-primary-foreground" />
          </div>
          <span className="font-bold text-lg">ReadmeForge</span>
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
      </nav>

      <div className="max-w-3xl mx-auto px-6 py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h1 className="text-3xl font-bold mb-2">Dashboard</h1>
          <p className="text-muted-foreground mb-10">Your recent conversions</p>

          <div className="glass-card overflow-hidden">
            <div className="px-6 py-4 border-b border-border/30">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Clock className="h-4 w-4" />
                Conversion History
                {!loading && (
                  <span className="ml-auto text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full font-mono">
                    {docs.length} total
                  </span>
                )}
              </div>
            </div>

            {/* Loading */}
            {loading && (
              <div className="flex items-center justify-center gap-2 py-16 text-muted-foreground">
                <Loader2 className="h-5 w-5 animate-spin" />
                <span className="text-sm">Loading history…</span>
              </div>
            )}

            {/* Error */}
            {!loading && error && (
              <div className="flex items-center gap-2 px-6 py-8 text-destructive text-sm">
                <AlertCircle className="h-4 w-4 shrink-0" />
                {error}
              </div>
            )}

            {/* Empty state */}
            {!loading && !error && docs.length === 0 && (
              <div className="flex flex-col items-center gap-3 py-16 text-muted-foreground">
                <FileText className="h-10 w-10 opacity-30" />
                <p className="text-sm">No conversions yet.</p>
                <Link
                  to="/"
                  className="text-sm text-primary hover:text-primary/80 transition-colors"
                >
                  Convert your first README →
                </Link>
              </div>
            )}

            {/* Document list */}
            <div className="divide-y divide-border/20">
              {docs.map((item, i) => (
                <motion.div
                  key={item.doc_id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.06 }}
                  className="flex items-center gap-4 px-6 py-4 hover:bg-card/40 transition-colors"
                >
                  <FileText className="h-5 w-5 text-primary shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{item.original_filename}</p>
                    <p className="text-xs text-muted-foreground">{timeAgo(item.created_at)}</p>
                  </div>
                  <span className="text-xs font-mono px-2 py-1 rounded-md bg-primary/10 text-primary uppercase">
                    {item.output_type}
                  </span>
                  <button
                    aria-label={`Download ${item.original_filename}`}
                    title={`Download ${item.original_filename}`}
                    className="p-2 rounded-lg hover:bg-secondary/60 text-muted-foreground hover:text-foreground transition-colors"
                  >
                    <Download className="h-4 w-4" />
                  </button>
                </motion.div>
              ))}
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default Dashboard;

