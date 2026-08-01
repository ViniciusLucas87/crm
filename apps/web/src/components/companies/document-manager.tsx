"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Download, Trash2, Pencil, Search, Upload, FileText, X, Check } from "lucide-react";

type Doc = {
  id: number; company_id: number; original_name: string; filename: string;
  file_size: number; mime_type: string; extension: string;
  created_at: string; uploaded_by?: string;
};

const EXT_ICONS: Record<string, string> = {
  ".pdf": "📄", ".doc": "📝", ".docx": "📝", ".xls": "📊", ".xlsx": "📊",
  ".csv": "📊", ".txt": "📄", ".png": "🖼️", ".jpeg": "🖼️", ".jpg": "🖼️",
  ".webp": "🖼️", ".zip": "📦",
};

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function DocumentManager({ companyId }: { companyId: number }) {
  const [docs, setDocs] = useState<Doc[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("newest");
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [renaming, setRenaming] = useState<number | null>(null);
  const [renameValue, setRenameValue] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchDocs = useCallback(async () => {
    try {
      setError("");
      const params = new URLSearchParams({ company_id: String(companyId), sort });
      if (search) params.set("search", search);
      const r = await fetch(`/api/documents?${params}`);
      if (!r.ok) throw new Error("Failed to load");
      const data = await r.json();
      setDocs(data.items || []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load documents");
    } finally {
      setLoading(false);
    }
  }, [companyId, search, sort]);

  useEffect(() => { fetchDocs(); }, [fetchDocs]);

  const handleUpload = async (file: File) => {
    setUploading(true);
    setUploadProgress(0);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const r = await fetch(`/api/documents?company_id=${companyId}`, {
        method: "POST", body: formData,
      });
      if (!r.ok) {
        const err = await r.json();
        throw new Error(err.detail || "Upload failed");
      }
      setUploadProgress(100);
      await fetchDocs();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleUpload(file);
  };

  const handleDownload = (doc: Doc) => {
    window.open(`/api/documents/${doc.id}/download`, "_blank");
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this document?")) return;
    try {
      await fetch(`/api/documents/${id}`, { method: "DELETE" });
      setDocs(prev => prev.filter(d => d.id !== id));
    } catch { setError("Delete failed"); }
  };

  const handleRename = async (id: number) => {
    if (!renameValue.trim()) return;
    try {
      await fetch(`/api/documents/${id}?name=${encodeURIComponent(renameValue.trim())}`, { method: "PATCH" });
      setDocs(prev => prev.map(d => d.id === id ? { ...d, original_name: renameValue.trim() } : d));
      setRenaming(null);
    } catch { setError("Rename failed"); }
  };

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-2">
        <Button variant="primary" size="sm" onClick={() => fileInputRef.current?.click()} disabled={uploading}>
          <Upload className="mr-1 h-3.5 w-3.5" />
          {uploading ? `Uploading ${uploadProgress}%...` : "Upload Document"}
        </Button>
        <input ref={fileInputRef} type="file" className="hidden"
          onChange={e => { const f = e.target.files?.[0]; if (f) handleUpload(f); }}
          accept=".pdf,.doc,.docx,.xls,.xlsx,.csv,.txt,.png,.jpeg,.jpg,.webp,.zip"
        />
        <div className="relative flex-1 min-w-[150px]">
          <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-500" />
          <input value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Search documents..." className="w-full rounded-lg border border-white/10 bg-slate-800/50 pl-8 pr-3 py-1.5 text-xs text-white placeholder:text-slate-600" />
        </div>
        <select value={sort} onChange={e => setSort(e.target.value)}
          className="rounded-lg border border-white/10 bg-slate-800/50 px-2 py-1.5 text-xs text-white">
          <option value="newest">Newest</option>
          <option value="oldest">Oldest</option>
          <option value="name">Name</option>
          <option value="size">Size</option>
        </select>
      </div>

      {/* Drag & drop zone */}
      <div
        className={`rounded-xl border-2 border-dashed p-6 text-center transition ${dragOver ? "border-cyan-400/50 bg-cyan-400/5" : "border-white/10 hover:border-white/20"}`}
        onDragOver={e => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
      >
        <Upload className="mx-auto h-6 w-6 text-slate-600 mb-1" />
        <p className="text-xs text-slate-500">Drag & drop a file here, or click Upload above</p>
      </div>

      {/* Error */}
      {error && <Card className="border-red-400/10 bg-red-400/5"><p className="text-sm text-red-400">{error}</p></Card>}

      {/* Loading */}
      {loading && <div className="space-y-2">{[1,2,3].map(i => <Skeleton key={i} className="h-14 rounded-xl" />)}</div>}

      {/* Empty */}
      {!loading && !error && docs.length === 0 && (
        <Card className="border-white/5 bg-slate-800/30 py-10 text-center">
          <FileText className="mx-auto h-8 w-8 text-slate-600 mb-2" />
          <p className="text-sm text-slate-400">No documents have been uploaded.</p>
          <p className="text-xs text-slate-500 mt-1">Store proposals, contracts, specifications, quotes and project files here.</p>
        </Card>
      )}

      {/* Document list */}
      {docs.length > 0 && (
        <div className="space-y-2">
          {docs.map(doc => (
            <Card key={doc.id} className="border-white/5 bg-slate-800/20 hover:bg-slate-800/30 transition flex items-center gap-3 p-3">
              <span className="text-xl shrink-0">{EXT_ICONS[doc.extension] || "📎"}</span>
              <div className="flex-1 min-w-0">
                {renaming === doc.id ? (
                  <div className="flex items-center gap-2">
                    <input value={renameValue} onChange={e => setRenameValue(e.target.value)}
                      className="flex-1 rounded border border-cyan-400/50 bg-slate-900 px-2 py-0.5 text-xs text-white"
                      onKeyDown={e => { if (e.key === "Enter") handleRename(doc.id); if (e.key === "Escape") setRenaming(null); }} />
                    <button onClick={() => handleRename(doc.id)} className="text-emerald-400"><Check className="h-3.5 w-3.5" /></button>
                    <button onClick={() => setRenaming(null)} className="text-slate-500"><X className="h-3.5 w-3.5" /></button>
                  </div>
                ) : (
                  <p className="text-sm text-white truncate font-medium">{doc.original_name}</p>
                )}
                <p className="text-xs text-slate-500 mt-0.5">
                  {formatSize(doc.file_size)} · {doc.extension} · {new Date(doc.created_at).toLocaleDateString()}
                  {doc.uploaded_by ? ` · ${doc.uploaded_by}` : ""}
                </p>
              </div>
              <div className="flex items-center gap-0.5 shrink-0">
                <button onClick={() => handleDownload(doc)} className="rounded p-1.5 text-slate-500 hover:text-cyan-400 hover:bg-white/5" title="Download"><Download className="h-3.5 w-3.5" /></button>
                <button onClick={() => { setRenaming(doc.id); setRenameValue(doc.original_name); }} className="rounded p-1.5 text-slate-500 hover:text-amber-400 hover:bg-white/5" title="Rename"><Pencil className="h-3.5 w-3.5" /></button>
                <button onClick={() => handleDelete(doc.id)} className="rounded p-1.5 text-slate-500 hover:text-red-400 hover:bg-white/5" title="Delete"><Trash2 className="h-3.5 w-3.5" /></button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
