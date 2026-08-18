"""Isolated persistence for PNS App Factory research and validation."""

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base


class AppFactoryCandidate(Base):
    __tablename__ = "app_factory_candidates"
    __table_args__ = (
        UniqueConstraint("organization_id", "slug", name="uq_app_factory_candidate_org_slug"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    audience: Mapped[str] = mapped_column(Text, nullable=False)
    problem: Mapped[str] = mapped_column(Text, nullable=False)
    proposed_format: Mapped[str] = mapped_column(String(40), nullable=False)
    proposed_price: Mapped[str] = mapped_column(String(120), nullable=False)
    distribution_thesis: Mapped[str] = mapped_column(Text, nullable=False)
    current_workaround: Mapped[str] = mapped_column(Text, nullable=False)
    decision: Mapped[str] = mapped_column(
        String(30), default="research", nullable=False, index=True
    )
    decision_reason: Mapped[str] = mapped_column(Text, nullable=False)
    score_json: Mapped[str] = mapped_column(Text, nullable=False)
    total_score: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    estimated_monthly_cost_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), default="low", nullable=False)
    evidence_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class AppFactoryEvidence(Base):
    __tablename__ = "app_factory_evidence"
    __table_args__ = (
        UniqueConstraint("candidate_id", "source_url", name="uq_app_factory_evidence_source"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("app_factory_candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_type: Mapped[str] = mapped_column(String(40), nullable=False)
    source_title: Mapped[str] = mapped_column(String(500), nullable=False)
    source_url: Mapped[str] = mapped_column(String(1200), nullable=False)
    observed_at: Mapped[str] = mapped_column(String(30), nullable=False)
    signal: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_kind: Mapped[str] = mapped_column(String(40), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class AppFactoryExperiment(Base):
    __tablename__ = "app_factory_experiments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("app_factory_candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hypothesis: Mapped[str] = mapped_column(Text, nullable=False)
    channel: Mapped[str] = mapped_column(String(80), nullable=False)
    success_metric: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="proposed", nullable=False, index=True)
    spend_limit_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    actual_spend_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    visitors: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    intent_actions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    paid_conversions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    result_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
