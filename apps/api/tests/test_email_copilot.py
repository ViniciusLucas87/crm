"""
Tests for Email Copilot — professional email generation for enterprise sales.

All tests deterministic. No LLM. No transcript.
Mock OpportunityIntelligence only.

Coverage:
    EmailContextBuilder, EmailStrategyEngine, EmailGenerator,
    EmailReviewEngine, Templates, EmailCopilot, Serialization.
"""

import json

import pytest

from app.domain.opportunity_intelligence import (
    OpportunityIntelligence, OpportunityStage, OpportunityStatus,
    TypedValue, Stakeholder, StakeholderRole, BusinessContext,
    SalesContext, SolutionContext, CustomerType, UrgencyLevel,
    create_empty_intelligence,
)
from app.application.copilot.email.models import (
    EmailContext, EmailStrategy, EmailDraft, EmailReview,
    EmailPurpose, EmailType,
)
from app.application.copilot.email.context_builder import (
    EmailContextBuilder, get_email_context_builder,
)
from app.application.copilot.email.strategy_engine import (
    EmailStrategyEngine, get_email_strategy_engine,
)
from app.application.copilot.email.generator import (
    EmailGenerator, get_email_generator,
)
from app.application.copilot.email.review_engine import (
    EmailReviewEngine, get_email_review_engine,
)
from app.application.copilot.email.templates import (
    get_template, list_templates, TEMPLATES,
)
from app.application.copilot.email.email_copilot import (
    EmailCopilot, get_email_copilot,
)


# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════

def sample_oi(stage: OpportunityStage = OpportunityStage.DISCOVERY) -> OpportunityIntelligence:
    oi = create_empty_intelligence(opportunity_id=1, company_id=100, organization_id=1)
    oi.stage = stage
    oi.company_name = "Acme Construction Ltd."
    oi.company_industry = "Construction"
    oi.company_employees = 250
    oi.company_locations = ["Vancouver, BC"]

    oi.stakeholders = [
        Stakeholder(id=1, name="Sarah Chen", title="VP Operations", email="sarah@acme.example.com",
                     role=StakeholderRole.DECISION_MAKER, is_primary=True),
        Stakeholder(id=2, name="Mike Torres", title="IT Manager", email="mike@acme.example.com",
                     role=StakeholderRole.TECHNICAL),
    ]

    oi.business.pain_points = [
        TypedValue(value="Manual inspections take 4 hours per site", confidence=90),
        TypedValue(value="Duplicate data entry across spreadsheets", confidence=85),
        TypedValue(value="Lost paperwork causing compliance issues", confidence=80),
    ]
    oi.business.business_goals = [
        TypedValue(value="Reduce inspection turnaround by 50%", confidence=85),
    ]
    oi.business.current_software = [
        TypedValue(value="Excel", confidence=90),
        TypedValue(value="QuickBooks", confidence=85),
    ]
    oi.business.current_process = [
        TypedValue(value="Field techs fill paper forms, office staff type them in", confidence=90),
    ]
    oi.business.budget = TypedValue(value=120000, confidence=80)
    oi.business.timeline = TypedValue(value="90_days", confidence=70)
    oi.business.constraints = [
        TypedValue(value="Must integrate with accounting system", confidence=85),
    ]

    oi.sales.buying_signals = [
        TypedValue(value="Looking for a solution for months", confidence=85),
    ]
    oi.sales.objections = [
        TypedValue(value="Worried about training time", confidence=80),
    ]
    oi.sales.urgency = TypedValue(value=UrgencyLevel.HIGH, confidence=75)
    oi.sales.customer_type = TypedValue(value=CustomerType.OPERATIONAL, confidence=80)
    oi.sales.next_best_action = "Schedule technical discovery"

    oi.solutions.recommended_products = [
        {"product": "Inspection Platform", "confidence": 95},
        {"product": "Document AI", "confidence": 88},
    ]
    oi.solutions.proposal_status = "none"
    oi.solutions.estimated_roi = "Estimated $48,000 annual savings"

    return oi


# ═══════════════════════════════════════════════════════════
# CONTEXT BUILDER
# ═══════════════════════════════════════════════════════════

class TestContextBuilder:
    def test_builds_complete_context(self):
        builder = get_email_context_builder()
        ctx = builder.build(sample_oi())
        assert ctx.company_name == "Acme Construction Ltd."
        assert ctx.contact_name == "Sarah Chen"
        assert ctx.contact_email == "sarah@acme.example.com"
        assert len(ctx.pain_points) >= 3
        assert len(ctx.buying_signals) >= 1
        assert ctx.budget == "$120,000"

    def test_empty_oi(self):
        builder = get_email_context_builder()
        ctx = builder.build(create_empty_intelligence())
        assert ctx.company_name == ""
        assert ctx.opportunity_stage == "lead"


# ═══════════════════════════════════════════════════════════
# STRATEGY ENGINE
# ═══════════════════════════════════════════════════════════

