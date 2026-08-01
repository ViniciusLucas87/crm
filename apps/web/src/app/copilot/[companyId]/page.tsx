"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import type { Route } from "next";
import {
  Brain, MessageSquare, Lightbulb, Target, AlertTriangle,
  CheckCircle, Building2, ChevronLeft, Sparkles, Radio,
} from "lucide-react";
import { Shell } from "@/components/dashboard/shell";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

type Alert = { level: string; message: string; detail: string | null };
type DiscoveryField = { field: string; status: string; value: string | null; confidence: number };
type CopilotData = {
  conversation_stage: string;
  discovery_progress: number;
  qualification_progress: number;
  pain_points: string[];
  buying_signals: string[];
  objections: string[];
  competitor_mentions: string[];
  suggested_question: string | null;
  suggested_product: string | null;
  suggested_case_study: string | null;
  suggested_next_step: string | null;
  current_strategy: string | null;
  alternative_strategy: string | null;
  estimated_deal_score: number;
  estimated_close_probability: number;
  budget_indicated: string | null;
  timeline_indicated: string | null;
  decision_maker_identified: boolean;
  missing_information: string[];
  alerts: Alert[];
  integration_opportunities: string[];
  discovery_fields: DiscoveryField[];
  company_context: Record<string, unknown> | null;
};

const STAGE_LABELS: Record<string, string> = {
  discovery: "Discovery", qualification: "Qualification",
  proposal: "Proposal", negotiation: "Negotiation", closing: "Closing",
};

const STATUS_COLORS: Record<string, string> = {
  known: "bg-emerald-400/20 text-emerald-400", verified: "bg-emerald-400/20 text-emerald-400",
  estimated: "bg-amber-400/20 text-amber-400", unknown: "bg-slate-400/20 text-slate-400",
};

const ALERT_ICONS: Record<string, typeof AlertTriangle> = {
  positive: CheckCircle, warning: AlertTriangle, critical: AlertTriangle, info: Lightbulb,
};
const ALERT_COLORS: Record<string, string> = {
  positive: "border-emerald-400/30 bg-emerald-400/5", warning: "border-amber-400/30 bg-amber-400/5",
  critical: "border-red-400/30 bg-red-400/5", info: "border-cyan-400/30 bg-cyan-400/5",
};

