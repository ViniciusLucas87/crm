"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import type { Route } from "next";
import { useParams, useRouter } from "next/navigation";
import { Building2, Globe, Mail, Phone, MapPin, Users, Briefcase, Hash, Calendar, Clock, FileText, ClipboardList, FolderKanban, Target, Sparkles, ChevronLeft, MessageSquare } from "lucide-react";
import { Shell } from "@/components/dashboard/shell";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { AiActionsBar } from "@/components/ui/page-header";
import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { CompanyContactsTab } from "@/components/companies/company-contacts-tab";
import { TimelineView } from "@/components/dashboard/timeline-view";
import { CompanyIntelligenceTab } from "@/components/companies/company-intelligence-tab";
import { DocumentManager } from "@/components/companies/document-manager";
import { CompanyTasksTab } from "@/components/companies/company-tasks-tab";
import { CompanyOpportunitiesTab } from "@/components/companies/company-opportunities-tab";
import { CompanyAiSummaryTab } from "@/components/companies/company-ai-summary-tab";
import { CompanyConversationTab } from "@/components/companies/company-conversation-tab";
import { useTelephony } from "@/lib/telephony-context";
import { CopilotPanel } from "@/components/transcription/copilot-panel";
import { LiveTranscript } from "@/components/transcription/live-transcript";
import { ConversationTimeline } from "@/components/transcription/conversation-timeline";
import { ConversationOpening } from "@/components/transcription/conversation-opening";
import { PostCallPreview } from "@/components/transcription/postcall-preview";
import { CallButton } from "@/components/companies/call-button";
import { ApiError, fetchCompany } from "@/lib/api";
import type { Company } from "@/lib/types";


type TabId = "overview" | "contacts" | "tasks" | "opportunities" | "timeline" | "intelligence" | "documents" | "ai-summary" | "conversation";

const tabs: { id: TabId; label: string; icon: typeof Building2 }[] = [
  { id: "overview", label: "Overview", icon: Building2 },
  { id: "contacts", label: "Contacts", icon: Users },
  { id: "tasks", label: "Tasks", icon: ClipboardList },
  { id: "opportunities", label: "Opportunities", icon: Target },
  { id: "timeline", label: "Timeline", icon: Clock },
  { id: "intelligence", label: "Intelligence", icon: Sparkles },
  { id: "documents", label: "Documents", icon: FolderKanban },
  { id: "ai-summary", label: "AI Summary", icon: Sparkles },
  { id: "conversation", label: "Conversation", icon: MessageSquare },
];

const emptyMessages: Record<Exclude<TabId, "overview">, { title: string; description: string }> = {
  contacts: { title: "No contacts yet", description: "Add contacts to this company to track key decision-makers and relationships." },
  tasks: { title: "No tasks yet", description: "Create tasks to track follow-ups and action items for this company." },
  opportunities: { title: "No opportunities yet", description: "Create pipeline opportunities linked to this company." },
  timeline: { title: "No timeline entries", description: "Recent activity and updates for this company will appear here." },
  intelligence: { title: "Intelligence analysis", description: "Click refresh to generate buying signals and opportunity scores." },
  documents: { title: "No documents yet", description: "Upload proposals, contracts, and files related to this company." },
  "ai-summary": { title: "AI Summary coming soon", description: "AI-powered company intelligence will be available in Sprint 3." },
  conversation: { title: "No conversation yet", description: "Start a conversation to track your relationship with this company across calls, emails, and meetings." },
};

