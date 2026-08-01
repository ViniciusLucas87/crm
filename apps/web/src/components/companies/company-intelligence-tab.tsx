"use client";

import { useEffect, useState } from "react";
import { ShieldAlert, ChevronDown, ChevronUp, Target, DollarSign, Zap } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

type Props = { companyId: number };

type ScoreBreakdownItem = { ruleId: string; category: string; description: string; points: number };
type ScoreResult = {
  opportunityScore: number; confidenceScore: number; confidenceLevel: string; confidenceDetail: string[];
  scoreBreakdown: ScoreBreakdownItem[]; recommendedServices: string[]; serviceReason: string;
  estimatedValue: { tier: string; range: string }; nextAction: string;
};

export function CompanyIntelligenceTab({ companyId }: Props) {
  const [result, setResult] = useState<ScoreResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const calculateScore = async () => {
    setLoading(true); setError(null);
    try {
      const r = await fetch(`/api/scoring/${companyId}`, { method: "POST" });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const d = await r.json();
      setResult({
        opportunityScore: d.opportunity_score, confidenceScore: d.confidence_score,
        confidenceLevel: d.confidence_level, confidenceDetail: d.confidence_detail ?? [],
        scoreBreakdown: (d.score_breakdown ?? []).map((b: Record<string, unknown>) => ({ ruleId: b.rule_id, category: b.category, description: b.description, points: b.points })),
        recommendedServices: d.recommended_services ?? [], serviceReason: d.service_reason ?? "",
        estimatedValue: d.estimated_value ?? { tier: "Unknown", range: "N/A" }, nextAction: d.next_action ?? "",
      });
    } catch (e) { setError(e instanceof Error ? e.message : "Failed"); }
    finally { setLoading(false); }
  };

  useEffect(() => { calculateScore(); }, [companyId]); // eslint-disable-line

  if (loading) return <div className="space-y-2">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-20 rounded-xl" />)}</div>;
  if (error) return <Card><p className="text-sm text-red-400">{error}</p><Button variant="secondary" className="mt-3" onClick={calculateScore}>Retry</Button></Card>;
  if (!result) return null;

  const { opportunityScore, confidenceScore, confidenceLevel, confidenceDetail, scoreBreakdown, recommendedServices, serviceReason, estimatedValue, nextAction } = result;
  const scoreColor = opportunityScore >= 70 ? "text-emerald-400" : opportunityScore >= 50 ? "text-amber-400" : "text-slate-400";
  const scoreBg = opportunityScore >= 70 ? "border-emerald-400/20 bg-emerald-400/5" : opportunityScore >= 50 ? "border-amber-400/20 bg-amber-400/5" : "";
  const scoreLabel = opportunityScore >= 80 ? "High Priority" : opportunityScore >= 60 ? "Good Prospect" : opportunityScore >= 40 ? "Needs Research" : "Low Priority";

  return (
    <div className="space-y-6">
      <Card className={`flex items-center gap-6 ${scoreBg}`}>
        <div className="flex h-24 w-24 shrink-0 items-center justify-center rounded-2xl border border-white/10 bg-white/5">
          <span className={`text-4xl font-bold ${scoreColor}`}>{opportunityScore}</span>
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">Opportunity Score</p>
            <Badge variant={confidenceLevel === "High" ? "success" : confidenceLevel === "Medium" ? "warning" : "neutral"}>{confidenceLevel} confidence</Badge>
          </div>
          <p className="mt-1 text-lg font-semibold text-white">{scoreLabel}</p>
          <p className="text-sm text-slate-400">{scoreBreakdown.length} signal{scoreBreakdown.length !== 1 ? "s" : ""} &middot; {confidenceScore}% data confidence</p>
          <div className="mt-3 flex gap-2">
            <Button variant="secondary" onClick={() => setExpanded(!expanded)}>{expanded ? <ChevronUp className="mr-1 h-3 w-3" /> : <ChevronDown className="mr-1 h-3 w-3" />}{expanded ? "Hide" : "Show"} Breakdown</Button>
            <Button variant="secondary" onClick={calculateScore}>Recalculate</Button>
          </div>
        </div>
      </Card>

      {expanded && (
        <Card>
          <h4 className="mb-3 text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">Score Breakdown</h4>
          <div className="space-y-1">
            {scoreBreakdown.map((b, i) => (
              <div key={i} className="flex items-center justify-between rounded-lg px-3 py-2 text-sm transition hover:bg-white/[0.02]">
                <span className={b.points > 0 ? "text-emerald-300" : "text-red-300"}>{b.description}</span>
                <span className={`ml-2 shrink-0 rounded-md px-2 py-0.5 text-xs font-medium ${b.points > 0 ? "bg-emerald-400/10 text-emerald-400" : "bg-red-400/10 text-red-400"}`}>{b.points > 0 ? `+${b.points}` : b.points}</span>
              </div>
            ))}
            <div className="mt-2 border-t border-white/5 pt-2 flex justify-between px-3 text-sm font-semibold">
              <span className="text-slate-300">Total</span>
              <span className={scoreColor}>{opportunityScore} / 100</span>
            </div>
          </div>
        </Card>
      )}

      <Card>
        <h4 className="mb-2 text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">Confidence Assessment</h4>
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl border border-white/10 bg-white/5">
            <ShieldAlert className={`h-5 w-5 ${confidenceLevel === "High" ? "text-emerald-400" : confidenceLevel === "Medium" ? "text-amber-400" : "text-slate-400"}`} />
          </div>
          <div>
            <p className="font-medium text-white">{confidenceLevel} ({confidenceScore}%)</p>
            <div className="mt-1 flex flex-wrap gap-x-2 gap-y-0.5">
              {confidenceDetail.slice(1).map((d, i) => (
                <span key={i} className={`text-xs ${d.startsWith("✓") ? "text-emerald-400" : "text-slate-600"}`}>{d.replace("✓ ","").replace("✗ ","")}{d.startsWith("✓") ? "" : " ✗"}</span>
              ))}
            </div>
          </div>
        </div>
      </Card>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <div className="mb-3 inline-flex rounded-lg border border-white/10 bg-white/5 p-1.5 text-slate-400"><Target className="h-3.5 w-3.5" /></div>
          <p className="text-xs font-medium uppercase tracking-[0.08em] text-slate-500">Services</p>
          <ul className="mt-2 space-y-1">{recommendedServices.map(s => <li key={s} className="text-sm text-slate-200">• {s}</li>)}</ul>
          <p className="mt-2 text-xs text-slate-500">{serviceReason}</p>
        </Card>
        <Card>
          <div className="mb-3 inline-flex rounded-lg border border-white/10 bg-white/5 p-1.5 text-slate-400"><DollarSign className="h-3.5 w-3.5" /></div>
          <p className="text-xs font-medium uppercase tracking-[0.08em] text-slate-500">Value</p>
          <p className="mt-2 text-lg font-semibold text-white">{estimatedValue.tier}</p>
          <p className="text-sm text-slate-400">{estimatedValue.range}</p>
        </Card>
        <Card>
          <div className="mb-3 inline-flex rounded-lg border border-white/10 bg-white/5 p-1.5 text-slate-400"><Zap className="h-3.5 w-3.5" /></div>
          <p className="text-xs font-medium uppercase tracking-[0.08em] text-slate-500">Next Action</p>
          <p className="mt-2 text-sm font-medium text-cyan-300">{nextAction}</p>
        </Card>
      </div>
    </div>
  );
}
