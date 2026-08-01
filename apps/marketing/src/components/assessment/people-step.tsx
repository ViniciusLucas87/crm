"use client";

import type { AssessmentState } from "@/lib/assessment";
import { Button } from "@/components/ui/button";

interface StepProps {
  state: AssessmentState;
  onUpdate: (partial: Partial<AssessmentState>) => void;
  onNext: () => void;
  onBack: () => void;
}

const PEOPLE_OPTIONS = ["1", "2–5", "6–15", "16–50", "50+"] as const;

export function PeopleStep({ state, onUpdate, onNext, onBack }: StepProps) {
  const selected = state.peopleInvolved;

  return (
    <div>
      <h2 className="text-[clamp(1.25rem,3vw,1.75rem)] font-semibold text-pns-text-primary mb-2">
        How many people are involved in this process?
      </h2>
      <p className="text-pns-text-muted mb-8">
        Count everyone who touches this workflow regularly.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3" role="radiogroup" aria-label="People involved">
        {PEOPLE_OPTIONS.map((option) => (
          <button
            key={option}
            type="button"
            role="radio"
            aria-checked={selected === option}
            onClick={() => onUpdate({ peopleInvolved: option })}
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
