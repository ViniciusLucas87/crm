"""
Sprint 48.1 — Call Lifecycle Service

Bridges the in-memory CallSessionManager to persistent Call records.
Every call state transition writes to the database, creates activities,
emits outbox events, and queues timeline projection.

Architecture:
    Telnyx Webhook / CRM API → CallLifecycleService → DB (Call) + Outbox
    Celery workers consume outbox → Activities, Timeline, Metrics, KG
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, UTC
from typing import Any

from sqlalchemy.orm import Session

from app.application.telephony import CallState
from app.infrastructure.db.models import Call, Activity, OutboxEvent, Company, Contact

logger = logging.getLogger(__name__)

DEFAULT_ORG_ID = 1


def _utcnow() -> datetime:
    """Return timezone-aware UTC now."""
    return datetime.now(UTC)


def _ensure_utc(dt: datetime | None) -> datetime | None:
    """Normalize a datetime to UTC-aware. SQLite strips timezone info."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        from datetime import timezone
        return dt.replace(tzinfo=timezone.utc)
    return dt


# ═══════════════════════════════════════════════════════════
# CANONICAL STATE MAPPING (Telnyx → Canonical)
# ═══════════════════════════════════════════════════════════

CANONICAL_STATES = {
    "idle": "CREATED",
    "dialing": "REQUESTING",
    "ringing": "RINGING",
    "connected": "CONNECTED",
    "ended": "COMPLETED",
    "failed": "FAILED",
    "missed": "MISSED",
    "on_hold": "CONNECTED",
}

# Telnyx SDK state → canonical
TELNYX_STATE_MAP: dict[str, str] = {
    "call.initiated": "REQUESTING",
    "call.answered": "CONNECTED",
    "call.hangup": "COMPLETED",
    "call.failed": "FAILED",
    "call.missed": "MISSED",
}

# Which events create Activities
ACTIVITY_PRODUCING_STATES = {
    "REQUESTING": "CALL_INITIATED",
    "CONNECTED": "CALL_CONNECTED",
    "COMPLETED": "CALL_COMPLETED",
    "MISSED": "CALL_MISSED",
    "FAILED": "CALL_FAILED",
}


# ═══════════════════════════════════════════════════════════
# SERVICE
# ═══════════════════════════════════════════════════════════

