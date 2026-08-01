"use client";

import type { AssessmentState } from "@/lib/assessment";
import { Button } from "@/components/ui/button";

interface StepProps {
  state: AssessmentState;
  onUpdate: (partial: Partial<AssessmentState>) => void;
  onNext: () => void;
  onBack: () => void;
}

const PROCESSES = [
  "Spreadsheets",
  "Email",
  "Paper forms",
  "Multiple software tools",
  "Mostly manual",
  "Existing custom system",
  "Other",
] as const;

export function CurrentProcessStep({ state, onUpdate, onNext, onBack }: StepProps) {
  const selected = state.currentProcess;

  return (
    <div>
      <h2 className="text-[clamp(1.25rem,3vw,1.75rem)] font-semibold text-pns-text-primary mb-2">
        How is this work handled today?
      </h2>
      <p className="text-pns-text-muted mb-8">
        Choose the tool or method your team relies on most.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3" role="radiogroup" aria-label="Current process">
        {PROCESSES.map((process) => (
          <button
            key={process}
            type="button"
            role="radio"
            aria-checked={selected === process}
            onClick={() => onUpdate({ currentProcess: process })}
            className={`min-h-[64px] p-5 rounded-[14px] border-2 text-left text-[15px] font-medium transition-all duration-150 ${
              selected === process
                ? "border-pns-text-primary bg-pns-text-primary text-white shadow-md"
                : "border-pns-assessment-input-border bg-white text-pns-text-primary hover:border-pns-text-primary/40 hover:bg-pns-soft-blue/50"
            }`}
          >
            {process}
          </button>
        ))}
      </div>

      <div className="mt-10 flex justify-between">
        <Button variant="ghost" size="default" onClick={onBack}>
          Back
        </Button>
        <Button variant="primary" size="default" onClick={onNext} disabled={!selected}>
          Continue
        </Button>
      </div>
    </div>
  );
}
