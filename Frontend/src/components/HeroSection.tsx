import { FileText, ArrowDown } from "lucide-react";

export const HeroSection = () => {
  const scrollToUpload = () => {
    document.getElementById("upload")?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <section className="relative min-h-screen flex items-center justify-center px-4 border-b border-border/30">
      <div className="relative z-10 text-center max-w-3xl mx-auto">

        {/* Eyebrow */}
        <div className="inline-flex items-center gap-3 mb-8 px-4 py-2 border border-border/60 rounded-sm bg-secondary/30">
          <img 
            src="/CRIMSON SCRIVENERS.webp" 
            alt="CSRF" 
            className="h-5 w-5 rounded-sm"
          />
          <span className="text-sm text-muted-foreground tracking-widest uppercase font-semibold">
            Crimsor Scriveners Readme Forger
          </span>
        </div>

        {/* Headline */}
        <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold leading-tight tracking-tight mb-6">
          Transform Your README into{" "}
          <span className="text-foreground">Professional Reports</span>
        </h1>

        {/* Sub */}
        <p className="text-lg md:text-xl text-muted-foreground max-w-xl mx-auto mb-10">
          Upload any <code className="font-mono text-sm bg-secondary px-1.5 py-0.5 rounded">.md</code> file.
          Download a polished DOCX, PDF, or HTML report in seconds.
        </p>

        {/* CTA */}
        <button
          onClick={scrollToUpload}
          className="gradient-bg font-semibold text-base px-8 py-3.5 rounded-sm inline-flex items-center gap-2 border border-foreground/20"
        >
          Convert Now
          <ArrowDown className="h-4 w-4" />
        </button>
      </div>
    </section>
  );
};