class CallLifecycleService:
    """Persistent call lifecycle — creates and updates Call rows, emits outbox events."""

    def __init__(self, session: Session):
        self._db = session

    # ── Call Creation ──

    def create_call(
        self,
        direction: str,
        phone_number: str,
        caller_id: str | None = None,
        normalized_caller_number: str | None = None,
        normalized_destination_number: str | None = None,
        company_id: int | None = None,
        contact_id: int | None = None,
        lead_id: int | None = None,
        organization_id: int = DEFAULT_ORG_ID,
        provider: str = "telnyx",
        correlation_id: str | None = None,
        session_id: str | None = None,
        created_by: str | None = None,
    ) -> Call:
        """Create a persistent Call record. Idempotent on provider_call_id later."""
        correlation_id = correlation_id or str(uuid.uuid4())
        now = datetime.now(UTC)

        call = Call(
            public_uuid=str(uuid.uuid4()),
            organization_id=organization_id,
            company_id=company_id,
            contact_id=contact_id,
            lead_id=lead_id,
            direction=direction,
            status="CREATED",
            phone_number=phone_number,
            caller_id=caller_id,
            normalized_caller_number=normalized_caller_number or _normalize_phone(caller_id if direction == "inbound" else phone_number),
            normalized_destination_number=normalized_destination_number or (_normalize_phone(phone_number) if direction == "outbound" else None),
            provider=provider,
            session_id=session_id,
            correlation_id=correlation_id,
            created_by=created_by,
            started_at=now,
            created_at=now,
            updated_at=now,
        )
        self._db.add(call)
        self._db.flush()

        logger.info(
            "Call created: uuid=%s direction=%s phone=%s company=%s",
            call.public_uuid, direction, phone_number, company_id,
        )

        # Activity + Timeline outbox
        _emit_outbox(self._db, "call.created", {
            "call_uuid": call.public_uuid, "call_id": call.id,
            "direction": direction, "company_id": company_id,
            "contact_id": contact_id, "lead_id": lead_id,
            "correlation_id": correlation_id,
        })

        return call

    # ── State Transitions ──

    def transition(
        self,
        call: Call,
        to_state: str,
        provider_event_id: str | None = None,
        provider_call_id: str | None = None,
        provider_leg_id: str | None = None,
        reason: str | None = None,
    ) -> Call:
        """Transition a call to a new canonical state. Persists changes + emits events."""
        previous = call.status
        canonical = CANONICAL_STATES.get(to_state, to_state)
        now = datetime.now(UTC)

        # State validation -- reject backward transitions on terminal states
        # MISSED is terminal: no further transitions allowed
        if previous in ("COMPLETED", "FAILED", "MISSED"):
            if canonical == previous:
                logger.info("Call %s already terminal (%s), no-op", call.public_uuid, previous)
                return call
            logger.warning(
                "Call %s already terminal (%s), rejecting transition to %s",
                call.public_uuid, previous, canonical,
            )
            return call

        call.status = canonical
        call.updated_at = now

        # Store provider identifiers
        if provider_call_id:
            call.provider_call_id = provider_call_id
        if provider_leg_id:
            call.provider_leg_id = provider_leg_id

        # Timing updates
        if canonical == "RINGING" and not call.ringing_at:
            call.ringing_at = now
        elif canonical == "CONNECTED" and not call.connected_at:
            call.connected_at = now
        elif canonical in ("COMPLETED", "FAILED", "MISSED"):
            call.ended_at = now
            call.outcome = canonical.lower()
            connected = _ensure_utc(call.connected_at)
            if connected:
                call.duration_seconds = int((now - connected).total_seconds())
            if canonical == "FAILED":
                call.failure_message = reason

        self._db.flush()

        # Activity-producing transitions
        activity_type = ACTIVITY_PRODUCING_STATES.get(canonical)
        activity_id = None
        if activity_type:
            activity_id = self._create_activity(call, activity_type)
            call.activity_id = activity_id
            self._db.flush()

        logger.info(
            "Call transition: uuid=%s %s→%s duration=%s",
            call.public_uuid, previous, canonical, call.duration_seconds,
        )

        # Outbox for Timeline + Metrics
        _emit_outbox(self._db, "call.state_changed", {
            "call_uuid": call.public_uuid, "call_id": call.id,
            "previous_status": previous, "new_status": canonical,
            "provider_event_id": provider_event_id,
            "activity_id": activity_id,
            "company_id": call.company_id, "contact_id": call.contact_id,
            "lead_id": call.lead_id,
            "correlation_id": call.correlation_id,
        })

        # On terminal state: queue post-call processing
        if canonical in ("COMPLETED", "FAILED", "MISSED"):
            _emit_outbox(self._db, "call.completed", {
                "call_uuid": call.public_uuid, "call_id": call.id,
                "status": canonical,
                "duration_seconds": call.duration_seconds,
                "company_id": call.company_id, "contact_id": call.contact_id,
                "correlation_id": call.correlation_id,
            })
            # Queue transcription + post-call analysis
            if canonical == "COMPLETED":
                _emit_outbox(self._db, "call.transcription.requested", {
                    "call_uuid": call.public_uuid, "call_id": call.id,
                    "provider_call_id": call.provider_call_id,
                })
                _emit_outbox(self._db, "call.postcall.requested", {
                    "call_uuid": call.public_uuid, "call_id": call.id,
                    "company_id": call.company_id,
                })
            # Queue metrics recalculation
            _emit_outbox(self._db, "call.metrics_recalculation.requested", {
                "call_uuid": call.public_uuid, "company_id": call.company_id,
                "call_id": call.id,
            })
            # Queue timeline projection
            _emit_outbox(self._db, "call.timeline_projection.requested", {
                "call_uuid": call.public_uuid, "call_id": call.id,
                "status": canonical, "company_id": call.company_id,
                "contact_id": call.contact_id,
            })
            # Queue KG ingestion
            _emit_outbox(self._db, "knowledge.call_ingestion.requested", {
                "call_uuid": call.public_uuid, "call_id": call.id,
                "company_id": call.company_id, "contact_id": call.contact_id,
                "duration_seconds": call.duration_seconds,
                "status": canonical, "direction": call.direction,
            })

        return call

    # ── Entity Resolution ──

    def resolve_entities(
        self,
        phone_number: str,
        company_id: int | None = None,
        contact_id: int | None = None,
        organization_id: int = DEFAULT_ORG_ID,
    ) -> dict[str, int | None]:
        """Resolve CRM entities from a phone number within an organization."""
        normalized = _normalize_phone(phone_number)

        # Explicit IDs take priority
        if contact_id:
            contact = self._db.query(Contact).filter(Contact.id == contact_id).first()
            if contact:
                return {"contact_id": contact.id, "company_id": contact.company_id, "lead_id": None}

        # Phone number match on Contact within the org
        if normalized:
            contact = self._db.query(Contact).filter(
                Contact.organization_id == organization_id,
                Contact.status == "active",
            ).filter(
                (Contact.phone == normalized) | (Contact.mobile == normalized)
            ).first()
            if contact:
                return {"contact_id": contact.id, "company_id": contact.company_id, "lead_id": None}

        # Company match on phone
        if normalized:
            company = self._db.query(Company).filter(
                Company.organization_id == organization_id,
                Company.phone == normalized,
                Company.is_archived == False,
            ).first()
            if company:
                return {"contact_id": None, "company_id": company.id, "lead_id": None}

        # Company by explicit ID
        if company_id:
            return {"contact_id": contact_id, "company_id": company_id, "lead_id": None}

        return {"contact_id": None, "company_id": None, "lead_id": None}

    # ── Find or Resume Call ──

    def find_by_provider_id(self, provider_call_id: str) -> Call | None:
        """Idempotent lookup — prevents duplicate calls."""
        return self._db.query(Call).filter(Call.provider_call_id == provider_call_id).first()

    def find_by_uuid(self, public_uuid: str) -> Call | None:
        return self._db.query(Call).filter(Call.public_uuid == public_uuid).first()

    # ── Activity Creation ──

    def _create_activity(self, call: Call, activity_type: str) -> int | None:
        """Create a canonical CRM Activity for a call event."""
        try:
            direction_label = "Outbound" if call.direction == "outbound" else "Inbound"
            duration_str = f" — {call.duration_seconds}s" if call.duration_seconds else ""
            company_id = call.company_id or DEFAULT_ORG_ID

            activity = Activity(
                organization_id=call.organization_id,
                company_id=company_id,
                contact_id=call.contact_id,
                activity_type=activity_type.lower(),
                subject=f"{direction_label} Call {activity_type.replace('_', ' ').title()}",
                body=(
                    f"{direction_label} call to {call.phone_number}{duration_str}. "
                    f"Status: {call.status}. "
                    f"Call UUID: {call.public_uuid}"
                ),
            )
            self._db.add(activity)
            self._db.flush()
            logger.info("Call activity created: call=%s activity_id=%s type=%s", call.public_uuid, activity.id, activity_type)
            return activity.id
        except Exception as exc:
            logger.error("Failed to create call activity: %s", exc)
            return None


# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════

def _normalize_phone(phone: str | None) -> str | None:
    """Normalize to E.164 format."""
    if not phone:
        return None
    import re
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 10:
        return f"+1{digits}"
    if len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"
    return phone


def _emit_outbox(session: Session, event_type: str, payload: dict) -> None:
    """Write a transactional outbox event."""
    evt = OutboxEvent(
        event_type=event_type,
        payload_json=payload,
        correlation_id=payload.get("correlation_id"),
    )
    session.add(evt)
