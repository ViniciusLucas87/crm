"use client";

import { useState, useEffect, useCallback } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Sparkles, Target, TrendingUp } from "lucide-react";

type Intel = {
  executive_summary?: string;
  pns_fit_score?: number;
  opportunity_score?: number;
  buying_signals?: string;
  recommended_services?: string;
  technology_maturity?: string;
  revenue_estimate?: string;
};

export function CompanyAiSummaryTab({ companyId }: { companyId: number }) {
  const [intel, setIntel] = useState<Intel | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchIntel = useCallback(async () => {
    try {
      // Find the lead that was imported as this company
      const r = await fetch(`/api/leads/?imported_company_id=${companyId}&page_size=1`);
      const d = await r.json();
      const lead = d.items?.[0];
      if (lead) {
        setIntel({
          executive_summary: lead.executive_summary,
          pns_fit_score: lead.pns_fit_score,
          opportunity_score: lead.opportunity_score,
          buying_signals: lead.buying_signals,
          recommended_services: lead.recommended_services,
          technology_maturity: lead.technology_maturity,
          revenue_estimate: lead.revenue_estimate,
        });
      }
    } finally { setLoading(false); }
  }, [companyId]);

  useEffect(() => { fetchIntel(); }, [fetchIntel]);

  if (loading) return <div className="space-y-3">{[1,2,3].map(i => <Skeleton key={i} className="h-20 rounded-xl" />)}</div>;

  if (!intel || !intel.executive_summary) {
    return (
      <Card className="border-white/5 bg-slate-800/30 py-10 text-center">
        <Sparkles className="mx-auto h-8 w-8 text-slate-600 mb-2" />
        <p className="text-sm text-slate-400">No AI intelligence available.</p>
        <p className="text-xs text-slate-500 mt-1">AI research data will appear here after lead enrichment.</p>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Scores */}
      <div className="grid gap-3 sm:grid-cols-2">
        {intel.pns_fit_score != null && (
          <Card className="border-emerald-400/10 bg-emerald-400/5 p-4">
            <div className="flex items-center gap-2">
              <Target className="h-4 w-4 text-emerald-400" />
              <p className="text-xs text-slate-500">PNS Fit Score</p>
            </div>
            <p className="text-2xl font-bold text-white mt-1">{intel.pns_fit_score}/100</p>
          </Card>
        )}
        {intel.opportunity_score != null && (
          <Card className="border-cyan-400/10 bg-cyan-400/5 p-4">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-cyan-400" />
              <p className="text-xs text-slate-500">Opportunity Score</p>
            </div>
            <p className="text-2xl font-bold text-white mt-1">{intel.opportunity_score}/100</p>
          </Card>
        )}
      </div>

      {/* Executive Summary */}
      <Card className="border-white/5 bg-slate-800/20 p-4">
        <div className="flex items-center gap-2 mb-2">
          <Sparkles className="h-4 w-4 text-cyan-400" />
          <p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-400">Executive Summary</p>
        </div>
        <p className="text-sm text-slate-300 leading-relaxed">{intel.executive_summary}</p>
      </Card>

      {/* Details grid */}
      <div className="grid gap-3 sm:grid-cols-2">
        {intel.buying_signals && (
          <Card className="border-white/5 bg-slate-800/20 p-3">
            <p className="text-xs text-slate-500 mb-1">Buying Signals</p>
            <p className="text-xs text-slate-300">{intel.buying_signals}</p>
          </Card>
        )}
        {intel.recommended_services && (
          <Card className="border-white/5 bg-slate-800/20 p-3">
            <p className="text-xs text-slate-500 mb-1">Recommended Services</p>
            <p className="text-xs text-slate-300">{intel.recommended_services}</p>
          </Card>
        )}
        {intel.technology_maturity && (
          <Card className="border-white/5 bg-slate-800/20 p-3">
            <p className="text-xs text-slate-500 mb-1">Technology Maturity</p>
            <Badge variant={intel.technology_maturity === "low" ? "success" : intel.technology_maturity === "high" ? "warning" : "neutral"}>{intel.technology_maturity}</Badge>
          </Card>
        )}
        {intel.revenue_estimate && (
          <Card className="border-white/5 bg-slate-800/20 p-3">
            <p className="text-xs text-slate-500 mb-1">Revenue Estimate</p>
            <p className="text-xs text-amber-400">{intel.revenue_estimate}</p>
          </Card>
        )}
      </div>
    </div>
  );
}
