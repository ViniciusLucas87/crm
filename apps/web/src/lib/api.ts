import type { Company, CompanyCreateInput, CompanyList, CompanyUpdateInput, DashboardSummary } from "@/lib/types";

const API_BASE_URL = "/api";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export type AppFactoryEvidence = {
  source_type: string; source_title: string; source_url: string;
  observed_at: string; signal: string; evidence_kind: string;
};

export type AppFactoryCandidate = {
  id: number; slug: string; name: string; audience: string; problem: string;
  proposed_format: string; proposed_price: string; distribution_thesis: string;
  current_workaround: string; decision: string; decision_reason: string;
  scores: Record<string, number>; total_score: number;
  estimated_monthly_cost_cents: number; risk_level: string;
  evidence_count: number; evidence_complete: boolean;
  eligible_for_validation: boolean; eligible_for_build: boolean;
  evidence: AppFactoryEvidence[];
};

export type AppFactoryPortfolio = {
  summary: {
    problems_researched: number; qualified_for_validation: number;
    qualified_for_build: number; active_experiments: number;
    monthly_experiment_cost_limit_cents: number; human_actions: string[];
  };
  candidates: AppFactoryCandidate[];
  experiments: Array<{ id: number; candidate_id: number; name: string; hypothesis: string; channel: string; success_metric: string; status: string; spend_limit_cents: number; actual_spend_cents: number; visitors: number; intent_actions: number; paid_conversions: number }>;
  guardrails: Record<string, boolean | number>;
};

export async function fetchAppFactoryPortfolio(): Promise<AppFactoryPortfolio> {
  const response = await fetch(`${API_BASE_URL}/app-factory/portfolio`, { cache: "no-store" });
  if (!response.ok) throw new ApiError(`Failed to load App Factory: ${response.status}`, response.status);
  return response.json();
}

export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  const response = await fetch(`${API_BASE_URL}/dashboard/summary`, {
    cache: "no-store"
  });

  if (!response.ok) {
    throw new ApiError(`Failed to load dashboard summary: ${response.status}`, response.status);
  }

  const payload = (await response.json()) as {
    tasks_today: number;
    companies: number;
    active_opportunities: number;
    meetings: number;
    pipeline_value: number;
    won_deals: number;
    revenue_forecast: number;
    activities_due_today: number;
  };

  return {
    tasksToday: payload.tasks_today,
    companies: payload.companies,
    activeOpportunities: payload.active_opportunities,
    meetings: payload.meetings,
    pipelineValue: payload.pipeline_value,
    wonDeals: payload.won_deals,
    revenueForecast: payload.revenue_forecast,
    activitiesDueToday: payload.activities_due_today
  };
}

type ListCompaniesParams = {
  page?: number;
  pageSize?: number;
  search?: string;
  owner?: string;
  status?: string;
  sortBy?: string;
  sortDir?: "asc" | "desc";
  includeArchived?: boolean;
};

function mapCompany(payload: {
  id: number;
  name: string;
  industry: string | null;
  website: string | null;
  phone: string | null;
  email: string | null;
  address: string | null;
  employees: number | null;
  revenue: number | null;
  status: string;
  tags: string | null;
  owner: string | null;
  notes: string | null;
  primary_contact_id: number | null;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}): Company {
  return {
    id: payload.id,
    name: payload.name,
    industry: payload.industry,
    website: payload.website,
    phone: payload.phone,
    email: payload.email,
    address: payload.address,
    employees: payload.employees,
    revenue: payload.revenue,
    status: payload.status,
    tags: payload.tags,
    owner: payload.owner,
    notes: payload.notes,
    primaryContactId: payload.primary_contact_id,
    isArchived: payload.is_archived,
    createdAt: payload.created_at,
    updatedAt: payload.updated_at
  };
}

