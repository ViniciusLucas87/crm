"""
Telephony API — call control, webhooks, tokens.

All CRM-facing code talks to TelephonyService. Provider selection is determined
by the TELEPHONY_PROVIDER env var (default: mock in dev, telnyx in prod).
"""

import json
import logging
import os
import re
import uuid
from datetime import UTC, datetime
from functools import lru_cache

import httpx
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.telephony import (
    CallProvider,
    TelephonyService,
    create_call_provider,
    is_telephony_enabled,
    is_webrtc_enabled,
    is_recording_enabled,
)
from app.infrastructure.auth.clerk import AuthContext, require_permission
from app.infrastructure.db.models import Call, Task, Activity, Company, Contact
from app.infrastructure.db.session import get_db_session

logger = logging.getLogger(__name__)
router = APIRouter()

# ── Phone validation ──────────────────────────────────────

_PHONE_RE = re.compile(r"^\+?[1-9]\d{6,14}$")

def _validate_phone(phone: str) -> bool:
    """Basic E.164-ish validation: optional +, digits only, 7-15 chars."""
    return bool(_PHONE_RE.match(phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")))


def _normalize_phone(phone: str) -> str:
    """Normalize a phone number to E.164 format (+1XXXXXXXXXX).

    Handles common North American formats:
      - 10 digits → adds +1 prefix
      - 11 digits starting with 1 → adds + prefix
      - Already E.164 (+1...) → passes through unchanged
    """
    digits = re.sub(r"\D", "", phone)

    if len(digits) == 10:
        return f"+1{digits}"
    if len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"
    if digits.startswith("+"):
        return digits

    # Unknown format — return as-is and let the provider validate
    return f"+{digits}" if not phone.startswith("+") else phone

# ── Telephony config ───────────────────────────────────────

TELEPHONY_PROVIDER = os.environ.get("TELEPHONY_PROVIDER", "mock").lower()

PROVIDER_CONFIGS: dict[str, dict[str, str]] = {
    "telnyx": {
        "api_key": os.environ.get("TELNYX_API_KEY", ""),
        "application_id": os.environ.get("TELNYX_APPLICATION_ID", ""),
        "connection_id": os.environ.get("TELNYX_CONNECTION_ID", ""),
        "phone_number": os.environ.get("TELNYX_PHONE_NUMBER", ""),
        "webhook_secret": os.environ.get("TELNYX_WEBHOOK_SECRET", ""),
        "public_url": os.environ.get("TELNYX_PUBLIC_URL", ""),
    },
    "mock": {},
}


@lru_cache
def _get_telephony_service() -> TelephonyService | None:
    """Lazy-init TelephonyService (cached per process)."""
    if not is_telephony_enabled():
        return None
    name = TELEPHONY_PROVIDER
    config = PROVIDER_CONFIGS.get(name, {})
    provider = create_call_provider(name, config)
    return TelephonyService(provider)


async def _require_telephony() -> TelephonyService:
    """Dependency: raises if telephony is disabled or uninitialized."""
    svc = _get_telephony_service()
    if svc is None:
        from fastapi import HTTPException
        raise HTTPException(503, "Telephony service is disabled")
    if not svc.available:
        await svc.initialize(PROVIDER_CONFIGS.get(TELEPHONY_PROVIDER, {}))
        if not svc.available:
            from fastapi import HTTPException
            raise HTTPException(503, "Telephony provider failed to initialize")
    return svc


# ── Status / config endpoint ───────────────────────────────

@router.get("/telephony/status")
async def telephony_status():
    """Returns telephony feature flags and provider info."""
    svc = _get_telephony_service()
    return {
        "enabled": is_telephony_enabled(),
        "webrtc": is_webrtc_enabled(),
        "recording": is_recording_enabled(),
        "provider": svc.provider_name if svc else "none",
        "available": svc.available if svc else False,
    }


# ── Client token (for browser WebRTC) ──────────────────────

@router.get("/telephony/token")
async def get_client_token(
    ctx: AuthContext = Depends(require_permission("companies:read")),
    svc: TelephonyService = Depends(_require_telephony),
):
    """Generate a client token for browser-based calling."""
    token = await svc.generate_token(str(ctx.user_id) if hasattr(ctx, "user_id") else "unknown")
    return {"token": token.get("token", ""), "expires_at": token.get("expires_at", ""), "provider": svc.provider_name}


# ── Browser registration (POST) ────────────────────────────

@router.post("/telephony/register")
async def register_browser(
    ctx: AuthContext = Depends(require_permission("companies:write")),
    svc: TelephonyService = Depends(_require_telephony),
):
    """Register a browser softphone with the telephony provider.

    Returns a temporary client credential. The API key is never exposed
    to the browser. The returned token is used by the WebRTC client to
    register with Telnyx.
    """
    user_id = str(ctx.user_id) if hasattr(ctx, "user_id") else "unknown"
    result = await svc.register_device(user_id)

    logger.info("Browser registered: user=%s provider=%s", user_id, svc.provider_name)
    return {
        "token": result.get("token", ""),
        "client_state_id": result.get("client_state_id", ""),
        "expires_at": result.get("expires_at", ""),
        "provider": svc.provider_name,
    }


# ── Outbound call ──────────────────────────────────────────

@router.post("/telephony/call")
async def start_outbound_call(
    company_id: int | None = Query(None),
    phone_number: str = Query(),
    contact_id: int | None = Query(None),
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
    svc: TelephonyService = Depends(_require_telephony),
):
    """Initiate an outbound call via the telephony provider."""
    # Normalize to E.164 format
    phone_number = _normalize_phone(phone_number)

    # Validate phone number
    if not _validate_phone(phone_number):
        return {"error": "Invalid phone number format"}

    caller_id = PROVIDER_CONFIGS.get(TELEPHONY_PROVIDER, {}).get("phone_number")
    result = await svc.start_call(
        phone_number,
        caller_id,
        company_id=company_id,
        contact_id=contact_id,
        organization_id=ctx.organization_id,
    )

    return {
        "status": result.status,
        "phone_number": phone_number,
        "caller_id": caller_id,
        "provider": svc.provider_name,
    }


class BrowserCallCreate(BaseModel):
    phone_number: str
    company_id: int | None = None
    contact_id: int | None = None


class BrowserCallUpdate(BaseModel):
    status: str = Field(pattern="^(dialing|ringing|connected|ended|failed)$")
    duration_seconds: int = Field(default=0, ge=0, le=86400)


class SmsSendRequest(BaseModel):
    phone_number: str
    message: str = Field(min_length=1, max_length=1000)
    company_id: int | None = None
    contact_id: int | None = None


def _validate_crm_links(
    session: Session,
    organization_id: int,
    company_id: int | None,
    contact_id: int | None,
) -> str | None:
    """Ensure optional CRM links belong to the authenticated organization."""
    if company_id is not None:
        company = session.execute(
            select(Company).where(Company.id == company_id, Company.organization_id == organization_id)
        ).scalar_one_or_none()
        if not company:
            return "Company not found"
    if contact_id is not None:
        contact = session.execute(
            select(Contact).where(Contact.id == contact_id, Contact.organization_id == organization_id)
        ).scalar_one_or_none()
        if not contact or (company_id is not None and contact.company_id != company_id):
            return "Contact not found"
    return None


@router.post("/telephony/calls/browser")
def create_browser_call(
    payload: BrowserCallCreate,
    ctx: AuthContext = Depends(require_permission("telephony:write")),
    session: Session = Depends(get_db_session),
):
    """Create the CRM ledger entry for a browser WebRTC call."""
    phone_number = _normalize_phone(payload.phone_number)
    if not _validate_phone(phone_number):
        return JSONResponse(content={"error": "Enter a valid phone number"}, status_code=422)
    link_error = _validate_crm_links(session, ctx.organization_id, payload.company_id, payload.contact_id)
    if link_error:
        return JSONResponse(content={"error": link_error}, status_code=404)

    call = Call(
        public_uuid=str(uuid.uuid4()),
        organization_id=ctx.organization_id,
        company_id=payload.company_id,
        contact_id=payload.contact_id,
        provider="telnyx_webrtc",
        direction="outbound",
        status="dialing",
        phone_number=phone_number,
        caller_id=PROVIDER_CONFIGS.get(TELEPHONY_PROVIDER, {}).get("phone_number"),
        normalized_destination_number=phone_number,
        started_at=datetime.now(UTC),
        created_by=str(ctx.user_id),
    )
    session.add(call)
    session.commit()
    session.refresh(call)
    return {"id": call.id, "call_uuid": call.public_uuid, "status": call.status}


@router.patch("/telephony/calls/browser/{call_id}")
def update_browser_call(
    call_id: int,
    payload: BrowserCallUpdate,
    ctx: AuthContext = Depends(require_permission("telephony:write")),
    session: Session = Depends(get_db_session),
):
    """Update a browser call without exposing provider credentials."""
    call = session.execute(
        select(Call).where(Call.id == call_id, Call.organization_id == ctx.organization_id)
    ).scalar_one_or_none()
    if not call:
        return JSONResponse(content={"error": "Call not found"}, status_code=404)

    call.status = payload.status
    call.duration_seconds = payload.duration_seconds
    if payload.status == "connected" and not call.connected_at:
        call.connected_at = datetime.now(UTC)
    if payload.status in {"ended", "failed"}:
        call.ended_at = datetime.now(UTC)
    session.commit()
    return {"id": call.id, "status": call.status}


@router.post("/telephony/sms")
async def send_sms(
    payload: SmsSendRequest,
    ctx: AuthContext = Depends(require_permission("telephony:write")),
    session: Session = Depends(get_db_session),
):
    """Send a one-to-one operational text and store it in CRM history."""
    from app.application.intake.sms import can_send_sms

    phone_number = _normalize_phone(payload.phone_number)
    if not _validate_phone(phone_number):
        return JSONResponse(content={"error": "Enter a valid phone number"}, status_code=422)
    link_error = _validate_crm_links(session, ctx.organization_id, payload.company_id, payload.contact_id)
    if link_error:
        return JSONResponse(content={"error": link_error}, status_code=404)

    allowed, reason = can_send_sms(session, ctx.organization_id, phone_number)
    if not allowed:
        message = "This number opted out of text messages" if reason == "phone_suppressed" else "Text message cannot be sent"
        return JSONResponse(content={"error": message}, status_code=409)

    api_key = os.environ.get("TELNYX_API_KEY", "")
    from_phone = os.environ.get("TELNYX_PHONE_NUMBER", "")
    messaging_profile_id = os.environ.get("TELNYX_MESSAGING_PROFILE_ID", "")
    if not api_key or not from_phone:
        return JSONResponse(content={"error": "Text messaging is not configured"}, status_code=503)

    body = {
        "from": from_phone,
        "to": phone_number,
        "text": payload.message.strip(),
        "webhook_url": os.environ.get("API_PUBLIC_URL", "").rstrip("/") + "/api/v1/telephony/sms/webhook",
    }
    if messaging_profile_id:
        body["messaging_profile_id"] = messaging_profile_id

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            "https://api.telnyx.com/v2/messages",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=body,
        )
    if response.status_code not in (200, 201, 202):
        logger.error("Telnyx SMS send failed with status %s", response.status_code)
        return JSONResponse(content={"error": "The text message could not be sent"}, status_code=502)

    provider_message_id = response.json().get("data", {}).get("id", "")
    activity = Activity(
        organization_id=ctx.organization_id,
        company_id=payload.company_id,
        contact_id=payload.contact_id,
        activity_type="sms_sent",
        subject=f"SMS to {phone_number}",
        body=payload.message.strip(),
    )
    session.add(activity)
    session.commit()
    return {"status": "sent", "message_id": provider_message_id, "activity_id": activity.id}


@router.get("/telephony/history")
def communication_history(
    limit: int = Query(default=100, ge=1, le=200),
    ctx: AuthContext = Depends(require_permission("telephony:read")),
    session: Session = Depends(get_db_session),
):
    """Return calls and text messages for the PNS phone workspace."""
    calls = session.execute(
        select(Call)
        .where(Call.organization_id == ctx.organization_id)
        .order_by(Call.created_at.desc())
        .limit(limit)
    ).scalars().all()
    activities = session.execute(
        select(Activity)
        .where(
            Activity.organization_id == ctx.organization_id,
            Activity.activity_type.in_(("sms_sent", "sms_received")),
        )
        .order_by(Activity.created_at.desc())
        .limit(limit)
    ).scalars().all()

    items: list[dict] = []
    for call in calls:
        missed = call.direction == "inbound" and call.status in {"missed", "no_answer", "ended"} and not call.connected_at
        items.append({
            "id": f"call-{call.id}",
            "kind": "call",
            "direction": call.direction,
            "status": "missed" if missed else call.status,
            "phone_number": call.phone_number,
            "timestamp": (call.started_at or call.created_at).isoformat(),
            "duration_seconds": call.duration_seconds or 0,
            "preview": "Missed call" if missed else ("Incoming call" if call.direction == "inbound" else "Outgoing call"),
        })
        if call.sms_sent_at:
            items.append({
                "id": f"recovery-sms-{call.id}",
                "kind": "sms",
                "direction": "outbound",
                "status": call.sms_status or "sent",
                "phone_number": call.phone_number,
                "timestamp": call.sms_sent_at.isoformat(),
                "duration_seconds": 0,
                "preview": "Automatic missed call reply",
            })

    for activity in activities:
        prefix = "SMS to " if activity.activity_type == "sms_sent" else "SMS from "
        subject = activity.subject or ""
        phone_number = subject[len(prefix):].strip() if subject.startswith(prefix) else "Unknown number"
        items.append({
            "id": f"activity-{activity.id}",
            "kind": "sms",
            "direction": "outbound" if activity.activity_type == "sms_sent" else "inbound",
            "status": "received" if activity.activity_type == "sms_received" else "sent",
            "phone_number": phone_number,
            "timestamp": activity.created_at.isoformat(),
            "duration_seconds": 0,
            "preview": activity.body or ("Text received" if activity.activity_type == "sms_received" else "Text sent"),
        })

    items.sort(key=lambda item: item["timestamp"], reverse=True)
    return {
        "phone_number": PROVIDER_CONFIGS.get(TELEPHONY_PROVIDER, {}).get("phone_number", ""),
        "items": items[:limit],
        "total": min(len(items), limit),
    }


# Webhook handler (Telnyx call events)

REDACT = "***REDACTED***"


def _redact_number(num: str | None) -> str:
    """Return last 4 digits only, or REDACT if None."""
    if not num:
        return REDACT
    digits = re.sub(r"\D", "", num)
    if len(digits) >= 4:
        return f"...{digits[-4:]}"
    return REDACT


@router.post("/telephony/webhook")
async def telnyx_webhook(request: Request, session: Session = Depends(get_db_session)):
    """Receive Telnyx call state webhooks. Fast acknowledge, deferred side effects.

    Flow:
      1. Verify Ed25519 signature (fail-closed)
      2. Insert into immutable event ledger (IntegrityError only -> duplicate ack)
      3. Find/create call, score spam, transition state
      4. Emit call.reconciliation.requested for hangup (worker determines missed)
      5. Single atomic commit -- processing_status is set only at commit time
    """
    from app.application.telephony.call_lifecycle import CallLifecycleService, TELNYX_STATE_MAP
    from app.application.intake.webhook_verify import verify_webhook_signature
    from app.application.intake import normalize_phone, score_call_spam
    from app.application.intake.spam import ALLOW_MAX
    from app.infrastructure.db.models import ProviderWebhookEvent, OutboxEvent
    from sqlalchemy.exc import IntegrityError
    import hashlib

    raw_body = await request.body()
    try:
        body_data = json.loads(raw_body)
    except Exception:
        return {"error": "Invalid JSON"}

    # Verify Telnyx Ed25519 signature -- fail closed
    signature = request.headers.get("telnyx-signature-ed25519", "")
    timestamp = request.headers.get("telnyx-timestamp", "")
    if not verify_webhook_signature(raw_body, signature, timestamp):
        logger.warning("Telnyx webhook: signature verification FAILED")
        return JSONResponse(content={"error": "Invalid signature"}, status_code=401)

    data = body_data.get("data", {})
    provider_event_id = data.get("id", "")
    event_type = data.get("event_type", "")
    payload = data.get("payload", {})
    provider_call_id = payload.get("call_control_id", "")
    provider_leg_id = payload.get("call_leg_id", "")

    if not provider_event_id:
        return {"error": "Missing provider event id"}

    # --- Transactional dedup: insert into immutable event ledger ---
    # Only IntegrityError (unique violation) means duplicate. All other DB errors
    # must propagate and be recorded, not silently acknowledged.
    payload_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]

    wh_event = ProviderWebhookEvent(
        provider_event_id=provider_event_id,
        provider="telnyx",
        event_type=event_type,
        call_control_id=provider_call_id or None,
        call_leg_id=provider_leg_id or None,
        payload_hash=payload_hash,
    )
    session.add(wh_event)
    try:
        session.flush()
    except IntegrityError:
        session.rollback()
        logger.info("Webhook: duplicate event %s acknowledged", provider_event_id[:32])
        return {"status": "duplicate", "provider_event_id": provider_event_id}
    # Any other exception (connection error, constraint, etc.) propagates up

    if not provider_call_id:
        # Mark processed atomically with commit
        wh_event.processing_status = "processed"
        session.commit()
        return {"status": "acknowledged", "note": "no call_control_id"}

    # --- Find or create call ---
    lifecycle = CallLifecycleService(session)
    call = lifecycle.find_by_provider_id(provider_call_id)

    if not call:
        caller_number = normalize_phone(payload.get("from", ""))
        dest_number = normalize_phone(payload.get("to", ""))
        org_id = _resolve_tenant(session, dest_number)
        entities = lifecycle.resolve_entities(
            caller_number or payload.get("from", ""),
            organization_id=org_id,
        )
        call = lifecycle.create_call(
            direction="inbound",
            phone_number=payload.get("from", ""),
            caller_id=payload.get("from", ""),
            company_id=entities.get("company_id"),
            contact_id=entities.get("contact_id"),
            organization_id=org_id,
            provider="telnyx",
            correlation_id=str(uuid.uuid4()),
        )

    call.provider_leg_id = provider_leg_id or call.provider_leg_id

    # --- Spam scoring on first event ---
    if call.spam_score is None:
        spam = score_call_spam(
            caller_number=call.normalized_caller_number,
            duration_seconds=call.duration_seconds or 0,
            call_status=call.status or "",
        )
        call.spam_score = spam.score
        call.spam_reasons = ", ".join(spam.reasons) if spam.reasons else None

    # --- Transition to canonical state ---
    # Hangup always transitions to COMPLETED. The reconciliation worker
    # determines missed-call status from the event ledger after a grace period.
    canonical = TELNYX_STATE_MAP.get(event_type)
    if canonical:
        try:
            lifecycle.transition(
                call=call,
                to_state=canonical,
                provider_event_id=event_type,
                provider_call_id=provider_call_id,
                provider_leg_id=provider_leg_id,
            )
        except Exception:
            session.rollback()
            raise

    # Deferred reconciliation: emit call.reconciliation.requested for hangup events
    # with ALLOW spam tier. The worker checks the event ledger after a grace period
    # and creates task + activity + SMS only if the call was truly missed.
    if event_type == "call.hangup" and _should_reconcile(session, call):
        rec_idem_key = f"reconciliation_{call.public_uuid}"
        reconciliation_event = OutboxEvent(
            event_type="call.reconciliation.requested",
            payload_json={
                "call_id": call.id,
                "call_public_uuid": call.public_uuid,
                "caller_number": _redact_number(call.caller_id),
                "normalized_caller_number": call.normalized_caller_number,
                "organization_id": call.organization_id,
                "contact_id": call.contact_id,
                "company_id": call.company_id,
            },
            correlation_id=rec_idem_key,
            idempotency_key=f"reconciliation_{call.public_uuid}",
        )
        # Use DB unique constraint on idempotency_key for concurrency safety
        try:
            session.add(reconciliation_event)
            session.flush()
        except IntegrityError:
            # Another webhook already enqueued this reconciliation — safe to skip
            session.rollback()
            logger.info(
                "Reconciliation already enqueued for call=%s, skipping duplicate",
                call.public_uuid,
            )
            # Re-add the webhook event since rollback removed it
            session.add(wh_event)
            wh_event.processing_status = "processed"
            session.commit()
            return {"status": "ok", "call_uuid": call.public_uuid, "state": call.status, "note": "reconciliation already enqueued"}

    # --- Atomic commit: ledger + call + reconciliation all-or-nothing ---
    wh_event.processing_status = "processed"
    session.commit()

    logger.info(
        "Webhook: event=%s call=%s state=%s spam=%s caller=%s",
        event_type, call.public_uuid, call.status, call.spam_score,
        _redact_number(call.caller_id),
    )
    return {"status": "ok", "call_uuid": call.public_uuid, "state": call.status}


