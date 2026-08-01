"""
Decision Maker Intelligence API.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.application.sales.decision_maker import DecisionMakerEngine, DecisionMakerReport
from app.infrastructure.auth.clerk import AuthContext, require_permission
from app.infrastructure.db.models import Company
from app.infrastructure.db.session import get_db_session
from sqlalchemy import select

router = APIRouter(prefix="/decision-maker", tags=["decision-maker"])


@router.get("/{company_id}", response_model=DecisionMakerReport)
def analyze_decision_makers(
    company_id: int,
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
) -> DecisionMakerReport:
    company = session.execute(
        select(Company).where(Company.id == company_id, Company.organization_id == ctx.organization_id)
    ).scalar_one()
    return DecisionMakerEngine(session).analyze(company)
