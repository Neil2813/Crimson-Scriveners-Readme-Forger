import { useCallback, useState, useRef } from "react";
import { Upload, X, FileText, Eye, Check } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { convertApi } from "@/lib/api";

interface UploadedFile {
  file: File;
  content: string;
}

// Mirror of backend SAFE_TABLE_COLORS — for display only
const TABLE_COLORS = [
  { key: "default",  label: "Default",  bg: "#111111", text: "#fff" },
  { key: "none",     label: "None",     bg: "#ffffff", text: "#111", border: true },
  { key: "slate",    label: "Slate",    bg: "#475569", text: "#fff" },
  { key: "stone",    label: "Stone",    bg: "#57534e", text: "#fff" },
  { key: "zinc",     label: "Zinc",     bg: "#52525b", text: "#fff" },
  { key: "steel",    label: "Steel",    bg: "#4b6070", text: "#fff" },
  { key: "sage",     label: "Sage",     bg: "#4a6741", text: "#fff" },
  { key: "ocean",    label: "Ocean",    bg: "#2d5f7a", text: "#fff" },
  { key: "dusk",     label: "Dusk",     bg: "#5b4d7a", text: "#fff" },
  { key: "wine",     label: "Wine",     bg: "#7a2d3e", text: "#fff" },
  { key: "cedar",    label: "Cedar",    bg: "#7a4a2d", text: "#fff" },
  { key: "teal",     label: "Teal",     bg: "#2d6b6b", text: "#fff" },
  { key: "graphite", label: "Graphite", bg: "#3d4451", text: "#fff" },
  { key: "forest",   label: "Forest",   bg: "#2d5a3d", text: "#fff" },
] as const;

type ColorKey = (typeof TABLE_COLORS)[number]["key"];