export default function CompanyDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const companyId = Number(params.id);

  const [company, setCompany] = useState<Company | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabId>("overview");
  const { startCall, call, transcription, transcriptId } = useTelephony();

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const c = await fetchCompany(companyId);
        if (!cancelled) { setCompany(c); setError(null); }
      } catch (err) {
        if (err instanceof ApiError && err.status === 401) { router.replace("/sign-in" as Route); return; }
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load company");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void load();
    return () => { cancelled = true; };
  }, [companyId, router]);

  if (loading) {
    return (
      <Shell>
        <div className="space-y-6">
          <Skeleton className="h-5 w-48" />
          <Skeleton className="h-10 w-full" />
          <div className="grid gap-4 sm:grid-cols-2">
            {Array.from({ length: 6 }).map((_, i) => (<Skeleton key={i} className="h-24 rounded-2xl" />))}
          </div>
        </div>
      </Shell>
    );
  }

  if (error || !company) {
    return (
      <Shell>
        <Card>
          <h3 className="text-lg font-semibold text-white">Company not found</h3>
          <p className="mt-2 text-sm text-slate-400">{error ?? "The requested company could not be loaded."}</p>
          <Link href={"/companies" as Route} className="mt-4 inline-flex items-center gap-1 text-sm text-cyan-400 hover:underline"><ChevronLeft className="h-4 w-4" />Back to Companies</Link>
        </Card>
      </Shell>
    );
  }

  return (
    <Shell>
      <div className="space-y-6">
        <Breadcrumbs items={[{ label: "Companies", href: "/companies" }, { label: company.name }]} />

        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 className="text-2xl font-semibold tracking-tight text-white">{company.name}</h2>
            <div className="mt-1 flex flex-wrap items-center gap-3 text-sm text-slate-400">
              {company.industry && <span>{company.industry}</span>}
              {company.website && (
                <a href={company.website.startsWith("http") ? company.website : `https://${company.website}`} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-cyan-400 hover:underline">
                  <Globe className="h-3 w-3" />{company.website}
                </a>
              )}
            </div>
          </div>
          <Badge variant={company.isArchived ? "danger" : "success"}>{company.isArchived ? "Archived" : company.status}</Badge>
        </div>

        {/* AI Actions Bar */}
        <AiActionsBar companyId={company.id} />

        {/* Call button ΓÇö uses primary contact phone via telephony context */}
        <CallButton companyId={company.id} callState={call.state} onCall={startCall} />
        {/* Sprint 46 — Conversation Opening (visible before call starts) */}
        {call.state === "idle" && (
          <ConversationOpening companyId={company.id} isCallActive={false} />
        )}
        {/* Sprint 46 — Live Copilot 2.0: 70/30 layout during active calls */}
        {call.state !== "idle" && call.state !== "ended" && call.state !== "failed" && (
          <div className="grid gap-4" style={{ gridTemplateColumns: "minmax(0, 2.2fr) minmax(0, 1fr)" }}>
            <LiveTranscript state={transcription} onStop={() => {}} />
            <CopilotPanel callId={call.callId || companyId} isCallActive={true} segments={transcription.segments || []} />
          </div>
        )}

        {/* Post-call — Conversation Timeline + Post-Call Preview */}
        {(call.state === "ended" || call.state === "failed") && transcriptId && transcriptId > 0 && (
          <div className="space-y-4">
            <PostCallPreview transcriptId={transcriptId} callId={call.callId} />
            <ConversationTimeline transcriptId={transcriptId} />
          </div>
        )}

        <div className="flex flex-wrap gap-1 overflow-x-auto rounded-2xl border border-white/10 bg-slate-900/40 p-1">
          {tabs.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              type="button"
              onClick={() => setActiveTab(id)}
              className={`flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-medium transition focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400/50 ${
                activeTab === id ? "bg-white/10 text-white" : "text-slate-500 hover:text-slate-300"
              }`}
            >
              <Icon className="h-4 w-4" />
              {label}
            </button>
          ))}
        </div>

        {activeTab === "overview" ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <FieldCard icon={Building2} label="Industry" value={company.industry} />
            <FieldCard icon={Globe} label="Website" value={company.website} isLink />
            <FieldCard icon={Mail} label="Email" value={company.email} />
            <FieldCard icon={Phone} label="Phone" value={company.phone} />
            <FieldCard icon={MapPin} label="Address" value={company.address} />
            <FieldCard icon={Users} label="Employees" value={company.employees?.toLocaleString()} />
            <FieldCard icon={Hash} label="Revenue" value={company.revenue ? `$${Number(company.revenue).toLocaleString()}` : null} />
            <FieldCard icon={Briefcase} label="Owner" value={company.owner} />
            <FieldCard icon={Calendar} label="Created" value={new Date(company.createdAt).toLocaleDateString()} />
            <FieldCard icon={FileText} label="Notes" value={company.notes} span />
          </div>
        ) : activeTab === "contacts" ? (
          <CompanyContactsTab companyId={company.id} />
        ) : activeTab === "documents" ? (
          <DocumentManager companyId={company.id} />
        ) : activeTab === "tasks" ? (
          <CompanyTasksTab companyId={company.id} />
        ) : activeTab === "opportunities" ? (
          <CompanyOpportunitiesTab companyId={company.id} />
        ) : activeTab === "ai-summary" ? (
          <CompanyAiSummaryTab companyId={company.id} />
        ) : activeTab === "timeline" ? (
          <TimelineView companyId={company.id} />
        ) : activeTab === "intelligence" ? (
          <CompanyIntelligenceTab companyId={company.id} />
        ) : activeTab === "conversation" ? (
          <CompanyConversationTab companyId={company.id} />
        ) : (
          <EmptyState
            icon={tabs.find(t => t.id === activeTab)?.icon}
            title={emptyMessages[activeTab as Exclude<TabId, "overview">]?.title ?? "Coming soon"}
            description={emptyMessages[activeTab as Exclude<TabId, "overview">]?.description ?? ""}
          />
        )}
      </div>
    </Shell>
  );
}

function FieldCard({ icon: Icon, label, value, isLink, span }: { icon: typeof Building2; label: string; value?: string | null; isLink?: boolean; span?: boolean }) {
  return (
    <Card className={span ? "sm:col-span-2 lg:col-span-3" : ""}>
      <div className="mb-3 inline-flex rounded-lg border border-white/10 bg-white/5 p-1.5 text-slate-400">
        <Icon className="h-3.5 w-3.5" />
      </div>
      <p className="text-xs font-medium uppercase tracking-[0.08em] text-slate-500">{label}</p>
      <p className="mt-1 text-sm text-slate-200">
        {value ? (
          isLink ? (
            <a href={value.startsWith("http") ? value : `https://${value}`} target="_blank" rel="noopener noreferrer" className="text-cyan-400 hover:underline">{value}</a>
          ) : value
        ) : (
          <span className="text-slate-600">ΓÇö</span>
        )}
      </p>
    </Card>
  );
}