export async function listCompanies(params: ListCompaniesParams = {}): Promise<CompanyList> {
  const query = new URLSearchParams();
  query.set("page", String(params.page ?? 1));
  query.set("page_size", String(params.pageSize ?? 10));
  if (params.search) query.set("search", params.search);
  if (params.owner) query.set("owner", params.owner);
  if (params.status) query.set("status", params.status);
  if (params.sortBy) query.set("sort_by", params.sortBy);
  if (params.sortDir) query.set("sort_dir", params.sortDir);
  if (params.includeArchived) query.set("include_archived", "true");

  const response = await fetch(`${API_BASE_URL}/companies?${query.toString()}`, {
    cache: "no-store"
  });
  if (!response.ok) {
    throw new ApiError(`Failed to list companies: ${response.status}`, response.status);
  }

  const payload = (await response.json()) as {
    items: Array<Parameters<typeof mapCompany>[0]>;
    total: number;
    page: number;
    page_size: number;
  };

  return {
    items: payload.items.map(mapCompany),
    total: payload.total,
    page: payload.page,
    pageSize: payload.page_size
  };
}

export async function createCompany(input: CompanyCreateInput): Promise<Company> {
  const response = await fetch(`${API_BASE_URL}/companies`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input)
  });
  if (!response.ok) {
    throw new ApiError(`Failed to create company: ${response.status}`, response.status);
  }
  return mapCompany((await response.json()) as Parameters<typeof mapCompany>[0]);
}

export async function updateCompany(companyId: number, input: CompanyUpdateInput): Promise<Company> {
  const response = await fetch(`${API_BASE_URL}/companies/${companyId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input)
  });
  if (!response.ok) {
    throw new ApiError(`Failed to update company: ${response.status}`, response.status);
  }
  return mapCompany((await response.json()) as Parameters<typeof mapCompany>[0]);
}

export async function archiveCompany(companyId: number): Promise<Company> {
  const response = await fetch(`${API_BASE_URL}/companies/${companyId}`, {
    method: "DELETE"
  });
  if (!response.ok) {
    throw new ApiError(`Failed to archive company: ${response.status}`, response.status);
  }
  return mapCompany((await response.json()) as Parameters<typeof mapCompany>[0]);
}

export async function restoreCompany(companyId: number): Promise<Company> {
  const response = await fetch(`${API_BASE_URL}/companies/${companyId}/restore`, {
    method: "POST"
  });
  if (!response.ok) {
    throw new ApiError(`Failed to restore company: ${response.status}`, response.status);
  }
  return mapCompany((await response.json()) as Parameters<typeof mapCompany>[0]);
}

export async function duplicateCompany(companyId: number): Promise<Company> {
  const response = await fetch(`${API_BASE_URL}/companies/${companyId}/duplicate`, {
    method: "POST"
  });
  if (!response.ok) {
    throw new ApiError(`Failed to duplicate company: ${response.status}`, response.status);
  }
  return mapCompany((await response.json()) as Parameters<typeof mapCompany>[0]);
}

export async function fetchCompany(companyId: number): Promise<Company> {
  const response = await fetch(`${API_BASE_URL}/companies/${companyId}`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new ApiError(`Failed to fetch company: ${response.status}`, response.status);
  }
  return mapCompany((await response.json()) as Parameters<typeof mapCompany>[0]);
}

// ── Helpers ──

function toSnakeCase(str: string): string {
  return str.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`);
}

// ── Audit ──

export interface AuditEntry {
  id: number;
  actor_user_id: string | null;
  idempotency_key: string;
  entity_type: string;
  entity_id: number;
  action: string;
  old_state: string | null;
  new_state: string | null;
  notes: string | null;
  created_at: string;
}

export interface AuditListResponse {
  entries: AuditEntry[];
  total: number;
  page: number;
  page_size: number;
}

export interface AuditListParams {
  page?: number;
  page_size?: number;
  entity_type?: string;
  entity_id?: number;
  action?: string;
}

