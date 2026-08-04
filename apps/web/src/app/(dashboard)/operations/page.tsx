"use client";

export const dynamic = "force-dynamic";

import { useEffect, useState, useCallback, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { Shell } from "@/components/dashboard/shell";
import { fetchOperationsStatus, type OperationsStatus, ApiError } from "@/lib/api";
import { Activity, Database, HardDrive, Mail, Server, WifiOff, CheckCircle, XCircle, AlertTriangle, HelpCircle, RefreshCw } from "lucide-react";

function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { icon: typeof CheckCircle; color: string; label: string }> = {
    healthy: { icon: CheckCircle, color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20", label: "Healthy" },
    degraded: { icon: AlertTriangle, color: "text-amber-400 bg-amber-500/10 border-amber-500/20", label: "Degraded" },
    unhealthy: { icon: XCircle, color: "text-red-400 bg-red-500/10 border-red-500/20", label: "Unhealthy" },
    connected: { icon: CheckCircle, color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20", label: "Connected" },
    disconnected: { icon: XCircle, color: "text-red-400 bg-red-500/10 border-red-500/20", label: "Disconnected" },
    running: { icon: CheckCircle, color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20", label: "Running" },
    stale: { icon: AlertTriangle, color: "text-amber-400 bg-amber-500/10 border-amber-500/20", label: "Stale" },
    unknown: { icon: HelpCircle, color: "text-slate-400 bg-slate-500/10 border-slate-500/20", label: "Unknown" },
  };
  const c = config[status] ?? config.unknown;
  const Icon = c.icon;
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium ${c.color}`}>
      <Icon className="h-3 w-3" />
      {c.label}
    </span>
  );
}

function MetricCard({ label, value, icon: Icon, subtitle }: { label: string; value: ReactNode; icon: typeof Database; subtitle?: string }) {
  return (
    <div className="rounded-lg border border-white/10 bg-white/5 p-4">
      <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-slate-400">
        <Icon className="h-3.5 w-3.5" />
        {label}
      </div>
      <div className="mt-2 text-2xl font-semibold text-white">{value}</div>
      {subtitle && <div className="mt-1 text-xs text-slate-500">{subtitle}</div>}
    </div>
  );
}

export default function OperationsPage() {
  const router = useRouter();
  const { isLoaded, userId } = useAuth();
  const [ready, setReady] = useState(false);
  const [status, setStatus] = useState<OperationsStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isLoaded) {
      if (!userId) {
        router.replace("/sign-in");
      } else {
        setReady(true);
      }
    }
  }, [isLoaded, userId, router]);

  const loadStatus = useCallback(() => {
    if (!ready) return;
    setLoading(true);
    setError(null);
    fetchOperationsStatus()
      .then(setStatus)
      .catch((err: unknown) => {
        setError(err instanceof ApiError ? err.message : "Failed to load operations status");
      })
      .finally(() => setLoading(false));
  }, [ready]);

  useEffect(() => {
    loadStatus();
  }, [loadStatus]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    if (!ready) return;
    const interval = setInterval(loadStatus, 30_000);
    return () => clearInterval(interval);
  }, [ready, loadStatus]);

  if (!ready) return null;

  return (
    <Shell>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-white">Operations</h1>
            <p className="mt-1 text-sm text-slate-400">
              Real-time system health for database, Redis, outbox, backups, and workers. This page auto-refreshes every 30 seconds.
            </p>
          </div>
          <button
            onClick={loadStatus}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-sm text-slate-300 transition hover:border-white/20 hover:text-white disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>

        {/* Error state */}
        {error && (
          <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300">
            <p className="font-medium">Unable to load operations status</p>
            <p className="mt-1 text-red-400">{error}</p>
          </div>
        )}

        {/* Loading state */}
        {loading && !status && !error && (
          <div className="rounded-lg border border-white/10 bg-white/5 p-12 text-center">
            <Activity className="mx-auto h-8 w-8 animate-pulse text-slate-600" />
            <p className="mt-3 text-sm text-slate-400">Loading system status...</p>
          </div>
        )}

        {/* Status content */}
        {status && (
          <>
            {/* Overall status */}
            <div className={`rounded-lg border p-6 ${
              status.status === "healthy" ? "border-emerald-500/20 bg-emerald-500/5" :
              status.status === "degraded" ? "border-amber-500/20 bg-amber-500/5" :
              "border-red-500/20 bg-red-500/5"
            }`}>
              <div className="flex flex-wrap items-center gap-4">
                <StatusBadge status={status.status} />
                <div className="text-sm text-slate-400">
                  <span className="text-slate-300">{status.environment}</span> environment
                  {status.build_id !== "unknown" && (
                    <span className="ml-2 text-xs text-slate-500">Build {status.build_id}</span>
                  )}
                </div>
                <div className="ml-auto text-xs text-slate-500">
                  Checked at {new Date(status.generated_at).toLocaleTimeString()}
                </div>
              </div>
            </div>

            {/* Metric cards */}
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
              <MetricCard
                label="Database"
                value={<StatusBadge status={status.db_status} />}
                icon={Database}
                subtitle={`Latency: ${status.db_latency_ms.toFixed(1)} ms`}
              />
              <MetricCard
                label="Redis"
                value={<StatusBadge status={status.redis_status} />}
                icon={Server}
                subtitle="Session and cache store"
              />
              <MetricCard
                label="Worker"
                value={<StatusBadge status={status.worker_status} />}
                icon={Activity}
                subtitle={status.worker_heartbeat_ms != null ? `Ping: ${status.worker_heartbeat_ms} ms` : "No heartbeat data"}
              />
              <MetricCard
                label="Backups"
                value={status.backups_ok === true ? <StatusBadge status="healthy" /> : status.backups_ok === false ? <StatusBadge status="unhealthy" /> : <StatusBadge status="unknown" />}
                icon={HardDrive}
                subtitle={status.backups_ok === null ? "Verified by backup script, not checked here" : status.backups_ok ? "Last backup verified" : "Backup check failed"}
              />
              <MetricCard
                label="Outbox Pending"
                value={status.outbox_pending}
                icon={Mail}
                subtitle={status.outbox_pending > 50 ? "Backlog building" : "Within normal range"}
              />
              <MetricCard
                label="Outbox Failed"
                value={status.outbox_failed}
                icon={WifiOff}
                subtitle={status.outbox_failed >= 100 ? "Critical: threshold exceeded" : status.outbox_failed > 0 ? "Some events failed" : "No failures"}
              />
            </div>

            {/* Build info */}
            <div className="rounded-lg border border-white/10 bg-white/5 p-4">
              <h3 className="text-sm font-medium text-slate-300">Build Information</h3>
              <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-slate-400 sm:grid-cols-3">
                <div>
                  <span className="text-slate-500">Build ID:</span>{" "}
                  <code className="text-slate-300">{status.build_id}</code>
                </div>
                <div>
                  <span className="text-slate-500">Git Commit:</span>{" "}
                  <code className="text-slate-300">{status.git_commit}</code>
                </div>
                <div>
                  <span className="text-slate-500">Environment:</span>{" "}
                  <span className="text-slate-300">{status.environment}</span>
                </div>
              </div>
            </div>

            {/* What this means */}
            <div className="rounded-lg border border-white/10 bg-white/5 p-4">
              <h3 className="text-sm font-medium text-slate-300">Understanding This Page</h3>
              <ul className="mt-2 space-y-1 text-xs text-slate-500">
                <li><strong className="text-slate-400">Database:</strong> Checks if PostgreSQL is reachable and responding to queries.</li>
                <li><strong className="text-slate-400">Redis:</strong> Checks if the Redis cache and message broker is connected.</li>
                <li><strong className="text-slate-400">Worker:</strong> Pings the Celery background worker. Unknown means the worker process may not be running or reachable.</li>
                <li><strong className="text-slate-400">Backups:</strong> Verifies the encrypted backup marker in Cloudflare R2. Healthy means the latest backup is recent and reachable.</li>
                <li><strong className="text-slate-400">Outbox:</strong> Counts pending and failed outbox events. High pending means workers are falling behind. Failed events may need manual replay.</li>
              </ul>
            </div>
          </>
        )}
      </div>
    </Shell>
  );
}