def _should_reconcile(session: Session, call: Call) -> bool:
    """Check if a hangup warrants reconciliation (was the call truly missed?).

    Reconciliation is deferred to the worker, which checks the event ledger
    after a configurable grace period. This function only gates whether to
    enqueue the reconciliation event.
    """
    from app.application.intake.spam import ALLOW_MAX

    # Only for hangups
    if call.status != "COMPLETED":
        return False
    # Only ALLOW tier (spam calls don't warrant reconciliation)
    if call.spam_score is not None and call.spam_score > ALLOW_MAX:
        return False
    # Call must have a provider_call_id for the worker to check
    if not call.provider_call_id:
        return False
    return True


def _resolve_tenant(session: Session, destination_number: str | None) -> int:
    """Resolve tenant from destination phone number or configured mapping.
    Production must have mapping or explicit destination number.
    """
    if not destination_number:
        if os.environ.get("ENVIRONMENT", "development") == "production":
            logger.error("Cannot resolve tenant: no destination number")
            raise ValueError("Tenant resolution failed: missing destination number")
        return 1

    tenant_map_str = os.environ.get("TELNYX_NUMBER_TENANT_MAP", "")
    if tenant_map_str:
        try:
            tenant_map = json.loads(tenant_map_str)
            org_id = tenant_map.get(destination_number)
            if org_id:
                return int(org_id)
        except Exception:
            pass

    if os.environ.get("ENVIRONMENT", "development") == "production":
        logger.error("Tenant not mapped for destination %s", _redact_number(destination_number))
        raise ValueError("Tenant resolution failed")

    return 1


