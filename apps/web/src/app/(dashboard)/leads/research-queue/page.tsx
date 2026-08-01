"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import type { Route } from "next";
import { FlaskConical, Play, RefreshCw, AlertTriangle, ChevronRight } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";

type ResearchStage = { key: string; label: string; order: number; status: string; result?: string; error?: string };
type LeadResearch = { id: number; name: string; status: string; opportunity_score: number | null; research_stages: string | null };

const STAGE_LABELS: Record<string, string> = {
  website_analysis: "Website Analysis",
  business_analysis: "Business Analysis",
  industry_detection: "Industry Detection",
  technology_detection: "Technology Detection",
  buying_signals: "Buying Signal Detection",
  decision_makers: "Decision Maker Discovery",
  operational_challenges: "Operational Challenge Detection",
  opportunity_analysis: "AI Opportunity Analysis",
  recommended_services: "Recommended Services",
  opportunity_scoring: "Opportunity Scoring",
  confidence_scoring: "Confidence Scoring",
  executive_summary: "Executive Summary",
};

export default function ResearchQueuePage() {
  const [leads, setLeads] = useState<LeadResearch[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchQueue = useCallback(() => {
    setLoading(true);
    fetch("/api/leads/?status=researching&page_size=20")
      .then(r => r.json())
      .then(d => setLeads(d.items || []))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { fetchQueue(); }, [fetchQueue]);

  const parseStages = (raw: string | null): ResearchStage[] => {
    if (!raw) return [];
    try { return JSON.parse(raw); } catch { return []; }
  };

  const startResearch = async (id: number) => {
    await fetch(`/api/leads/${id}/research/start`, { method: "POST" });
    fetchQueue();
  };

  return (
    <div className="space-y-4">
      <Breadcrumbs items={[{ label: "Lead Intelligence", href: "/leads" }, { label: "Research Queue" }]} />
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">Research Queue</h2>
          <p className="text-sm text-slate-400">AI research pipeline progress for active leads.</p>
        </div>
        <Link href="/leads/workspace" className="text-xs text-slate-400 hover:text-cyan-300">← Workspace</Link>
      </div>

      {loading ? (
        <div className="space-y-3">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-32 rounded-xl" />)}</div>
      ) : leads.length === 0 ? (
        <Card className="border-cyan-400/10 bg-gradient-to-br from-cyan-400/5 to-purple-400/5">
          <div className="py-12 text-center">
            <FlaskConical className="mx-auto h-10 w-10 text-cyan-400" />
            <h3 className="mt-3 text-lg font-semibold text-white">No Active Research</h3>
            <p className="mt-1 text-sm text-slate-400 max-w-md mx-auto">
              Start AI research on leads from your workspace. Each lead progresses through a 12-stage enrichment pipeline.
            </p>
            <Link href="/leads/workspace" className="mt-4 inline-flex items-center gap-1 text-sm text-cyan-400">
              Go to Lead Workspace <ChevronRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </Card>
      ) : (
        <div className="space-y-4">
          {leads.map(lead => {
            const stages = parseStages(lead.research_stages);
            const completed = stages.filter(s => s.status === "complete").length;
            const running = stages.some(s => s.status === "running");
            const pct = stages.length ? Math.round(completed / stages.length * 100) : 0;

            return (
              <Card key={lead.id}>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <Link href={`/leads/${lead.id}` as Route} className="font-medium text-white hover:text-cyan-300">{lead.name}</Link>
                    {lead.opportunity_score != null && <Badge variant={lead.opportunity_score >= 70 ? "success" : "warning"}>{lead.opportunity_score}</Badge>}
                    {running && <Badge variant="neutral" className="animate-pulse">Running</Badge>}
                  </div>
                  <div className="flex gap-1">
                    <Button variant="secondary" size="sm" onClick={() => startResearch(lead.id)}><Play className="h-3 w-3" /></Button>
                    <Button variant="secondary" size="sm" onClick={() => fetchQueue()}><RefreshCw className="h-3 w-3" /></Button>
                  </div>
                </div>

                {/* Progress bar */}
                <div className="mt-3 mb-2">
                  <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
                    <span>{completed}/{stages.length} stages complete</span>
                    <span>{pct}%</span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-slate-800">
                    <div className="h-full rounded-full bg-gradient-to-r from-cyan-400 to-purple-400 transition-all" style={{ width: `${pct}%` }} />
                  </div>
                </div>

                {/* Stage list */}
                <div className="grid gap-1 sm:grid-cols-2 lg:grid-cols-3">
                  {stages.map(stage => (
                    <div key={stage.key} className="flex items-center gap-2 rounded px-2 py-1 text-xs">
                      <span className={
                        stage.status === "complete" ? "text-emerald-400" :
                        stage.status === "running" ? "text-cyan-400 animate-pulse" :
                        stage.status === "failed" ? "text-red-400" : "text-slate-600"
                      }>
                        {stage.status === "complete" ? "●" : stage.status === "running" ? "◉" : stage.status === "failed" ? "✕" : "○"}
                      </span>
                      <span className={stage.status === "failed" ? "text-red-300" : stage.status === "pending" ? "text-slate-500" : "text-slate-300"}>
                        {STAGE_LABELS[stage.key] || stage.label}
                      </span>
                      {stage.status === "failed" && stage.error && (
                        <span title={stage.error}><AlertTriangle className="h-3 w-3 text-red-400" /></span>
                      )}
                    </div>
                  ))}
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
