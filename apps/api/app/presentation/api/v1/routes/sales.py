from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.application.events.bridge import emit
from app.application.workers.events import EventType
from app.application.sales.services import ActivityService, OpportunityService, TaskService
from app.domain.sales.entities import (
    ActivityCreate, ActivityListResponse, ActivityRead, ActivityUpdate,
    OpportunityCreate, OpportunityListResponse, OpportunityRead, OpportunityUpdate,
    TaskCreate, TaskListResponse, TaskRead, TaskUpdate,
)
from app.infrastructure.auth.clerk import AuthContext, require_permission
from app.infrastructure.db.session import get_db_session
from app.presentation.api.v1.deps import get_activity_service, get_opportunity_service, get_task_service

router = APIRouter()

# ── Contacts ──

# ── Activities ──

@router.post("/activities", response_model=ActivityRead)
def create_activity(payload: ActivityCreate, ctx: AuthContext = Depends(require_permission("companies:write")), svc: ActivityService = Depends(get_activity_service), session: Session = Depends(get_db_session)) -> ActivityRead:
    result = svc.create(payload, ctx.organization_id)
    emit(session, EventType.ACTIVITY_LOGGED, "activity", result.id, {"company_id": result.company_id, "type": result.activity_type})
    return result

@router.get("/activities", response_model=ActivityListResponse)
def list_activities(company_id: int | None = Query(default=None), page: int = Query(default=1, ge=1), page_size: int = Query(default=20, ge=1, le=100), activity_type: str | None = Query(default=None), ctx: AuthContext = Depends(require_permission("companies:read")), svc: ActivityService = Depends(get_activity_service)) -> ActivityListResponse:
    return svc.list(ctx.organization_id, company_id, page, page_size, activity_type)

@router.patch("/activities/{activity_id}", response_model=ActivityRead)
def update_activity(activity_id: int, payload: ActivityUpdate, ctx: AuthContext = Depends(require_permission("companies:write")), svc: ActivityService = Depends(get_activity_service)) -> ActivityRead:
    return svc.update(activity_id, payload, ctx.organization_id)

# ── Tasks ──

@router.post("/tasks", response_model=TaskRead)
def create_task(payload: TaskCreate, ctx: AuthContext = Depends(require_permission("companies:write")), svc: TaskService = Depends(get_task_service), session: Session = Depends(get_db_session)) -> TaskRead:
    result = svc.create(payload, ctx.organization_id)
    emit(session, EventType.TASK_CREATED, "task", result.id, {"company_id": result.company_id, "priority": result.priority})
    return result

@router.get("/tasks", response_model=TaskListResponse)
def list_tasks(company_id: int | None = Query(default=None), page: int = Query(default=1, ge=1), page_size: int = Query(default=20, ge=1, le=100), status: str | None = Query(default=None), priority: str | None = Query(default=None), ctx: AuthContext = Depends(require_permission("companies:read")), svc: TaskService = Depends(get_task_service)) -> TaskListResponse:
    return svc.list(ctx.organization_id, company_id, page, page_size, status, priority)

@router.patch("/tasks/{task_id}", response_model=TaskRead)
def update_task(task_id: int, payload: TaskUpdate, ctx: AuthContext = Depends(require_permission("companies:write")), svc: TaskService = Depends(get_task_service), session: Session = Depends(get_db_session)) -> TaskRead:
    result = svc.update(task_id, payload, ctx.organization_id)
    if getattr(result, "is_completed", False) or getattr(result, "status", None) == "completed":
        emit(session, EventType.TASK_COMPLETED, "task", result.id, {"company_id": result.company_id})
    return result

# ── Opportunities ──

@router.post("/opportunities", response_model=OpportunityRead)
def create_opportunity(payload: OpportunityCreate, ctx: AuthContext = Depends(require_permission("companies:write")), svc: OpportunityService = Depends(get_opportunity_service), session: Session = Depends(get_db_session)) -> OpportunityRead:
    result = svc.create(payload, ctx.organization_id)
    emit(session, EventType.OPPORTUNITY_CREATED, "opportunity", result.id, {"company_id": result.company_id, "stage": result.stage})
    return result

@router.get("/opportunities", response_model=OpportunityListResponse)
def list_opportunities(company_id: int | None = Query(default=None), page: int = Query(default=1, ge=1), page_size: int = Query(default=20, ge=1, le=100), stage: str | None = Query(default=None), ctx: AuthContext = Depends(require_permission("companies:read")), svc: OpportunityService = Depends(get_opportunity_service)) -> OpportunityListResponse:
    return svc.list(ctx.organization_id, company_id, page, page_size, stage)

@router.patch("/opportunities/{opportunity_id}", response_model=OpportunityRead)
def update_opportunity(opportunity_id: int, payload: OpportunityUpdate, ctx: AuthContext = Depends(require_permission("companies:write")), svc: OpportunityService = Depends(get_opportunity_service), session: Session = Depends(get_db_session)) -> OpportunityRead:
    result = svc.update(opportunity_id, payload, ctx.organization_id)
    emit(session, EventType.OPPORTUNITY_UPDATED, "opportunity", result.id, {"stage": result.stage, "status": result.status})
    if getattr(result, "stage", None) == "won":
        emit(session, EventType.OPPORTUNITY_WON, "opportunity", result.id, {"company_id": result.company_id})
    if getattr(result, "stage", None) == "lost":
        emit(session, EventType.OPPORTUNITY_LOST, "opportunity", result.id, {"company_id": result.company_id})
    return result
