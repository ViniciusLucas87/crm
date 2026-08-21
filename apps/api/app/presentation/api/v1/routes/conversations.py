"""
Conversation API — business relationship management.

Conversations aggregate calls, emails, meetings, tasks, and notes
into a single timeline representing an ongoing customer relationship.
"""

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.infrastructure.auth.clerk import AuthContext, require_permission
from app.infrastructure.db.models import Activity, Call, Contact, Conversation, EmailMessage, Task
from app.infrastructure.db.session import get_db_session

logger = logging.getLogger(__name__)
router = APIRouter()

# ── Relationship stages ────────────────────────────────────

RELATIONSHIP_STAGES = [
    "new", "contacted", "discovery", "qualified",
    "proposal", "negotiation", "won", "lost", "dormant",
]

HEALTH_LABELS = {
    range(80, 101): "Healthy",
    range(60, 80): "Warm",
    range(40, 60): "Cold",
    range(20, 40): "At Risk",
    range(0, 20): "Inactive",
}


def _health_label(score: int) -> str:
    for r, label in HEALTH_LABELS.items():
        if score in r:
            return label
    return "Inactive"


def _days_since(value: datetime | None) -> int:
    if not value:
        return 0
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return max(0, (datetime.now(UTC) - value).days)


def _canonical_phone(value: str | None) -> str | None:
    """Normalize a North American contact number for legacy call matching."""
    if not value:
        return None
    digits = "".join(character for character in value if character.isdigit())
    if len(digits) == 10:
        return f"+1{digits}"
    if len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"
    return f"+{digits}" if digits else None


def _conversation_to_dict(c: Conversation) -> dict:
    return {
        "id": c.id,
        "company_id": c.company_id,
        "primary_contact_id": c.primary_contact_id,
        "status": c.status,
        "relationship_stage": c.relationship_stage,
        "opened_by": c.opened_by,
        "owner": c.owner,
        "health_score": c.health_score,
        "health_label": _health_label(c.health_score),
        "summary": c.summary,
        "last_activity_at": str(c.last_activity_at) if c.last_activity_at else None,
        "created_at": str(c.created_at),
        "updated_at": str(c.updated_at),
    }


# ── List / Create ──────────────────────────────────────────

@router.get("/conversations")
def list_conversations(
    company_id: int | None = Query(None),
    stage: str | None = Query(None),
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    """List conversations, optionally filtered by company or stage."""
    stmt = select(Conversation).where(Conversation.organization_id == ctx.organization_id)
    if company_id:
        stmt = stmt.where(Conversation.company_id == company_id)
    if stage:
        stmt = stmt.where(Conversation.relationship_stage == stage)
    stmt = stmt.order_by(Conversation.updated_at.desc()).limit(50)

    conversations = session.execute(stmt).scalars().all()
    return {
        "items": [_conversation_to_dict(c) for c in conversations],
        "total": len(conversations),
        "stages": RELATIONSHIP_STAGES,
    }


@router.post("/conversations")
def create_conversation(
    company_id: int = Query(),
    primary_contact_id: int | None = Query(None),
    owner: str | None = Query(None),
    summary: str | None = Query(None),
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
):
    """Open a new conversation with a company."""
    existing = session.execute(
        select(Conversation).where(
            Conversation.organization_id == ctx.organization_id,
            Conversation.company_id == company_id,
            Conversation.status == "active",
        ).order_by(Conversation.updated_at.desc())
    ).scalars().first()
    if existing:
        return _conversation_to_dict(existing)

    now = datetime.now(UTC)
    conv = Conversation(
        organization_id=ctx.organization_id,
        company_id=company_id,
        primary_contact_id=primary_contact_id,
        status="active",
        relationship_stage="new",
        opened_by=str(getattr(ctx, "user_id", "")) if hasattr(ctx, "user_id") else None,
        owner=owner,
        summary=summary,
        last_activity_at=now,
    )
    session.add(conv)
    session.flush()

    # A company page may be opened after a call or activity was recorded. Attach
    # unlinked company events so Conversation remains the single history view.
    for activity in session.execute(
        select(Activity).where(
            Activity.organization_id == ctx.organization_id,
            Activity.company_id == company_id,
            Activity.conversation_id.is_(None),
        )
    ).scalars():
        activity.conversation_id = conv.id
    for task in session.execute(
        select(Task).where(
            Task.organization_id == ctx.organization_id,
            Task.company_id == company_id,
            Task.conversation_id.is_(None),
        )
    ).scalars():
        task.conversation_id = conv.id
    for call in session.execute(
        select(Call).where(
            Call.organization_id == ctx.organization_id,
            Call.company_id == company_id,
            Call.conversation_id.is_(None),
        )
    ).scalars():
        call.conversation_id = conv.id

    # Browser calls made before a contact was added had no company ID. If their
    # normalized number now matches one contact at this company, backfill them.
    contacts = session.execute(
        select(Contact).where(
            Contact.organization_id == ctx.organization_id,
            Contact.company_id == company_id,
        )
    ).scalars().all()
    phone_contacts: dict[str, list[Contact]] = {}
    for contact in contacts:
        for value in (contact.phone, contact.mobile):
            phone = _canonical_phone(value)
            if phone:
                phone_contacts.setdefault(phone, []).append(contact)
    for call in session.execute(
        select(Call).where(
            Call.organization_id == ctx.organization_id,
            Call.company_id.is_(None),
            Call.conversation_id.is_(None),
        )
    ).scalars():
        match_values = {
            _canonical_phone(value)
            for value in (
                call.phone_number,
                call.normalized_destination_number,
                call.normalized_caller_number,
            )
        }
        matches = {
            contact.id: contact
            for phone in match_values
            if phone
            for contact in phone_contacts.get(phone, [])
        }
        if not matches:
            continue
        call.company_id = company_id
        call.conversation_id = conv.id
        if len(matches) == 1:
            call.contact_id = next(iter(matches.values())).id
    session.commit()
    session.refresh(conv)
    logger.info("Conversation created: id=%s company=%s", conv.id, company_id)
    return _conversation_to_dict(conv)


# ── Single conversation ────────────────────────────────────

@router.get("/conversations/{conversation_id}")
def get_conversation(
    conversation_id: int,
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    """Get a single conversation by ID."""
    conv = session.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.organization_id == ctx.organization_id,
        )
    ).scalar_one_or_none()
    if not conv:
        return {"error": "Conversation not found"}
    return _conversation_to_dict(conv)


