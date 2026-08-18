"""Never Forget controlled MVP APIs."""

import hashlib
import json
import os
import secrets
from datetime import UTC, date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, HttpUrl, model_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.infrastructure.auth.clerk import AuthContext, require_permission
from app.infrastructure.db.never_forget import (
    NeverForgetCustomerAction,
    NeverForgetReminder,
    NeverForgetServiceRecord,
)
from app.infrastructure.db.session import get_db_session

router = APIRouter(prefix="/never-forget", tags=["never-forget"])


class ServiceRecordInput(BaseModel):
    contractor_name: str = Field(min_length=2, max_length=255)
    contractor_phone: str | None = Field(default=None, max_length=50)
    contractor_email: str | None = Field(default=None, max_length=255)
    customer_name: str = Field(min_length=2, max_length=255)
    customer_phone: str | None = Field(default=None, max_length=50)
    customer_email: str | None = Field(default=None, max_length=255)
    service_address: str | None = Field(default=None, max_length=500)
    job_title: str = Field(min_length=3, max_length=255)
    job_summary: str = Field(min_length=10, max_length=5000)
    completed_on: date
    invoice_reference: str | None = Field(default=None, max_length=120)
    receipt_url: HttpUrl | None = None
    work_photo_urls: list[HttpUrl] = Field(default_factory=list, max_length=10)
    warranty_summary: str | None = Field(default=None, max_length=3000)
    warranty_expires_on: date | None = None
    maintenance_instructions: str | None = Field(default=None, max_length=3000)
    next_service_on: date | None = None
    customer_consented_to_reminders: bool = False

    @model_validator(mode="after")
    def validate_dates(self):
        if self.warranty_expires_on and self.warranty_expires_on < self.completed_on:
            raise ValueError("Warranty expiry cannot be before the completed date")
        if self.next_service_on and self.next_service_on <= self.completed_on:
            raise ValueError("Next service date must be after the completed date")
        if self.customer_consented_to_reminders and not (
            self.customer_phone or self.customer_email
        ):
            raise ValueError("A phone number or email is required for reminders")
        urls = ([self.receipt_url] if self.receipt_url else []) + self.work_photo_urls
        if any(url.scheme != "https" for url in urls):
            raise ValueError("Receipt and photo links must use HTTPS")
        return self


class CustomerActionInput(BaseModel):
    action_type: str = Field(pattern="^(request_service|ask_question|stop_reminders)$")
    note: str | None = Field(default=None, max_length=1000)


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _record_payload(record: NeverForgetServiceRecord, *, public_token: str | None = None) -> dict:
    payload = {
        "id": record.id,
        "contractor_name": record.contractor_name,
        "contractor_phone": record.contractor_phone,
        "contractor_email": record.contractor_email,
        "customer_name": record.customer_name,
        "customer_phone": record.customer_phone,
        "customer_email": record.customer_email,
        "service_address": record.service_address,
        "job_title": record.job_title,
        "job_summary": record.job_summary,
        "completed_on": record.completed_on.isoformat(),
        "invoice_reference": record.invoice_reference,
        "receipt_url": record.receipt_url,
        "work_photo_urls": json.loads(record.work_photo_urls_json),
        "warranty_summary": record.warranty_summary,
        "warranty_expires_on": (
            record.warranty_expires_on.isoformat() if record.warranty_expires_on else None
        ),
        "maintenance_instructions": record.maintenance_instructions,
        "next_service_on": record.next_service_on.isoformat() if record.next_service_on else None,
        "customer_consented_to_reminders": record.customer_consented_to_reminders,
        "status": record.status,
        "created_at": record.created_at.isoformat(),
    }
    if public_token:
        payload["customer_record_url"] = (
            f"{os.getenv('MARKETING_SITE_URL', 'https://www.pacificnorthsystems.com').rstrip('/')}/service-record/{public_token}"
        )
    return payload


def _public_record(session: Session, token: str) -> NeverForgetServiceRecord:
    record = session.scalar(
        select(NeverForgetServiceRecord).where(
            NeverForgetServiceRecord.public_token_hash == _hash(token),
            NeverForgetServiceRecord.status == "active",
        )
    )
    if record is None:
        raise HTTPException(404, "This service record is unavailable")
    return record