def _resolve_sms_tenant(
    session: Session,
    event_type: str,
    from_number: str | None,
    to_number: str | None,
) -> int:
    """Resolve the tenant from the business-owned side of an SMS event.

    Inbound messages are addressed to our number. Delivery receipts describe an
    outbound message, so our number is the sender. Trying only the destination
    makes production delivery receipts resolve against the customer's number.
    """
    primary = from_number if event_type == "message.finalized" else to_number
    secondary = to_number if event_type == "message.finalized" else from_number

    tenant_map_str = os.environ.get("TELNYX_NUMBER_TENANT_MAP", "")
    try:
        tenant_map = json.loads(tenant_map_str) if tenant_map_str else {}
    except (TypeError, ValueError):
        tenant_map = {}

    for candidate in (primary, secondary):
        if candidate and candidate in tenant_map:
            return int(tenant_map[candidate])

    return _resolve_tenant(session, primary)


# ── Inbound SMS webhook ────────────────────────────────────

@router.post("/telephony/sms/webhook")
async def sms_webhook(request: Request, session: Session = Depends(get_db_session)):
    """Receive Telnyx inbound SMS webhooks: STOP, START, replies, delivery receipts.

    Flow:
      1. Verify signature (fail-closed)
      2. Dedup via provider event id
      3. STOP/START: durably update phone_suppressions
      4. Normal reply: store as activity on contact timeline
      5. Delivery receipt: update SMS message status on call
    """
    from app.application.intake.webhook_verify import verify_webhook_signature
    from app.application.intake import normalize_phone
    from app.application.intake.sms import suppress_phone, remove_suppression
    from app.infrastructure.db.models import ProviderWebhookEvent, PhoneSuppression, Activity
    from sqlalchemy.exc import IntegrityError
    import hashlib

    raw_body = await request.body()
    try:
        body_data = json.loads(raw_body)
    except Exception:
        return {"error": "Invalid JSON"}

    signature = request.headers.get("telnyx-signature-ed25519", "")
    timestamp = request.headers.get("telnyx-timestamp", "")
    if not verify_webhook_signature(raw_body, signature, timestamp):
        logger.warning("SMS webhook: signature FAILED")
        return JSONResponse(content={"error": "Invalid signature"}, status_code=401)

    data = body_data.get("data", {})
    provider_event_id = data.get("id", "")
    event_type = data.get("event_type", "")
    payload = data.get("payload", {})

    if not provider_event_id:
        return {"error": "Missing provider event id"}

    # Dedup
    payload_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]
    wh_event = ProviderWebhookEvent(
        provider_event_id=provider_event_id,
        provider="telnyx",
        event_type=event_type,
        payload_hash=payload_hash,
    )
    session.add(wh_event)
    try:
        session.flush()
    except IntegrityError:
        session.rollback()
        return {"status": "duplicate", "provider_event_id": provider_event_id}
    except Exception:
        session.rollback()
        raise

    from_number = payload.get("from", {}).get("phone_number", "") if isinstance(payload.get("from"), dict) else ""
    to_number = payload.get("to", [{}])[0].get("phone_number", "") if isinstance(payload.get("to"), list) and payload.get("to") else ""
    text = payload.get("text", "").strip()
    normalized_from = normalize_phone(from_number) if from_number else None

    normalized_to = normalize_phone(to_number) if to_number else None

    # Resolve against the business-owned number. For outbound delivery receipts,
    # that is the sender; for inbound messages, it is the destination.
    org_id = _resolve_sms_tenant(
        session,
        event_type,
        normalized_from,
        normalized_to,
    )

    # STOP/START handling
    text_upper = text.upper()
    if text_upper in ("STOP", "STOPALL", "UNSUBSCRIBE", "CANCEL", "END", "QUIT"):
        suppress_phone(session, org_id, normalized_from or from_number, reason=text_upper, source_event_id=provider_event_id)
        wh_event.processing_status = "processed"
        session.commit()
        logger.info("SMS STOP: %s for org %d", _redact_number(from_number), org_id)
        return {"status": "suppressed", "phone": _redact_number(from_number)}

    if text_upper in ("START", "YES", "UNSTOP"):
        remove_suppression(session, org_id, normalized_from or from_number)
        wh_event.processing_status = "processed"
        session.commit()
        logger.info("SMS START: %s for org %d", _redact_number(from_number), org_id)
        return {"status": "unsuppressed", "phone": _redact_number(from_number)}

    # Delivery receipt
    if event_type == "message.finalized":
        dlr_status = payload.get("detail", {}).get("status", "")
        message_id = payload.get("id", "")
        if message_id:
            call = session.query(Call).filter(Call.sms_message_id == message_id).first()
            if call:
                call.sms_status = dlr_status or "delivered"
                wh_event.processing_status = "processed"
                session.commit()
                return {"status": "dlr_updated", "call_uuid": call.public_uuid}

    # Normal inbound reply: find contact, create activity
    contact = None
    if normalized_from:
        contact = session.query(Contact).filter(
            Contact.organization_id == org_id,
            (Contact.phone == normalized_from) | (Contact.mobile == normalized_from),
        ).first()

    if text:
        activity = Activity(
            organization_id=org_id,
            company_id=contact.company_id if contact else None,
            contact_id=contact.id if contact else None,
            activity_type="sms_received",
            subject=f"SMS from {normalized_from or from_number}",
            body=text,
        )
        session.add(activity)

    wh_event.processing_status = "processed"
    session.commit()
    return {"status": "ok", "contact_id": contact.id if contact else None}


