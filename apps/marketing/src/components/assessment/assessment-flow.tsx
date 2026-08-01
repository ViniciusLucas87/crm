"use client";

import { useState, useEffect, useCallback } from "react";
import { AssessmentProgress } from "./assessment-progress";
import { BusinessTypeStep } from "./business-type-step";
import { ProblemStep } from "./problem-step";
import { CurrentProcessStep } from "./current-process-step";
import { TimeSpentStep } from "./time-spent-step";
import { PeopleStep } from "./people-step";
import { ContactStep } from "./contact-step";
import { ResultsStep } from "./results-step";
import type { AssessmentState, AssessmentResults } from "@/lib/assessment";
import {
  loadFromSession,
  saveToSession,
  clearSession,
  calculateAllResults,
  ASSESSMENT_VERSION,
} from "@/lib/assessment";
import {
  isStorageAvailable,
  saveSubmission,
  loadSubmission,
  removeSubmission,
  cleanExpiredSubmissions,
} from "@/lib/submission-storage";

const STEP_LABELS = [
  "Business Type",
  "Main Problem",
  "Current Process",
  "Time Spent",
  "People",
  "Contact",
  "Results",
];

const TOTAL_STEPS = 7;

const EMPTY_STATE: AssessmentState = {
  version: ASSESSMENT_VERSION,
  mainProblems: [],
  currentStep: 1,
};

