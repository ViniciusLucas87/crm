"use client";

import React, { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ToolPage, ContactStep } from "@/components/free-tools/tool-page";
import { Calendar, Users } from "lucide-react";
import { track } from "@/lib/analytics";

const SLUG = "automation-roi-calculator";

/* ------------------------------------------------------------------ */
/*  Calculations                                                       */
/* ------------------------------------------------------------------ */

interface ROIInput {
  implementationCost: number;
  monthlyRecurringCost: number;
  peopleAffected: number;
  hoursSavedPerWeek: number;
  loadedHourlyCost: number;
  additionalMonthlyRevenue: number;
}

interface ROIResult {
  grossMonthlyBenefit: number;
  grossAnnualBenefit: number;
  netYearOneBenefit: number;
  paybackMonths: number;
  yearOneROI: number;
  assumptionText: string;
}

function calculateROI(input: ROIInput): ROIResult {
  const monthlyLabourSaving =
    input.peopleAffected * input.hoursSavedPerWeek * 4.33 * input.loadedHourlyCost;
  const grossMonthlyBenefit = monthlyLabourSaving + input.additionalMonthlyRevenue;
  const grossAnnualBenefit = grossMonthlyBenefit * 12;
  const totalYearOneCost = input.implementationCost + input.monthlyRecurringCost * 12;
  const netYearOneBenefit = grossAnnualBenefit - totalYearOneCost;
  const netMonthlyBenefit = grossMonthlyBenefit - input.monthlyRecurringCost;
  const paybackMonths =
    netMonthlyBenefit > 0
      ? Math.ceil((input.implementationCost / netMonthlyBenefit) * 10) / 10
      : Infinity;
  const yearOneROI =
    totalYearOneCost > 0
      ? Math.round(((netYearOneBenefit / totalYearOneCost) * 100) * 10) / 10
      : 0;

  const assumptionText = [
    `Labour saving: ${input.peopleAffected} people × ${input.hoursSavedPerWeek} hrs/week saved × 4.33 weeks/month × $${input.loadedHourlyCost}/hr loaded cost = $${Math.round(monthlyLabourSaving).toLocaleString()}/month.`,
    `Initial implementation cost: $${input.implementationCost.toLocaleString()}. Monthly recurring: $${input.monthlyRecurringCost.toLocaleString()}/month for support, hosting, and licensing.`,
    input.additionalMonthlyRevenue > 0
      ? `Additional monthly revenue estimate: $${input.additionalMonthlyRevenue.toLocaleString()}/month.`
      : `No additional revenue estimated. The projection is based on labour savings only and uses a conservative assumption.`,
    `Actual ROI depends on implementation quality, user adoption, process standardization, and ongoing optimization. These are directional estimates for business planning.`,
  ].join("\n\n");

  return {
    grossMonthlyBenefit: Math.round(grossMonthlyBenefit),
    grossAnnualBenefit: Math.round(grossAnnualBenefit),
    netYearOneBenefit: Math.round(netYearOneBenefit),
    paybackMonths,
    yearOneROI,
    assumptionText,
  };
}

/* ------------------------------------------------------------------ */
/*  Steps                                                               */
/* ------------------------------------------------------------------ */

function ImplementationCostStep({
  onNext, defaultValues,
}: { onNext: (d: Record<string, unknown>) => void; defaultValues?: Record<string, unknown> }) {
  const [value, setValue] = useState((defaultValues?.implementationCost as number) || 15000);
  return (
    <Card className="p-6 md:p-8" variant="elevated">
      <h3 className="font-heading font-semibold text-[20px] text-pns-text-primary mb-2">
        Estimated initial implementation cost
      </h3>
      <p className="text-pns-text-muted text-[15px] leading-relaxed mb-4">
        Enter a complete written estimate covering discovery, development, setup, security, migration, training, and contingency.
      </p>
      <div className="flex flex-wrap gap-3 mb-4">
        {[5000, 15000, 25000, 50000, 75000].map((v) => (
          <button
            key={v}
            onClick={() => setValue(v)}
            className={`h-11 px-4 rounded-[10px] border font-inter text-[15px] transition-colors ${
              value === v ? "border-[#051226] bg-[#051226] text-white" : "border-pns-assessment-input-border bg-pns-assessment-input-bg text-pns-text-primary hover:border-[#051226]/30"
            }`}
            aria-pressed={value === v}
          >
            ${v.toLocaleString()}
          </button>
        ))}
      </div>
      <label htmlFor="impl-cost" className="sr-only">Custom implementation cost</label>
      <div className="flex items-center gap-3">
        <span className="text-[15px] text-pns-text-muted">Custom: $</span>
        <input
          id="impl-cost"
          type="number"
          min={1000}
          max={500000}
          step={1000}
          value={value}
          onChange={(e) => setValue(Number(e.target.value))}
          className="w-28 h-11 rounded-[10px] border border-pns-assessment-input-border bg-pns-assessment-input-bg px-3 text-[15px] font-inter text-pns-text-primary text-center focus:outline-none focus:ring-2 focus:ring-[#051226]/20"
        />
        <span className="text-[15px] text-pns-text-muted">CAD</span>
      </div>
      <div className="flex justify-end mt-6">
        <Button onClick={() => { track("tool_step_completed", { tool: SLUG, step: 1 }); onNext({ implementationCost: value }); }}>
          Next
        </Button>
      </div>
    </Card>
  );
}

