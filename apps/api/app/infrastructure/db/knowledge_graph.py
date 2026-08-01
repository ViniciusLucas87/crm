"""
Knowledge Graph — Phase 1: Core Models

The Knowledge Graph is the single source of truth for all business intelligence.
Every AI module reads from and writes to the graph. No module owns its own memory.

Architecture:
    Layer 1: KnowledgeFact — immutable facts with source/confidence/history
    Layer 2: KnowledgeRelationship — connections between entities
    Layer 3: KnowledgeEvent — immutable event log for everything
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Integer, String, Text, Index, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base


# ═══════════════════════════════════════════════════════════
# LAYER 1 — FACTS (versioned, sourced, confidence-tracked)
# ═══════════════════════════════════════════════════════════

class KnowledgeFact(Base):
    """A single independently versioned fact about any entity.

    Facts are NOT entity properties — they're independent objects with full
    provenance: source, confidence, verification status, and immutable history.

    Example facts:
        entity_type="company", entity_id=42, key="employees", value="145"
        entity_type="company", entity_id=42, key="uses_software", value="Procore"
        entity_type="company", entity_id=42, key="pain_point", value="Manual Reporting"
        entity_type="contact", entity_id=7, key="decision_maker_for", value="ERP Purchase"
    """
    __tablename__ = "knowledge_facts"
    __table_args__ = (
        Index("idx_kf_entity", "entity_type", "entity_id"),
        Index("idx_kf_key", "key"),
        Index("idx_kf_confidence", "confidence"),
        UniqueConstraint("entity_type", "entity_id", "key", name="uq_entity_fact"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))

    # ── Target entity ──
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # ── Fact ──
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    value_type: Mapped[str] = mapped_column(String(20), default="string")  # string | number | boolean | json | date

    # ── Provenance ──
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="manual")
    source_detail: Mapped[str | None] = mapped_column(String(255), nullable=True)  # "LinkedIn API", "Lead Discovery Engine"
    confidence: Mapped[float] = mapped_column(Float, default=0.5)

    # ── Verification ──
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Status ──
    status: Mapped[str] = mapped_column(String(20), default="active")  # active | outdated | disputed | expired
    manual_override: Mapped[bool] = mapped_column(Boolean, default=False)  # User explicitly set this

    # ── Expiration ──
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Audit ──
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)


class KnowledgeFactHistory(Base):
    """Immutable history of every change to a fact."""
    __tablename__ = "knowledge_fact_history"
    __table_args__ = (Index("idx_kfh_fact", "fact_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    fact_id: Mapped[int] = mapped_column(ForeignKey("knowledge_facts.id", ondelete="CASCADE"), nullable=False)
    previous_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str] = mapped_column(Text, nullable=False)
    previous_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    new_confidence: Mapped[float] = mapped_column(Float, default=0.5)
    previous_source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    new_source: Mapped[str] = mapped_column(String(50), nullable=False)
    changed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)


# ═══════════════════════════════════════════════════════════
# LAYER 2 — RELATIONSHIPS
# ═══════════════════════════════════════════════════════════

class KnowledgeRelationship(Base):
    """A typed directed relationship between any two graph entities.

    Examples:
        (contact, WORKS_FOR, company)
        (employee, REPORTS_TO, employee)
        (company, USES, technology)
        (company, HAS_PAIN_POINT, pain_point_description)
        (call, DISCUSSED, opportunity)
        (proposal, GENERATED_FROM, meeting)
    """
    __tablename__ = "knowledge_relationships"
    __table_args__ = (
        Index("idx_kr_from", "from_type", "from_id"),
        Index("idx_kr_to", "to_type", "to_id"),
        Index("idx_kr_rel_type", "relationship_type"),
        UniqueConstraint("from_type", "from_id", "to_type", "to_id", "relationship_type", name="uq_relationship"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))

    # ── Source ──
    from_type: Mapped[str] = mapped_column(String(50), nullable=False)
    from_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # ── Relationship ──
    relationship_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # ── Target ──
    to_type: Mapped[str] = mapped_column(String(50), nullable=False)
    to_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # ── Metadata ──
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    source: Mapped[str] = mapped_column(String(50), default="manual")
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active | removed | disputed

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)


# ═══════════════════════════════════════════════════════════
# LAYER 3 — EVENTS (immutable log)
# ═══════════════════════════════════════════════════════════

class KnowledgeEvent(Base):
    """Immutable event log — every significant action is recorded forever.

    Events are NEVER modified or deleted. This is the audit trail for
    everything that happens in the knowledge graph.
    """
    __tablename__ = "knowledge_events"
    __table_args__ = (
        Index("idx_ke_entity", "entity_type", "entity_id"),
        Index("idx_ke_type", "event_type"),
        Index("idx_ke_created", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))

    # ── Event identity ──
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # Types: fact_created, fact_updated, fact_verified, fact_expired,
    #        relationship_created, relationship_removed,
    #        company_created, lead_imported, call_started, call_ended,
    #        transcript_received, buying_signal_detected, pain_point_detected,
    #        proposal_generated, email_sent, task_completed,
    #        opportunity_updated, knowledge_merged, knowledge_resolved

    # ── Target entity ──
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # ── Event data ──
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Actor ──
    actor_type: Mapped[str] = mapped_column(String(20), default="system")  # system | user | ai
    actor_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # ── Organization scope ──
    organization_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True)
