"use client";

import { useState, useMemo } from "react";
import type { AssessmentState } from "@/lib/assessment";
import { Button } from "@/components/ui/button";
import { Mail, Phone, MessageSquare } from "lucide-react";

interface StepProps {
  state: AssessmentState;
  onUpdate: (partial: Partial<AssessmentState>) => void;
  onSubmit: () => Promise<void>;
  onBack: () => void;
  submitting: boolean;
  submitError: string | null;
}

const contactMethods = [
  { value: "email", label: "Email", icon: Mail, desc: "We'll send your results and follow up by email" },
  { value: "phone", label: "Phone Call", icon: Phone, desc: "We'll call you to discuss your results" },
  { value: "sms", label: "SMS / Text", icon: MessageSquare, desc: "We'll text you to schedule a conversation" },
] as const;

const timeOptions = [
  { value: "morning", label: "Morning (8–12)" },
  { value: "afternoon", label: "Afternoon (12–5)" },
  { value: "evening", label: "Evening (5–8)" },
  { value: "anytime", label: "Anytime" },
] as const;

export function ContactStep({ state, onUpdate, onSubmit, onBack, submitting, submitError }: StepProps) {
  const [errors, setErrors] = useState<Record<string, string>>({});

  const method = state.preferredContactMethod || "email";

  // All lead-capture fields are required
  const isRequired = useMemo(() => ({
    name: true,
    company: true,
    email: true,
    phone: method === "phone" || method === "sms",
  }), [method]);

  const validate = (): boolean => {
    const errs: Record<string, string> = {};
    if (!state.contactName?.trim()) errs.contactName = "Name is required";
    if (!state.contactCompany?.trim()) errs.contactCompany = "Company name is required";
    if (isRequired.email) {
      if (!state.contactEmail?.trim()) errs.contactEmail = "Email is required";
      else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(state.contactEmail)) errs.contactEmail = "Enter a valid email";
    } else if (state.contactEmail && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(state.contactEmail)) {
      errs.contactEmail = "Enter a valid email";
    }
    if (isRequired.phone && !state.contactPhone?.trim()) {
      errs.contactPhone = "Phone number is required";
    }
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = () => {
    if (validate()) onSubmit();
  };

  const inputClass = (field: string) =>
    `w-full min-h-[52px] rounded-[12px] border px-4 py-3 text-[15px] text-pns-text-primary placeholder:text-pns-text-muted/60 transition-colors ${
      errors[field]
        ? "border-red-400 bg-red-50/30"
        : "border-pns-assessment-input-border bg-white focus:border-pns-text-primary/50"
    }`;

  const labelClass = (required: boolean) =>
    `block text-sm font-medium text-pns-text-primary mb-1.5 ${required ? "" : "text-pns-text-muted"}`;

  return (
    <div>
      <h2 className="text-[clamp(1.25rem,3vw,1.75rem)] font-semibold text-pns-text-primary mb-2">
        How would you like us to contact you?
      </h2>
      <p className="text-pns-text-muted mb-8">
        We&apos;ll review your assessment and contact you using your preferred method. We won&apos;t share your information or send spam.
      </p>

      {/* Contact method selector */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-8" role="radiogroup" aria-label="Preferred contact method">
        {contactMethods.map((m) => {
          const selected = method === m.value;
          const Icon = m.icon;
          return (
            <button
              key={m.value}
              type="button"
              role="radio"
              aria-checked={selected}
              onClick={() => onUpdate({ preferredContactMethod: m.value })}
              className={`
                flex flex-col items-center gap-2 p-4 rounded-[14px] border-2 text-center
                transition-all duration-150 cursor-pointer
                ${selected
                  ? "border-pns-text-primary bg-pns-text-primary text-white shadow-md"
                  : "border-pns-assessment-input-border bg-white text-pns-text-primary hover:border-pns-text-primary/40 hover:bg-pns-soft-blue/50"
                }
              `}
            >
              <Icon className={`w-5 h-5 ${selected ? "text-white" : "text-pns-text-muted"}`} />
              <span className="text-[14px] font-semibold">{m.label}</span>
              <span className={`text-[11px] leading-tight ${selected ? "text-white/70" : "text-pns-text-muted"}`}>
                {m.desc}
              </span>
            </button>
          );
        })}
      </div>

      {/* Form fields */}
      <div className="space-y-5 max-w-[520px]">
        {/* Name */}
        <div>
          <label htmlFor="contact-name" className={labelClass(true)}>
            Full Name <span className="text-red-500">*</span>
          </label>
          <input
            id="contact-name"
            type="text"
            className={inputClass("contactName")}
            placeholder="Your full name"
            value={state.contactName ?? ""}
            onChange={(e) => onUpdate({ contactName: e.target.value })}
          />
          {errors.contactName && <p className="text-xs text-red-500 mt-1">{errors.contactName}</p>}
        </div>

        {/* Company */}
        <div>
          <label htmlFor="contact-company" className={labelClass(true)}>
            Company name <span className="text-red-500">*</span>
          </label>
          <input
            id="contact-company"
            type="text"
            className={inputClass("contactCompany")}
            placeholder="Your company"
            value={state.contactCompany ?? ""}
            onChange={(e) => onUpdate({ contactCompany: e.target.value })}
          />
          {errors.contactCompany && <p className="text-xs text-red-500 mt-1">{errors.contactCompany}</p>}
        </div>

        {/* Email */}
        <div>
          <label htmlFor="contact-email" className={labelClass(isRequired.email)}>
            Business email {isRequired.email ? <span className="text-red-500">*</span> : <span className="text-pns-text-muted font-normal">(recommended)</span>}
          </label>
          <input
            id="contact-email"
            type="email"
            className={inputClass("contactEmail")}
            placeholder="you@company.com"
            value={state.contactEmail ?? ""}
            onChange={(e) => onUpdate({ contactEmail: e.target.value })}
          />
          {errors.contactEmail && <p className="text-xs text-red-500 mt-1">{errors.contactEmail}</p>}
        </div>

        {/* Phone */}
        <div>
          <label htmlFor="contact-phone" className={labelClass(isRequired.phone)}>
            {isRequired.phone ? (
              <>{method === "sms" ? "Mobile phone" : "Phone number"} <span className="text-red-500">*</span></>
            ) : (
              <>Phone <span className="text-pns-text-muted font-normal">(optional)</span></>
            )}
          </label>
          <input
            id="contact-phone"
            type="tel"
            className={inputClass("contactPhone")}
            placeholder="+1 (604) 555-0123"
            value={state.contactPhone ?? ""}
            onChange={(e) => onUpdate({ contactPhone: e.target.value })}
          />
          {errors.contactPhone && <p className="text-xs text-red-500 mt-1">{errors.contactPhone}</p>}
        </div>

        {/* Best time to contact */}
        <div>
          <label htmlFor="contact-time" className="block text-sm font-medium text-pns-text-primary mb-1.5">
            Best time to contact <span className="text-pns-text-muted font-normal">(optional)</span>
          </label>
          <select
            id="contact-time"
            className="w-full min-h-[52px] rounded-[12px] border border-pns-assessment-input-border bg-white px-4 py-3 text-[15px] text-pns-text-primary"
            value={state.bestTimeToContact ?? ""}
            onChange={(e) => onUpdate({ bestTimeToContact: e.target.value })}
          >
            <option value="">Select preferred time</option>
            {timeOptions.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
        </div>

        {/* Additional details */}
        <div>
          <label htmlFor="contact-details" className="block text-sm font-medium text-pns-text-primary mb-1.5">
            Additional details <span className="text-pns-text-muted font-normal">(optional)</span>
          </label>
          <textarea
            id="contact-details"
            className="w-full min-h-[100px] rounded-[12px] border border-pns-assessment-input-border bg-white px-4 py-3 text-[15px] text-pns-text-primary placeholder:text-pns-text-muted/60 focus:border-pns-text-primary/50 transition-colors resize-y"
            placeholder="Anything else you'd like us to know about your operation..."
            value={state.additionalDetails ?? ""}
            onChange={(e) => onUpdate({ additionalDetails: e.target.value })}
          />
        </div>
      </div>

      <div className="mt-10 flex justify-between">
        <Button variant="ghost" size="default" onClick={onBack} disabled={submitting}>
          Back
        </Button>
        <Button variant="primary" size="default" onClick={handleSubmit} disabled={submitting}>
          {submitting ? "Sending…" : "View My Results"}
        </Button>
      </div>

      {submitError && (
        <p className="mt-4 text-sm text-red-500 text-center" role="alert">
          {submitError}
        </p>
      )}
    </div>
  );
}
