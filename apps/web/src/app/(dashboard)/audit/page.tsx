"use client";

export const dynamic = "force-dynamic";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { Shell } from "@/components/dashboard/shell";
import { fetchAuditEntries, type AuditEntry, type AuditListResponse, ApiError } from "@/lib/api";
import { Shield, ChevronLeft, ChevronRight, Clock, FileText, User, Tag } from "lucide-react";

type Filter = { entity_type?: string; action?: string };

const ENTITY_TYPES = ["task", "lead"];
const ACTIONS = ["completed", "rescheduled", "assigned"];

export default function AuditPage() {
  const router = useRouter();
  const { isLoaded, userId } = useAuth();
  const [ready, setReady] = useState(false);
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<Filter>({});
  const pageSize = 50;

  useEffect(() => {
    if (isLoaded) {
      if (!userId) {
        router.replace("/sign-in");
      } else {
        setReady(true);
      }
    }
  }, [isLoaded, userId, router]);

  useEffect(() => {
    if (!ready) return;
    setLoading(true);
    setError(null);
    fetchAuditEntries({ page, page_size: pageSize, ...filter })
      .then((data: AuditListResponse) => {
        setEntries(data.entries);
        setTotal(data.total);
      })
      .catch((err: unknown) => {
        setError(err instanceof ApiError ? err.message : "Failed to load audit entries");
      })
      .finally(() => setLoading(false));
  }, [ready, page, filter]);

  if (!ready) return null;

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  const clearFilters = () => {
    setFilter({});
    setPage(1);
  };

  const toggleFilter = (key: keyof Filter, value: string) => {
    setFilter((prev) => {
      const current = prev[key];
      return { ...prev, [key]: current === value ? undefined : value };
    });
    setPage(1);
  };

  return (
    <Shell>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-white">Audit Log</h1>
            <p className="mt-1 text-sm text-slate-400">
              Every action taken on tasks and leads is recorded here. This log is append-only and cannot be modified or deleted.
            </p>
          </div>
          <div className="flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-sm text-cyan-300">
            <Shield className="h-4 w-4" />
            <span>Immutable record</span>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-medium uppercase tracking-wider text-slate-500">Filter:</span>
          {ENTITY_TYPES.map((et) => (
            <button
              key={et}
              onClick={() => toggleFilter("entity_type", et)}
              className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-medium transition ${
                filter.entity_type === et
                  ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
                  : "bg-white/5 text-slate-400 border border-white/10 hover:border-white/20 hover:text-slate-300"
              }`}
            >
              <FileText className="h-3 w-3" />
              {et}
            </button>
          ))}
          <span className="mx-1 text-slate-600">|</span>
          {ACTIONS.map((a) => (
            <button
              key={a}
              onClick={() => toggleFilter("action", a)}
              className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-medium transition ${
                filter.action === a
                  ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
                  : "bg-white/5 text-slate-400 border border-white/10 hover:border-white/20 hover:text-slate-300"
              }`}
            >
              <Tag className="h-3 w-3" />
              {a}
            </button>
          ))}
          {(filter.entity_type || filter.action) && (
            <button
              onClick={clearFilters}
              className="ml-2 text-xs text-slate-500 hover:text-slate-300 transition"
            >
              Clear filters
            </button>
          )}
        </div>

        {/* Error state */}
        {error && (
          <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300">
            <p className="font-medium">Unable to load audit entries</p>
            <p className="mt-1 text-red-400">{error}</p>
          </div>
        )}

        {/* Loading state */}
        {loading && !error && (
          <div className="rounded-lg border border-white/10 bg-white/5 p-8 text-center">
            <p className="text-sm text-slate-400">Loading audit entries...</p>
          </div>
        )}

        {/* Empty state */}
        {!loading && !error && entries.length === 0 && (
          <div className="rounded-lg border border-white/10 bg-white/5 p-12 text-center">
            <Clock className="mx-auto h-8 w-8 text-slate-600" />
            <p className="mt-3 text-sm font-medium text-slate-300">No audit entries yet</p>
            <p className="mt-1 text-xs text-slate-500">
              {filter.entity_type || filter.action
                ? "No entries match the current filters. Try clearing them."
                : "Actions taken on tasks and leads will appear here once activity begins."}
            </p>
          </div>
        )}

        {/* Entries table */}
        {!loading && !error && entries.length > 0 && (
          <>
            <div className="overflow-x-auto rounded-lg border border-white/10">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-white/10 bg-white/5">
                    <th className="px-4 py-3 text-xs font-medium uppercase tracking-wider text-slate-400">
                      <span className="inline-flex items-center gap-1"><FileText className="h-3 w-3" /> Entity</span>
                    </th>
                    <th className="px-4 py-3 text-xs font-medium uppercase tracking-wider text-slate-400">
                      <span className="inline-flex items-center gap-1"><Tag className="h-3 w-3" /> Action</span>
                    </th>
                    <th className="px-4 py-3 text-xs font-medium uppercase tracking-wider text-slate-400 hidden md:table-cell">
                      <span className="inline-flex items-center gap-1"><User className="h-3 w-3" /> Actor</span>
                    </th>
                    <th className="px-4 py-3 text-xs font-medium uppercase tracking-wider text-slate-400 hidden md:table-cell">Old State</th>
                    <th className="px-4 py-3 text-xs font-medium uppercase tracking-wider text-slate-400 hidden md:table-cell">New State</th>
                    <th className="px-4 py-3 text-xs font-medium uppercase tracking-wider text-slate-400">
                      <span className="inline-flex items-center gap-1"><Clock className="h-3 w-3" /> When</span>
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {entries.map((entry) => (
                    <tr key={entry.id} className="hover:bg-white/[0.02] transition">
                      <td className="px-4 py-3">
                        <span className="text-slate-300">{entry.entity_type}</span>
                        <span className="ml-1 text-xs text-slate-500">#{entry.entity_id}</span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                          entry.action === "completed" ? "bg-emerald-500/20 text-emerald-300" :
                          entry.action === "rescheduled" ? "bg-amber-500/20 text-amber-300" :
                          "bg-blue-500/20 text-blue-300"
                        }`}>
                          {entry.action}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-400 text-xs hidden md:table-cell">
                        {entry.actor_user_id || "System"}
                      </td>
                      <td className="px-4 py-3 text-slate-500 text-xs font-mono hidden md:table-cell max-w-[120px] truncate" title={entry.old_state ?? undefined}>
                        {entry.old_state || "-"}
                      </td>
                      <td className="px-4 py-3 text-slate-300 text-xs font-mono hidden md:table-cell max-w-[120px] truncate" title={entry.new_state ?? undefined}>
                        {entry.new_state || "-"}
                      </td>
                      <td className="px-4 py-3 text-slate-400 text-xs whitespace-nowrap">
                        {new Date(entry.created_at).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between text-sm text-slate-400">
              <span>
                Page {page} of {totalPages} ({total} total entries)
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="inline-flex items-center gap-1 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium transition hover:border-white/20 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed"
                >
                  <ChevronLeft className="h-3 w-3" />
                  Previous
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                  className="inline-flex items-center gap-1 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium transition hover:border-white/20 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed"
                >
                  Next
                  <ChevronRight className="h-3 w-3" />
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </Shell>
  );
}
