"use client";

import type { AssessmentState } from "@/lib/assessment";
import { Button } from "@/components/ui/button";

interface StepProps {
  state: AssessmentState;
  onUpdate: (partial: Partial<AssessmentState>) => void;
  onNext: () => void;
  onBack: () => void;
}

const TIME_OPTIONS = [
  "Less than 5 hours",
  "5–10 hours",
  "10–20 hours",
  "20–40 hours",
  "More than 40 hours",
  "Not sure",
] as const;

export function TimeSpentStep({ state, onUpdate, onNext, onBack }: StepProps) {
  const selected = state.weeklyTimeSpent;

  return (
    <div>
      <h2 className="text-[clamp(1.25rem,3vw,1.75rem)] font-semibold text-pns-text-primary mb-2">
        Approximately how much time does your team spend on this each week?
      </h2>
      <p className="text-pns-text-muted mb-8">
        Estimate the total across everyone involved. Don&apos;t overthink it , a rough estimate works.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3" role="radiogroup" aria-label="Weekly time spent">
        {TIME_OPTIONS.map((option) => (
          <button
            key={option}
            type="button"
            role="radio"
            aria-checked={selected === option}
            onClick={() => onUpdate({ weeklyTimeSpent: option })}
            className={`min-h-[64px] p-5 rounded-[14px] border-2 text-left text-[15px] font-medium transition-all duration-150 ${
              selected === option
                ? "border-pns-text-primary bg-pns-text-primary text-white shadow-md"
                : "border-pns-assessment-input-border bg-white text-pns-text-primary hover:border-pns-text-primary/40 hover:bg-pns-soft-blue/50"
            }`}
          >
            {option}
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
