"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@clerk/nextjs";
import {
  Activity, Play, Pause, RotateCcw, Square, Heart, AlertTriangle,
  Zap, BarChart3, Clock, Database, RefreshCw,
} from "lucide-react";
import { Shell } from "@/components/dashboard/shell";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

type WorkerState = {
  name: string;
  description: string;
  status: string;
  priority: string;
  schedule: string;
  healthy: boolean;
  capabilities: string[];
  worker_id: string;
  queue?: string;
  heartbeat?: string | null;
  current_job_id?: number | null;
  jobs_processed: number;
  jobs_succeeded: number;
  jobs_failed: number;
  retries: number;
  avg_runtime_ms: number;
  last_run: string | null;
  facts_created: number;
  facts_verified: number;
  relationships_created: number;
  insights_generated: number;
  queue_depth?: number;
  last_error?: string | null;
};

type WorkerMetrics = {
  aggregate: Record<string, number>;
  workers: Record<string, WorkerHealth>;
  dead_letter_count: number;
  manager_running: boolean;
  timestamp: string;
};

type WorkerHealth = {
  status: string;
  healthy: boolean;
  jobs_processed: number;
  jobs_succeeded: number;
  jobs_failed: number;
  retries: number;
  avg_runtime_ms: number;
  last_run: string | null;
  last_error: string | null;
  facts_created: number;
  facts_verified: number;
  relationships_created: number;
  insights_generated: number;
  entities_enriched: number;
  queue_depth?: number;
  heartbeat?: string | null;
  current_job_id?: number | null;
};

const STATUS_COLORS: Record<string, string> = {
  running: "text-emerald-400",
  starting: "text-cyan-400",
  paused: "text-amber-400",
  stopping: "text-orange-400",
  stopped: "text-gray-500",
  error: "text-red-400",
};

const STATUS_BG: Record<string, string> = {
  running: "bg-emerald-400/10",
  starting: "bg-cyan-400/10",
  paused: "bg-amber-400/10",
  stopping: "bg-orange-400/10",
  stopped: "bg-gray-400/10",
  error: "bg-red-400/10",
};

