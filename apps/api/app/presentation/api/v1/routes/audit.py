"""Audit API — read-only, organization-scoped access to the FollowUpAction ledger."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from app.infrastructure.auth.clerk import AuthContext, require_permission
from app.infrastructure.db.session import get_db_session
from app.infrastructure.db.models import FollowUpAction

router = APIRouter()


class AuditEntryResponse(BaseModel):
    id: int
    actor_user_id: Optional[str] = None
    idempotency_key: str
    entity_type: str
    entity_id: int
    action: str
    old_state: Optional[str] = None
    new_state: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditListResponse(BaseModel):
    entries: list[AuditEntryResponse]
    total: int
    page: int
    page_size: int


@router.get("/audit", response_model=AuditListResponse)
def list_audit_entries(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    entity_type: Optional[str] = Query(None, description="Filter by entity type: task, lead"),
    entity_id: Optional[int] = Query(None, description="Filter by entity ID"),
    action: Optional[str] = Query(None, description="Filter by action: completed, rescheduled, assigned"),
    context: AuthContext = Depends(require_permission("dashboard:read")),
    db: Session = Depends(get_db_session),
) -> AuditListResponse:
    """List follow-up audit entries for the authenticated organization.
    Append-only: no update or delete endpoints exist."""
    query = db.query(FollowUpAction).filter(
        FollowUpAction.organization_id == context.organization_id,
    )
    if entity_type:
        query = query.filter(FollowUpAction.entity_type == entity_type)
    if entity_id is not None:
        query = query.filter(FollowUpAction.entity_id == entity_id)
    if action:
        query = query.filter(FollowUpAction.action == action)

    total = query.count()
    entries = (
        query.order_by(FollowUpAction.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return AuditListResponse(
        entries=[AuditEntryResponse.model_validate(e) for e in entries],
        total=total,
        page=page,
        page_size=page_size,
    )
