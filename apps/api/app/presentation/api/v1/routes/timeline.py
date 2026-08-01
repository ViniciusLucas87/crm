from fastapi import APIRouter, Depends, Query

from app.application.sales.timeline_service import TimelineService
from app.domain.sales.timeline import TimelineResponse
from app.infrastructure.auth.clerk import AuthContext, require_permission
from app.presentation.api.v1.deps import get_timeline_service

router = APIRouter()


@router.get("/timeline", response_model=TimelineResponse)
def get_timeline(
    company_id: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=30, ge=1, le=100),
    ctx: AuthContext = Depends(require_permission("companies:read")),
    svc: TimelineService = Depends(get_timeline_service),
) -> TimelineResponse:
    return svc.get_timeline(ctx.organization_id, company_id=company_id, page=page, page_size=page_size)
