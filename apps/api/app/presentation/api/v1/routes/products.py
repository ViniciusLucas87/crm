"""Never Miss product APIs, including the Never Miss Plus lead inbox."""

import hashlib
import secrets
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.infrastructure.auth.clerk import AuthContext, require_permission
from app.infrastructure.db.models import Call, LeadCaptureRecord, ProductConfiguration, ProductSubscription, Task
from app.infrastructure.db.session import get_db_session

router = APIRouter(prefix="/products")
PRODUCT_CODES = {"never_miss"}


class ProductConfigurationInput(BaseModel):
    enabled: bool = False
    plan: str = Field(default="never_miss", pattern="^(never_miss|never_miss_plus)$")
    business_name: str | None = Field(default=None, max_length=255)
    business_phone: str | None = Field(default=None, max_length=50)
    notification_phone: str | None = Field(default=None, max_length=50)
    recovery_message: str | None = Field(default=None, max_length=1000)
    business_hours_json: dict | None = None
    monthly_call_limit: int = Field(default=50, ge=1, le=100000)
    monthly_message_limit: int = Field(default=100, ge=1, le=100000)


class CustomerInquiryInput(BaseModel):
    source: str = Field(default="manual", pattern="^(manual|website|form|assessment|phone|sms|referral)$")
    external_id: str | None = Field(default=None, max_length=128)
    name: str | None = Field(default=None, max_length=255)
    company_name: str | None = Field(default=None, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    summary: str | None = Field(default=None, max_length=4000)
    priority: str = Field(default="normal", pattern="^(low|normal|high|urgent)$")
    metadata_json: dict | None = None


class CustomerInquiryUpdate(BaseModel):
    status: str | None = Field(default=None, pattern="^(new|contacted|qualified|booked|won|lost|archived)$")
    priority: str | None = Field(default=None, pattern="^(low|normal|high|urgent)$")
    owner_user_id: str | None = Field(default=None, max_length=255)
    next_action: str | None = Field(default=None, max_length=255)
    next_action_at: datetime | None = None


def _configuration(session: Session, organization_id: int, product_code: str) -> ProductConfiguration:
    if product_code not in PRODUCT_CODES:
        raise HTTPException(404, "Product not found")
    config = session.execute(
        select(ProductConfiguration).where(
            ProductConfiguration.organization_id == organization_id,
            ProductConfiguration.product_code == product_code,
        )
    ).scalar_one_or_none()
    if config is None:
        config = ProductConfiguration(organization_id=organization_id, product_code=product_code)
        session.add(config)
        session.commit()
        session.refresh(config)
    return config


def _config_payload(config: ProductConfiguration) -> dict:
    return {
        "product_code": config.product_code,
        "enabled": config.enabled,
        "plan": config.plan,
        "business_name": config.business_name,
        "business_phone": config.business_phone,
        "notification_phone": config.notification_phone,
        "recovery_message": config.recovery_message,
        "business_hours_json": config.business_hours_json or {},
        "monthly_call_limit": config.monthly_call_limit,
        "monthly_message_limit": config.monthly_message_limit,
        "intake_key_configured": bool(config.intake_key_hash),
        "updated_at": config.updated_at.isoformat(),
    }


def _lead_payload(record: LeadCaptureRecord) -> dict:
    return {
        "id": record.id,
        "source": record.source,
        "external_id": record.external_id,
        "name": record.name,
        "company_name": record.company_name,
        "email": record.email,
        "phone": record.phone,
        "summary": record.summary,
        "status": record.status,
        "priority": record.priority,
        "owner_user_id": record.owner_user_id,
        "next_action": record.next_action,
        "next_action_at": record.next_action_at.isoformat() if record.next_action_at else None,
        "created_at": record.created_at.isoformat(),
        "updated_at": record.updated_at.isoformat(),
    }


@router.get("/{product_code}/configuration")
def get_product_configuration(
    product_code: str,
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    return _config_payload(_configuration(session, ctx.organization_id, product_code))


@router.put("/{product_code}/configuration")
def update_product_configuration(
    product_code: str,
    payload: ProductConfigurationInput,
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
):
    config = _configuration(session, ctx.organization_id, product_code)
    for key, value in payload.model_dump().items():
        setattr(config, key, value)
    session.commit()
    session.refresh(config)
    return _config_payload(config)


# Old lead_capture paths remain private aliases so existing integrations keep working.
@router.post("/never_miss_plus/intake-key")
@router.post("/lead_capture/intake-key", include_in_schema=False)
def rotate_intake_key(
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
):
    config = _configuration(session, ctx.organization_id, "never_miss")
    token = f"pns_intake_{secrets.token_urlsafe(32)}"
    config.intake_key_hash = hashlib.sha256(token.encode()).hexdigest()
    session.commit()
    return {"intake_key": token, "message": "Store this key securely. It will not be shown again."}


@router.get("/never_miss/summary")
def never_miss_summary(
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    calls = session.execute(select(Call).where(Call.organization_id == ctx.organization_id)).scalars().all()
    missed = [call for call in calls if call.direction == "inbound" and not call.connected_at and call.status in {"missed", "no_answer", "ended"}]
    messages_sent = sum(1 for call in missed if call.sms_sent_at is not None)
    callbacks_open = session.scalar(
        select(func.count(Task.id)).where(
            Task.organization_id == ctx.organization_id,
            Task.source == "missed_call",
            Task.is_completed.is_(False),
        )
    ) or 0
    return {
        "missed_calls": len(missed),
        "automatic_messages_sent": messages_sent,
        "callbacks_open": callbacks_open,
        "reply_rate": 0,
        "recent": [
            {
                "id": call.id,
                "phone": call.phone_number,
                "status": call.status,
                "message_status": call.sms_status,
                "occurred_at": (call.started_at or call.created_at).isoformat(),
            }
            for call in sorted(missed, key=lambda item: item.created_at, reverse=True)[:20]
        ],
    }


@router.get("/never_miss/testers")
def never_miss_testers(
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    """Private operator view for a controlled Never Miss pilot."""
    if ctx.role != "admin":
        raise HTTPException(403, "Administrator access is required")
    subscriptions = session.execute(
        select(ProductSubscription).order_by(ProductSubscription.created_at.desc()).limit(100)
    ).scalars().all()
    items = []
    for subscription in subscriptions:
        calls = []
        config = None
        if subscription.organization_id:
            calls = session.execute(
                select(Call).where(Call.organization_id == subscription.organization_id).order_by(Call.created_at.desc())
            ).scalars().all()
            config = session.execute(select(ProductConfiguration).where(
                ProductConfiguration.organization_id == subscription.organization_id,
                ProductConfiguration.product_code == "never_miss",
            )).scalar_one_or_none()
        items.append({
            "id": subscription.id,
            "business_name": subscription.business_name or subscription.customer_name or "Setup not completed",
            "customer_email": subscription.customer_email,
            "plan": subscription.plan,
            "status": subscription.status,
            "assigned_phone": subscription.assigned_phone,
            "existing_phone": subscription.existing_phone,
            "setup_ready": bool(subscription.assigned_phone and subscription.existing_phone and config and config.enabled),
            "calls": len(calls),
            "messages_sent": sum(1 for call in calls if call.sms_sent_at is not None),
            "last_call_at": calls[0].created_at.isoformat() if calls else None,
            "last_error": subscription.last_error,
            "created_at": subscription.created_at.isoformat(),
        })
    return {"items": items, "total": len(items)}


@router.post("/never_miss_plus/intake")
@router.post("/lead_capture/intake", include_in_schema=False)
def create_customer_inquiry(
    payload: CustomerInquiryInput,
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
):
    return _create_inquiry(session, ctx.organization_id, payload)


@router.post("/never_miss_plus/public-intake", status_code=202)
@router.post("/lead_capture/public-intake", status_code=202, include_in_schema=False)
def public_customer_inquiry(
    payload: CustomerInquiryInput,
    x_pns_intake_key: str | None = Header(default=None),
    session: Session = Depends(get_db_session),
):
    if not x_pns_intake_key:
        raise HTTPException(401, "Missing intake key")
    key_hash = hashlib.sha256(x_pns_intake_key.encode()).hexdigest()
    config = session.execute(
        select(ProductConfiguration).where(
            ProductConfiguration.product_code == "never_miss",
            ProductConfiguration.plan == "never_miss_plus",
            ProductConfiguration.enabled.is_(True),
            ProductConfiguration.intake_key_hash == key_hash,
        )
    ).scalar_one_or_none()
    if config is None:
        raise HTTPException(401, "Invalid intake key")
    return _create_inquiry(session, config.organization_id, payload)


def _create_inquiry(session: Session, organization_id: int, payload: CustomerInquiryInput) -> dict:
    external_id = payload.external_id or str(uuid.uuid4())
    record = LeadCaptureRecord(
        organization_id=organization_id,
        external_id=external_id,
        status="new",
        **payload.model_dump(exclude={"external_id"}),
    )
    session.add(record)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        existing = session.execute(
            select(LeadCaptureRecord).where(
                LeadCaptureRecord.organization_id == organization_id,
                LeadCaptureRecord.source == payload.source,
                LeadCaptureRecord.external_id == external_id,
            )
        ).scalar_one()
        return _lead_payload(existing)
    session.refresh(record)
    return _lead_payload(record)


@router.get("/never_miss_plus/inbox")
@router.get("/lead_capture/inbox", include_in_schema=False)
def customer_inquiry_inbox(
    status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    query = select(LeadCaptureRecord).where(LeadCaptureRecord.organization_id == ctx.organization_id)
    if status:
        query = query.where(LeadCaptureRecord.status == status)
    records = session.execute(query.order_by(LeadCaptureRecord.created_at.desc()).limit(limit)).scalars().all()
    return {"items": [_lead_payload(record) for record in records], "total": len(records)}


@router.patch("/never_miss_plus/inbox/{record_id}")
@router.patch("/lead_capture/inbox/{record_id}", include_in_schema=False)
def update_customer_inquiry(
    record_id: int,
    payload: CustomerInquiryUpdate,
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
):
    record = session.execute(
        select(LeadCaptureRecord).where(
            LeadCaptureRecord.id == record_id,
            LeadCaptureRecord.organization_id == ctx.organization_id,
        )
    ).scalar_one_or_none()
    if record is None:
        raise HTTPException(404, "Customer inquiry not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, key, value)
    session.commit()
    session.refresh(record)
    return _lead_payload(record)