@router.get("/summary")
def summary(
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    records = (
        session.scalar(
            select(func.count(NeverForgetServiceRecord.id)).where(
                NeverForgetServiceRecord.organization_id == ctx.organization_id
            )
        )
        or 0
    )
    reminders = (
        session.scalar(
            select(func.count(NeverForgetReminder.id)).where(
                NeverForgetReminder.organization_id == ctx.organization_id,
                NeverForgetReminder.status == "scheduled",
            )
        )
        or 0
    )
    requests = (
        session.scalar(
            select(func.count(NeverForgetCustomerAction.id)).where(
                NeverForgetCustomerAction.organization_id == ctx.organization_id,
                NeverForgetCustomerAction.status == "new",
            )
        )
        or 0
    )
    return {
        "records": records,
        "scheduled_reminders": reminders,
        "open_customer_requests": requests,
        "live_messages_enabled": os.getenv("NEVER_FORGET_LIVE_MESSAGES_ENABLED", "false").lower()
        == "true",
        "release_status": "controlled_mvp",
    }


@router.get("/records")
def list_records(
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    records = session.scalars(
        select(NeverForgetServiceRecord)
        .where(NeverForgetServiceRecord.organization_id == ctx.organization_id)
        .order_by(NeverForgetServiceRecord.created_at.desc())
    ).all()
    return {"items": [_record_payload(record) for record in records], "total": len(records)}


@router.get("/actions")
def list_actions(
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    rows = session.execute(
        select(NeverForgetCustomerAction, NeverForgetServiceRecord)
        .join(
            NeverForgetServiceRecord,
            NeverForgetServiceRecord.id == NeverForgetCustomerAction.service_record_id,
        )
        .where(NeverForgetCustomerAction.organization_id == ctx.organization_id)
        .order_by(NeverForgetCustomerAction.created_at.desc())
        .limit(100)
    ).all()
    return {
        "items": [
            {
                "id": action.id,
                "action_type": action.action_type,
                "note": action.note,
                "status": action.status,
                "created_at": action.created_at.isoformat(),
                "customer_name": record.customer_name,
                "job_title": record.job_title,
            }
            for action, record in rows
        ]
    }


@router.post("/records", status_code=201)
def create_record(
    payload: ServiceRecordInput,
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
):
    token = secrets.token_urlsafe(32)
    record = NeverForgetServiceRecord(
        organization_id=ctx.organization_id,
        public_token_hash=_hash(token),
        created_by=ctx.user_id,
        work_photo_urls_json=json.dumps([str(url) for url in payload.work_photo_urls]),
        receipt_url=str(payload.receipt_url) if payload.receipt_url else None,
        **payload.model_dump(exclude={"work_photo_urls", "receipt_url"}),
    )
    session.add(record)
    session.flush()
    if payload.customer_consented_to_reminders and payload.next_service_on:
        scheduled_for = datetime.combine(payload.next_service_on, time(hour=9), tzinfo=UTC)
        session.add(
            NeverForgetReminder(
                organization_id=ctx.organization_id,
                service_record_id=record.id,
                reminder_type="maintenance_due",
                channel="sms" if payload.customer_phone else "email",
                scheduled_for=scheduled_for,
                message=f"Hi {payload.customer_name}, {payload.contractor_name} recorded that {payload.job_title.lower()} may be due for service. Reply to arrange a visit or ask a question.",
            )
        )
    session.commit()
    session.refresh(record)
    return _record_payload(record, public_token=token)


@router.get("/public/{token}")
def get_public_record(token: str, session: Session = Depends(get_db_session)):
    record = _public_record(session, token)
    payload = _record_payload(record)
    for field in ("customer_phone", "customer_email"):
        payload.pop(field, None)
    return payload


@router.post("/public/{token}/actions", status_code=202)
def create_customer_action(
    token: str, payload: CustomerActionInput, session: Session = Depends(get_db_session)
):
    record = _public_record(session, token)
    recent_actions = (
        session.scalar(
            select(func.count(NeverForgetCustomerAction.id)).where(
                NeverForgetCustomerAction.service_record_id == record.id,
                NeverForgetCustomerAction.created_at >= datetime.now(UTC) - timedelta(hours=1),
            )
        )
        or 0
    )
    if recent_actions >= 5:
        raise HTTPException(429, "Too many requests. Please contact the contractor directly.")
    if payload.action_type == "stop_reminders":
        record.customer_consented_to_reminders = False
        reminders = session.scalars(
            select(NeverForgetReminder).where(
                NeverForgetReminder.service_record_id == record.id,
                NeverForgetReminder.status == "scheduled",
            )
        ).all()
        for reminder in reminders:
            reminder.status = "cancelled"
    session.add(
        NeverForgetCustomerAction(
            organization_id=record.organization_id,
            service_record_id=record.id,
            action_type=payload.action_type,
            note=payload.note,
        )
    )
    session.commit()
    return {"status": "received", "message": "Your contractor will see this request."}
