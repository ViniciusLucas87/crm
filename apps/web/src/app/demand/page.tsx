"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@clerk/nextjs";
import { Search, TrendingUp, Target, Zap, BarChart3, Radio, Phone, Mail, Linkedin, FileText } from "lucide-react";
import { Shell } from "@/components/dashboard/shell";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

type Signal = {
  id: number;
  source: string;
  title: string;
  content: string;
  company_name?: string;
  author?: string;
  pain_type: string;
  urgency: string;
  buying_intent: number;
  lead_score: number;
  recommended_action: string;
  confidence: number;
  technologies: string[];
  keywords: string[];
};

type Stats = {
  total_signals: number;
  high_intent: number;
  avg_score: number;
  by_pain: Record<string, number>;
  by_source: Record<string, number>;
  top_signals: Signal[];
};

const ACTION_ICONS: Record<string, React.ReactNode> = {
  phone_call: <Phone className="w-3.5 h-3.5" />,
  cold_email: <Mail className="w-3.5 h-3.5" />,
  linkedin_message: <Linkedin className="w-3.5 h-3.5" />,
  create_proposal: <FileText className="w-3.5 h-3.5" />,
  monitor: <Radio className="w-3.5 h-3.5" />,
  not_qualified: <Target className="w-3.5 h-3.5" />,
};

const ACTION_LABELS: Record<string, string> = {
  phone_call: "Call Now",
  cold_email: "Send Email",
  linkedin_message: "LinkedIn DM",
  create_proposal: "Create Proposal",
  monitor: "Monitor",
  not_qualified: "Not Qualified",
};

const SCORE_COLOR = (s: number) => s >= 70 ? "text-emerald-400" : s >= 45 ? "text-amber-400" : "text-red-400";
const SCORE_BG = (s: number) => s >= 70 ? "bg-emerald-400/10" : s >= 45 ? "bg-amber-400/10" : "bg-red-400/10";

export default function DemandDashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [signals, setSignals] = useState<Signal[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const { getToken } = useAuth();

  const apiFetch = async (url: string, options: RequestInit = {}) => {
    const token = await getToken();
    return fetch(url, {
      ...options,
      headers: { ...options.headers, Authorization: `Bearer ${token}` },
    });
  };

  useEffect(() => {
    if (!getToken) return;
    apiFetch("/api/v1/demand/stats").then(r => r.json()).then(setStats).catch(() => {});
    apiFetch("/api/v1/demand/signals?limit=50").then(r => r.json()).then(d => setSignals(d.signals || [])).catch(() => {});
  }, [getToken]);

  const doSearch = async () => {
    setLoading(true);
    try {
      const r = await apiFetch("/api/v1/demand/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: searchQuery || "inspection software" }),
      });
      if (r.ok) {
        const d = await r.json();
        setSignals(prev => [...d.results, ...prev]);
        apiFetch("/api/v1/demand/stats").then(r => r.json()).then(setStats).catch(() => {});
      }
    } catch { /* */ }
    setLoading(false);
  };

  const highIntent = signals.filter(s => s.lead_score >= 70);

  return (
    <Shell>
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-semibold text-white">Demand Intelligence</h2>
          <p className="text-sm text-slate-400 mt-1">Discover companies actively expressing operational pain or looking for solutions</p>
        </div>

        {stats && (
          <div className="grid gap-3 sm:grid-cols-4">
            <StatCard icon={Zap} label="Total Signals" value={stats.total_signals} color="text-cyan-400" />
            <StatCard icon={TrendingUp} label="High Intent" value={stats.high_intent} color="text-emerald-400" />
            <StatCard icon={Target} label="Avg Score" value={Math.round(stats.avg_score)} color="text-violet-400" />
            <StatCard icon={BarChart3} label="Sources" value={Object.keys(stats.by_source).length} color="text-amber-400" />
          </div>
        )}

        <Card className="p-4">
          <div className="flex gap-2">
            <input
              type="text"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              onKeyDown={e => e.key === "Enter" && doSearch()}
              placeholder="Search for buying signals... e.g. inspection software, replacing CRM"
              className="flex-1 rounded-lg bg-slate-800 border border-slate-700 px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400/50"
            />
            <Button onClick={doSearch} disabled={loading} className="bg-cyan-600 hover:bg-cyan-500 text-white text-sm px-4 py-2 rounded-lg">
              <Search className="w-4 h-4 mr-1" /> {loading ? "Searching..." : "Scan for Signals"}
            </Button>
          </div>
        </Card>

        {highIntent.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-gray-200 mb-3 flex items-center gap-2">
              <Zap className="w-4 h-4 text-amber-400" />
              High Intent Signals ({highIntent.length})
            </h3>
            <div className="space-y-3">
              {highIntent.map(signal => (
                <SignalCard key={signal.id} signal={signal} />
              ))}
            </div>
          </div>
        )}

        <div>
          <h3 className="text-sm font-semibold text-gray-200 mb-3">All Signals ({signals.length})</h3>
          <div className="space-y-3">
            {signals.map(signal => (
              <SignalCard key={signal.id} signal={signal} />
            ))}
            {signals.length === 0 && (
              <div className="flex flex-col items-center justify-center py-12 text-gray-500 text-sm gap-2">
                <Radio className="w-10 h-10 opacity-20" />
                No signals yet — click &ldquo;Scan for Signals&rdquo; to discover demand
              </div>
            )}
          </div>
        </div>
      </div>
    </Shell>
  );
}

function SignalCard({ signal }: { signal: Signal }) {
  const scoreColor = SCORE_COLOR(signal.lead_score);
  const scoreBg = SCORE_BG(signal.lead_score);

  return (
    <Card className="p-4 bg-gray-900 border-gray-700 hover:border-gray-600 transition-colors">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-800 text-gray-400 uppercase">{signal.source}</span>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-800 text-gray-400">{signal.pain_type?.replace(/_/g, " ")}</span>
            {signal.company_name && (
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-cyan-400/10 text-cyan-400">{signal.company_name}</span>
            )}
          </div>
          <h4 className="text-sm font-medium text-white mb-1">{signal.title}</h4>
          <p className="text-xs text-gray-400 line-clamp-2">{signal.content}</p>
          {signal.keywords.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {signal.keywords.slice(0, 5).map(kw => (
                <span key={kw} className="text-[10px] px-1.5 py-0.5 rounded bg-gray-800 text-gray-500">{kw}</span>
              ))}
            </div>
          )}
        </div>

        <div className="flex flex-col items-end gap-2 shrink-0">
          <div className="flex items-center gap-2">
            <span className={`text-lg font-bold ${scoreColor}`}>{signal.lead_score}</span>
            <span className="text-[10px] text-gray-500">/100</span>
          </div>
          <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-[10px] ${scoreBg} ${scoreColor}`}>
            {ACTION_ICONS[signal.recommended_action]}
            {ACTION_LABELS[signal.recommended_action] || signal.recommended_action}
          </div>
          <div className="flex items-center gap-1 text-[10px] text-gray-500">
            <span>{Math.round(signal.confidence * 100)}% confidence</span>
          </div>
        </div>
      </div>
    </Card>
  );
}

function StatCard({ icon: Icon, label, value, color }: { icon: typeof Zap; label: string; value: string | number; color: string }) {
  return (
    <Card className="p-4 flex items-center gap-3">
      <Icon className={`w-5 h-5 ${color}`} />
      <div>
        <p className="text-xs text-slate-500">{label}</p>
        <p className="text-lg font-semibold text-white">{value}</p>
      </div>
    </Card>
  );
}
