"use client";

import { Card } from "@/components/ui/card";

// ── Helpers ──

function parseJSON<T>(data: string | null | undefined): T | null {
  if (!data) return null;
  try { return JSON.parse(data); } catch { return null; }
}

// ═══════════════════════════════════════════════════════════
// WEBSITE INTELLIGENCE CARD
// ═══════════════════════════════════════════════════════════

type WebsiteData = {
  provider?: string; stage?: string; status?: string;
  data?: {
    phone_numbers?: string[]; general_email?: string; sales_email?: string;
    support_email?: string; contact_page_url?: string; website_title?: string;
    services?: string[]; industries_served?: string[];
    office_locations?: string[]; certifications?: string[];
    technology_references?: string[];
  };
  evidence?: {
    requested_url?: string; source_url?: string; redirected_cross_domain?: boolean;
    title?: string; meta_description?: string;
    emails?: string[]; phones?: string[]; important_links?: Record<string, string>;
    evidence_chars?: number;
  };
  analysis?: string;
  processing_time_ms?: number;
};

export function WebsiteIntelCard({ data }: { data: string | null | undefined }) {
  const parsed = parseJSON<WebsiteData>(data);
  if (!parsed || parsed.status === "failed") return null;
  const d = parsed.data || {};
  const evidence = parsed.evidence;

  return (
    <Card className="border-green-400/10 bg-gradient-to-r from-green-400/5 to-teal-400/5">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-sm">🌐</span>
        <p className="text-xs font-semibold uppercase tracking-[0.1em] text-green-300">Website Intelligence</p>
      </div>
      <div className="grid gap-2 sm:grid-cols-2 text-xs">
        {(evidence?.title || d.website_title) && <div><span className="text-slate-500">Title: </span><span className="text-slate-300">{evidence?.title || d.website_title}</span></div>}
        {d.services && d.services.length > 0 && <div><span className="text-slate-500">Services: </span><span className="text-slate-300">{d.services.slice(0, 4).join(", ")}</span></div>}
        {d.industries_served && d.industries_served.length > 0 && <div><span className="text-slate-500">Industries: </span><span className="text-slate-300">{d.industries_served.join(", ")}</span></div>}
        {(evidence?.phones?.[0] || d.phone_numbers?.[0]) && <div><span className="text-slate-500">Phone: </span><span className="text-slate-300">{evidence?.phones?.[0] || d.phone_numbers?.[0]}</span></div>}
        {(evidence?.emails?.[0] || d.general_email) && <div><span className="text-slate-500">Email: </span><span className="text-cyan-400">{evidence?.emails?.[0] || d.general_email}</span></div>}
        {d.sales_email && <div><span className="text-slate-500">Sales: </span><span className="text-cyan-400">{d.sales_email}</span></div>}
        {d.office_locations && d.office_locations.length > 0 && <div><span className="text-slate-500">Offices: </span><span className="text-slate-400">{d.office_locations.join(", ")}</span></div>}
        {d.certifications && d.certifications.length > 0 && <div><span className="text-slate-500">Certs: </span><span className="text-slate-400">{d.certifications.join(", ")}</span></div>}
      </div>
      {evidence?.redirected_cross_domain && (
        <p className="mt-2 rounded-lg border border-amber-400/20 bg-amber-400/5 px-3 py-2 text-xs text-amber-300">
          Verify identity: the supplied website redirected to a different domain before using this evidence for outreach.
        </p>
      )}
      {parsed.analysis && <p className="mt-3 whitespace-pre-wrap text-xs leading-relaxed text-slate-400">{parsed.analysis}</p>}
      <div className="mt-2 pt-2 border-t border-white/5 text-xs text-slate-600">
        Source: {evidence?.source_url ? <a href={evidence.source_url} target="_blank" rel="noopener noreferrer" className="text-cyan-500 hover:underline">live website evidence</a> : "Website analysis"}
        {evidence?.evidence_chars ? ` · ${evidence.evidence_chars.toLocaleString()} characters read` : ""}
      </div>
    </Card>
  );
}

// ═══════════════════════════════════════════════════════════
// GOOGLE REVIEWS INTELLIGENCE CARD
// ═══════════════════════════════════════════════════════════

type ReviewsData = {
  provider?: string; stage?: string; status?: string;
  data?: {
    average_rating?: number; review_count_estimate?: number;
    top_strengths?: string[]; common_complaints?: string[];
    operational_pain_points?: string[]; software_opportunities?: string[];
    customer_experience_summary?: string;
  };
  processing_time_ms?: number;
};

