"use client";

import type { AssessmentState } from "@/lib/assessment";
import { Button } from "@/components/ui/button";
import { Check } from "lucide-react";

interface StepProps {
  state: AssessmentState;
  onUpdate: (partial: Partial<AssessmentState>) => void;
  onNext: () => void;
  onBack: () => void;
}

const PROBLEMS = [
  "Repetitive data entry",
  "Scheduling and dispatching",
  "Managing documents",
  "Reporting",
  "Customer follow up",
  "Information spread across different systems",
  "Manual approvals",
  "Other",
] as const;

export function ProblemStep({ state, onUpdate, onNext, onBack }: StepProps) {
  const selected = state.mainProblems;

  const toggle = (problem: string) => {
    const next = selected.includes(problem)
      ? selected.filter((p) => p !== problem)
      : [...selected, problem];
    onUpdate({ mainProblems: next });
  };

  return (
    <div>
      <h2 className="text-[clamp(1.25rem,3vw,1.75rem)] font-semibold text-pns-text-primary mb-2">
        What is costing your team the most time?
      </h2>
      <p className="text-pns-text-muted mb-2">Select all that apply.</p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-8" role="group" aria-label="Select problems">
        {PROBLEMS.map((problem) => {
          const isSelected = selected.includes(problem);
          return (
            <button
              key={problem}
              type="button"
              role="checkbox"
              aria-checked={isSelected}
              onClick={() => toggle(problem)}
              className={`min-h-[64px] p-5 rounded-[14px] border-2 text-left text-[15px] font-medium transition-all duration-150 flex items-center gap-3 ${
                isSelected
                  ? "border-pns-text-primary bg-pns-text-primary text-white shadow-md"
                  : "border-pns-assessment-input-border bg-white text-pns-text-primary hover:border-pns-text-primary/40 hover:bg-pns-soft-blue/50"
              }`}
            >
              <span
                className={`shrink-0 w-5 h-5 rounded border-2 flex items-center justify-center transition-colors ${
                  isSelected
                    ? "border-white bg-white"
                    : "border-pns-assessment-input-border"
                }`}
              >
                {isSelected && <Check className="w-3.5 h-3.5 text-pns-text-primary" />}
              </span>
              {problem}
            </button>
          );
        })}
      </div>

      <div className="mt-10 flex justify-between">
        <Button variant="ghost" size="default" onClick={onBack}>
          Back
        </Button>
        <Button
          variant="primary"
          size="default"
          onClick={onNext}
          disabled={selected.length === 0}
        >
          Continue
        </Button>
      </div>
    </div>
  );
}