# ── Call list (for Conversation page) ──────────────────────

@router.get("/calls")
async def list_calls(
    company_id: int = Query(),
    session: Session = Depends(get_db_session),
):
    """List calls for a company. Returns public UUIDs only."""
    calls = session.execute(
        select(Call).where(
            Call.company_id == company_id,
        ).order_by(Call.created_at.desc()).limit(50)
    ).scalars().all()

    return [{
        "call_uuid": c.public_uuid,
        "direction": c.direction,
        "status": c.status,
        "phone_number": c.phone_number,
        "duration_seconds": c.duration_seconds,
        "connected_at": c.connected_at.isoformat() if c.connected_at else None,
        "ended_at": c.ended_at.isoformat() if c.ended_at else None,
        "outcome": c.outcome,
    } for c in calls]


@router.get("/calls/{public_uuid}")
async def get_call_detail(
    public_uuid: str,
    session: Session = Depends(get_db_session),
):
    """Get detailed call info by public UUID."""
    call = session.execute(
        select(Call).where(Call.public_uuid == public_uuid)
    ).scalar_one_or_none()

    if not call:
        return {"error": "Call not found"}

    return {
        "call_uuid": call.public_uuid,
        "direction": call.direction,
        "status": call.status,
        "outcome": call.outcome,
        "phone_number": call.phone_number,
        "caller_id": call.caller_id,
        "duration_seconds": call.duration_seconds,
        "started_at": call.started_at.isoformat() if call.started_at else None,
        "ringing_at": call.ringing_at.isoformat() if call.ringing_at else None,
        "connected_at": call.connected_at.isoformat() if call.connected_at else None,
        "ended_at": call.ended_at.isoformat() if call.ended_at else None,
        "transcript_status": call.transcript_status,
        "post_call_status": call.post_call_status,
        "company_id": call.company_id,
        "contact_id": call.contact_id,
        "lead_id": call.lead_id,
        "disconnect_reason": call.disconnect_reason,
        "provider": call.provider,
    }


