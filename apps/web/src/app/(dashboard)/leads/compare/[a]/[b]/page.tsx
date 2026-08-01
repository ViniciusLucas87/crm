"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { TrendingUp } from "lucide-react";

type LeadFull = {
  id: number; name: string; industry: string | null; city: string | null;
  opportunity_score: number | null; confidence_score: number | null;
  estimated_deal_low: number | null; estimated_deal_high: number | null;
  buying_signals: string | null; technology_maturity: string | null;
  status: string; employees: number | null; executive_summary: string | null;
};

type CompareData = { a: LeadFull; b: LeadFull; comparison: { score_delta: number; winner: string } };

export default function ComparePage() {
  const params = useParams<{ a: string; b: string }>();
  const [data, setData] = useState<CompareData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!params.a || !params.b) return;
    fetch(`/api/leads/compare/${params.a}/${params.b}`)
      .then(r => r.json())
      .then(setData)
      .finally(() => setLoading(false));
  }, [params.a, params.b]);

  if (loading) return <div className="space-y-3">{Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-32 rounded-xl" />)}</div>;
  if (!data) return <Card><p className="text-red-400">Comparison data not available.</p></Card>;

  const fields = [
    { label: "Score", key: "opportunity_score", a: data.a.opportunity_score, b: data.b.opportunity_score },
    { label: "Confidence", key: "confidence_score", a: data.a.confidence_score, b: data.b.confidence_score },
    { label: "Est. Deal", key: "estimated_deal_low", a: data.a.estimated_deal_low, b: data.b.estimated_deal_low, fmt: (v: number | null) => v ? `$${v.toLocaleString()}` : "—" },
    { label: "Employees", key: "employees", a: data.a.employees, b: data.b.employees },
    { label: "Tech Maturity", key: "technology_maturity", a: data.a.technology_maturity, b: data.b.technology_maturity },
    { label: "Signals", key: "buying_signals", a: data.a.buying_signals ? "✓" : "—", b: data.b.buying_signals ? "✓" : "—" },
  ];

  const best = (aVal: unknown, bVal: unknown) => {
    if (aVal == null && bVal == null) return "none";
    if (aVal == null) return "b";
    if (bVal == null) return "a";
    if (typeof aVal === "number" && typeof bVal === "number") return aVal > bVal ? "a" : bVal > aVal ? "b" : "tie";
    return "none";
  };

  return (
    <div className="space-y-6">
      <Breadcrumbs items={[{ label: "Lead Intelligence", href: "/leads" }, { label: "Workspace", href: "/leads/workspace" }, { label: "Compare" }]} />
      <h2 className="text-lg font-semibold text-white">Company Comparison</h2>

      {/* Winner */}
      <Card className="border-cyan-400/10 bg-gradient-to-r from-cyan-400/5 to-emerald-400/5">
        <div className="flex items-center gap-3">
          <TrendingUp className="h-5 w-5 text-cyan-400" />
          <div>
            <p className="text-sm text-white"><strong className="text-cyan-300">{data.comparison.winner}</strong> scores higher by <strong>{Math.abs(data.comparison.score_delta)}</strong> points</p>
          </div>
        </div>
      </Card>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/5">
              <th className="py-3 pr-4 text-left text-xs text-slate-500">Metric</th>
              <th className="py-3 pr-4 text-left">
                <Link href={`/leads/${data.a.id}`} className="font-medium text-white hover:text-cyan-300">{data.a.name}</Link>
                <p className="text-xs text-slate-500">{data.a.industry} · {data.a.city}</p>
              </th>
              <th className="py-3 pr-4 text-left">
                <Link href={`/leads/${data.b.id}`} className="font-medium text-white hover:text-cyan-300">{data.b.name}</Link>
                <p className="text-xs text-slate-500">{data.b.industry} · {data.b.city}</p>
              </th>
            </tr>
          </thead>
          <tbody>
            {fields.map(f => {
              const winner = best(f.a, f.b);
              return (
                <tr key={f.key} className="border-b border-white/[0.02]">
                  <td className="py-3 pr-4 text-xs text-slate-500">{f.label}</td>
                  <td className={`py-3 pr-4 ${winner === "a" ? "text-emerald-400 font-medium" : "text-slate-300"}`}>
                    {f.fmt ? f.fmt(f.a as number | null) : (f.a ?? "—")}
                  </td>
                  <td className={`py-3 pr-4 ${winner === "b" ? "text-emerald-400 font-medium" : "text-slate-300"}`}>
                    {f.fmt ? f.fmt(f.b as number | null) : (f.b ?? "—")}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Summaries */}
      <div className="grid gap-4 sm:grid-cols-2">
        <Card>
          <p className="text-xs font-semibold text-slate-500 mb-2">{data.a.name}</p>
          <p className="text-xs text-slate-400">{data.a.executive_summary || "No executive summary available."}</p>
        </Card>
        <Card>
          <p className="text-xs font-semibold text-slate-500 mb-2">{data.b.name}</p>
          <p className="text-xs text-slate-400">{data.b.executive_summary || "No executive summary available."}</p>
        </Card>
      </div>
    </div>
  );
}
