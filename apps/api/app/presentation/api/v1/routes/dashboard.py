from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.application.dashboard.services import DashboardService
from app.application.dashboard.today_service import TodayService
from app.domain.dashboard.entities import DashboardSummary
from app.domain.dashboard.today_entities import (
    FollowUpRequest,
    FollowUpResponse,
    TodayWorkspaceResponse,
)
from app.infrastructure.auth.clerk import AuthContext, require_permission
from app.infrastructure.db.session import get_db_session
from app.presentation.api.v1.deps import get_dashboard_service

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(
    context: AuthContext = Depends(require_permission("dashboard:read")),
    service: DashboardService = Depends(get_dashboard_service),
) -> DashboardSummary:
    return service.get_summary(context.organization_id)


@router.post("/replies/{email_id}/acknowledge")
def acknowledge_reply(
    email_id: int,
    context: AuthContext = Depends(require_permission("companies:write")),
    db: Session = Depends(get_db_session),
):
    """Acknowledge an inbound reply so it leaves the Today queue."""
    service = TodayService(db, context.organization_id)
    try:
        return service.acknowledge_reply(email_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/today", response_model=TodayWorkspaceResponse)
def today_workspace(
    context: AuthContext = Depends(require_permission("dashboard:read")),
    db: Session = Depends(get_db_session),
) -> TodayWorkspaceResponse:
    """Get the Today workspace — all attention items for the current tenant."""
    service = TodayService(db, context.organization_id)
    return service.get_workspace()


@router.post("/leads/{lead_id}/assign-next-step", response_model=FollowUpResponse)
def lead_assign_next_step(
    lead_id: int,
    request: FollowUpRequest,
    context: AuthContext = Depends(require_permission("companies:write")),
    db: Session = Depends(get_db_session),
) -> FollowUpResponse:
    service = TodayService(db, context.organization_id)
    try:
        return service.assign_next_step(lead_id, request, actor_user_id=context.user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tasks/{task_id}/follow-up", response_model=FollowUpResponse)
def task_follow_up(
    task_id: int,
    request: FollowUpRequest,
    context: AuthContext = Depends(require_permission("companies:write")),
    db: Session = Depends(get_db_session),
) -> FollowUpResponse:
    service = TodayService(db, context.organization_id)
    try:
        if request.action == "complete":
            return service.complete_follow_up(task_id, request, actor_user_id=context.user_id)
        elif request.action == "reschedule":
            return service.reschedule_follow_up(task_id, request, actor_user_id=context.user_id)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {request.action}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
