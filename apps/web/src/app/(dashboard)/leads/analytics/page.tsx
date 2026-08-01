"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";

type Stats = {
  total: number;
  by_status: Record<string, number>;
  avg_opportunity_score: number;
  avg_deal_size: number;
  estimated_pipeline_value: number;
  top_industries: { industry: string; count: number }[];
  conversion: {
    discovered: number; researched: number; approved: number;
    imported: number; rejected: number; import_rate: number; approval_rate: number;
  };
};

export default function AnalyticsPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/leads/stats/summary")
      .then(r => r.json())
      .then(setStats)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="space-y-3">{Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-24 rounded-xl" />)}</div>;

  const s = stats;
  if (!s) return null;

  const statusList = [
    { key: "new", label: "New", color: "bg-blue-400" },
    { key: "researching", label: "Researching", color: "bg-cyan-400" },
    { key: "ready_for_review", label: "Ready", color: "bg-amber-400" },
    { key: "needs_more_research", label: "Needs Research", color: "bg-orange-400" },
    { key: "approved", label: "Approved", color: "bg-emerald-400" },
    { key: "rejected", label: "Rejected", color: "bg-red-400" },
    { key: "imported", label: "Imported", color: "bg-violet-400" },
    { key: "archived", label: "Archived", color: "bg-slate-500" },
  ];

  return (
    <div className="space-y-6">
      <Breadcrumbs items={[{ label: "Lead Intelligence", href: "/leads" }, { label: "Analytics" }]} />
      <h2 className="text-lg font-semibold text-white">Lead Intelligence Analytics</h2>

      {/* KPI Row */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Card><p className="text-xs text-slate-500">Companies Discovered</p><p className="mt-1 text-2xl font-bold text-white">{s.total}</p></Card>
        <Card><p className="text-xs text-slate-500">Pipeline Value</p><p className="mt-1 text-2xl font-bold text-amber-400">${s.estimated_pipeline_value.toLocaleString()}</p></Card>
        <Card><p className="text-xs text-slate-500">Avg Opportunity Score</p><p className="mt-1 text-2xl font-bold text-emerald-400">{s.avg_opportunity_score}</p></Card>
        <Card><p className="text-xs text-slate-500">Avg Deal Size</p><p className="mt-1 text-2xl font-bold text-cyan-400">${s.avg_deal_size.toLocaleString()}</p></Card>
      </div>

      {/* Conversion Funnel */}
      <Card>
        <h4 className="mb-4 text-xs font-semibold uppercase tracking-[0.1em] text-slate-500">Conversion Funnel</h4>
        <div className="space-y-3">
          {[
            { label: "Discovered", value: s.conversion.discovered, pct: 100, color: "bg-slate-400" },
            { label: "Researched", value: s.conversion.researched, pct: s.total ? Math.round(s.conversion.researched / s.total * 100) : 0, color: "bg-cyan-400" },
            { label: "Approved", value: s.conversion.approved, pct: s.conversion.approval_rate, color: "bg-emerald-400" },
            { label: "Imported to CRM", value: s.conversion.imported, pct: s.conversion.import_rate, color: "bg-violet-400" },
          ].map(step => (
            <div key={step.label} className="flex items-center gap-3">
              <span className="w-24 text-xs text-slate-400">{step.label}</span>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <div className="h-6 rounded-full bg-slate-800 flex-1">
                    <div className={`h-full rounded-full ${step.color} transition-all`} style={{ width: `${step.pct}%` }} />
                  </div>
                  <span className="text-sm font-medium text-white w-12 text-right">{step.value}</span>
                  <span className="text-xs text-slate-500 w-10 text-right">{step.pct}%</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Status Distribution */}
      <div className="grid gap-4 sm:grid-cols-2">
        <Card>
          <h4 className="mb-3 text-xs font-semibold uppercase tracking-[0.1em] text-slate-500">By Status</h4>
          <div className="space-y-2">
            {statusList.filter(st => (s.by_status[st.key] || 0) > 0).map(st => {
              const count = s.by_status[st.key] || 0;
              const pct = s.total ? Math.round(count / s.total * 100) : 0;
              return (
                <div key={st.key} className="flex items-center gap-2">
                  <span className="w-20 text-xs text-slate-400">{st.label}</span>
                  <div className="h-4 flex-1 rounded-full bg-slate-800">
                    <div className={`h-full rounded-full ${st.color}`} style={{ width: `${pct}%` }} />
                  </div>
                  <span className="text-xs text-white w-8 text-right">{count}</span>
                </div>
              );
            })}
          </div>
        </Card>

        <Card>
          <h4 className="mb-3 text-xs font-semibold uppercase tracking-[0.1em] text-slate-500">Top Industries</h4>
          {s.top_industries.length === 0 ? (
            <p className="text-sm text-slate-500">No industry data yet.</p>
          ) : (
            <div className="space-y-2">
              {s.top_industries.map((ind, i) => (
                <div key={i} className="flex items-center justify-between">
                  <span className="text-sm text-slate-300">{ind.industry}</span>
                  <Badge variant="neutral">{ind.count}</Badge>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      {/* Key Metrics */}
      <Card>
        <h4 className="mb-3 text-xs font-semibold uppercase tracking-[0.1em] text-slate-500">Performance Metrics</h4>
        <div className="grid gap-4 sm:grid-cols-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-emerald-400">{s.conversion.approval_rate}%</p>
            <p className="text-xs text-slate-500">Approval Rate</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-violet-400">{s.conversion.import_rate}%</p>
            <p className="text-xs text-slate-500">Import Rate</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-amber-400">{s.avg_opportunity_score}</p>
            <p className="text-xs text-slate-500">Avg Score</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-cyan-400">${s.avg_deal_size.toLocaleString()}</p>
            <p className="text-xs text-slate-500">Avg Deal Size</p>
          </div>
        </div>
      </Card>
    </div>
  );
}
