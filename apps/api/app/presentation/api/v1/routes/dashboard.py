from fastapi import APIRouter, Depends

from app.application.dashboard.services import DashboardService
from app.domain.dashboard.entities import DashboardSummary
from app.infrastructure.auth.clerk import AuthContext, require_permission
from app.presentation.api.v1.deps import get_dashboard_service

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(
    context: AuthContext = Depends(require_permission("dashboard:read")),
    service: DashboardService = Depends(get_dashboard_service),
) -> DashboardSummary:
    return service.get_summary(context.organization_id)
