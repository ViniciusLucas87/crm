"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import type { Route } from "next";
import { Sparkles, CheckCircle, XCircle, Download, FlaskConical, Clock, Send, Mail, Phone, MessageSquare, Lightbulb, Edit3, Save, TrendingUp, Shield, Zap, Target, Info } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { GoogleMapsCard } from "@/components/leads/google-maps-card";
import { ProductRecommendationCard } from "@/components/leads/product-recommendation-card";
import { WebsiteIntelCard, ReviewsIntelCard, LinkedInIntelCard } from "@/components/leads/provider-cards";

type LeadFull = {
  id: number; name: string; industry: string | null; website: string | null;
  employees: number | null; city: string | null; province: string | null;
  country: string | null; linkedin_url: string | null;
  description: string | null; revenue_estimate: string | null;
  opportunity_score: number | null; confidence_score: number | null;
  buying_signals: string | null; recommended_services: string | null;
  estimated_value: string | null;
  estimated_deal_low: number | null; estimated_deal_high: number | null;
  technology_maturity: string | null;
  status: string; source: string | null; tags: string | null;
  notes: string | null; executive_summary: string | null;
  research_stages: string | null;
  decision_makers_data: string | null;
  outreach_data: string | null;
  last_researched_at: string | null;
  imported_company_id: number | null;
  research_data: string | null;  // explainability JSON
  pns_fit_score: number | null;
  pns_fit_data: string | null;  // JSON: pns_fit_analysis + outreach_strategy
  enrichment_status?: string;
  google_maps_data?: string | null;
  product_recommendation_data?: string | null;
  website_data?: string | null;
  reviews_data?: string | null;
  linkedin_data?: string | null;
  created_at: string; updated_at: string;
};

type TimelineEvent = {
  id: number; event_type: string; description: string | null;
  metadata: Record<string, unknown> | null; created_at: string;
};

type ResearchStage = { key: string; label: string; order: number; status: string; result?: string; error?: string };

const STAGE_LABELS: Record<string, string> = {
  website_analysis: "Website Analysis", business_analysis: "Business Analysis",
  industry_detection: "Industry Detection", technology_detection: "Technology Detection",
  buying_signals: "Buying Signal Detection", decision_makers: "Decision Maker Discovery",
  operational_challenges: "Operational Challenge Detection",
  opportunity_analysis: "AI Opportunity Analysis", recommended_services: "Recommended Services",
  opportunity_scoring: "Opportunity Scoring", confidence_scoring: "Confidence Scoring",
  executive_summary: "Executive Summary",
};

type Tab = "overview" | "research" | "timeline" | "outreach" | "explainability";

