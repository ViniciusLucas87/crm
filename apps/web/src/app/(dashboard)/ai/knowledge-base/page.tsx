"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { BookOpen, CheckCircle, Database, FileText, Home, Lightbulb, Radar, Search, Shield, Sparkles } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";

type Category = { id: string; name: string; description: string; itemCount: number; status: string };
type PlaybookItem = { category: string; title: string; summary: string; content: string };

export default function KnowledgeBasePage() {
  const [data, setData] = useState<{ categories: Category[]; playbook: PlaybookItem[]; totalItems: number; readyForAi: boolean; message: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState("all");
  const [search, setSearch] = useState("");

  useEffect(() => {
    fetch("/api/ai/knowledge-base").then(r => r.ok ? r.json() : Promise.reject(r)).then((d: Record<string, unknown>) => {
      const ov = d.overview as Record<string, unknown>;
      setData({
        categories: (ov.categories as Record<string, unknown>[] || []).map(c => ({ id: c.id as string, name: c.name as string, description: c.description as string, itemCount: c.item_count as number, status: c.status as string })),
        playbook: (d.playbook || []) as PlaybookItem[],
        totalItems: ov.total_items as number,
        readyForAi: ov.ready_for_ai as boolean,
        message: ov.message as string,
      });
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="space-y-2">{Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-20 rounded-xl" />)}</div>;

  const visibleItems = (data?.playbook || []).filter(item => {
    const matchesCategory = category === "all" || item.category === category;
    const q = search.trim().toLowerCase();
    return matchesCategory && (!q || `${item.title} ${item.summary} ${item.content}`.toLowerCase().includes(q));
  });

  return (
    <div className="space-y-6">
      <Breadcrumbs items={[{ label: "CRM Home", href: "/" }, { label: "AI Knowledge Base" }]} />
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">AI Knowledge Base</p>
          <h2 className="mt-1 text-lg font-semibold text-white">PNS Sales & System Playbook</h2>
          <p className="mt-1 text-sm text-slate-400">Learn how we sell, contact leads, qualify opportunities, and use the CRM safely.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link href="/"><Button variant="secondary" size="sm"><Home className="mr-1 h-3.5 w-3.5" />CRM Home</Button></Link>
          <Link href="/leads"><Button variant="secondary" size="sm"><Radar className="mr-1 h-3.5 w-3.5" />Lead Intelligence</Button></Link>
          <Link href="/ai/explorer"><Button variant="secondary" size="sm"><Sparkles className="mr-1 h-3.5 w-3.5" />AI Explorer</Button></Link>
        </div>
      </div>

      {data && <Card className="border-cyan-400/10 bg-cyan-400/5"><div className="flex items-start gap-3"><Lightbulb className="mt-1 h-5 w-5 text-cyan-400" /><div><p className="text-sm font-medium text-white">Ready for the team and AI assistants</p><p className="mt-1 text-xs text-slate-400">{data.message}</p></div></div></Card>}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {(data?.categories || []).map(c => (
          <button key={c.id} onClick={() => setCategory(c.id)} className="text-left">
            <Card className={`h-full transition hover:border-cyan-400/30 ${category === c.id ? "border-cyan-400/40 bg-cyan-400/5" : ""}`}>
              <div className="mb-2 flex items-center gap-2">
                {c.id === "services" ? <Database className="h-4 w-4 text-cyan-400" /> : c.id === "pricing" || c.id === "technical" ? <Shield className="h-4 w-4 text-cyan-400" /> : c.id === "scripts" ? <FileText className="h-4 w-4 text-cyan-400" /> : <BookOpen className="h-4 w-4 text-cyan-400" />}
                <p className="text-sm font-medium text-white">{c.name}</p>
              </div>
              <p className="text-xs text-slate-400">{c.description}</p>
              <div className="mt-2 flex items-center gap-2"><Badge variant="success">Ready</Badge><span className="text-xs text-slate-600">{c.itemCount} items</span></div>
            </Card>
          </button>
        ))}
      </div>

      {data && <>
        <Card><div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <div className="relative flex-1"><Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" /><input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search scripts, objections, discovery questions..." className="w-full rounded-lg border border-white/10 bg-slate-800/50 py-2 pl-9 pr-3 text-sm text-white placeholder:text-slate-500 focus:border-cyan-400/50 focus:outline-none" /></div>
          <select value={category} onChange={e => setCategory(e.target.value)} className="rounded-lg border border-white/10 bg-slate-800 px-3 py-2 text-sm text-white"><option value="all">All topics</option>{data.categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select>
        </div></Card>

        <div className="space-y-3">
          {visibleItems.map(item => <Card key={`${item.category}-${item.title}`}><div className="flex items-start gap-3"><CheckCircle className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" /><div className="min-w-0"><div className="flex flex-wrap items-center gap-2"><h3 className="text-sm font-semibold text-white">{item.title}</h3><Badge variant="neutral">{data.categories.find(c => c.id === item.category)?.name || item.category}</Badge></div><p className="mt-1 text-sm text-cyan-100">{item.summary}</p><p className="mt-3 whitespace-pre-line text-sm leading-relaxed text-slate-400">{item.content}</p></div></div></Card>)}
          {visibleItems.length === 0 && <Card><p className="py-6 text-center text-sm text-slate-400">No playbook items match that search.</p></Card>}
        </div>

        <Card className="border-violet-400/10 bg-violet-400/5"><div className="flex items-start gap-3"><Shield className="mt-0.5 h-5 w-5 text-violet-300" /><div><p className="text-sm font-medium text-white">How the system uses this knowledge</p><p className="mt-1 text-xs leading-relaxed text-slate-400">PNS assistants use these approved principles when preparing research, outreach, call guidance, and proposals. Company-specific facts still come from CRM records and verified research. A person reviews communication before sending.</p></div></div></Card>
      </>}
    </div>
  );
}
