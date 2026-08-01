"use client";

import { useEffect, useState, useCallback } from "react";
import { MessageSquare, Phone, Calendar, CheckSquare, TrendingUp, Heart, User, Clock, Target } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

type ConversationData = {
  id: number;
  company_id: number;
  primary_contact_id: number | null;
  status: string;
  relationship_stage: string;
  opened_by: string | null;
  owner: string | null;
  health_score: number;
  health_label: string;
  summary: string | null;
  last_activity_at: string | null;
  created_at: string;
  updated_at: string;
};

type TimelineEvent = {
  type: string;
  id: number;
  timestamp: string;
  data: Record<string, unknown>;
};

type Stats = {
  call_count: number;
  activity_count: number;
  task_count: number;
  total_events: number;
  total_call_duration_seconds: number;
  relationship_stage: string;
  health_score: number;
  health_label: string;
  days_active: number;
};

const STAGE_LABELS: Record<string, string> = {
  new: "New", contacted: "Contacted", discovery: "Discovery", qualified: "Qualified",
  proposal: "Proposal", negotiation: "Negotiation", won: "Won", lost: "Lost", dormant: "Dormant",
};

const STAGES = ["new", "contacted", "discovery", "qualified", "proposal", "negotiation", "won", "lost", "dormant"];

const EVENT_ICONS: Record<string, typeof Phone> = {
  call: Phone,
  activity: Calendar,
  task: CheckSquare,
};

