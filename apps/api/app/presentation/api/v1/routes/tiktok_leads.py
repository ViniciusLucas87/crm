"""Human-reviewed TikTok prospect research workspace."""

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
    STAGES,
    ApprovalRequest,
    OpportunityCreate,
    OpportunityUpdate,
    _campaign_dict,
    _opportunity_dict,
    _require_new_social_opportunity,
)

router = APIRouter(prefix="/tiktok", tags=["tiktok-leads"])

DEFAULT_SEARCH_AREAS = [
    "Canadian contractors",
    "Canadian home services",
    "small business Canada",
    "contractor life",
]
DEFAULT_SIGNALS = [
    "missed calls",
    "cannot answer the phone",
    "customers call while working",
    "after-hours enquiries",
    "forgotten follow-up",
    "estimate follow-up",
    "busy on site",
]


def _campaign(session: Session, organization_id: int) -> SocialLeadCampaign:
    campaign = session.execute(
        select(SocialLeadCampaign).where(
            SocialLeadCampaign.organization_id == organization_id,
            SocialLeadCampaign.channel == "tiktok",
            SocialLeadCampaign.product_code == "never_miss",
        )
    ).scalar_one_or_none()
    if campaign:
        return campaign

    campaign = SocialLeadCampaign(
        organization_id=organization_id,
        channel="tiktok",
        name="Never Miss TikTok service-business research",
        product_code="never_miss",
        audience="Canadian contractors and owner-operated service businesses posting about missed calls, slow lead response, or forgotten follow-up",
        communities_json=json.dumps(DEFAULT_SEARCH_AREAS),
        pain_signals_json=json.dumps(DEFAULT_SIGNALS),
        offer_summary="Never Miss helps a business respond after an unanswered call and keep callbacks organized without changing the advertised business number.",
        public_reply_guidance="Save only public posts with a specific business pain signal. Do not add agencies, competing products, generic advice accounts, or unverifiable claims.",
        dm_guidance="Do not follow, comment, or send a TikTok message automatically. A person must review the post, approve a personalized contact, and record the reason before any action.",
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
            SocialLeadOpportunity.channel == "tiktok",
        )
    ).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="TikTok opportunity not found")
    return item


@router.get("/status")
def status(ctx: AuthContext = Depends(require_permission("companies:read"))):
    return {
        "connected": False,
        "mode": "human_approved_outreach",
        "message": "Public post research is ready. Sign in to TikTok only when you are ready to personally review a follow, comment, or direct message.",
        "rules": [
            "Use public posts as research evidence only",
            "No scraping or bulk following",
            "Do not contact competing products or agencies as prospects",
            "Every social action requires human review and recorded approval",
        ],
    }


@router.get("/campaigns")
def campaigns(
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    _campaign(session, ctx.organization_id)
    items = (
        session.execute(
            select(SocialLeadCampaign)
            .where(
                SocialLeadCampaign.organization_id == ctx.organization_id,
                SocialLeadCampaign.channel == "tiktok",
            )
            .order_by(SocialLeadCampaign.created_at.desc())
        )
        .scalars()
        .all()
    )
    return {"items": [_campaign_dict(item) for item in items]}


@router.get("/opportunities")
def opportunities(
    limit: int = Query(50, ge=1, le=100),
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    items = (
        session.execute(
            select(SocialLeadOpportunity)
            .where(
                SocialLeadOpportunity.organization_id == ctx.organization_id,
                SocialLeadOpportunity.channel == "tiktok",
            )
            .order_by(
                SocialLeadOpportunity.relevance_score.desc(),
                SocialLeadOpportunity.created_at.desc(),
            )
            .limit(limit)
        )
        .scalars()
        .all()
    )
    return {"items": [_opportunity_dict(item) for item in items], "total": len(items)}


@router.post("/opportunities")
def create(
    body: OpportunityCreate,
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
):
    campaign = _campaign(session, ctx.organization_id)
    _require_new_social_opportunity(
        session,
        ctx.organization_id,
        "tiktok",
        str(body.source_url),
        body.author_handle.strip().removeprefix("@"),
    )
    item = SocialLeadOpportunity(
        organization_id=ctx.organization_id,
        campaign_id=campaign.id,
        channel="tiktok",
        community=body.community.strip(),
        author_handle=body.author_handle.strip().removeprefix("@"),
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
        raise HTTPException(
            status_code=409, detail="This TikTok post is already in your workspace"
        ) from exc
    session.refresh(item)
    return _opportunity_dict(item)


@router.post("/opportunities/{opportunity_id}/draft")
def draft(
    opportunity_id: int,
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
):
    item = _get(session, ctx.organization_id, opportunity_id)
    item.public_reply_draft = (
        f"Hi @{item.author_handle}, I saw your post about {item.post_title.lower()}. "
        "I’m with Pacific North Systems and we help small service businesses keep missed-call follow-up organized. "
        "Would it be useful if I shared a simple way to handle that?"
    )
    item.dm_draft = (
        f"Hi @{item.author_handle}, Vini here from Pacific North Systems. I reached out because your post described a missed-call or follow-up challenge. "
        "Never Miss helps a business respond after an unanswered call and keep callbacks in one place. "
        "Would you like a short explanation of how it would fit your current phone setup?"
    )
    item.status = "public_reply_ready"
    session.commit()
    session.refresh(item)
    return _opportunity_dict(item)


@router.patch("/opportunities/{opportunity_id}")
def update(
    opportunity_id: int,
    body: OpportunityUpdate,
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
):
    item = _get(session, ctx.organization_id, opportunity_id)
    if body.status is not None:
        if body.status not in STAGES:
            raise HTTPException(status_code=422, detail="Unknown TikTok workflow stage")
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
def approve(
    opportunity_id: int,
    body: ApprovalRequest,
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
):
    item = _get(session, ctx.organization_id, opportunity_id)
    if not body.human_approved:
        raise HTTPException(
            status_code=422, detail="A person must approve the personalized TikTok contact"
        )
    item.permission_basis = body.permission_basis.strip()
    item.human_approved_at = datetime.now(UTC)
    item.status = "dm_ready"
    session.commit()
    session.refresh(item)
    return _opportunity_dict(item)


@router.post("/opportunities/{opportunity_id}/mark-contacted")
def contacted(
    opportunity_id: int,
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
):
    item = _get(session, ctx.organization_id, opportunity_id)
    if not item.human_approved_at or not item.permission_basis:
        raise HTTPException(
            status_code=409, detail="Approve the personalized contact before recording it"
        )
    item.contacted_at = datetime.now(UTC)
    item.status = "contacted"
    session.commit()
    session.refresh(item)
    return _opportunity_dict(item)
