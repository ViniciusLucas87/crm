"""
Opportunity Intelligence — canonical business representation of a sales opportunity.

This is the single source of truth for every AI capability (Coach, Proposal,
Email, Meetings, Analytics, Workflow). No module should independently interpret
ConversationInsights — they all consume OpportunityIntelligence.

Architecture:
    Transcript → Conversation Intelligence → Decision Engine
                                                    ↓
                                          OpportunityIntelligence
                                                    ↓
              ┌──────────────────────────────────────┼──────────────────────────┐
              ↓               ↓               ↓               ↓                ↓
         AI Coach     Proposal Studio   Email Copilot   Meeting Copilot   Analytics
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import StrEnum
from decimal import Decimal
from typing import Any, Generic, TypeVar


# ═══════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════

class OpportunityStage(StrEnum):
    LEAD = "lead"
    QUALIFIED = "qualified"
    DISCOVERY = "discovery"
    SOLUTION_DESIGN = "solution_design"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    WON = "won"
    IMPLEMENTATION = "implementation"
    SUPPORT = "support"
    LOST = "lost"


class OpportunityStatus(StrEnum):
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class StakeholderRole(StrEnum):
    DECISION_MAKER = "decision_maker"
    CHAMPION = "champion"
    INFLUENCER = "influencer"
    TECHNICAL = "technical"
    FINANCE = "finance"
    END_USER = "end_user"
    OTHER = "other"


class CustomerType(StrEnum):
    OPERATIONAL = "operational"
    STRATEGIC = "strategic"
    FINANCIAL = "financial"
    TECHNICAL = "technical"
    UNKNOWN = "unknown"


class UrgencyLevel(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class EventType(StrEnum):
    CALL = "call"
    EMAIL = "email"
    MEETING = "meeting"
    ACTIVITY = "activity"
    PAIN_POINT_DISCOVERED = "pain_point_discovered"
    BUDGET_IDENTIFIED = "budget_identified"
    DECISION_MAKER_IDENTIFIED = "decision_maker_identified"
    PROPOSAL_GENERATED = "proposal_generated"
    PROPOSAL_SENT = "proposal_sent"
    STAGE_CHANGED = "stage_changed"
    INSIGHT_EXTRACTED = "insight_extracted"
    OBJECTION_RAISED = "objection_raised"
    OBJECTION_RESOLVED = "objection_resolved"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"
    NOTE_ADDED = "note_added"
    TASK_CREATED = "task_created"


STAGE_TRANSITIONS: dict[OpportunityStage, list[OpportunityStage]] = {
    OpportunityStage.LEAD: [OpportunityStage.QUALIFIED, OpportunityStage.LOST],
    OpportunityStage.QUALIFIED: [OpportunityStage.DISCOVERY, OpportunityStage.LOST],
    OpportunityStage.DISCOVERY: [OpportunityStage.SOLUTION_DESIGN, OpportunityStage.LOST],
    OpportunityStage.SOLUTION_DESIGN: [OpportunityStage.PROPOSAL, OpportunityStage.LOST],
    OpportunityStage.PROPOSAL: [OpportunityStage.NEGOTIATION, OpportunityStage.LOST],
    OpportunityStage.NEGOTIATION: [OpportunityStage.WON, OpportunityStage.LOST],
    OpportunityStage.WON: [OpportunityStage.IMPLEMENTATION],
    OpportunityStage.IMPLEMENTATION: [OpportunityStage.SUPPORT],
    OpportunityStage.SUPPORT: [],
    OpportunityStage.LOST: [],
}


# ═══════════════════════════════════════════════════════════
# TYPED VALUE — every field carries confidence
# ═══════════════════════════════════════════════════════════

T = TypeVar("T")


@dataclass
class TypedValue(Generic[T]):
    """A value with confidence, source, and timestamp.
    
    Every field in OpportunityIntelligence uses this to track provenance.
    """
    value: T | None = None
    confidence: int = 0  # 0-100
    source: str = ""  # "conversation", "crm", "manual", "ai"
    updated_at: str = ""

    @classmethod
    def empty(cls) -> TypedValue:
        return cls(value=None, confidence=0, source="", updated_at="")

    @classmethod
    def from_value(cls, value: T, source: str = "crm", confidence: int = 95) -> TypedValue:
        return cls(value=value, confidence=confidence, source=source, updated_at=datetime.now(UTC).isoformat())

    def is_known(self) -> bool:
        return self.value is not None and self.confidence > 0


# ═══════════════════════════════════════════════════════════
# STAKEHOLDER
# ═══════════════════════════════════════════════════════════

@dataclass
class Stakeholder:
    id: int | None = None
    name: str = ""
    title: str = ""
    email: str = ""
    phone: str = ""
    role: StakeholderRole = StakeholderRole.OTHER
    is_primary: bool = False
    confidence: int = 0
    source: str = ""


# ═══════════════════════════════════════════════════════════
# BUSINESS CONTEXT
# ═══════════════════════════════════════════════════════════

@dataclass
class BusinessContext:
    current_process: list[TypedValue[str]] = field(default_factory=list)
    current_software: list[TypedValue[str]] = field(default_factory=list)
    business_goals: list[TypedValue[str]] = field(default_factory=list)
    pain_points: list[TypedValue[str]] = field(default_factory=list)
    manual_work_indicators: list[str] = field(default_factory=list)
    operational_risks: list[TypedValue[str]] = field(default_factory=list)
    constraints: list[TypedValue[str]] = field(default_factory=list)
    compliance_requirements: list[TypedValue[str]] = field(default_factory=list)
    implementation_window: TypedValue[str] = field(default_factory=TypedValue.empty)
    budget: TypedValue[int] = field(default_factory=TypedValue.empty)  # normalized to int
    budget_raw: str = ""
    timeline: TypedValue[str] = field(default_factory=TypedValue.empty)


# ═══════════════════════════════════════════════════════════
# SALES CONTEXT
# ═══════════════════════════════════════════════════════════

@dataclass
class SalesContext:
    buying_signals: list[TypedValue[str]] = field(default_factory=list)
    objections: list[TypedValue[str]] = field(default_factory=list)
    urgency: TypedValue[UrgencyLevel] = field(default_factory=TypedValue.empty)
    priority: TypedValue[str] = field(default_factory=TypedValue.empty)
    customer_type: TypedValue[CustomerType] = field(default_factory=TypedValue.empty)
    sales_strategy: str = ""
    next_best_action: str = ""
    next_best_question: str = ""
    current_milestone: str = ""
    recommended_followup: str = ""


# ═══════════════════════════════════════════════════════════
# SOLUTION CONTEXT
# ═══════════════════════════════════════════════════════════

@dataclass
class SolutionContext:
    recommended_products: list[dict[str, Any]] = field(default_factory=list)
    recommended_services: list[str] = field(default_factory=list)
    recommended_integrations: list[str] = field(default_factory=list)
    estimated_roi: str = ""
    estimated_savings: str = ""
    estimated_complexity: str = ""
    proposal_status: str = "none"
    proposal_quality: int = 0


# ═══════════════════════════════════════════════════════════
# TIMELINE EVENT
# ═══════════════════════════════════════════════════════════

@dataclass
class TimelineEvent:
    event_type: EventType
    description: str = ""
    timestamp: str = ""
    source: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════
# OPPORTUNITY INTELLIGENCE — canonical business object
# ═══════════════════════════════════════════════════════════

@dataclass
class OpportunityIntelligence:
    """Canonical representation of a sales opportunity.

    This is the single source of truth consumed by every AI module.
    Aggregates and normalizes data from conversations, CRM, activities,
    calls, and proposals.

    No AI module should independently interpret ConversationInsights —
    they all consume this object.
    """

    # ── Identity ──
    opportunity_id: int | None = None
    company_id: int | None = None
    organization_id: int | None = None

    # ── Core scores ──
    stage: OpportunityStage = OpportunityStage.LEAD
    status: OpportunityStatus = OpportunityStatus.ACTIVE
    deal_health: TypedValue[int] = field(default_factory=TypedValue.empty)
    opportunity_score: TypedValue[int] = field(default_factory=TypedValue.empty)
    discovery_score: TypedValue[int] = field(default_factory=TypedValue.empty)
    proposal_readiness: TypedValue[int] = field(default_factory=TypedValue.empty)

    # ── Company ──
    company_name: str = ""
    company_industry: str = ""
    company_employees: int | None = None
    company_revenue: Decimal | None = None
    company_locations: list[str] = field(default_factory=list)
    company_website: str = ""

    # ── Stakeholders ──
    stakeholders: list[Stakeholder] = field(default_factory=list)

    # ── Business ──
    business: BusinessContext = field(default_factory=BusinessContext)

    # ── Sales ──
    sales: SalesContext = field(default_factory=SalesContext)

    # ── Solutions ──
    solutions: SolutionContext = field(default_factory=SolutionContext)

    # ── History ──
    timeline: list[TimelineEvent] = field(default_factory=list)

    # ── Metadata ──
    confidence: int = 0
    source_count: int = 0
    last_updated: str = ""
    created_at: str = ""
    updated_at: str = ""

    # ── Raw data counts ──
    insight_count: int = 0
    call_count: int = 0
    email_count: int = 0
    meeting_count: int = 0
    activity_count: int = 0
    proposal_count: int = 0


# ═══════════════════════════════════════════════════════════
# FACTORY
# ═══════════════════════════════════════════════════════════

def create_empty_intelligence(
    opportunity_id: int | None = None,
    company_id: int | None = None,
    organization_id: int | None = None,
) -> OpportunityIntelligence:
    now = datetime.now(UTC).isoformat()
    return OpportunityIntelligence(
        opportunity_id=opportunity_id,
        company_id=company_id,
        organization_id=organization_id,
        created_at=now,
        updated_at=now,
    )
