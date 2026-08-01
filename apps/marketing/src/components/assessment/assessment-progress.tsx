interface AssessmentProgressProps {
  currentStep: number;
  totalSteps: number;
  labels: string[];
}

export function AssessmentProgress({
  currentStep,
  totalSteps,
  labels,
}: AssessmentProgressProps) {
  return (
    <div className="mb-8" role="progressbar" aria-valuenow={currentStep} aria-valuemin={1} aria-valuemax={totalSteps} aria-label={`Step ${currentStep} of ${totalSteps}: ${labels[currentStep - 1]}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-pns-text-primary">
          Step {currentStep} of {totalSteps}
        </span>
        <span className="text-xs text-pns-text-muted">
          Takes about 2 minutes
        </span>
      </div>
      <div className="h-2 bg-pns-assessment-input-border rounded-full overflow-hidden">
        <div
          className="h-full bg-pns-text-primary rounded-full transition-all duration-300"
          style={{ width: `${(currentStep / totalSteps) * 100}%` }}
        />
      </div>
      <p className="text-sm text-pns-text-muted mt-2">
        {labels[currentStep - 1]}
      </p>
    </div>
  );
}