export const UploadSection = () => {
  const [uploadedFile, setUploadedFile] = useState<UploadedFile | null>(null);
  const [isConverting, setIsConverting]   = useState(false);
  const [isConverted, setIsConverted]     = useState(false);
  const [isDragging, setIsDragging]       = useState(false);
  const [htmlPreview, setHtmlPreview]     = useState<string | null>(null);
  const [showPreview, setShowPreview]     = useState(false);
  const [tableColor, setTableColor]       = useState<ColorKey>("default");
  const inputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  // ── File handling ──────────────────────────────────────────────────────────

  const handleFile = useCallback((file: File) => {
    if (!file.name.endsWith(".md")) {
      toast({ title: "Invalid file", description: "Please upload a .md file", variant: "destructive" });
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      toast({ title: "File too large", description: "Maximum file size is 5 MB", variant: "destructive" });
      return;
    }
    const reader = new FileReader();
    reader.onload = (e) => {
      setUploadedFile({ file, content: e.target?.result as string });
      setIsConverted(false);
      setHtmlPreview(null);
      setShowPreview(false);
      toast({ title: "File uploaded", description: `${file.name} ready for conversion` });
    };
    reader.readAsText(file);
  }, [toast]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }, [handleFile]);

  const removeFile = () => {
    setUploadedFile(null);
    setIsConverted(false);
    setHtmlPreview(null);
    setShowPreview(false);
  };

  // ── Conversion ─────────────────────────────────────────────────────────────

  const handleConvert = async () => {
    if (!uploadedFile) return;
    setIsConverting(true);
    try {
      const result = await convertApi.preview(uploadedFile.file, tableColor);
      setHtmlPreview(result.html_preview);
      setIsConverted(true);
      toast({
        title: "Conversion complete!",
        description: `"${result.document_model.title}" — ${result.document_model.sections.length} sections`,
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Conversion failed";
      toast({ title: "Conversion failed", description: msg, variant: "destructive" });
    } finally {
      setIsConverting(false);
    }
  };

  const handleDownload = async (downloadFormat: "pdf" | "docx") => {
    if (!uploadedFile) return;
    try {
      toast({ title: "Generating file…", description: `Building your ${downloadFormat.toUpperCase()}` });
      const { blob, filename } = await convertApi.download(uploadedFile.file, downloadFormat, tableColor);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
      toast({ title: "Download started", description: filename });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Download failed";
      toast({ title: "Download failed", description: msg, variant: "destructive" });
    }
  };

  const formatSize = (bytes: number) =>
    bytes < 1024 ? `${bytes} B` : `${(bytes / 1024).toFixed(1)} KB`;

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <section id="upload" className="min-h-screen flex items-center justify-center px-4 py-24 border-t border-border/30">
      <div className="w-full max-w-xl mx-auto">
        <div className="text-center mb-10">
          <h2 className="text-3xl md:text-4xl font-bold mb-3">Upload & Convert</h2>
          <p className="text-muted-foreground">Drop your markdown file and get a professional document</p>
        </div>

        <div className="glass-card p-8 space-y-6">

          {/* ── Drop Zone ──────────────────────────────────────────────── */}
          <div
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            onClick={() => inputRef.current?.click()}
            className={`relative cursor-pointer border-2 border-dashed rounded-sm p-10 text-center ${
              isDragging
                ? "border-foreground bg-secondary"
                : "border-border/60 hover:border-muted-foreground"
            }`}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".md"
              className="hidden"
              aria-label="Upload Markdown file"
              title="Upload a .md Markdown file"
              onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
            />
            <Upload className="mx-auto mb-3 h-9 w-9 text-muted-foreground" />
            <p className="text-foreground font-medium mb-1">Drag & drop your .md file here</p>
            <p className="text-sm text-muted-foreground">or click to browse — max 5 MB</p>
          </div>

          {/* ── File badge ─────────────────────────────────────────────── */}
          {uploadedFile && (
            <div className="flex items-center gap-3 bg-secondary rounded-sm p-4 border border-border/40">
              <FileText className="h-8 w-8 text-foreground shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{uploadedFile.file.name}</p>
                <p className="text-xs text-muted-foreground">{formatSize(uploadedFile.file.size)}</p>
              </div>
              <button
                onClick={(e) => { e.stopPropagation(); removeFile(); }}
                aria-label="Remove uploaded file"
                title="Remove uploaded file"
                className="p-1 rounded-sm border border-border/50 text-muted-foreground hover:text-destructive"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          )}

          {/* ── Table colour picker ────────────────────────────────────── */}
          {uploadedFile && (
            <div className="space-y-3">
              <div className="flex items-baseline justify-between">
                <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
                  Table Header Colour
                </p>
                <span className="text-xs text-muted-foreground font-mono">
                  {TABLE_COLORS.find(c => c.key === tableColor)?.label}
                </span>
              </div>

              {/* Colour swatch grid — 7 per row */}
              <div className="grid grid-cols-7 gap-1.5">
                {TABLE_COLORS.map((c) => (
                  <button
                    key={c.key}
                    title={c.label}
                    aria-label={`Table colour: ${c.label}`}
                    onClick={() => setTableColor(c.key)}
                    style={{ background: c.bg }}
                    className={`relative h-8 w-full rounded-sm flex items-center justify-center ${"border" in c ? "border border-border" : ""} ${
                      tableColor === c.key ? "ring-2 ring-offset-1 ring-foreground ring-offset-background" : ""
                    }`}
                  >
                    {tableColor === c.key && (
                      <Check
                        className={`h-3 w-3 ${c.key === "none" ? "text-zinc-900" : "text-white"}`}
                      />
                    )}
                  </button>
                ))}
              </div>

              {/* Colour label row */}
              <div className="grid grid-cols-7 gap-1.5">
                {TABLE_COLORS.map((c) => (
                  <p
                    key={c.key}
                    className="text-center text-muted-foreground font-mono text-[6.5px] leading-tight"
                  >
                    {c.label}
                  </p>
                ))}
              </div>
            </div>
          )}

          {/* ── Convert button ─────────────────────────────────────────── */}
          {uploadedFile && !isConverted && (
            <button
              onClick={handleConvert}
              disabled={isConverting}
              className="w-full gradient-bg font-semibold py-4 rounded-sm flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {isConverting ? (
                <>
                  <div className="h-4 w-4 border-2 border-background/40 border-t-background rounded-full animate-spin" />
                  Converting…
                </>
              ) : (
                "Convert Now"
              )}
            </button>
          )}

          {/* ── Download section ───────────────────────────────────────── */}
          {isConverted && (
            <div className="space-y-4">
              <p className="text-sm font-medium text-center text-muted-foreground">
                Conversion complete — choose your output
              </p>

              <button
                onClick={() => setShowPreview((v) => !v)}
                className="w-full flex items-center justify-center gap-2 py-3 rounded-sm border border-border/60 text-sm font-medium text-muted-foreground hover:text-foreground"
              >
                <Eye className="h-4 w-4" />
                {showPreview ? "Hide" : "Preview"} HTML Report
              </button>

              <div className="flex gap-3">
                <button
                  onClick={() => handleDownload("pdf")}
                  className="flex-1 gradient-bg font-semibold py-3.5 rounded-sm flex items-center justify-center gap-2"
                >
                  <FileText className="h-4 w-4" />
                  Download PDF
                </button>
                <button
                  onClick={() => handleDownload("docx")}
                  className="flex-1 gradient-bg font-semibold py-3.5 rounded-sm flex items-center justify-center gap-2"
                >
                  <FileText className="h-4 w-4" />
                  Download DOCX
                </button>
              </div>
            </div>
          )}

          {/* ── HTML Preview iframe ────────────────────────────────────── */}
          {showPreview && htmlPreview && (
            <div className="overflow-hidden border border-border/50 rounded-sm">
              <div className="flex items-center justify-between px-4 py-2 bg-secondary border-b border-border/40">
                <span className="text-xs font-medium text-muted-foreground font-mono uppercase tracking-wide">
                  Document Preview
                </span>
                <button
                  onClick={() => setShowPreview(false)}
                  className="text-xs text-muted-foreground hover:text-foreground"
                >
                  Close
                </button>
              </div>
              <iframe
                srcDoc={htmlPreview}
                className="w-full bg-white h-[520px] border-0"
                title="Document Preview"
                sandbox="allow-same-origin"
              />
            </div>
          )}

        </div>
      </div>
    </section>
  );
};