export function AssessmentFlow() {
  const [state, setState] = useState<AssessmentState>(EMPTY_STATE);
  const [results, setResults] = useState<AssessmentResults | null>(null);
  const [hydrated, setHydrated] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [requestId, setRequestId] = useState<string | null>(null);
  const [submitStatus, setSubmitStatus] = useState<"persisted" | "unavailable" | null>(null);
  const [storageFailed, setStorageFailed] = useState(false);

  // Hydrate from session on mount + clean expired submissions
  useEffect(() => {
    cleanExpiredSubmissions();
    const saved = loadFromSession();
    if (saved) {
      setState((prev) => ({ ...prev, ...saved }));
    }
    setHydrated(true);
  }, []);

  // Persist on change (only during input steps, not results)
  useEffect(() => {
    if (hydrated && state.currentStep < TOTAL_STEPS) {
      saveToSession(state);
    }
  }, [state, hydrated]);

  const updateState = useCallback((partial: Partial<AssessmentState>) => {
    setState((prev) => ({ ...prev, ...partial }));
  }, []);

  const goToStep = useCallback(
    (step: number) => {
      if (step === TOTAL_STEPS) {
        const calculated = calculateAllResults(state);
        setResults(calculated);
      }
      setState((prev) => ({ ...prev, currentStep: step }));
    },
    [state],
  );

  const handleReset = useCallback(() => {
    clearSession();
    if (requestId) removeSubmission(requestId);
    setState(EMPTY_STATE);
    setResults(null);
    setSubmitError(null);
    setRequestId(null);
    setSubmitStatus(null);
    setStorageFailed(false);
  }, [requestId]);

  const handleSubmitAssessment = useCallback(async () => {
    setSubmitting(true);
    setSubmitError(null);
    setSubmitStatus(null);
    setStorageFailed(false);

    try {
      const calculated = calculateAllResults(state);
      setResults(calculated);

      const submissionPayload = {
        contactName: state.contactName,
        contactEmail: state.contactEmail,
        contactCompany: state.contactCompany,
        contactPhone: state.contactPhone,
        preferredContactMethod: state.preferredContactMethod || "email",
        bestTimeToContact: state.bestTimeToContact || null,
        additionalDetails: state.additionalDetails,
        businessType: state.businessType,
        mainProblems: state.mainProblems,
        currentProcess: state.currentProcess,
        weeklyTimeSpent: state.weeklyTimeSpent,
        peopleInvolved: state.peopleInvolved,
        results: calculated,
      };

      const res = await fetch("/api/assessment-submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(submissionPayload),
      });

      const data = await res.json();
      const rid = data.requestId || null;

      if (res.status === 201) {
        // CRM confirmed durable persistence
        if (rid) removeSubmission(rid);
        setRequestId(rid);
        setSubmitStatus("persisted");
        setState((prev) => ({ ...prev, currentStep: TOTAL_STEPS }));
        return;
      }

      // CRM unavailable or not configured — attempt browser recovery
      if (res.status === 503 && rid) {
        const storageOk = isStorageAvailable();
        if (storageOk) {
          const saved = saveSubmission(rid, submissionPayload);
          if (!saved.ok) {
            setStorageFailed(true);
          }
        } else {
          setStorageFailed(true);
        }
        setRequestId(rid);
        setSubmitStatus("unavailable");
        setSubmitError(data.error || null);
        setState((prev) => ({ ...prev, currentStep: TOTAL_STEPS }));
        return;
      }

      // Other errors (400, 409, 500, 502)
      setSubmitError(data.error || "An unexpected error occurred. Please try again.");
    } catch (err) {
      setSubmitError(
        err instanceof Error ? err.message : "Something went wrong. Please try again.",
      );
    } finally {
      setSubmitting(false);
    }
  }, [state]);

  const handleRetry = useCallback(async () => {
    if (!requestId) return;
    setSubmitting(true);
    setSubmitError(null);

    const saved = loadSubmission(requestId);
    if (!saved) {
      setSubmitError("Your saved form data is no longer available. Please restart the assessment.");
      setSubmitting(false);
      return;
    }

    try {
      const res = await fetch("/api/assessment-submit", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ requestId, ...(saved as Record<string, unknown>) }),
      });

      const data = await res.json();

      if (res.status === 201 || res.status === 200) {
        removeSubmission(requestId);
        setSubmitStatus("persisted");
        setSubmitError(null);
        setStorageFailed(false);
        return;
      }

      setSubmitStatus("unavailable");
      setSubmitError(data.error || "Still unable to reach our processing system.");
    } catch (err) {
      setSubmitError(
        err instanceof Error ? err.message : "Retry failed. Your form data is preserved in your browser.",
      );
    } finally {
      setSubmitting(false);
    }
  }, [requestId]);

  if (!hydrated) {
    return (
      <div className="max-w-[960px] mx-auto p-5">
        <div className="animate-pulse">
          <div className="h-8 bg-pns-assessment-panel rounded w-1/3 mb-4" />
          <div className="h-4 bg-pns-assessment-panel rounded w-2/3" />
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-[960px] mx-auto px-4 sm:px-6 py-8">
      {/* Step indicator */}
      {state.currentStep < TOTAL_STEPS && (
        <AssessmentProgress
          currentStep={state.currentStep}
          totalSteps={TOTAL_STEPS - 1}
          labels={STEP_LABELS.slice(0, -1)}
        />
      )}

      {/* Steps */}
      <div className="bg-white rounded-[16px] border border-pns-assessment-input-border p-5 sm:p-8">
        {state.currentStep === 1 && (
          <BusinessTypeStep
            state={state}
            onUpdate={updateState}
            onNext={() => goToStep(2)}
          />
        )}
        {state.currentStep === 2 && (
          <ProblemStep
            state={state}
            onUpdate={updateState}
            onNext={() => goToStep(3)}
            onBack={() => goToStep(1)}
          />
        )}
        {state.currentStep === 3 && (
          <CurrentProcessStep
            state={state}
            onUpdate={updateState}
            onNext={() => goToStep(4)}
            onBack={() => goToStep(2)}
          />
        )}
        {state.currentStep === 4 && (
          <TimeSpentStep
            state={state}
            onUpdate={updateState}
            onNext={() => goToStep(5)}
            onBack={() => goToStep(3)}
          />
        )}
        {state.currentStep === 5 && (
          <PeopleStep
            state={state}
            onUpdate={updateState}
            onNext={() => goToStep(6)}
            onBack={() => goToStep(4)}
          />
        )}
        {state.currentStep === 6 && (
          <ContactStep
            state={state}
            onUpdate={updateState}
            onSubmit={handleSubmitAssessment}
            onBack={() => goToStep(5)}
            submitting={submitting}
            submitError={submitError}
          />
        )}
        {state.currentStep === 7 && (
          <ResultsStep
            results={results}
            requestId={requestId}
            submitStatus={submitStatus}
            submitting={submitting}
            submitError={submitError}
            storageFailed={storageFailed}
            onReset={handleReset}
            onRetry={handleRetry}
            onBack={() => goToStep(6)}
          />
        )}
      </div>
    </div>
  );
}

