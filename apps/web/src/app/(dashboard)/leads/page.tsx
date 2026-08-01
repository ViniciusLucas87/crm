"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import type { Route } from "next";
import { Radar, TrendingUp, Search, Sparkles, ArrowRight, Building2, FlaskConical, Send, Download, Users } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";

type LeadStats = {
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

type Lead = {
  id: number; name: string; industry: string | null; status: string;
  opportunity_score: number | null; confidence_score: number | null;
  city: string | null; estimated_deal_low: number | null;
  buying_signals: string | null; tags: string | null;
  created_at: string;
};

const NAV_ITEMS = [
  { label: "Overview", href: "/leads", icon: Radar },
  { label: "Discover", href: "/leads/discover", icon: Search },
  { label: "Workspace", href: "/leads/workspace", icon: Building2 },
  { label: "Research Queue", href: "/leads/research-queue", icon: FlaskConical },
  { label: "Decision Makers", href: "/leads/decision-makers", icon: Users },
  { label: "Buying Signals", href: "/leads/buying-signals", icon: TrendingUp },
  { label: "Outreach", href: "/leads/outreach-queue", icon: Send },
  { label: "Import Review", href: "/leads/import-review", icon: Download },
  { label: "Analytics", href: "/leads/analytics", icon: TrendingUp },
];

export default function LeadIntelligenceHome() {
  const [stats, setStats] = useState<LeadStats | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch("/api/leads/stats/summary").then(r => r.json()),
      fetch("/api/leads/?page_size=8&sort=score_desc").then(r => r.json()),
    ]).then(([s, l]) => {
      setStats(s);
      setLeads((l.items || []) as Lead[]);
    }).finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">Lead Intelligence</p>
          <h2 className="mt-1 text-lg font-semibold text-white">AI Sales Research Platform</h2>
        </div>
        <div className="flex gap-2">
          <Link href="/leads/discover"><Button variant="secondary" size="sm"><Search className="mr-1 h-3.5 w-3.5" />Discover</Button></Link>
          <Link href="/leads/workspace"><Button variant="primary" size="sm">+ Add Lead</Button></Link>
        </div>
      </div>

      {/* Sub-nav */}
      <div className="flex gap-1 overflow-x-auto pb-1">
        {NAV_ITEMS.map(item => (
          <Link key={item.href} href={item.href as Route}
            className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs text-slate-400 transition hover:bg-white/5 hover:text-slate-200">
            <item.icon className="h-3.5 w-3.5" />{item.label}
          </Link>
        ))}
      </div>

      {loading ? (
        <div className="space-y-4">{Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-20 rounded-xl" />)}</div>
      ) : (
        <>
          {/* KPI Cards */}
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
            <Card><p className="text-xs text-slate-500">Total Leads</p><p className="mt-1 text-2xl font-bold text-white">{stats?.total || 0}</p></Card>
            <Card className="border-blue-400/20"><p className="text-xs text-slate-500">New</p><p className="mt-1 text-2xl font-bold text-blue-400">{stats?.by_status?.new || 0}</p></Card>
            <Card className="border-cyan-400/20"><p className="text-xs text-slate-500">Researching</p><p className="mt-1 text-2xl font-bold text-cyan-400">{stats?.by_status?.researching || 0}</p></Card>
            <Card className="border-emerald-400/20"><p className="text-xs text-slate-500">Approved</p><p className="mt-1 text-2xl font-bold text-emerald-400">{stats?.by_status?.approved || 0}</p></Card>
            <Card><p className="text-xs text-slate-500">Pipeline Value</p><p className="mt-1 text-2xl font-bold text-amber-400">${(stats?.estimated_pipeline_value || 0).toLocaleString()}</p></Card>
          </div>

          {/* Conversion Funnel */}
          {stats?.conversion && (
            <Card>
              <h4 className="mb-3 text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">Conversion Funnel</h4>
              <div className="flex items-center gap-2 text-xs">
                <div className="flex-1 rounded-lg bg-slate-800 p-2 text-center">
                  <p className="text-lg font-bold text-white">{stats.conversion.discovered}</p>
                  <p className="text-slate-500">Discovered</p>
                </div>
                <ArrowRight className="h-4 w-4 text-slate-600" />
                <div className="flex-1 rounded-lg bg-slate-800 p-2 text-center">
                  <p className="text-lg font-bold text-cyan-400">{stats.conversion.researched}</p>
                  <p className="text-slate-500">Researched</p>
                </div>
                <ArrowRight className="h-4 w-4 text-slate-600" />
                <div className="flex-1 rounded-lg bg-slate-800 p-2 text-center">
                  <p className="text-lg font-bold text-emerald-400">{stats.conversion.approved}</p>
                  <p className="text-slate-500">Approved</p>
                </div>
                <ArrowRight className="h-4 w-4 text-slate-600" />
                <div className="flex-1 rounded-lg bg-slate-800 p-2 text-center">
                  <p className="text-lg font-bold text-violet-400">{stats.conversion.imported}</p>
                  <p className="text-slate-500">Imported</p>
                </div>
              </div>
              <div className="mt-3 flex gap-4 text-xs text-slate-500">
                <span>Approval rate: <strong className="text-white">{stats.conversion.approval_rate}%</strong></span>
                <span>Import rate: <strong className="text-white">{stats.conversion.import_rate}%</strong></span>
                <span>Avg score: <strong className="text-white">{stats.avg_opportunity_score}</strong></span>
              </div>
            </Card>
          )}

          {/* Quick Actions */}
          <div className="grid gap-2 sm:grid-cols-4">
            <Link href="/leads/discover"><Card className="flex items-center gap-3 border-cyan-400/10 bg-cyan-400/5 p-4 transition hover:bg-cyan-400/10"><Sparkles className="h-5 w-5 text-cyan-400" /><div><p className="text-sm font-medium text-white">Discover</p><p className="text-xs text-slate-500">AI prospect search</p></div></Card></Link>
            <Link href="/leads/research-queue"><Card className="flex items-center gap-3 border-purple-400/10 bg-purple-400/5 p-4 transition hover:bg-purple-400/10"><FlaskConical className="h-5 w-5 text-purple-400" /><div><p className="text-sm font-medium text-white">Research Queue</p><p className="text-xs text-slate-500">{stats?.by_status?.researching || 0} in progress</p></div></Card></Link>
            <Link href="/leads/import-review"><Card className="flex items-center gap-3 border-emerald-400/10 bg-emerald-400/5 p-4 transition hover:bg-emerald-400/10"><Download className="h-5 w-5 text-emerald-400" /><div><p className="text-sm font-medium text-white">Import</p><p className="text-xs text-slate-500">{stats?.by_status?.approved || 0} ready</p></div></Card></Link>
            <Link href="/leads/outreach-queue"><Card className="flex items-center gap-3 border-amber-400/10 bg-amber-400/5 p-4 transition hover:bg-amber-400/10"><Send className="h-5 w-5 text-amber-400" /><div><p className="text-sm font-medium text-white">Outreach</p><p className="text-xs text-slate-500">Generate messages</p></div></Card></Link>
          </div>

          {/* Top Leads */}
          <Card>
            <div className="mb-3 flex items-center justify-between">
              <h4 className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">Top Opportunities</h4>
              <Link href="/leads/workspace" className="text-xs text-cyan-400">View all</Link>
            </div>
            {leads.length === 0 ? (
              <div className="py-8 text-center">
                <Building2 className="mx-auto h-8 w-8 text-slate-600" />
                <p className="mt-2 text-sm text-slate-500">No leads yet. Start discovering companies.</p>
                <Link href="/leads/discover" className="mt-3 inline-flex items-center gap-1 text-sm text-cyan-400"><Sparkles className="h-3.5 w-3.5" />Discover Companies</Link>
              </div>
            ) : (
              <div className="space-y-1">
                {leads.map(l => (
                  <Link key={l.id} href={`/leads/${l.id}` as Route} className="flex items-center justify-between rounded-lg border border-white/5 px-4 py-3 transition hover:bg-white/[0.02]">
                    <div>
                      <p className="text-sm font-medium text-white">{l.name}</p>
                      <p className="text-xs text-slate-500">{l.industry || "Unknown"} {l.city ? `· ${l.city}` : ""}</p>
                    </div>
                    <div className="flex items-center gap-3">
                      {l.estimated_deal_low != null && <span className="text-xs text-amber-400">${l.estimated_deal_low.toLocaleString()}</span>}
                      {l.opportunity_score != null && <Badge variant={l.opportunity_score >= 70 ? "success" : "warning"}>{l.opportunity_score}</Badge>}
                      <Badge variant="neutral">{l.status.replace(/_/g, " ")}</Badge>
                      <ArrowRight className="h-4 w-4 text-slate-600" />
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </Card>

          {/* Top Industries */}
          {stats?.top_industries && stats.top_industries.length > 0 && (
            <Card>
              <h4 className="mb-3 text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">Top Industries</h4>
              <div className="flex flex-wrap gap-2">
                {stats.top_industries.map((ind, i) => (
                  <Badge key={i} variant="neutral">{ind.industry} ({ind.count})</Badge>
                ))}
              </div>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
