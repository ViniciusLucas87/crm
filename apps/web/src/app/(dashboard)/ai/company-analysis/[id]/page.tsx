"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Sparkles, Shield, Target, AlertTriangle, Lightbulb, DollarSign, Users, TrendingUp } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { AiPageNav, AiPageError } from "@/components/ai/ai-page-nav";

type Section = { title: string; content: string; confidence: string; sources: string[] };
type Analysis = { companyName: string; businessSummary: Section; businessModel: Section; growthIndicators: Section; buyingSignals: Section; operationalChallenges: Section; softwareOpportunities: Section; decisionMakers: Section; recommendedServices: Section; estimatedBudget: Section; projectSize: Section; closingProbability: Section; conversationTopics: Section; discoveryQuestions: Section; risks: Section; nextAction: Section };

function SectionCard({ s, icon: Icon }: { s: Section; icon: typeof Sparkles }) {
  return (
    <Card>
      <div className="mb-2 flex items-center gap-2">
        <Icon className="h-3.5 w-3.5 text-cyan-400" />
        <p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-400">{s.title}</p>
        <Badge variant={s.confidence === "high" ? "success" : s.confidence === "medium" ? "warning" : "neutral"}>{s.confidence}</Badge>
      </div>
      <p className="text-sm text-slate-200 whitespace-pre-line">{s.content}</p>
      {s.sources.length > 0 && <p className="mt-2 text-[11px] text-slate-600">Sources: {s.sources.join(", ")}</p>}
    </Card>
  );
}

export default function CompanyAnalysisPage() {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [aiInsight, setAiInsight] = useState<string | null>(null);

  useEffect(() => {
    fetch(`/api/ai/analysis/${id}`).then(r => r.ok ? r.json() : Promise.reject(r.status)).then((d: Record<string, unknown>) => {
      const sec = (k: string): Section => {
        const s = (d[k] || {}) as Record<string, unknown>;
        return { title: s.title as string || "", content: s.content as string || "", confidence: s.confidence as string || "low", sources: s.sources as string[] || [] };
      };
      const analysis = {
        companyName: d.company_name as string,
        businessSummary: sec("business_summary"), businessModel: sec("business_model"), growthIndicators: sec("growth_indicators"),
        buyingSignals: sec("buying_signals"), operationalChallenges: sec("operational_challenges"), softwareOpportunities: sec("software_opportunities"),
        decisionMakers: sec("decision_makers"), recommendedServices: sec("recommended_services"), estimatedBudget: sec("estimated_budget"),
        projectSize: sec("project_size"), closingProbability: sec("closing_probability"), conversationTopics: sec("conversation_topics"),
        discoveryQuestions: sec("discovery_questions"), risks: sec("risks"), nextAction: sec("next_action"),
      };
      setData(analysis);
      // Fetch AI enrichment
      fetch("/api/ai/enrich/company_analysis", { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({ context: { name: analysis.companyName, summary: analysis.businessSummary.content, signals: analysis.buyingSignals.content, risks: analysis.risks.content, nextAction: analysis.nextAction.content } }) })
        .then(r => r.ok ? r.json() : null).then(d => { if (d?.enriched) setAiInsight(d.content); }).catch(() => {});
    }).catch(() => {}).finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="space-y-2"><AiPageNav companyId={id} pageTitle="Company Analysis" /><div className="space-y-2">{Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-24 rounded-xl" />)}</div></div>;
  if (!data) return <AiPageError message="Failed to load analysis. The company may not exist." companyId={id} />;

  return (
    <div className="space-y-6">
      <AiPageNav companyName={data.companyName} companyId={id} pageTitle="Company Analysis" />
      <div className="flex items-center gap-3">
        <div className="rounded-xl bg-cyan-400/15 p-2 text-cyan-300"><Sparkles className="h-5 w-5" /></div>
        <div><p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">AI Company Analysis</p><h2 className="text-lg font-semibold text-white">{data.companyName}</h2></div>
      </div>

      {/* AI Insight Banner */}
      {aiInsight && (
        <Card className="border-cyan-400/10 bg-gradient-to-r from-cyan-950/40 to-violet-950/20">
          <div className="flex items-start gap-3">
            <div className="mt-0.5 rounded-xl bg-cyan-400/15 p-1.5 text-cyan-300"><Sparkles className="h-4 w-4" /></div>
            <div><p className="text-xs font-semibold uppercase tracking-[0.1em] text-cyan-400">AI Strategic Assessment</p><p className="mt-1 text-sm text-slate-200 whitespace-pre-line">{aiInsight}</p></div>
          </div>
        </Card>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        <SectionCard s={data.businessSummary} icon={Sparkles} />
        <SectionCard s={data.businessModel} icon={Target} />
        <SectionCard s={data.growthIndicators} icon={TrendingUp} />
        <SectionCard s={data.buyingSignals} icon={TrendingUp} />
        <SectionCard s={data.operationalChallenges} icon={AlertTriangle} />
        <SectionCard s={data.softwareOpportunities} icon={Lightbulb} />
        <SectionCard s={data.decisionMakers} icon={Users} />
        <SectionCard s={data.recommendedServices} icon={Target} />
        <SectionCard s={data.estimatedBudget} icon={DollarSign} />
        <SectionCard s={data.closingProbability} icon={Shield} />
        <SectionCard s={data.projectSize} icon={Target} />
        <SectionCard s={data.risks} icon={AlertTriangle} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <SectionCard s={data.conversationTopics} icon={Lightbulb} />
        <SectionCard s={data.discoveryQuestions} icon={Target} />
      </div>

      <SectionCard s={data.nextAction} icon={Sparkles} />
    </div>
  );
}