export async function fetchAuditEntries(params: AuditListParams = {}): Promise<AuditListResponse> {
  const query = new URLSearchParams();
  query.set("page", String(params.page ?? 1));
  query.set("page_size", String(params.page_size ?? 50));
  if (params.entity_type) query.set("entity_type", params.entity_type);
  if (params.entity_id != null) query.set("entity_id", String(params.entity_id));
  if (params.action) query.set("action", params.action);

  const response = await fetch(`${API_BASE_URL}/audit?${query.toString()}`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new ApiError(`Failed to fetch audit entries: ${response.status}`, response.status);
  }
  return response.json() as Promise<AuditListResponse>;
}

// ── Operations ──

export interface OperationsStatus {
  status: string;
  build_id: string;
  git_commit: string;
  environment: string;
  db_status: string;
  db_latency_ms: number;
  redis_status: string;
  outbox_pending: number;
  outbox_failed: number;
  backups_ok: boolean | null;
  backup_last_ts: string | null;
  worker_status: string;
  worker_heartbeat_ms: number | null;
  generated_at: string;
}

export async function fetchOperationsStatus(): Promise<OperationsStatus> {
  const response = await fetch(`${API_BASE_URL}/operations/status`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new ApiError(`Failed to fetch operations status: ${response.status}`, response.status);
  }
  return response.json() as Promise<OperationsStatus>;
}

function toSnakeKeys(obj: Record<string, unknown>): Record<string, unknown> {
  const result: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(obj)) {
    if (value !== undefined) {
      result[toSnakeCase(key)] = value;
    }
  }
  return result;
}

// ── Contacts ──

export async function listContacts(companyId: number, params: { page?: number; pageSize?: number; search?: string } = {}): Promise<ContactList> {
  const q = new URLSearchParams({ company_id: String(companyId), page: String(params.page ?? 1), page_size: String(params.pageSize ?? 20) });
  if (params.search) q.set("search", params.search);
  const r = await fetch(`${API_BASE_URL}/contacts?${q}`, { cache: "no-store" });
  if (!r.ok) throw new ApiError(`Failed: ${r.status}`, r.status);
  const p = await r.json();
  return { items: p.items.map((c: Record<string, unknown>) => ({ id: c.id, companyId: c.companyId ?? c.company_id, firstName: c.firstName ?? c.first_name, lastName: c.lastName ?? c.last_name, jobTitle: c.jobTitle ?? c.job_title, department: c.department, email: c.email, phone: c.phone, mobile: c.mobile, linkedin: c.linkedin, preferredContact: c.preferredContact ?? c.preferred_contact, isDecisionMaker: c.isDecisionMaker ?? c.is_decision_maker, isPrimary: c.isPrimary ?? c.is_primary, confidence: c.confidence, notes: c.notes, status: c.status, createdAt: c.createdAt ?? c.created_at, updatedAt: c.updatedAt ?? c.updated_at })), total: p.total, page: p.page, pageSize: p.pageSize ?? p.page_size };
}

export async function createContact(input: ContactCreateInput): Promise<Contact> {
  const r = await fetch(`${API_BASE_URL}/contacts`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(toSnakeKeys(input as unknown as Record<string, unknown>)) });
  if (!r.ok) throw new ApiError(`Failed: ${r.status}`, r.status);
  const c = await r.json();
  return { id: c.id, companyId: c.company_id, firstName: c.first_name, lastName: c.last_name, jobTitle: c.job_title, department: c.department, email: c.email, phone: c.phone, mobile: c.mobile, linkedin: c.linkedin, preferredContact: c.preferred_contact, isDecisionMaker: c.is_decision_maker, isPrimary: c.is_primary, confidence: c.confidence, notes: c.notes, status: c.status, createdAt: c.created_at, updatedAt: c.updated_at };
}