export default function WorkerDashboard() {
  const [workers, setWorkers] = useState<WorkerState[]>([]);
  const [metrics, setMetrics] = useState<WorkerMetrics | null>(null);
  const [loading, setLoading] = useState(false);
  const { getToken } = useAuth();

  const apiFetch = useCallback(async (url: string, options: RequestInit = {}) => {
    const token = await getToken();
    return fetch(url, { ...options, headers: { ...options.headers, Authorization: `Bearer ${token}` } });
  }, [getToken]);

  const fetchData = useCallback(async () => {
    try {
      const [wr, mr] = await Promise.all([
        apiFetch("/api/v1/workers").then(r => r.json()),
        apiFetch("/api/v1/workers/metrics").then(r => r.json()),
      ]);

      // Merge worker list with metrics
      const merged = (wr.workers || []).map((w: WorkerState) => {
        const m = mr.workers?.[w.name] || {};
        return { ...w, ...m };
      });
      setWorkers(merged);
      setMetrics(mr);
    } catch { /* */ }
  }, [apiFetch]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const action = async (name: string, op: string) => {
    setLoading(true);
    try {
      await apiFetch(`/api/v1/workers/${name}/${op}`, { method: "POST" });
      setTimeout(fetchData, 1500);
    } catch { /* */ }
    setLoading(false);
  };

  const running = workers.filter(w => w.status === "running").length;
  const errors = workers.filter(w => w.status === "error" || !w.healthy).length;
  const totalJobs = workers.reduce((s, w) => s + (w.jobs_processed || 0), 0);
  const aggregate = metrics?.aggregate || {};

  return (
    <Shell>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-semibold text-white">Autonomous Knowledge Workers</h2>
            <p className="text-sm text-slate-400 mt-1">
              {running}/{workers.length} workers running — continuously improving the Knowledge Graph
            </p>
          </div>
          <Button onClick={fetchData} className="bg-gray-800 hover:bg-gray-700 text-white text-sm px-3 py-2 rounded-lg">
            <RefreshCw className="w-4 h-4 mr-1" /> Refresh
          </Button>
        </div>

        {/* Aggregate Stats */}
        <div className="grid gap-3 sm:grid-cols-6">
          <StatCard icon={Activity} label="Workers Running" value={`${running}/${workers.length}`} color="text-emerald-400" />
          <StatCard icon={AlertTriangle} label="Errors" value={errors} color={errors > 0 ? "text-red-400" : "text-gray-500"} />
          <StatCard icon={BarChart3} label="Jobs Processed" value={totalJobs} color="text-cyan-400" />
          <StatCard icon={Database} label="Facts Created" value={aggregate.facts_created || 0} color="text-violet-400" />
          <StatCard icon={Zap} label="Insights" value={aggregate.insights_generated || 0} color="text-amber-400" />
          <StatCard icon={Clock} label="Dead Letters" value={metrics?.dead_letter_count || 0} color="text-orange-400" />
        </div>

        {/* Worker Cards */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {workers.map(worker => (
            <Card key={worker.name} className={`p-4 border ${worker.healthy ? "border-gray-700" : "border-red-700/50"} bg-gray-900`}>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Heart className={`w-4 h-4 ${worker.healthy ? "text-emerald-400" : "text-red-400"}`} />
                  <span className="text-sm font-medium text-white truncate">{worker.name.replace(/_/g, " ")}</span>
                </div>
                <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${STATUS_BG[worker.status]} ${STATUS_COLORS[worker.status]}`}>
                  {worker.status}
                </span>
              </div>

              <p className="text-[11px] text-gray-500 mb-3 truncate">{worker.description}</p>

              <div className="mb-3 space-y-1 text-[10px] text-slate-500">
                <p>Queue: <span className="text-slate-300">{worker.queue ?? "normal"}</span></p>
                <p>Heartbeat: <span className="text-slate-300">{worker.heartbeat ? new Date(worker.heartbeat).toLocaleTimeString() : "none"}</span></p>
                <p>Current job: <span className="text-slate-300">{worker.current_job_id ?? "idle"}</span></p>
                <p>Queue depth: <span className="text-slate-300">{worker.queue_depth ?? 0}</span></p>
                {worker.last_error && <p className="truncate text-red-400">Last error: {worker.last_error}</p>}
              </div>

              {/* Mini Stats */}
              <div className="grid grid-cols-3 gap-2 mb-3 text-center">
                <div>
                  <p className="text-lg font-bold text-white">{worker.jobs_processed || 0}</p>
                  <p className="text-[10px] text-gray-500">Processed</p>
                </div>
                <div>
                  <p className="text-lg font-bold text-emerald-400">{worker.jobs_succeeded || 0}</p>
                  <p className="text-[10px] text-gray-500">Succeeded</p>
                </div>
                <div>
                  <p className="text-lg font-bold text-red-400">{worker.jobs_failed || 0}</p>
                  <p className="text-[10px] text-gray-500">Failed</p>
                </div>
              </div>

              {/* Controls */}
              <div className="flex gap-1">
                {worker.status !== "running" && (
                  <Button onClick={() => action(worker.name, "start")} disabled={loading} className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white text-[11px] px-2 py-1.5 rounded">
                    <Play className="w-3 h-3 mr-1" /> Start
                  </Button>
                )}
                {worker.status === "running" && (
                  <Button onClick={() => action(worker.name, "pause")} disabled={loading} className="flex-1 bg-amber-600 hover:bg-amber-500 text-white text-[11px] px-2 py-1.5 rounded">
                    <Pause className="w-3 h-3 mr-1" /> Pause
                  </Button>
                )}
                {(worker.status === "running" || worker.status === "paused") && (
                  <Button onClick={() => action(worker.name, "stop")} disabled={loading} className="flex-1 bg-red-600 hover:bg-red-500 text-white text-[11px] px-2 py-1.5 rounded">
                    <Square className="w-3 h-3 mr-1" /> Stop
                  </Button>
                )}
                <Button onClick={() => action(worker.name, "restart")} disabled={loading} className="flex-1 bg-gray-700 hover:bg-gray-600 text-white text-[11px] px-2 py-1.5 rounded">
                  <RotateCcw className="w-3 h-3 mr-1" /> Restart
                </Button>
              </div>
            </Card>
          ))}
        </div>

        {workers.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 text-gray-500 text-sm gap-2">
            <Activity className="w-12 h-12 opacity-20" />
            No workers registered — the Worker Manager starts automatically on API startup
          </div>
        )}

        {/* Legend */}
        <Card className="p-4 bg-gray-900 border-gray-700">
          <h3 className="text-sm font-semibold text-gray-200 mb-3">Architecture</h3>
          <div className="text-xs text-gray-500 space-y-1">
            <p><span className="text-cyan-400">Event Bus</span> → Workers consume immutable events from the Knowledge Graph</p>
            <p><span className="text-violet-400">Knowledge Graph</span> → All workers read/write facts, relationships, and events</p>
            <p><span className="text-amber-400">Workers never call each other directly</span> — all communication via Events + Graph</p>
            <p className="mt-2"><span className="text-emerald-400">12 workers</span> running independently: Company Enrichment, Fact Verification, Entity Resolution, Relationship Discovery, Technology Detection, Buying Signal Detector, Knowledge Decay, Reasoning, Timeline Generator, Opportunity Scoring, Search Indexer, Recommendation Engine</p>
          </div>
        </Card>
      </div>
    </Shell>
  );
}

function StatCard({ icon: Icon, label, value, color }: { icon: typeof Activity; label: string; value: string | number; color: string }) {
  return (
    <Card className="p-3 flex items-center gap-3 bg-gray-900 border-gray-700">
      <Icon className={`w-5 h-5 ${color}`} />
      <div>
        <p className="text-[10px] text-slate-500">{label}</p>
        <p className="text-lg font-semibold text-white">{value}</p>
      </div>
    </Card>
  );
}
