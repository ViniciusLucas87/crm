"""Human reviewed LinkedIn prospect research and outreach workspace."""

import json
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.infrastructure.auth.clerk import AuthContext, require_permission
from app.infrastructure.db.session import get_db_session
from app.infrastructure.db.social_leads import SocialLeadCampaign, SocialLeadOpportunity
from app.presentation.api.v1.routes.reddit_leads import (
    ApprovalRequest,
    OpportunityCreate,
    OpportunityUpdate,
    STAGES,
    _campaign_dict,
    _opportunity_dict,
)

router = APIRouter(prefix="/linkedin", tags=["linkedin-leads"])


def _campaign(session: Session, organization_id: int) -> SocialLeadCampaign:
    campaign = session.execute(
        select(SocialLeadCampaign).where(
            SocialLeadCampaign.organization_id == organization_id,
            SocialLeadCampaign.channel == "linkedin",
            SocialLeadCampaign.product_code == "never_miss",
        )
    ).scalar_one_or_none()
    if campaign:
        return campaign
    campaign = SocialLeadCampaign(
        organization_id=organization_id,
        channel="linkedin",
        name="Never Miss Canadian contractor outreach",
        product_code="never_miss",
        audience="Owners of Canadian plumbing, HVAC, electrical, roofing and field service companies",
        communities_json=json.dumps(["British Columbia", "Alberta", "Ontario", "Canada"]),
        pain_signals_json=json.dumps([
            "owner answers the business phone",
            "calls missed while on site",
            "after-hours enquiries",
            "voicemail loses jobs",
            "small field team",
            "actively hiring reception help",
        ]),
        offer_summary="Never Miss protects the business number they already advertise and turns unanswered calls into organized callbacks.",
        public_reply_guidance="Research from public business sources. Do not scrape LinkedIn or pretend to know the owner personally.",
        dm_guidance="Personalize one connection request at a time. Identify the business reason for contacting them. Never automate sending.",
    )
    session.add(campaign)
    session.commit()
    session.refresh(campaign)
    return campaign


def _get(session: Session, organization_id: int, opportunity_id: int) -> SocialLeadOpportunity:
    item = session.execute(
        select(SocialLeadOpportunity).where(
            SocialLeadOpportunity.id == opportunity_id,
            SocialLeadOpportunity.organization_id == organization_id,
            SocialLeadOpportunity.channel == "linkedin",
        )
    ).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="LinkedIn opportunity not found")
    return item


@router.get("/status")
def status(ctx: AuthContext = Depends(require_permission("companies:read"))):
    return {
        "connected": False,
        "mode": "human_approved_outreach",
        "message": "Manual owner research is ready. Open each LinkedIn profile and approve every connection request yourself.",
        "rules": [
            "Google and public business research only",
            "No LinkedIn scraping or bulk automation",
            "Every message requires human review",
            "Record the business reason and result",
        ],
    }


@router.get("/campaigns")
def campaigns(ctx: AuthContext = Depends(require_permission("companies:read")), session: Session = Depends(get_db_session)):
    _campaign(session, ctx.organization_id)
    items = session.execute(
        select(SocialLeadCampaign).where(
            SocialLeadCampaign.organization_id == ctx.organization_id,
            SocialLeadCampaign.channel == "linkedin",
        ).order_by(SocialLeadCampaign.created_at.desc())
    ).scalars().all()
    return {"items": [_campaign_dict(item) for item in items]}


@router.get("/opportunities")
def opportunities(limit: int = Query(50, ge=1, le=100), ctx: AuthContext = Depends(require_permission("companies:read")), session: Session = Depends(get_db_session)):
    items = session.execute(
        select(SocialLeadOpportunity).where(
            SocialLeadOpportunity.organization_id == ctx.organization_id,
            SocialLeadOpportunity.channel == "linkedin",
        ).order_by(SocialLeadOpportunity.relevance_score.desc(), SocialLeadOpportunity.created_at.desc()).limit(limit)
    ).scalars().all()
    return {"items": [_opportunity_dict(item) for item in items], "total": len(items)}


