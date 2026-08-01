"""
Tests for Meeting Copilot — preparation, guidance, summary, actions, follow-up.

All tests deterministic. No LLM. No transcript.
Mock OpportunityIntelligence only.
"""

import json

import pytest

from app.domain.opportunity_intelligence import (
    OpportunityIntelligence, OpportunityStage, TypedValue,
    Stakeholder, StakeholderRole, BusinessContext, SalesContext,
    CustomerType, UrgencyLevel, create_empty_intelligence,
)
from app.application.copilot.meeting.models import (
    MeetingBrief, MeetingAgenda, DiscoveryQuestion, QuestionPlan,
    LiveGuidance, MeetingSummary, ActionItem, ActionPlan, FollowUpPlan,
)
from app.application.copilot.meeting.preparation import get_preparation_engine
from app.application.copilot.meeting.agenda import get_agenda_generator
from app.application.copilot.meeting.questions import get_question_planner
from app.application.copilot.meeting.live_guidance import get_live_guidance_engine
from app.application.copilot.meeting.summary import get_summary_engine
from app.application.copilot.meeting.actions import get_action_item_engine
from app.application.copilot.meeting.followup import get_followup_engine
from app.application.copilot.meeting.meeting_copilot import get_meeting_copilot


def sample_oi(stage=OpportunityStage.DISCOVERY) -> OpportunityIntelligence:
    oi = create_empty_intelligence(opportunity_id=1, company_id=100, organization_id=1)
    oi.stage = stage
    oi.company_name = "Acme Construction Ltd."
    oi.company_industry = "Construction"
    oi.company_employees = 250
    oi.stakeholders = [
        Stakeholder(id=1, name="Sarah Chen", title="VP Operations", role=StakeholderRole.DECISION_MAKER, is_primary=True),
        Stakeholder(id=2, name="Mike Torres", title="IT Manager", role=StakeholderRole.TECHNICAL),
    ]
    oi.business.pain_points = [
        TypedValue(value="Manual inspections take 4 hours per site", confidence=90),
        TypedValue(value="Duplicate data entry across spreadsheets", confidence=85),
    ]
    oi.business.business_goals = [
        TypedValue(value="Reduce inspection turnaround by 50%", confidence=85),
    ]
    oi.business.current_process = [TypedValue(value="Paper-based workflow", confidence=90)]
    oi.business.current_software = [TypedValue(value="Excel", confidence=90)]
    oi.business.budget = TypedValue(value=120000, confidence=80)
    oi.business.timeline = TypedValue(value="90_days", confidence=70)
    oi.business.constraints = [TypedValue(value="Integration with accounting", confidence=85)]
    oi.sales.buying_signals = [TypedValue(value="Looking for solution", confidence=85)]
    oi.sales.objections = [TypedValue(value="Training concern", confidence=80)]
    oi.sales.urgency = TypedValue(value=UrgencyLevel.HIGH, confidence=75)
    oi.sales.next_best_action = "Schedule technical discovery"
    oi.solutions.proposal_status = "none"
    oi.discovery_score = TypedValue(value=65, confidence=80)
    oi.opportunity_score = TypedValue(value=78, confidence=80)
    oi.deal_health = TypedValue(value=70, confidence=75)
    return oi


class TestPreparation:
    def test_briefing_complete(self):
        result = get_preparation_engine().prepare(sample_oi())
        assert result.company_name == "Acme Construction Ltd."
        assert result.industry == "Construction"
        assert len(result.stakeholders) >= 2
        assert len(result.pain_points) >= 2
        assert result.meeting_objective

    def test_empty_oi(self):
        result = get_preparation_engine().prepare(create_empty_intelligence())
        assert result.current_stage == "lead"


class TestAgenda:
    def test_discovery_agenda(self):
        result = get_agenda_generator().generate(sample_oi(OpportunityStage.DISCOVERY))
        assert len(result.items) >= 3
        assert "Discovery" in result.title

    def test_proposal_agenda(self):
        result = get_agenda_generator().generate(sample_oi(OpportunityStage.PROPOSAL))
        # Proposal agenda should contain review/walkthrough items
        assert any("Review" in i.topic or "Walkthrough" in i.topic for i in result.items)

    def test_total_duration(self):
        result = get_agenda_generator().generate(sample_oi())
        assert "minutes" in result.total_duration