function RecurringCostStep({
  onNext, defaultValues,
}: { onNext: (d: Record<string, unknown>) => void; defaultValues?: Record<string, unknown> }) {
  const [value, setValue] = useState((defaultValues?.monthlyRecurringCost as number) || 500);
  return (
    <Card className="p-6 md:p-8" variant="elevated">
      <h3 className="font-heading font-semibold text-[20px] text-pns-text-primary mb-2">
        Estimated monthly recurring cost
      </h3>
      <p className="text-pns-text-muted text-[15px] leading-relaxed mb-4">
        Include hosting, support, usage, licensing, monitoring, maintenance, and vendor price changes.
      </p>
      <div className="flex flex-wrap gap-3 mb-4">
        {[200, 500, 1000, 1500, 2000].map((v) => (
          <button
            key={v}
            onClick={() => setValue(v)}
            className={`h-11 px-4 rounded-[10px] border font-inter text-[15px] transition-colors ${
              value === v ? "border-[#051226] bg-[#051226] text-white" : "border-pns-assessment-input-border bg-pns-assessment-input-bg text-pns-text-primary hover:border-[#051226]/30"
            }`}
            aria-pressed={value === v}
          >
            ${v.toLocaleString()}/mo
          </button>
        ))}
      </div>
      <label htmlFor="recurring-cost" className="sr-only">Custom recurring cost</label>
      <div className="flex items-center gap-3">
        <span className="text-[15px] text-pns-text-muted">Custom: $</span>
        <input
          id="recurring-cost"
          type="number"
          min={0}
          max={20000}
          step={50}
          value={value}
          onChange={(e) => setValue(Number(e.target.value))}
          className="w-28 h-11 rounded-[10px] border border-pns-assessment-input-border bg-pns-assessment-input-bg px-3 text-[15px] font-inter text-pns-text-primary text-center focus:outline-none focus:ring-2 focus:ring-[#051226]/20"
        />
        <span className="text-[15px] text-pns-text-muted">/mo CAD</span>
      </div>
      <div className="flex justify-between mt-6">
        <Button variant="ghost" onClick={() => onNext({ monthlyRecurringCost: value, _back: true })}>Back</Button>
        <Button onClick={() => { track("tool_step_completed", { tool: SLUG, step: 2 }); onNext({ monthlyRecurringCost: value }); }}>Next</Button>
      </div>
    </Card>
  );
}

