"""
Executive Reports API.

Generates daily, weekly, and monthly executive intelligence reports.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.application.reporting import ExecutiveReportingEngine
from app.infrastructure.auth.clerk import AuthContext, require_permission
from app.infrastructure.db.session import get_db_session

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/{report_type}")
def generate_report(
    report_type: str,
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    """Generate an executive intelligence report (daily, weekly, monthly)."""
    if report_type not in ("daily", "weekly", "monthly"):
        return {"error": "Report type must be: daily, weekly, or monthly"}, 400

    engine = ExecutiveReportingEngine(session, ctx.organization_id)
    report = engine.generate(report_type)

    # Support format parameter
    return report.model_dump()