@router.patch("/conversations/{conversation_id}")
def update_conversation(
    conversation_id: int,
    stage: str | None = Query(None),
    owner: str | None = Query(None),
    summary: str | None = Query(None),
    health_score: int | None = Query(None),
    primary_contact_id: int | None = Query(None),
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
):
    """Update conversation stage, owner, summary, or health."""
    conv = session.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.organization_id == ctx.organization_id,
        )
    ).scalar_one_or_none()
    if not conv:
        return {"error": "Conversation not found"}

    if stage and stage in RELATIONSHIP_STAGES:
        conv.relationship_stage = stage
    if owner is not None:
        conv.owner = owner
    if summary is not None:
        conv.summary = summary
    if health_score is not None:
        conv.health_score = max(0, min(100, health_score))
    if primary_contact_id is not None:
        conv.primary_contact_id = primary_contact_id

    conv.updated_at = datetime.now(UTC)
    session.commit()
    return _conversation_to_dict(conv)


# ── Conversation timeline ──────────────────────────────────

@router.get("/conversations/{conversation_id}/timeline")
def conversation_timeline(
    conversation_id: int,
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    """Get the aggregated timeline for a conversation."""
    conv = session.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.organization_id == ctx.organization_id,
        )
    ).scalar_one_or_none()
    if not conv:
        return {"error": "Conversation not found"}

    events: list[dict] = []

    # Calls
    calls = session.execute(
        select(Call).where(
            Call.organization_id == ctx.organization_id,
            or_(
                Call.conversation_id == conversation_id,
                (Call.company_id == conv.company_id) & Call.conversation_id.is_(None),
            ),
        ).order_by(Call.created_at.desc()).limit(50)
    ).scalars().all()
    for c in calls:
        events.append({
            "type": "call",
            "id": c.id,
            "timestamp": str(c.created_at),
            "data": {
                "direction": c.direction, "status": c.status,
                "phone_number": c.phone_number, "duration_seconds": c.duration_seconds,
                "recording_url": c.recording_url,
            },
        })

    # Activities
    activities = session.execute(
        select(Activity).where(
            or_(
                Activity.conversation_id == conversation_id,
                (Activity.company_id == conv.company_id) & Activity.conversation_id.is_(None),
            ),
            Activity.id.not_in(
                select(EmailMessage.activity_id).where(
                    EmailMessage.organization_id == ctx.organization_id,
                    EmailMessage.activity_id.is_not(None),
                )
            ),
        ).order_by(Activity.created_at.desc()).limit(50)
    ).scalars().all()
    for a in activities:
        events.append({
            "type": "activity",
            "id": a.id,
            "timestamp": str(a.created_at),
            "data": {"activity_type": a.activity_type, "subject": a.subject},
        })

    # Emails explicitly linked to this conversation, plus older company emails
    # that predate conversation linking. Organization and company scoping keeps
    # the fallback tenant-safe while making historical outreach visible.
    emails = session.execute(
        select(EmailMessage).where(
            EmailMessage.organization_id == ctx.organization_id,
            EmailMessage.company_id == conv.company_id,
            or_(
                EmailMessage.conversation_id == conversation_id,
                EmailMessage.conversation_id.is_(None),
            ),
        ).order_by(EmailMessage.created_at.desc()).limit(50)
    ).scalars().all()
    for email in emails:
        events.append({
            "type": "email",
            "id": email.id,
            "timestamp": str(email.sent_at or email.received_at or email.created_at),
            "data": {
                "direction": email.direction,
                "status": email.status,
                "delivery_status": email.delivery_status,
                "from_address": email.from_address,
                "to_address": email.to_address,
                "subject": email.subject,
                "provider": email.provider,
            },
        })

    # Tasks
    tasks = session.execute(
        select(Task).where(
            Task.organization_id == ctx.organization_id,
            or_(
                Task.conversation_id == conversation_id,
                (Task.company_id == conv.company_id) & Task.conversation_id.is_(None),
            ),
        ).order_by(Task.created_at.desc()).limit(50)
    ).scalars().all()
    for t in tasks:
        events.append({
            "type": "task",
            "id": t.id,
            "timestamp": str(t.created_at),
            "data": {"title": t.title, "status": t.status, "priority": t.priority, "due_date": str(t.due_date)},
        })

    # Sort by timestamp descending
    events.sort(key=lambda e: e["timestamp"], reverse=True)

    return {
        "conversation_id": conversation_id,
        "company_id": conv.company_id,
        "events": events[:50],
        "total_events": len(events),
    }


