"""
MCP Context Builders.

Assemble structured, typed context from CRM data before
the LLM receives it. The LLM never accesses the database directly.

All builders return Pydantic models — no raw SQL, no ORM leakage.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


# ── Company Context ──

class CompanyContext(BaseModel):
    id: int
    name: str
    industry: str | None
    website: str | None
    phone: str | None
    email: str | None
    employees: int | None
    city: str | None
    province: str | None
    country: str | None
    status: str
    opportunity_score: int | None
    confidence_score: int | None
    buying_signals: str | None
    research_status: str | None
    tech_stack: str | None
    description: str | None
    linkedin_url: str | None
    contacts: list["ContactSummary"]
    activities_recent: list["ActivitySummary"]
    opportunities_open: list["OpportunitySummary"]
    tasks_pending: list["TaskSummary"]

    @classmethod
    def from_company(cls, c: Any, contacts: list[Any], activities: list[Any], opps: list[Any], tasks: list[Any]) -> "CompanyContext":
        return cls(
            id=c.id, name=c.name, industry=c.industry, website=c.website,
            phone=c.phone, email=c.email, employees=c.employees,
            city=c.city, province=c.province, country=c.country, status=c.status,
            opportunity_score=c.opportunity_score, confidence_score=c.confidence_score,
            buying_signals=c.buying_signals, research_status=c.research_status,
            tech_stack=c.tech_stack, description=c.description, linkedin_url=c.linkedin_url,
            contacts=[ContactSummary.from_contact(ct) for ct in contacts],
            activities_recent=[ActivitySummary.from_activity(a) for a in activities],
            opportunities_open=[OpportunitySummary.from_opportunity(o) for o in opps],
            tasks_pending=[TaskSummary.from_task(t) for t in tasks],
        )


class ContactSummary(BaseModel):
    id: int
    first_name: str
    last_name: str
    title: str | None
    email: str | None
    phone: str | None

    @classmethod
    def from_contact(cls, c: Any) -> "ContactSummary":
        return cls(id=c.id, first_name=c.first_name, last_name=c.last_name, title=c.job_title, email=c.email, phone=c.phone)


class ActivitySummary(BaseModel):
    id: int
    type: str
    subject: str | None
    body: str | None
    created_at: datetime

    @classmethod
    def from_activity(cls, a: Any) -> "ActivitySummary":
        return cls(id=a.id, type=a.type, subject=a.subject, body=a.body, created_at=a.created_at)


class OpportunitySummary(BaseModel):
    id: int
    title: str | None
    stage: str
    estimated_value: float | None
    probability: float | None
    expected_close_date: str | None

    @classmethod
    def from_opportunity(cls, o: Any) -> "OpportunitySummary":
        return cls(
            id=o.id, title=o.title, stage=o.stage,
            estimated_value=float(o.estimated_value) if o.estimated_value else None,
            probability=float(o.probability) if o.probability else None,
            expected_close_date=str(o.expected_close_date) if o.expected_close_date else None,
        )


class TaskSummary(BaseModel):
    id: int
    title: str | None
    description: str | None
    priority: str | None
    status: str
    due_date: str | None

    @classmethod
    def from_task(cls, t: Any) -> "TaskSummary":
        return cls(
            id=t.id, title=t.title, description=t.description,
            priority=t.priority, status=t.status,
            due_date=str(t.due_date) if t.due_date else None,
        )


# ── Meeting Context ──

class MeetingContext(BaseModel):
    company: CompanyContext
    recent_timeline: list[ActivitySummary]
    buying_signals_parsed: list[str]
    recommended_goals: list[str]
    suggested_questions: list[str]
    likely_objections: list[dict[str, str]]
    talking_points: list[str]
    cross_selling_ideas: list[str]
    upselling_ideas: list[str]
    checklist: list[str]


# ── Proposal Context ──

class ProposalContext(BaseModel):
    company: CompanyContext
    opportunity_score: int | None
    confidence_score: int | None
    recommended_services: list[str]
    estimated_value: dict[str, Any]
    industry_insights: str
    key_contacts: list[ContactSummary]
    recent_engagement: list[ActivitySummary]


# ── Timeline Context ──

class TimelineContext(BaseModel):
    company_id: int
    company_name: str
    events: list[dict[str, Any]]
    event_count: int
    date_range_start: str | None
    date_range_end: str | None


# ── Sales Context ──

class SalesContext(BaseModel):
    organization_id: int
    total_companies: int
    total_opportunities: int
    pipeline_value: float
    won_value: float
    top_opportunities: list[OpportunitySummary]
    companies_needing_attention: list[CompanyContext]
    overdue_tasks: list[TaskSummary]
    upcoming_meetings: list[ActivitySummary]
    daily_brief_summary: str


# ── Research Context ──

class ResearchContext(BaseModel):
    company: CompanyContext
    research_status: str | None
    research_date: str | None
    data_completeness: dict[str, bool]
    missing_fields: list[str]
    suggested_sources: list[str]