function SavingsStep({
  onNext, defaultValues,
}: { onNext: (d: Record<string, unknown>) => void; defaultValues?: Record<string, unknown> }) {
  const [people, setPeople] = useState((defaultValues?.peopleAffected as number) || 3);
  const [hours, setHours] = useState((defaultValues?.hoursSavedPerWeek as number) || 10);
  const [cost, setCost] = useState((defaultValues?.loadedHourlyCost as number) || 35);

  return (
    <Card className="p-6 md:p-8" variant="elevated">
      <h3 className="font-heading font-semibold text-[20px] text-pns-text-primary mb-2">
        Labour savings estimate
      </h3>
      <p className="text-pns-text-muted text-[15px] leading-relaxed mb-6">
        How much time would automation save, and at what loaded cost?
      </p>
      <div className="space-y-4">
        <div>
          <label htmlFor="roi-people" className="block text-[14px] font-medium text-pns-text-primary mb-2">
            People affected
          </label>
          <input id="roi-people" type="number" min={1} max={200} value={people} onChange={(e) => setPeople(Number(e.target.value))}
            className="w-24 h-11 rounded-[10px] border border-pns-assessment-input-border bg-pns-assessment-input-bg px-3 text-[15px] font-inter text-pns-text-primary text-center focus:outline-none focus:ring-2 focus:ring-[#051226]/20" />
        </div>
        <div>
          <label htmlFor="roi-hours" className="block text-[14px] font-medium text-pns-text-primary mb-2">
            Hours saved per week per person
          </label>
          <input id="roi-hours" type="number" min={1} max={40} value={hours} onChange={(e) => setHours(Number(e.target.value))}
            className="w-24 h-11 rounded-[10px] border border-pns-assessment-input-border bg-pns-assessment-input-bg px-3 text-[15px] font-inter text-pns-text-primary text-center focus:outline-none focus:ring-2 focus:ring-[#051226]/20" />
        </div>
        <div>
          <label htmlFor="roi-cost" className="block text-[14px] font-medium text-pns-text-primary mb-2">
            Loaded hourly cost ($/hr CAD)
          </label>
          <input id="roi-cost" type="number" min={15} max={200} value={cost} onChange={(e) => setCost(Number(e.target.value))}
            className="w-24 h-11 rounded-[10px] border border-pns-assessment-input-border bg-pns-assessment-input-bg px-3 text-[15px] font-inter text-pns-text-primary text-center focus:outline-none focus:ring-2 focus:ring-[#051226]/20" />
        </div>
      </div>
      <div className="flex justify-between mt-6">
        <Button variant="ghost" onClick={() => onNext({ peopleAffected: people, hoursSavedPerWeek: hours, loadedHourlyCost: cost, _back: true })}>Back</Button>
        <Button onClick={() => { track("tool_step_completed", { tool: SLUG, step: 3 }); onNext({ peopleAffected: people, hoursSavedPerWeek: hours, loadedHourlyCost: cost }); }}>Next</Button>
      </div>
    </Card>
  );
}

function RevenueStep({
  onNext, defaultValues,
}: { onNext: (d: Record<string, unknown>) => void; defaultValues?: Record<string, unknown> }) {
  const [value, setValue] = useState((defaultValues?.additionalMonthlyRevenue as number) || 0);
  return (
    <Card className="p-6 md:p-8" variant="elevated">
      <h3 className="font-heading font-semibold text-[20px] text-pns-text-primary mb-2">
        Additional monthly revenue (optional)
      </h3>
      <p className="text-pns-text-muted text-[15px] leading-relaxed mb-6">
        If automation helps you close more deals, serve more clients, or launch new offerings, estimate the additional monthly revenue. Leave at $0 for a conservative estimate based only on labour savings.
      </p>
      <label htmlFor="additional-revenue" className="sr-only">Additional monthly revenue</label>
      <div className="flex items-center gap-3">
        <span className="text-[15px] text-pns-text-muted">$</span>
        <input id="additional-revenue" type="number" min={0} max={500000} step={500} value={value}
          onChange={(e) => setValue(Number(e.target.value))}
          className="w-32 h-11 rounded-[10px] border border-pns-assessment-input-border bg-pns-assessment-input-bg px-3 text-[15px] font-inter text-pns-text-primary text-center focus:outline-none focus:ring-2 focus:ring-[#051226]/20" />
        <span className="text-[15px] text-pns-text-muted">/mo CAD</span>
      </div>
      <div className="flex justify-between mt-6">
        <Button variant="ghost" onClick={() => onNext({ additionalMonthlyRevenue: value, _back: true })}>Back</Button>
        <Button onClick={() => { track("tool_completed", { tool: SLUG }); onNext({ additionalMonthlyRevenue: value }); }}>See results</Button>
      </div>
    </Card>
  );
}

/* ------------------------------------------------------------------ */
/*  Results                                                             */
/* ------------------------------------------------------------------ */

