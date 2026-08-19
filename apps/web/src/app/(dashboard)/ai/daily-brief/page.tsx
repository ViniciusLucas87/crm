"use client";

import { useEffect, useState } from "react";
import { Sparkles, Clock, AlertTriangle, Target, Lightbulb, ChevronRight, Zap, TrendingUp, ArrowRight } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import Link from "next/link";
import type { Route } from "next";

type BriefItem = { type: string; title: string; description: string; companyName?: string; companyId?: number; score?: number; reason?: string };
type DailyBrief = {
  greeting: string; date: string; summary: string;
  priorities: BriefItem[]; followUps: BriefItem[]; signals: BriefItem[];
  upcomingMeetings: BriefItem[]; overdueTasks: BriefItem[];
  topOpportunities: BriefItem[]; researchQueue: BriefItem[];
  actions: BriefItem[];
  outreach: { channel: string; total: number; contacted: number; ready: number; replies: number; needs_review: number }[];
  dataWarnings: BriefItem[];
};

function Section({ title, icon: Icon, items }: { title: string; icon: typeof Sparkles; items: BriefItem[]; empty?: string; color?: string }) {
  if (!items.length) return null;
  return (
    <Card>
      <div className="mb-3 inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.1em] text-slate-400">
        <Icon className="h-3.5 w-3.5" />{title}
      </div>
      <div className="space-y-2">
        {items.map((item, i) => (
          <div key={i} className="flex items-start justify-between gap-3 rounded-lg border border-white/5 bg-white/[0.01] px-4 py-3 transition hover:bg-white/[0.03]">
            <div className="min-w-0">
              <p className="text-sm font-medium text-white">{item.title}</p>
              <p className="mt-0.5 text-xs text-slate-400">{item.description}</p>
              {item.reason && <p className="mt-1 text-xs text-cyan-400/70">{item.reason}</p>}
            </div>
            {item.companyId ? (
              <Link href={`/companies/${item.companyId}` as Route} target="_blank" rel="noopener noreferrer" className="shrink-0 rounded-lg p-1.5 text-slate-600 transition hover:bg-white/5 hover:text-cyan-400">
                <ChevronRight className="h-4 w-4" />
              </Link>
            ) : item.score ? (
              <Badge variant={item.score >= 70 ? "success" : "warning"}>{item.score}</Badge>
            ) : null}
          </div>
        ))}
      </div>
    </Card>
  );
}

