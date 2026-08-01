"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@clerk/nextjs";
import { Search, Database, Link2, History, Activity, Target } from "lucide-react";
import { Shell } from "@/components/dashboard/shell";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

type KnowledgeStats = {
  total_facts: number;
  total_relationships: number;
  total_events: number;
  facts_by_entity_type: Record<string, number>;
  top_facts: KnowledgeFact[];
};

type KnowledgeFact = {
  id: number;
  entity_type: string;
  entity_id: number;
  key: string;
  value: string;
  source: string;
  confidence: number;
  version: number;
  created_at: string;
};

type KnowledgeRelationship = {
  id: number;
  from_type: string;
  from_id: number;
  to_type: string;
  to_id: number;
  rel_type: string;
  properties: Record<string, unknown>;
};

type KnowledgeEvent = {
  id: number;
  entity_type: string;
  entity_id: number;
  event_type: string;
  payload: Record<string, unknown>;
  created_at: string;
};

export default function KnowledgeExplorer() {
  const [stats, setStats] = useState<KnowledgeStats | null>(null);
  const [facts, setFacts] = useState<KnowledgeFact[]>([]);
  const [relationships, setRelationships] = useState<KnowledgeRelationship[]>([]);
  const [events, setEvents] = useState<KnowledgeEvent[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<KnowledgeFact[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"facts" | "relationships" | "events">("facts");
  const [snapshotType, setSnapshotType] = useState("company");
  const [snapshotId, setSnapshotId] = useState("");
  const [snapshot, setSnapshot] = useState<KnowledgeFact[] | null>(null);
  const { getToken } = useAuth();

  const apiFetch = async (url: string, options: RequestInit = {}) => {
    const token = await getToken();
    return fetch(url, { ...options, headers: { ...options.headers, Authorization: `Bearer ${token}` } });
  };

  useEffect(() => {
    if (!getToken) return;
    apiFetch("/api/v1/knowledge/stats").then(r => r.json()).then(setStats).catch(() => {});
    apiFetch("/api/v1/knowledge/facts?limit=50").then(r => r.json()).then(d => setFacts(d.facts || [])).catch(() => {});
    apiFetch("/api/v1/knowledge/relationships?limit=50").then(r => r.json()).then(d => setRelationships(d.relationships || [])).catch(() => {});
  }, [getToken]);

  const doSearch = async () => {
    if (!searchQuery.trim()) return;
    setLoading(true);
    try {
      const r = await apiFetch(`/api/v1/knowledge/search?q=${encodeURIComponent(searchQuery)}`);
      if (r.ok) { const d = await r.json(); setSearchResults(d.results || []); }
    } catch { /* */ }
    setLoading(false);
  };

  const loadSnapshot = async () => {
    if (!snapshotId.trim()) return;
    try {
      const r = await apiFetch(`/api/v1/knowledge/snapshot/${snapshotType}/${snapshotId}`);
      if (r.ok) { const d = await r.json(); setSnapshot(d.facts || []); }
    } catch { /* */ }
  };

  const loadEvents = async () => {
    if (!snapshotId.trim()) return;
    try {
      const r = await apiFetch(`/api/v1/knowledge/events/${snapshotType}/${snapshotId}`);
      if (r.ok) { const d = await r.json(); setEvents(d.events || []); setActiveTab("events"); }
    } catch { /* */ }
  };

  return (
    <Shell>
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-semibold text-white">Knowledge Explorer</h2>
          <p className="text-sm text-slate-400 mt-1">Semantic knowledge graph — facts, relationships, and immutable event log</p>
        </div>

        {/* Stats */}
        {stats && (
          <div className="grid gap-3 sm:grid-cols-4">
            <StatCard icon={Database} label="Total Facts" value={stats.total_facts} color="text-cyan-400" />
            <StatCard icon={Link2} label="Relationships" value={stats.total_relationships} color="text-emerald-400" />
            <StatCard icon={History} label="Events" value={stats.total_events} color="text-violet-400" />
            <StatCard icon={Activity} label="Entity Types" value={Object.keys(stats.facts_by_entity_type).length} color="text-amber-400" />
          </div>
        )}

        {/* Search */}
        <Card className="p-4">
          <div className="flex gap-2">
            <input
              type="text"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              onKeyDown={e => e.key === "Enter" && doSearch()}
              placeholder="Search knowledge graph... e.g. company name, contact, technology"
              className="flex-1 rounded-lg bg-slate-800 border border-slate-700 px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400/50"
            />
            <Button onClick={doSearch} disabled={loading} className="bg-cyan-600 hover:bg-cyan-500 text-white text-sm px-4 py-2 rounded-lg">
              <Search className="w-4 h-4 mr-1" /> {loading ? "Searching..." : "Search"}
            </Button>
          </div>
        </Card>

        {/* Search Results */}
        {searchResults.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-gray-200 mb-3">Search Results ({searchResults.length})</h3>
            <div className="space-y-2">
              {searchResults.map(fact => (
                <FactCard key={fact.id} fact={fact} />
              ))}
            </div>
          </div>
        )}

        {/* Snapshot Explorer */}
        <Card className="p-4">
          <h3 className="text-sm font-semibold text-gray-200 mb-3">Entity Snapshot</h3>
          <div className="flex gap-2 flex-wrap">
            <select
              value={snapshotType}
              onChange={e => setSnapshotType(e.target.value)}
              className="rounded-lg bg-slate-800 border border-slate-700 px-3 py-2 text-sm text-white focus:outline-none"
            >
              <option value="company">Company</option>
              <option value="contact">Contact</option>
              <option value="lead">Lead</option>
              <option value="opportunity">Opportunity</option>
            </select>
            <input
              type="text"
              value={snapshotId}
              onChange={e => setSnapshotId(e.target.value)}
              placeholder="Entity ID..."
              className="rounded-lg bg-slate-800 border border-slate-700 px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none"
            />
            <Button onClick={loadSnapshot} className="bg-violet-600 hover:bg-violet-500 text-white text-sm px-3 py-2 rounded-lg">
              <Database className="w-4 h-4 mr-1" /> Load Facts
            </Button>
            <Button onClick={loadEvents} className="bg-amber-600 hover:bg-amber-500 text-white text-sm px-3 py-2 rounded-lg">
              <History className="w-4 h-4 mr-1" /> Load Events
            </Button>
          </div>
        </Card>

        {/* Snapshot Results */}
        {snapshot && (
          <div>
            <h3 className="text-sm font-semibold text-gray-200 mb-3">Entity Facts ({snapshot.length})</h3>
            <div className="space-y-2">
              {snapshot.map(fact => (
                <FactCard key={fact.id} fact={fact} />
              ))}
            </div>
          </div>
        )}

        {/* Tabs: Facts / Relationships / Events */}
        <div className="flex gap-1 bg-gray-900 rounded-lg p-1">
          {(["facts", "relationships", "events"] as const).map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex-1 px-3 py-2 rounded-md text-sm capitalize ${
                activeTab === tab
                  ? "bg-gray-700 text-white"
                  : "text-gray-400 hover:text-gray-300"
              }`}
            >
              {tab === "facts" && <Database className="w-3.5 h-3.5 inline mr-1" />}
              {tab === "relationships" && <Link2 className="w-3.5 h-3.5 inline mr-1" />}
              {tab === "events" && <History className="w-3.5 h-3.5 inline mr-1" />}
              {tab}
            </button>
          ))}
        </div>

        {/* Facts */}
        {activeTab === "facts" && (
          <div className="space-y-2">
            {facts.map(fact => (
              <FactCard key={fact.id} fact={fact} />
            ))}
            {facts.length === 0 && <EmptyState icon={Database} text="No facts yet" />}
          </div>
        )}

        {/* Relationships */}
        {activeTab === "relationships" && (
          <div className="space-y-2">
            {relationships.map(rel => (
              <Card key={rel.id} className="p-3 bg-gray-900 border-gray-700">
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-cyan-400">{rel.from_type}:{rel.from_id}</span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-violet-400/10 text-violet-400">{rel.rel_type}</span>
                  <span className="text-cyan-400">{rel.to_type}:{rel.to_id}</span>
                </div>
              </Card>
            ))}
            {relationships.length === 0 && <EmptyState icon={Link2} text="No relationships yet" />}
          </div>
        )}

        {/* Events */}
        {activeTab === "events" && (
          <div className="space-y-2">
            {events.map(event => (
              <Card key={event.id} className="p-3 bg-gray-900 border-gray-700">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-400/10 text-amber-400">{event.event_type}</span>
                    <span className="text-xs text-gray-400">{event.entity_type}:{event.entity_id}</span>
                  </div>
                  <span className="text-[10px] text-gray-500">{new Date(event.created_at).toLocaleString()}</span>
                </div>
              </Card>
            ))}
            {events.length === 0 && <EmptyState icon={History} text="No events yet — load an entity snapshot first" />}
          </div>
        )}
      </div>
    </Shell>
  );
}

function FactCard({ fact }: { fact: KnowledgeFact }) {
  return (
    <Card className="p-3 bg-gray-900 border-gray-700 hover:border-gray-600 transition-colors">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-800 text-gray-400">{fact.entity_type}</span>
            <span className="text-[10px] text-gray-500">v{fact.version}</span>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-cyan-400/10 text-cyan-400">{fact.source}</span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-sm font-medium text-white">{fact.key}</span>
            <span className="text-xs text-gray-400">= {fact.value}</span>
          </div>
        </div>
        <div className="flex items-center gap-1 text-[10px] text-gray-500">
          <Target className="w-3 h-3" />
          {Math.round(fact.confidence * 100)}%
        </div>
      </div>
    </Card>
  );
}

function StatCard({ icon: Icon, label, value, color }: { icon: typeof Database; label: string; value: string | number; color: string }) {
  return (
    <Card className="p-4 flex items-center gap-3 bg-gray-900 border-gray-700">
      <Icon className={`w-5 h-5 ${color}`} />
      <div>
        <p className="text-xs text-slate-500">{label}</p>
        <p className="text-lg font-semibold text-white">{value}</p>
      </div>
    </Card>
  );
}

function EmptyState({ icon: Icon, text }: { icon: typeof Database; text: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-gray-500 text-sm gap-2">
      <Icon className="w-10 h-10 opacity-20" />
      {text}
    </div>
  );
}
