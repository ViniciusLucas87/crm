"""
Lead Intelligence API — Complete AI Sales Research Workspace.

Endpoints:
  CRUD, status workflow, bulk operations
  Research pipeline (start, progress, run stages, retry)
  Outreach generation
  Timeline
  Tags, notes
  Saved searches
  Smart CRM import with optional actions
  Analytics
  Comparison
"""

import json
import os
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from app.application.llm.enrichment import EnrichmentService
from app.application.sales.outreach import OutreachGenerator
from app.application.sales.research_pipeline import ResearchPipeline, RESEARCH_STAGES, STAGE_STATUSES
from app.application.sales.scoring import ScoringEngine
from app.infrastructure.auth.clerk import AuthContext, require_permission
from app.infrastructure.db.models import Company, Contact, Lead, LeadTimelineEvent, Opportunity, SavedSearch
from app.infrastructure.db.session import get_db_session

router = APIRouter(prefix="/leads", tags=["leads"])

# ── Helpers ──

LEAD_STATUSES = ("new", "researching", "ready_for_review", "needs_more_research", "approved", "rejected", "archived", "imported")

DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY", "")


def _lead_dict(lead: Lead) -> dict[str, Any]:
    return {
        "id": lead.id, "name": lead.name, "industry": lead.industry,
        "website": lead.website, "employees": lead.employees, "city": lead.city,
        "province": lead.province, "country": lead.country,
        "linkedin_url": lead.linkedin_url, "description": lead.description,
        "revenue_estimate": lead.revenue_estimate,
        "opportunity_score": lead.opportunity_score, "confidence_score": lead.confidence_score,
        "pns_fit_score": lead.pns_fit_score,
        "pns_fit_data": lead.pns_fit_data,
        "enrichment_status": lead.enrichment_status,
        "google_maps_data": lead.google_maps_data,
        "product_recommendation_data": lead.product_recommendation_data,
        "website_data": lead.website_data,
        "reviews_data": lead.reviews_data,
        "linkedin_data": lead.linkedin_data,
        "buying_signals": lead.buying_signals, "recommended_services": lead.recommended_services,
        "estimated_value": lead.estimated_value,
        "estimated_deal_low": lead.estimated_deal_low,
        "estimated_deal_high": lead.estimated_deal_high,
        "technology_maturity": lead.technology_maturity,
        "status": lead.status, "source": lead.source, "tags": lead.tags,
        "notes": lead.notes, "executive_summary": lead.executive_summary,
        "research_stages": lead.research_stages,
        "decision_makers_data": lead.decision_makers_data,
        "outreach_data": lead.outreach_data,
        "last_researched_at": str(lead.last_researched_at) if lead.last_researched_at else None,
        "imported_company_id": lead.imported_company_id,
        "research_data": lead.research_data,  # explainability JSON
        "created_at": str(lead.created_at), "updated_at": str(lead.updated_at),
    }


def _get_enrichment() -> EnrichmentService:
    return EnrichmentService(api_key=DEEPSEEK_KEY)


# ── Request Models ──

class LeadCreate(BaseModel):
    name: str
    industry: str = ""
    website: str = ""
    employees: int | None = None
    city: str = ""
    province: str = ""
    country: str = ""
    source: str = "manual"
    tags: str = ""
    description: str = ""


class LeadUpdate(BaseModel):
    name: str | None = None
    industry: str | None = None
    website: str | None = None
    employees: int | None = None
    city: str | None = None
    province: str | None = None
    country: str | None = None
    description: str | None = None
    tags: str | None = None
    notes: str | None = None
    linkedin_url: str | None = None


class BulkAction(BaseModel):
    ids: list[int]
    status: str | None = None
    action: str = ""  # "approve", "reject", "archive", "export"


class SmartImport(BaseModel):
    create_company: bool = True
    create_contacts: bool = True
    create_opportunity: bool = True
    launch_enrichment: bool = True
    generate_analysis: bool = False
    generate_proposal: bool = False
    generate_outreach: bool = False
    assign_owner: str = ""


class SavedSearchCreate(BaseModel):
    name: str
    filters_json: str  # JSON string