export default function DailyBriefPage() {
  const [brief, setBrief] = useState<DailyBrief | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [aiInsight, setAiInsight] = useState<string | null>(null);
  const [enriching, setEnriching] = useState(false);

  useEffect(() => {
    fetch("/api/ai/brief").then(r => r.ok ? r.json() : Promise.reject(r.status)).then((d: Record<string, unknown>) => {
      const b: DailyBrief = {
      greeting: d.greeting as string, date: d.date as string, summary: d.summary as string,
      priorities: (d.priorities as Record<string, unknown>[] || []).map(b => ({ type: b.type as string, title: b.title as string, description: b.description as string, companyName: b.company_name as string, companyId: b.company_id as number, score: b.score as number, reason: b.reason as string })),
      followUps: (d.follow_ups as Record<string, unknown>[] || []).map(b => ({ type: b.type as string, title: b.title as string, description: b.description as string, companyName: b.company_name as string, companyId: b.company_id as number })),
      signals: (d.signals as Record<string, unknown>[] || []).map(b => ({ type: b.type as string, title: b.title as string, description: b.description as string, companyName: b.company_name as string, companyId: b.company_id as number, score: b.score as number, reason: b.reason as string })),
      upcomingMeetings: (d.upcoming_meetings as Record<string, unknown>[] || []).map(b => ({ type: b.type as string, title: b.title as string, description: b.description as string, companyName: b.company_name as string, companyId: b.company_id as number })),
      overdueTasks: (d.overdue_tasks as Record<string, unknown>[] || []).map(b => ({ type: b.type as string, title: b.title as string, description: b.description as string, companyName: b.company_name as string, companyId: b.company_id as number })),
      topOpportunities: (d.top_opportunities as Record<string, unknown>[] || []).map(b => ({ type: b.type as string, title: b.title as string, description: b.description as string, companyName: b.company_name as string, companyId: b.company_id as number })),
      researchQueue: (d.research_queue as Record<string, unknown>[] || []).map(b => ({ type: b.type as string, title: b.title as string, description: b.description as string, companyName: b.company_name as string, companyId: b.company_id as number })),
      actions: (d.actions as Record<string, unknown>[] || []).map(b => ({ type: b.type as string, title: b.title as string, description: b.description as string, reason: b.reason as string })),
      outreach: (d.outreach as DailyBrief["outreach"]) || [],
      dataWarnings: (d.data_warnings as Record<string, unknown>[] || []).map(b => ({ type: b.type as string, title: b.title as string, description: b.description as string, reason: b.reason as string })),
      }; setBrief(b);
    }).catch(e => setError(String(e))).finally(() => setLoading(false));
  }, []);

  const generateAiInsight = async () => {
    if (!brief || enriching) return;
    setEnriching(true);
    try {
      const response = await fetch("/api/ai/enrich/daily_brief", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ context: {
          priorities: brief.priorities.slice(0, 3),
          signals: brief.signals.slice(0, 3),
          followUps: brief.followUps.slice(0, 2),
          overdueTasks: brief.overdueTasks.slice(0, 2),
        } }),
      });
      const data = response.ok ? await response.json() : null;
      if (data?.enriched) setAiInsight(data.content);
    } finally {
      setEnriching(false);
    }
  };

  if (loading) return <div className="space-y-4">{Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-24 rounded-xl" />)}</div>;
  if (error) return <Card><p className="text-red-400">{error}</p></Card>;
  if (!brief) return null;

  return (
    <div className="space-y-8">
      <Breadcrumbs items={[{ label: "AI Daily Brief" }]} />
      {/* Hero */}
      <section className="relative overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-cyan-950/60 via-slate-900/80 to-violet-950/40 p-6 md:p-8">
        <div className="relative z-10">
          <p className="text-sm font-medium text-cyan-300/80">{brief.greeting}</p>
          <p className="mt-1 text-xs text-slate-500">{brief.date}</p>
          <div className="mt-3 flex items-start gap-3">
            <div className="mt-1 rounded-xl bg-cyan-400/15 p-2 text-cyan-300"><Sparkles className="h-5 w-5" /></div>
            <p className="text-lg font-semibold text-white">{brief.summary}</p>
          </div>
        </div>
        <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-cyan-500/5 blur-3xl" />
      </section>

      {/* AI Insight Banner */}
      {!aiInsight && (
        <Card className="border-cyan-400/10 bg-gradient-to-r from-cyan-950/30 to-violet-950/10">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-sm font-medium text-white">AI Executive Brief</p>
              <p className="mt-0.5 text-xs text-slate-400">Uses DeepSeek only when you request it.</p>
            </div>
            <button
              type="button"
              onClick={generateAiInsight}
              disabled={enriching}
              className="rounded-lg bg-cyan-400 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {enriching ? "Generating..." : "Generate AI Brief"}
            </button>
          </div>
        </Card>
      )}
      {aiInsight && (
        <Card className="border-cyan-400/10 bg-gradient-to-r from-cyan-950/40 to-violet-950/20">
          <div className="flex items-start gap-3">
            <div className="mt-0.5 rounded-xl bg-cyan-400/15 p-1.5 text-cyan-300"><Sparkles className="h-4 w-4" /></div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.1em] text-cyan-400">AI Executive Brief</p>
              <p className="mt-1 text-sm text-slate-200 whitespace-pre-line">{aiInsight}</p>
            </div>
          </div>
        </Card>
      )}

      {/* Priorities */}
      <Card>
        <div className="mb-3 inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.1em] text-slate-400">
          <Target className="h-3.5 w-3.5" />Outreach tracked in CRM
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          {brief.outreach.map(channel => (
            <div key={channel.channel} className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
              <p className="font-medium capitalize text-white">{channel.channel}</p>
              <p className="mt-2 text-sm text-slate-300">{channel.contacted} contacted · {channel.ready} ready · {channel.replies} replies recorded</p>
            </div>
          ))}
        </div>
        <p className="mt-3 text-xs text-slate-500">Upwork requires a separate inbox check until an approved integration is connected.</p>
      </Card>

      <Section title="Data Checks" icon={AlertTriangle} items={brief.dataWarnings} />

      <Section title="Today's Priorities" icon={Target} items={brief.priorities} empty="No urgent priorities today." />

      {/* Signals + Follow-ups */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Section title="Buying Signals" icon={TrendingUp} items={brief.signals} empty="No new buying signals." color="emerald" />
        <Section title="Follow-ups" icon={Clock} items={brief.followUps} empty="No follow-ups needed." />
      </div>

      {/* Overdue + Meetings */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Section title="Overdue Tasks" icon={AlertTriangle} items={brief.overdueTasks} empty="No overdue tasks." color="red" />
        <Section title="Upcoming Meetings" icon={Zap} items={brief.upcomingMeetings} empty="No upcoming meetings." />
      </div>

      {/* Opportunities + Research */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Section title="Top Opportunities" icon={TrendingUp} items={brief.topOpportunities} empty="No open opportunities." color="amber" />
        <Section title="Research Queue" icon={Lightbulb} items={brief.researchQueue} empty="Research queue is clear." />
      </div>

      {/* Suggested Actions */}
      <Card>
        <div className="mb-3 inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.1em] text-slate-400">
          <ArrowRight className="h-3.5 w-3.5" />Suggested Actions
        </div>
        <div className="grid gap-2 sm:grid-cols-2">
          {brief.actions.map((a, i) => (
            <div key={i} className="flex items-start gap-3 rounded-xl border border-cyan-400/10 bg-cyan-400/5 px-4 py-3">
              <div className="mt-0.5 rounded-lg bg-cyan-400/15 p-1 text-cyan-400"><Lightbulb className="h-3.5 w-3.5" /></div>
              <div>
                <p className="text-sm font-medium text-white">{a.title}</p>
                <p className="text-xs text-slate-400">{a.description}</p>
                {a.reason && <p className="mt-0.5 text-xs text-cyan-400/60">{a.reason}</p>}
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
