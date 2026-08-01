"use client";

import type { AssessmentResults } from "@/lib/assessment";
import { Button } from "@/components/ui/button";
import { siteConfig } from "@/lib/site-config";
import {
  Clock,
  DollarSign,
  TrendingUp,
  Lightbulb,
  Users,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
} from "lucide-react";

interface ResultsStepProps {
  results: AssessmentResults | null;
  requestId: string | null;
  submitStatus: "persisted" | "unavailable" | null;
  submitting: boolean;
  submitError: string | null;
  storageFailed: boolean;
  onReset: () => void;
  onRetry: () => Promise<void>;
  onBack: () => void;
}

export function ResultsStep({
  results,
  requestId,
  submitStatus,
  submitting,
  submitError,
  storageFailed,
  onReset,
  onRetry,
  onBack,
}: ResultsStepProps) {
  if (!results) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-semibold text-pns-text-primary mb-4">
          Unable to calculate results
        </h2>
        <p className="text-pns-text-muted mb-6">
          Please go back and complete all steps.
        </p>
        <Button variant="primary" onClick={onBack}>
          Go Back
        </Button>
      </div>
    );
  }

  const formatHours = (n: number) => Math.round(n).toLocaleString();
  const formatMoney = (n: number) =>
    new Intl.NumberFormat("en-CA", {
      style: "currency",
      currency: "CAD",
      maximumFractionDigits: 0,
    }).format(n);

  return (
    <div>
      <h2 className="text-2xl font-semibold text-pns-text-primary mb-1">
        Your Operations Assessment
      </h2>

      {/* Submission status: CRM confirmed durable persistence */}
      {submitStatus === "persisted" && (
        <div
          className="mt-4 p-4 rounded-[10px] bg-emerald-50 border border-emerald-200 flex items-start gap-3"
          role="status"
          aria-live="polite"
        >
          <CheckCircle2 className="w-5 h-5 text-emerald-600 mt-0.5 shrink-0" aria-hidden="true" />
          <div>
            <p className="text-sm font-medium text-emerald-800">
              Assessment submitted successfully
            </p>
            <p className="text-xs text-emerald-700 mt-1">
              We&apos;ll review your results and follow up within 1 business day.
            </p>
            {requestId && (
              <p className="text-xs text-emerald-600/70 mt-1 font-mono" aria-label={`Reference number ${requestId}`}>
                Ref: {requestId}
              </p>
            )}
          </div>
        </div>
      )}

      {/* Submission status: CRM unavailable — browser recovery active */}
      {submitStatus === "unavailable" && (
        <div
          className="mt-4 p-4 rounded-[10px] bg-yellow-50 border border-yellow-200"
          role="alert"
          aria-live="assertive"
        >
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-yellow-700 mt-0.5 shrink-0" aria-hidden="true" />
            <div>
              <p className="text-sm font-medium text-yellow-800">
                Couldn&apos;t reach our processing system
              </p>
              <p className="text-xs text-yellow-700 mt-1">
                {storageFailed
                  ? "We couldn&apos;t submit your assessment or save a recovery copy. Please try again or contact us directly."
                  : "Your form data is saved in this browser. You can retry now, or email us at "}
                {!storageFailed && (
                  <a
                    href="mailto:hello@pacificnorthsystems.com"
                    className="underline font-medium"
                  >
                    hello@pacificnorthsystems.com
                  </a>
                )}
                {!storageFailed && " and we&apos;ll review your operations personally."}
              </p>
              {requestId && (
                <p className="text-xs text-yellow-600/70 mt-1 font-mono" aria-label={`Reference number ${requestId}`}>
                  Ref: {requestId}
                </p>
              )}
            </div>
          </div>
          {submitError && (
            <p className="text-xs text-red-600 mt-2" role="alert">{submitError}</p>
          )}
          <Button
            variant="outline"
            className="mt-3 w-full"
            onClick={onRetry}
            disabled={submitting}
            aria-label={submitting ? "Retrying submission" : "Retry submission"}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${submitting ? "animate-spin" : ""}`} aria-hidden="true" />
            {submitting ? "Retrying…" : "Retry Submission"}
          </Button>
        </div>
      )}

      {/* Score */}
      <div className="mt-6 p-6 rounded-[16px] bg-pns-soft-blue text-center">
        <p className="text-sm text-pns-text-muted uppercase tracking-wide">
          Operational Efficiency Score
        </p>
        <p className="text-5xl font-bold text-pns-text-primary mt-2">
          {results.opportunityScore}
        </p>
        <p className="text-sm text-pns-text-muted mt-1">
          {results.scoreInterpretation}
        </p>
      </div>

      {/* Key metrics */}
      <div className="mt-8 grid grid-cols-1 sm:grid-cols-2 gap-4">
        <MetricCard
          icon={Clock}
          label="Estimated Weekly Time Lost"
          value={`${formatHours(results.estimatedWeeklyHours)} hrs`}
          subtitle={`~${formatHours(results.estimatedAnnualHours)} hrs/year across ~${results.estimatedPeopleCount} ${results.estimatedPeopleCount === 1 ? "person" : "people"}`}
        />
        <MetricCard
          icon={DollarSign}
          label="Estimated Annual Labour Cost"
          value={formatMoney(results.estimatedAnnualLabourCost)}
          subtitle="Current cost of repetitive manual work"
        />
        <MetricCard
          icon={TrendingUp}
          label="Potential Annual Savings"
          value={formatMoney(results.estimatedAnnualSavings)}
          subtitle="Through automation and process improvement"
        />
        <MetricCard
          icon={Users}
          label="AI Readiness"
          value={results.aiReadiness.label}
          subtitle="Based on your current processes"
        />
      </div>

      {/* Top opportunities */}
      {results.topOpportunities.length > 0 && (
        <div className="mt-10">
          <h3 className="text-lg font-semibold text-pns-text-primary mb-4">
            Top Automation Opportunities
          </h3>
          <div className="space-y-3">
            {results.topOpportunities.map((opp) => (
              <div
                key={opp.rank}
                className="p-5 rounded-[14px] border border-pns-assessment-input-border bg-white hover:border-pns-text-primary/20 transition-colors"
              >
                <div className="flex items-start gap-3">
                  <span className="shrink-0 w-7 h-7 rounded-full bg-pns-text-primary text-white text-sm font-bold flex items-center justify-center mt-0.5">
                    {opp.rank}
                  </span>
                  <div>
                    <p className="font-semibold text-pns-text-primary text-[15px]">
                      {opp.label}
                    </p>
                    <p className="text-sm text-pns-text-muted mt-1 leading-relaxed">
                      {opp.description}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Assumptions */}
      <div className="mt-10 p-5 rounded-[14px] bg-pns-assessment-panel">
        <div className="flex items-start gap-2">
          <Lightbulb className="w-4 h-4 text-pns-text-muted mt-0.5 shrink-0" />
          <div>
            <p className="text-sm font-medium text-pns-text-primary mb-2">
              About this estimate
            </p>
            <ul className="space-y-1.5">
              {results.assumptions.map((a, i) => (
                <li key={i} className="text-xs text-pns-text-muted leading-relaxed">
                  {a}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* CTA */}
      <div className="mt-8 p-6 rounded-[16px] bg-pns-soft-blue text-center">
        <h3 className="text-lg font-bold text-pns-text-primary">
          Want a detailed, personalized assessment?
        </h3>
        <p className="mt-1 text-sm text-pns-text-muted">
          Book a free 30-minute Operations Audit and we&apos;ll review your results together.
        </p>
        <div className="mt-4 flex flex-col sm:flex-row items-center justify-center gap-3">
          <Button
            variant="primary"
            href={siteConfig.contact.calendlyAudit}
            external
          >
            Book a 30-minute Operations Audit
          </Button>
          <Button variant="ghost" size="default" onClick={onReset}>
            Start Over
          </Button>
        </div>
      </div>

      {/* Back */}
      <div className="mt-6 flex justify-start">
        <Button variant="ghost" size="sm" onClick={onBack}>
          ← Adjust answers
        </Button>
      </div>
    </div>
  );
}

function MetricCard({
  icon: Icon,
  label,
  value,
  subtitle,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
  subtitle: string;
}) {
  return (
    <div className="p-5 rounded-[14px] border border-pns-assessment-input-border bg-white">
      <Icon className="w-5 h-5 text-pns-text-muted mb-2" aria-hidden="true" />
      <p className="text-xs text-pns-text-muted uppercase tracking-wide">{label}</p>
      <p className="text-lg font-bold text-pns-text-primary mt-1">{value}</p>
      <p className="text-xs text-pns-text-muted mt-1">{subtitle}</p>
    </div>
  );
}

