import { Link, useNavigate, useLocation } from "react-router-dom";
import { History, LogOut } from "lucide-react";
import { authApi } from "@/lib/api";
import { useState, useEffect } from "react";

export const Navbar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [user, setUser] = useState(authApi.currentUser());

  // Re-sync auth state whenever the route changes (e.g. returning from /auth)
  useEffect(() => {
    setUser(authApi.currentUser());
  }, [location.pathname]);

  // Also re-sync on window focus (cross-tab sign-in/out)
  useEffect(() => {
    const syncUser = () => setUser(authApi.currentUser());
    window.addEventListener("focus", syncUser);
    return () => window.removeEventListener("focus", syncUser);
  }, []);

  const handleSignOut = () => {
    authApi.logout();
    setUser(null);
    navigate("/");
  };

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b border-border/30 bg-background/60 backdrop-blur-xl">
      <div className="max-w-6xl mx-auto px-6 py-3 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-3">
          <img
            src="/CRIMSON SCRIVENERS.webp"
            alt="CSRF Logo"
            className="h-8 w-8 rounded-sm object-cover"
          />
          <span className="font-bold text-lg tracking-tight">Crimson Scriveners Readme Forger</span>
        </Link>

        <div className="flex items-center gap-3">
          {user ? (
            <>
              <span className="text-sm text-muted-foreground hidden sm:block">
                {user.name}
              </span>
              <Link
                to="/dashboard"
                className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors px-3 py-2"
              >
                <History className="h-4 w-4" />
                <span className="hidden sm:inline">History</span>
              </Link>
              <button
                onClick={handleSignOut}
                className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors px-3 py-2"
              >
                <LogOut className="h-4 w-4" />
                <span className="hidden sm:inline">Sign out</span>
              </button>
            </>
          ) : (
            <>
              <Link
                to="/auth"
                className="text-sm text-muted-foreground hover:text-foreground transition-colors px-4 py-2"
              >
                Sign In
              </Link>
              <Link
                to="/auth"
                className="gradient-bg text-primary-foreground text-sm font-medium px-5 py-2 rounded-xl hover:shadow-lg hover:scale-105 transition-all duration-300"
              >
                Get Started
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
};