export async function updateContact(id: number, input: ContactUpdateInput): Promise<Contact> {
  const r = await fetch(`${API_BASE_URL}/contacts/${id}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(toSnakeKeys(input as unknown as Record<string, unknown>)) });
  if (!r.ok) throw new ApiError(`Failed: ${r.status}`, r.status);
  const c = await r.json();
  return { id: c.id, companyId: c.company_id, firstName: c.first_name, lastName: c.last_name, jobTitle: c.job_title, department: c.department, email: c.email, phone: c.phone, mobile: c.mobile, linkedin: c.linkedin, preferredContact: c.preferred_contact, isDecisionMaker: c.is_decision_maker, isPrimary: c.is_primary, confidence: c.confidence, notes: c.notes, status: c.status, createdAt: c.created_at, updatedAt: c.updated_at };
}

export async function deleteContact(id: number): Promise<Contact> {
  const r = await fetch(`${API_BASE_URL}/contacts/${id}`, { method: "DELETE" });
  if (!r.ok) throw new ApiError(`Failed: ${r.status}`, r.status);
  const c = await r.json();
  return { id: c.id, companyId: c.company_id, firstName: c.first_name, lastName: c.last_name, jobTitle: c.job_title, department: c.department, email: c.email, phone: c.phone, mobile: c.mobile, linkedin: c.linkedin, preferredContact: c.preferred_contact, isDecisionMaker: c.is_decision_maker, isPrimary: c.is_primary, confidence: c.confidence, notes: c.notes, status: c.status, createdAt: c.created_at, updatedAt: c.updated_at };
}

// ── Activities ──

export async function listActivities(companyId: number, params: { page?: number; pageSize?: number; type?: string } = {}): Promise<ActivityList> {
  const q = new URLSearchParams({ company_id: String(companyId), page: String(params.page ?? 1), page_size: String(params.pageSize ?? 20) });
  if (params.type) q.set("activity_type", params.type);
  const r = await fetch(`${API_BASE_URL}/activities?${q}`, { cache: "no-store" });
  if (!r.ok) throw new ApiError(`Failed: ${r.status}`, r.status);
  const p = await r.json();
  return { items: p.items.map((a: Record<string, unknown>) => ({ id: a.id, companyId: a.company_id, contactId: a.contact_id, activityType: a.activity_type, subject: a.subject, body: a.body, dueDate: a.due_date, completedAt: a.completed_at, createdAt: a.created_at })), total: p.total, page: p.page, pageSize: p.page_size };
}

export async function createActivity(input: ActivityCreateInput): Promise<Activity> {
  const r = await fetch(`${API_BASE_URL}/activities`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(toSnakeKeys(input as unknown as Record<string, unknown>)) });
  if (!r.ok) throw new ApiError(`Failed: ${r.status}`, r.status);
  const a = await r.json();
  return { id: a.id, companyId: a.company_id, contactId: a.contact_id, activityType: a.activity_type, subject: a.subject, body: a.body, dueDate: a.due_date, completedAt: a.completed_at, createdAt: a.created_at };
}

// ── Tasks ──

export async function listTasks(companyId: number, params: { page?: number; pageSize?: number; status?: string; priority?: string } = {}): Promise<TaskList> {
  const q = new URLSearchParams({ company_id: String(companyId), page: String(params.page ?? 1), page_size: String(params.pageSize ?? 20) });
  if (params.status) q.set("status", params.status);
  if (params.priority) q.set("priority", params.priority);
  const r = await fetch(`${API_BASE_URL}/tasks?${q}`, { cache: "no-store" });
  if (!r.ok) throw new ApiError(`Failed: ${r.status}`, r.status);
  const p = await r.json();
  return { items: p.items.map((t: Record<string, unknown>) => ({ id: t.id, companyId: t.company_id, contactId: t.contact_id, title: t.title, description: t.description, priority: t.priority, status: t.status, dueDate: t.due_date, isCompleted: t.is_completed, createdAt: t.created_at })), total: p.total, page: p.page, pageSize: p.page_size };
}

export async function createTask(input: TaskCreateInput): Promise<Task> {
  const r = await fetch(`${API_BASE_URL}/tasks`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(input) });
  if (!r.ok) throw new ApiError(`Failed: ${r.status}`, r.status);
  const t = await r.json();
  return { id: t.id, companyId: t.company_id, contactId: t.contact_id, title: t.title, description: t.description, priority: t.priority, status: t.status, dueDate: t.due_date, isCompleted: t.is_completed, createdAt: t.created_at };
}

export async function updateTask(id: number, input: TaskUpdateInput): Promise<Task> {
  const r = await fetch(`${API_BASE_URL}/tasks/${id}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(input) });
  if (!r.ok) throw new ApiError(`Failed: ${r.status}`, r.status);
  const t = await r.json();
  return { id: t.id, companyId: t.company_id, contactId: t.contact_id, title: t.title, description: t.description, priority: t.priority, status: t.status, dueDate: t.due_date, isCompleted: t.is_completed, createdAt: t.created_at };
}

