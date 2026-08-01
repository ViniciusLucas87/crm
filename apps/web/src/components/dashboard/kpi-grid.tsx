import { BriefcaseBusiness, Building2, CalendarCheck2, HandCoins, Inbox, MessageCircleReply, Target, Timer, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { cn } from "@/lib/cn";
import type { DashboardSummary } from "@/lib/types";

type KpiGridProps = {
  summary: DashboardSummary;
};

type KpiCardData = {
  label: string;
  value: string | number;
  icon: typeof Timer;
  secondary?: {
    label: string;
    trend?: "up" | "down" | "neutral";
  };
  accent: string;
};

const currency = new Intl.NumberFormat("en-CA", { style: "currency", currency: "CAD", maximumFractionDigits: 0 });

function TrendIcon({ trend }: { trend?: "up" | "down" | "neutral" }) {
  if (!trend || trend === "neutral") return <Minus className="h-3 w-3" />;
  return trend === "up" ? <TrendingUp className="h-3 w-3 text-emerald-400" /> : <TrendingDown className="h-3 w-3 text-red-400" />;
}

function KpiCard({ label, value, icon: Icon, secondary, accent }: KpiCardData) {
  return (
    <div
      className={cn(
        "group relative overflow-hidden rounded-2xl border border-white/10 bg-slate-900/60 p-5 shadow-[0_0_0_1px_rgba(255,255,255,0.03)] backdrop-blur transition-all duration-300 hover:-translate-y-0.5 hover:border-white/15 hover:shadow-lg",
      )}
    >
      <div className="mb-4 inline-flex rounded-xl border border-white/10 p-2 transition-colors group-hover:border-white/20" style={{ backgroundColor: `${accent}15`, color: accent }}>
        <Icon className="h-4 w-4" />
      </div>
      <p className="text-sm font-medium text-slate-400">{label}</p>
      <p className="mt-1 text-2xl font-semibold tracking-tight text-white">{value}</p>
      {secondary && (
        <div className="mt-2 flex items-center gap-1.5 text-xs text-slate-500">
          <TrendIcon trend={secondary.trend} />
          <span>{secondary.label}</span>
        </div>
      )}
    </div>
  );
}

export function KpiGrid({ summary }: KpiGridProps) {
  const cards: KpiCardData[] = [
    {
      label: "Tasks Today",
      value: summary.tasksToday,
      icon: Timer,
      accent: "#22d3ee",
      secondary: summary.tasksToday > 0 ? { label: `${summary.tasksToday} remaining`, trend: "neutral" } : { label: "All caught up", trend: "up" },
    },
    {
      label: "Companies",
      value: summary.companies,
      icon: Building2,
      accent: "#a78bfa",
      secondary: { label: `${summary.companies} total accounts`, trend: "neutral" },
    },
    {
      label: "Active Opportunities",
      value: summary.activeOpportunities,
      icon: Target,
      accent: "#f472b6",
      secondary: { label: "Open pipeline deals", trend: "neutral" },
    },
    {
      label: "Meetings",
      value: summary.meetings,
      icon: CalendarCheck2,
      accent: "#34d399",
      secondary: { label: summary.meetings > 0 ? "Scheduled this week" : "None scheduled", trend: "neutral" },
    },
    {
      label: "Pipeline Value",
      value: currency.format(summary.pipelineValue),
      icon: HandCoins,
      accent: "#fb923c",
      secondary: { label: "Total open value", trend: "neutral" },
    },
    {
      label: "Won Deals",
      value: summary.wonDeals,
      icon: MessageCircleReply,
      accent: "#38bdf8",
      secondary: { label: summary.wonDeals > 0 ? "Closed won" : "No wins yet", trend: summary.wonDeals > 0 ? "up" : "neutral" },
    },
    {
      label: "Revenue Forecast",
      value: currency.format(summary.revenueForecast),
      icon: BriefcaseBusiness,
      accent: "#fbbf24",
      secondary: { label: "Projected revenue", trend: "neutral" },
    },
    {
      label: "Activities Due",
      value: summary.activitiesDueToday,
      icon: Inbox,
      accent: "#f87171",
      secondary: summary.activitiesDueToday > 0 ? { label: `${summary.activitiesDueToday} due today`, trend: "down" } : { label: "Nothing due", trend: "up" },
    },
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {cards.map((card) => (
        <KpiCard key={card.label} {...card} />
      ))}
    </div>
  );
}
