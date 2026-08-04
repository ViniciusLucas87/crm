export type DashboardSummary = {
  tasksToday: number;
  companies: number;
  activeOpportunities: number;
  meetings: number;
  pipelineValue: number;
  wonDeals: number;
  revenueForecast: number;
  activitiesDueToday: number;
};

export type Company = {
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
  primaryContactId: number | null;
  isArchived: boolean;
  createdAt: string;
  updatedAt: string;
};

export type CompanyList = {
  items: Company[];
  total: number;
  page: number;
  pageSize: number;
};

export type CompanyCreateInput = {
  name: string;
  industry?: string;
  website?: string;
  phone?: string;
  email?: string;
  address?: string;
  employees?: number;
  revenue?: number;
  status?: string;
  tags?: string;
  owner?: string;
  notes?: string;
};

export type CompanyUpdateInput = Partial<CompanyCreateInput>;

// ── Contact ──

export type Contact = {
  id: number;
  companyId: number;
  firstName: string;
  lastName: string;
  jobTitle: string | null;
  department: string | null;
  email: string | null;
  phone: string | null;
  mobile: string | null;
  linkedin: string | null;
  preferredContact: string | null;
  isDecisionMaker: boolean;
  isPrimary: boolean;
  confidence: string;
  notes: string | null;
  status: string;
  createdAt: string;
  updatedAt: string;
};

export type ContactCreateInput = {
  companyId: number;
  firstName: string;
  lastName: string;
  jobTitle?: string;
  email?: string;
  phone?: string;
  mobile?: string;
  linkedin?: string;
  preferredContact?: string;
  isDecisionMaker?: boolean;
  notes?: string;
};

export type ContactUpdateInput = Partial<ContactCreateInput>;

export type ContactList = { items: Contact[]; total: number; page: number; pageSize: number };

// ── Activity ──

export type Activity = {
  id: number;
  companyId: number;
  contactId: number | null;
  activityType: string;
  subject: string | null;
  body: string | null;
  dueDate: string | null;
  completedAt: string | null;
  createdAt: string;
};

export type ActivityCreateInput = {
  companyId: number;
  contactId?: number;
  activityType: string;
  subject?: string;
  body?: string;
  dueDate?: string;
};

export type ActivityUpdateInput = Partial<Omit<ActivityCreateInput, "companyId">>;

export type ActivityList = { items: Activity[]; total: number; page: number; pageSize: number };

// ── Task ──

export type Task = {
  id: number;
  companyId: number | null;
  contactId: number | null;
  title: string;
  description: string | null;
  priority: string;
  status: string;
  dueDate: string | null;
  isCompleted: boolean;
  createdAt: string;
};

export type TaskCreateInput = {
  companyId: number;
  contactId?: number;
  title: string;
  description?: string;
  priority?: string;
  dueDate: string;
};

export type TaskUpdateInput = Partial<Omit<TaskCreateInput, "companyId"> & { status: string; isCompleted: boolean }>;

export type TaskList = { items: Task[]; total: number; page: number; pageSize: number };

// ── Opportunity ──

export type Opportunity = {
  id: number;
  companyId: number;
  contactId: number | null;
  title: string;
  estimatedValue: number;
  probability: number;
  expectedCloseDate: string | null;
  owner: string | null;
  stage: string;
  status: string;
  notes: string | null;
  createdAt: string;
  updatedAt: string | null;
};

export type OpportunityCreateInput = {
  companyId: number;
  contactId?: number;
  title: string;
  estimatedValue?: number;
  probability?: number;
  expectedCloseDate?: string;
  owner?: string;
  stage?: string;
  notes?: string;
};

export type OpportunityUpdateInput = Partial<OpportunityCreateInput>;

export type OpportunityList = { items: Opportunity[]; total: number; page: number; pageSize: number };

// ── Today Workspace ──

export type TodayLeadItem = {
  id: number;
  leadId: number;
  name: string;
  companyName: string;
  industry: string | null;
  opportunityScore: number;
  status: string;
  createdAt: string;
  ownerUserId: string | null;
  reason: string;
};

export type TodayMissedCallItem = {
  id: number;
  callUuid: string;
  callerNumber: string;
  callerDisplay: string;
  calledAt: string;
  spamScore: number | null;
  companyId: number | null;
  companyName: string | null;
  contactId: number | null;
  contactName: string | null;
  reason: string;
};

export type TodayReplyItem = {
  id: number;
  emailUuid: string;
  fromAddress: string;
  subject: string | null;
  receivedAt: string;
  companyId: number | null;
  companyName: string | null;
  contactId: number | null;
  contactName: string | null;
  reason: string;
};

export type TodayTaskItem = {
  id: number;
  leadId: number | null;
  title: string;
  description: string | null;
  priority: string;
  status: string;
  dueDate: string;
  isCompleted: boolean;
  source: string | null;
  companyId: number | null;
  companyName: string | null;
  contactId: number | null;
  contactName: string | null;
  contactEmail: string | null;
  contactPhone: string | null;
  ownerUserId: string | null;
  reason: string;
};

export type TodayWorkspace = {
  assessmentLeads: TodayLeadItem[];
  missedCalls: TodayMissedCallItem[];
  inboundReplies: TodayReplyItem[];
  overdueFollowUps: TodayTaskItem[];
  dueToday: TodayTaskItem[];
  upcoming: TodayTaskItem[];
  leadsNoNextAction: TodayTaskItem[];
  generatedAt: string;
};

export type FollowUpRequest = {
  action: "complete" | "reschedule" | "assign_next_step";
  idempotencyKey?: string;
  newDueDate?: string;
  nextStepTitle?: string;
  nextStepPriority?: string;
  nextStepDueDate?: string;
  terminalOutcome?: string;
  notes?: string;
};

export type FollowUpResponse = {
  taskId: number;
  action: string;
  activityId: number | null;
  nextTaskId: number | null;
  message: string;
};