# ── Conversation statistics ────────────────────────────────

@router.get("/conversations/{conversation_id}/stats")
def conversation_stats(
    conversation_id: int,
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    """Get statistics for a conversation (calls, activities, tasks count)."""
    conv = session.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.organization_id == ctx.organization_id,
        )
    ).scalar_one_or_none()
    if not conv:
        return {"error": "Conversation not found"}

    call_count = session.execute(
        select(func.count(Call.id)).where(
            Call.organization_id == ctx.organization_id,
            or_(
                Call.conversation_id == conversation_id,
                (Call.company_id == conv.company_id) & Call.conversation_id.is_(None),
            ),
        )
    ).scalar() or 0

    activity_count = session.execute(
        select(func.count(Activity.id)).where(
            Activity.organization_id == ctx.organization_id,
            or_(
                Activity.conversation_id == conversation_id,
                (Activity.company_id == conv.company_id) & Activity.conversation_id.is_(None),
            ),
        )
    ).scalar() or 0

    task_count = session.execute(
        select(func.count(Task.id)).where(
            Task.organization_id == ctx.organization_id,
            or_(
                Task.conversation_id == conversation_id,
                (Task.company_id == conv.company_id) & Task.conversation_id.is_(None),
            ),
        )
    ).scalar() or 0

    email_count = session.execute(
        select(func.count(EmailMessage.id)).where(
            EmailMessage.organization_id == ctx.organization_id,
            EmailMessage.company_id == conv.company_id,
            or_(
                EmailMessage.conversation_id == conversation_id,
                EmailMessage.conversation_id.is_(None),
            ),
        )
    ).scalar() or 0

    total_duration = session.execute(
        select(func.sum(Call.duration_seconds)).where(
            Call.organization_id == ctx.organization_id,
            or_(
                Call.conversation_id == conversation_id,
                (Call.company_id == conv.company_id) & Call.conversation_id.is_(None),
            ),
            Call.duration_seconds > 0,
        )
    ).scalar() or 0

    return {
        "conversation_id": conversation_id,
        "call_count": call_count,
        "activity_count": activity_count,
        "email_count": email_count,
        "task_count": task_count,
        "total_events": call_count + activity_count + email_count + task_count,
        "total_call_duration_seconds": total_duration,
        "relationship_stage": conv.relationship_stage,
        "health_score": conv.health_score,
        "health_label": _health_label(conv.health_score),
        "days_active": _days_since(conv.created_at),
    }


# ── Link call/activity/task to conversation ────────────────

@router.post("/conversations/{conversation_id}/link")
def link_to_conversation(
    conversation_id: int,
    call_id: int | None = Query(None),
    activity_id: int | None = Query(None),
    task_id: int | None = Query(None),
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
):
    """Link a call, activity, or task to a conversation."""
    conv = session.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.organization_id == ctx.organization_id,
        )
    ).scalar_one_or_none()
    if not conv:
        return {"error": "Conversation not found"}

    linked: list[str] = []

    if call_id:
        call = session.execute(
            select(Call).where(Call.id == call_id, Call.organization_id == ctx.organization_id)
        ).scalar_one_or_none()
        if call:
            call.conversation_id = conversation_id
            linked.append("call")

    if activity_id:
        activity = session.execute(
            select(Activity).where(Activity.id == activity_id, Activity.organization_id == ctx.organization_id)
        ).scalar_one_or_none()
        if activity:
            activity.conversation_id = conversation_id
            linked.append("activity")

    if task_id:
        task = session.execute(
            select(Task).where(Task.id == task_id, Task.organization_id == ctx.organization_id)
        ).scalar_one_or_none()
        if task:
            task.conversation_id = conversation_id
            linked.append("task")

    if linked:
        conv.last_activity_at = datetime.now(UTC)
        conv.updated_at = datetime.now(UTC)
        session.commit()

    return {"linked": linked, "conversation_id": conversation_id}
