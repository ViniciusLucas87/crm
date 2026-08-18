"""Permission based Reddit lead intelligence and outreach workspace."""

import json
import os
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.infrastructure.auth.clerk import AuthContext, require_permission
from app.infrastructure.db.session import get_db_session
from app.infrastructure.db.social_leads import SocialLeadCampaign, SocialLeadOpportunity

router = APIRouter(prefix="/reddit", tags=["reddit-leads"])

STAGES = (
    "watch",
    "public_reply_ready",
    "engaged",
    "permission_received",
    "dm_ready",
    "contacted",
    "follow_up",
    "won",
    "closed",
)
DEFAULT_COMMUNITIES = [
    "Contractor",
    "Construction",
    "HVAC",
    "electricians",
    "plumbing",
    "smallbusinesscanada",
    "vancouver",
]
DEFAULT_SIGNALS = [
    "missed calls",
    "cannot answer the phone",
    "lost jobs",
    "voicemail",
    "too busy on site",
    "customers call while working",
    "need someone to answer",
    "follow up is difficult",
]


def _campaign_dict(campaign: SocialLeadCampaign) -> dict[str, Any]:
    return {
        "id": campaign.id,
        "channel": campaign.channel,
        "name": campaign.name,
        "product_code": campaign.product_code,
        "audience": campaign.audience,
        "communities": json.loads(campaign.communities_json or "[]"),
        "pain_signals": json.loads(campaign.pain_signals_json or "[]"),
        "offer_summary": campaign.offer_summary,
        "public_reply_guidance": campaign.public_reply_guidance,
        "dm_guidance": campaign.dm_guidance,
        "status": campaign.status,
    }