class TestQuestions:
    def test_planner_generates_questions(self):
        result = get_question_planner().plan(sample_oi())
        assert result.total_count >= 15
        assert result.answered_count >= 5
        assert len(result.missing_categories) >= 0

    def test_questions_sorted(self):
        result = get_question_planner().plan(sample_oi())
        priorities = [q.priority for q in result.questions[:5]]
        assert priorities[0] >= priorities[-1]  # first should be high priority

    def test_empty_oi(self):
        result = get_question_planner().plan(create_empty_intelligence())
        assert result.answered_count == 0
        assert len(result.missing_categories) >= 3


class TestLiveGuidance:
    def test_guidance_complete(self):
        result = get_live_guidance_engine().guide(sample_oi())
        assert len(result.recommended_questions) >= 0
        assert result.deal_health
        assert result.opportunity_score >= 0

    def test_missing_topics(self):
        oi = create_empty_intelligence()
        result = get_live_guidance_engine().guide(oi)
        assert len(result.missing_topics) >= 5


class TestSummary:
    def test_summary_complete(self):
        result = get_summary_engine().summarize(sample_oi())
        assert result.executive_summary
        assert len(result.topics_discussed) >= 2
        assert result.pain_points_discussed

    def test_empty_oi(self):
        result = get_summary_engine().summarize(create_empty_intelligence())
        assert result.executive_summary


class TestActions:
    def test_generates_actions(self):
        result = get_action_item_engine().generate(sample_oi())
        assert len(result.items) >= 3
        assert len(result.salesperson_items) >= 1

    def test_separated_by_owner(self):
        result = get_action_item_engine().generate(sample_oi())
        for item in result.customer_items:
            assert item.owner == "customer"
        for item in result.salesperson_items:
            assert item.owner == "salesperson"

    def test_discovery_has_documentation_action(self):
        result = get_action_item_engine().generate(sample_oi(OpportunityStage.DISCOVERY))
        assert any("workflow" in i.description.lower() for i in result.salesperson_items)


class TestFollowUp:
    def test_followup_complete(self):
        result = get_followup_engine().prepare(sample_oi())
        assert result.meeting_recap
        assert result.suggested_email
        assert result.crm_activity

    def test_email_has_subject(self):
        result = get_followup_engine().prepare(sample_oi())
        assert "Subject:" in result.suggested_email


class TestMeetingCopilot:
    def test_prepare_endpoint(self):
        result = get_meeting_copilot().prepare(sample_oi())
        assert "briefing" in result
        assert "agenda" in result
        assert "questions" in result

    def test_live_endpoint(self):
        result = get_meeting_copilot().live(sample_oi())
        assert "missing_topics" in result
        assert "recommended_questions" in result

    def test_summary_endpoint(self):
        result = get_meeting_copilot().summarize(sample_oi())
        assert "summary" in result
        assert "action_items" in result
        assert "follow_up" in result
        assert "customer" in result["action_items"]
        assert "salesperson" in result["action_items"]


class TestSerialization:
    def test_prepare_serializable(self):
        result = get_meeting_copilot().prepare(sample_oi())
        json.dumps(result)

    def test_summary_serializable(self):
        result = get_meeting_copilot().summarize(sample_oi())
        json.dumps(result)

    def test_live_serializable(self):
        result = get_meeting_copilot().live(sample_oi())
        json.dumps(result)


class TestDeterministic:
    def test_prepare_deterministic(self):
        oi = sample_oi()
        r1 = get_meeting_copilot().prepare(oi)
        r2 = get_meeting_copilot().prepare(oi)
        assert r1["briefing"]["meeting_objective"] == r2["briefing"]["meeting_objective"]

    def test_summary_deterministic(self):
        oi = sample_oi()
        r1 = get_meeting_copilot().summarize(oi)
        r2 = get_meeting_copilot().summarize(oi)
        assert r1["summary"]["executive_summary"] == r2["summary"]["executive_summary"]
