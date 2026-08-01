"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Sparkles } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { AiPageNav } from "@/components/ai/ai-page-nav";
import { useTelephony } from "@/lib/telephony-context";
import { CallButton } from "@/components/companies/call-button";
import { LiveTranscript } from "@/components/transcription/live-transcript";
import { CopilotPanel } from "@/components/transcription/copilot-panel";
import type { Contact } from "@/lib/types";

type PreCall = {
  companyName: string; objectives: { goal: string; successCriteria: string }[];
  companySummary: string; buyingSignals: string; suggestedQuestions: string[];
  likelyObjections: { objection: string; response: string }[];
  talkingPoints: string[]; crossSelling: string[]; upselling: string[];
  successCriteria: string[];
};

type PostCall = {
  summary: string; tasks: { title: string; priority: string; due: string }[];
  timelineEvents: { type: string; subject: string }[];
  opportunityUpdates: string[]; followUpRecommendations: string[];
};

export default function CallAssistantPage() {
  const { id } = useParams<{ id: string }>();
  const [prep, setPrep] = useState<PreCall | null>(null);
  const [debrief, setDebrief] = useState<PostCall | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<"pre" | "post">("pre");
  const { call, startCall, transcription } = useTelephony();
  const [contacts, setContacts] = useState<Contact[]>([]);

  useEffect(() => {
    fetch(`/api/contacts?company_id=${id}&page_size=20`)
      .then(r => r.ok ? r.json() : null)
      .then(d => d?.items && setContacts(d.items))
      .catch(() => {});
  }, [id]);

  useEffect(() => {
    fetch(`/api/ai/call-prep/${id}`).then(r => r.ok ? r.json() : Promise.reject(r)).then((d: Record<string, unknown>) => setPrep({
      companyName: d.company_name as string,
      objectives: (d.objectives as Record<string, unknown>[] || []).map(o => ({ goal: o.goal as string, successCriteria: o.success_criteria as string })),
      companySummary: d.company_summary as string, buyingSignals: d.buying_signals as string,
      suggestedQuestions: d.suggested_questions as string[] || [],
      likelyObjections: (d.likely_objections as Record<string, unknown>[] || []).map(o => ({ objection: o.objection as string, response: o.response as string })),
      talkingPoints: d.talking_points as string[] || [], crossSelling: d.cross_selling as string[] || [],
      upselling: d.upselling as string[] || [], successCriteria: d.success_criteria as string[] || [],
    })).catch(() => {}).finally(() => setLoading(false));
  }, [id]);

  const handleDebrief = async () => {
    setLoading(true);
    const r = await fetch(`/api/ai/call-debrief/${id}`, { method: "POST" });
    const d = await r.json();
    setDebrief({
      summary: d.summary, tasks: d.tasks || [],
      timelineEvents: d.timeline_events || [], opportunityUpdates: d.opportunity_updates || [],
      followUpRecommendations: d.follow_up_recommendations || [],
    });
    setTab("post"); setLoading(false);
  };

  if (loading) return <div className="space-y-2"><AiPageNav companyId={id} pageTitle="Call Assistant" /><div className="space-y-2">{Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-20 rounded-xl" />)}</div></div>;

  return (
    <div className="space-y-6">
      <AiPageNav companyName={prep?.companyName} companyId={id} pageTitle="Call Assistant" />
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">AI Call Assistant</p>
          <h2 className="mt-1 text-lg font-semibold text-white">{prep?.companyName || "Company"}</h2>
        </div>
        <div className="flex gap-2 items-center">
          <CallButton companyId={Number(id)} callState={call.state} onCall={startCall} contacts={contacts} />
          <Button variant={tab === "pre" ? "primary" : "secondary"} onClick={() => setTab("pre")}>Pre-Call</Button>
          <Button variant={tab === "post" ? "primary" : "secondary"} onClick={handleDebrief}>Post-Call</Button>
        </div>
      </div>

      {/* Live call: transcript + coach */}
      {call.state !== "idle" && call.state !== "ended" && call.state !== "failed" && (
        <div className="grid gap-4 lg:grid-cols-2">
          <div className="grid gap-4" style={{ gridTemplateColumns: "minmax(0, 1fr) minmax(0, 1fr)" }}>
            <LiveTranscript state={transcription} onStop={() => {}} />
            <CopilotPanel callId={call.callId || Number(id)} isCallActive={true} segments={transcription.segments} preCall={prep ? {
              companyName: prep.companyName,
              companySummary: prep.companySummary,
              suggestedQuestions: prep.suggestedQuestions,
              talkingPoints: prep.talkingPoints,
              objectives: prep.objectives,
            } : undefined} contacts={contacts} />
          </div>
        </div>
      )}

      {tab === "pre" && prep && (
        <div className="space-y-4">
          <Card><p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-400">Company Summary</p><p className="mt-2 text-sm text-slate-200">{prep.companySummary}</p></Card>
          <Card><p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-400">Buying Signals</p><p className="mt-2 text-sm text-slate-200">{prep.buyingSignals}</p></Card>
          <Card>
            <p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-400">Call Objectives</p>
            <div className="mt-3 space-y-2">
              {prep.objectives.map((o, i) => (
                <div key={i} className="rounded-xl border border-white/5 bg-white/[0.01] p-3">
                  <p className="text-sm font-medium text-white">{o.goal}</p>
                  <p className="text-xs text-slate-400">{o.successCriteria}</p>
                </div>
              ))}
            </div>
          </Card>
          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-400">Suggested Questions</p>
              <ul className="mt-2 space-y-1">{prep.suggestedQuestions.map((q, i) => <li key={i} className="text-sm text-slate-300">• {q}</li>)}</ul>
            </Card>
            <Card>
              <p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-400">Likely Objections</p>
              <div className="mt-2 space-y-2">
                {prep.likelyObjections.map((o, i) => (
                  <div key={i} className="rounded-lg border border-amber-400/10 bg-amber-400/5 p-2">
                    <p className="text-xs font-medium text-amber-300">{o.objection}</p>
                    <p className="text-xs text-slate-400">{o.response}</p>
                  </div>
                ))}
              </div>
            </Card>
          </div>
          <Card>
            <p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-400">Talking Points</p>
            <ul className="mt-2 space-y-1">{prep.talkingPoints.map((t, i) => <li key={i} className="text-sm text-slate-300">• {t}</li>)}</ul>
          </Card>
          <div className="grid gap-4 lg:grid-cols-3">
            <Card><p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-400">Cross-Selling</p><ul className="mt-2 space-y-1">{prep.crossSelling.map((s, i) => <li key={i} className="text-sm text-slate-300">• {s}</li>)}</ul></Card>
            <Card><p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-400">Upselling</p><ul className="mt-2 space-y-1">{prep.upselling.map((s, i) => <li key={i} className="text-sm text-slate-300">• {s}</li>)}</ul></Card>
            <Card><p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-400">Success Criteria</p><ul className="mt-2 space-y-1">{prep.successCriteria.map((s, i) => <li key={i} className="text-sm text-slate-300">• {s}</li>)}</ul></Card>
          </div>
        </div>
      )}

      {tab === "post" && debrief && (
        <div className="space-y-4">
          <Card>
            <div className="flex items-center gap-2"><Sparkles className="h-4 w-4 text-cyan-400" /><p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-400">Call Summary</p></div>
            <p className="mt-2 text-sm text-slate-200">{debrief.summary}</p>
          </Card>
          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-400">Generated Tasks</p>
              <div className="mt-2 space-y-2">{debrief.tasks.map((t, i) => <div key={i} className="flex items-center gap-2 rounded-lg border border-white/5 p-2"><Badge variant={t.priority === "high" ? "danger" : "warning"}>{t.priority}</Badge><span className="text-sm text-slate-300">{t.title}</span></div>)}</div>
            </Card>
            <Card>
              <p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-400">Follow-up Recommendations</p>
              <ul className="mt-2 space-y-1">{debrief.followUpRecommendations.map((r, i) => <li key={i} className="text-sm text-slate-300">• {r}</li>)}</ul>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
