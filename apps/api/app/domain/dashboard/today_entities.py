"""Today workspace request/response schemas."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class TodayLeadItem(BaseModel):
    id: int
    lead_id: int
    name: str
    company_name: str = ""
    industry: Optional[str] = None
    opportunity_score: int = 0
    status: str
    created_at: datetime
    owner_user_id: Optional[str] = None
    reason: str


class TodayMissedCallItem(BaseModel):
    id: int
    call_uuid: str
    caller_number: str = ""
    caller_display: str = ""
    called_at: datetime
    spam_score: Optional[int] = None
    company_id: Optional[int] = None
    company_name: Optional[str] = None
    contact_id: Optional[int] = None
    contact_name: Optional[str] = None
    reason: str


class TodayReplyItem(BaseModel):
    id: int
    email_uuid: str = ""
    from_address: str = ""
    subject: Optional[str] = None
    received_at: datetime
    company_id: Optional[int] = None
    company_name: Optional[str] = None
    contact_id: Optional[int] = None
    contact_name: Optional[str] = None
    reason: str


class TodayTaskItem(BaseModel):
    id: int
    lead_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    status: str = "open"
    due_date: date
    is_completed: bool = False
    source: Optional[str] = None
    company_id: Optional[int] = None
    company_name: Optional[str] = None
    contact_id: Optional[int] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    owner_user_id: Optional[str] = None
    reason: str


class TodayWorkspaceResponse(BaseModel):
    assessment_leads: list[TodayLeadItem] = Field(default_factory=list)
    missed_calls: list[TodayMissedCallItem] = Field(default_factory=list)
    inbound_replies: list[TodayReplyItem] = Field(default_factory=list)
    overdue_follow_ups: list[TodayTaskItem] = Field(default_factory=list)
    due_today: list[TodayTaskItem] = Field(default_factory=list)
    upcoming: list[TodayTaskItem] = Field(default_factory=list)
    leads_no_next_action: list[TodayTaskItem] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.now)


class FollowUpRequest(BaseModel):
    action: str = Field(..., pattern="^(complete|reschedule|assign_next_step)$")
    new_due_date: Optional[date] = None
    next_step_title: Optional[str] = None
    next_step_priority: Optional[str] = "medium"
    next_step_due_date: Optional[date] = None
    terminal_outcome: Optional[str] = None
    idempotency_key: Optional[str] = None
    notes: Optional[str] = None


class FollowUpResponse(BaseModel):
    task_id: int
    action: str
    activity_id: Optional[int] = None
    next_task_id: Optional[int] = None
    message: str = ""
