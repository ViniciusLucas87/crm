"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  Sparkles, TrendingUp, Zap, Target, Lightbulb, Clock,
  Phone, Mail, FileText, AlertTriangle, CheckCircle, Users,
  BarChart3, ArrowRight, ExternalLink
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

type AssessmentDetail = {
  id: string;
  status: string;
  created_at: string | null;
  company_id: number | null;
  contact_id: number | null;
  lead_id: number | null;
  automation_score: number;
  score_interpretation: string;
  raw_answers: Record<string, unknown>;
  industry: string | null;
  employee_range: string | null;
  estimated_weekly_hours: number;
  estimated_annual_hours: number;
  estimated_annual_savings: number;
  estimated_people_count: number;
  calculated_output: Record<string, unknown>;
  primary_pain_point: string | null;
  secondary_pain_points: string[];
  current_process_summary: string | null;
  root_cause: string | null;
  business_impact: string | null;
  recommended_solution_categories: string[];
  recommendation_reasons: string[];
  urgency: string | null;
  buying_signals: string[];
  likely_decision_maker: string | null;
  project_size_band: string | null;
  next_best_action: string | null;
  discovery_questions: string[];
  intelligence_version: string | null;
  intelligence_confidence: number | null;
  pdf_status: string;
  email_status: string;
  assessment_version: string;
};

