"use client";

import { useState } from "react";
import { Search, Sparkles, ChevronRight, Lightbulb } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import Link from "next/link";
import type { Route } from "next";

type Result = { companyId: number; companyName: string; industry: string | null; employees: number | null; opportunityScore: number | null; matchReasons: string[] };
type Response = { query: string; interpretedAs: string; results: Result[]; total: number; suggestion?: string };

const EXAMPLES = [
  "construction companies with high scores",
  "companies with no contacts",
  "growing companies",
  "needs inspection",
  "not researched",
];

export default function OpportunityExplorerPage() {
  const [query, setQuery] = useState("");
  const [data, setData] = useState<Response | null>(null);
  const [loading, setLoading] = useState(false);

  const search = async (q: string) => {
    setLoading(true); setQuery(q);
    const r = await fetch(`/api/ai/explorer?q=${encodeURIComponent(q)}`);
    const d = await r.json();
    setData({
      query: d.query, interpretedAs: d.interpreted_as, total: d.total,
      results: (d.results || []).map((r2: Record<string, unknown>) => ({
        companyId: r2.company_id as number, companyName: r2.company_name as string,
        industry: r2.industry as string | null, employees: r2.employees as number | null,
        opportunityScore: r2.opportunity_score as number | null,
        matchReasons: (r2.match_reasons as string[]) || [],
      })),
      suggestion: d.suggestion,
    });
    setLoading(false);
  };

  return (
    <div className="space-y-6">
      <Card className="border-cyan-400/10 bg-gradient-to-br from-cyan-950/40 to-slate-900/80 p-6">
        <div className="flex items-center gap-2 text-cyan-300"><Sparkles className="h-4 w-4" /><span className="text-xs font-semibold uppercase tracking-[0.12em]">AI Opportunity Explorer</span></div>
        <p className="mt-2 text-sm text-slate-400">Find prospects using natural language. Results include explanations of why each company matches.</p>
        <div className="mt-4 flex gap-2">
          <Input value={query} onChange={e => setQuery(e.target.value)} placeholder="e.g., construction companies with high opportunity scores" className="flex-1" onKeyDown={e => e.key === "Enter" && query.trim() && search(query.trim())} />
          <Button onClick={() => query.trim() && search(query.trim())} disabled={!query.trim()}><Search className="mr-1 h-3.5 w-3.5" />Search</Button>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          {EXAMPLES.map(ex => <button key={ex} onClick={() => search(ex)} className="rounded-full border border-white/10 px-3 py-1 text-xs text-slate-400 transition hover:border-cyan-400/30 hover:text-cyan-300">{ex}</button>)}
        </div>
      </Card>

      {loading && <div className="space-y-2">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-20 rounded-xl" />)}</div>}

      {data && !loading && (
        <>
          <p className="text-xs text-slate-500">Interpreted as: <span className="text-slate-300">{data.interpretedAs}</span> · {data.total} result{data.total !== 1 ? "s" : ""}</p>
          {data.results.length === 0 ? (
            <Card><div className="flex items-center gap-3"><Lightbulb className="h-5 w-5 text-amber-400" /><p className="text-sm text-slate-400">{data.suggestion || "No results found."}</p></div></Card>
          ) : (
            <div className="space-y-2">
              {data.results.map(r => (
                <Link key={r.companyId} href={`/companies/${r.companyId}` as Route} className="block">
                  <Card className="transition hover:border-cyan-400/20 hover:bg-white/[0.02]">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-medium text-white">{r.companyName}</p>
                        <p className="text-xs text-slate-400">{r.industry || "Unknown"} {r.employees ? `· ~${r.employees} employees` : ""}</p>
                        <div className="mt-2 flex flex-wrap gap-1">
                          {r.matchReasons.map((reason, i) => <Badge key={i} variant="neutral">{reason}</Badge>)}
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        {r.opportunityScore != null && <Badge variant={r.opportunityScore >= 70 ? "success" : "warning"}>{r.opportunityScore}</Badge>}
                        <ChevronRight className="h-4 w-4 text-slate-600" />
                      </div>
                    </div>
                  </Card>
                </Link>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
