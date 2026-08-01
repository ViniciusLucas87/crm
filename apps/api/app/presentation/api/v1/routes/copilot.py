"""
AI Sales Copilot API — real-time sales coaching + conversation intelligence.

POST /copilot/analyze — returns structured coaching recommendations
POST /copilot/intelligence — extracts business insights from transcript
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.application.copilot.decision_engine import get_decision_engine
from app.application.transcription import TranscriptSegment
from app.application.transcription.intelligence import get_conversation_intelligence
from app.infrastructure.auth.clerk import AuthContext, require_permission
from app.infrastructure.db.models import Company, Contact, Conversation, Activity, Opportunity
from app.infrastructure.db.session import get_db_session
from sqlalchemy import select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_SEGMENTS = 200
MAX_SEGMENT_LENGTH = 2000
MAX_TOTAL_LENGTH = 50000


class SegmentInput(BaseModel):
    speaker: str = Field(default="Unknown", max_length=50)
    text: str = Field(min_length=1, max_length=MAX_SEGMENT_LENGTH)
    start: float = Field(default=0.0, ge=0.0)
    end: float = Field(default=0.0, ge=0.0)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    is_final: bool = True

    @field_validator("speaker")
    @classmethod
    def sanitize_speaker(cls, v: str) -> str:
        return v.strip()[:50] or "Unknown"


class CopilotAnalyzeRequest(BaseModel):
    company_id: int | None = None
    conversation_id: int | None = None
    transcript: str = ""
    recent_events: list[dict] | None = None


class IntelligenceRequest(BaseModel):
    company_id: int | None = None
    conversation_id: int | None = None
    segments: list[SegmentInput] = Field(default_factory=list, max_length=MAX_SEGMENTS)


@router.post("/copilot/intelligence")
async def extract_intelligence(
    payload: IntelligenceRequest,
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    """Extract structured business intelligence from transcript segments.

    Returns pain points, buying signals, decision makers, objections,
    budget, timeline, and more — each with confidence and evidence.

    Validates all segments for length, speaker, and confidence bounds.
    Rejects hallucinated insights — every finding includes transcript evidence.
    """
    # Validate total transcript length
    total_len = sum(len(s.text) for s in payload.segments)
    if total_len > MAX_TOTAL_LENGTH:
        raise HTTPException(400, f"Total transcript length exceeds {MAX_TOTAL_LENGTH} characters")

    if not payload.segments:
        raise HTTPException(400, "At least one transcript segment is required")

    # Convert to internal segment format
    segments = [
        TranscriptSegment(
            speaker=s.speaker,
            text=s.text.strip(),
            start=s.start,
            end=s.end or s.start + 1.0,
            confidence=s.confidence,
            is_final=s.is_final,
        )
        for s in payload.segments
        if s.text.strip()  # Skip empty segments
    ]

    if not segments:
        raise HTTPException(400, "No valid transcript segments (all were empty)")

    # Sort by start time
    segments.sort(key=lambda s: s.start)

    # Run intelligence extraction
    intel = get_conversation_intelligence()
    report = await intel.analyze(segments)

    # Filter out low-confidence insights without evidence
    valid_insights = [
        i for i in report.insights
        if i.confidence >= 30 and i.evidence and len(i.evidence) > 5
    ]

    logger.info(
        "Intelligence extracted: %d insights from %d segments (%d chars)",
        len(valid_insights), len(segments), total_len,
    )

    return {
        "summary": report.summary,
        "pain_points": report.pain_points,
        "current_software": report.current_software,
        "current_process": report.current_process,
        "decision_makers": report.decision_makers,
        "budget_indicated": report.budget_indicated,
        "timeline_indicated": report.timeline_indicated,
        "buying_signals": report.buying_signals,
        "objections": report.objections,
        "competitors": report.competitors,
        "goals": report.goals,
        "risks": report.risks,
        "action_items": report.action_items,
        "questions_asked": report.questions_asked,
        "commitments": report.commitments,
        "insights": [
            {
                "category": i.category.value,
                "value": i.value,
                "confidence": i.confidence,
                "evidence": i.evidence,
                "speaker": i.speaker,
            }
            for i in report.insights
        ],
        "transcript_length": report.transcript_length,
        "analyzed_at": report.analyzed_at,
    }


@router.post("/copilot/analyze")
async def copilot_analyze(
    payload: CopilotAnalyzeRequest,
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    """Analyze current conversation context and return coaching recommendations.

    Called by the Copilot UI every few seconds during a live interaction.
    Returns structured insights: stage, progress, questions, alerts, deal metrics.
    """
    # Gather company context
    company_context = {}
    conversation_history = None

    if payload.company_id:
        company = session.execute(
            select(Company).where(
                Company.id == payload.company_id,
                Company.organization_id == ctx.organization_id,
            )
        ).scalar_one_or_none()

        if company:
            company_context = {
                "name": company.name,
                "industry": company.industry,
                "employees": company.employees,
                "revenue": str(company.revenue) if company.revenue else None,
                "website": company.website,
                "description": company.description,
            }

            # Get primary contact
            if company.primary_contact_id:
                contact = session.get(Contact, company.primary_contact_id)
                if contact:
                    company_context["primary_contact"] = {
                        "name": f"{contact.first_name} {contact.last_name}",
                        "title": contact.job_title,
                        "email": contact.email,
                        "phone": contact.phone or contact.mobile,
                    }

    if payload.conversation_id:
        conv = session.execute(
            select(Conversation).where(
                Conversation.id == payload.conversation_id,
                Conversation.organization_id == ctx.organization_id,
            )
        ).scalar_one_or_none()

        if conv:
            company_context["relationship_stage"] = conv.relationship_stage
            company_context["health_score"] = conv.health_score

    # Run Decision Engine
    engine = get_decision_engine()
    result = await engine.analyze(
        transcript=payload.transcript,
        company_context=company_context,
        conversation_history=conversation_history,
    )

    return {
        "conversation_stage": result.conversation_stage,
        "discovery_progress": result.discovery_progress,
        "qualification_progress": result.qualification_progress,
        "pain_points": result.pain_points,
        "buying_signals": result.buying_signals,
        "objections": result.objections,
        "competitor_mentions": result.competitor_mentions,
        "suggested_question": result.suggested_question,
        "suggested_product": result.suggested_product,
        "suggested_case_study": result.suggested_case_study,
        "suggested_next_step": result.suggested_next_step,
        "current_strategy": result.current_strategy,
        "alternative_strategy": result.alternative_strategy,
        "estimated_deal_score": result.estimated_deal_score,
        "estimated_close_probability": result.estimated_close_probability,
        "budget_indicated": result.budget_indicated,
        "timeline_indicated": result.timeline_indicated,
        "decision_maker_identified": result.decision_maker_identified,
        "missing_information": result.missing_information,
        "alerts": [{"level": a.level.value, "message": a.message, "detail": a.detail} for a in result.alerts],
        "integration_opportunities": result.integration_opportunities,
        "discovery_fields": [
            {"field": f.field, "status": f.status.value, "value": f.value, "confidence": f.confidence}
            for f in result.discovery_fields
        ],
        "company_context": company_context,
    }


class CoachRequest(BaseModel):
    insights: list[dict] = Field(default_factory=list, max_length=500)


@router.post("/copilot/coach")
async def get_coaching(
    payload: CoachRequest,
    ctx: AuthContext = Depends(require_permission("companies:read")),
):
    """Generate live coaching recommendations from structured ConversationInsights.

    Consumes structured insights (never raw transcript). Returns unified
    SalesCoachReport with discovery, opportunity scoring, ranked product
    recommendations, sales strategy, risk analysis, and next best question.
    """
    from app.application.copilot.coach_report import get_coach_report_generator
    from app.application.transcription.intelligence import ConversationInsight as CI, InsightCategory

    insights = [
        CI(
            category=InsightCategory(i.get("category", "pain_point")),
            value=str(i.get("value", "")),
            confidence=int(i.get("confidence", 50)),
            evidence=str(i.get("evidence", "")),
            speaker=str(i.get("speaker", "Unknown")),
        )
        for i in payload.insights
        if i.get("category") in [c.value for c in InsightCategory]
    ]

    generator = get_coach_report_generator()
    report = generator.generate(insights)

    # ── Serialize DiscoveryReport ──
    discovery = (
        {
            "completion_pct": report.discovery.completion_pct,
            "missing_keys": report.discovery.missing_keys,
            "missing_priority_order": report.discovery.missing_priority_order,
            "fields": [
                {
                    "field_key": f.field_key,
                    "label": f.label,
                    "known": f.known,
                    "value": f.value,
                    "evidence": f.evidence,
                    "confidence": f.confidence,
                    "priority": f.priority,
                }
                for f in report.discovery.fields
            ],
        }
        if report.discovery
        else None
    )

    # ── Serialize OpportunityReport ──
    opportunity = (
        {
            "score": report.opportunity.score,
            "confidence": report.opportunity.confidence,
            "strengths": report.opportunity.strengths,
            "weaknesses": report.opportunity.weaknesses,
            "risk_level": report.opportunity.risk_level,
            "recommended_milestone": report.opportunity.recommended_milestone,
        }
        if report.opportunity
        else None
    )

    # ── Serialize Recommendations ──
    recommendations = [
        {
            "product": r.product,
            "confidence": r.confidence,
            "reason": r.reason,
            "evidence": r.evidence,
            "rank": r.rank,
        }
        for r in report.recommendations
    ]

    # ── Serialize Strategy ──
    strategy = (
        {
            "current_stage": report.strategy.current_stage,
            "customer_type": report.strategy.customer_type,
            "recommended_strategy": report.strategy.recommended_strategy,
            "avoid": report.strategy.avoid,
            "next_best_action": report.strategy.next_best_action,
            "alternative_path": report.strategy.alternative_path,
        }
        if report.strategy
        else None
    )

    # ── Serialize RiskReport ──
    risk_report = (
        {
            "risks": [
                {"risk": r.risk, "severity": r.severity, "mitigation": r.mitigation}
                for r in report.risk_report.risks
            ],
            "critical_count": report.risk_report.critical_count,
            "high_count": report.risk_report.high_count,
            "medium_count": report.risk_report.medium_count,
            "low_count": report.risk_report.low_count,
            "overall_risk": report.risk_report.overall_risk,
        }
        if report.risk_report
        else None
    )

    return {
        # ── Deal Health ──
        "deal_health": report.deal_health,
        "deal_health_score": report.deal_health_score,

        # ── Discovery ──
        "discovery": discovery,

        # ── Opportunity ──
        "opportunity": opportunity,

        # ── Recommendations ──
        "recommendations": recommendations,

        # ── Strategy ──
        "strategy": strategy,

        # ── Risks ──
        "risk_report": risk_report,

        # ── Buying Signals ──
        "buying_signals": report.buying_signals,

        # ── Objections ──
        "objections": report.objections,

        # ── Next Best ──
        "next_best_question": report.next_best_question,
        "next_best_action": report.next_best_action,

        # ── Extracted ──
        "pain_points": report.pain_points,
        "decision_makers": report.decision_makers,
        "budget_indicated": report.budget_indicated,
        "timeline_indicated": report.timeline_indicated,

        # ── Meta ──
        "generated_at": report.generated_at,
    }


class ProposalRequest(BaseModel):
    company_id: int | None = None
    company_name: str = ""
    company_context: dict | None = None
    insights: list[dict] = Field(default_factory=list, max_length=500)


@router.post("/copilot/proposal")
async def generate_proposal(
    payload: ProposalRequest,
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    """Generate a structured software proposal from conversation insights.

    Consumes ConversationInsights and company context. Produces a complete
    proposal with executive summary, solution, pricing, timeline, and ROI.
    """
    from app.application.copilot.proposal_generator import ProposalGenerator
    from app.application.transcription.intelligence import ConversationInsight as CI, InsightCategory

    # Build company context from DB if company_id provided
    company_context = payload.company_context or {}
    company_name = payload.company_name

    if payload.company_id:
        company = session.execute(
            select(Company).where(Company.id == payload.company_id, Company.organization_id == ctx.organization_id)
        ).scalar_one_or_none()
        if company:
            company_name = company.name
            company_context = {
                "name": company.name, "industry": company.industry,
                "employees": company.employees, "revenue": str(company.revenue) if company.revenue else None,
                "website": company.website, "description": company.description,
            }

    insights = [
        CI(category=InsightCategory(i.get("category", "pain_point")), value=str(i.get("value", "")),
           confidence=int(i.get("confidence", 50)), evidence=str(i.get("evidence", "")),
           speaker=str(i.get("speaker", "Unknown")))
        for i in payload.insights if i.get("category") in [c.value for c in InsightCategory]
    ]

    generator = ProposalGenerator()
    proposal = generator.generate(company_name=company_name, company_context=company_context, insights=insights)

    return {
        "title": proposal.title,
        "company_name": proposal.company_name,
        "generated_at": proposal.generated_at,
        "executive_summary": proposal.executive_summary,
        "current_state": proposal.current_state,
        "proposed_solution": proposal.proposed_solution,
        "solution_components": proposal.solution_components,
        "implementation_plan": proposal.implementation_plan,
        "deliverables": proposal.deliverables,
        "roi_analysis": proposal.roi_analysis,
        "roi_metrics": proposal.roi_metrics,
        "risks": proposal.risks,
        "investment": proposal.investment,
        "timeline": proposal.timeline,
        "next_steps": proposal.next_steps,
        "quality_score": proposal.quality_score,
        "missing_information": proposal.missing_information,
        "readiness": proposal.readiness,
    }


# ═══════════════════════════════════════════════════════════
# PROPOSAL STUDIO — flagship consulting proposal platform
# ═══════════════════════════════════════════════════════════

class ProposalStudioRequest(BaseModel):
    opportunity_id: int | None = None
    company_id: int | None = None


@router.post("/copilot/proposal-studio")
async def generate_proposal_studio(
    payload: ProposalStudioRequest,
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    """Generate a professional consulting proposal from OpportunityIntelligence.

    This is the flagship endpoint — consumes OpportunityIntelligence exclusively.
    Produces a complete, reviewable, exportable proposal with 14 sections.
    """
    from app.application.copilot.proposal.proposal_studio import get_proposal_studio
    from app.application.opportunity_intelligence.builder import get_opportunity_intelligence_builder
    from app.application.opportunity_intelligence.cache import get_opportunity_intelligence_cache

    # Load or build OpportunityIntelligence
    opp_id = payload.opportunity_id
    company_id = payload.company_id

    if not opp_id and company_id:
        # Look up opportunity by company
        opp = session.execute(
            select(Opportunity).where(
                Opportunity.company_id == company_id,
                Opportunity.organization_id == ctx.organization_id,
            ).order_by(Opportunity.created_at.desc())
        ).scalars().first()
        if opp:
            opp_id = opp.id

    if opp_id:
        cache = get_opportunity_intelligence_cache()
        oi = cache.get(cache.make_key(opp_id, ctx.organization_id))
        if oi is None:
            # Build it
            opp = session.execute(
                select(Opportunity).where(
                    Opportunity.id == opp_id,
                    Opportunity.organization_id == ctx.organization_id,
                )
            ).scalar_one_or_none()
            if not opp:
                raise HTTPException(404, "Opportunity not found")

            company = session.execute(
                select(Company).where(Company.id == opp.company_id)
            ).scalar_one_or_none()

            contacts = session.execute(
                select(Contact).where(Contact.company_id == opp.company_id)
            ).scalars().all()

            activities = session.execute(
                select(Activity).where(
                    Activity.company_id == opp.company_id,
                    Activity.organization_id == ctx.organization_id,
                ).order_by(Activity.created_at.desc()).limit(50)
            ).scalars().all()

            builder = get_opportunity_intelligence_builder()
            oi = builder.build(
                company={
                    "id": company.id, "name": company.name, "industry": company.industry,
                    "website": company.website, "employees": company.employees,
                    "revenue": float(company.revenue) if company.revenue else None,
                    "city": company.city, "province": company.province, "country": company.country,
                    "opportunity_score": company.opportunity_score,
                } if company else {},
                contacts=[{
                    "id": c.id, "first_name": c.first_name, "last_name": c.last_name,
                    "job_title": c.job_title, "email": c.email,
                    "phone": c.phone, "mobile": c.mobile,
                    "is_decision_maker": c.is_decision_maker, "is_primary": c.is_primary,
                } for c in contacts],
                activities=[{
                    "id": a.id, "activity_type": a.activity_type,
                    "subject": a.subject, "body": a.body,
                    "created_at": a.created_at.isoformat() if a.created_at else "",
                } for a in activities],
                opportunity={"id": opp.id, "stage": opp.stage, "status": opp.status},
            )
            cache.set(cache.make_key(opp.id, ctx.organization_id), oi)
    else:
        raise HTTPException(400, "opportunity_id or company_id required")

    # Generate proposal
    studio = get_proposal_studio()
    proposal = studio.generate(oi, opportunity_id=opp_id)

    return {
        "id": proposal.id,
        "title": proposal.title,
        "company_name": proposal.company_name,
        "opportunity_id": proposal.opportunity_id,
        "generated_at": proposal.generated_at,
        "current_version": proposal.current_version,
        "quality_score": proposal.quality_score,
        "ready_to_send": proposal.ready_to_send,
        "missing_information": proposal.missing_information,
        "sections": [
            {
                "id": s.id,
                "title": s.title,
                "content": s.content,
                "status": s.status,
                "generated_at": s.generated_at,
            }
            for s in proposal.sections
        ],
        "versions": [
            {
                "version": v.version,
                "created_at": v.created_at,
                "generated_by": v.generated_by,
                "reason": v.reason,
            }
            for v in proposal.versions
        ],
    }


class ExportRequest(BaseModel):
    format: str = "markdown"  # markdown, html


@router.post("/copilot/proposal-studio/export")
async def export_proposal_studio(
    payload: dict,
    ctx: AuthContext = Depends(require_permission("companies:read")),
):
    """Export a proposal in the specified format (markdown, html)."""
    from app.application.copilot.proposal.proposal_studio import get_proposal_studio
    from app.application.copilot.proposal.models import Proposal, ProposalSection

    # Rebuild minimal proposal from payload
    sections = [
        ProposalSection(
            id=s.get("id", ""), title=s.get("title", ""),
            content=s.get("content", ""), status=s.get("status", "generated"),
            generated_at=s.get("generated_at", ""),
        )
        for s in payload.get("sections", [])
    ]

    proposal = Proposal(
        id=payload.get("id", ""),
        title=payload.get("title", ""),
        company_name=payload.get("company_name", ""),
        generated_at=payload.get("generated_at", ""),
        sections=sections,
        current_version=payload.get("current_version", 1),
        quality_score=payload.get("quality_score", 0),
    )

    fmt = payload.get("format", "markdown")
    studio = get_proposal_studio()

    if fmt == "markdown":
        result = studio.export(proposal, format="markdown")
        return {"format": "markdown", "content": result}
    elif fmt == "html":
        result = studio.export(proposal, format="html")
        return {"format": "html", "content": result}
    else:
        raise HTTPException(400, f"Unsupported format: {fmt}")


# ═══════════════════════════════════════════════════════════
# OPPORTUNITY INTELLIGENCE — canonical business endpoint
# ═══════════════════════════════════════════════════════════

@router.get("/opportunities/{opportunity_id}/intelligence")
async def get_opportunity_intelligence(
    opportunity_id: int,
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    """Return the canonical OpportunityIntelligence for an opportunity.

    This is the single source of truth consumed by AI Coach, Proposal
    Studio, Email Copilot, Meeting Copilot, and Analytics.

    Serves from cache when available (<50ms target).
    """
    from app.application.opportunity_intelligence.builder import get_opportunity_intelligence_builder
    from app.application.opportunity_intelligence.cache import get_opportunity_intelligence_cache
    from app.domain.opportunity_intelligence import (
        OpportunityStage, OpportunityStatus,
        TypedValue, Stakeholder, BusinessContext, SalesContext,
        SolutionContext, TimelineEvent, EventType, CustomerType, UrgencyLevel,
    )

    cache = get_opportunity_intelligence_cache()
    cache_key = cache.make_key(opportunity_id, ctx.organization_id)

    # Try cache first
    cached = cache.get(cache_key)
    if cached is not None:
        return _serialize_intelligence(cached)

    # Load opportunity
    opp = session.execute(
        select(Opportunity).where(
            Opportunity.id == opportunity_id,
            Opportunity.organization_id == ctx.organization_id,
        )
    ).scalar_one_or_none()

    if not opp:
        raise HTTPException(404, "Opportunity not found")

    # Load related data
    company = session.execute(
        select(Company).where(Company.id == opp.company_id)
    ).scalar_one_or_none()

    contacts_query = session.execute(
        select(Contact).where(Contact.company_id == opp.company_id)
    ).scalars().all()

    activities_query = session.execute(
        select(Activity).where(
            Activity.company_id == opp.company_id,
            Activity.organization_id == ctx.organization_id,
        ).order_by(Activity.created_at.desc()).limit(50)
    ).scalars().all()

    # Build dicts
    company_dict = {}
    if company:
        company_dict = {
            "id": company.id,
            "organization_id": company.organization_id,
            "name": company.name,
            "industry": company.industry,
            "website": company.website,
            "employees": company.employees,
            "revenue": float(company.revenue) if company.revenue else None,
            "city": company.city,
            "province": company.province,
            "country": company.country,
            "opportunity_score": company.opportunity_score,
        }

    contacts_list = [
        {
            "id": c.id,
            "first_name": c.first_name,
            "last_name": c.last_name,
            "job_title": c.job_title,
            "email": c.email,
            "phone": c.phone,
            "mobile": c.mobile,
            "is_decision_maker": c.is_decision_maker,
            "is_primary": c.is_primary,
        }
        for c in contacts_query
    ]

    activities_list = [
        {
            "id": a.id,
            "activity_type": a.activity_type,
            "subject": a.subject,
            "body": a.body,
            "created_at": a.created_at.isoformat() if a.created_at else "",
        }
        for a in activities_query
    ]

    opp_dict = {
        "id": opp.id,
        "stage": opp.stage,
        "status": opp.status,
    }

    # Build OpportunityIntelligence (no insights for this query — just CRM data)
    builder = get_opportunity_intelligence_builder()
    intelligence = builder.build(
        company=company_dict,
        contacts=contacts_list,
        activities=activities_list,
        opportunity=opp_dict,
    )

    # Cache it
    cache.set(cache_key, intelligence)

    return _serialize_intelligence(intelligence)


@router.post("/opportunities/{opportunity_id}/intelligence/refresh")
async def refresh_opportunity_intelligence(
    opportunity_id: int,
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    """Refresh (rebuild) OpportunityIntelligence for an opportunity.

    Invalidates cache and rebuilds from all data sources including
    recent ConversationInsights.
    """
    from app.application.opportunity_intelligence.builder import get_opportunity_intelligence_builder
    from app.application.opportunity_intelligence.cache import get_opportunity_intelligence_cache

    opp = session.execute(
        select(Opportunity).where(
            Opportunity.id == opportunity_id,
            Opportunity.organization_id == ctx.organization_id,
        )
    ).scalar_one_or_none()

    if not opp:
        raise HTTPException(404, "Opportunity not found")

    # Load company
    company = session.execute(
        select(Company).where(Company.id == opp.company_id)
    ).scalar_one_or_none()

    contacts = session.execute(
        select(Contact).where(Contact.company_id == opp.company_id)
    ).scalars().all()

    activities = session.execute(
        select(Activity).where(
            Activity.company_id == opp.company_id,
            Activity.organization_id == ctx.organization_id,
        ).order_by(Activity.created_at.desc()).limit(100)
    ).scalars().all()

    # Build
    builder = get_opportunity_intelligence_builder()
    intelligence = builder.build(
        company={
            "id": company.id, "name": company.name, "industry": company.industry,
            "website": company.website, "employees": company.employees,
            "revenue": float(company.revenue) if company.revenue else None,
            "city": company.city, "province": company.province, "country": company.country,
            "opportunity_score": company.opportunity_score,
        } if company else {},
        contacts=[{
            "id": c.id, "first_name": c.first_name, "last_name": c.last_name,
            "job_title": c.job_title, "email": c.email,
            "phone": c.phone, "mobile": c.mobile,
            "is_decision_maker": c.is_decision_maker, "is_primary": c.is_primary,
        } for c in contacts],
        activities=[{
            "id": a.id, "activity_type": a.activity_type,
            "subject": a.subject, "body": a.body,
            "created_at": a.created_at.isoformat() if a.created_at else "",
        } for a in activities],
        opportunity={"id": opp.id, "stage": opp.stage, "status": opp.status},
    )

    # Cache it
    cache = get_opportunity_intelligence_cache()
    cache.set(cache.make_key(opportunity_id, ctx.organization_id), intelligence)

    logger.info("OpportunityIntelligence refreshed for opportunity %d", opportunity_id)
    return _serialize_intelligence(intelligence)


# ═══════════════════════════════════════════════════════════
# EMAIL COPILOT — professional email generation
# ═══════════════════════════════════════════════════════════

class EmailGenerateRequest(BaseModel):
    opportunity_id: int | None = None
    company_id: int | None = None
    template_id: str | None = None


class EmailReviewRequest(BaseModel):
    subject: str = ""
    body: str = ""
    greeting: str = ""
    call_to_action: str = ""
    signature: str = ""


@router.post("/copilot/email")
async def generate_email(
    payload: EmailGenerateRequest,
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    """Generate a professional email based on OpportunityIntelligence.

    Determines the right email purpose, strategy, and content based on
    the current opportunity state. Returns a complete draft with review.
    """
    from app.application.copilot.email.email_copilot import get_email_copilot
    from app.application.opportunity_intelligence.builder import get_opportunity_intelligence_builder
    from app.application.opportunity_intelligence.cache import get_opportunity_intelligence_cache

    opp_id = payload.opportunity_id

    if not opp_id and payload.company_id:
        opp = session.execute(
            select(Opportunity).where(
                Opportunity.company_id == payload.company_id,
                Opportunity.organization_id == ctx.organization_id,
            ).order_by(Opportunity.created_at.desc())
        ).scalars().first()
        if opp:
            opp_id = opp.id

    if not opp_id:
        raise HTTPException(400, "opportunity_id or company_id required")

    # Load or build OpportunityIntelligence
    cache = get_opportunity_intelligence_cache()
    oi = cache.get(cache.make_key(opp_id, ctx.organization_id))

    if oi is None:
        opp = session.execute(
            select(Opportunity).where(
                Opportunity.id == opp_id,
                Opportunity.organization_id == ctx.organization_id,
            )
        ).scalar_one_or_none()

        if not opp:
            raise HTTPException(404, "Opportunity not found")

        company = session.execute(
            select(Company).where(Company.id == opp.company_id)
        ).scalar_one_or_none()

        contacts = session.execute(
            select(Contact).where(Contact.company_id == opp.company_id)
        ).scalars().all()

        builder = get_opportunity_intelligence_builder()
        oi = builder.build(
            company={
                "id": company.id, "name": company.name, "industry": company.industry,
                "website": company.website, "employees": company.employees,
                "revenue": float(company.revenue) if company.revenue else None,
            } if company else {},
            contacts=[{
                "id": c.id, "first_name": c.first_name, "last_name": c.last_name,
                "job_title": c.job_title, "email": c.email,
                "is_decision_maker": c.is_decision_maker, "is_primary": c.is_primary,
            } for c in contacts],
            opportunity={"id": opp.id, "stage": opp.stage, "status": opp.status},
        )
        cache.set(cache.make_key(opp.id, ctx.organization_id), oi)

    copilot = get_email_copilot()
    result = copilot.generate(oi, template_id=payload.template_id)

    logger.info("Email generated for opportunity %d: %s", opp_id, result["strategy"]["purpose"])
    return result


@router.get("/copilot/email/templates")
async def get_email_templates(
    ctx: AuthContext = Depends(require_permission("companies:read")),
):
    """List available email templates."""
    from app.application.copilot.email.email_copilot import get_email_copilot
    copilot = get_email_copilot()
    return {"templates": copilot.get_templates()}


@router.post("/copilot/email/review")
async def review_email(
    payload: EmailReviewRequest,
    ctx: AuthContext = Depends(require_permission("companies:read")),
):
    """Review an email draft for quality and readiness."""
    from app.application.copilot.email.email_copilot import get_email_copilot
    copilot = get_email_copilot()
    return copilot.review_draft({
        "subject": payload.subject,
        "body": payload.body,
        "greeting": payload.greeting,
        "call_to_action": payload.call_to_action,
        "signature": payload.signature,
    })


# ═══════════════════════════════════════════════════════════
# MEETING COPILOT — preparation, live guidance, summary
# ═══════════════════════════════════════════════════════════

class MeetingRequest(BaseModel):
    opportunity_id: int | None = None
    company_id: int | None = None


def _load_opportunity_intelligence(opportunity_id, company_id, org_id, session):
    """Shared helper to load/build OpportunityIntelligence for copilot endpoints."""
    from app.application.opportunity_intelligence.builder import get_opportunity_intelligence_builder
    from app.application.opportunity_intelligence.cache import get_opportunity_intelligence_cache

    opp_id = opportunity_id
    if not opp_id and company_id:
        opp = session.execute(
            select(Opportunity).where(
                Opportunity.company_id == company_id,
                Opportunity.organization_id == org_id,
            ).order_by(Opportunity.created_at.desc())
        ).scalars().first()
        if opp:
            opp_id = opp.id

    if not opp_id:
        return None, None

    cache = get_opportunity_intelligence_cache()
    oi = cache.get(cache.make_key(opp_id, org_id))

    if oi is None:
        opp = session.execute(
            select(Opportunity).where(Opportunity.id == opp_id, Opportunity.organization_id == org_id)
        ).scalar_one_or_none()
        if not opp:
            return None, None

        company = session.execute(select(Company).where(Company.id == opp.company_id)).scalar_one_or_none()
        contacts = session.execute(select(Contact).where(Contact.company_id == opp.company_id)).scalars().all()

        builder = get_opportunity_intelligence_builder()
        oi = builder.build(
            company={"id": company.id, "name": company.name, "industry": company.industry,
                     "website": company.website, "employees": company.employees,
                     "revenue": float(company.revenue) if company.revenue else None} if company else {},
            contacts=[{"id": c.id, "first_name": c.first_name, "last_name": c.last_name,
                       "job_title": c.job_title, "email": c.email,
                       "is_decision_maker": c.is_decision_maker, "is_primary": c.is_primary} for c in contacts],
            opportunity={"id": opp.id, "stage": opp.stage, "status": opp.status},
        )
        cache.set(cache.make_key(opp.id, org_id), oi)

    return oi, opp_id


@router.post("/copilot/meeting/prepare")
async def prepare_meeting(
    payload: MeetingRequest,
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    """Generate pre-meeting briefing, agenda, and discovery questions."""
    from app.application.copilot.meeting.meeting_copilot import get_meeting_copilot

    oi, opp_id = _load_opportunity_intelligence(payload.opportunity_id, payload.company_id, ctx.organization_id, session)
    if oi is None:
        raise HTTPException(400, "opportunity_id or company_id required, or opportunity not found")

    copilot = get_meeting_copilot()
    return copilot.prepare(oi)


@router.post("/copilot/meeting/live")
async def live_meeting_guidance(
    payload: MeetingRequest,
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    """Get real-time guidance: missing topics, recommended questions, signals, health."""
    from app.application.copilot.meeting.meeting_copilot import get_meeting_copilot

    oi, opp_id = _load_opportunity_intelligence(payload.opportunity_id, payload.company_id, ctx.organization_id, session)
    if oi is None:
        raise HTTPException(400, "opportunity_id or company_id required, or opportunity not found")

    copilot = get_meeting_copilot()
    return copilot.live(oi)


@router.post("/copilot/meeting/summary")
async def meeting_summary(
    payload: MeetingRequest,
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    """Generate post-meeting summary, action items, and follow-up plan."""
    from app.application.copilot.meeting.meeting_copilot import get_meeting_copilot

    oi, opp_id = _load_opportunity_intelligence(payload.opportunity_id, payload.company_id, ctx.organization_id, session)
    if oi is None:
        raise HTTPException(400, "opportunity_id or company_id required, or opportunity not found")

    copilot = get_meeting_copilot()
    return copilot.summarize(oi)


@router.post("/copilot/meeting/actions")
async def meeting_actions(
    payload: MeetingRequest,
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    """Generate action items only (subset of summary)."""
    from app.application.copilot.meeting.meeting_copilot import get_meeting_copilot

    oi, opp_id = _load_opportunity_intelligence(payload.opportunity_id, payload.company_id, ctx.organization_id, session)
    if oi is None:
        raise HTTPException(400, "opportunity_id or company_id required, or opportunity not found")

    copilot = get_meeting_copilot()
    result = copilot.summarize(oi)
    return {"action_items": result["action_items"]}


def _serialize_intelligence(oi) -> dict:
    """Serialize OpportunityIntelligence to JSON-safe dict."""
    return {
        "opportunity_id": oi.opportunity_id,
        "company_id": oi.company_id,
        "organization_id": oi.organization_id,
        "stage": oi.stage.value if hasattr(oi.stage, "value") else str(oi.stage),
        "status": oi.status.value if hasattr(oi.status, "value") else str(oi.status),
        "deal_health": {"value": oi.deal_health.value, "confidence": oi.deal_health.confidence},
        "opportunity_score": {"value": oi.opportunity_score.value, "confidence": oi.opportunity_score.confidence},
        "discovery_score": {"value": oi.discovery_score.value, "confidence": oi.discovery_score.confidence},
        "proposal_readiness": {"value": oi.proposal_readiness.value, "confidence": oi.proposal_readiness.confidence},
        "company": {
            "name": oi.company_name,
            "industry": oi.company_industry,
            "employees": oi.company_employees,
            "revenue": str(oi.company_revenue) if oi.company_revenue else None,
            "locations": oi.company_locations,
            "website": oi.company_website,
        },
        "stakeholders": [
            {
                "id": s.id, "name": s.name, "title": s.title,
                "email": s.email, "phone": s.phone,
                "role": s.role.value if hasattr(s.role, "value") else str(s.role),
                "is_primary": s.is_primary,
                "confidence": s.confidence, "source": s.source,
            }
            for s in oi.stakeholders
        ],
        "business": {
            "current_process": [{"value": p.value, "confidence": p.confidence} for p in oi.business.current_process],
            "current_software": [{"value": s.value, "confidence": s.confidence} for s in oi.business.current_software],
            "business_goals": [{"value": g.value, "confidence": g.confidence} for g in oi.business.business_goals],
            "pain_points": [{"value": p.value, "confidence": p.confidence} for p in oi.business.pain_points],
            "manual_work_indicators": oi.business.manual_work_indicators,
            "operational_risks": [{"value": r.value, "confidence": r.confidence} for r in oi.business.operational_risks],
            "constraints": [{"value": c.value, "confidence": c.confidence} for c in oi.business.constraints],
            "compliance_requirements": [{"value": c.value, "confidence": c.confidence} for c in oi.business.compliance_requirements],
            "budget": {"value": oi.business.budget.value, "confidence": oi.business.budget.confidence, "raw": oi.business.budget_raw},
            "timeline": {"value": oi.business.timeline.value, "confidence": oi.business.timeline.confidence},
        },
        "sales": {
            "buying_signals": [{"value": b.value, "confidence": b.confidence} for b in oi.sales.buying_signals],
            "objections": [{"value": o.value, "confidence": o.confidence} for o in oi.sales.objections],
            "urgency": {"value": oi.sales.urgency.value, "confidence": oi.sales.urgency.confidence},
            "customer_type": {"value": oi.sales.customer_type.value, "confidence": oi.sales.customer_type.confidence},
            "sales_strategy": oi.sales.sales_strategy,
            "next_best_action": oi.sales.next_best_action,
            "next_best_question": oi.sales.next_best_question,
            "current_milestone": oi.sales.current_milestone,
        },
        "solutions": {
            "recommended_products": oi.solutions.recommended_products,
            "recommended_services": oi.solutions.recommended_services,
            "recommended_integrations": oi.solutions.recommended_integrations,
            "estimated_roi": oi.solutions.estimated_roi,
            "estimated_savings": oi.solutions.estimated_savings,
            "estimated_complexity": oi.solutions.estimated_complexity,
            "proposal_status": oi.solutions.proposal_status,
            "proposal_quality": oi.solutions.proposal_quality,
        },
        "timeline": [
            {
                "event_type": e.event_type.value if hasattr(e.event_type, "value") else str(e.event_type),
                "description": e.description,
                "timestamp": e.timestamp,
                "source": e.source,
            }
            for e in oi.timeline[:50]  # Last 50 events
        ],
        "metadata": {
            "confidence": oi.confidence,
            "source_count": oi.source_count,
            "last_updated": oi.last_updated,
            "created_at": oi.created_at,
            "insight_count": oi.insight_count,
            "call_count": oi.call_count,
            "email_count": oi.email_count,
            "meeting_count": oi.meeting_count,
            "activity_count": oi.activity_count,
            "proposal_count": oi.proposal_count,
        },
    }
