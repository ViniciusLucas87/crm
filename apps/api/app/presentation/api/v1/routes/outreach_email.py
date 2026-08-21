"""Audited, rate-limited outbound email queue for approved PNS outreach."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.auth.clerk import AuthContext, require_permission
from app.infrastructure.db.models import EmailMessage, OutboxEvent
from app.infrastructure.db.session import get_db_session

router = APIRouter(prefix="/outreach-email", tags=["outreach-email"])

OUTREACH_EVENT = "outreach.email.requested"
MAX_DAILY_OUTREACH_EMAILS = 10


class OutreachEmailInput(BaseModel):
    contact_email: str = Field(min_length=5, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    contact_name: str = Field(min_length=1, max_length=255)
    subject: str = Field(min_length=3, max_length=180)
    body_text: str = Field(min_length=40, max_length=6000)
    source_platform: str = Field(min_length=2, max_length=30)
    source_url: str = Field(min_length=12, max_length=2000, pattern=r"^https://")
    public_evidence: str = Field(min_length=12, max_length=3000)
    email_source: str = Field(min_length=8, max_length=2000)
    lead_id: int | None = Field(default=None, ge=1)


def _sender_configured() -> bool:
    import os

    # The worker owns Zoho SMTP credentials. The API receives only this
    # non-secret readiness flag, so a web process never needs mail secrets.
    enabled = os.getenv("OUTREACH_EMAIL_ENABLED", "").strip().lower()
    return enabled in {"1", "true", "yes"} or bool(
        os.getenv("SMTP_USER") and os.getenv("SMTP_PASS") and os.getenv("SMTP_FROM_EMAIL")
    )


@router.get("/sender-status")
def sender_status(ctx: AuthContext = Depends(require_permission("companies:read"))):
    """Expose readiness only; credentials remain in the deployment environment."""
    return {
        "configured": _sender_configured(),
        "provider": "zoho_smtp" if _sender_configured() else None,
        "daily_cap": MAX_DAILY_OUTREACH_EMAILS,
        "duplicate_guard_days": 60,
        "mode": "queued_and_audited",
    }


@router.post("/send", status_code=202)
def queue_outreach_email(
    payload: OutreachEmailInput,
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
):
    """Queue one evidence-backed business email. Delivery is performed by the worker."""
    if not _sender_configured():
        raise HTTPException(503, "The authorized Zoho sender is not configured")
    if "opt out" not in payload.body_text.lower() and "unsubscribe" not in payload.body_text.lower():
        raise HTTPException(422, "Outreach email must include a clear opt-out")

    address = payload.contact_email.strip().lower()
    now = datetime.now(UTC)
    duplicate_cutoff = now - timedelta(days=60)
    prior = session.execute(
        select(EmailMessage.id).where(
            EmailMessage.organization_id == ctx.organization_id,
            EmailMessage.direction == "outbound",
            EmailMessage.to_address == address,
            EmailMessage.sent_at.is_not(None),
            EmailMessage.sent_at >= duplicate_cutoff,
        ).limit(1)
    ).scalar_one_or_none()
    if prior:
        raise HTTPException(409, "This address was contacted in the last 60 days")

    queued_duplicate = session.execute(
        select(OutboxEvent.id).where(
            OutboxEvent.event_type == OUTREACH_EVENT,
            OutboxEvent.created_at >= duplicate_cutoff,
            OutboxEvent.payload_json["organization_id"].as_integer() == ctx.organization_id,
            OutboxEvent.payload_json["contact_email"].as_string() == address,
        ).limit(1)
    ).scalar_one_or_none()
    if queued_duplicate:
        raise HTTPException(409, "This address is already queued in the 60-day outreach window")

    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    delivered_today = session.execute(
        select(EmailMessage.id).where(
            EmailMessage.organization_id == ctx.organization_id,
            EmailMessage.direction == "outbound",
            EmailMessage.sent_at >= day_start,
        )
    ).all()
    queued_today = session.execute(
        select(OutboxEvent.id).where(
            OutboxEvent.event_type == OUTREACH_EVENT,
            OutboxEvent.created_at >= day_start,
            OutboxEvent.payload_json["organization_id"].as_integer() == ctx.organization_id,
        )
    ).all()
    if len(delivered_today) + len(queued_today) >= MAX_DAILY_OUTREACH_EMAILS:
        raise HTTPException(429, "Daily outreach sending cap reached")

    digest = hashlib.sha256(f"{ctx.organization_id}:{address}:{now.date().isoformat()}".encode()).hexdigest()
    event = OutboxEvent(
        event_type=OUTREACH_EVENT,
        payload_json={
            "organization_id": ctx.organization_id,
            "contact_email": address,
            "contact_name": payload.contact_name.strip(),
            "subject": payload.subject.strip(),
            "body_text": payload.body_text.strip(),
            "source_platform": payload.source_platform.strip().lower(),
            "source_url": payload.source_url,
            "public_evidence": payload.public_evidence.strip(),
            "email_source": payload.email_source.strip(),
            "lead_id": payload.lead_id,
            "owner_user_id": ctx.user_id,
        },
        correlation_id=digest[:64],
        idempotency_key=f"outreach-{digest}",
    )
    session.add(event)
    session.commit()
    return {"status": "queued", "event_id": event.id, "duplicate_guard_until": (now + timedelta(days=60)).date().isoformat()}
