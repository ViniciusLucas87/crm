"use client";

import React, { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ToolPage, ContactStep } from "@/components/free-tools/tool-page";
import { Clock, DollarSign, TrendingDown, Users } from "lucide-react";
import { track } from "@/lib/analytics";

const SLUG = "manual-work-cost-calculator";

/* ------------------------------------------------------------------ */
/*  Calculations (client-side only)                                    */
/* ------------------------------------------------------------------ */

interface ManualWorkInput {
  employeesAffected: number;
  hoursPerWeek: number;
  loadedHourlyCost: number;
  weeksPerYear: number;
  recoverablePercent: number;
}

interface ManualWorkResult {
  weeklyHours: number;
  annualHours: number;
  weeklyCost: number;
  annualCost: number;
  recoverableHours: number;
  recoverableCost: number;
  loadedHourlyCost: number;
  assumptionText: string;
}

function calculateManualWork(input: ManualWorkInput): ManualWorkResult {
  const weeklyHours = input.employeesAffected * input.hoursPerWeek;
  const annualHours = weeklyHours * input.weeksPerYear;
  const weeklyCost = weeklyHours * input.loadedHourlyCost;
  const annualCost = annualHours * input.loadedHourlyCost;
  const recoverableHours = annualHours * (input.recoverablePercent / 100);
  const recoverableCost = recoverableHours * input.loadedHourlyCost;

  const assumptionText = [
    `Based on ${input.employeesAffected} employee${input.employeesAffected > 1 ? "s" : ""} each spending ${input.hoursPerWeek} hours/week on this task, at $${input.loadedHourlyCost.toFixed(0)}/hr loaded cost (salary + benefits + overhead), across ${input.weeksPerYear} working weeks.`,
    `Recoverable value uses the ${input.recoverablePercent}% scenario you selected. Validate it with a pilot; it is not an industry benchmark or guarantee.`,
    `Actual savings depend on implementation quality, process standardization, and employee adoption. These are directional estimates, not guarantees.`,
  ].join("\n\n");

  return {
    weeklyHours: Math.round(weeklyHours * 10) / 10,
    annualHours: Math.round(annualHours),
    weeklyCost: Math.round(weeklyCost),
    annualCost: Math.round(annualCost),
    recoverableHours: Math.round(recoverableHours),
    recoverableCost: Math.round(recoverableCost),
    loadedHourlyCost: input.loadedHourlyCost,
    assumptionText,
  };
}

/* ------------------------------------------------------------------ */
/*  Step 1: Employees affected                                         */
/* ------------------------------------------------------------------ */

function EmployeesStep({ onNext, defaultValues }: { onNext: (d: Record<string, unknown>) => void; defaultValues?: Record<string, unknown> }) {
  const [value, setValue] = useState<number>(
    (defaultValues?.employeesAffected as number) || 5
  );
  const [error, setError] = useState("");

  const handleNext = () => {
    if (value < 1 || value > 500) {
      setError("Please enter between 1 and 500 employees.");
      return;
    }
    track("tool_step_completed", { tool: SLUG, step: 1 });
    onNext({ employeesAffected: value });
  };

  return (
    <Card className="p-6 md:p-8" variant="elevated">
      <h3 className="font-heading font-semibold text-[20px] text-pns-text-primary mb-2">
        How many employees are affected by this manual task?
      </h3>
      <p className="text-pns-text-muted text-[15px] leading-relaxed mb-6">
        Count everyone who spends meaningful time on this process, including data entry,
        report compilation, scheduling, invoicing, etc.
      </p>
      <label htmlFor="employees-affected" className="sr-only">
        Number of employees affected
      </label>
      <input
        id="employees-affected"
        type="number"
        min={1}
        max={500}
        value={value}
        onChange={(e) => { setValue(Number(e.target.value)); setError(""); }}
        className="w-full h-12 rounded-[10px] border border-pns-assessment-input-border bg-pns-assessment-input-bg px-4 text-[18px] font-inter text-pns-text-primary text-center focus:outline-none focus:ring-2 focus:ring-[#051226]/20"
        aria-describedby={error ? "employees-error" : undefined}
      />
      {error && <p id="employees-error" className="mt-2 text-[14px] text-pns-assessment-error" role="alert">{error}</p>}
      <div className="flex justify-end mt-6">
        <Button onClick={handleNext}>Next</Button>
      </div>
    </Card>
  );
}

/* ------------------------------------------------------------------ */
/*  Step 2: Hours per week per employee                                */
/* ------------------------------------------------------------------ */

