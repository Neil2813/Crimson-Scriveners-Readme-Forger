import { Link } from "react-router-dom";
import { FileText } from "lucide-react";

export const Navbar = () => {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b border-border/30 bg-background/60 backdrop-blur-xl">
      <div className="max-w-6xl mx-auto px-6 py-3 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-3">
          <img 
            src="/CRIMSON SCRIVENERS.webp" 
            alt="CSRF Logo" 
            className="h-8 w-8 rounded-sm object-cover"
          />
          <span className="font-bold text-lg tracking-tight">Crimsor Scriveners Readme Forger</span>
        </Link>
        <div className="flex items-center gap-3">
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
        </div>
      </div>
    </nav>
  );
};