# ── Call status ─────────────────────────────────────────────

@router.get("/telephony/call/{call_id}/status")
async def get_call_status(
    call_id: int,
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    """Get current call status for auto-end polling."""
    call = session.execute(
        select(Call).where(Call.id == call_id, Call.organization_id == ctx.organization_id)
    ).scalar_one_or_none()

    if not call:
        return {"error": "Call not found"}

    return {
        "call_id": call.id,
        "status": call.status,
        "provider_call_id": call.provider_call_id,
        "duration_seconds": call.duration_seconds,
    }


# ── End call ───────────────────────────────────────────────

@router.post("/telephony/call/{call_id}/end")
async def end_call(
    call_id: int,
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
    svc: TelephonyService = Depends(_require_telephony),
):
    """End an active call."""
    call = session.execute(
        select(Call).where(Call.id == call_id, Call.organization_id == ctx.organization_id)
    ).scalar_one_or_none()

    if not call:
        return {"error": "Call not found"}

    if call.provider_call_id:
        await svc.end_call(call.provider_call_id)

    call.status = "ended"
    call.ended_at = datetime.now(UTC)
    if call.started_at:
        call.duration_seconds = int((call.ended_at - call.started_at).total_seconds())
    session.commit()

    return {"call_id": call.id, "status": "ended", "duration_seconds": call.duration_seconds}


# ── Call controls ──────────────────────────────────────────

@router.post("/telephony/call/{call_id}/mute")
async def mute_call(
    call_id: int,
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
    svc: TelephonyService = Depends(_require_telephony),
):
    """Mute an active call."""
    call = session.execute(
        select(Call).where(Call.id == call_id, Call.organization_id == ctx.organization_id)
    ).scalar_one_or_none()
    if not call or not call.provider_call_id:
        return {"error": "Call not found"}
    ok = await svc.mute(call.provider_call_id, True)
    return {"call_id": call.id, "muted": ok}


@router.post("/telephony/call/{call_id}/unmute")
async def unmute_call(
    call_id: int,
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
    svc: TelephonyService = Depends(_require_telephony),
):
    """Unmute a muted call."""
    call = session.execute(
        select(Call).where(Call.id == call_id, Call.organization_id == ctx.organization_id)
    ).scalar_one_or_none()
    if not call or not call.provider_call_id:
        return {"error": "Call not found"}
    ok = await svc.mute(call.provider_call_id, False)
    return {"call_id": call.id, "unmuted": ok}


@router.post("/telephony/call/{call_id}/hold")
async def hold_call(
    call_id: int,
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
    svc: TelephonyService = Depends(_require_telephony),
):
    """Place a call on hold."""
    call = session.execute(
        select(Call).where(Call.id == call_id, Call.organization_id == ctx.organization_id)
    ).scalar_one_or_none()
    if not call or not call.provider_call_id:
        return {"error": "Call not found"}
    ok = await svc.hold(call.provider_call_id)
    return {"call_id": call.id, "on_hold": ok}


@router.post("/telephony/call/{call_id}/resume")
async def resume_call(
    call_id: int,
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
    svc: TelephonyService = Depends(_require_telephony),
):
    """Resume a call from hold."""
    call = session.execute(
        select(Call).where(Call.id == call_id, Call.organization_id == ctx.organization_id)
    ).scalar_one_or_none()
    if not call or not call.provider_call_id:
        return {"error": "Call not found"}
    ok = await svc.resume(call.provider_call_id)
    return {"call_id": call.id, "resumed": ok}


# ── Recording ──────────────────────────────────────────────

@router.post("/telephony/call/{call_id}/recording/start")
async def start_recording(
    call_id: int,
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
    svc: TelephonyService = Depends(_require_telephony),
):
    """Start recording an active call."""
    call = session.execute(
        select(Call).where(Call.id == call_id, Call.organization_id == ctx.organization_id)
    ).scalar_one_or_none()
    if not call or not call.provider_call_id:
        return {"error": "Call not found"}
    rec_id = await svc.start_recording(call.provider_call_id)
    if rec_id:
        call.recording_status = "in_progress"
        session.commit()
    return {"call_id": call.id, "recording_id": rec_id}


@router.post("/telephony/call/{call_id}/recording/stop")
async def stop_recording(
    call_id: int,
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
    svc: TelephonyService = Depends(_require_telephony),
):
    """Stop recording and retrieve the recording URL."""
    call = session.execute(
        select(Call).where(Call.id == call_id, Call.organization_id == ctx.organization_id)
    ).scalar_one_or_none()
    if not call or not call.provider_call_id:
        return {"error": "Call not found"}
    # We store recording_id in metadata; in practice it would come from start_recording
    rec_id = "recording"
    url = await svc.stop_recording(call.provider_call_id, rec_id)
    if url:
        call.recording_url = url
        call.recording_status = "completed"
        session.commit()
    return {"call_id": call.id, "recording_url": url or None}


# ── Call history ───────────────────────────────────────────

@router.get("/telephony/calls")
def list_calls(
    company_id: int | None = Query(None),
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    """List call history."""
    stmt = select(Call).where(Call.organization_id == ctx.organization_id)
    if company_id:
        stmt = stmt.where(Call.company_id == company_id)
    stmt = stmt.order_by(Call.created_at.desc()).limit(50)

    calls = session.execute(stmt).scalars().all()
    return {
        "items": [{
            "id": c.id, "session_id": c.session_id,
            "company_id": c.company_id, "contact_id": c.contact_id, "activity_id": c.activity_id,
            "provider": c.provider, "provider_call_id": c.provider_call_id,
            "direction": c.direction, "status": c.status,
            "phone_number": c.phone_number, "caller_id": c.caller_id,
            "started_at": str(c.started_at) if c.started_at else None,
            "answered_at": str(c.connected_at) if c.connected_at else None,
            "ended_at": str(c.ended_at) if c.ended_at else None,
            "duration_seconds": c.duration_seconds,
            "recording_url": c.recording_url, "recording_status": c.recording_status,
            "transcript_status": c.transcript_status, "ai_status": c.post_call_status,
            "created_at": str(c.created_at),
        } for c in calls],
        "total": len(calls),
    }


# ── Webhooks ───────────────────────────────────────────────

@router.post("/telephony/webhooks/telnyx")
async def telnyx_webhook(request: Request, session: Session = Depends(get_db_session)):
    """Handle provider webhook events with signature verification."""
    # Read raw body for signature verification
    raw_body = await request.body()

    try:
        body = json.loads(raw_body)
    except Exception:
        return {"status": "invalid_json"}

    # Verify webhook signature
    svc = _get_telephony_service()
    if svc:
        signature = request.headers.get("Telnyx-Signature", "")
        timestamp = request.headers.get("Telnyx-Timestamp", "")
        if not svc.verify_webhook_signature(raw_body, signature, timestamp):
            logger.warning("Telnyx webhook: signature verification FAILED")
            return {"status": "invalid_signature"}

    event_type = body.get("data", {}).get("event_type", "")
    payload = body.get("data", {}).get("payload", {})
    call_control_id = payload.get("call_control_id", "")

    logger.info("Telephony webhook: %s (call %s)", event_type, call_control_id)

    # Update state machine via TelephonyService
    if svc:
        svc.handle_webhook_event(event_type, call_control_id, payload)

    # Update DB call record
    if call_control_id:
        call = session.execute(
            select(Call).where(Call.provider_call_id == call_control_id)
        ).scalar_one_or_none()

        if call:
            if event_type == "call.answered":
                call.status = "connected"
                call.connected_at = datetime.now(UTC)
            elif event_type == "call.hangup":
                call.status = "ended"
                call.ended_at = datetime.now(UTC)
                if call.started_at:
                    call.duration_seconds = int((call.ended_at - call.started_at).total_seconds())
            elif event_type == "call.recording.saved":
                recording_urls = payload.get("recording_urls", {})
                call.recording_url = recording_urls.get("mp3", "") or payload.get("recording_url", "")
                call.recording_status = "completed"
            elif event_type == "call.failed":
                call.status = "failed"
                call.metadata_json = {"error": payload}
            elif event_type == "call.missed":
                call.status = "missed"
            elif event_type == "call.initiated":
                call.status = "dialing"

            session.commit()

    return {"status": "ok", "event": event_type}