class TestStrategyEngine:
    def test_discovery_stage(self):
        engine = get_email_strategy_engine()
        # With budget set and signals present, falls to default discovery followup
        oi = sample_oi(OpportunityStage.DISCOVERY)
        s = engine.determine(oi)
        # Budget IS set in sample, so it falls through to default discovery followup
        assert s.purpose == EmailPurpose.DISCOVERY_FOLLOWUP

    def test_discovery_without_budget(self):
        engine = get_email_strategy_engine()
        oi = sample_oi(OpportunityStage.DISCOVERY)
        oi.business.budget = TypedValue.empty()  # Remove budget
        s = engine.determine(oi)
        assert s.purpose == EmailPurpose.BUDGET_DISCUSSION

    def test_lead_stage(self):
        engine = get_email_strategy_engine()
        s = engine.determine(sample_oi(OpportunityStage.LEAD))
        assert s.purpose == EmailPurpose.DISCOVERY_FOLLOWUP

    def test_proposal_stage(self):
        engine = get_email_strategy_engine()
        oi = sample_oi(OpportunityStage.PROPOSAL)
        oi.solutions.proposal_status = "generated"
        s = engine.determine(oi)
        assert s.purpose in (EmailPurpose.PROPOSAL_DELIVERY, EmailPurpose.OBJECTION_RESPONSE)

    def test_won_stage(self):
        engine = get_email_strategy_engine()
        s = engine.determine(sample_oi(OpportunityStage.WON))
        assert s.purpose == EmailPurpose.IMPLEMENTATION_KICKOFF

    def test_lost_stage(self):
        engine = get_email_strategy_engine()
        s = engine.determine(sample_oi(OpportunityStage.LOST))
        assert s.purpose == EmailPurpose.LOST_RECOVERY

    def test_negotiation_stage(self):
        engine = get_email_strategy_engine()
        s = engine.determine(sample_oi(OpportunityStage.NEGOTIATION))
        assert s.purpose == EmailPurpose.CONTRACT_FOLLOWUP

    def test_strategy_has_focus_and_avoid(self):
        engine = get_email_strategy_engine()
        s = engine.determine(sample_oi())
        assert len(s.focus_points) >= 1
        assert len(s.avoid_topics) >= 1
        assert s.tone in ("professional", "direct", "warm", "formal", "confident")


# ═══════════════════════════════════════════════════════════
# EMAIL GENERATOR
# ═══════════════════════════════════════════════════════════

class TestEmailGenerator:
    def test_generates_complete_draft(self):
        gen = get_email_generator()
        builder = get_email_context_builder()
        strategy_engine = get_email_strategy_engine()

        oi = sample_oi()
        ctx = builder.build(oi)
        strategy = strategy_engine.determine(oi)
        draft = gen.generate(ctx, strategy)

        assert draft.subject
        assert draft.greeting
        assert draft.body
        assert draft.call_to_action
        assert draft.signature
        assert "Pacific North Systems" in draft.signature

    def test_subject_contains_company(self):
        gen = get_email_generator()
        ctx = get_email_context_builder().build(sample_oi())
        strategy = get_email_strategy_engine().determine(sample_oi())
        draft = gen.generate(ctx, strategy)
        assert "Acme" in draft.subject

    def test_greeting_is_personal(self):
        gen = get_email_generator()
        ctx = get_email_context_builder().build(sample_oi())
        strategy = get_email_strategy_engine().determine(sample_oi())
        draft = gen.generate(ctx, strategy)
        assert "Sarah" in draft.greeting

    def test_template_generation(self):
        gen = get_email_generator()
        ctx = get_email_context_builder().build(sample_oi())
        strategy = get_email_strategy_engine().determine(sample_oi())
        draft = gen.generate_from_template(ctx, strategy, "discovery_followup")
        assert draft.subject
        assert "Acme" in draft.subject

    def test_no_invented_information(self):
        gen = get_email_generator()
        ctx = get_email_context_builder().build(sample_oi())
        strategy = get_email_strategy_engine().determine(sample_oi())
        draft = gen.generate(ctx, strategy)
        # Should not contain made-up numbers or claims
        assert "500%" not in draft.body  # No invented statistics

    def test_preview_is_truncated(self):
        gen = get_email_generator()
        ctx = get_email_context_builder().build(sample_oi())
        strategy = get_email_strategy_engine().determine(sample_oi())
        draft = gen.generate(ctx, strategy)
        assert len(draft.preview) <= 124


# ═══════════════════════════════════════════════════════════
# TEMPLATES
# ═══════════════════════════════════════════════════════════

class TestTemplates:
    def test_all_purposes_have_templates(self):
        purposes = [
            EmailPurpose.DISCOVERY_FOLLOWUP, EmailPurpose.PROPOSAL_DELIVERY,
            EmailPurpose.MEETING_SCHEDULING, EmailPurpose.MEETING_RECAP,
            EmailPurpose.OBJECTION_RESPONSE, EmailPurpose.IMPLEMENTATION_KICKOFF,
            EmailPurpose.CUSTOMER_CHECKIN, EmailPurpose.REENGAGEMENT,
            EmailPurpose.THANK_YOU,
        ]
        for p in purposes:
            assert get_template(p) is not None, f"No template for {p}"

    def test_list_templates(self):
        templates = list_templates()
        assert len(templates) >= 8
        for t in templates:
            assert "id" in t
            assert "name" in t
            assert "purpose" in t

    def test_template_variables_present(self):
        for tid, t in TEMPLATES.items():
            assert t.variables, f"Template {tid} has no variables"
            for v in t.variables:
                assert f"{{{v}}}" in t.subject_template + t.body_template, f"Variable {v} not in template {tid}"


