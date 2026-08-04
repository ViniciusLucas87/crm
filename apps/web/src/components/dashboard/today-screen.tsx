"use client";

import React, { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { fetchTodayWorkspace, executeFollowUp, acknowledgeReply } from "@/lib/api";
import type { TodayWorkspace, TodayTaskItem, FollowUpRequest } from "@/lib/types";

type SectionState = "loading" | "loaded" | "empty" | "error";

export default function TodayScreen() {
  const [workspace, setWorkspace] = useState<TodayWorkspace | null>(null);
  const [state, setState] = useState<SectionState>("loading");
  const [error, setError] = useState("");
  const [actionMsg, setActionMsg] = useState("");

  const load = useCallback(async () => {
    setState("loading");
    setError("");
    try {
      const data = await fetchTodayWorkspace();
      setWorkspace(data);
      const hasData =
        data.assessmentLeads.length > 0 ||
        data.missedCalls.length > 0 ||
        data.inboundReplies.length > 0 ||
        data.overdueFollowUps.length > 0 ||
        data.dueToday.length > 0 ||
        data.upcoming.length > 0 ||
        data.leadsNoNextAction.length > 0;
      setState(hasData ? "loaded" : "empty");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load your Today workspace");
      setState("error");
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleAction = async (taskId: number, req: FollowUpRequest) => {
    setActionMsg("");
    try {
      const result = await executeFollowUp(taskId, req);
      setActionMsg(result.message);
      load();
    } catch (e) {
      setActionMsg(e instanceof Error ? e.message : "Action failed");
    }
  };

  const handleAcknowledge = async (emailId: number) => {
    setActionMsg("");
    try {
      await acknowledgeReply(emailId);
      setActionMsg("Reply acknowledged");
      load();
    } catch {
      setActionMsg("We could not acknowledge this reply. Please try again.");
    }
  };

  if (state === "loading") return <TodayLoading />;
  if (state === "error") return <TodayError message={error} onRetry={load} />;
  if (state === "empty" || !workspace) return <TodayEmpty onRefresh={load} />;

  const totalItems =
    workspace.assessmentLeads.length +
    workspace.missedCalls.length +
    workspace.inboundReplies.length +
    workspace.overdueFollowUps.length +
    workspace.dueToday.length +
    workspace.upcoming.length +
    workspace.leadsNoNextAction.length;

  return (
    <div style={{ padding: "24px 32px", maxWidth: 1100, margin: "0 auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, margin: 0, color: "var(--color-text-primary)" }}>Today</h1>
          <p style={{ margin: "4px 0 0", color: "var(--color-text-tertiary)", fontSize: 14 }}>
            {totalItems} {totalItems === 1 ? "item" : "items"} need your attention
          </p>
        </div>
        <button onClick={load} style={refreshBtnStyle}>Refresh</button>
      </div>

      {actionMsg && (
        <div style={{ background: "#ECFDF5", color: "#059669", padding: "10px 16px", borderRadius: 8, marginBottom: 16, fontSize: 14 }}>
          {actionMsg}
        </div>
      )}

      <Section title="New Assessment Leads" count={workspace.assessmentLeads.length} color="#5EEAD4">
        {workspace.assessmentLeads.map((lead) => (
          <LeadCard key={`lead-${lead.id}`} lead={lead} />
        ))}
      </Section>

      <Section title="Missed Calls" count={workspace.missedCalls.length} color="#DC2626">
        {workspace.missedCalls.map((call) => (
          <MissedCallCard key={`call-${call.id}`} call={call} />
        ))}
      </Section>

      <Section title="Inbound Replies" count={workspace.inboundReplies.length} color="#7DD3FC">
        {workspace.inboundReplies.map((reply) => (
          <ReplyCard key={`reply-${reply.id}`} reply={reply} onAcknowledge={handleAcknowledge} />
        ))}
      </Section>

      <Section title="Overdue Follow Ups" count={workspace.overdueFollowUps.length} color="#DC2626">
        {workspace.overdueFollowUps.map((task) => (
          <TaskCard key={`overdue-${task.id}`} task={task} onAction={handleAction} />
        ))}
      </Section>

      <Section title="Due Today" count={workspace.dueToday.length} color="#D97706">
        {workspace.dueToday.map((task) => (
          <TaskCard key={`today-${task.id}`} task={task} onAction={handleAction} />
        ))}
      </Section>

      <Section title="Upcoming" count={workspace.upcoming.length} color="#94A3B8">
        {workspace.upcoming.map((task) => (
          <TaskCard key={`upcoming-${task.id}`} task={task} onAction={handleAction} />
        ))}
      </Section>

      <Section title="Leads with No Next Action" count={workspace.leadsNoNextAction.length} color="#D97706">
        {workspace.leadsNoNextAction.map((task) => (
          <TaskCard key={`nolead-${task.leadId || task.id}`} task={task} onAction={handleAction} isLeadAction />
        ))}
      </Section>
    </div>
  );
}

// ── Section wrapper ──

function Section({ title, count, color, children }: { title: string; count: number; color: string; children: React.ReactNode }) {
  if (count === 0) return null;
  return (
    <div style={{ marginBottom: 24 }}>
      <h2 style={{ fontSize: 16, fontWeight: 600, color, margin: "0 0 10px", display: "flex", alignItems: "center", gap: 8 }}>
        {title}
        <span style={{ background: color, color: "#fff", borderRadius: 12, padding: "1px 8px", fontSize: 12, fontWeight: 600 }}>{count}</span>
      </h2>
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>{children}</div>
    </div>
  );
}

// ── Lead Card ──

function LeadCard({ lead }: { lead: TodayWorkspace["assessmentLeads"][0] }) {
  return (
    <div style={cardStyle}>
      <div style={{ flex: 1 }}>
        <div style={cardTitleStyle}>{lead.name || lead.companyName}</div>
        <div style={cardDetailStyle}>
          {lead.industry && `${lead.industry}, `}Score: {lead.opportunityScore}/100. {lead.reason}
        </div>
      </div>
      <div style={{ display: "flex", gap: 6 }}>
        <Link href={`/leads`} style={actionLinkStyle}>Open</Link>
      </div>
    </div>
  );
}

// ── Missed Call Card ──

function MissedCallCard({ call }: { call: TodayWorkspace["missedCalls"][0] }) {
  return (
    <div style={cardStyle}>
      <div style={{ flex: 1 }}>
        <div style={cardTitleStyle}>
          {call.callerDisplay}
          {call.companyName && <span style={{ color: "#94A3B8", fontWeight: 400 }}>, {call.companyName}</span>}
        </div>
        <div style={cardDetailStyle}>{call.reason}</div>
      </div>
      <div style={{ display: "flex", gap: 6 }}>
        {call.companyId && (
          <Link href={`/companies/${call.companyId}`} style={actionLinkStyle}>Open</Link>
        )}
        <a href={`tel:${call.callerNumber}`} style={actionLinkStyle}>Call</a>
      </div>
    </div>
  );
}

// ── Reply Card ──

function ReplyCard({ reply, onAcknowledge }: {
  reply: TodayWorkspace["inboundReplies"][0];
  onAcknowledge: (id: number) => void;
}) {
  return (
    <div style={cardStyle}>
      <div style={{ flex: 1 }}>
        <div style={cardTitleStyle}>
          {reply.fromAddress}
          {reply.companyName && <span style={{ color: "#94A3B8", fontWeight: 400 }}>, {reply.companyName}</span>}
        </div>
        <div style={cardDetailStyle}>
          {reply.subject && `${reply.subject}. `}{reply.reason}
        </div>
      </div>
      <div style={{ display: "flex", gap: 6 }}>
        {reply.companyId && (
          <Link href={`/companies/${reply.companyId}`} style={actionLinkStyle}>Open</Link>
        )}
        {reply.companyId && (
          <Link href={`/companies/${reply.companyId}?action=email`} style={actionLinkStyle}>Reply</Link>
        )}
        <button onClick={() => onAcknowledge(reply.id)} style={{ ...actionBtnStyle, color: "#059669" }}>
          Acknowledge
        </button>
      </div>
    </div>
  );
}

// ── Task Card ──

function TaskCard({
  task,
  onAction,
  isLeadAction,
}: {
  task: TodayTaskItem;
  onAction: (taskId: number, req: FollowUpRequest) => void;
  isLeadAction?: boolean;
}) {
  const [showReschedule, setShowReschedule] = useState(false);
  const [newDate, setNewDate] = useState(task.dueDate || "");
  const [nextTitle, setNextTitle] = useState("");
  const [terminalOutcome, setTerminalOutcome] = useState("");
  const [completeGuidance, setCompleteGuidance] = useState("");

  const canComplete = !isLeadAction && (nextTitle.trim() !== "" || terminalOutcome !== "");

  const handleComplete = () => {
    if (!canComplete) {
      setCompleteGuidance("Choose a terminal outcome or enter a next step before completing.");
      return;
    }
    setCompleteGuidance("");
    const req: FollowUpRequest = {
      action: "complete",
      idempotencyKey: crypto.randomUUID(),
    };
    if (nextTitle.trim()) req.nextStepTitle = nextTitle.trim();
    if (terminalOutcome) req.terminalOutcome = terminalOutcome;
    onAction(task.id, req);
    setNextTitle("");
    setTerminalOutcome("");
  };

  const handleReschedule = () => {
    onAction(task.id, {
      action: "reschedule",
      newDueDate: newDate,
      idempotencyKey: crypto.randomUUID(),
    });
    setShowReschedule(false);
  };

  const handleAssignNext = () => {
    onAction(task.id, {
      action: "assign_next_step",
      nextStepTitle: nextTitle || "Follow up",
      idempotencyKey: crypto.randomUUID(),
    });
    setNextTitle("");
  };

  const priorityColor = task.priority === "high" ? "#DC2626" : task.priority === "low" ? "#059669" : "#D97706";

  return (
    <div style={cardStyle}>
      <div style={{ flex: 1 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ background: priorityColor, width: 8, height: 8, borderRadius: "50%", flexShrink: 0 }} />
          <span style={cardTitleStyle}>{task.title}</span>
        </div>
        <div style={cardDetailStyle}>
          {task.companyName && `${task.companyName}, `}
          {task.reason}. Due {task.dueDate || "no date"}
          {task.contactName && `, ${task.contactName}`}
        </div>
      </div>
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap", alignItems: "flex-start" }}>
        {task.companyId && (
          <Link href={`/companies/${task.companyId}`} style={actionLinkStyle}>Open</Link>
        )}
        {task.contactEmail && task.companyId && (
          <Link href={`/companies/${task.companyId}?action=email`} style={actionLinkStyle}>Email</Link>
        )}
        {task.contactPhone && task.companyId && (
          <Link href={`/companies/${task.companyId}?action=call`} style={actionLinkStyle}>Call</Link>
        )}
        {!isLeadAction && (
          <>
            <button onClick={handleComplete} style={canComplete ? { ...actionBtnStyle, background: "#059669", color: "#fff" } : actionBtnStyle}>
              Complete
            </button>
            <button onClick={() => setShowReschedule(!showReschedule)} style={actionBtnStyle}>Reschedule</button>
          </>
        )}
        {isLeadAction && (
          <button onClick={handleAssignNext} style={{ ...actionBtnStyle, background: "#0B1526", color: "#fff" }}>
            Assign Next Step
          </button>
        )}
      </div>

      {!isLeadAction && (
        <div style={{ marginTop: 8 }}>
          <input
            type="text"
            placeholder="Next step title (optional)"
            value={nextTitle}
            onChange={(e) => { setNextTitle(e.target.value); setCompleteGuidance(""); }}
            style={textInputStyle}
          />
          <select
            value={terminalOutcome}
            onChange={(e) => { setTerminalOutcome(e.target.value); setCompleteGuidance(""); }}
            style={{ ...textInputStyle, width: "auto", marginLeft: 8, color: terminalOutcome ? "#E2E8F0" : "#94A3B8" }}
          >
            <option value="">Terminal outcome (optional)</option>
            <option value="won">Won</option>
            <option value="lost">Lost</option>
            <option value="disqualified">Disqualified</option>
            <option value="archived">Archived</option>
          </select>
          {completeGuidance && (
            <div style={{ color: "#D97706", fontSize: 12, marginTop: 4 }}>{completeGuidance}</div>
          )}
        </div>
      )}

      {showReschedule && (
        <div style={{ marginTop: 8, display: "flex", gap: 6, alignItems: "center" }}>
          <input
            type="date"
            value={newDate}
            onChange={(e) => setNewDate(e.target.value)}
            style={{ fontSize: 13, padding: "4px 8px", border: "1px solid #E8ECF0", borderRadius: 6 }}
          />
          <button onClick={handleReschedule} style={{ ...actionBtnStyle, background: "#D97706", color: "#fff" }}>Save</button>
        </div>
      )}
    </div>
  );
}

// ── States ──

function TodayLoading() {
  return (
    <div style={{ padding: "48px 32px", textAlign: "center", color: "#526372" }}>
      <p style={{ fontSize: 16 }}>Loading your Today workspace</p>
    </div>
  );
}

function TodayError({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div style={{ padding: "48px 32px", textAlign: "center" }}>
      <p style={{ color: "#DC2626", fontSize: 14, marginBottom: 12 }}>{message}</p>
      <button onClick={onRetry} style={{ ...actionBtnStyle, background: "#0B1526", color: "#fff", padding: "8px 20px" }}>Try Again</button>
    </div>
  );
}

function TodayEmpty({ onRefresh }: { onRefresh: () => void }) {
  return (
    <div style={{ padding: "48px 32px", textAlign: "center" }}>
      <p style={{ fontSize: 16, color: "#0B1526", fontWeight: 600, margin: 0 }}>All caught up</p>
      <p style={{ color: "#526372", fontSize: 14, marginTop: 4 }}>There is nothing that needs your attention right now.</p>
      <button onClick={onRefresh} style={{ marginTop: 16, ...actionBtnStyle, background: "#0B1526", color: "#fff", padding: "8px 20px" }}>Refresh</button>
    </div>
  );
}

// ── Styles ──

const cardStyle: React.CSSProperties = {
  background: "var(--color-bg-elevated)",
  border: "1px solid var(--color-border-default)",
  borderRadius: 10,
  padding: "14px 18px",
  display: "flex",
  flexWrap: "wrap",
  gap: 10,
  alignItems: "flex-start",
};

const actionLinkStyle: React.CSSProperties = {
  fontSize: 13,
  fontWeight: 500,
  color: "var(--color-text-primary)",
  background: "var(--color-bg-overlay)",
  textDecoration: "none",
  padding: "5px 12px",
  border: "1px solid var(--color-border-strong)",
  borderRadius: 6,
  whiteSpace: "nowrap",
};

const actionBtnStyle: React.CSSProperties = {
  fontSize: 13,
  fontWeight: 500,
  background: "var(--color-bg-overlay)",
  color: "var(--color-text-primary)",
  border: "1px solid var(--color-border-strong)",
  borderRadius: 6,
  padding: "5px 12px",
  cursor: "pointer",
  whiteSpace: "nowrap",
};

const refreshBtnStyle: React.CSSProperties = {
  ...actionBtnStyle,
  background: "#0B1526",
  color: "#fff",
  border: "none",
  padding: "8px 18px",
};

const cardTitleStyle: React.CSSProperties = {
  fontWeight: 600,
  color: "var(--color-text-primary)",
  fontSize: 14,
};

const cardDetailStyle: React.CSSProperties = {
  color: "var(--color-text-secondary)",
  fontSize: 13,
  marginTop: 2,
};

const textInputStyle: React.CSSProperties = {
  fontSize: 13,
  padding: "6px 9px",
  border: "1px solid var(--color-border-strong)",
  borderRadius: 6,
  width: "100%",
  maxWidth: 280,
  background: "var(--color-bg-overlay)",
  color: "var(--color-text-primary)",
};
