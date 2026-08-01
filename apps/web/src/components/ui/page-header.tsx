"use client";

import Link from "next/link";
import type { Route } from "next";
import { ArrowLeft, ChevronRight, type LucideIcon } from "lucide-react";

export type ContextAction = {
  label: string;
  href: string;
  icon: LucideIcon;
  description?: string;
};

type Props = {
  /** Breadcrumb items */
  crumbs: { label: string; href?: string }[];
  /** Logical parent for "Back to" */
  parentLabel?: string;
  parentHref?: string;
  /** Page title */
  title: string;
  /** Contextual actions shown below the header */
  actions?: ContextAction[];
  /** Subtitle / description */
  subtitle?: string;
};

export function PageHeader({ crumbs, parentLabel, parentHref, title, actions, subtitle }: Props) {
  return (
    <div className="space-y-4">
      {/* Breadcrumbs */}
      <nav className="flex items-center gap-1.5 text-xs text-slate-500" aria-label="Breadcrumb">
        <Link href="/" className="transition hover:text-slate-300">Home</Link>
        {crumbs.map((item, i) => (
          <span key={i} className="flex items-center gap-1.5">
            <ChevronRight className="h-3 w-3" />
            {item.href ? (
              <Link href={item.href as Route} className="transition hover:text-slate-300">
                {item.label}
              </Link>
            ) : (
              <span className="text-slate-300">{item.label}</span>
            )}
          </span>
        ))}
      </nav>

      {/* Back link */}
      {parentLabel && parentHref && (
        <Link
          href={parentHref as Route}
          className="inline-flex items-center gap-1.5 text-sm text-slate-400 transition hover:text-cyan-300"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back to {parentLabel}
        </Link>
      )}

      {/* Title */}
      <div>
        <h2 className="text-lg font-semibold text-white">{title}</h2>
        {subtitle && <p className="mt-1 text-sm text-slate-400">{subtitle}</p>}
      </div>

      {/* Contextual Actions */}
      {actions && actions.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {actions.map(action => (
            <Link
              key={action.label}
              href={action.href as Route}
              className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-xs text-slate-300 transition hover:border-cyan-400/30 hover:bg-cyan-400/5 hover:text-cyan-300"
              title={action.description}
            >
              <action.icon className="h-3.5 w-3.5" />
              {action.label}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * Inline contextual nav bar — horizontal tabs for switching between related views.
 */
export function ContextNav({ items, className = "" }: { items: { label: string; href: string; active?: boolean }[]; className?: string }) {
  return (
    <div className={`flex flex-wrap gap-1 overflow-x-auto ${className}`}>
      {items.map(item => (
        <Link
          key={item.href}
          href={item.href as Route}
          className={`rounded-lg px-3 py-1.5 text-xs font-medium transition ${
            item.active
              ? "bg-white/10 text-white"
              : "text-slate-500 hover:bg-white/5 hover:text-slate-300"
          }`}
        >
          {item.label}
        </Link>
      ))}
    </div>
  );
}

/**
 * AI Actions bar — shows all available AI tools for a company/lead.
 */
export function AiActionsBar({ companyId, leadId, className = "" }: { companyId?: number; leadId?: number; className?: string }) {
  const actions: ContextAction[] = [];

  if (companyId) {
    actions.push(
      { label: "AI Analysis", href: `/companies/${companyId}?tab=ai-summary`, icon: SparklesIcon, description: "AI-powered company intelligence" },
      { label: "Proposal", href: `/ai/proposals/${companyId}`, icon: FileIcon, description: "Generate a proposal" },
      { label: "Meeting Prep", href: `/ai/meeting-prep/${companyId}`, icon: CalendarIcon, description: "Prepare for a meeting" },
      { label: "Email", href: `/ai/email/${companyId}`, icon: MailIcon, description: "AI email assistant" },
      { label: "Call Script", href: `/ai/call/${companyId}`, icon: PhoneIcon, description: "Cold call script" },
    );
  }

  if (leadId) {
    actions.push(
      { label: "Research", href: `/leads/${leadId}?tab=research`, icon: FlaskIcon, description: "AI research pipeline" },
      { label: "Outreach", href: `/leads/${leadId}?tab=outreach`, icon: SendIcon, description: "Generate outreach" },
      { label: "Timeline", href: `/leads/${leadId}?tab=timeline`, icon: ClockIcon, description: "Activity timeline" },
    );
  }

  if (actions.length === 0) return null;

  return (
    <div className={`flex flex-wrap gap-2 ${className}`}>
      {actions.map(action => (
        <Link
          key={action.label}
          href={action.href as Route}
          className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-xs text-slate-300 transition hover:border-cyan-400/30 hover:bg-cyan-400/5 hover:text-cyan-300"
          title={action.description}
        >
          <action.icon className="h-3.5 w-3.5" />
          {action.label}
        </Link>
      ))}
    </div>
  );
}

// Re-export small inline icons to avoid import clutter
import { Sparkles, FileText, CalendarCheck2, Mail, Phone, FlaskConical, Send, Clock } from "lucide-react";
const SparklesIcon = Sparkles;
const FileIcon = FileText;
const CalendarIcon = CalendarCheck2;
const MailIcon = Mail;
const PhoneIcon = Phone;
const FlaskIcon = FlaskConical;
const SendIcon = Send;
const ClockIcon = Clock;