export function CompanyConversationTab({ companyId }: { companyId: number }) {
  const [conversation, setConversation] = useState<ConversationData | null>(null);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const listR = await fetch(`/api/conversations?company_id=${companyId}`);
      if (!listR.ok) throw new Error("Failed to load");
      const listData = await listR.json();
      let conv = listData.items?.[0] ?? null;

      if (!conv) {
        const createR = await fetch(`/api/conversations?company_id=${companyId}`, { method: "POST" });
        if (createR.ok) conv = await createR.json();
      }

      if (conv) {
        setConversation(conv);
        const tlR = await fetch(`/api/conversations/${conv.id}/timeline`);
        if (tlR.ok) {
          const tlData = await tlR.json();
          setTimeline(tlData.events || []);
        }

        // ── Sprint 48.1: Fetch real call data ──
        let callStats = { call_count: 0, talk_time: 0, last_call_at: null as string | null };
        try {
          const callsR = await fetch(`http://localhost:8000/api/v1/calls?company_id=${companyId}`);
          if (callsR.ok) {
            const callsData = await callsR.json();
            const completed = callsData.filter((c: Record<string, unknown>) => c.status === "COMPLETED");
            callStats = {
              call_count: callsData.length,
              talk_time: completed.reduce((sum: number, c: Record<string, unknown>) => sum + ((c.duration_seconds as number) || 0), 0),
              last_call_at: callsData[0]?.ended_at || null,
            };
          }
        } catch { /* calls not available — keep defaults */ }

        // Merge with backend stats
        const stR = await fetch(`/api/conversations/${conv.id}/stats`);
        if (stR.ok) {
          const backendStats = await stR.json();
          setStats({ ...backendStats, ...callStats, days_active: backendStats.days_active || 0 });
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, [companyId]);

  useEffect(() => { void load(); }, [load]);

  const updateStage = async (stage: string) => {
    if (!conversation) return;
    const r = await fetch(`/api/conversations/${conversation.id}?stage=${stage}`, { method: "PATCH" });
    if (r.ok) setConversation(await r.json());
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-32 rounded-2xl" />
        <Skeleton className="h-64 rounded-2xl" />
      </div>
    );
  }

  if (error || !conversation) {
    return (
      <Card>
        <div className="p-6 text-center">
          <p className="text-slate-400">Could not load conversation. <button onClick={load} className="text-cyan-400 hover:underline">Retry</button></p>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* ── Header card ── */}
      <Card>
        <div className="p-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="rounded-xl border border-white/10 bg-white/5 p-3">
                <MessageSquare className="h-6 w-6 text-cyan-400" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white">Conversation</h3>
                <p className="text-xs text-slate-500">Relationship since {new Date(conversation.created_at).toLocaleDateString()}</p>
              </div>
            </div>
            <Badge variant={conversation.status === "active" ? "success" : "warning"}>
              {conversation.status}
            </Badge>
          </div>

          {/* Stage selector */}
          <div className="mt-4">
            <p className="text-xs font-medium uppercase tracking-[0.08em] text-slate-500 mb-2">Relationship Stage</p>
            <div className="flex flex-wrap gap-1">
              {STAGES.map(stage => (
                <button
                  key={stage}
                  onClick={() => updateStage(stage)}
                  className={`rounded-lg px-3 py-1.5 text-xs font-medium transition ${
                    conversation.relationship_stage === stage
                      ? "bg-cyan-400/20 text-cyan-400 border border-cyan-400/30"
                      : "border border-white/10 text-slate-500 hover:text-slate-300 hover:border-white/20"
                  }`}
                >
                  {STAGE_LABELS[stage]}
                </button>
              ))}
            </div>
          </div>
        </div>
      </Card>

      {/* ── Stats grid ── */}
      {stats && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard icon={Phone} label="Calls" value={stats.call_count > 0 ? String(stats.call_count) : "No calls yet"} />
          <StatCard icon={Calendar} label="Activities" value={stats.activity_count > 0 ? String(stats.activity_count) : "No activities"} />
          <StatCard icon={CheckSquare} label="Tasks" value={stats.task_count > 0 ? String(stats.task_count) : "No tasks"} />
          <StatCard icon={Clock} label="Days Active" value={stats.days_active > 0 ? String(stats.days_active) : "0"} />
          <StatCard icon={Heart} label="Health" value={stats.health_label} sub={`${stats.health_score}/100`} />
          <StatCard
            icon={Phone}
            label="Talk Time"
            value={stats.total_call_duration_seconds > 0
              ? `${Math.floor(stats.total_call_duration_seconds / 60)}m`
              : "—"}
          />
          <StatCard icon={User} label="Owner" value={conversation.owner || "—"} />
          <StatCard icon={Target} label="Stage" value={STAGE_LABELS[stats.relationship_stage] || stats.relationship_stage} />
        </div>
      )}

      {/* ── Summary ── */}
      {conversation.summary && (
        <Card>
          <div className="p-4">
            <p className="text-xs font-medium uppercase tracking-[0.08em] text-slate-500 mb-1">Summary</p>
            <p className="text-sm text-slate-300">{conversation.summary}</p>
          </div>
        </Card>
      )}

      {/* ── Timeline ── */}
      <Card>
        <div className="p-4">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="h-4 w-4 text-slate-400" />
            <h4 className="text-sm font-semibold text-white">Conversation Timeline</h4>
          </div>

          {timeline.length === 0 ? (
            <p className="text-sm text-slate-500 py-8 text-center">
              No events yet. Calls, activities, and tasks linked to this conversation will appear here.
            </p>
          ) : (
            <div className="space-y-1">
              {timeline.map((event) => {
                const Icon = EVENT_ICONS[event.type] || Calendar;
                const ts = new Date(event.timestamp);
                return (
                  <div key={`${event.type}-${event.id}`} className="flex items-start gap-3 rounded-lg px-3 py-2 hover:bg-white/5 transition">
                    <div className="mt-0.5 rounded-lg border border-white/10 bg-white/5 p-1.5 text-slate-400">
                      <Icon className="h-3.5 w-3.5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <Badge variant="neutral" className="text-[10px] py-0 px-1.5">{event.type}</Badge>
                        <span className="text-xs text-slate-500">{ts.toLocaleDateString()} {ts.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
                      </div>
                      <p className="text-sm text-slate-300 mt-0.5">
                        {event.type === "call" && `${event.data.direction === "outbound" ? "📞 Outbound" : "📞 Inbound"} call · ${event.data.status}${event.data.duration_seconds ? ` · ${Math.floor(Number(event.data.duration_seconds) / 60)}m ${Number(event.data.duration_seconds) % 60}s` : ""}`}
                        {event.type === "activity" && `${String(event.data.activity_type)}${event.data.subject ? `: ${String(event.data.subject)}` : ""}`}
                        {event.type === "task" && `${String(event.data.title)} · ${String(event.data.status)} · ${String(event.data.priority)}`}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, sub }: { icon: typeof Phone; label: string; value: string | number; sub?: string }) {
  return (
    <Card>
      <div className="p-4">
        <div className="mb-2 inline-flex rounded-lg border border-white/10 bg-white/5 p-1.5 text-slate-400">
          <Icon className="h-3.5 w-3.5" />
        </div>
        <p className="text-xs font-medium uppercase tracking-[0.08em] text-slate-500">{label}</p>
        <p className="mt-1 text-xl font-semibold text-white">{value}</p>
        {sub && <p className="text-xs text-slate-500">{sub}</p>}
      </div>
    </Card>
  );
}