// ── Opportunities ──

export async function listOpportunities(companyId: number, params: { page?: number; pageSize?: number; stage?: string } = {}): Promise<OpportunityList> {
  const q = new URLSearchParams({ company_id: String(companyId), page: String(params.page ?? 1), page_size: String(params.pageSize ?? 20) });
  if (params.stage) q.set("stage", params.stage);
  const r = await fetch(`${API_BASE_URL}/opportunities?${q}`, { cache: "no-store" });
  if (!r.ok) throw new ApiError(`Failed: ${r.status}`, r.status);
  const p = await r.json();
  return { items: p.items.map((o: Record<string, unknown>) => ({ id: o.id, companyId: o.company_id, contactId: o.contact_id, title: o.title, estimatedValue: Number(o.estimated_value ?? 0), probability: o.probability, expectedCloseDate: o.expected_close_date, owner: o.owner, stage: o.stage, status: o.status, notes: o.notes, createdAt: o.created_at, updatedAt: o.updated_at })), total: p.total, page: p.page, pageSize: p.page_size };
}

export async function createOpportunity(input: OpportunityCreateInput): Promise<Opportunity> {
  const r = await fetch(`${API_BASE_URL}/opportunities`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(input) });
  if (!r.ok) throw new ApiError(`Failed: ${r.status}`, r.status);
  const o = await r.json();
  return { id: o.id, companyId: o.company_id, contactId: o.contact_id, title: o.title, estimatedValue: Number(o.estimated_value ?? 0), probability: o.probability, expectedCloseDate: o.expected_close_date, owner: o.owner, stage: o.stage, status: o.status, notes: o.notes, createdAt: o.created_at, updatedAt: o.updated_at };
}

