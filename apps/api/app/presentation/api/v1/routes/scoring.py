from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.application.sales.scoring import OpportunityScoreResult, ScoringEngine
from app.infrastructure.auth.clerk import AuthContext, require_permission
from app.infrastructure.db.models import Company
from app.infrastructure.db.session import get_db_session
from sqlalchemy import select

router = APIRouter()


@router.post("/scoring/{company_id}", response_model=OpportunityScoreResult)
def score_company(
    company_id: int,
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
) -> OpportunityScoreResult:
    company = session.execute(
        select(Company).where(Company.id == company_id, Company.organization_id == ctx.organization_id)
    ).scalar_one()
    return ScoringEngine(session).score_company(company)
