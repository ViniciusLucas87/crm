"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Sparkles, TrendingUp, Target, Clock, ArrowRight, AlertTriangle, CheckCircle } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

type AssessmentIntel = {
  id: string;
  automation_score: number;
  primary_pain_point: string | null;
  estimated_annual_savings: number;
  recommended_solution_categories: string[];
  urgency: string | null;
  next_best_action: string | null;
  current_process_summary: string | null;
  estimated_weekly_hours: number;
  discovery_questions: string[];
  likely_decision_maker: string | null;
  project_size_band: string | null;
};

export default function AssessmentIntelligenceCard({ leadId }: { leadId: number | string }) {
  const [data, setData] = useState<AssessmentIntel | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch the most recent assessment for this lead's company
    const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
    fetch(`${apiBase}/api/v1/assessments/by-lead/${leadId}`)
      .then(r => r.ok ? r.json() : null)
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [leadId]);

  if (loading) return <Skeleton className="h-48 w-full rounded-xl" />;
  if (!data) return null;

  const urgencyColors: Record<string, string> = {
    critical: "bg-red-100 text-red-800", high: "bg-orange-100 text-orange-800",
    medium: "bg-yellow-100 text-yellow-800", low: "bg-green-100 text-green-800",
  };

  return (
    <Card className="p-5 border-l-4 border-l-[#0B1526]">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-[#0B1526]" /> Assessment Intelligence
        </h3>
        <Link href={`/assessments/${data.id}`} className="text-xs text-blue-600 hover:underline flex items-center gap-1">
          Full Report <ArrowRight className="w-3 h-3" />
        </Link>
      </div>

      {/* Score */}
      <div className="flex items-center gap-3 mb-4">
        <div className="text-3xl font-bold text-[#0B1526]">{data.automation_score}<span className="text-lg text-gray-400">/100</span></div>
        <Badge className={urgencyColors[data.urgency || "medium"]}>{data.urgency?.toUpperCase()}</Badge>
      </div>

      {/* Key details */}
      <div className="space-y-2 text-sm">
        <IntelLine icon={Target} label="Primary pain" value={data.primary_pain_point} />
        <IntelLine icon={TrendingUp} label="Estimated savings" value={`$${data.estimated_annual_savings?.toLocaleString()}/year`} highlight />
        <IntelLine icon={CheckCircle} label="Recommended solution" value={data.recommended_solution_categories?.[0]} />
        <IntelLine icon={AlertTriangle} label="Current process" value={data.current_process_summary} />
        <IntelLine icon={Clock} label="Weekly hours" value={data.estimated_weekly_hours ? `${data.estimated_weekly_hours}h` : null} />
        <IntelLine icon={ArrowRight} label="Next action" value={data.next_best_action} highlight />
      </div>

      <div className="mt-3 pt-3 border-t border-gray-100">
        <p className="text-xs text-gray-400">
          Decision maker: {data.likely_decision_maker || "—"} · Project: {data.project_size_band || "—"}
        </p>
      </div>
    </Card>
  );
}

function IntelLine({ icon: Icon, label, value, highlight }: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string | null | undefined;
  highlight?: boolean;
}) {
  if (!value) return null;
  return (
    <div className="flex items-start gap-2">
      <Icon className={`w-3.5 h-3.5 mt-0.5 shrink-0 ${highlight ? "text-[#0B1526]" : "text-gray-400"}`} />
      <div>
        <span className="text-xs text-gray-500">{label}: </span>
        <span className={`text-xs ${highlight ? "text-[#0B1526] font-semibold" : "text-gray-700"}`}>{value}</span>
      </div>
    </div>
  );
}
