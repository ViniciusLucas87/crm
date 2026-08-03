"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import type { Route } from "next";
import { Search, ArrowRight, Building2, CheckCircle, XCircle, Archive, FlaskConical, Sparkles } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";

type Lead = {
  id: number; name: string; industry: string | null; status: string;
  opportunity_score: number | null; confidence_score: number | null;
  city: string | null; province: string | null;
  estimated_deal_low: number | null; estimated_deal_high: number | null;
  buying_signals: string | null; tags: string | null;
  technology_maturity: string | null; executive_summary: string | null;
  last_researched_at: string | null; created_at: string;
  enrichment_status?: string; pns_fit_score?: number | null;
};

const STATUSES = ["active", "all", "new", "researching", "ready_for_review", "needs_more_research", "approved", "rejected", "archived", "imported"];

export default function LeadWorkspacePage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("active");
  const [sort, setSort] = useState("score_desc");
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [page, setPage] = useState(1);
  const [pollingActive, setPollingActive] = useState(false);
  const [bulkBusy, setBulkBusy] = useState(false);
  const [bulkError, setBulkError] = useState("");
  const [bulkNotice, setBulkNotice] = useState("");

  const fetchLeads = useCallback(() => {
    const params = new URLSearchParams();
    if (status) params.set("status", status);
    if (search) params.set("search", search);
    params.set("sort", sort);
    params.set("page", String(page));
    params.set("page_size", "25");

    fetch(`/api/leads/?${params}`)
      .then(r => r.json())
      .then(d => {
        setLeads(d.items || []);
        setTotal(d.total || 0);
        // Check if any leads still have pending enrichment
        const hasPending = (d.items || []).some(
          (l: Lead) => l.enrichment_status === "pending" || l.enrichment_status === "processing" ||
            l.enrichment_status === "queued" || l.enrichment_status === "retrying"
        );
        setPollingActive(hasPending);
      })
      .finally(() => setLoading(false));
  }, [status, search, sort, page]);

  useEffect(() => { fetchLeads(); }, [fetchLeads]);

  // Smart polling: only when enrichments are pending, at 30s intervals
  useEffect(() => {
    if (!pollingActive) return;
    const id = setInterval(() => fetchLeads(), 30000);
    return () => clearInterval(id);
  }, [pollingActive, fetchLeads]);

  const toggleSelect = (id: number) => {
    const next = new Set(selected);
    if (next.has(id)) { next.delete(id); } else { next.add(id); }
    setSelected(next);
  };

  const toggleAll = () => {
    if (selected.size === leads.length) setSelected(new Set());
    else setSelected(new Set(leads.map(l => l.id)));
  };

  const bulkAction = async (action: string) => {
    setBulkBusy(true);
    setBulkError("");
    setBulkNotice("");
    const selectedCount = selected.size;
    try {
      const endpoint = action === "research" ? "/api/leads/research/bulk" : "/api/leads/bulk";
      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ids: Array.from(selected), action }),
      });
      if (!response.ok) throw new Error(`${action} failed (${response.status})`);
      setSelected(new Set());
      setBulkNotice(action === "archive" ? `${selectedCount} lead${selectedCount === 1 ? "" : "s"} archived.` : `${selectedCount} lead${selectedCount === 1 ? "" : "s"} updated.`);
      fetchLeads();
    } catch (error) {
      setBulkError(error instanceof Error ? error.message : `${action} failed. Please retry.`);
    } finally {
      setBulkBusy(false);
    }
  };

  const statusLabel = (s: string) => s.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());

  const enrichmentBadge = (l: Lead) => {
    const es = l.enrichment_status || "pending";
    if (es === "complete") return <Badge variant="success">🟢 Ready</Badge>;
    if (es === "processing") return <Badge variant="neutral">🔵 Processing</Badge>;
    if (es === "pending" || es === "queued") return <Badge variant="warning">🟡 Waiting</Badge>;
    if (es === "retrying") return <Badge variant="warning">🔄 Retry</Badge>;
    if (es === "failed") return <Badge variant="danger">🔴 Failed</Badge>;
    return <Badge variant="neutral">{es}</Badge>;
  };

  return (
    <div className="space-y-4">
      <Breadcrumbs items={[{ label: "Lead Intelligence", href: "/leads" }, { label: "Workspace" }]} />
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">Lead Workspace</h2>
        </div>
        <div className="flex gap-2">
          {selected.size > 0 && (
            <>
              <Button variant="primary" size="sm" onClick={() => bulkAction("approve")}><CheckCircle className="mr-1 h-3.5 w-3.5" />Approve ({selected.size})</Button>
              <Button variant="secondary" size="sm" onClick={() => bulkAction("reject")}><XCircle className="mr-1 h-3.5 w-3.5" />Reject</Button>
              <Button variant="secondary" size="sm" onClick={() => bulkAction("archive")}><Archive className="mr-1 h-3.5 w-3.5" />Archive</Button>
            </>
          )}
          <Button variant="secondary" size="sm" onClick={() => bulkAction("research")} disabled={selected.size === 0 || bulkBusy}>
            <FlaskConical className="mr-1 h-3.5 w-3.5" />{bulkBusy ? "Researching selected leads…" : "Research"}
          </Button>
        </div>
      </div>
      {bulkError && <p className="rounded-lg border border-red-400/20 bg-red-400/5 px-3 py-2 text-sm text-red-300">{bulkError}</p>}
      {bulkNotice && <p role="status" className="rounded-lg border border-emerald-400/20 bg-emerald-400/5 px-3 py-2 text-sm text-emerald-300">{bulkNotice}</p>}

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-500" />
          <input
            type="text" placeholder="Search leads..."
            value={search} onChange={e => { setSearch(e.target.value); setPage(1); }}
            className="w-full rounded-lg border border-white/10 bg-slate-800/50 py-2 pl-9 pr-3 text-sm text-white placeholder:text-slate-500 focus:border-cyan-400/50 focus:outline-none"
          />
        </div>
        <select value={status} onChange={e => { setStatus(e.target.value === "all" ? "" : e.target.value); setPage(1); }}
          className="rounded-lg border border-white/10 bg-slate-800/50 px-3 py-2 text-sm text-white focus:border-cyan-400/50 focus:outline-none">
          {STATUSES.map(s => <option key={s} value={s === "all" ? "" : s}>{s === "active" ? "Active Pipeline" : s === "all" ? "All Statuses" : statusLabel(s)}</option>)}
        </select>
        <select value={sort} onChange={e => setSort(e.target.value)}
          className="rounded-lg border border-white/10 bg-slate-800/50 px-3 py-2 text-sm text-white focus:border-cyan-400/50 focus:outline-none">
          <option value="score_desc">Score ↓</option>
          <option value="score_asc">Score ↑</option>
          <option value="pns_fit_desc">PNS Fit ↓</option>
          <option value="pns_fit_asc">PNS Fit ↑</option>
          <option value="created_at_desc">Newest</option>
          <option value="created_at_asc">Oldest</option>
          <option value="name_asc">Name A-Z</option>
        </select>
        <span className="text-xs text-slate-500">{total} leads</span>
      </div>

      {/* Table */}
      <Card className="overflow-hidden p-0">
        {loading ? (
          <div className="space-y-2 p-4">{Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-14 rounded-lg" />)}</div>
        ) : leads.length === 0 ? (
          <div className="py-12 text-center">
            <Building2 className="mx-auto h-8 w-8 text-slate-600" />
            <p className="mt-2 text-sm text-slate-500">No leads match your filters.</p>
            <Link href="/leads/discover" className="mt-2 inline-flex items-center gap-1 text-sm text-cyan-400"><Sparkles className="h-3.5 w-3.5" />Discover Companies</Link>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-white/5 text-left text-xs text-slate-500">
                    <th className="py-2 pl-4"><input type="checkbox" checked={selected.size === leads.length && leads.length > 0} onChange={toggleAll} className="rounded" /></th>
                    <th className="py-2 pr-4">Company</th>
                    <th className="py-2 pr-4">Score</th>
                    <th className="py-2 pr-4">Deal</th>
                    <th className="py-2 pr-4">Signals</th>
                    <th className="py-2 pr-4">Status</th>
                    <th className="py-2 pr-4">Intel</th>
                    <th className="py-2 pr-4">Tags</th>
                    <th className="py-2 pr-4"></th>
                  </tr>
                </thead>
                <tbody>
                  {leads.map(l => (
                    <tr key={l.id} className="border-b border-white/[0.02] transition hover:bg-white/[0.01]">
                      <td className="py-3 pl-4"><input type="checkbox" checked={selected.has(l.id)} onChange={() => toggleSelect(l.id)} className="rounded" /></td>
                      <td className="py-3 pr-4">
                        <Link href={`/leads/${l.id}` as Route} className="font-medium text-white hover:text-cyan-300">{l.name}</Link>
                        <p className="text-xs text-slate-500">{l.industry || "—"} {l.city ? `· ${l.city}` : ""}</p>
                      </td>
                      <td className="py-3 pr-4">
                        {l.opportunity_score != null ? <Badge variant={l.opportunity_score >= 70 ? "success" : l.opportunity_score >= 40 ? "warning" : "neutral"}>{l.opportunity_score}</Badge> : "—"}
                      </td>
                      <td className="py-3 pr-4 text-xs text-amber-400">{l.estimated_deal_low ? `$${l.estimated_deal_low.toLocaleString()}` : "—"}</td>
                      <td className="py-3 pr-4 text-xs text-slate-400">{l.buying_signals ? "✓" : "—"}</td>
                      <td className="py-3 pr-4"><Badge variant="neutral">{statusLabel(l.status)}</Badge></td>
                      <td className="py-3 pr-4">{enrichmentBadge(l)}</td>
                      <td className="py-3 pr-4 text-xs text-slate-500">{l.tags || "—"}</td>
                      <td className="py-3 pr-4"><Link href={`/leads/${l.id}` as Route}><ArrowRight className="h-4 w-4 text-slate-600 hover:text-cyan-400" /></Link></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {/* Pagination */}
            <div className="flex items-center justify-between border-t border-white/5 p-3 text-xs text-slate-500">
              <span>Showing {leads.length} of {total}</span>
              <div className="flex gap-1">
                <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className="rounded px-2 py-1 hover:bg-white/5 disabled:opacity-30">Prev</button>
                <button onClick={() => setPage(p => p + 1)} disabled={page * 25 >= total} className="rounded px-2 py-1 hover:bg-white/5 disabled:opacity-30">Next</button>
              </div>
            </div>
          </>
        )}
      </Card>
    </div>
  );
}