# ═══════════════════════════════════════════════════════════
# REVIEW ENGINE
# ═══════════════════════════════════════════════════════════

class TestReviewEngine:
    def test_reviews_draft(self):
        engine = get_email_review_engine()
        gen = get_email_generator()
        ctx = get_email_context_builder().build(sample_oi())
        strategy = get_email_strategy_engine().determine(sample_oi())
        draft = gen.generate(ctx, strategy)

        review = engine.review(draft)
        assert 0 <= review.overall_score <= 100
        assert review.professionalism >= 0
        assert review.clarity >= 0

    def test_has_suggestions(self):
        engine = get_email_review_engine()
        draft = EmailDraft(subject="", body="hi", greeting="hey")
        review = engine.review(draft)
        assert isinstance(review.suggestions, list)

    def test_ready_to_send_boolean(self):
        engine = get_email_review_engine()
        gen = get_email_generator()
        ctx = get_email_context_builder().build(sample_oi())
        strategy = get_email_strategy_engine().determine(sample_oi())
        review = engine.review(gen.generate(ctx, strategy))
        assert isinstance(review.ready_to_send, bool)

    def test_all_scores_in_range(self):
        engine = get_email_review_engine()
        gen = get_email_generator()
        ctx = get_email_context_builder().build(sample_oi())
        strategy = get_email_strategy_engine().determine(sample_oi())
        review = engine.review(gen.generate(ctx, strategy))
        assert 0 <= review.professionalism <= 100
        assert 0 <= review.clarity <= 100
        assert 0 <= review.tone_score <= 100
        assert 0 <= review.grammar_score <= 100
        assert 0 <= review.business_accuracy <= 100
        assert 0 <= review.opportunity_consistency <= 100
        assert 0 <= review.call_to_action_score <= 100
        assert 0 <= review.length_score <= 100


# ═══════════════════════════════════════════════════════════
# EMAIL COPILOT (ORCHESTRATOR)
# ═══════════════════════════════════════════════════════════

class TestEmailCopilot:
    def test_generates_full_result(self):
        copilot = get_email_copilot()
        result = copilot.generate(sample_oi())
        assert "context" in result
        assert "strategy" in result
        assert "draft" in result
        assert "review" in result

    def test_context_has_contact(self):
        copilot = get_email_copilot()
        result = copilot.generate(sample_oi())
        assert result["context"]["contact_name"] == "Sarah Chen"

    def test_draft_is_complete(self):
        copilot = get_email_copilot()
        result = copilot.generate(sample_oi())
        draft = result["draft"]
        assert draft["subject"]
        assert draft["body"]
        assert draft["signature"]

    def test_review_included(self):
        copilot = get_email_copilot()
        result = copilot.generate(sample_oi())
        review = result["review"]
        assert "overall_score" in review
        assert "ready_to_send" in review

    def test_templates_listed(self):
        copilot = get_email_copilot()
        templates = copilot.get_templates()
        assert len(templates) >= 8

    def test_review_draft_standalone(self):
        copilot = get_email_copilot()
        result = copilot.review_draft({
            "subject": "Test", "body": "This is a test email.",
            "greeting": "Hi there,", "call_to_action": "Let me know.",
            "signature": "Best, PNS",
        })
        assert result["overall_score"] >= 0


# ═══════════════════════════════════════════════════════════
# SERIALIZATION
# ═══════════════════════════════════════════════════════════

class TestSerialization:
    def test_full_result_is_json_serializable(self):
        copilot = get_email_copilot()
        result = copilot.generate(sample_oi())
        json_str = json.dumps(result)
        parsed = json.loads(json_str)
        assert parsed["strategy"]["purpose"]
        assert parsed["draft"]["subject"]

    def test_templates_serializable(self):
        copilot = get_email_copilot()
        templates = copilot.get_templates()
        json_str = json.dumps(templates)
        parsed = json.loads(json_str)
        assert len(parsed) >= 8


# ═══════════════════════════════════════════════════════════
# DETERMINISTIC
# ═══════════════════════════════════════════════════════════

class TestDeterministic:
    def test_same_input_same_output(self):
        copilot = get_email_copilot()
        oi = sample_oi()
        r1 = copilot.generate(oi)
        r2 = copilot.generate(oi)
        assert r1["draft"]["subject"] == r2["draft"]["subject"]
        assert r1["draft"]["body"] == r2["draft"]["body"]
        assert r1["review"]["overall_score"] == r2["review"]["overall_score"]
        assert r1["strategy"]["purpose"] == r2["strategy"]["purpose"]
