"use client";

import { useEffect, useState } from "react";
import type { Route } from "next";
import { useRouter } from "next/navigation";
import { useUser } from "@clerk/nextjs";
import { CalendarCheck2, Phone, Target, Zap } from "lucide-react";
import { KpiGrid } from "@/components/dashboard/kpi-grid";
import { RecentActivity } from "@/components/dashboard/recent-activity";
import { KpiSkeleton } from "@/components/ui/skeleton";
import { Card } from "@/components/ui/card";
import { ApiError, fetchDashboardSummary } from "@/lib/api";
import type { DashboardSummary } from "@/lib/types";

const signInRoute = "/sign-in" as Route;

function getGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 17) return "Good afternoon";
  return "Good evening";
}

function getFirstName(fullName: string | null | undefined): string {
  if (!fullName) return "";
  return fullName.split(" ")[0];
}

function getTodayDate(): string {
  return new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" });
}

export function DashboardScreen() {
  const router = useRouter();
  const { user } = useUser();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  const greeting = getGreeting();
  const firstName = getFirstName(user?.fullName);
  const today = getTodayDate();

  function missionPulse(metric: number): "green" | "amber" | "red" {
    if (metric === 0) return "green";
    if (metric <= 3) return "amber";
    return "red";
  }

  const pulseBorder: Record<string, string> = {
    green: "border-emerald-400/20 bg-emerald-400/5",
    amber: "border-amber-400/20 bg-amber-400/5",
    red: "border-red-400/20 bg-red-400/5",
  };

  const pulseDot: Record<string, string> = {
    green: "bg-emerald-400",
    amber: "bg-amber-400",
    red: "bg-red-400",
  };

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const nextSummary = await fetchDashboardSummary();
        if (!cancelled) {
          setSummary(nextSummary);
          setError(null);
        }
      } catch (err) {
        if (err instanceof ApiError && err.status === 401) {
          router.replace(signInRoute);
          return;
        }

        if (!cancelled) {
          if (err instanceof ApiError && err.status === 403) {
            setError("Your account is signed in, but it does not have permission to view the dashboard.");
          } else if (err instanceof ApiError && err.status >= 500) {
            setError("The dashboard service is temporarily unavailable. Please try again shortly.");
          } else {
            setError(err instanceof Error ? err.message : "Failed to load dashboard summary.");
          }
        }
      }
    };

    void load();

    return () => {
      cancelled = true;
    };
  }, [router]);

  if (error) {
    return (
      <Card>
        <h3 className="text-lg font-semibold text-white">Dashboard unavailable</h3>
        <p className="mt-2 text-sm text-slate-300">{error}</p>
      </Card>
    );
  }

  if (summary === null) {
    return (
      <div className="space-y-6">
        <section>
          <h3 className="mb-4 text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Key Metrics</h3>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <KpiSkeleton key={i} />
            ))}
          </div>
        </section>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Hero */}
      <section className="relative overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-slate-900/80 via-slate-900/60 to-cyan-950/40 p-6 md:p-8">
        <div className="relative z-10">
          <p className="text-sm font-medium text-cyan-300/80">
            {greeting}{firstName ? `, ${firstName}` : ""} 👋
          </p>
          <p className="mt-1 text-xs text-slate-500">{today}</p>
          <p className="mt-3 text-sm text-slate-400">Welcome back. Here&apos;s your business briefing for today. <a href="/ai/daily-brief" className="text-cyan-400 transition hover:text-cyan-300">View full brief →</a></p>

          <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <div className={`flex items-center gap-3 rounded-xl border px-4 py-3 ${pulseBorder[missionPulse(summary.tasksToday)]}`}>
              <span className={`h-2 w-2 rounded-full ${pulseDot[missionPulse(summary.tasksToday)]}`} />
              <Phone className="h-4 w-4 text-cyan-400" />
              <span className="text-sm text-slate-300">
                {summary.tasksToday > 0 ? `${summary.tasksToday} follow-ups due` : "No follow-ups today"}
              </span>
            </div>
            <div className={`flex items-center gap-3 rounded-xl border px-4 py-3 ${pulseBorder[missionPulse(summary.meetings)]}`}>
              <span className={`h-2 w-2 rounded-full ${pulseDot[missionPulse(summary.meetings)]}`} />
              <CalendarCheck2 className="h-4 w-4 text-emerald-400" />
              <span className="text-sm text-slate-300">
                {summary.meetings > 0 ? `${summary.meetings} meetings today` : "No meetings today"}
              </span>
            </div>
            <div className={`flex items-center gap-3 rounded-xl border px-4 py-3 ${pulseBorder[summary.pipelineValue > 0 ? "amber" : "green"]}`}>
              <span className={`h-2 w-2 rounded-full ${pulseDot[summary.pipelineValue > 0 ? "amber" : "green"]}`} />
              <Target className="h-4 w-4 text-amber-400" />
              <span className="text-sm text-slate-300">
                {summary.pipelineValue > 0 ? `Pipeline: ${new Intl.NumberFormat("en-CA", { style: "currency", currency: "CAD", maximumFractionDigits: 0 }).format(summary.pipelineValue)}` : "Pipeline is empty"}
              </span>
            </div>
            <div className={`flex items-center gap-3 rounded-xl border px-4 py-3 ${pulseBorder[summary.activeOpportunities]}`}>
              <span className={`h-2 w-2 rounded-full ${pulseDot[missionPulse(summary.activeOpportunities)]}`} />
              <Zap className="h-4 w-4 text-violet-400" />
              <span className="text-sm text-slate-300">
                {summary.activeOpportunities > 0 ? `${summary.activeOpportunities} active opportunities` : "Great day to prospect"}
              </span>
            </div>
          </div>
        </div>
        <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-cyan-500/5 blur-3xl" />
        <div className="absolute -bottom-10 -left-10 h-48 w-48 rounded-full bg-violet-500/5 blur-3xl" />
      </section>

      {/* KPIs */}
      <section>
        <h3 className="mb-4 text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Key Metrics</h3>
        <KpiGrid summary={summary} />
      </section>

      {/* Two-column: Priorities + Recent Activity */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Today's Priorities — AI-Powered */}
        <Card>
          <h3 className="text-sm font-semibold uppercase tracking-[0.12em] text-slate-400">Today&apos;s Priorities</h3>
          {summary.tasksToday > 0 ? (
            <p className="mt-2 text-sm text-slate-300">{summary.tasksToday} task{summary.tasksToday !== 1 ? "s" : ""} due today</p>
          ) : (
            <p className="mt-2 text-sm text-slate-500">No tasks due today — great time to prospect.</p>
          )}
          {summary.activeOpportunities > 0 && (
            <p className="mt-1 text-sm text-amber-300">{summary.activeOpportunities} active opportunit{summary.activeOpportunities !== 1 ? "ies" : "y"} in pipeline</p>
          )}
          <div className="mt-3">
            <a href="/ai/daily-brief" className="text-xs text-cyan-400 transition hover:text-cyan-300">View AI Daily Brief →</a>
          </div>
        </Card>

        {/* Recent Activity */}
        <RecentActivity items={[]} />
      </div>

      {/* Bottom row: AI Insights + Upcoming */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* AI Insights — Powered by Sales Copilot */}
        <Card>
          <h3 className="text-sm font-semibold uppercase tracking-[0.12em] text-slate-400">AI Insights</h3>
          <p className="mt-4 text-sm text-slate-500">Your AI Sales Copilot analyzes your CRM data to surface actionable insights.</p>
          <div className="mt-4 space-y-2">
            <a href="/ai/daily-brief" className="flex items-center gap-3 rounded-xl border border-cyan-400/10 bg-cyan-400/5 px-4 py-3 text-sm text-cyan-300 transition hover:bg-cyan-400/10">
              View your daily AI briefing →
            </a>
            <a href="/ai/explorer" className="flex items-center gap-3 rounded-xl border border-white/5 px-4 py-3 text-sm text-slate-400 transition hover:bg-white/[0.02]">
              Find new opportunities →
            </a>
          </div>
        </Card>

        {/* Upcoming Meetings */}
        <Card>
          <h3 className="text-sm font-semibold uppercase tracking-[0.12em] text-slate-400">Upcoming Meetings</h3>
          <p className="mt-4 text-sm text-slate-500">Your scheduled meetings and follow-ups will appear here.</p>
          <div className="mt-4 space-y-2">
            <div className="flex items-center gap-3 rounded-xl border border-dashed border-white/10 bg-white/[0.02] px-4 py-3 text-sm text-slate-600">
              Meetings coming in Sprint 2
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}