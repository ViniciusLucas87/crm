"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { Building2, Search, UserPlus, ClipboardList, Target, Phone, Radar } from "lucide-react";

type SearchResult = {
  id: number; type: string; title: string; subtitle: string; href: string;
};

export function GlobalSearch() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedIdx, setSelectedIdx] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if ((e.key === "k" && (e.metaKey || e.ctrlKey)) || e.key === "/") {
        e.preventDefault();
        setOpen((prev) => !prev);
      }
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, []);

  useEffect(() => {
    if (open) { inputRef.current?.focus(); setQuery(""); setResults([]); }
  }, [open]);

  useEffect(() => {
    if (query.length < 1) { setResults([]); return; }
    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const r = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        const d = await r.json();
        const mapped: SearchResult[] = [];
        (d.companies ?? []).forEach((c: Record<string, unknown>) => mapped.push({ id: c.id as number, type: "Company", title: c.name as string, subtitle: c.industry as string ?? "", href: `/companies/${c.id}` }));
        (d.contacts ?? []).forEach((c: Record<string, unknown>) => mapped.push({ id: c.id as number, type: "Contact", title: `${c.first_name} ${c.last_name}`, subtitle: c.email as string ?? "", href: `/companies/${c.company_id}` }));
        (d.tasks ?? []).forEach((t: Record<string, unknown>) => mapped.push({ id: t.id as number, type: "Task", title: t.title as string, subtitle: t.status as string ?? "", href: `/companies/${t.company_id}` }));
        (d.leads ?? []).forEach((l: Record<string, unknown>) => mapped.push({ id: l.id as number, type: "Lead", title: l.name as string, subtitle: `${l.industry ?? ""} · ${l.status ?? ""}`, href: `/leads/${l.id}` }));
        (d.opportunities ?? []).forEach((o: Record<string, unknown>) => mapped.push({ id: o.id as number, type: "Opportunity", title: o.title as string, subtitle: o.stage as string ?? "", href: `/companies/${o.company_id}` }));
        (d.signals ?? []).forEach((s: Record<string, unknown>) => mapped.push({ id: s.id as number, type: "Signal", title: s.title as string, subtitle: `${s.pain_type ?? ""} · score ${s.lead_score ?? 0}`, href: `/demand` }));
        (d.knowledge_facts ?? []).forEach((f: Record<string, unknown>) => mapped.push({ id: f.id as number, type: "Knowledge", title: `${f.key as string}: ${f.value as string}`, subtitle: `${f.entity_type as string} #${f.entity_id as number}`, href: `/knowledge` }));
        setResults(mapped.slice(0, 10));
      } catch {
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 200);
    return () => clearTimeout(timer);
  }, [query]);

  const goTo = useCallback((href: string) => {
    setOpen(false);
    window.open(href, "_blank", "noopener,noreferrer");
  }, []);

  const iconMap: Record<string, typeof Building2> = { Company: Building2, Contact: UserPlus, Task: ClipboardList, Opportunity: Target, Activity: Phone, Lead: Radar, Signal: Radar, Knowledge: Building2 };

  if (!open)
    return (
      <button onClick={() => setOpen(true)} className="flex items-center gap-2 rounded-xl border border-white/10 bg-slate-950/60 px-3 py-2 text-sm text-slate-500 transition hover:border-white/20 hover:text-slate-300" aria-label="Search (Ctrl+K)">
        <Search className="h-4 w-4" />
        <span className="hidden sm:inline">Search...</span>
        <kbd className="ml-auto hidden rounded-md border border-white/10 px-1.5 py-0.5 text-[10px] sm:inline">Ctrl+K</kbd>
      </button>
    );

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/60 pt-[15vh] backdrop-blur-sm">
      <div className="w-full max-w-lg rounded-2xl border border-white/10 bg-slate-950 shadow-2xl backdrop-blur-xl">
        <div className="flex items-center gap-3 border-b border-white/5 px-4 py-3">
          <Search className="h-4 w-4 text-slate-500" />
          <input
            ref={inputRef}
            className="flex-1 bg-transparent text-sm text-slate-100 outline-none placeholder:text-slate-500"
            placeholder="Search companies, leads, contacts, tasks..."
            value={query}
            onChange={(e) => { setQuery(e.target.value); setSelectedIdx(0); }}
            onKeyDown={(e) => {
              if (e.key === "ArrowDown") { e.preventDefault(); setSelectedIdx((i) => Math.min(i + 1, results.length - 1)); }
              if (e.key === "ArrowUp") { e.preventDefault(); setSelectedIdx((i) => Math.max(i - 1, 0)); }
              if (e.key === "Enter" && results[selectedIdx]) goTo(results[selectedIdx].href);
            }}
          />
          <kbd className="rounded-md border border-white/10 px-1.5 py-0.5 text-[10px] text-slate-600">ESC</kbd>
        </div>
        <div className="max-h-80 overflow-y-auto p-2">
          {loading && <p className="px-3 py-4 text-sm text-slate-500">Searching...</p>}
          {!loading && query && results.length === 0 && <p className="px-3 py-4 text-sm text-slate-500">No results found.</p>}
          {!loading && !query && <p className="px-3 py-4 text-sm text-slate-500">Type to search across companies, contacts, and tasks.</p>}
          {results.map((r, i) => {
            const Icon = iconMap[r.type] ?? Building2;
            return (
              <button
                key={`${r.type}-${r.id}`}
                className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm transition ${i === selectedIdx ? "bg-white/10 text-white" : "text-slate-400 hover:bg-white/5"}`}
                onClick={() => goTo(r.href)}
              >
                <Icon className="h-4 w-4 shrink-0" />
                <div className="min-w-0 flex-1">
                  <p className="truncate font-medium text-slate-200">{r.title}</p>
                  <p className="truncate text-xs text-slate-500">{r.subtitle}</p>
                </div>
                <span className="shrink-0 rounded-md border border-white/10 px-1.5 py-0.5 text-[10px] text-slate-600">{r.type}</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
