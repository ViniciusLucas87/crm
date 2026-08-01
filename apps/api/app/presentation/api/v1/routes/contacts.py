"""
Contacts API — CRUD for company contacts.

GET  /contacts?company_id=X          — list contacts for a company
POST /contacts                       — create contact
GET  /contacts/{id}                  — get contact
PATCH /contacts/{id}                 — update contact
DELETE /contacts/{id}                — archive contact
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.infrastructure.auth.clerk import AuthContext, require_permission
from app.infrastructure.db.models import Contact, Company
from app.infrastructure.db.session import get_db_session
from sqlalchemy import select, func
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter()


class ContactCreate(BaseModel):
    company_id: int
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
    notes: str | None = None


class ContactUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    job_title: str | None = None
    department: str | None = None
    email: str | None = None
    phone: str | None = None
    mobile: str | None = None
    linkedin: str | None = None
    preferred_contact: str | None = None
    is_decision_maker: bool | None = None
    is_primary: bool | None = None
    notes: str | None = None


def _serialize_contact(c: Contact) -> dict:
    return {
        "id": c.id,
        "companyId": c.company_id,
        "firstName": c.first_name,
        "lastName": c.last_name,
        "jobTitle": c.job_title,
        "department": c.department,
        "email": c.email,
        "phone": c.phone,
        "mobile": c.mobile,
        "linkedin": c.linkedin,
        "preferredContact": c.preferred_contact,
        "isDecisionMaker": c.is_decision_maker,
        "isPrimary": c.is_primary,
        "notes": c.notes,
        "status": c.status,
        "createdAt": c.created_at.isoformat() if c.created_at else "",
        "updatedAt": c.updated_at.isoformat() if c.updated_at else "",
    }


@router.get("/contacts")
def list_contacts(
    company_id: int = Query(..., description="Company ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    company = session.get(Company, company_id)
    if not company or company.organization_id != ctx.organization_id:
        raise HTTPException(404, "Company not found")

    total = session.execute(
        select(func.count()).select_from(Contact).where(
            Contact.company_id == company_id,
            Contact.organization_id == ctx.organization_id,
        )
    ).scalar() or 0

    contacts = session.execute(
        select(Contact)
        .where(Contact.company_id == company_id, Contact.organization_id == ctx.organization_id)
        .order_by(Contact.is_primary.desc(), Contact.last_name.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).scalars().all()

    return {
        "items": [_serialize_contact(c) for c in contacts],
        "total": total,
        "page": page,
        "pageSize": page_size,
    }


@router.post("/contacts")
def create_contact(
    payload: ContactCreate,
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
):
    company = session.get(Company, payload.company_id)
    if not company or company.organization_id != ctx.organization_id:
        raise HTTPException(404, "Company not found")

    # If marking as primary, unset any existing primary
    if payload.is_primary:
        session.execute(
            select(Contact).where(
                Contact.company_id == payload.company_id,
                Contact.is_primary == True,
            )
        )
        existing_primary = session.execute(
            select(Contact).where(
                Contact.company_id == payload.company_id,
                Contact.is_primary == True,
            )
        ).scalars().all()
        for c in existing_primary:
            c.is_primary = False

    contact = Contact(
        organization_id=ctx.organization_id,
        company_id=payload.company_id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        job_title=payload.job_title,
        department=payload.department,
        email=payload.email,
        phone=payload.phone,
        mobile=payload.mobile,
        linkedin=payload.linkedin,
        preferred_contact=payload.preferred_contact,
        is_decision_maker=payload.is_decision_maker,
        is_primary=payload.is_primary,
        notes=payload.notes,
    )
    session.add(contact)
    session.commit()
    session.refresh(contact)
    from app.application.events.bridge import emit
    from app.application.workers.events import EventType
    emit(session, EventType.CONTACT_CREATED, "contact", contact.id, {"company_id": payload.company_id})
    return _serialize_contact(contact)


@router.get("/contacts/{contact_id}")
def get_contact(
    contact_id: int,
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    contact = session.get(Contact, contact_id)
    if not contact or contact.organization_id != ctx.organization_id:
        raise HTTPException(404, "Contact not found")
    return _serialize_contact(contact)


@router.patch("/contacts/{contact_id}")
def update_contact(
    contact_id: int,
    payload: ContactUpdate,
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
):
    contact = session.get(Contact, contact_id)
    if not contact or contact.organization_id != ctx.organization_id:
        raise HTTPException(404, "Contact not found")

    if payload.is_primary:
        existing = session.execute(
            select(Contact).where(
                Contact.company_id == contact.company_id,
                Contact.is_primary == True,
                Contact.id != contact_id,
            )
        ).scalars().all()
        for c in existing:
            c.is_primary = False

    for field in ("first_name", "last_name", "job_title", "department", "email",
                   "phone", "mobile", "linkedin", "preferred_contact",
                   "is_decision_maker", "is_primary", "notes"):
        val = getattr(payload, field, None)
        if val is not None:
            setattr(contact, field, val)

    session.commit()
    session.refresh(contact)
    from app.application.events.bridge import emit
    from app.application.workers.events import EventType
    emit(session, EventType.CONTACT_UPDATED, "contact", contact_id)
    return _serialize_contact(contact)


@router.delete("/contacts/{contact_id}")
def archive_contact(
    contact_id: int,
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
):
    contact = session.get(Contact, contact_id)
    if not contact or contact.organization_id != ctx.organization_id:
        raise HTTPException(404, "Contact not found")
    contact.status = "archived"
    session.commit()
    return {"status": "ok"}
