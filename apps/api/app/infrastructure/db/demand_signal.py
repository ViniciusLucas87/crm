"""
Demand Intelligence — Signal Persistence Model

Stores classified buying signals discovered from external sources.
Each signal is enriched with lead scoring, recommended actions, and knowledge graph links.
"""

from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base


class DemandSignal(Base):
    """A classified buying signal with lead scoring and action recommendations."""

    __tablename__ = "demand_signals"
    __table_args__ = (
        Index("idx_ds_source", "source"),
        Index("idx_ds_pain_type", "pain_type"),
        Index("idx_ds_lead_score", "lead_score"),
        Index("idx_ds_processed_at", "processed_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # ── Source ──
    source: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    source_url: Mapped[str] = mapped_column(String(2048), default="")

    # ── Content ──
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    author_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # ── Classification ──
    pain_type: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    urgency: Mapped[str] = mapped_column(String(20), default="medium")
    buying_intent: Mapped[int] = mapped_column(Integer, default=0)
    lead_score: Mapped[int] = mapped_column(Integer, default=0, index=True)
    recommended_action: Mapped[str] = mapped_column(String(50), default="monitor")
    confidence: Mapped[float] = mapped_column(Float, default=0.5)

    # ── Metadata ──
    technologies: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array
    keywords: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array
    raw_data: Mapped[str | None] = mapped_column(Text, nullable=True)  # Full raw JSON

    # ── Timestamps ──
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
