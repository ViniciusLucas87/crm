"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import type { Route } from "next";
import { Users, Target, Shield, Wrench, BarChart3, Mail } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";

type Lead = {
  id: number; name: string; industry: string | null; city: string | null;
  opportunity_score: number | null; status: string;
  decision_makers_data: string | null;
};

type DM = {
  contact_id?: number; full_name?: string; job_title?: string;
  email?: string; phone?: string;
  role_fit_score?: number; influence_score?: number;
  accessibility_score?: number; executive_authority?: number;
  technical_authority?: number; operational_impact?: number;
  overall_priority?: number; role_category?: string;
  reasoning?: string[];
};

export default function DecisionMakersPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/leads/?page_size=50")
      .then(r => r.json())
      .then(d => setLeads(d.items || []))
      .finally(() => setLoading(false));
  }, []);

  const parseDMs = (raw: string | null): DM[] => {
    if (!raw) return [];
    try { return JSON.parse(raw); } catch { return []; }
  };

  const leadsWithDMs = leads.filter(l => l.decision_makers_data);

  return (
    <div className="space-y-4">
      <Breadcrumbs items={[{ label: "Lead Intelligence", href: "/leads" }, { label: "Decision Makers" }]} />
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">Decision Makers</h2>
          <p className="text-sm text-slate-400">Key contacts identified across your lead pipeline.</p>
        </div>
        <Link href="/leads/buying-signals" className="text-xs text-slate-400 hover:text-cyan-300">Buying Signals →</Link>
      </div>

      {loading ? (
        <div className="space-y-3">{Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-24 rounded-xl" />)}</div>
      ) : leadsWithDMs.length === 0 ? (
        <Card className="border-cyan-400/10 bg-gradient-to-br from-cyan-400/5 to-purple-400/5">
          <div className="py-12 text-center">
            <Users className="mx-auto h-10 w-10 text-cyan-400" />
            <h3 className="mt-3 text-lg font-semibold text-white">No Decision Makers Yet</h3>
            <p className="mt-1 text-sm text-slate-400 max-w-md mx-auto">
              Run the AI research pipeline on your leads to discover key decision makers, their roles, and influence levels.
            </p>
          </div>
        </Card>
      ) : (
        <div className="space-y-4">
          {leadsWithDMs.map(lead => {
            const dms = parseDMs(lead.decision_makers_data);
            if (!Array.isArray(dms) || dms.length === 0) return null;
            return dms.map((dm, i) => (
              <Card key={`${lead.id}-${i}`}>
                <div className="flex items-start justify-between">
                  <div>
                    <Link href={`/leads/${lead.id}` as Route} className="font-medium text-white hover:text-cyan-300">
                      {dm.full_name || "Unknown Contact"}
                    </Link>
                    <p className="text-xs text-slate-400">{dm.job_title || "Unknown Role"} · {lead.name}</p>
                    <p className="text-xs text-slate-500">{lead.industry} {lead.city ? `· ${lead.city}` : ""}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    {dm.overall_priority != null && (
                      <Badge variant={dm.overall_priority >= 80 ? "success" : dm.overall_priority >= 60 ? "warning" : "neutral"}>
                        Priority: {dm.overall_priority}
                      </Badge>
                    )}
                    <Badge variant="neutral">{dm.role_category || "unknown"}</Badge>
                  </div>
                </div>

                {/* Score breakdown */}
                <div className="mt-3 grid grid-cols-6 gap-2">
                  {[
                    { label: "Role Fit", value: dm.role_fit_score, icon: Target },
                    { label: "Influence", value: dm.influence_score, icon: BarChart3 },
                    { label: "Access", value: dm.accessibility_score, icon: Mail },
                    { label: "Exec Auth", value: dm.executive_authority, icon: Shield },
                    { label: "Tech Auth", value: dm.technical_authority, icon: Wrench },
                    { label: "Ops Impact", value: dm.operational_impact, icon: BarChart3 },
                  ].map(metric => (
                    <div key={metric.label} className="rounded-lg bg-slate-800/50 p-2 text-center">
                      <metric.icon className="mx-auto h-3 w-3 text-slate-500" />
                      <p className="mt-1 text-sm font-bold text-white">{metric.value ?? "—"}</p>
                      <p className="text-[10px] text-slate-500">{metric.label}</p>
                    </div>
                  ))}
                </div>
              </Card>
            ));
          })}
        </div>
      )}
    </div>
  );
}