# ═══════════════════════════════════════════════════════════
# LIST / CREATE
# ═══════════════════════════════════════════════════════════

@router.get("/")
def list_leads(
    status: str = "",
    search: str = "",
    industry: str = "",
    tag: str = "",
    min_score: int | None = None,
    sort: str = "created_at_desc",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, le=100),
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    stmt = select(Lead).where(Lead.organization_id == ctx.organization_id)
    if status: stmt = stmt.where(Lead.status == status)
    if search: stmt = stmt.where(or_(Lead.name.ilike(f"%{search}%"), Lead.industry.ilike(f"%{search}%")))
    if industry: stmt = stmt.where(Lead.industry.ilike(f"%{industry}%"))
    if tag: stmt = stmt.where(Lead.tags.ilike(f"%{tag}%"))
    if min_score is not None: stmt = stmt.where(Lead.opportunity_score >= min_score)

    # Sorting
    sort_map = {
        "created_at_desc": Lead.created_at.desc(),
        "created_at_asc": Lead.created_at.asc(),
        "score_desc": Lead.opportunity_score.desc().nullslast(),
        "score_asc": Lead.opportunity_score.asc().nullslast(),
        "pns_fit_desc": Lead.pns_fit_score.desc().nullslast(),
        "pns_fit_asc": Lead.pns_fit_score.asc().nullslast(),
        "name_asc": Lead.name.asc(),
        "name_desc": Lead.name.desc(),
    }
    order = sort_map.get(sort, Lead.created_at.desc())

    # Total (filtered)
    total = session.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    leads = session.execute(stmt.order_by(order).offset((page - 1) * page_size).limit(page_size)).scalars().all()

    return {
        "items": [_lead_dict(l) for l in leads],
        "total": total, "page": page, "page_size": page_size,
    }


@router.post("/")
def create_lead(
    body: LeadCreate,
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
):
    lead = Lead(
        organization_id=ctx.organization_id, name=body.name,
        industry=body.industry or None, website=body.website or None,
        employees=body.employees, city=body.city or None,
        province=body.province or None, country=body.country or None,
        source=body.source, tags=body.tags or None,
        description=body.description or None,
    )
    session.add(lead); session.commit(); session.refresh(lead)
    # Add timeline event
    session.add(LeadTimelineEvent(
        organization_id=ctx.organization_id, lead_id=lead.id,
        event_type="created", description=f"Lead created via {body.source}",
    ))
    session.commit()
    from app.application.events.bridge import emit
    from app.application.workers.events import EventType
    emit(session, EventType.LEAD_IMPORTED, "lead", lead.id, {"name": lead.name, "source": body.source})
    return _lead_dict(lead)


# ═══════════════════════════════════════════════════════════
# GET / UPDATE / DELETE
# ═══════════════════════════════════════════════════════════