function HoursStep({ onNext, defaultValues }: { onNext: (d: Record<string, unknown>) => void; defaultValues?: Record<string, unknown> }) {
  const [value, setValue] = useState<number>(
    (defaultValues?.hoursPerWeek as number) || 5
  );

  return (
    <Card className="p-6 md:p-8" variant="elevated">
      <h3 className="font-heading font-semibold text-[20px] text-pns-text-primary mb-2">
        How many hours per week does each employee spend on this task?
      </h3>
      <p className="text-pns-text-muted text-[15px] leading-relaxed mb-6">
        Include time spent preparing, checking, entering data again, and fixing errors, not just the core task.
      </p>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[2, 5, 10, 15, 20, 25, 30, 40].map((h) => (
          <button
            key={h}
            onClick={() => setValue(h)}
            className={`h-12 rounded-[10px] border font-inter text-[15px] transition-colors ${
              value === h
                ? "border-[#051226] bg-[#051226] text-white"
                : "border-pns-assessment-input-border bg-pns-assessment-input-bg text-pns-text-primary hover:border-[#051226]/30"
            }`}
            aria-pressed={value === h}
          >
            {h} {h === 1 ? "hr" : "hrs"}
          </button>
        ))}
      </div>
      <div className="flex justify-between mt-6">
        <Button variant="ghost" onClick={() => onNext({ hoursPerWeek: value, _back: true })}>
          Back
        </Button>
        <Button onClick={() => { track("tool_step_completed", { tool: SLUG, step: 2 }); onNext({ hoursPerWeek: value }); }}>
          Next
        </Button>
      </div>
    </Card>
  );
}

/* ------------------------------------------------------------------ */
/*  Step 3: Loaded hourly cost                                         */
/* ------------------------------------------------------------------ */

function CostStep({ onNext, defaultValues }: { onNext: (d: Record<string, unknown>) => void; defaultValues?: Record<string, unknown> }) {
  const [value, setValue] = useState<number>(
    (defaultValues?.loadedHourlyCost as number) || 35
  );
  const [error, setError] = useState("");

  const presetCosts = [
    { label: "$25/hr", value: 25, hint: "Entry-level admin" },
    { label: "$35/hr", value: 35, hint: "Experienced admin" },
    { label: "$50/hr", value: 50, hint: "Specialist / coordinator" },
    { label: "$75/hr", value: 75, hint: "Manager / professional" },
  ];

  return (
    <Card className="p-6 md:p-8" variant="elevated">
      <h3 className="font-heading font-semibold text-[20px] text-pns-text-primary mb-2">
        What is the average loaded hourly cost per employee?
      </h3>
      <p className="text-pns-text-muted text-[15px] leading-relaxed mb-6">
        Use your organization&apos;s actual loaded cost, including only the payroll contributions, benefits, equipment, and relevant overhead your records support.
      </p>
      <div className="grid grid-cols-2 gap-3 mb-4">
        {presetCosts.map((p) => (
          <button
            key={p.value}
            onClick={() => { setValue(p.value); setError(""); }}
            className={`p-3 rounded-[10px] border text-left transition-colors ${
              value === p.value
                ? "border-[#051226] bg-[#051226] text-white"
                : "border-pns-assessment-input-border bg-pns-assessment-input-bg hover:border-[#051226]/30"
            }`}
            aria-pressed={value === p.value}
          >
            <span className={`block text-[16px] font-semibold ${value === p.value ? "text-white" : "text-pns-text-primary"}`}>
              {p.label}
            </span>
            <span className={`block text-[13px] ${value === p.value ? "text-white/70" : "text-pns-text-muted"}`}>
              {p.hint}
            </span>
          </button>
        ))}
      </div>
      <label htmlFor="hourly-cost-custom" className="sr-only">Custom hourly cost</label>
      <div className="flex items-center gap-3">
        <span className="text-[15px] text-pns-text-muted">Custom: $</span>
        <input
          id="hourly-cost-custom"
          type="number"
          min={15}
          max={200}
          value={value}
          onChange={(e) => { setValue(Number(e.target.value)); setError(""); }}
          className="w-24 h-11 rounded-[10px] border border-pns-assessment-input-border bg-pns-assessment-input-bg px-3 text-[15px] font-inter text-pns-text-primary text-center focus:outline-none focus:ring-2 focus:ring-[#051226]/20"
          aria-describedby={error ? "cost-error" : undefined}
        />
        <span className="text-[15px] text-pns-text-muted">/hr CAD</span>
      </div>
      {error && <p id="cost-error" className="mt-2 text-[14px] text-pns-assessment-error" role="alert">{error}</p>}
      <div className="flex justify-between mt-6">
        <Button variant="ghost" onClick={() => onNext({ loadedHourlyCost: value, _back: true })}>
          Back
        </Button>
        <Button onClick={() => { track("tool_step_completed", { tool: SLUG, step: 3 }); onNext({ loadedHourlyCost: value }); }}>
          Next
        </Button>
      </div>
    </Card>
  );
}

