from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CompanyBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    industry: str | None = None
    website: str | None = None
    phone: str | None = None  # deprecated — use primary contact
    email: str | None = None  # deprecated — use primary contact
    address: str | None = None
    employees: int | None = Field(default=None, ge=0)
    revenue: Decimal | None = Field(default=None, ge=0)
    status: str = "active"
    tags: str | None = None
    owner: str | None = None
    notes: str | None = None
    primary_contact_id: int | None = None


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    industry: str | None = None
    website: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    employees: int | None = Field(default=None, ge=0)
    revenue: Decimal | None = Field(default=None, ge=0)
    status: str | None = None
    tags: str | None = None
    owner: str | None = None
    notes: str | None = None
    primary_contact_id: int | None = None


class CompanyRead(CompanyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_archived: bool
    created_at: datetime
    updated_at: datetime


class CompanyListResponse(BaseModel):
    items: list[CompanyRead]
    total: int
    page: int
    page_size: int
