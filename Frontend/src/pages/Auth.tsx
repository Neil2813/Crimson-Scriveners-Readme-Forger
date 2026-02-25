import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Eye, EyeOff, FileText, ArrowLeft } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { Link, useNavigate } from "react-router-dom";
import { authApi } from "@/lib/api";

const Auth = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();
  const navigate = useNavigate();

  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isLogin && form.password !== form.confirmPassword) {
      toast({ title: "Passwords don't match", variant: "destructive" });
      return;
    }
    setIsLoading(true);
    try {
      if (isLogin) {
        await authApi.login(form.email, form.password);
        toast({ title: "Welcome back!", description: "Signed in successfully." });
      } else {
        await authApi.register(form.name, form.email, form.password);
        toast({ title: "Account created!", description: "You're now signed in." });
      }
      setTimeout(() => navigate("/"), 800);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Something went wrong";
      toast({ title: isLogin ? "Sign in failed" : "Registration failed", description: msg, variant: "destructive" });
    } finally {
      setIsLoading(false);
    }
  };


  const update = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((prev) => ({ ...prev, [field]: e.target.value }));

  return (
    <div className="min-h-screen flex bg-background">
      {/* Left: Branding */}
      <div className="hidden lg:flex flex-1 relative items-center justify-center overflow-hidden">
        {/* no decorative globs */}
        <div className="relative z-10 px-16 max-w-lg">
          <Link to="/" className="inline-flex items-center gap-2 mb-10 text-foreground hover:text-primary transition-colors">
            <ArrowLeft className="h-4 w-4" />
            Back to home
          </Link>
          <div className="flex items-center gap-4 mb-8">
            <img 
              src="/CRIMSON SCRIVENERS.webp" 
              alt="CSRF Logo" 
              className="h-10 w-10 rounded-sm object-cover shadow-sm bg-white"
            />
            <span className="text-2xl font-bold tracking-tight">Crimson Scriveners Readme Forger</span>
          </div>
          <h2 className="text-3xl font-bold mb-4">
            Create professional documents from your Markdown files
          </h2>
          <p className="text-muted-foreground text-lg">
            Upload, convert, and download — it's that simple. Join thousands of writers who trust Scriveners.
          </p>
          <div className="mt-12 glass-card p-6 max-w-xs">
            <div className="h-2 w-full rounded-sm bg-border mb-2" />
            <div className="h-2 w-3/4 rounded-sm bg-border/70 mb-2" />
            <div className="h-2 w-1/2 rounded-sm bg-border/50" />
          </div>
        </div>
      </div>

      {/* Right: Form */}
      <div className="flex-1 flex items-center justify-center p-6">
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-md"
        >
          <div className="lg:hidden mb-8">
            <Link to="/" className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors text-sm">
              <ArrowLeft className="h-4 w-4" /> Back
            </Link>
          </div>

          <div className="glass-card p-8">
            <AnimatePresence mode="wait">
              <motion.div
                key={isLogin ? "login" : "signup"}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.3 }}
              >
                <h2 className="text-2xl font-bold mb-1">{isLogin ? "Welcome back" : "Create account"}</h2>
                <p className="text-muted-foreground mb-8 text-sm">
                  {isLogin ? "Sign in to your account" : "Get started with CSRF"}
                </p>

                <form onSubmit={handleSubmit} className="space-y-4">
                  {!isLogin && (
                    <div>
                      <label className="text-sm font-medium text-muted-foreground mb-1.5 block">Name</label>
                      <input
                        type="text"
                        required
                        value={form.name}
                        onChange={update("name")}
                        className="w-full bg-secondary/60 border border-border/50 rounded-xl px-4 py-3 text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
                        placeholder="Your name"
                      />
                    </div>
                  )}
                  <div>
                    <label className="text-sm font-medium text-muted-foreground mb-1.5 block">Email</label>
                    <input
                      type="email"
                      required
                      value={form.email}
                      onChange={update("email")}
                      className="w-full bg-secondary/60 border border-border/50 rounded-xl px-4 py-3 text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
                      placeholder="you@example.com"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium text-muted-foreground mb-1.5 block">Password</label>
                    <div className="relative">
                      <input
                        type={showPassword ? "text" : "password"}
                        required
                        value={form.password}
                        onChange={update("password")}
                        className="w-full bg-secondary/60 border border-border/50 rounded-xl px-4 py-3 pr-12 text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
                        placeholder="••••••••"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                      >
                        {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                  </div>
                  {!isLogin && (
                    <div>
                      <label className="text-sm font-medium text-muted-foreground mb-1.5 block">Confirm Password</label>
                      <div className="relative">
                        <input
                          type={showConfirmPassword ? "text" : "password"}
                          required
                          value={form.confirmPassword}
                          onChange={update("confirmPassword")}
                          className="w-full bg-secondary/60 border border-border/50 rounded-xl px-4 py-3 pr-12 text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
                          placeholder="••••••••"
                        />
                        <button
                          type="button"
                          onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                          className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                        >
                          {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </button>
                      </div>
                    </div>
                  )}
                  {isLogin && (
                    <div className="text-right">
                      <button type="button" className="text-sm text-primary hover:text-primary/80 transition-colors">
                        Forgot password?
                      </button>
                    </div>
                  )}
                  <button
                    type="submit"
                    disabled={isLoading}
                    className="w-full gradient-bg text-primary-foreground font-semibold py-3.5 rounded-xl shadow-lg hover:shadow-xl hover:scale-[1.01] transition-all duration-300 disabled:opacity-70 disabled:scale-100 flex items-center justify-center gap-2 mt-2"
                  >
                    {isLoading ? (
                      <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
                        className="h-5 w-5 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full"
                      />
                    ) : (
                      isLogin ? "Sign In" : "Create Account"
                    )}
                  </button>
                </form>

                <p className="text-center text-sm text-muted-foreground mt-6">
                  {isLogin ? "Don't have an account? " : "Already have an account? "}
                  <button
                    onClick={() => { setIsLogin(!isLogin); setShowPassword(false); setShowConfirmPassword(false); }}
                    className="text-primary hover:text-primary/80 font-medium transition-colors"
                  >
                    {isLogin ? "Create one" : "Sign in"}
                  </button>
                </p>
              </motion.div>
            </AnimatePresence>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default Auth;
