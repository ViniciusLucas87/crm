"""
Meeting Copilot — prepares, guides, and follows up on every sales meeting.

All engines consume ONLY OpportunityIntelligence.
Never ConversationInsights. Never transcript.

Architecture:
    OpportunityIntelligence → MeetingCopilot → Briefing + Agenda + Guidance + Summary
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC


@dataclass
class MeetingBrief:
    """Complete pre-meeting briefing for the salesperson."""
    company_name: str = ""
    industry: str = ""
    stakeholders: list[dict] = field(default_factory=list)
    decision_makers: list[str] = field(default_factory=list)
    previous_meetings: list[str] = field(default_factory=list)
    current_stage: str = ""
    proposal_status: str = ""
    pain_points: list[str] = field(default_factory=list)
    business_goals: list[str] = field(default_factory=list)
    buying_signals: list[str] = field(default_factory=list)
    objections: list[str] = field(default_factory=list)
    recommended_strategy: str = ""
    estimated_duration: str = "30 minutes"
    meeting_objective: str = ""
    generated_at: str = ""


@dataclass
class AgendaItem:
    topic: str
    duration: str = ""
    description: str = ""
    priority: str = "medium"


@dataclass
class MeetingAgenda:
    title: str = ""
    items: list[AgendaItem] = field(default_factory=list)
    total_duration: str = ""
    meeting_objective: str = ""
    generated_at: str = ""


@dataclass
class DiscoveryQuestion:
    category: str  # discovery, business, technical, operational, financial, decision_making, implementation, risk
    question: str
    priority: int = 5
    answered: bool = False
    reason: str = ""


@dataclass
class QuestionPlan:
    questions: list[DiscoveryQuestion] = field(default_factory=list)
    answered_count: int = 0
    total_count: int = 0
    missing_categories: list[str] = field(default_factory=list)
    generated_at: str = ""


@dataclass
class LiveGuidance:
    missing_topics: list[str] = field(default_factory=list)
    recommended_questions: list[str] = field(default_factory=list)
    buying_signals_detected: list[str] = field(default_factory=list)
    objections_detected: list[str] = field(default_factory=list)
    deal_health: str = ""
    opportunity_score: int = 0
    discovery_progress: int = 0
    recommended_next_action: str = ""
    generated_at: str = ""


@dataclass
class MeetingSummary:
    executive_summary: str = ""
    topics_discussed: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    risks_identified: list[str] = field(default_factory=list)
    customer_goals: list[str] = field(default_factory=list)
    pain_points_discussed: list[str] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    generated_at: str = ""


@dataclass
class ActionItem:
    description: str
    owner: str  # customer, salesperson, technical, management
    deadline: str = ""
    priority: str = "medium"


@dataclass
class ActionPlan:
    items: list[ActionItem] = field(default_factory=list)
    customer_items: list[ActionItem] = field(default_factory=list)
    salesperson_items: list[ActionItem] = field(default_factory=list)
    technical_items: list[ActionItem] = field(default_factory=list)
    management_items: list[ActionItem] = field(default_factory=list)
    generated_at: str = ""


@dataclass
class FollowUpPlan:
    meeting_recap: str = ""
    suggested_email: str = ""
    crm_activity: str = ""
    next_meeting: str = ""
    proposal_recommendation: str = ""
    generated_at: str = ""