@router.get("/{lead_id}")
def get_lead(
    lead_id: int,
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    lead = session.execute(
        select(Lead).where(Lead.id == lead_id, Lead.organization_id == ctx.organization_id)
    ).scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return _lead_dict(lead)


@router.patch("/{lead_id}")
def update_lead(
    lead_id: int,
    body: LeadUpdate,
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
):
    lead = session.execute(
        select(Lead).where(Lead.id == lead_id, Lead.organization_id == ctx.organization_id)
    ).scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(lead, field, value)

    session.add(lead)
    session.add(LeadTimelineEvent(
        organization_id=ctx.organization_id, lead_id=lead.id,
        event_type="updated", description="Lead details updated",
    ))
    session.commit()
    return _lead_dict(lead)


# ═══════════════════════════════════════════════════════════
# STATUS WORKFLOW
# ═══════════════════════════════════════════════════════════

@router.post("/{lead_id}/status")
def update_status(
    lead_id: int,
    status: str = Query(...),
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
):
    if status not in LEAD_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {LEAD_STATUSES}")
    lead = session.execute(
        select(Lead).where(Lead.id == lead_id, Lead.organization_id == ctx.organization_id)
    ).scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    old_status = lead.status
    lead.status = status
    session.add(lead)
    session.add(LeadTimelineEvent(
        organization_id=ctx.organization_id, lead_id=lead.id,
        event_type="status_changed",
        description=f"Status changed: {old_status} → {status}",
        metadata_json=json.dumps({"from": old_status, "to": status}),
    ))
    session.commit()
    return {"id": lead.id, "status": lead.status, "previous": old_status}


# ═══════════════════════════════════════════════════════════
# BULK OPERATIONS
# ═══════════════════════════════════════════════════════════

@router.post("/bulk")
def bulk_action(
    body: BulkAction,
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
):
    if not body.ids:
        raise HTTPException(status_code=400, detail="No lead IDs provided")

    leads = session.execute(
        select(Lead).where(Lead.id.in_(body.ids), Lead.organization_id == ctx.organization_id)
    ).scalars().all()

    results: list[dict] = []
    for lead in leads:
        old = lead.status
        if body.action == "approve":
            lead.status = "approved"
        elif body.action == "reject":
            lead.status = "rejected"
        elif body.action == "archive":
            lead.status = "archived"
        elif body.status:
            lead.status = body.status
        session.add(lead)
        session.add(LeadTimelineEvent(
            organization_id=ctx.organization_id, lead_id=lead.id,
            event_type="bulk_action",
            description=f"Bulk {body.action or body.status}: {old} → {lead.status}",
        ))
        results.append({"id": lead.id, "status": lead.status, "previous": old})

    session.commit()
    return {"updated": len(results), "results": results}


# ═══════════════════════════════════════════════════════════
# SMART CRM IMPORT
# ═══════════════════════════════════════════════════════════

@router.post("/{lead_id}/import")
def import_to_crm(
    lead_id: int,
    options: SmartImport = SmartImport(),
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
):
    lead = session.execute(
        select(Lead).where(Lead.id == lead_id, Lead.organization_id == ctx.organization_id, Lead.status == "approved")
    ).scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=400, detail="Lead not found or not approved")

    existing = session.execute(
        select(Company).where(
            Company.organization_id == ctx.organization_id,
            Company.name == lead.name, Company.is_archived.is_(False),
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail=f"Company '{lead.name}' already exists in CRM")

    result: dict[str, Any] = {"lead_id": lead.id, "lead_name": lead.name}

    # ── Create Company with ALL lead intelligence ──
    if options.create_company:
        company = Company(
            organization_id=ctx.organization_id,
            name=lead.name,
            industry=lead.industry,
            website=lead.website,
            employees=lead.employees,
            city=lead.city,
            province=lead.province,
            country=lead.country,
            description=lead.description or lead.executive_summary,
            linkedin_url=lead.linkedin_url,
            opportunity_score=lead.opportunity_score,
            confidence_score=lead.confidence_score,
            buying_signals=lead.buying_signals,
            source_history=json.dumps({
                "lead_id": lead.id,
                "source": lead.source,
                "website_data": lead.website_data,
                "research_data": lead.research_data,
                "decision_makers_data": lead.decision_makers_data,
                "pns_fit_data": lead.pns_fit_data,
            }),
            research_status="enriching",
            status="lead",
            owner=options.assign_owner or None,
            notes=lead.notes,
        )
        session.add(company); session.commit(); session.refresh(company)
        lead.imported_company_id = company.id
        result["company_id"] = company.id
        result["company_name"] = company.name

        # Import only attributable decision makers. A name without a source or
        # contact channel is not sufficient evidence to create a CRM contact.
        if options.create_contacts and lead.decision_makers_data:
            try:
                decision_data = json.loads(lead.decision_makers_data)
                candidates = decision_data.get("decision_makers", []) if isinstance(decision_data, dict) else decision_data
            except (json.JSONDecodeError, TypeError):
                candidates = []
            created_contacts = []
            for candidate in candidates if isinstance(candidates, list) else []:
                if not isinstance(candidate, dict):
                    continue
                full_name = str(candidate.get("name") or "").strip()
                source_url = str(candidate.get("source_url") or "").strip()
                email = str(candidate.get("email") or "").strip() or None
                phone = str(candidate.get("phone") or "").strip() or None
                linkedin = str(candidate.get("linkedin") or candidate.get("linkedin_url") or "").strip() or None
                if not full_name or full_name.lower() in {"unknown", "n/a", "none"}:
                    continue
                if not (source_url or email or phone or linkedin):
                    continue
                names = full_name.split(maxsplit=1)
                contact = Contact(
                    organization_id=ctx.organization_id,
                    company_id=company.id,
                    first_name=names[0],
                    last_name=names[1] if len(names) > 1 else "",
                    job_title=str(candidate.get("role") or candidate.get("title") or "").strip() or None,
                    email=email,
                    phone=phone,
                    linkedin=linkedin,
                    is_decision_maker=True,
                    is_primary=not created_contacts,
                    confidence=str(candidate.get("confidence") or "researched")[:20],
                    discovery_source="lead_web_research",
                    notes=f"Research source: {source_url}" if source_url else "Imported from lead research evidence",
                )
                session.add(contact)
                session.flush()
                created_contacts.append(contact.id)
            if created_contacts:
                result["contact_ids"] = created_contacts

        # Timeline event
        session.add(LeadTimelineEvent(
            organization_id=ctx.organization_id, lead_id=lead.id,
            event_type="imported",
            description=f"Imported + Enriched to CRM as Company #{company.id}",
        ))

        # ── Create Opportunity ──
        if options.create_opportunity:
            estimated = lead.estimated_deal_low or 0
            opportunity = Opportunity(
                organization_id=ctx.organization_id, company_id=company.id,
                title=f"{lead.name} — Initial Engagement",
                estimated_value=estimated, probability=lead.opportunity_score or 30,
                stage="lead", status="active",
                owner=options.assign_owner or None,
            )
            session.add(opportunity); session.commit()
            result["opportunity_id"] = opportunity.id

        # ── Launch background enrichment via Celery worker ──
        if options.launch_enrichment:
            try:
                from app.application.llm.enrichment import EnrichmentService
                enrichment = EnrichmentService(api_key=os.getenv("DEEPSEEK_API_KEY", os.getenv("OPENAI_API_KEY", "")))
                # Fire-and-forget: the worker handles the actual enrichment
                enrichment_data = {
                    "company_name": company.name,
                    "website": company.website,
                    "industry": company.industry,
                    "city": company.city,
                    "province": company.province,
                    "lead_id": lead.id,
                }
                enrichment.enrich_company_background(
                    company_id=company.id,
                    organization_id=ctx.organization_id,
                    lead_data=enrichment_data,
                    existing_data={
                        "description": company.description,
                        "employees": company.employees,
                        "linkedin_url": company.linkedin_url,
                        "buying_signals": company.buying_signals,
                        "opportunity_score": company.opportunity_score,
                    },
                )
                lead.enrichment_status = "enriching"
                result["enrichment"] = "launched"
            except Exception as e:
                result["enrichment"] = f"deferred: {e}"
                lead.enrichment_status = "pending"

    lead.status = "imported"
    session.add(lead)
    session.add(LeadTimelineEvent(
        organization_id=ctx.organization_id, lead_id=lead.id,
        event_type="workflow_complete",
        description="Import + Enrich workflow completed",
        metadata_json=json.dumps(options.model_dump()),
    ))
    session.commit()

    from app.application.events.bridge import emit
    from app.application.workers.events import EventType
    emit(session, EventType.LEAD_CONVERTED, "lead", lead_id, {"company_id": result.get("company_id"), "opportunity_id": result.get("opportunity_id")})
    if result.get("company_id"):
        emit(session, EventType.COMPANY_CREATED, "company", result["company_id"], {"name": result.get("company_name", lead.name)})
    if result.get("opportunity_id"):
        emit(session, EventType.OPPORTUNITY_CREATED, "opportunity", result["opportunity_id"])

    return {"status": "imported", **result}


# ═══════════════════════════════════════════════════════════
# RESEARCH PIPELINE
# ═══════════════════════════════════════════════════════════

@router.get("/{lead_id}/research/progress")
def get_research_progress(
    lead_id: int,
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    lead = session.execute(
        select(Lead).where(Lead.id == lead_id, Lead.organization_id == ctx.organization_id)
    ).scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    pipeline = ResearchPipeline(session)
    return pipeline.get_progress(lead)


@router.post("/{lead_id}/research/start")
def start_research(
    lead_id: int,
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
):
    lead = session.execute(
        select(Lead).where(Lead.id == lead_id, Lead.organization_id == ctx.organization_id)
    ).scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    pipeline = ResearchPipeline(session)
    return pipeline.start_pipeline(lead, ctx.organization_id)


@router.post("/{lead_id}/research/run")
async def run_research_stage(
    lead_id: int,
    stage: str = Query(...),
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
):
    lead = session.execute(
        select(Lead).where(Lead.id == lead_id, Lead.organization_id == ctx.organization_id)
    ).scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    pipeline = ResearchPipeline(session, _get_enrichment())
    return await pipeline.run_stage(lead, ctx.organization_id, stage)


@router.post("/{lead_id}/research/run-all")
async def run_full_research(
    lead_id: int,
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
):
    lead = session.execute(
        select(Lead).where(Lead.id == lead_id, Lead.organization_id == ctx.organization_id)
    ).scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    pipeline = ResearchPipeline(session, _get_enrichment())
    return await pipeline.run_full_pipeline(lead, ctx.organization_id)


@router.post("/{lead_id}/research/retry")
def retry_stage(
    lead_id: int,
    stage: str = Query(...),
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
):
    lead = session.execute(
        select(Lead).where(Lead.id == lead_id, Lead.organization_id == ctx.organization_id)
    ).scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    pipeline = ResearchPipeline(session)
    return pipeline.retry_stage(lead, ctx.organization_id, stage)


@router.post("/research/bulk")
async def research_bulk(
    body: BulkAction,
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
):
    """Run the complete research pipeline for multiple selected leads."""
    leads = session.execute(
        select(Lead).where(Lead.id.in_(body.ids), Lead.organization_id == ctx.organization_id)
    ).scalars().all()

    pipeline = ResearchPipeline(session, _get_enrichment())
    results = []
    for lead in leads:
        r = await pipeline.run_full_pipeline(lead, ctx.organization_id)
        results.append({"id": lead.id, "status": lead.status, "percent": r["percent"]})

    return {"completed": len(results), "results": results}


# ═══════════════════════════════════════════════════════════
# OUTREACH
# ═══════════════════════════════════════════════════════════

@router.post("/{lead_id}/outreach/generate")
async def generate_outreach(
    lead_id: int,
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
):
    lead = session.execute(
        select(Lead).where(Lead.id == lead_id, Lead.organization_id == ctx.organization_id)
    ).scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    gen = OutreachGenerator(_get_enrichment())
    outreach = await gen.generate(lead)

    # Save to lead
    lead.outreach_data = json.dumps(outreach)
    session.add(lead)
    session.add(LeadTimelineEvent(
        organization_id=ctx.organization_id, lead_id=lead.id,
        event_type="outreach_generated", description="Outreach content generated",
    ))
    session.commit()

    return {"lead_id": lead.id, "outreach": outreach}


@router.put("/{lead_id}/outreach")
def save_outreach(
    lead_id: int,
    body: dict,
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
):
    """Save user-edited outreach content."""
    lead = session.execute(
        select(Lead).where(Lead.id == lead_id, Lead.organization_id == ctx.organization_id)
    ).scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead.outreach_data = json.dumps(body)
    session.add(lead); session.commit()
    return {"status": "saved"}


# ═══════════════════════════════════════════════════════════
# TIMELINE
# ═══════════════════════════════════════════════════════════

@router.get("/{lead_id}/timeline")
def get_timeline(
    lead_id: int,
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    events = session.execute(
        select(LeadTimelineEvent)
        .where(LeadTimelineEvent.lead_id == lead_id, LeadTimelineEvent.organization_id == ctx.organization_id)
        .order_by(LeadTimelineEvent.created_at.desc())
        .limit(100)
    ).scalars().all()

    return {
        "lead_id": lead_id,
        "events": [
            {
                "id": e.id, "event_type": e.event_type,
                "description": e.description,
                "metadata": json.loads(e.metadata_json) if e.metadata_json else None,
                "created_at": str(e.created_at),
            }
            for e in events
        ],
    }


# ═══════════════════════════════════════════════════════════
# COMPARISON
# ═══════════════════════════════════════════════════════════

@router.get("/compare/{id_a}/{id_b}")
def compare_leads(
    id_a: int,
    id_b: int,
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    a = session.execute(
        select(Lead).where(Lead.id == id_a, Lead.organization_id == ctx.organization_id)
    ).scalar_one_or_none()
    b = session.execute(
        select(Lead).where(Lead.id == id_b, Lead.organization_id == ctx.organization_id)
    ).scalar_one_or_none()
    if not a or not b:
        raise HTTPException(status_code=404, detail="One or both leads not found")

    return {
        "a": _lead_dict(a),
        "b": _lead_dict(b),
        "comparison": {
            "score_delta": (a.opportunity_score or 0) - (b.opportunity_score or 0),
            "winner": a.name if (a.opportunity_score or 0) > (b.opportunity_score or 0) else b.name,
        },
    }


# ═══════════════════════════════════════════════════════════
# SAVED SEARCHES
# ═══════════════════════════════════════════════════════════

@router.get("/saved/list")
def list_saved_searches(
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    items = session.execute(
        select(SavedSearch).where(SavedSearch.organization_id == ctx.organization_id)
        .order_by(SavedSearch.created_at.desc())
    ).scalars().all()
    return {
        "items": [
            {
                "id": s.id, "name": s.name,
                "filters": json.loads(s.filters_json) if s.filters_json else {},
                "created_at": str(s.created_at),
            }
            for s in items
        ],
    }


@router.post("/saved")
def create_saved_search(
    body: SavedSearchCreate,
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
):
    s = SavedSearch(
        organization_id=ctx.organization_id, name=body.name,
        filters_json=body.filters_json,
    )
    session.add(s); session.commit(); session.refresh(s)
    return {"id": s.id, "name": s.name}


@router.delete("/saved/{search_id}")
def delete_saved_search(
    search_id: int,
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
):
    s = session.execute(
        select(SavedSearch).where(SavedSearch.id == search_id, SavedSearch.organization_id == ctx.organization_id)
    ).scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Saved search not found")
    session.delete(s); session.commit()
    return {"status": "deleted"}


# ═══════════════════════════════════════════════════════════
# ANALYTICS
# ═══════════════════════════════════════════════════════════

@router.get("/stats/summary")
def lead_stats(
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    org = ctx.organization_id

    def _count(status: str) -> int:
        return session.execute(
            select(func.count(Lead.id)).where(Lead.organization_id == org, Lead.status == status)
        ).scalar_one()

    total = _count("") if False else session.execute(select(func.count(Lead.id)).where(Lead.organization_id == org)).scalar_one()
    # Actually properly count each
    new_c = session.execute(select(func.count(Lead.id)).where(Lead.organization_id == org, Lead.status == "new")).scalar_one()
    researching = session.execute(select(func.count(Lead.id)).where(Lead.organization_id == org, Lead.status == "researching")).scalar_one()
    ready = session.execute(select(func.count(Lead.id)).where(Lead.organization_id == org, Lead.status == "ready_for_review")).scalar_one()
    needs_more = session.execute(select(func.count(Lead.id)).where(Lead.organization_id == org, Lead.status == "needs_more_research")).scalar_one()
    approved = session.execute(select(func.count(Lead.id)).where(Lead.organization_id == org, Lead.status == "approved")).scalar_one()
    rejected = session.execute(select(func.count(Lead.id)).where(Lead.organization_id == org, Lead.status == "rejected")).scalar_one()
    imported = session.execute(select(func.count(Lead.id)).where(Lead.organization_id == org, Lead.status == "imported")).scalar_one()
    archived = session.execute(select(func.count(Lead.id)).where(Lead.organization_id == org, Lead.status == "archived")).scalar_one()

    avg_score = session.execute(
        select(func.avg(Lead.opportunity_score)).where(Lead.organization_id == org, Lead.opportunity_score.isnot(None))
    ).scalar_one()

    avg_deal = session.execute(
        select(func.avg(Lead.estimated_deal_low)).where(Lead.organization_id == org, Lead.estimated_deal_low.isnot(None))
    ).scalar_one()

    pipeline_value = session.execute(
        select(func.sum(Lead.estimated_deal_low)).where(
            Lead.organization_id == org,
            Lead.status.in_(["new", "researching", "ready_for_review", "approved"]),
            Lead.estimated_deal_low.isnot(None),
        )
    ).scalar_one()

    # Top industries
    industries = session.execute(
        select(Lead.industry, func.count(Lead.id))
        .where(Lead.organization_id == org, Lead.industry.isnot(None), Lead.industry != "")
        .group_by(Lead.industry).order_by(func.count(Lead.id).desc()).limit(5)
    ).all()

    # Conversion funnel
    conversion = {
        "discovered": total,
        "researched": researching + ready + needs_more + approved,
        "approved": approved,
        "imported": imported,
        "rejected": rejected,
        "import_rate": round(imported / total * 100, 1) if total else 0,
        "approval_rate": round(approved / total * 100, 1) if total else 0,
    }

    return {
        "total": total,
        "by_status": {
            "new": new_c, "researching": researching, "ready_for_review": ready,
            "needs_more_research": needs_more, "approved": approved,
            "rejected": rejected, "imported": imported, "archived": archived,
        },
        "avg_opportunity_score": round(float(avg_score or 0), 1),
        "avg_deal_size": round(float(avg_deal or 0), 1) if avg_deal else 0,
        "estimated_pipeline_value": int(pipeline_value or 0),
        "top_industries": [{"industry": i, "count": c} for i, c in industries],
        "conversion": conversion,
    }


# ═══════════════════════════════════════════════════════════
# TAGS
# ═══════════════════════════════════════════════════════════

@router.get("/tags/list")
def list_tags(
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    """Extract all unique tags across leads."""
    rows = session.execute(
        select(Lead.tags).where(Lead.organization_id == ctx.organization_id, Lead.tags.isnot(None), Lead.tags != "")
    ).scalars().all()

    tag_set: set[str] = set()
    for tags_str in rows:
        for t in tags_str.split(","):
            t = t.strip()
            if t:
                tag_set.add(t)

    return {"tags": sorted(tag_set)}


@router.put("/{lead_id}/tags")
def update_tags(
    lead_id: int,
    tags: str = Query(...),
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
):
    lead = session.execute(
        select(Lead).where(Lead.id == lead_id, Lead.organization_id == ctx.organization_id)
    ).scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead.tags = tags
    session.add(lead); session.commit()
    return {"id": lead.id, "tags": lead.tags}


# ═══════════════════════════════════════════════════════════
# STAGES REFERENCE
# ═══════════════════════════════════════════════════════════

@router.get("/meta/stages")
def list_stages():
    """Return all research pipeline stages for UI rendering."""
    return {"stages": RESEARCH_STAGES, "statuses": STAGE_STATUSES}


@router.get("/meta/statuses")
def list_statuses():
    """Return all lead statuses."""
    return {"statuses": LEAD_STATUSES}


# ═══════════════════════════════════════════════════════════
# AI PROSPECT DISCOVERY ENGINE
# ═══════════════════════════════════════════════════════════

class DiscoveryRequest(BaseModel):
    industry: str = ""
    city: str = ""
    province: str = ""
    country: str = ""
    min_employees: int | None = None
    max_employees: int | None = None
    keyword: str = ""
    business_type: str = ""
    count: int = 5


@router.post("/discover")
async def discover_prospects(
    body: DiscoveryRequest,
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
):
    """AI Prospect Discovery: search, research, and create leads automatically."""
    from app.application.sales.discovery_engine import (
        DiscoveryCriteria,
        DiscoveryEngine,
        LLMDiscoveryProvider,
    )

    provider = LLMDiscoveryProvider(api_key=DEEPSEEK_KEY)
    engine = DiscoveryEngine(session, provider)

    criteria = DiscoveryCriteria(
        industry=body.industry,
        city=body.city,
        province=body.province,
        country=body.country,
        min_employees=body.min_employees,
        max_employees=body.max_employees,
        keyword=body.keyword,
        business_type=body.business_type,
        count=body.count,
    )

    result = await engine.discover(ctx.organization_id, criteria)

    return {
        "stage": result.stage,
        "progress_pct": result.progress_pct,
        "message": result.message,
        "total_time_ms": result.total_time_ms,
        "companies": [
            {
                "name": c.name,
                "industry": c.industry,
                "city": c.city,
                "province": c.province,
                "employees": c.employees,
                "description": c.description,
                "executive_summary": c.executive_summary,
                "opportunity_score": c.opportunity_score,
                "confidence_score": c.confidence_score,
                "buying_signals": c.buying_signals,
                "recommended_services": c.recommended_services,
                "estimated_deal_low": c.estimated_deal_low,
                "estimated_deal_high": c.estimated_deal_high,
                "technology_maturity": c.technology_maturity,
                "revenue_estimate": c.revenue_estimate,
                "explainability": json.loads(c.explainability) if c.explainability else None,
                "pns_fit_score": c.pns_fit_score,
                "pns_fit_data": json.loads(c.pns_fit_data) if c.pns_fit_data else None,
            }
            for c in result.companies
        ],
        "leads_created": result.leads_created,
        "duplicates_skipped": result.duplicates_skipped,
    }


# ═══════════════════════════════════════════════════════════
# INTELLIGENCE PIPELINE — JOB STATUS & METRICS
# ═══════════════════════════════════════════════════════════

@router.get("/enrichment/jobs")
def list_enrichment_jobs(
    status: str = "",
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    """List enrichment jobs with optional status filter."""
    from app.infrastructure.db.models import EnrichmentJob

    stmt = select(EnrichmentJob).where(EnrichmentJob.organization_id == ctx.organization_id)
    if status:
        stmt = stmt.where(EnrichmentJob.status == status)
    stmt = stmt.order_by(EnrichmentJob.created_at.desc()).limit(100)

    jobs = session.execute(stmt).scalars().all()
    return {
        "jobs": [
            {
                "id": j.id, "lead_id": j.lead_id, "status": j.status,
                "discovery_source": j.discovery_source,
                "attempts": j.attempts, "max_attempts": j.max_attempts,
                "error_message": j.error_message,
                "worker_id": j.worker_id,
                "processing_time_ms": j.processing_time_ms,
                "created_at": str(j.created_at),
                "started_at": str(j.started_at) if j.started_at else None,
                "completed_at": str(j.completed_at) if j.completed_at else None,
            }
            for j in jobs
        ],
        "total": len(jobs),
    }


@router.get("/enrichment/metrics")
def enrichment_metrics(
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    """Operational metrics for the Intelligence Pipeline."""
    from app.infrastructure.db.models import EnrichmentJob

    org_filter = EnrichmentJob.organization_id == ctx.organization_id
    total = session.execute(select(func.count(EnrichmentJob.id)).where(org_filter)).scalar_one()
    queued = session.execute(select(func.count(EnrichmentJob.id)).where(org_filter, EnrichmentJob.status == "queued")).scalar_one()
    running = session.execute(select(func.count(EnrichmentJob.id)).where(org_filter, EnrichmentJob.status == "running")).scalar_one()
    completed = session.execute(select(func.count(EnrichmentJob.id)).where(org_filter, EnrichmentJob.status == "completed")).scalar_one()
    failed = session.execute(select(func.count(EnrichmentJob.id)).where(org_filter, EnrichmentJob.status == "failed")).scalar_one()
    retrying = session.execute(select(func.count(EnrichmentJob.id)).where(org_filter, EnrichmentJob.status == "retrying")).scalar_one()

    avg_time = session.execute(
        select(func.avg(EnrichmentJob.processing_time_ms)).where(org_filter, EnrichmentJob.status == "completed")
    ).scalar()

    return {
        "total_jobs": total,
        "queued": queued,
        "running": running,
        "completed": completed,
        "failed": failed,
        "retrying": retrying,
        "avg_processing_time_ms": int(avg_time) if avg_time else None,
    }
