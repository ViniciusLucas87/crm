"""
Email Copilot — professional email generation for enterprise software sales.

All engines consume ONLY OpportunityIntelligence.
Never ConversationInsights. Never transcript. Never performs business analysis.

Architecture:
    OpportunityIntelligence → EmailCopilot → Professional Email
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC


# ═══════════════════════════════════════════════════════════
# EMAIL CONTEXT
# ═══════════════════════════════════════════════════════════

@dataclass
class EmailContext:
    """Aggregated context for email generation from OpportunityIntelligence."""
    company_name: str = ""
    contact_name: str = ""
    contact_title: str = ""
    contact_email: str = ""
    opportunity_stage: str = ""
    deal_health: str = ""
    proposal_status: str = ""
    last_activity: str = ""
    last_meeting_date: str = ""
    next_action: str = ""
    buying_signals: list[str] = field(default_factory=list)
    objections: list[str] = field(default_factory=list)
    pain_points: list[str] = field(default_factory=list)
    business_goals: list[str] = field(default_factory=list)
    recommended_products: list[str] = field(default_factory=list)
    timeline: str = ""
    budget: str = ""
    decision_makers: list[str] = field(default_factory=list)
    previous_activities: list[str] = field(default_factory=list)
    previous_emails: list[str] = field(default_factory=list)
    generated_at: str = ""


# ═══════════════════════════════════════════════════════════
# EMAIL STRATEGY
# ═══════════════════════════════════════════════════════════

class EmailPurpose:
    DISCOVERY_FOLLOWUP = "discovery_followup"
    PROPOSAL_DELIVERY = "proposal_delivery"
    PROPOSAL_REMINDER = "proposal_reminder"
    MEETING_SCHEDULING = "meeting_scheduling"
    MEETING_CONFIRMATION = "meeting_confirmation"
    MEETING_RECAP = "meeting_recap"
    OBJECTION_RESPONSE = "objection_response"
    BUDGET_DISCUSSION = "budget_discussion"
    TECHNICAL_CLARIFICATION = "technical_clarification"
    CONTRACT_FOLLOWUP = "contract_followup"
    IMPLEMENTATION_KICKOFF = "implementation_kickoff"
    CUSTOMER_CHECKIN = "customer_checkin"
    REENGAGEMENT = "reengagement"
    LOST_RECOVERY = "lost_recovery"
    THANK_YOU = "thank_you"
    REFERRAL_REQUEST = "referral_request"


class EmailType:
    SHORT = "short"
    STANDARD = "standard"
    EXECUTIVE_SUMMARY = "executive_summary"
    TECHNICAL = "technical"
    FRIENDLY = "friendly"
    FORMAL = "formal"
    FOLLOWUP = "followup"
    REMINDER = "reminder"


@dataclass
class EmailStrategy:
    purpose: str = EmailPurpose.DISCOVERY_FOLLOWUP
    email_type: str = EmailType.STANDARD
    tone: str = "professional"
    focus_points: list[str] = field(default_factory=list)
    avoid_topics: list[str] = field(default_factory=list)
    generated_at: str = ""


# ═══════════════════════════════════════════════════════════
# EMAIL DRAFT
# ═══════════════════════════════════════════════════════════

@dataclass
class EmailDraft:
    subject: str = ""
    preview: str = ""
    greeting: str = ""
    opening: str = ""
    body: str = ""
    call_to_action: str = ""
    signature: str = ""
    strategy: EmailStrategy | None = None
    generated_at: str = ""


# ═══════════════════════════════════════════════════════════
# TEMPLATE
# ═══════════════════════════════════════════════════════════

@dataclass
class EmailTemplate:
    id: str
    name: str
    description: str
    purpose: str
    subject_template: str
    body_template: str
    variables: list[str] = field(default_factory=list)
    tone: str = "professional"


# ═══════════════════════════════════════════════════════════
# EMAIL REVIEW
# ═══════════════════════════════════════════════════════════

@dataclass
class EmailReview:
    professionalism: int = 0
    clarity: int = 0
    tone_score: int = 0
    grammar_score: int = 0
    business_accuracy: int = 0
    opportunity_consistency: int = 0
    call_to_action_score: int = 0
    length_score: int = 0
    overall_score: int = 0
    suggestions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    ready_to_send: bool = False
    generated_at: str = ""
