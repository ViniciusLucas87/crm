"""
Telemetry API.

Provides observability data for admin dashboard.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.infrastructure.auth.clerk import AuthContext, require_permission
from app.infrastructure.db.session import get_db_session
from app.infrastructure.telemetry import get_telemetry

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.get("/stats")
def telemetry_stats(
    days: int = Query(7, ge=1, le=90),
    ctx: AuthContext = Depends(require_permission("companies:read")),
):
    """Get telemetry statistics for the dashboard."""
    return get_telemetry().get_stats(ctx.organization_id, days)


@router.get("/health")
def ai_health(
    ctx: AuthContext = Depends(require_permission("companies:read")),
):
    """Get current AI health score."""
    stats = get_telemetry().get_stats(ctx.organization_id, 1)
    return {
        "health_score": stats["health_score"],
        "success_rate": stats["success_rate"],
        "fallback_rate": stats["fallback_rate"],
        "avg_latency_ms": stats["avg_latency_ms"],
        "total_requests_today": stats["total_requests"],
        "total_cost_today": stats["total_cost"],
    }