@router.post("/opportunities")
def create(body: OpportunityCreate, ctx: AuthContext = Depends(require_permission("companies:write")), session: Session = Depends(get_db_session)):
    campaign = _campaign(session, ctx.organization_id)
    item = SocialLeadOpportunity(
        organization_id=ctx.organization_id,
        campaign_id=campaign.id,
        channel="linkedin",
        community=body.community.strip(),
        author_handle=body.author_handle.strip(),
        post_title=body.post_title.strip(),
        post_excerpt=body.post_excerpt.strip(),
        source_url=str(body.source_url),
        relevance_score=body.relevance_score,
        relevance_reason=body.relevance_reason.strip(),
        detected_signals_json=json.dumps(body.detected_signals),
        owner_user_id=ctx.user_id,
    )
    session.add(item)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=409, detail="This LinkedIn profile is already in your workspace") from exc
    session.refresh(item)
    return _opportunity_dict(item)


@router.post("/opportunities/{opportunity_id}/draft")
def draft(opportunity_id: int, ctx: AuthContext = Depends(require_permission("companies:write")), session: Session = Depends(get_db_session)):
    item = _get(session, ctx.organization_id, opportunity_id)
    item.public_reply_draft = (
        f"Hi {item.author_handle}, I am Vini, founder of Pacific North Systems in Vancouver. "
        "Quick question: when you are on a job and cannot answer, do customers sometimes call the next contractor? "
        "I built a simple way to text missed callers immediately while keeping your current number. Open to connecting?"
    )
    item.dm_draft = (
        f"Hi {item.author_handle}, thanks for connecting. I am Vini from Pacific North Systems. "
        "I asked because I built Never Miss for owner-operated contractors who cannot always answer while working. "
        "It keeps your current business number, texts missed callers, and organizes the callbacks. "
        "Would you like me to show you how it would work with your current phone setup?"
    )
    item.status = "public_reply_ready"
    session.commit()
    session.refresh(item)
    return _opportunity_dict(item)


@router.patch("/opportunities/{opportunity_id}")
def update(opportunity_id: int, body: OpportunityUpdate, ctx: AuthContext = Depends(require_permission("companies:write")), session: Session = Depends(get_db_session)):
    item = _get(session, ctx.organization_id, opportunity_id)
    if body.status is not None:
        if body.status not in STAGES:
            raise HTTPException(status_code=422, detail="Unknown LinkedIn workflow stage")
        item.status = body.status
    if body.permission_basis is not None:
        item.permission_basis = body.permission_basis.strip() or None
    if body.response_summary is not None:
        item.response_summary = body.response_summary.strip() or None
    if body.next_follow_up_at is not None:
        item.next_follow_up_at = body.next_follow_up_at
    session.commit()
    session.refresh(item)
    return _opportunity_dict(item)


@router.post("/opportunities/{opportunity_id}/approve-dm")
def approve(opportunity_id: int, body: ApprovalRequest, ctx: AuthContext = Depends(require_permission("companies:write")), session: Session = Depends(get_db_session)):
    item = _get(session, ctx.organization_id, opportunity_id)
    if not body.human_approved:
        raise HTTPException(status_code=422, detail="A person must approve the message")
    item.permission_basis = body.permission_basis.strip()
    item.human_approved_at = datetime.now(UTC)
    item.status = "dm_ready"
    session.commit()
    session.refresh(item)
    return _opportunity_dict(item)


@router.post("/opportunities/{opportunity_id}/mark-contacted")
def contacted(opportunity_id: int, ctx: AuthContext = Depends(require_permission("companies:write")), session: Session = Depends(get_db_session)):
    item = _get(session, ctx.organization_id, opportunity_id)
    if not item.human_approved_at or not item.permission_basis:
        raise HTTPException(status_code=409, detail="Approve the personalized message before recording contact")
    item.contacted_at = datetime.now(UTC)
    item.status = "contacted"
    session.commit()
    session.refresh(item)
    return _opportunity_dict(item)