function Results({ values, onRestart }: { values: Record<string, unknown>; onRestart: () => void }) {
  const input: ROIInput = {
    implementationCost: (values.implementationCost as number) || 15000,
    monthlyRecurringCost: (values.monthlyRecurringCost as number) || 500,
    peopleAffected: (values.peopleAffected as number) || 3,
    hoursSavedPerWeek: (values.hoursSavedPerWeek as number) || 10,
    loadedHourlyCost: (values.loadedHourlyCost as number) || 35,
    additionalMonthlyRevenue: (values.additionalMonthlyRevenue as number) || 0,
  };

  const [showContact, setShowContact] = useState(false);
  const result = calculateROI(input);

  return (
    <div className="space-y-6">
      <Card className="p-6 md:p-8" variant="elevated">
        <h2 className="font-heading font-bold text-[22px] text-pns-text-primary mb-6">
          Your Automation ROI Estimate
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
          <div className="bg-pns-soft-blue rounded-[12px] p-4">
            <span className="text-[13px] text-pns-text-muted">Gross monthly benefit</span>
            <p className="text-[24px] font-bold text-pns-text-primary">
              ${result.grossMonthlyBenefit.toLocaleString()}
            </p>
          </div>
          <div className="bg-pns-soft-blue rounded-[12px] p-4">
            <span className="text-[13px] text-pns-text-muted">Gross annual benefit</span>
            <p className="text-[24px] font-bold text-pns-text-primary">
              ${result.grossAnnualBenefit.toLocaleString()}
            </p>
          </div>
          <div className="bg-pns-soft-blue rounded-[12px] p-4">
            <span className="text-[13px] text-pns-text-muted">Net first year benefit</span>
            <p className={`text-[24px] font-bold ${result.netYearOneBenefit >= 0 ? "text-green-700" : "text-pns-assessment-error"}`}>
              ${result.netYearOneBenefit.toLocaleString()}
            </p>
          </div>
          <div className="bg-pns-soft-blue rounded-[12px] p-4">
            <span className="text-[13px] text-pns-text-muted">First year ROI</span>
            <p className={`text-[24px] font-bold ${result.yearOneROI >= 0 ? "text-green-700" : "text-pns-assessment-error"}`}>
              {result.yearOneROI}%
            </p>
          </div>
        </div>

        {/* Payback */}
        <div className="bg-blue-50 border border-blue-200 rounded-[12px] p-4 mb-6">
          <div className="flex items-center gap-2">
            <Calendar className="w-5 h-5 text-blue-700" />
            <span className="font-semibold text-[16px] text-blue-800">
              Payback period:{" "}
              {result.paybackMonths === Infinity
                ? "Not reached (monthly benefit ≤ $0)"
                : `${result.paybackMonths} months`}
            </span>
          </div>
        </div>

        <details className="group">
          <summary className="text-[14px] text-pns-text-muted cursor-pointer hover:text-pns-text-primary transition-colors">
            How we calculated this
          </summary>
          <p className="mt-3 text-[14px] text-pns-text-muted leading-relaxed whitespace-pre-line">
            {result.assumptionText}
          </p>
        </details>
      </Card>

      {!showContact && !values.contact_submitted && !values.contact_skipped && (
        <div className="text-center">
          <Button onClick={() => { setShowContact(true); track("contact_started", { tool: SLUG }); }}>
            <Users className="w-4 h-4 mr-2" />
            Get a free expert review of these numbers
          </Button>
          <p className="mt-2 text-[13px] text-pns-text-muted">Optional. No cost and no obligation.</p>
        </div>
      )}

      {showContact && !values.contact_submitted && !values.contact_skipped && (
        <ContactStep
          onNext={(d) => { if (d.contact_submitted) track("lead_submitted", { tool: SLUG }); }}
          values={{ ...values, _toolSlug: SLUG }}
          resultSummary={`ROI: $${result.grossAnnualBenefit.toLocaleString()}/yr benefit, $${result.netYearOneBenefit.toLocaleString()} net Y1, ${result.yearOneROI}% ROI, ${result.paybackMonths}mo payback.`}
        />
      )}

      <div className="text-center">
        <Button variant="ghost" onClick={onRestart}>Start over</Button>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Page                                                                */
/* ------------------------------------------------------------------ */

export default function AutomationROICalculator() {
  React.useEffect(() => { track("tool_view", { tool: SLUG }); }, []);
  return (
    <ToolPage
      config={{
        title: "Automation ROI Calculator",
        description: "Estimate the return on investment for automating your business processes.",
        slug: SLUG,
        steps: [ImplementationCostStep, RecurringCostStep, SavingsStep, RevenueStep],
        results: Results,
      }}
    />
  );
}
