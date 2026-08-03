"use client";

import { useState, useCallback } from "react";
import { Container } from "@/components/ui/container";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { CheckCircle2 } from "lucide-react";
import Link from "next/link";

/* ------------------------------------------------------------------ */
/*  Shared types                                                       */
/* ------------------------------------------------------------------ */

interface StepProps {
  onNext: (data: Record<string, unknown>) => void;
  onBack?: () => void;
  defaultValues?: Record<string, unknown>;
}

interface ResultProps {
  values: Record<string, unknown>;
  onRestart: () => void;
}

export interface ToolPageConfig {
  title: string;
  description: string;
  slug: string;
  steps: React.ComponentType<StepProps>[];
  results: React.ComponentType<ResultProps>;
}

/* ------------------------------------------------------------------ */
/*  Reusable wrapper                                                   */
/* ------------------------------------------------------------------ */

const STORAGE_PREFIX = "pns_tool_";

export function ToolPage({ config }: { config: ToolPageConfig }) {
  const [step, setStep] = useState(0);
  const [values, setValues] = useState<Record<string, unknown>>(() => {
    if (typeof window === "undefined") return {};
    try {
      const stored = sessionStorage.getItem(`${STORAGE_PREFIX}${config.slug}`);
      return stored ? JSON.parse(stored) : {};
    } catch {
      return {};
    }
  });

  const persist = useCallback(
    (v: Record<string, unknown>) => {
      setValues(v);
      try {
        sessionStorage.setItem(
          `${STORAGE_PREFIX}${config.slug}`,
          JSON.stringify(v)
        );
      } catch {
        /* quota exceeded — silently continue */
      }
    },
    [config.slug]
  );

  const handleNext = useCallback(
    (data: Record<string, unknown>) => {
      const merged = { ...values, ...data };
      persist(merged);
      if (step < config.steps.length) {
        setStep((s) => s + 1);
      }
    },
    [values, persist, step, config.steps.length]
  );

  const handleRestart = useCallback(() => {
    setValues({});
    setStep(0);
    try {
      sessionStorage.removeItem(`${STORAGE_PREFIX}${config.slug}`);
    } catch {
      /* ignore */
    }
  }, [config.slug]);

  const ActiveStep = config.steps[step];
  const ResultsComponent = config.results;

  return (
    <div className="min-h-screen bg-pns-bg">
      <Container className="max-w-[720px] py-12">
        {/* Breadcrumb */}
        <nav className="flex items-center gap-2 text-[14px] text-pns-text-muted mb-8">
          <Link href="/free-tools" className="hover:text-pns-text-primary transition-colors">
            Free Tools
          </Link>
          <span>/</span>
          <span className="text-pns-text-primary font-medium">{config.title}</span>
        </nav>

        {/* Progress */}
        {step < config.steps.length && (
          <div className="mb-6">
            <div className="flex justify-between text-[13px] text-pns-text-muted mb-2">
              <span>
                Step {step + 1} of {config.steps.length}
              </span>
              <span>
                {Math.round(((step + 1) / config.steps.length) * 100)}%
              </span>
            </div>
            <div className="h-1.5 bg-pns-assessment-input-bg rounded-full overflow-hidden">
              <div
                className="h-full bg-[#051226] rounded-full transition-all duration-300"
                style={{
                  width: `${Math.round(((step + 1) / config.steps.length) * 100)}%`,
                }}
              />
            </div>
          </div>
        )}

        {ActiveStep ? (
          <ActiveStep onNext={handleNext} defaultValues={values} />
        ) : (
          <ResultsComponent values={values} onRestart={handleRestart} />
        )}
      </Container>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Contact step (shared across all tools)                             */
/* ------------------------------------------------------------------ */

export function ContactStep({
  onNext,
  values,
  resultSummary,
}: {
  onNext: (data: Record<string, unknown>) => void;
  values: Record<string, unknown>;
  resultSummary: string;
}) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [company, setCompany] = useState("");
  const [phone, setPhone] = useState("");
  const [contactMethod, setContactMethod] = useState("Email");
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState("");
  const [duplicate, setDuplicate] = useState(false);
  const [privacyAccepted, setPrivacyAccepted] = useState(false);
  const [skipped, setSkipped] = useState(false);

  const handleSubmit = async () => {
    if (!name.trim() || !email.trim() || !company.trim()) {
      setError("Full name, work email, and company are required.");
      return;
    }
    if ((contactMethod === "Phone" || contactMethod === "SMS") && !phone.trim()) {
      setError(`A phone number is required when ${contactMethod} is selected.`);
      return;
    }
    if (!privacyAccepted) {
      setError("Please confirm that we may use these details to follow up about your results.");
      return;
    }
    setSubmitting(true);
    setError("");

    const searchParams = new URLSearchParams(window.location.search);
    const payload: Record<string, unknown> = {
      name: name.trim(),
      email: email.trim(),
      company: company.trim() || undefined,
      phone: phone.trim() || undefined,
      contact_method: contactMethod,
      source_tool: values._toolSlug as string || "unknown",
      calculated_summary: resultSummary,
      attribution: {
        utm_source: searchParams.get("utm_source"),
        utm_medium: searchParams.get("utm_medium"),
        utm_campaign: searchParams.get("utm_campaign"),
        utm_term: searchParams.get("utm_term"),
        utm_content: searchParams.get("utm_content"),
        referrer: document.referrer || null,
        landing_page: window.location.href,
      },
    };

    try {
      const res = await fetch("/api/assessment-submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        if (res.status === 409) {
          setDuplicate(true);
          setSubmitted(true);
          onNext({ contact_submitted: true });
          return;
        }
        throw new Error(body.detail || "Submission failed");
      }
      setSubmitted(true);
      onNext({ contact_submitted: true });
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "Something went wrong. Please try again."
      );
    } finally {
      setSubmitting(false);
    }
  };

  const handleSkip = () => {
    setSkipped(true);
    onNext({ contact_skipped: true, contact_submitted: false });
  };

  if (skipped) return null;

  if (submitted) {
    return (
      <Card className="p-8 text-center" variant="elevated">
        <CheckCircle2 className="w-12 h-12 text-green-600 mx-auto mb-4" />
        <h3 className="font-heading font-semibold text-[20px] text-pns-text-primary mb-2">
          {duplicate ? "Already submitted" : "Thank you!"}
        </h3>
        <p className="text-pns-text-muted text-[15px]">
          {duplicate
            ? "You've already submitted your results. We'll be in touch soon."
            : "Your results and contact details have been saved. We'll follow up within one business day."}
        </p>
      </Card>
    );
  }

  return (
    <Card className="p-6 md:p-8" variant="elevated">
      <h3 className="font-heading font-semibold text-[20px] text-pns-text-primary mb-2">
        Want us to review your results?
      </h3>
      <p className="text-pns-text-muted text-[15px] leading-relaxed mb-6">
        Optional. If you&apos;d like a Pacific North Systems team member to
        review your numbers and suggest next steps — at no cost — leave your
        details below. We&apos;ll follow up within one business day.
      </p>

      <div className="space-y-4">
        <div>
          <label htmlFor="tool-name" className="block text-[14px] font-medium text-pns-text-primary mb-1">
            Full name <span className="text-pns-assessment-error">*</span>
          </label>
          <input
            id="tool-name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full h-11 rounded-[10px] border border-pns-assessment-input-border bg-pns-assessment-input-bg px-4 text-[15px] font-inter text-pns-text-primary focus:outline-none focus:ring-2 focus:ring-[#051226]/20"
            placeholder="Jane Smith"
            aria-required="true"
          />
        </div>
        <div>
          <label htmlFor="tool-email" className="block text-[14px] font-medium text-pns-text-primary mb-1">
            Work email <span className="text-pns-assessment-error">*</span>
          </label>
          <input
            id="tool-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full h-11 rounded-[10px] border border-pns-assessment-input-border bg-pns-assessment-input-bg px-4 text-[15px] font-inter text-pns-text-primary focus:outline-none focus:ring-2 focus:ring-[#051226]/20"
            placeholder="jane@company.ca"
            aria-required="true"
          />
        </div>
        <div>
          <label htmlFor="tool-company" className="block text-[14px] font-medium text-pns-text-primary mb-1">
            Company <span className="text-pns-assessment-error">*</span>
          </label>
          <input
            id="tool-company"
            type="text"
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            className="w-full h-11 rounded-[10px] border border-pns-assessment-input-border bg-pns-assessment-input-bg px-4 text-[15px] font-inter text-pns-text-primary focus:outline-none focus:ring-2 focus:ring-[#051226]/20"
            placeholder="Acme Manufacturing Ltd."
          />
        </div>
        <div>
          <label htmlFor="tool-phone" className="block text-[14px] font-medium text-pns-text-primary mb-1">
            Phone
          </label>
          <input
            id="tool-phone"
            type="tel"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            className="w-full h-11 rounded-[10px] border border-pns-assessment-input-border bg-pns-assessment-input-bg px-4 text-[15px] font-inter text-pns-text-primary focus:outline-none focus:ring-2 focus:ring-[#051226]/20"
            placeholder="(604) 555-0123"
          />
        </div>
        <fieldset>
          <legend className="text-[14px] font-medium text-pns-text-primary mb-2">
            Preferred contact method
          </legend>
          <div className="flex gap-4">
            {["Email", "Phone", "SMS"].map((method) => (
              <label key={method} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="contact-method"
                  value={method}
                  checked={contactMethod === method}
                  onChange={(e) => setContactMethod(e.target.value)}
                  className="w-4 h-4 accent-[#051226]"
                />
                <span className="text-[14px] text-pns-text-primary">{method}</span>
              </label>
            ))}
          </div>
        </fieldset>
        <label className="flex items-start gap-3 text-[13px] text-pns-text-muted leading-relaxed">
          <input
            type="checkbox"
            checked={privacyAccepted}
            onChange={(event) => setPrivacyAccepted(event.target.checked)}
            className="mt-0.5 w-4 h-4 accent-[#051226]"
          />
          <span>
            I agree that Pacific North Systems may use these details to contact me about
            my results. This does not subscribe me to marketing. See our{" "}
            <Link href="/privacy" className="underline hover:text-pns-text-primary">
              privacy policy
            </Link>
            .
          </span>
        </label>
      </div>

      {error && (
        <p className="mt-4 text-[14px] text-pns-assessment-error" role="alert">
          {error}
        </p>
      )}

      <div className="flex flex-col sm:flex-row gap-3 mt-6">
        <Button onClick={handleSubmit} disabled={submitting}>
          {submitting ? "Submitting..." : "Submit & get follow-up"}
        </Button>
        <Button variant="ghost" onClick={handleSkip}>
          Skip — I just want the results
        </Button>
      </div>
    </Card>
  );
}