def _opportunity_dict(item: SocialLeadOpportunity) -> dict[str, Any]:
    return {
        "id": item.id,
        "campaign_id": item.campaign_id,
        "channel": item.channel,
        "community": item.community,
        "author_handle": item.author_handle,
        "post_title": item.post_title,
        "post_excerpt": item.post_excerpt,
        "source_url": item.source_url,
        "relevance_score": item.relevance_score,
        "relevance_reason": item.relevance_reason,
        "detected_signals": json.loads(item.detected_signals_json or "[]"),
        "status": item.status,
        "public_reply_draft": item.public_reply_draft,
        "dm_draft": item.dm_draft,
        "permission_basis": item.permission_basis,
        "human_approved_at": item.human_approved_at,
        "contacted_at": item.contacted_at,
        "response_summary": item.response_summary,
        "next_follow_up_at": item.next_follow_up_at,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


def _never_miss_campaign(session: Session, organization_id: int) -> SocialLeadCampaign:
    campaign = session.execute(
        select(SocialLeadCampaign).where(
            SocialLeadCampaign.organization_id == organization_id,
            SocialLeadCampaign.channel == "reddit",
            SocialLeadCampaign.product_code == "never_miss",
        )
    ).scalar_one_or_none()
    if campaign:
        return campaign

    campaign = SocialLeadCampaign(
        organization_id=organization_id,
        channel="reddit",
        name="Never Miss contractor pilot",
        product_code="never_miss",
        audience="Canadian contractors and service business owners who lose calls while working on site",
        communities_json=json.dumps(DEFAULT_COMMUNITIES),
        pain_signals_json=json.dumps(DEFAULT_SIGNALS),
        offer_summary="Never Miss texts callers after an unanswered business call and organizes the callback without changing the advertised business number.",
        public_reply_guidance="Be useful first. Address the exact problem in the post. Mention Never Miss only when it directly helps. Never pretend to be a customer or hide the PNS connection.",
        dm_guidance="Send only after the person asks for details or clearly accepts contact. Refer to the exact conversation, identify yourself as Vini from Pacific North Systems, and ask one simple question.",
    )
    session.add(campaign)
    session.commit()
    session.refresh(campaign)
    return campaign


class OpportunityCreate(BaseModel):
    campaign_id: int | None = None
    community: str = Field(min_length=1, max_length=120)
    author_handle: str = Field(min_length=1, max_length=120)
    post_title: str = Field(min_length=1, max_length=500)
    post_excerpt: str = Field(min_length=1, max_length=6000)
    source_url: HttpUrl
    relevance_score: int = Field(default=50, ge=0, le=100)
    relevance_reason: str = Field(min_length=1, max_length=3000)
    detected_signals: list[str] = []


class OpportunityUpdate(BaseModel):
    status: str | None = None
    permission_basis: str | None = Field(default=None, max_length=3000)
    response_summary: str | None = Field(default=None, max_length=5000)
    next_follow_up_at: datetime | None = None


class ApprovalRequest(BaseModel):
    human_approved: bool
    permission_basis: str = Field(min_length=5, max_length=3000)


@router.get("/status")
def reddit_status(ctx: AuthContext = Depends(require_permission("companies:read"))):
    configured = bool(os.getenv("REDDIT_CLIENT_ID") and os.getenv("REDDIT_CLIENT_SECRET"))
    access_status = os.getenv("REDDIT_ACCESS_STATUS", "").strip().lower()
    approval_pending = access_status == "pending_approval"
    return {
        "connected": False,
        "api_configured": configured,
        "access_status": "pending_approval" if approval_pending else ("configured" if configured else "not_requested"),
        "mode": "human_approved_outreach",
        "message": (
            "Reddit commercial API access was requested. Approval is pending. Manual conversation intake remains available."
            if approval_pending
            else (
                "Connect a registered Reddit application to monitor approved public communities."
                if configured
                else "Reddit application credentials are required before live monitoring can start."
            )
        ),
        "rules": [
            "Public conversation monitoring only",
            "No automated unsolicited private messages",
            "AI drafts require human review",
            "Direct messages require a recorded invitation or clear permission",
        ],
    }


@router.get("/campaigns")
def list_campaigns(
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    _never_miss_campaign(session, ctx.organization_id)
    campaigns = (
        session.execute(
            select(SocialLeadCampaign)
            .where(
                SocialLeadCampaign.organization_id == ctx.organization_id,
                SocialLeadCampaign.channel == "reddit",
            )
            .order_by(SocialLeadCampaign.created_at.desc())
        )
        .scalars()
        .all()
    )
    return {"items": [_campaign_dict(item) for item in campaigns]}


@router.get("/opportunities")
def list_opportunities(
    status: str = "",
    limit: int = Query(50, ge=1, le=100),
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    stmt = select(SocialLeadOpportunity).where(
        SocialLeadOpportunity.organization_id == ctx.organization_id,
        SocialLeadOpportunity.channel == "reddit",
    )
    if status:
        stmt = stmt.where(SocialLeadOpportunity.status == status)
    items = (
        session.execute(
            stmt.order_by(
                SocialLeadOpportunity.relevance_score.desc(),
                SocialLeadOpportunity.created_at.desc(),
            ).limit(limit)
        )
        .scalars()
        .all()
    )
    return {"items": [_opportunity_dict(item) for item in items], "total": len(items)}


@router.post("/opportunities")
def create_opportunity(
    body: OpportunityCreate,
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
):
    campaign = _never_miss_campaign(session, ctx.organization_id)
    if body.campaign_id:
        campaign = session.execute(
            select(SocialLeadCampaign).where(
                SocialLeadCampaign.id == body.campaign_id,
                SocialLeadCampaign.organization_id == ctx.organization_id,
            )
        ).scalar_one_or_none()
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

    item = SocialLeadOpportunity(
        organization_id=ctx.organization_id,
        campaign_id=campaign.id,
        channel="reddit",
        community=body.community.removeprefix("r/"),
        author_handle=body.author_handle.removeprefix("u/"),
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
            status_code=409, detail="This Reddit conversation is already in your workspace"
        ) from exc
    session.refresh(item)
    return _opportunity_dict(item)


@router.post("/opportunities/{opportunity_id}/draft")
def prepare_drafts(
    opportunity_id: int,
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
):
    item = session.execute(
        select(SocialLeadOpportunity).where(
            SocialLeadOpportunity.id == opportunity_id,
            SocialLeadOpportunity.organization_id == ctx.organization_id,
        )
    ).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Reddit opportunity not found")

    item.public_reply_draft = (
        "That is frustrating. I ran into this exact problem and built a small solution for it. "
        "You keep your business number, callers get a text when you cannot answer, and you get a simple callback list. "
        "If it helps, I can explain how I set it up."
    )
    item.dm_draft = (
        f"Hi {item.author_handle}, Vini here from Pacific North Systems. Thanks for the conversation in r/{item.community}. "
        "You mentioned the challenge of staying on top of calls while working. We built Never Miss to text callers after an unanswered call while you keep your existing number. "
        "Would you like a quick explanation of how it would work with your current phone setup?"
    )
    item.status = "public_reply_ready"
    session.commit()
    session.refresh(item)
    return _opportunity_dict(item)


@router.patch("/opportunities/{opportunity_id}")
def update_opportunity(
    opportunity_id: int,
    body: OpportunityUpdate,
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
):
    item = session.execute(
        select(SocialLeadOpportunity).where(
            SocialLeadOpportunity.id == opportunity_id,
            SocialLeadOpportunity.organization_id == ctx.organization_id,
        )
    ).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Reddit opportunity not found")
    if body.status is not None:
        if body.status not in STAGES:
            raise HTTPException(status_code=422, detail="Unknown Reddit workflow stage")
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
def approve_dm(
    opportunity_id: int,
    body: ApprovalRequest,
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
):
    item = session.execute(
        select(SocialLeadOpportunity).where(
            SocialLeadOpportunity.id == opportunity_id,
            SocialLeadOpportunity.organization_id == ctx.organization_id,
        )
    ).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Reddit opportunity not found")
    if not body.human_approved:
        raise HTTPException(status_code=422, detail="A person must approve the message")
    item.permission_basis = body.permission_basis.strip()
    item.human_approved_at = datetime.now(UTC)
    item.status = "dm_ready"
    session.commit()
    session.refresh(item)
    return _opportunity_dict(item)


@router.post("/opportunities/{opportunity_id}/mark-contacted")
def mark_contacted(
    opportunity_id: int,
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
):
    item = session.execute(
        select(SocialLeadOpportunity).where(
            SocialLeadOpportunity.id == opportunity_id,
            SocialLeadOpportunity.organization_id == ctx.organization_id,
        )
    ).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Reddit opportunity not found")
    if not item.human_approved_at or not item.permission_basis:
        raise HTTPException(
            status_code=409,
            detail="Record the person's permission and approve the draft before contact",
        )
    item.contacted_at = datetime.now(UTC)
    item.status = "contacted"
    session.commit()
    session.refresh(item)
    return _opportunity_dict(item)


@router.post("/scan")
def scan_public_conversations(
    ctx: AuthContext = Depends(require_permission("companies:write")),
):
    if not (os.getenv("REDDIT_CLIENT_ID") and os.getenv("REDDIT_CLIENT_SECRET")):
        raise HTTPException(
            status_code=503,
            detail="Connect a registered Reddit application before live monitoring can start",
        )
    return {
        "status": "connection_required",
        "message": "Reddit OAuth authorization is required. The CRM will not scrape Reddit or automate unsolicited messages.",
    }