export function ReviewsIntelCard({ data }: { data: string | null | undefined }) {
  const parsed = parseJSON<ReviewsData>(data);
  if (!parsed || parsed.status === "failed") return null;
  const d = parsed.data || {};

  return (
    <Card className="border-yellow-400/10 bg-gradient-to-r from-yellow-400/5 to-amber-400/5">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-sm">⭐</span>
        <p className="text-xs font-semibold uppercase tracking-[0.1em] text-yellow-300">Google Reviews Intelligence</p>
        {d.average_rating && <span className="ml-auto text-xs text-amber-400">★ {d.average_rating} ({d.review_count_estimate ?? "?"} reviews)</span>}
      </div>
      <div className="grid gap-2 sm:grid-cols-2 text-xs">
        {d.top_strengths && d.top_strengths.length > 0 && (
          <div><span className="text-slate-500">Strengths: </span><span className="text-emerald-400">{d.top_strengths.slice(0, 3).join(", ")}</span></div>
        )}
        {d.common_complaints && d.common_complaints.length > 0 && (
          <div><span className="text-slate-500">Complaints: </span><span className="text-red-400">{d.common_complaints.slice(0, 3).join(", ")}</span></div>
        )}
        {d.operational_pain_points && d.operational_pain_points.length > 0 && (
          <div className="sm:col-span-2"><span className="text-slate-500">Pain Points: </span><span className="text-slate-300">{d.operational_pain_points.join(" · ")}</span></div>
        )}
        {d.customer_experience_summary && (
          <div className="sm:col-span-2"><p className="text-slate-400 italic">{d.customer_experience_summary}</p></div>
        )}
        {d.software_opportunities && d.software_opportunities.length > 0 && (
          <div className="sm:col-span-2"><span className="text-slate-500">SW Opportunities: </span><span className="text-purple-400">{d.software_opportunities.join(" · ")}</span></div>
        )}
      </div>
      <div className="mt-2 pt-2 border-t border-white/5 text-xs text-slate-600">Source: Review analysis{parsed.processing_time_ms ? ` · ${(parsed.processing_time_ms / 1000).toFixed(1)}s` : ""}</div>
    </Card>
  );
}

// ═══════════════════════════════════════════════════════════
// LINKEDIN INTELLIGENCE CARD
// ═══════════════════════════════════════════════════════════

type LinkedInData = {
  provider?: string; stage?: string; status?: string;
  data?: {
    linkedin_url?: string; company_size_on_linkedin?: string;
    employee_count_on_linkedin?: number; headquarters?: string;
    decision_makers?: Array<{ name: string; role: string; confidence: number; likely_decision_maker: boolean }>;
    departments?: string[]; growth_indicators?: { hiring_now?: boolean; hiring_roles?: string[] };
    recommended_contact?: { name: string; role: string; confidence: number; reason: string };
  };
  processing_time_ms?: number;
};

export function LinkedInIntelCard({ data }: { data: string | null | undefined }) {
  const parsed = parseJSON<LinkedInData>(data);
  if (!parsed || parsed.status === "failed") return null;
  const d = parsed.data || {};
  const rc = d.recommended_contact;
  const dm = d.decision_makers || [];
  const gi = d.growth_indicators || {};

  return (
    <Card className="border-blue-400/10 bg-gradient-to-r from-blue-400/5 to-indigo-400/5">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-sm">🔗</span>
        <p className="text-xs font-semibold uppercase tracking-[0.1em] text-blue-300">LinkedIn Intelligence</p>
        {d.company_size_on_linkedin && <span className="ml-auto text-xs text-slate-400">{d.company_size_on_linkedin} employees</span>}
      </div>
      <div className="grid gap-2 sm:grid-cols-2 text-xs">
        {d.headquarters && <div><span className="text-slate-500">HQ: </span><span className="text-slate-300">{d.headquarters}</span></div>}
        {d.departments && d.departments.length > 0 && <div><span className="text-slate-500">Depts: </span><span className="text-slate-300">{d.departments.join(", ")}</span></div>}
        {gi.hiring_now && <div><span className="text-slate-500">Hiring: </span><span className="text-emerald-400">Active{gi.hiring_roles ? ` — ${gi.hiring_roles.join(", ")}` : ""}</span></div>}
        {dm.length > 0 && (
          <div className="sm:col-span-2">
            <span className="text-slate-500">Decision Makers: </span>
            {dm.slice(0, 3).map((m, i) => (
              <span key={i} className="text-slate-300">{m.name} ({m.role}){i < Math.min(dm.length, 3) - 1 ? ", " : ""}</span>
            ))}
          </div>
        )}
      </div>
      {rc && rc.name && (
        <div className="mt-3 rounded-lg border border-emerald-400/20 bg-emerald-400/5 p-3">
          <p className="text-xs font-medium text-emerald-300">🎯 Recommended Contact</p>
          <p className="text-sm font-semibold text-white mt-0.5">{rc.name} — {rc.role}</p>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-xs text-emerald-400">{rc.confidence}% confidence</span>
          </div>
          {rc.reason && <p className="text-xs text-slate-400 mt-1">{rc.reason}</p>}
        </div>
      )}
      <div className="mt-2 pt-2 border-t border-white/5 text-xs text-slate-600">Source: LinkedIn analysis{parsed.processing_time_ms ? ` · ${(parsed.processing_time_ms / 1000).toFixed(1)}s` : ""}</div>
    </Card>
  );
}
