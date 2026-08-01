from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.infrastructure.auth.clerk import AuthContext, require_permission
from app.infrastructure.db.demand_signal import DemandSignal
from app.infrastructure.db.knowledge_graph import KnowledgeEvent, KnowledgeFact, KnowledgeRelationship
from app.infrastructure.db.models import Company, Contact, Lead, Opportunity, Task
from app.infrastructure.db.session import get_db_session

router = APIRouter()


@router.get("/search")
def global_search(
    q: str = Query(min_length=1),
    mode: str = Query(default="keyword", pattern="^(keyword|boolean|semantic|ai)$"),
    industry: str | None = Query(default=None),
    location: str | None = Query(default=None),
    technology: str | None = Query(default=None),
    pain_type: str | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=50),
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    terms = [part.strip() for part in q.split() if part.strip()]
    if mode == "boolean":
        term_filters = [Company.name.ilike(f"%{term}%") for term in terms]
        company_clause = and_(*term_filters) if term_filters else Company.name.ilike(f"%{q}%")
    else:
        company_clause = Company.name.ilike(f"%{q}%")

    pattern = f"%{q}%"
    companies = session.execute(
        select(Company.id, Company.name, Company.industry, Company.city, Company.province, Company.website).where(
            Company.organization_id == ctx.organization_id,
            Company.is_archived.is_(False),
            company_clause,
            Company.industry.ilike(f"%{industry}%") if industry else True,
            or_(Company.city.ilike(f"%{location}%"), Company.province.ilike(f"%{location}%")) if location else True,
            Company.buying_signals.ilike(f"%{technology}%") if technology else True,
        ).limit(limit)
    ).all()
    contacts = session.execute(
        select(Contact.id, Contact.first_name, Contact.last_name, Contact.email, Contact.company_id).where(
            Contact.organization_id == ctx.organization_id,
            or_(Contact.first_name.ilike(pattern), Contact.last_name.ilike(pattern), Contact.email.ilike(pattern))
        ).limit(limit)
    ).all()
    tasks = session.execute(
        select(Task.id, Task.title, Task.status, Task.company_id).where(
            Task.organization_id == ctx.organization_id,
            Task.title.ilike(pattern)
        ).limit(limit)
    ).all()
    leads = session.execute(
        select(Lead.id, Lead.name, Lead.industry, Lead.status).where(
            Lead.organization_id == ctx.organization_id,
            or_(Lead.name.ilike(pattern), Lead.description.ilike(pattern))
        ).limit(limit)
    ).all()
    opportunities = session.execute(
        select(Opportunity.id, Opportunity.title, Opportunity.stage, Opportunity.company_id).where(
            Opportunity.organization_id == ctx.organization_id,
            Opportunity.title.ilike(pattern),
        ).limit(limit)
    ).all()
    signals = session.execute(
        select(DemandSignal.id, DemandSignal.title, DemandSignal.pain_type, DemandSignal.company_name, DemandSignal.lead_score).where(
            or_(DemandSignal.title.ilike(pattern), DemandSignal.content.ilike(pattern)),
            DemandSignal.pain_type == pain_type if pain_type else True,
        ).limit(limit)
    ).all()
    facts = session.execute(
        select(KnowledgeFact.id, KnowledgeFact.entity_type, KnowledgeFact.entity_id, KnowledgeFact.key, KnowledgeFact.value, KnowledgeFact.confidence).where(
            or_(KnowledgeFact.key.ilike(pattern), KnowledgeFact.value.ilike(pattern))
        ).limit(limit)
    ).all()
    events = session.execute(
        select(KnowledgeEvent.id, KnowledgeEvent.entity_type, KnowledgeEvent.entity_id, KnowledgeEvent.event_type, KnowledgeEvent.description).where(
            or_(KnowledgeEvent.event_type.ilike(pattern), KnowledgeEvent.description.ilike(pattern))
        ).limit(limit)
    ).all()
    return {
        "mode": mode,
        "companies": [{"id": c.id, "name": c.name, "industry": c.industry, "city": c.city, "province": c.province, "website": c.website} for c in companies],
        "contacts": [{"id": c.id, "first_name": c.first_name, "last_name": c.last_name, "email": c.email, "company_id": c.company_id} for c in contacts],
        "tasks": [{"id": t.id, "title": t.title, "status": t.status, "company_id": t.company_id} for t in tasks],
        "leads": [{"id": l.id, "name": l.name, "industry": l.industry, "status": l.status} for l in leads],
        "opportunities": [{"id": o.id, "title": o.title, "stage": o.stage, "company_id": o.company_id} for o in opportunities],
        "signals": [{"id": s.id, "title": s.title, "pain_type": s.pain_type, "company_name": s.company_name, "lead_score": s.lead_score} for s in signals],
        "knowledge_facts": [{"id": f.id, "entity_type": f.entity_type, "entity_id": f.entity_id, "key": f.key, "value": f.value, "confidence": f.confidence} for f in facts],
        "knowledge_events": [{"id": e.id, "entity_type": e.entity_type, "entity_id": e.entity_id, "event_type": e.event_type, "description": e.description} for e in events],
    }