export default function CopilotPage() {
  const params = useParams<{ companyId: string }>();
  const companyId = Number(params.companyId);
  const [data, setData] = useState<CopilotData | null>(null);
  const [loading, setLoading] = useState(true);
  const [active, setActive] = useState(false);

  const analyze = useCallback(async () => {
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
      const r = await fetch(`${apiBase}/api/v1/copilot/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ company_id: companyId, transcript: "" }),
      });
      if (r.ok) setData(await r.json());
    } catch { /* silent */ }
  }, [companyId]);

  useEffect(() => { void analyze().then(() => setLoading(false)); }, [analyze]);

  // Auto-refresh every 15 seconds when active
  useEffect(() => {
    if (!active) return;
    const id = setInterval(analyze, 15000);
    return () => clearInterval(id);
  }, [active, analyze]);

  const companyName = (data?.company_context as Record<string, unknown>)?.name as string || `Company #${companyId}`;

  return (
    <Shell>
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href={`/companies/${companyId}` as Route} className="text-slate-400 hover:text-white">
              <ChevronLeft className="h-5 w-5" />
            </Link>
            <div className="rounded-xl bg-cyan-400/10 p-2">
              <Brain className="h-5 w-5 text-cyan-400" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-white">AI Sales Copilot</h2>
              <p className="text-xs text-slate-400">{companyName}</p>
            </div>
          </div>
          <button
            onClick={() => setActive(!active)}
            className={`flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-medium transition ${
              active ? "bg-emerald-400/20 text-emerald-400 border border-emerald-400/30" : "bg-white/5 text-slate-400 border border-white/10"
            }`}
          >
            <Radio className={`h-3 w-3 ${active ? "animate-pulse" : ""}`} />
            {active ? "Live" : "Paused"}
          </button>
        </div>

        {loading ? (
          <div className="grid gap-4 lg:grid-cols-3">
            <Skeleton className="h-96 rounded-2xl" />
            <Skeleton className="h-96 rounded-2xl" />
            <Skeleton className="h-96 rounded-2xl" />
          </div>
        ) : (
          <div className="grid gap-4 lg:grid-cols-3">
            {/* LEFT — Live Transcript */}
            <Card className="border-white/10 bg-slate-900/80">
              <div className="p-4">
                <div className="flex items-center gap-2 mb-3">
                  <MessageSquare className="h-4 w-4 text-slate-400" />
                  <h3 className="text-sm font-semibold text-white">Live Transcript</h3>
                </div>
                <div className="space-y-2">
                  <div className="rounded-lg bg-slate-800/50 p-3 border border-white/5">
                    <p className="text-xs text-slate-500 mb-1">00:00</p>
                    <p className="text-sm text-slate-300">
                      Transcript will appear here during live calls. Connect a call to begin real-time analysis.
                    </p>
                  </div>
                  <div className="text-center py-8">
                    <Sparkles className="h-8 w-8 text-slate-600 mx-auto mb-2" />
                    <p className="text-xs text-slate-500">Waiting for conversation to begin…</p>
                  </div>
                </div>
              </div>
            </Card>

            {/* CENTER — AI Coach */}
            <Card className="border-white/10 bg-slate-900/80">
              <div className="p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Brain className="h-4 w-4 text-cyan-400" />
                  <h3 className="text-sm font-semibold text-white">AI Coach</h3>
                  {data && (
                    <Badge variant="success" className="ml-auto text-[10px]">
                      {STAGE_LABELS[data.conversation_stage] || data.conversation_stage}
                    </Badge>
                  )}
                </div>

                {data ? (
                  <div className="space-y-4">
                    {/* Progress bars */}
                    <div className="space-y-2">
                      <div>
                        <div className="flex justify-between text-xs mb-1">
                          <span className="text-slate-400">Discovery</span>
                          <span className="text-cyan-400">{data.discovery_progress}%</span>
                        </div>
                        <div className="h-1.5 rounded-full bg-slate-800">
                          <div className="h-full rounded-full bg-cyan-400 transition-all" style={{ width: `${data.discovery_progress}%` }} />
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between text-xs mb-1">
                          <span className="text-slate-400">Qualification</span>
                          <span className="text-emerald-400">{data.qualification_progress}%</span>
                        </div>
                        <div className="h-1.5 rounded-full bg-slate-800">
                          <div className="h-full rounded-full bg-emerald-400 transition-all" style={{ width: `${data.qualification_progress}%` }} />
                        </div>
                      </div>
                    </div>

                    {/* Deal score */}
                    <div className="grid grid-cols-2 gap-2">
                      <div className="rounded-lg bg-slate-800/50 p-2 text-center">
                        <p className="text-[10px] text-slate-500 uppercase">Deal Score</p>
                        <p className="text-lg font-bold text-white">{data.estimated_deal_score}</p>
                      </div>
                      <div className="rounded-lg bg-slate-800/50 p-2 text-center">
                        <p className="text-[10px] text-slate-500 uppercase">Close Prob</p>
                        <p className="text-lg font-bold text-white">{data.estimated_close_probability}%</p>
                      </div>
                    </div>

                    {/* Recommended question */}
                    {data.suggested_question && (
                      <div className="rounded-lg border border-cyan-400/20 bg-cyan-400/5 p-3">
                        <p className="text-[10px] text-cyan-400 uppercase mb-1">Suggested Question</p>
                        <p className="text-sm text-white">{data.suggested_question}</p>
                      </div>
                    )}

                    {/* Strategy */}
                    {data.current_strategy && (
                      <div className="rounded-lg bg-slate-800/50 p-3">
                        <p className="text-[10px] text-slate-500 uppercase mb-1">Strategy</p>
                        <p className="text-xs text-slate-300">{data.current_strategy}</p>
                      </div>
                    )}

                    {/* Product rec */}
                    {data.suggested_product && (
                      <div className="rounded-lg bg-slate-800/50 p-3">
                        <p className="text-[10px] text-slate-500 uppercase mb-1">Recommended Product</p>
                        <p className="text-xs text-emerald-400">{data.suggested_product}</p>
                      </div>
                    )}

                    {/* Missing info */}
                    {data.missing_information.length > 0 && (
                      <div>
                        <p className="text-[10px] text-slate-500 uppercase mb-2">Missing Information</p>
                        <div className="space-y-1">
                          {data.missing_information.map((m, i) => (
                            <div key={i} className="flex items-center gap-2 text-xs text-amber-400">
                              <AlertTriangle className="h-3 w-3" />{m}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Signals */}
                    {data.buying_signals.length > 0 && (
                      <div>
                        <p className="text-[10px] text-slate-500 uppercase mb-1">Buying Signals</p>
                        <div className="flex flex-wrap gap-1">
                          {data.buying_signals.map((s, i) => (
                            <span key={i} className="rounded bg-emerald-400/10 px-2 py-0.5 text-[10px] text-emerald-400">{s}</span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Objections */}
                    {data.objections.length > 0 && (
                      <div>
                        <p className="text-[10px] text-slate-500 uppercase mb-1">Objections</p>
                        <div className="flex flex-wrap gap-1">
                          {data.objections.map((o, i) => (
                            <span key={i} className="rounded bg-red-400/10 px-2 py-0.5 text-[10px] text-red-400">{o}</span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Brain className="h-8 w-8 text-slate-600 mx-auto mb-2" />
                    <p className="text-xs text-slate-500">Analyzing context…</p>
                  </div>
                )}
              </div>
            </Card>

            {/* RIGHT — Company Intelligence */}
            <Card className="border-white/10 bg-slate-900/80">
              <div className="p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Building2 className="h-4 w-4 text-slate-400" />
                  <h3 className="text-sm font-semibold text-white">Company Intelligence</h3>
                </div>

                {data?.company_context ? (
                  <div className="space-y-3">
                    {(() => {
                      const ctx = data.company_context as Record<string, unknown>;
                      const items: React.ReactNode[] = [];
                      for (const [key, value] of Object.entries(ctx)) {
                        if (key === "primary_contact") continue;
                        if (!value || value === "None") continue;
                        items.push(
                          <div key={key} className="rounded-lg bg-slate-800/50 p-2">
                            <p className="text-[10px] text-slate-500 uppercase">{key.replace(/_/g, " ")}</p>
                            <p className="text-xs text-slate-300">{String(value)}</p>
                          </div>
                        );
                      }
                      return items;
                    })()}
                    {!!((data.company_context as Record<string, unknown>)?.primary_contact) && (
                      <div className="rounded-lg border border-cyan-400/20 bg-cyan-400/5 p-3">
                        <p className="text-[10px] text-cyan-400 uppercase mb-1">Primary Contact</p>
                        <p className="text-sm text-white">
                          {String(((data.company_context as Record<string, unknown>).primary_contact as Record<string, unknown>).name || "—")}
                        </p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Building2 className="h-8 w-8 text-slate-600 mx-auto mb-2" />
                    <p className="text-xs text-slate-500">No company data loaded</p>
                  </div>
                )}
              </div>
            </Card>
          </div>
        )}

        {/* Discovery fields */}
        {data?.discovery_fields && data.discovery_fields.length > 0 && (
          <Card className="border-white/10 bg-slate-900/80">
            <div className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <Target className="h-4 w-4 text-slate-400" />
                <h3 className="text-sm font-semibold text-white">Discovery Framework</h3>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-2">
                {data.discovery_fields.map((f) => (
                  <div key={f.field} className="rounded-lg bg-slate-800/50 p-2">
                    <p className="text-[10px] text-slate-500 capitalize mb-1">{f.field.replace(/_/g, " ")}</p>
                    <span className={`text-[10px] rounded px-1.5 py-0.5 ${STATUS_COLORS[f.status] || "text-slate-400"}`}>
                      {f.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        )}

        {/* Alerts */}
        {data?.alerts && data.alerts.length > 0 && (
          <div className="space-y-2">
            {data.alerts.map((a, i) => {
              const Icon = ALERT_ICONS[a.level] || Lightbulb;
              return (
                <div key={i} className={`flex items-start gap-3 rounded-xl border p-3 ${ALERT_COLORS[a.level] || ""}`}>
                  <Icon className="h-4 w-4 mt-0.5 shrink-0" />
                  <div>
                    <p className="text-sm text-white">{a.message}</p>
                    {a.detail && <p className="text-xs text-slate-400 mt-0.5">{a.detail}</p>}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </Shell>
  );
}