export async function updateOpportunity(id: number, input: OpportunityUpdateInput): Promise<Opportunity> {
  const r = await fetch(`${API_BASE_URL}/opportunities/${id}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(input) });
  if (!r.ok) throw new ApiError(`Failed: ${r.status}`, r.status);
  const o = await r.json();
  return { id: o.id, companyId: o.company_id, contactId: o.contact_id, title: o.title, estimatedValue: Number(o.estimated_value ?? 0), probability: o.probability, expectedCloseDate: o.expected_close_date, owner: o.owner, stage: o.stage, status: o.status, notes: o.notes, createdAt: o.created_at, updatedAt: o.updated_at };
}

// ── Today Workspace ──

export async function fetchTodayWorkspace(): Promise<TodayWorkspace> {
  const r = await fetch(`${API_BASE_URL}/dashboard/today`, { cache: "no-store" });
  if (!r.ok) throw new ApiError(`Failed to load today workspace: ${r.status}`, r.status);
  const p = await r.json();
  return {
    assessmentLeads: (p.assessment_leads || []).map(mapTodayLead),
    missedCalls: (p.missed_calls || []).map(mapTodayMissedCall),
    inboundReplies: (p.inbound_replies || []).map(mapTodayReply),
    overdueFollowUps: (p.overdue_follow_ups || []).map(mapTodayTask),
    dueToday: (p.due_today || []).map(mapTodayTask),
    upcoming: (p.upcoming || []).map(mapTodayTask),
    leadsNoNextAction: (p.leads_no_next_action || []).map(mapTodayTask),
    generatedAt: p.generated_at,
  };
}

export async function executeFollowUp(taskId: number, request: FollowUpRequest): Promise<FollowUpResponse> {
  const endpoint = request.action === "assign_next_step"
    ? `${API_BASE_URL}/dashboard/leads/${taskId}/assign-next-step`
    : `${API_BASE_URL}/dashboard/tasks/${taskId}/follow-up`;
  const r = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      action: request.action,
      new_due_date: request.newDueDate,
      next_step_title: request.nextStepTitle,
      next_step_priority: request.nextStepPriority,
      next_step_due_date: request.nextStepDueDate,
      terminal_outcome: request.terminalOutcome,
      idempotency_key: request.idempotencyKey,
      notes: request.notes,
    }),
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({ detail: `Failed: ${r.status}` }));
    throw new ApiError(err.detail || `Failed: ${r.status}`, r.status);
  }
  const p = await r.json();
  return {
    taskId: p.task_id,
    action: p.action,
    activityId: p.activity_id,
    nextTaskId: p.next_task_id,
    message: p.message,
  };
}

export async function acknowledgeReply(emailId: number): Promise<{ id: number; status: string }> {
  const r = await fetch(`${API_BASE_URL}/dashboard/replies/${emailId}/acknowledge`, {
    method: "POST",
  });
  if (!r.ok) throw new ApiError(`Failed: ${r.status}`, r.status);
  return r.json();
}

function mapTodayLead(p: Record<string, unknown>): TodayLeadItem {
  return {
    id: p.id as number,
    leadId: p.lead_id as number,
    name: p.name as string,
    companyName: (p.company_name as string) || "",
    industry: p.industry as string | null,
    opportunityScore: p.opportunity_score as number,
    status: p.status as string,
    createdAt: p.created_at as string,
    ownerUserId: p.owner_user_id as string | null,
    reason: p.reason as string,
  };
}

function mapTodayMissedCall(p: Record<string, unknown>): TodayMissedCallItem {
  return {
    id: p.id as number,
    callUuid: p.call_uuid as string,
    callerNumber: p.caller_number as string,
    callerDisplay: p.caller_display as string,
    calledAt: p.called_at as string,
    spamScore: p.spam_score as number | null,
    companyId: p.company_id as number | null,
    companyName: p.company_name as string | null,
    contactId: p.contact_id as number | null,
    contactName: p.contact_name as string | null,
    reason: p.reason as string,
  };
}

function mapTodayReply(p: Record<string, unknown>): TodayReplyItem {
  return {
    id: p.id as number,
    emailUuid: p.email_uuid as string,
    fromAddress: p.from_address as string,
    subject: p.subject as string | null,
    receivedAt: p.received_at as string,
    companyId: p.company_id as number | null,
    companyName: p.company_name as string | null,
    contactId: p.contact_id as number | null,
    contactName: p.contact_name as string | null,
    reason: p.reason as string,
  };
}

function mapTodayTask(p: Record<string, unknown>): TodayTaskItem {
  return {
    id: p.id as number,
    leadId: p.lead_id as number | null,
    title: p.title as string,
    description: p.description as string | null,
    priority: p.priority as string,
    status: p.status as string,
    dueDate: p.due_date as string,
    isCompleted: p.is_completed as boolean,
    source: p.source as string | null,
    companyId: p.company_id as number | null,
    companyName: p.company_name as string | null,
    contactId: p.contact_id as number | null,
    contactName: p.contact_name as string | null,
    contactEmail: p.contact_email as string | null,
    contactPhone: p.contact_phone as string | null,
    ownerUserId: p.owner_user_id as string | null,
    reason: p.reason as string,
  };
}

import type {
  Activity, ActivityCreateInput, ActivityList,
  Contact, ContactCreateInput, ContactList, ContactUpdateInput,
  FollowUpRequest, FollowUpResponse,
  Opportunity, OpportunityCreateInput, OpportunityList, OpportunityUpdateInput,
  Task, TaskCreateInput, TaskList, TaskUpdateInput,
  TodayLeadItem, TodayMissedCallItem, TodayReplyItem, TodayTaskItem, TodayWorkspace,
} from "@/lib/types";
