"use client";

import { useEffect, useState } from "react";
import { Target, Users, Phone, Mail, ArrowRight, Lightbulb, Star } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

type ContactScore = {
  contactId: number; fullName: string; jobTitle: string | null; email: string | null;
  phone: string | null; roleFitScore: number; influenceScore: number;
  accessibilityScore: number; executiveAuthority: number; technicalAuthority: number;
  operationalImpact: number; overallPriority: number; roleCategory: string; reasoning: string[];
};

type Report = {
  companyName: string;
  contactsScored: ContactScore[];
  primaryContact: ContactScore | null;
  secondaryContact: ContactScore | null;
  technicalContact: ContactScore | null;
  operationalContact: ContactScore | null;
  executiveSponsor: ContactScore | null;
  engagementStrategy: string[];
  outreachPlan: Record<string, unknown>;
};

function PriorityBadge({ score }: { score: number }) {
  const color = score >= 80 ? "bg-emerald-400/10 text-emerald-400" : score >= 60 ? "bg-amber-400/10 text-amber-400" : "bg-slate-400/10 text-slate-400";
  return <span className={`rounded-lg px-2 py-0.5 text-xs font-bold ${color}`}>{score}</span>;
}

function ContactCard({ c, label, icon: Icon }: { c: ContactScore; label: string; icon: typeof Star }) {
  return (
    <Card className="border-cyan-400/10 bg-gradient-to-r from-cyan-950/20 to-transparent">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Icon className="h-3.5 w-3.5 text-cyan-400" />
            <p className="text-xs font-semibold uppercase tracking-[0.1em] text-cyan-400">{label}</p>
          </div>
          <p className="mt-1 text-sm font-medium text-white">{c.fullName}</p>
          {c.jobTitle && <p className="text-xs text-slate-400">{c.jobTitle}</p>}
          <div className="mt-2 flex flex-wrap gap-2">
            {c.email && <span className="flex items-center gap-1 text-xs text-slate-500"><Mail className="h-3 w-3" />{c.email}</span>}
            {c.phone && <span className="flex items-center gap-1 text-xs text-slate-500"><Phone className="h-3 w-3" />{c.phone}</span>}
          </div>
        </div>
        <PriorityBadge score={c.overallPriority} />
      </div>
    </Card>
  );
}

function ScoreRow({ label, value }: { label: string; value: number }) {
  const pct = Math.min(100, Math.max(0, value));
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-28 text-slate-500">{label}</span>
      <div className="flex-1 h-1.5 rounded-full bg-white/5">
        <div className="h-full rounded-full bg-cyan-400/60" style={{ width: `${pct}%` }} />
      </div>
      <span className="w-8 text-right text-slate-400">{value}</span>
    </div>
  );
}

