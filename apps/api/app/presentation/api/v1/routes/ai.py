from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.application.sales.ai_brief import DailyBrief, DailyBriefEngine
from app.application.sales.ai_analysis import CompanyAnalysis, CompanyAnalysisEngine
from app.application.sales.ai_meeting import MeetingPrep, MeetingPrepEngine
from app.application.sales.ai_proposal import ProposalDraft, ProposalBuilderEngine
from app.application.sales.ai_email import EmailDraft, EmailAssistantEngine
from app.application.sales.ai_call import PreCallBrief, PostCallResult, CallAssistantEngine
from app.application.sales.ai_explorer import ExplorerResponse, OpportunityExplorerEngine
from app.application.sales.ai_knowledge import KnowledgeBaseArchitecture
from app.infrastructure.auth.clerk import AuthContext, require_permission
from app.infrastructure.db.models import Company
from app.infrastructure.db.session import get_db_session
from sqlalchemy import select

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/brief", response_model=DailyBrief)
def daily_brief(
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
) -> DailyBrief:
    return DailyBriefEngine(session, ctx.organization_id).generate()


@router.get("/analysis/{company_id}", response_model=CompanyAnalysis)
def company_analysis(
    company_id: int,
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
) -> CompanyAnalysis:
    company = session.execute(
        select(Company).where(Company.id == company_id, Company.organization_id == ctx.organization_id)
    ).scalar_one()
    return CompanyAnalysisEngine(session).analyze(company)


@router.get("/meeting-prep/{company_id}", response_model=MeetingPrep)
def meeting_prep(
    company_id: int,
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
) -> MeetingPrep:
    company = session.execute(
        select(Company).where(Company.id == company_id, Company.organization_id == ctx.organization_id)
    ).scalar_one()
    return MeetingPrepEngine(session).prepare(company)


@router.get("/proposal/{company_id}", response_model=ProposalDraft)
def proposal(
    company_id: int,
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
) -> ProposalDraft:
    company = session.execute(
        select(Company).where(Company.id == company_id, Company.organization_id == ctx.organization_id)
    ).scalar_one()
    return ProposalBuilderEngine(session).build(company)


@router.get("/email/{company_id}", response_model=EmailDraft)
def email_draft(
    company_id: int,
    email_type: str = Query("cold", pattern=r"^(cold|followup|proposal|meeting|reengagement|thank_you|reminder|discovery)$"),
    contact_id: int | None = Query(None),
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
) -> EmailDraft:
    company = session.execute(
        select(Company).where(Company.id == company_id, Company.organization_id == ctx.organization_id)
    ).scalar_one()
    return EmailAssistantEngine(session).generate(company, email_type, contact_id)


@router.get("/call/prep/{company_id}", response_model=PreCallBrief)
def call_prep(
    company_id: int,
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
) -> PreCallBrief:
    company = session.execute(
        select(Company).where(Company.id == company_id, Company.organization_id == ctx.organization_id)
    ).scalar_one()
    return CallAssistantEngine(session).pre_call(company)


@router.post("/call/debrief/{company_id}", response_model=PostCallResult)
def call_debrief(
    company_id: int,
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
) -> PostCallResult:
    company = session.execute(
        select(Company).where(Company.id == company_id, Company.organization_id == ctx.organization_id)
    ).scalar_one()
    return CallAssistantEngine(session).post_call(company)


@router.get("/explorer", response_model=ExplorerResponse)
def explorer(
    q: str = Query(..., min_length=2, description="Natural language search query"),
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
) -> ExplorerResponse:
    return OpportunityExplorerEngine(session, ctx.organization_id).search(q)


@router.get("/knowledge-base")
def knowledge_base(
    ctx: AuthContext = Depends(require_permission("companies:read")),
) -> dict:
    kb = KnowledgeBaseArchitecture()
    return {"overview": kb.get_overview().model_dump(), "playbook": kb.get_playbook(), "mcp_schema": kb.get_mcp_context_schema()}
