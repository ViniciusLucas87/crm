"use client";

import type { AssessmentState } from "@/lib/assessment";
import { Button } from "@/components/ui/button";

interface StepProps {
  state: AssessmentState;
  onUpdate: (partial: Partial<AssessmentState>) => void;
  onNext: () => void;
}

const BUSINESS_TYPES = [
  "Construction / Trades",
  "Property Management",
  "Tourism / Transportation",
  "Professional Services",
  "Manufacturing",
  "Other",
] as const;

export function BusinessTypeStep({ state, onUpdate, onNext }: StepProps) {
  const selected = state.businessType;

  return (
    <div>
      <h2 className="text-[clamp(1.25rem,3vw,1.75rem)] font-semibold text-pns-text-primary mb-2">
        What type of business do you operate?
      </h2>
      <p className="text-pns-text-muted mb-8">
        This helps us tailor your results to your industry.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3" role="radiogroup" aria-label="Business type">
        {BUSINESS_TYPES.map((type) => (
          <button
            key={type}
            type="button"
            role="radio"
            aria-checked={selected === type}
            onClick={() => onUpdate({ businessType: type })}
            className={`min-h-[64px] p-5 rounded-[14px] border-2 text-left text-[15px] font-medium transition-all duration-150 ${
              selected === type
                ? "border-pns-text-primary bg-pns-text-primary text-white shadow-md"
                : "border-pns-assessment-input-border bg-white text-pns-text-primary hover:border-pns-text-primary/40 hover:bg-pns-soft-blue/50"
            }`}
          >
            {type}
          </button>
        ))}
      </div>

      <div className="mt-10 flex justify-end">
        <Button variant="primary" size="default" onClick={onNext} disabled={!selected}>
          Continue
        </Button>
      </div>
    </div>
  );
}
