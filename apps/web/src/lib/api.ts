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
  return { items: p.items.map((c: Record<string, unknown>) => ({ id: c.id, companyId: c.company_id, firstName: c.first_name, lastName: c.last_name, jobTitle: c.job_title, department: c.department, email: c.email, phone: c.phone, mobile: c.mobile, linkedin: c.linkedin, preferredContact: c.preferred_contact, isDecisionMaker: c.is_decision_maker, isPrimary: c.is_primary, confidence: c.confidence, notes: c.notes, status: c.status, createdAt: c.created_at, updatedAt: c.updated_at })), total: p.total, page: p.page, pageSize: p.page_size };
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
  const r = await fetch(`${API_BASE_URL}/activities`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(input) });
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

import type { Activity, ActivityCreateInput, ActivityList, Contact, ContactCreateInput, ContactList, ContactUpdateInput, Opportunity, OpportunityCreateInput, OpportunityList, OpportunityUpdateInput, Task, TaskCreateInput, TaskList, TaskUpdateInput } from "@/lib/types";