export function DecisionMakersTab({ companyId }: { companyId: number }) {
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);

  const mapContact = (d: Record<string, unknown>): ContactScore => ({
    contactId: d.contact_id as number, fullName: d.full_name as string, jobTitle: d.job_title as string | null,
    email: d.email as string | null, phone: d.phone as string | null,
    roleFitScore: d.role_fit_score as number, influenceScore: d.influence_score as number,
    accessibilityScore: d.accessibility_score as number, executiveAuthority: d.executive_authority as number,
    technicalAuthority: d.technical_authority as number, operationalImpact: d.operational_impact as number,
    overallPriority: d.overall_priority as number, roleCategory: d.role_category as string,
    reasoning: (d.reasoning as string[]) || [],
  });

  useEffect(() => {
    fetch(`/api/decision-maker/${companyId}`)
      .then(r => r.ok ? r.json() : Promise.reject(r))
      .then((d: Record<string, unknown>) => setReport({
        companyName: d.company_name as string,
        contactsScored: ((d.contacts_scored || []) as Record<string, unknown>[]).map(s => ({
          contactId: s.contact_id as number, fullName: s.full_name as string, jobTitle: s.job_title as string | null,
          email: s.email as string | null, phone: s.phone as string | null,
          roleFitScore: s.role_fit_score as number, influenceScore: s.influence_score as number,
          accessibilityScore: s.accessibility_score as number, executiveAuthority: s.executive_authority as number,
          technicalAuthority: s.technical_authority as number, operationalImpact: s.operational_impact as number,
          overallPriority: s.overall_priority as number, roleCategory: s.role_category as string,
          reasoning: (s.reasoning as string[]) || [],
        })),
        primaryContact: d.primary_contact ? mapContact(d.primary_contact as Record<string, unknown>) : null,
        secondaryContact: d.secondary_contact ? mapContact(d.secondary_contact as Record<string, unknown>) : null,
        technicalContact: d.technical_contact ? mapContact(d.technical_contact as Record<string, unknown>) : null,
        operationalContact: d.operational_contact ? mapContact(d.operational_contact as Record<string, unknown>) : null,
        executiveSponsor: d.executive_sponsor ? mapContact(d.executive_sponsor as Record<string, unknown>) : null,
        engagementStrategy: (d.engagement_strategy as string[]) || [],
        outreachPlan: (d.outreach_plan as Record<string, unknown>) || {},
      }))
      .catch(() => setReport(null))
      .finally(() => setLoading(false));
  }, [companyId]);

  if (loading) return <div className="space-y-2">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-24 rounded-xl" />)}</div>;
  if (!report) return <Card><p className="text-sm text-red-400">Failed to load decision maker analysis.</p></Card>;

  const hasContacts = report.contactsScored.length > 0;
  const hasStrategy = report.engagementStrategy.length > 0;
  const hasOutreach = !!(report.outreachPlan && report.outreachPlan.cold_email_body);
  const hasCallScript = !!(report.outreachPlan && report.outreachPlan.call_script);

  return (
    <div className="space-y-6">
      {/* Key Contacts */}
      <div className="grid gap-3 sm:grid-cols-2">
        {report.primaryContact && <ContactCard c={report.primaryContact} label="⭐ Primary Contact" icon={Star} />}
        {report.operationalContact && report.operationalContact.contactId !== report.primaryContact?.contactId && <ContactCard c={report.operationalContact} label="Operational Champion" icon={Target} />}
        {report.technicalContact && <ContactCard c={report.technicalContact} label="Technical Evaluator" icon={Lightbulb} />}
        {report.executiveSponsor && report.executiveSponsor.contactId !== report.primaryContact?.contactId && <ContactCard c={report.executiveSponsor} label="Executive Sponsor" icon={Users} />}
      </div>

      {/* Contact Rankings */}
      {hasContacts ? (
        <Card>
          <h4 className="mb-3 text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">Contact Priority Rankings</h4>
          <div className="space-y-3">
            {report.contactsScored.slice(0, 6).map((c, i) => (
              <div key={i} className="rounded-xl border border-white/5 bg-white/[0.01] p-3">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-slate-600">#{i + 1}</span>
                      <span className="text-sm font-medium text-white">{c.fullName}</span>
                      {c.jobTitle && <span className="text-xs text-slate-500">— {c.jobTitle}</span>}
                    </div>
                    <div className="mt-1 flex flex-wrap gap-1">
                      {c.reasoning.slice(0, 3).map((r, j) => <span key={j} className="text-[11px] text-slate-500">• {r}</span>)}
                    </div>
                  </div>
                  <PriorityBadge score={c.overallPriority} />
                </div>
                <div className="mt-2 space-y-0.5">
                  <ScoreRow label="Role Fit" value={c.roleFitScore} />
                  <ScoreRow label="Authority" value={c.executiveAuthority} />
                  <ScoreRow label="Accessibility" value={c.accessibilityScore} />
                </div>
              </div>
            ))}
          </div>
        </Card>
      ) : null}

      {/* Engagement Strategy */}
      {hasStrategy ? (
        <Card>
          <h4 className="mb-3 text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">Recommended Engagement Strategy</h4>
          <div className="space-y-2">
            {report.engagementStrategy.map((step, i) => (
              <div key={i} className="flex items-start gap-2 rounded-lg border border-white/5 px-3 py-2">
                <ArrowRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-cyan-400" />
                <span className="text-sm text-slate-300">{step}</span>
              </div>
            ))}
          </div>
        </Card>
      ) : null}

      {/* Outreach Plan */}
      {hasOutreach ? (
        <Card>
          <h4 className="mb-3 text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">Outreach Plan — {report.outreachPlan.primary_contact as string}</h4>
          <div className="space-y-3">
            <div>
              <p className="text-xs text-slate-500">Subject: {report.outreachPlan.cold_email_subject as string}</p>
              <div className="mt-1 rounded-xl border border-white/10 bg-white/5 p-3 text-sm text-slate-300 whitespace-pre-line">
                {report.outreachPlan.cold_email_body as string}
              </div>
            </div>
            {hasCallScript ? (
              <div>
                <p className="text-xs font-medium text-slate-400">Call Script:</p>
                <ul className="mt-1 space-y-1">
                  {(report.outreachPlan.call_script as string[]).map((s, i) => (
                    <li key={i} className="text-xs text-slate-400">{s}</li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>
        </Card>
      ) : null}
    </div>
  );
}
