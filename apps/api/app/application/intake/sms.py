"""
SMS sending, delivery tracking, and phone suppression (STOP/START).
Transactional only. No promotional messaging.
"""

import logging
import os
from datetime import UTC, datetime

logger = logging.getLogger(__name__)

MISSED_CALL_SMS_MESSAGE = (
    "Hi, this is Pacific North Systems. Sorry we missed your call. "
    "We received your message and will call you back shortly. "
    "Reply with your name and what you need if that is easier. "
    "Reply STOP to opt out."
)


def is_phone_suppressed(db_session, organization_id: int, normalized_phone: str) -> bool:
    """Check if a phone number is opted out from SMS."""
    from app.infrastructure.db.models import PhoneSuppression

    row = db_session.query(PhoneSuppression).filter(
        PhoneSuppression.organization_id == organization_id,
        PhoneSuppression.normalized_phone == normalized_phone,
        PhoneSuppression.status == "suppressed",
    ).first()
    return row is not None


def suppress_phone(
    db_session,
    organization_id: int,
    normalized_phone: str,
    reason: str = "STOP",
    source_event_id: str | None = None,
) -> None:
    """Durably opt out a phone number. Idempotent upsert. Caller owns commit."""
    from app.infrastructure.db.models import PhoneSuppression
    from sqlalchemy.dialects.postgresql import insert

    stmt = insert(PhoneSuppression).values(
        organization_id=organization_id,
        phone_number=normalized_phone,
        normalized_phone=normalized_phone,
        status="suppressed",
        reason=reason[:50],
        source_event_id=source_event_id,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["organization_id", "normalized_phone"],
        set_={
            "status": "suppressed",
            "reason": reason[:50],
            "source_event_id": source_event_id,
            "updated_at": datetime.now(UTC),
        },
    )
    db_session.execute(stmt)
    # Caller must commit


def remove_suppression(
    db_session,
    organization_id: int,
    normalized_phone: str,
) -> None:
    """Remove opt-out (START). Caller owns commit."""
    from app.infrastructure.db.models import PhoneSuppression

    suppressed = db_session.query(PhoneSuppression).filter(
        PhoneSuppression.organization_id == organization_id,
        PhoneSuppression.normalized_phone == normalized_phone,
    ).first()
    if suppressed:
        suppressed.status = "active"
        suppressed.updated_at = datetime.now(UTC)
    # Caller must commit


def can_send_sms(db_session, organization_id: int, normalized_phone: str) -> tuple[bool, str]:
    """Check if SMS can be sent to this phone.
    Returns (can_send, reason).
    """
    if not normalized_phone:
        return False, "no_phone_number"
    if is_phone_suppressed(db_session, organization_id, normalized_phone):
        return False, "phone_suppressed"
    return True, "ok"