export default function LeadDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [lead, setLead] = useState<LeadFull | null>(null);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<Tab>("overview");
  const [editingNotes, setEditingNotes] = useState(false);
  const [notesDraft, setNotesDraft] = useState("");

  const fetchLead = () => {
    setLoading(true);
    Promise.all([
      fetch(`/api/leads/${id}`).then(r => r.ok ? r.json() : Promise.reject(r)),
      fetch(`/api/leads/${id}/timeline`).then(r => r.ok ? r.json() : { events: [] }),
    ]).then(([l, t]) => {
      setLead(l);
      setTimeline(t.events || []);
      setNotesDraft(l.notes || "");
    }).finally(() => setLoading(false));
  };
  useEffect(() => { fetchLead(); }, [id]); // eslint-disable-line react-hooks/exhaustive-deps

  const updateStatus = async (status: string) => {
    await fetch(`/api/leads/${id}/status?status=${status}`, { method: "POST" });
    fetchLead();
  };

  const importLead = async () => {
    const r = await fetch(`/api/leads/${id}/import`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ create_company: true, create_opportunity: false }),
    });
    const d = await r.json();
    if (d.company_id) {
      alert(`Imported as Company #${d.company_id}`);
      fetchLead();
    } else {
      alert(d.detail || d.error || "Import failed");
    }
  };

  const startResearch = async () => {
    await fetch(`/api/leads/${id}/research/run-all`, { method: "POST" });
    fetchLead();
  };

  const generateOutreach = async () => {
    await fetch(`/api/leads/${id}/outreach/generate`, { method: "POST" });
    fetchLead();
  };

  const saveNotes = async () => {
    await fetch(`/api/leads/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ notes: notesDraft }),
    });
    setEditingNotes(false);
    fetchLead();
  };

  const parseStages = (raw: string | null): ResearchStage[] => {
    if (!raw) return [];
    try { return JSON.parse(raw); } catch { return []; }
  };

  const parseOutreach = (raw: string | null): Record<string, unknown> | null => {
    if (!raw) return null;
    try { return JSON.parse(raw); } catch { return null; }
  };

  const statusLabel = (s: string) => s.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());

  if (loading) return <div className="space-y-2">{Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-20 rounded-xl" />)}</div>;
  if (!lead) return <Card><p className="text-red-400">Lead not found.</p></Card>;

  return (
    <div className="space-y-6">
      {/* Breadcrumbs */}
      <div className="flex items-center gap-2 text-xs text-slate-500">
        <Link href="/leads" className="hover:text-cyan-300">Lead Intelligence</Link>
        <span>/</span>
        <Link href="/leads/workspace" className="hover:text-cyan-300">Workspace</Link>
        <span>/</span>
        <span className="text-slate-300">{lead.name}</span>
      </div>

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Badge variant="neutral">{statusLabel(lead.status)}</Badge>
            {lead.source && <Badge variant="neutral">{lead.source}</Badge>}
            {lead.tags && lead.tags.split(",").map(t => <Badge key={t.trim()} variant="neutral">{t.trim()}</Badge>)}
          </div>
          <h2 className="mt-1 text-xl font-semibold text-white">{lead.name}</h2>
          <p className="text-sm text-slate-400">
            {lead.industry || "Unknown industry"}
            {lead.city ? ` · ${lead.city}, ${lead.province || ""}` : ""}
            {lead.country ? `, ${lead.country}` : ""}
            {lead.employees ? ` · ~${lead.employees} employees` : ""}
          </p>
          {lead.website && <a href={lead.website} target="_blank" rel="noopener noreferrer" className="text-xs text-cyan-400 hover:underline">{lead.website}</a>}
        </div>
        <div className="flex gap-2">
          {lead.status === "approved" && !lead.imported_company_id && (
            <Button variant="primary" onClick={importLead}><Download className="mr-1 h-3.5 w-3.5" />Import to CRM</Button>
          )}
          {["new", "needs_more_research", "ready_for_review"].includes(lead.status) && (
            <>
              <Button variant="primary" onClick={() => updateStatus("approved")}><CheckCircle className="mr-1 h-3.5 w-3.5" />Approve</Button>
              <Button variant="secondary" onClick={() => updateStatus("rejected")}><XCircle className="mr-1 h-3.5 w-3.5" />Reject</Button>
            </>
          )}
          {(lead.status === "new" || lead.status === "ready_for_review") && (
            <Button variant="secondary" onClick={startResearch}><FlaskConical className="mr-1 h-3.5 w-3.5" />Research</Button>
          )}
          {lead.status === "approved" && !lead.outreach_data && (
            <Button variant="secondary" onClick={generateOutreach}><Send className="mr-1 h-3.5 w-3.5" />Generate Outreach</Button>
          )}
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid gap-3 sm:grid-cols-5">
        <Card><p className="text-xs text-slate-500">Score</p><p className="mt-1 text-xl font-bold text-white">{lead.opportunity_score ?? "—"}</p></Card>
        <Card><p className="text-xs text-slate-500">Confidence</p><p className="mt-1 text-xl font-bold text-white">{lead.confidence_score ? `${lead.confidence_score}%` : "—"}</p></Card>
        <Card><p className="text-xs text-slate-500">Est. Deal</p><p className="mt-1 text-xl font-bold text-amber-400">{lead.estimated_deal_low ? `$${lead.estimated_deal_low.toLocaleString()}` : lead.estimated_value || "—"}</p></Card>
        <Card><p className="text-xs text-slate-500">Tech Maturity</p><p className="mt-1 text-lg font-bold text-white">{lead.technology_maturity || "—"}</p></Card>
        <Card><p className="text-xs text-slate-500">Revenue</p><p className="mt-1 text-lg font-bold text-white">{lead.revenue_estimate || "—"}</p></Card>
      </div>

      {/* PNS ICP Fit */}
      <PNSFitCard pnsFitScore={lead.pns_fit_score} pnsFitData={lead.pns_fit_data} />

      {/* Google Maps Intelligence */}
      <GoogleMapsCard data={lead.google_maps_data} />

      {/* Product Recommendation */}
      <ProductRecommendationCard data={lead.product_recommendation_data} />

      {/* Website Intelligence */}
      <WebsiteIntelCard data={lead.website_data} />

      {/* Google Reviews Intelligence */}
      <ReviewsIntelCard data={lead.reviews_data} />

      {/* LinkedIn Intelligence */}
      <LinkedInIntelCard data={lead.linkedin_data} />

      {/* Research Provenance */}
      <Card className="border-cyan-400/10 bg-gradient-to-r from-cyan-400/5 to-purple-400/5">
        <div className="flex items-center gap-2 mb-2">
          <Sparkles className="h-4 w-4 text-cyan-400" />
          <p className="text-xs font-semibold uppercase tracking-[0.1em] text-cyan-300">Research Provenance</p>
        </div>
        <div className="grid gap-2 sm:grid-cols-4 text-xs">
          <div>
            <span className="text-slate-500">Source: </span>
            <span className="text-slate-300">{lead.source === "ai_discovery" ? "AI Discovery Engine" : lead.source || "Manual"}</span>
          </div>
          <div>
            <span className="text-slate-500">Provider: </span>
            <span className="text-slate-300">DeepSeek (deepseek-chat)</span>
          </div>
          <div>
            <span className="text-slate-500">Researched: </span>
            <span className="text-slate-300">{lead.last_researched_at ? new Date(lead.last_researched_at).toLocaleString() : "Pending"}</span>
          </div>
          <div>
            <span className="text-slate-500">Confidence: </span>
            <span className="text-slate-300">{lead.confidence_score ? `${lead.confidence_score}%` : "N/A"}</span>
          </div>
        </div>
      </Card>

      {/* Imported badge */}
      {lead.imported_company_id && (
        <Card className="border-emerald-400/10 bg-emerald-400/5">
          <p className="text-sm text-emerald-400">✅ Imported to CRM as <Link href={`/companies/${lead.imported_company_id}` as Route} className="underline">Company #{lead.imported_company_id}</Link></p>
        </Card>
      )}

      {/* Executive Summary */}
      {lead.executive_summary && (
        <Card className="border-cyan-400/10 bg-gradient-to-r from-cyan-400/5 to-purple-400/5">
          <div className="flex items-center gap-2 mb-2"><Sparkles className="h-4 w-4 text-cyan-400" /><p className="text-xs font-semibold uppercase tracking-[0.1em] text-cyan-300">AI Executive Summary</p></div>
          <p className="text-sm text-slate-300 leading-relaxed">{lead.executive_summary}</p>
        </Card>
      )}

      {/* Tabs */}
      <div className="flex gap-1 border-b border-white/5">
        {(["overview", "research", "timeline", "outreach", "explainability"] as Tab[]).map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm transition ${tab === t ? "border-b-2 border-cyan-400 text-white" : "text-slate-500 hover:text-slate-300"}`}>
            {t === "overview" ? "Overview" : t === "research" ? "Research Pipeline" : t === "timeline" ? "Timeline" : t === "outreach" ? "Outreach" : "Explainability"}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {tab === "overview" && (
        <div className="space-y-4">
          {lead.description && <Card><p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-500 mb-2">Description</p><p className="text-sm text-slate-300">{lead.description}</p></Card>}
          {lead.buying_signals && <Card><p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-500 mb-2">Buying Signals</p><p className="text-sm text-slate-300">{lead.buying_signals}</p></Card>}
          {lead.recommended_services && <Card><p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-500 mb-2">Recommended Services</p><p className="text-sm text-slate-300">{lead.recommended_services}</p></Card>}

          {/* Notes */}
          <Card>
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-500">Notes</p>
              {!editingNotes ? (
                <button onClick={() => setEditingNotes(true)} className="text-xs text-slate-500 hover:text-cyan-400"><Edit3 className="h-3 w-3" /></button>
              ) : (
                <button onClick={saveNotes} className="text-xs text-cyan-400"><Save className="h-3 w-3" /></button>
              )}
            </div>
            {editingNotes ? (
              <textarea value={notesDraft} onChange={e => setNotesDraft(e.target.value)}
                className="w-full rounded-lg border border-white/10 bg-slate-800/50 p-3 text-sm text-white focus:border-cyan-400/50 focus:outline-none min-h-[100px]" />
            ) : (
              <p className="text-sm text-slate-300">{lead.notes || "No notes yet."}</p>
            )}
          </Card>
        </div>
      )}

      {tab === "research" && (
        <div className="space-y-4">
          {!lead.research_stages ? (
            <Card className="border-cyan-400/10 bg-gradient-to-br from-cyan-400/5 to-purple-400/5">
              <div className="py-8 text-center">
                <FlaskConical className="mx-auto h-8 w-8 text-cyan-400" />
                <p className="mt-2 text-sm text-slate-400">Research pipeline not started.</p>
                <Button variant="primary" className="mt-3" onClick={startResearch}>Start Research</Button>
              </div>
            </Card>
          ) : (
            parseStages(lead.research_stages).map(stage => (
              <Card key={stage.key}>
                <div className="flex items-center gap-3">
                  <span className={
                    stage.status === "complete" ? "text-emerald-400" :
                    stage.status === "running" ? "text-cyan-400 animate-pulse" :
                    stage.status === "failed" ? "text-red-400" : "text-slate-600"
                  }>
                    {stage.status === "complete" ? "✓" : stage.status === "running" ? "◉" : stage.status === "failed" ? "✕" : "○"}
                  </span>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-white">{STAGE_LABELS[stage.key] || stage.label}</p>
                    {stage.result && <p className="text-xs text-slate-400 mt-0.5">{stage.result}</p>}
                    {stage.error && <p className="text-xs text-red-400 mt-0.5">{stage.error}</p>}
                  </div>
                  <Badge variant={stage.status === "complete" ? "success" : stage.status === "failed" ? "warning" : "neutral"}>
                    {stage.status}
                  </Badge>
                </div>
              </Card>
            ))
          )}
        </div>
      )}

      {tab === "timeline" && (
        <div className="space-y-2">
          {timeline.length === 0 ? (
            <Card><div className="py-8 text-center"><Clock className="mx-auto h-8 w-8 text-slate-600" /><p className="mt-2 text-sm text-slate-500">No timeline events yet.</p></div></Card>
          ) : (
            <div className="relative border-l border-white/10 pl-6 space-y-4 ml-2">
              {timeline.map(event => (
                <div key={event.id} className="relative">
                  <div className="absolute -left-[25px] mt-1 h-2.5 w-2.5 rounded-full bg-cyan-400" />
                  <div>
                    <p className="text-sm text-slate-300">{event.description || event.event_type}</p>
                    <p className="text-xs text-slate-500">
                      {event.event_type.replace(/_/g, " ")} · {new Date(event.created_at).toLocaleString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {tab === "outreach" && (
        <div className="space-y-4">
          {!lead.outreach_data ? (
            <Card className="border-cyan-400/10 bg-gradient-to-br from-cyan-400/5 to-purple-400/5">
              <div className="py-8 text-center">
                <Send className="mx-auto h-8 w-8 text-cyan-400" />
                <p className="mt-2 text-sm text-slate-400">No outreach content generated yet.</p>
                <Button variant="primary" className="mt-3" onClick={generateOutreach}>Generate Outreach</Button>
              </div>
            </Card>
          ) : (
            (() => {
              const o = parseOutreach(lead.outreach_data);
              if (!o) return null;
              return (
                <>
                  {o.cold_email && (
                    <Card>
                      <div className="flex items-center gap-2 mb-2"><Mail className="h-4 w-4 text-cyan-400" /><p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-500">Cold Email</p></div>
                      <pre className="whitespace-pre-wrap text-sm text-slate-300 font-sans">{o.cold_email as string}</pre>
                    </Card>
                  )}
                  {o.linkedin_message && (
                    <Card>
                      <div className="flex items-center gap-2 mb-2"><MessageSquare className="h-4 w-4 text-blue-400" /><p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-500">LinkedIn Message</p></div>
                      <p className="text-sm text-slate-300">{o.linkedin_message as string}</p>
                    </Card>
                  )}
                  {o.cold_call_script && (
                    <Card>
                      <div className="flex items-center gap-2 mb-2"><Phone className="h-4 w-4 text-amber-400" /><p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-500">Cold Call Script</p></div>
                      <p className="text-sm text-slate-300">{o.cold_call_script as string}</p>
                    </Card>
                  )}
                  {Array.isArray(o.discovery_questions) && (o.discovery_questions as string[]).length > 0 && (
                    <Card>
                      <div className="flex items-center gap-2 mb-2"><Lightbulb className="h-4 w-4 text-purple-400" /><p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-500">Discovery Questions</p></div>
                      <ul className="space-y-1">{(o.discovery_questions as string[]).map((q: string, i: number) => <li key={i} className="text-sm text-slate-300">• {q}</li>)}</ul>
                    </Card>
                  )}
                </>
              );
            })()
          )}
        </div>
      )}

      {tab === "explainability" && (
        <ExplainabilityPanel researchData={lead.research_data} />
      )}
    </div>
  );
}

type PNSFitData = {
  founder_recommendation?: string; founder_advice?: string; pursue_rationale?: string;
  pns_fit_score?: number;
  fit_factors?: { factor: string; score: number; max: number; rationale: string }[];
  sales_difficulty?: string; estimated_sales_cycle?: string; sales_difficulty_rationale?: string;
  first_project?: { name?: string; rationale?: string; estimated_value?: number; timeline?: string; chance_of_success?: number; expansion_potential?: string };
  return_on_founder_time?: { estimated_hours?: number; expected_value?: number; hourly_return?: number; comparison?: string };
  next_best_action?: string; next_action_rationale?: string;
  why_pns?: string[]; risk_factors?: string[];
  outreach_strategy?: {
    decision_maker?: string; channel?: string; opening_message?: string;
    discovery_questions?: string[]; likely_objections?: string[]; objection_responses?: string[];
  };
  market_intelligence?: { market_maturity?: string; digital_maturity?: string; common_pain_points?: string[] };
};

const DIFFICULTY_LABELS: Record<string, string> = {
  very_easy: "Very Easy", easy: "Easy", moderate: "Moderate", difficult: "Difficult", enterprise: "Enterprise",
};

function PNSFitCard({ pnsFitScore, pnsFitData }: { pnsFitScore: number | null; pnsFitData: string | null }) {
  const data: PNSFitData | null = (() => {
    if (!pnsFitData) return null;
    try { return JSON.parse(pnsFitData); } catch { return null; }
  })();

  if (!data) return null;

  const rec = data.founder_recommendation || "LATER";
  const difficulty = data.sales_difficulty || "moderate";
  const cycle = data.estimated_sales_cycle || "3 months";
  const fp = data.first_project;
  const roft = data.return_on_founder_time;
  const out = data.outreach_strategy;

  const recColor = rec === "YES" ? "border-emerald-400/20 bg-emerald-400/5" : rec === "NO" ? "border-red-400/20 bg-red-400/5" : "border-amber-400/20 bg-amber-400/5";
  const recBadge = rec === "YES" ? "success" as const : rec === "NO" ? "danger" as const : "warning" as const;

  return (
    <Card className={`${recColor} bg-gradient-to-r from-emerald-400/5 to-cyan-400/5`}>
      <div className="flex items-center gap-2 mb-3">
        <Target className="h-4 w-4 text-emerald-400" />
        <p className="text-xs font-semibold uppercase tracking-[0.1em] text-emerald-300">Founder Mode — Business Development Brain</p>
        <span className="ml-auto rounded-lg bg-emerald-400/10 px-2 py-0.5 text-xs font-bold text-emerald-400">
          PNS Fit: {pnsFitScore ?? data.pns_fit_score ?? "—"}/100
        </span>
      </div>

      {/* Founder Recommendation */}
      <div className="flex items-center gap-2 mb-3">
        <Badge variant={recBadge}>{rec === "YES" ? "🔥 PURSUE" : rec === "NO" ? "🚫 SKIP" : "⏳ LATER"}</Badge>
        {data.pursue_rationale && <p className="text-xs text-slate-400">{data.pursue_rationale}</p>}
      </div>

      {/* Founder Advice */}
      {data.founder_advice && (
        <div className="mb-3 rounded-lg border border-white/5 bg-white/[0.02] p-3">
          <p className="text-xs font-medium text-cyan-300 mb-1">💡 Founder Advice</p>
          <p className="text-xs text-slate-300 leading-relaxed italic">&ldquo;{data.founder_advice}&rdquo;</p>
        </div>
      )}

      <div className="grid gap-3 sm:grid-cols-2">
        {/* Fit Factors */}
        <div>
          {data.fit_factors && data.fit_factors.length > 0 && (
            <div className="space-y-1">
              {data.fit_factors.map((f, i) => (
                <div key={i} className="flex items-center gap-2 text-xs">
                  <div className="h-1.5 flex-1 rounded-full bg-slate-800">
                    <div className="h-full rounded-full bg-emerald-400/60" style={{ width: `${(f.score / f.max) * 100}%` }} />
                  </div>
                  <span className="w-20 text-right text-slate-400">{f.factor}</span>
                  <span className="w-8 text-right font-medium text-white">{f.score}</span>
                </div>
              ))}
            </div>
          )}
          {data.why_pns && data.why_pns.length > 0 && (
            <div className="mt-2 space-y-0.5">
              {data.why_pns.map((r, i) => (
                <p key={i} className="text-xs text-emerald-300/80">✓ {r}</p>
              ))}
            </div>
          )}
        </div>

        {/* Sales + First Project + ROI */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500">Difficulty:</span>
            <Badge variant={difficulty === "very_easy" || difficulty === "easy" ? "success" : difficulty === "moderate" ? "warning" : "danger"}>
              {DIFFICULTY_LABELS[difficulty] || difficulty}
            </Badge>
            <span className="text-xs text-slate-500">· {cycle}</span>
          </div>

          {fp && fp.name && (
            <div>
              <span className="text-xs text-slate-500">First Project:</span>
              <p className="text-xs font-medium text-cyan-300">{fp.name}</p>
              {fp.rationale && <p className="text-xs text-slate-400 mt-0.5">{fp.rationale}</p>}
              {fp.estimated_value && (
                <p className="text-xs text-amber-400 mt-0.5">
                  ~${fp.estimated_value.toLocaleString()} · {fp.timeline || ""} · {fp.chance_of_success}% success · expansion: {fp.expansion_potential}
                </p>
              )}
            </div>
          )}

          {roft && roft.estimated_hours && (
            <div className="rounded bg-slate-800/50 p-2">
              <p className="text-xs text-slate-500">Return on Founder Time</p>
              <p className="text-xs font-medium text-white">
                {roft.estimated_hours}h → ${roft.expected_value?.toLocaleString()} = ${roft.hourly_return}/hr
              </p>
            </div>
          )}

          {data.next_best_action && (
            <div>
              <span className="text-xs text-slate-500">Next: </span>
              <span className="text-xs font-medium text-white">{data.next_best_action}</span>
              {data.next_action_rationale && <p className="text-xs text-slate-400">{data.next_action_rationale}</p>}
            </div>
          )}
        </div>
      </div>

      {/* Outreach */}
      {out && out.opening_message && (
        <div className="mt-3 pt-3 border-t border-white/5">
          <div className="grid gap-1 sm:grid-cols-2 text-xs mb-2">
            {out.decision_maker && <span className="text-slate-400">Target: <span className="text-slate-300">{out.decision_maker}</span></span>}
            {out.channel && <span className="text-slate-400">Via: <span className="text-slate-300">{out.channel}</span></span>}
          </div>
          <p className="text-xs text-slate-400 italic">&ldquo;{out.opening_message}&rdquo;</p>
        </div>
      )}
    </Card>
  );
}

type ExplainData = {
  score_breakdown?: { factor: string; points: number; rationale: string }[];
  confidence_factors?: { factor: string; status: string; detail: string }[];
  signal_evidence?: { signal: string; evidence: string; confidence: number; source: string }[];
  service_reasoning?: { service: string; match_reason: string; expected_roi: string; implementation_effort: string; business_impact: string }[];
};

function ExplainabilityPanel({ researchData }: { researchData: string | null }) {
  const data: ExplainData | null = (() => {
    if (!researchData) return null;
    try { return JSON.parse(researchData); } catch { return null; }
  })();

  if (!data) {
    return (
      <Card className="border-cyan-400/10 bg-gradient-to-br from-cyan-400/5 to-purple-400/5">
        <div className="py-8 text-center">
          <Info className="mx-auto h-8 w-8 text-cyan-400" />
          <p className="mt-2 text-sm text-slate-400">No explainability data available yet.</p>
          <p className="text-xs text-slate-500 mt-1">Run AI research to generate detailed score breakdowns and reasoning.</p>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {data.score_breakdown && data.score_breakdown.length > 0 && (
        <Card>
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp className="h-4 w-4 text-emerald-400" />
            <p className="text-xs font-semibold uppercase tracking-[0.1em] text-emerald-300">Opportunity Score Breakdown</p>
          </div>
          <div className="space-y-2">
            {data.score_breakdown.map((item, i) => (
              <div key={i} className="flex items-start gap-3 rounded-lg border border-white/5 p-3">
                <span className="shrink-0 rounded-lg bg-emerald-400/10 px-2 py-1 text-xs font-bold text-emerald-400">+{item.points}</span>
                <div>
                  <p className="text-sm font-medium text-white">{item.factor}</p>
                  <p className="text-xs text-slate-400">{item.rationale}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {data.confidence_factors && data.confidence_factors.length > 0 && (
        <Card>
          <div className="flex items-center gap-2 mb-3">
            <Shield className="h-4 w-4 text-cyan-400" />
            <p className="text-xs font-semibold uppercase tracking-[0.1em] text-cyan-300">Confidence Justification</p>
          </div>
          <div className="space-y-2">
            {data.confidence_factors.map((item, i) => (
              <div key={i} className="flex items-center gap-3 rounded-lg border border-white/5 p-3">
                <span className={item.status === "verified" ? "text-emerald-400" : "text-amber-400"}>
                  {item.status === "verified" ? "✓" : "⚠"}
                </span>
                <div>
                  <p className="text-sm font-medium text-white">{item.factor}</p>
                  <p className="text-xs text-slate-400">{item.detail}</p>
                </div>
                <Badge variant={item.status === "verified" ? "success" : "warning"}>{item.status}</Badge>
              </div>
            ))}
          </div>
        </Card>
      )}

      {data.signal_evidence && data.signal_evidence.length > 0 && (
        <Card>
          <div className="flex items-center gap-2 mb-3">
            <Zap className="h-4 w-4 text-amber-400" />
            <p className="text-xs font-semibold uppercase tracking-[0.1em] text-amber-300">Buying Signal Evidence</p>
          </div>
          <div className="space-y-2">
            {data.signal_evidence.map((item, i) => (
              <div key={i} className="flex items-start gap-3 rounded-lg border border-white/5 p-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium text-white">{item.signal}</p>
                    <Badge variant="neutral">{item.confidence}%</Badge>
                  </div>
                  <p className="text-xs text-slate-400 mt-1">{item.evidence}</p>
                  <p className="text-xs text-slate-500 mt-0.5">Source: {item.source}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {data.service_reasoning && data.service_reasoning.length > 0 && (
        <Card>
          <div className="flex items-center gap-2 mb-3">
            <Target className="h-4 w-4 text-purple-400" />
            <p className="text-xs font-semibold uppercase tracking-[0.1em] text-purple-300">Service Recommendations — With Reasoning</p>
          </div>
          <div className="space-y-3">
            {data.service_reasoning.map((item, i) => (
              <div key={i} className="rounded-lg border border-white/5 p-4">
                <p className="text-sm font-medium text-white">{item.service}</p>
                <p className="text-xs text-slate-400 mt-1">{item.match_reason}</p>
                <div className="mt-2 grid grid-cols-3 gap-2 text-xs">
                  <div className="rounded bg-slate-800/50 p-2 text-center">
                    <p className="text-slate-500">ROI</p>
                    <p className="font-medium text-white">{item.expected_roi}</p>
                  </div>
                  <div className="rounded bg-slate-800/50 p-2 text-center">
                    <p className="text-slate-500">Effort</p>
                    <p className="font-medium text-white">{item.implementation_effort}</p>
                  </div>
                  <div className="rounded bg-slate-800/50 p-2 text-center">
                    <p className="text-slate-500">Impact</p>
                    <p className="font-medium text-white">{item.business_impact}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
