from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# ── Contact ──

class ContactBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=120)
    last_name: str = Field(min_length=1, max_length=120)
    job_title: str | None = None
    department: str | None = None
    email: str | None = None
    phone: str | None = None
    mobile: str | None = None
    linkedin: str | None = None
    preferred_contact: str | None = None
    is_decision_maker: bool = False
    is_primary: bool = False
    confidence: str = "manual"
    discovery_source: str | None = None
    notes: str | None = None
    status: str = "active"


class ContactCreate(ContactBase):
    company_id: int


class ContactUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=120)
    last_name: str | None = Field(default=None, min_length=1, max_length=120)
    job_title: str | None = None
    department: str | None = None
    email: str | None = None
    phone: str | None = None
    mobile: str | None = None
    linkedin: str | None = None
    preferred_contact: str | None = None
    is_decision_maker: bool | None = None
    is_primary: bool | None = None
    confidence: str | None = None
    discovery_source: str | None = None
    notes: str | None = None
    status: str | None = None


class ContactRead(ContactBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int
    created_at: datetime
    updated_at: datetime


class ContactListResponse(BaseModel):
    items: list[ContactRead]
    total: int
    page: int
    page_size: int


# ── Activity ──

class ActivityBase(BaseModel):
    activity_type: str = Field(min_length=1, max_length=20)
    subject: str | None = None
    body: str | None = None
    due_date: date | None = None
    completed_at: datetime | None = None


class ActivityCreate(ActivityBase):
    company_id: int
    contact_id: int | None = None


class ActivityUpdate(BaseModel):
    activity_type: str | None = None
    subject: str | None = None
    body: str | None = None
    due_date: date | None = None
    completed_at: datetime | None = None


class ActivityRead(ActivityBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int
    contact_id: int | None
    created_at: datetime


class ActivityListResponse(BaseModel):
    items: list[ActivityRead]
    total: int
    page: int
    page_size: int


# ── Task ──

class TaskBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    priority: str = "medium"
    status: str = "open"
    due_date: date
    is_completed: bool = False


class TaskCreate(TaskBase):
    company_id: int
    contact_id: int | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1)
    description: str | None = None
    priority: str | None = None
    status: str | None = None
    due_date: date | None = None
    is_completed: bool | None = None


class TaskRead(TaskBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int | None
    contact_id: int | None
    created_at: datetime


class TaskListResponse(BaseModel):
    items: list[TaskRead]
    total: int
    page: int
    page_size: int


# ── Opportunity ──

class OpportunityBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    estimated_value: Decimal = Field(default=0, ge=0)
    probability: int = Field(default=50, ge=0, le=100)
    expected_close_date: date | None = None
    owner: str | None = None
    stage: str = "lead"
    status: str = "active"
    notes: str | None = None


class OpportunityCreate(OpportunityBase):
    company_id: int
    contact_id: int | None = None


class OpportunityUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1)
    estimated_value: Decimal | None = Field(default=None, ge=0)
    probability: int | None = Field(default=None, ge=0, le=100)
    expected_close_date: date | None = None
    owner: str | None = None
    stage: str | None = None
    status: str | None = None
    notes: str | None = None


class OpportunityRead(OpportunityBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int
    contact_id: int | None
    created_at: datetime
    updated_at: datetime | None


class OpportunityListResponse(BaseModel):
    items: list[OpportunityRead]
    total: int
    page: int
    page_size: int