export default function AssessmentDetailPage() {
  const params = useParams();
  const id = params?.id as string;
  const [data, setData] = useState<AssessmentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    fetch(`http://localhost:8000/api/v1/assessments/${id}`)
      .then(r => { if (!r.ok) throw new Error("Not found"); return r.json(); })
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <AssessmentSkeleton />;
  if (error || !data) return <ErrorState error={error} />;

  const answers = data.raw_answers || {};
  const urgencyColors: Record<string, string> = {
    critical: "bg-red-100 text-red-800 border-red-200",
    high: "bg-orange-100 text-orange-800 border-orange-200",
    medium: "bg-yellow-100 text-yellow-800 border-yellow-200",
    low: "bg-green-100 text-green-800 border-green-200",
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Assessment Detail</h1>
          <p className="text-sm text-gray-500 mt-1">
            ID: {data.id} · v{data.assessment_version} · {data.created_at ? new Date(data.created_at).toLocaleDateString() : ""}
          </p>
        </div>
        <div className="flex gap-2">
          <Link href={`/leads/${data.lead_id || ""}`} className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-lg border hover:bg-gray-50">
            View Lead <ArrowRight className="w-4 h-4" />
          </Link>
          <Link href={`/companies/${data.company_id || ""}`} className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-lg border hover:bg-gray-50">
            View Company <ExternalLink className="w-4 h-4" />
          </Link>
        </div>
      </div>

      {/* Score Card */}
      <Card className="p-6 bg-gradient-to-br from-[#0B1526] to-[#1A2744] text-white">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm text-gray-400 uppercase tracking-wide">Automation Opportunity Score</p>
            <p className="text-5xl font-bold mt-2">{data.automation_score}<span className="text-2xl text-gray-400">/100</span></p>
            <p className="text-sm text-gray-300 mt-2 max-w-lg">{data.score_interpretation}</p>
          </div>
          <div className="flex flex-col gap-2 items-end">
            <Badge className={urgencyColors[data.urgency || "medium"] || ""}>
              {data.urgency?.toUpperCase()} URGENCY
            </Badge>
            <Badge variant="outline" className="text-gray-300 border-gray-600">
              {data.project_size_band?.toUpperCase()} PROJECT
            </Badge>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Column */}
        <div className="lg:col-span-2 space-y-6">
          {/* Raw Answers */}
          <Card className="p-5">
            <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide mb-4 flex items-center gap-2">
              <FileText className="w-4 h-4" /> Submitted Answers
            </h3>
            <dl className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
              <AnswerRow label="Industry" value={(answers.businessType as string) || data.industry || "—"} />
              <AnswerRow label="People Involved" value={(answers.peopleInvolved as string) || data.employee_range || "—"} />
              <AnswerRow label="Weekly Time Spent" value={(answers.weeklyTimeSpent as string) || "—"} />
              <AnswerRow label="Current Process" value={(answers.currentProcess as string) || data.current_process_summary || "—"} />
              <AnswerRow label="Main Problems" value={Array.isArray(answers.mainProblems) ? (answers.mainProblems as string[]).join(", ") : "—"} />
              <AnswerRow label="Additional Details" value={(answers.additionalDetails as string) || "—"} span={2} />
            </dl>
          </Card>

          {/* Calculated Outputs */}
          <Card className="p-5">
            <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide mb-4 flex items-center gap-2">
              <BarChart3 className="w-4 h-4" /> Calculated Outputs
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <MetricBox label="Weekly Hours" value={data.estimated_weekly_hours} />
              <MetricBox label="Annual Hours" value={data.estimated_annual_hours?.toLocaleString()} />
              <MetricBox label="Annual Savings" value={`$${data.estimated_annual_savings?.toLocaleString()}`} highlight />
              <MetricBox label="People Affected" value={data.estimated_people_count || (answers.peopleInvolved as string) || "—"} />
            </div>
          </Card>

          {/* Intelligence */}
          <Card className="p-5">
            <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide mb-4 flex items-center gap-2">
              <Sparkles className="w-4 h-4" /> Sales Intelligence
            </h3>
            <div className="space-y-4">
              <IntelRow icon={Target} label="Primary Pain Point" value={data.primary_pain_point} />
              <IntelRow icon={Zap} label="Root Cause" value={data.root_cause} />
              <IntelRow icon={TrendingUp} label="Business Impact" value={data.business_impact} />
              <IntelRow icon={Users} label="Likely Decision Maker" value={data.likely_decision_maker} />
              <IntelRow icon={AlertTriangle} label="Buying Signals" value={data.buying_signals?.join(" · ")} />
              <IntelRow icon={Lightbulb} label="Next Best Action" value={data.next_best_action} highlight />
            </div>
          </Card>

          {/* Recommended Solutions */}
          <Card className="p-5">
            <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide mb-4">Recommended PNS Solutions</h3>
            <div className="space-y-3">
              {data.recommended_solution_categories?.map((sol, i) => (
                <div key={sol} className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg">
                  <CheckCircle className="w-5 h-5 text-blue-600 mt-0.5 shrink-0" />
                  <div>
                    <p className="text-sm font-semibold text-gray-900">{sol}</p>
                    <p className="text-xs text-gray-600 mt-0.5">{data.recommendation_reasons?.[i] || ""}</p>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* Discovery Questions */}
          <Card className="p-5">
            <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide mb-4 flex items-center gap-2">
              <Phone className="w-4 h-4" /> Discovery Questions
            </h3>
            <ol className="space-y-2 list-decimal list-inside text-sm text-gray-700">
              {data.discovery_questions?.map((q, i) => (
                <li key={i} className="leading-relaxed">{q}</li>
              ))}
            </ol>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Status Card */}
          <Card className="p-5">
            <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide mb-3">Status</h3>
            <div className="space-y-2 text-sm">
              <StatusRow label="PDF" status={data.pdf_status} />
              <StatusRow label="Email" status="delivered" />
              <StatusRow label="Intelligence" status={data.intelligence_version || "pending"} />
              <StatusRow label="Knowledge Graph" status="ingested" />
            </div>
          </Card>

          {/* Contact Actions */}
          <Card className="p-5">
            <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide mb-3">Actions</h3>
            <div className="space-y-2">
              <Button variant="outline" className="w-full justify-start gap-2" size="sm">
                <Phone className="w-4 h-4" /> Call Contact
              </Button>
              <Button variant="outline" className="w-full justify-start gap-2" size="sm">
                <Mail className="w-4 h-4" /> Email Contact
              </Button>
              <Link href="/leads" className="w-full">
                <Button className="w-full justify-start gap-2 bg-[#0B1526] hover:bg-[#1A2744]" size="sm">
                  <Target className="w-4 h-4" /> View in CRM
                </Button>
              </Link>
            </div>
          </Card>

          {/* Metadata */}
          <Card className="p-5">
            <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide mb-3">Metadata</h3>
            <div className="text-xs text-gray-500 space-y-1">
              <p>Version: {data.assessment_version}</p>
              <p>Intelligence: v{data.intelligence_version || "—"}</p>
              <p>Confidence: {data.intelligence_confidence ? `${(data.intelligence_confidence * 100).toFixed(0)}%` : "—"}</p>
              <p className="text-gray-400 mt-2">Rule-based · AI enrichment pending</p>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

function AnswerRow({ label, value, span = 1 }: { label: string; value: string; span?: number }) {
  return (
    <div className={span === 2 ? "sm:col-span-2" : ""}>
      <dt className="text-gray-500 text-xs uppercase">{label}</dt>
      <dd className="text-gray-900 mt-0.5">{value}</dd>
    </div>
  );
}

function MetricBox({ label, value, highlight }: { label: string; value: string | number; highlight?: boolean }) {
  return (
    <div className="bg-gray-50 rounded-lg p-3 text-center">
      <p className="text-xs text-gray-500 uppercase">{label}</p>
      <p className={`text-lg font-bold mt-1 ${highlight ? "text-green-600" : "text-gray-900"}`}>{value}</p>
    </div>
  );
}

function IntelRow({ icon: Icon, label, value, highlight }: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string | null | undefined;
  highlight?: boolean;
}) {
  return (
    <div className="flex items-start gap-2">
      <Icon className={`w-4 h-4 mt-0.5 shrink-0 ${highlight ? "text-[#0B1526]" : "text-gray-400"}`} />
      <div>
        <p className="text-xs text-gray-500 uppercase">{label}</p>
        <p className={`text-sm ${highlight ? "text-[#0B1526] font-semibold" : "text-gray-700"}`}>{value || "—"}</p>
      </div>
    </div>
  );
}

function StatusRow({ label, status }: { label: string; status: string }) {
  const colors: Record<string, string> = {
    completed: "text-green-600", delivered: "text-green-600",
    pending: "text-yellow-600", queued: "text-yellow-600",
    ingested: "text-green-600", failed: "text-red-600",
  };
  return (
    <div className="flex justify-between">
      <span className="text-gray-500">{label}</span>
      <span className={`font-medium ${colors[status] || "text-gray-600"}`}>{status}</span>
    </div>
  );
}

function AssessmentSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-8 w-64" />
      <Skeleton className="h-40 w-full rounded-xl" />
      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 space-y-4">
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-48 w-full" />
        </div>
        <Skeleton className="h-64 w-full" />
      </div>
    </div>
  );
}

function ErrorState({ error }: { error: string | null }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <AlertTriangle className="w-12 h-12 text-gray-400 mb-4" />
      <h2 className="text-lg font-semibold text-gray-900">Assessment Not Found</h2>
      <p className="text-sm text-gray-500 mt-1">{error || "The assessment could not be loaded."}</p>
      <Link href="/leads" className="mt-4 text-sm text-blue-600 hover:underline">← Back to Leads</Link>
    </div>
  );
}