/* ------------------------------------------------------------------ */
/*  Step 4: Weeks per year + recoverable %                              */
/* ------------------------------------------------------------------ */

function RecoverableStep({ onNext, defaultValues }: { onNext: (d: Record<string, unknown>) => void; defaultValues?: Record<string, unknown> }) {
  const [weeks, setWeeks] = useState<number>((defaultValues?.weeksPerYear as number) || 48);
  const [recoverable, setRecoverable] = useState<number>((defaultValues?.recoverablePercent as number) || 35);

  return (
    <Card className="p-6 md:p-8" variant="elevated">
      <h3 className="font-heading font-semibold text-[20px] text-pns-text-primary mb-2">
        Working weeks per year & recoverable percentage
      </h3>
      <p className="text-pns-text-muted text-[15px] leading-relaxed mb-6">
        Standard working year: 48-50 weeks (after vacation and statutory holidays). Recoverable: what percentage of this manual work could realistically be automated or streamlined?
      </p>

      <div className="mb-6">
        <label htmlFor="weeks-per-year" className="block text-[14px] font-medium text-pns-text-primary mb-2">
          Working weeks per year
        </label>
        <div className="flex gap-3">
          {[46, 48, 50, 52].map((w) => (
            <button
              key={w}
              onClick={() => setWeeks(w)}
              className={`h-11 px-4 rounded-[10px] border font-inter text-[15px] transition-colors ${
                weeks === w
                  ? "border-[#051226] bg-[#051226] text-white"
                  : "border-pns-assessment-input-border bg-pns-assessment-input-bg text-pns-text-primary hover:border-[#051226]/30"
              }`}
              aria-pressed={weeks === w}
            >
              {w}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label htmlFor="recoverable-pct" className="block text-[14px] font-medium text-pns-text-primary mb-2">
          Recoverable: {recoverable}%
        </label>
        <input
          id="recoverable-pct"
          type="range"
          min={10}
          max={80}
          step={5}
          value={recoverable}
          onChange={(e) => setRecoverable(Number(e.target.value))}
          className="w-full accent-[#051226]"
        />
        <div className="flex justify-between text-[13px] text-pns-text-muted mt-1">
          <span>10% (conservative)</span>
          <span>80% (aggressive)</span>
        </div>
      </div>

      <div className="flex justify-between mt-6">
        <Button variant="ghost" onClick={() => onNext({ weeksPerYear: weeks, recoverablePercent: recoverable, _back: true })}>
          Back
        </Button>
        <Button onClick={() => { track("tool_step_completed", { tool: SLUG, step: 4 }); onNext({ weeksPerYear: weeks, recoverablePercent: recoverable }); }}>
          See results
        </Button>
      </div>
    </Card>
  );
}

/* ------------------------------------------------------------------ */
/*  Results                                                             */
/* ------------------------------------------------------------------ */

function Results({ values, onRestart }: { values: Record<string, unknown>; onRestart: () => void }) {
  const input: ManualWorkInput = {
    employeesAffected: (values.employeesAffected as number) || 5,
    hoursPerWeek: (values.hoursPerWeek as number) || 5,
    loadedHourlyCost: (values.loadedHourlyCost as number) || 35,
    weeksPerYear: (values.weeksPerYear as number) || 48,
    recoverablePercent: (values.recoverablePercent as number) || 35,
  };

  const [showContact, setShowContact] = useState(false);
  const result = calculateManualWork(input);

  return (
    <div className="space-y-6">
      <Card className="p-6 md:p-8" variant="elevated">
        <h2 className="font-heading font-bold text-[22px] text-pns-text-primary mb-6">
          Your Manual Work Cost Estimate
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
          <div className="bg-pns-soft-blue rounded-[12px] p-4">
            <div className="flex items-center gap-2 mb-1">
              <Clock className="w-4 h-4 text-pns-text-muted" />
              <span className="text-[13px] text-pns-text-muted">Weekly Hours</span>
            </div>
            <p className="text-[24px] font-bold text-pns-text-primary">
              {result.weeklyHours.toLocaleString()}
            </p>
          </div>
          <div className="bg-pns-soft-blue rounded-[12px] p-4">
            <div className="flex items-center gap-2 mb-1">
              <Clock className="w-4 h-4 text-pns-text-muted" />
              <span className="text-[13px] text-pns-text-muted">Annual Hours</span>
            </div>
            <p className="text-[24px] font-bold text-pns-text-primary">
              {result.annualHours.toLocaleString()}
            </p>
          </div>
          <div className="bg-pns-soft-blue rounded-[12px] p-4">
            <div className="flex items-center gap-2 mb-1">
              <DollarSign className="w-4 h-4 text-pns-text-muted" />
              <span className="text-[13px] text-pns-text-muted">Weekly Cost</span>
            </div>
            <p className="text-[24px] font-bold text-pns-text-primary">
              ${result.weeklyCost.toLocaleString()}
            </p>
          </div>
          <div className="bg-pns-soft-blue rounded-[12px] p-4">
            <div className="flex items-center gap-2 mb-1">
              <DollarSign className="w-4 h-4 text-pns-text-muted" />
              <span className="text-[13px] text-pns-text-muted">Annual Cost</span>
            </div>
            <p className="text-[24px] font-bold text-pns-text-primary">
              ${result.annualCost.toLocaleString()}
            </p>
          </div>
        </div>

        {/* Recovery estimate */}
        <div className="bg-green-50 border border-green-200 rounded-[12px] p-5 mb-6">
          <div className="flex items-center gap-2 mb-2">
            <TrendingDown className="w-5 h-5 text-green-700" />
            <h4 className="font-heading font-semibold text-[16px] text-green-800">
              Potential Recovery ({input.recoverablePercent}% automation)
            </h4>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <span className="text-[13px] text-green-700">Hours/year</span>
              <p className="text-[20px] font-bold text-green-800">
                {result.recoverableHours.toLocaleString()}
              </p>
            </div>
            <div>
              <span className="text-[13px] text-green-700">Cost/year</span>
              <p className="text-[20px] font-bold text-green-800">
                ${result.recoverableCost.toLocaleString()}
              </p>
            </div>
          </div>
        </div>

        {/* Assumptions */}
        <details className="group">
          <summary className="text-[14px] text-pns-text-muted cursor-pointer hover:text-pns-text-primary transition-colors">
            How we calculated this
          </summary>
          <p className="mt-3 text-[14px] text-pns-text-muted leading-relaxed whitespace-pre-line">
            {result.assumptionText}
          </p>
        </details>
      </Card>

      {/* Contact step inline */}
      {!showContact && !values.contact_submitted && !values.contact_skipped && (
        <div className="text-center">
          <Button onClick={() => { setShowContact(true); track("contact_started", { tool: SLUG }); }}>
            <Users className="w-4 h-4 mr-2" />
            Get a free expert review of these numbers
          </Button>
          <p className="mt-2 text-[13px] text-pns-text-muted">
            Optional. We&apos;ll review your specific situation at no cost.
          </p>
        </div>
      )}

      {showContact && !values.contact_submitted && !values.contact_skipped && (
        <ContactStep
          onNext={(d) => {
            if (d.contact_submitted) track("lead_submitted", { tool: SLUG });
          }}
          values={{ ...values, _toolSlug: SLUG }}
          resultSummary={`Manual Work: ${input.employeesAffected} employees × ${input.hoursPerWeek}hrs/wk @ $${input.loadedHourlyCost}/hr = $${result.annualCost.toLocaleString()}/yr; ${result.recoverableHours.toLocaleString()} hrs/yr recoverable at ${input.recoverablePercent}%.`}
        />
      )}

      <div className="text-center">
        <Button variant="ghost" onClick={onRestart}>
          Start over
        </Button>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Page                                                                */
/* ------------------------------------------------------------------ */

export default function ManualWorkCostCalculator() {
  React.useEffect(() => {
    track("tool_view", { tool: SLUG });
  }, []);

  return (
    <ToolPage
      config={{
        title: "Manual Work Cost Calculator",
        description: "Estimate how much repetitive manual work costs your business.",
        slug: SLUG,
        steps: [EmployeesStep, HoursStep, CostStep, RecoverableStep],
        results: Results,
      }}
    />
  );
}
