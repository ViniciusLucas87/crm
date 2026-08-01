from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.application.sales.discovery import ProspectDiscovery, ResearchQueueService
from app.application.sales.signals import BuyingSignalEngine, SignalResponse
from app.infrastructure.auth.clerk import AuthContext, require_permission
from app.infrastructure.db.session import get_db_session

router = APIRouter()


@router.get("/signals", response_model=SignalResponse)
def get_signals(
    min_score: int = Query(default=50, ge=0, le=100),
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
) -> SignalResponse:
    return BuyingSignalEngine(session).detect(ctx.organization_id, min_score=min_score)


@router.get("/prospects")
def discover_prospects(
    industry: str | None = Query(default=None),
    city: str | None = Query(default=None),
    province: str | None = Query(default=None),
    country: str | None = Query(default=None),
    min_employees: int | None = Query(default=None),
    max_employees: int | None = Query(default=None),
    business_type: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    research_status: str | None = Query(default=None),
    min_score: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    return ProspectDiscovery(session).search(
        ctx.organization_id,
        industry=industry, city=city, province=province, country=country,
        min_employees=min_employees, max_employees=max_employees,
        business_type=business_type, keyword=keyword,
        research_status=research_status, min_score=min_score,
        page=page, page_size=page_size,
    )


@router.get("/research-queue")
def get_research_queue(
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    return ResearchQueueService(session).get_queue(ctx.organization_id)


@router.post("/research-queue/{company_id}/complete")
def mark_researched(
    company_id: int,
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
):
    return ResearchQueueService(session).mark_researched(company_id, ctx.organization_id)
