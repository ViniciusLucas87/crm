"""Database models for reusable social lead campaigns."""

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base


class SocialLeadCampaign(Base):
    """Reusable social-listening campaign for one PNS product and audience."""

    __tablename__ = "social_lead_campaigns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(30), default="reddit", nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    product_code: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    audience: Mapped[str] = mapped_column(Text, nullable=False)
    communities_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    pain_signals_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    offer_summary: Mapped[str] = mapped_column(Text, nullable=False)
    public_reply_guidance: Mapped[str] = mapped_column(Text, nullable=False)
    dm_guidance: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class SocialLeadOpportunity(Base):
    """A public social conversation that may become a permission-based sales lead."""

    __tablename__ = "social_lead_opportunities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("social_lead_campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    channel: Mapped[str] = mapped_column(String(30), default="reddit", nullable=False, index=True)
    external_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    community: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    author_handle: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    post_title: Mapped[str] = mapped_column(String(500), nullable=False)
    post_excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    relevance_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    relevance_reason: Mapped[str] = mapped_column(Text, nullable=False)
    detected_signals_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="watch", nullable=False, index=True)
    public_reply_draft: Mapped[str | None] = mapped_column(Text, nullable=True)
    dm_draft: Mapped[str | None] = mapped_column(Text, nullable=True)
    permission_basis: Mapped[str | None] = mapped_column(Text, nullable=True)
    human_approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    contacted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    response_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_follow_up_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    owner_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
