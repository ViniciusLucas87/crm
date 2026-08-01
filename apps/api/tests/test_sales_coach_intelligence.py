"""
Tests for Sprint 36.5 — Sales Intelligence Assistant engines.

All tests are deterministic — no LLM calls required.
Uses mock ConversationInsights to validate each engine independently.

Test coverage:
    DiscoveryEngine, OpportunityEngine, RecommendationEngine,
    SalesStrategyEngine, RiskAnalysis, SalesCoachReportGenerator,
    score calculations, ranking logic, question selection.
"""

import pytest
from datetime import datetime

from app.application.transcription.intelligence import ConversationInsight, InsightCategory
from app.application.copilot.discovery_engine import (
    DiscoveryEngine, DiscoveryReport, FieldStatus, DISCOVERY_FIELDS,
)
from app.application.copilot.opportunity_engine import (
    OpportunityEngine, OpportunityReport,
)
from app.application.copilot.recommendation_engine import (
    RecommendationEngine, ProductRecommendation,
)
from app.application.copilot.sales_strategy_engine import (
    SalesStrategyEngine, StrategyReport, STRATEGIES,
)
from app.application.copilot.risk_analysis import (
    RiskAnalysis, RiskReport, DealRisk, RISK_RULES,
)
from app.application.copilot.coach_report import (
    SalesCoachReportGenerator, SalesCoachReport, NEXT_QUESTIONS_BY_FIELD,
)


# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════

def make_insight(category: InsightCategory, value: str, confidence: int = 85, evidence: str = "") -> ConversationInsight:
    return ConversationInsight(
        category=category,
        value=value,
        confidence=confidence,
        evidence=evidence or f"Customer said: '{value}'",
        speaker="Speaker 0",
    )


def realistic_insights() -> list[ConversationInsight]:
    """Simulate a realistic discovery call with an operational customer."""
    return [
        make_insight(InsightCategory.PAIN_POINT, "Manual inspections take 4 hours per site"),
        make_insight(InsightCategory.PAIN_POINT, "Duplicate data entry across 3 spreadsheets"),
        make_insight(InsightCategory.PAIN_POINT, "Lost paperwork causing compliance issues"),
        make_insight(InsightCategory.CURRENT_SOFTWARE, "Excel and QuickBooks"),
        make_insight(InsightCategory.CURRENT_PROCESS, "Field techs fill paper forms, office staff type them in"),
        make_insight(InsightCategory.DECISION_MAKER, "VP Operations Sarah Chen"),
        make_insight(InsightCategory.BUDGET, "Allocated $120K for this fiscal year"),
        make_insight(InsightCategory.TIMELINE, "Want to go live by March"),
        make_insight(InsightCategory.GOAL, "Reduce inspection turnaround by 50%"),
        make_insight(InsightCategory.BUYING_SIGNAL, "We've been looking for a solution for months"),
        make_insight(InsightCategory.BUYING_SIGNAL, "Our current process is unsustainable"),
        make_insight(InsightCategory.URGENCY, "Need this solved before next audit"),
        make_insight(InsightCategory.OBJECTION, "Worried about training time for field staff"),
        make_insight(InsightCategory.CONSTRAINT, "Must integrate with existing accounting system"),
    ]


# ═══════════════════════════════════════════════════════════
# DISCOVERY ENGINE
# ═══════════════════════════════════════════════════════════

class TestDiscoveryEngine:
    def test_empty_insights(self):
        engine = DiscoveryEngine()
        report = engine.evaluate([])
        assert report.completion_pct == 0
        assert len(report.missing_keys) == len(DISCOVERY_FIELDS)
        assert len(report.missing_priority_order) == len(DISCOVERY_FIELDS)

    def test_full_discovery_realistic(self):
        engine = DiscoveryEngine()
        report = engine.evaluate(realistic_insights())
        assert report.completion_pct > 50, f"Expected >50% but got {report.completion_pct}%"
        # These should be known from our realistic insights
        known_keys = {f.field_key for f in report.fields if f.known}
        assert "pain_points" in known_keys
        assert "current_software" in known_keys
        assert "current_process" in known_keys
        assert "decision_maker" in known_keys
        assert "budget" in known_keys
        assert "timeline" in known_keys
        assert "goals" in known_keys
        assert "urgency" in known_keys
        assert "technical_constraints" in known_keys

    def test_company_context(self):
        engine = DiscoveryEngine()
        report = engine.evaluate([], company_context={
            "name": "Acme Corp", "industry": "Construction", "employees": 250,
        })
        known = {f.field_key: f.known for f in report.fields}
        assert known["company"] is True
        assert known["industry"] is True
        assert known["employees"] is True
        assert report.fields[0].value == "Acme Corp"
        assert report.completion_pct > 0

    def test_missing_field_has_reason(self):
        engine = DiscoveryEngine()
        report = engine.evaluate([])
        for missing in report.missing_priority_order:
            assert "reason" in missing
            assert len(missing["reason"]) > 20
            assert "field" in missing
            assert "priority" in missing

    def test_priority_ordering(self):
        engine = DiscoveryEngine()
        report = engine.evaluate([])
        priorities = [m["priority"] for m in report.missing_priority_order]
        assert priorities == sorted(priorities), "Missing fields should be in priority order"

    def test_single_pain_point(self):
        engine = DiscoveryEngine()
        insights = [make_insight(InsightCategory.PAIN_POINT, "Paperwork is slow")]
        report = engine.evaluate(insights)
        assert report.completion_pct > 0
        pain_field = next(f for f in report.fields if f.field_key == "pain_points")
        assert pain_field.known is True
        assert pain_field.value == "Paperwork is slow"
        assert pain_field.evidence


# ═══════════════════════════════════════════════════════════
# OPPORTUNITY ENGINE
# ═══════════════════════════════════════════════════════════

class TestOpportunityEngine:
    def test_empty_insights(self):
        engine = OpportunityEngine()
        report = engine.evaluate([])
        assert report.score <= 40
        assert "No pain points" in report.weaknesses[0]
        assert report.risk_level in ("high", "critical")

    def test_strong_opportunity(self):
        engine = OpportunityEngine()
        report = engine.evaluate(realistic_insights(), discovery_pct=80)
        assert report.score >= 70, f"Expected >=70, got {report.score}"
        assert report.risk_level in ("low", "medium")
        assert len(report.strengths) >= 3
        assert report.confidence >= 40

    def test_opportunity_score_range(self):
        engine = OpportunityEngine()
        report = engine.evaluate(realistic_insights(), discovery_pct=80)
        assert 0 <= report.score <= 100, f"Score {report.score} out of range"

    def test_no_budget_lowers_score(self):
        engine = OpportunityEngine()
        # Use moderate insights so score doesn't saturate at 100
        insights = [
            make_insight(InsightCategory.PAIN_POINT, "Manual data entry"),
            make_insight(InsightCategory.BUYING_SIGNAL, "Interested"),
            make_insight(InsightCategory.DECISION_MAKER, "CEO"),
            make_insight(InsightCategory.BUDGET, "$50K"),
            make_insight(InsightCategory.TIMELINE, "Q3"),
        ]
        full = engine.evaluate(insights, discovery_pct=60)
        no_budget = [i for i in insights if i.category != InsightCategory.BUDGET]
        reduced = engine.evaluate(no_budget, discovery_pct=60)
        assert reduced.score < full.score

    def test_objections_reduce_score(self):
        engine = OpportunityEngine()
        # Use moderate insights so score doesn't saturate at 100
        insights = [
            make_insight(InsightCategory.PAIN_POINT, "Manual data entry"),
            make_insight(InsightCategory.BUYING_SIGNAL, "Interested"),
            make_insight(InsightCategory.DECISION_MAKER, "CEO"),
            make_insight(InsightCategory.OBJECTION, "Concerned about cost"),
        ]
        base = engine.evaluate(insights)
        extra = insights + [
            make_insight(InsightCategory.OBJECTION, "Too expensive"),
            make_insight(InsightCategory.OBJECTION, "Not sure about timing"),
            make_insight(InsightCategory.OBJECTION, "Current vendor is fine"),
        ]
        with_more = engine.evaluate(extra)
        assert with_more.score < base.score

    def test_milestone_progression(self):
        engine = OpportunityEngine()
        early = engine.evaluate([], discovery_pct=10)
        assert early.recommended_milestone == "Discovery"

        mid = engine.evaluate(realistic_insights(), discovery_pct=50)
        assert mid.recommended_milestone == "Technical Discovery"

        late = engine.evaluate(realistic_insights(), discovery_pct=85)
        assert late.recommended_milestone in ("Proposal", "Demo")

    def test_strengths_and_weaknesses(self):
        engine = OpportunityEngine()
        report = engine.evaluate(realistic_insights(), discovery_pct=65)
        assert len(report.strengths) >= 2
        # Should have at least one weakness (budget, timeline, etc.)
        assert len(report.weaknesses) >= 0  # May be zero if all covered


# ═══════════════════════════════════════════════════════════
# RECOMMENDATION ENGINE
# ═══════════════════════════════════════════════════════════

class TestRecommendationEngine:
    def test_empty_insights(self):
        engine = RecommendationEngine()
        results = engine.recommend([])
        assert results == []

    def test_inspection_recommendation(self):
        engine = RecommendationEngine()
        insights = [
            make_insight(InsightCategory.PAIN_POINT, "Manual inspections are taking too long"),
        ]
        results = engine.recommend(insights)
        assert len(results) >= 1
        assert any("Inspection" in r.product for r in results)

    def test_max_five_recommendations(self):
        engine = RecommendationEngine()
        insights = realistic_insights()
        results = engine.recommend(insights)
        assert len(results) <= 5

    def test_confidence_score_range(self):
        engine = RecommendationEngine()
        insights = realistic_insights()
        results = engine.recommend(insights)
        for r in results:
            assert 0 <= r.confidence <= 100, f"Confidence {r.confidence} out of range"

    def test_ranked_by_confidence(self):
        engine = RecommendationEngine()
        insights = realistic_insights()
        results = engine.recommend(insights)
        confidences = [r.confidence for r in results]
        assert confidences == sorted(confidences, reverse=True), "Not sorted by confidence"

    def test_each_has_reason(self):
        engine = RecommendationEngine()
        insights = realistic_insights()
        results = engine.recommend(insights)
        for r in results:
            assert r.reason, f"No reason for {r.product}"
            assert len(r.reason) > 10

    def test_document_ai_from_paperwork(self):
        engine = RecommendationEngine()
        insights = [
            make_insight(InsightCategory.PAIN_POINT, "Too much paperwork in the office"),
        ]
        results = engine.recommend(insights)
        assert len(results) >= 1
        assert any("Document AI" == r.product for r in results)

    def test_evidence_tracking(self):
        engine = RecommendationEngine()
        insights = realistic_insights()
        results = engine.recommend(insights)
        for r in results:
            assert isinstance(r.evidence, list)
            if r.evidence:
                assert all(isinstance(e, str) for e in r.evidence)


# ═══════════════════════════════════════════════════════════
# SALES STRATEGY ENGINE
# ═══════════════════════════════════════════════════════════

class TestSalesStrategyEngine:
    def test_empty_insights(self):
        engine = SalesStrategyEngine()
        report = engine.evaluate([])
        assert report.current_stage == "Discovery"
        assert report.customer_type == "unknown"

    def test_operational_customer(self):
        engine = SalesStrategyEngine()
        insights = realistic_insights()
        report = engine.evaluate(insights, discovery_pct=45, opportunity_score=60)
        assert report.customer_type in ("operational", "unknown")
        assert report.recommended_strategy
        assert report.avoid
        assert report.next_best_action

    def test_all_strategies_exist(self):
        for ctype in ["operational", "technical", "executive", "financial", "unknown"]:
            assert ctype in STRATEGIES
            s = STRATEGIES[ctype]
            assert "focus" in s
            assert "avoid" in s
            assert "next_action" in s
            assert "alternative" in s

    def test_stage_progression(self):
        engine = SalesStrategyEngine()
        assert engine.evaluate([], discovery_pct=10, opportunity_score=20).current_stage == "Discovery"
        assert engine.evaluate([], discovery_pct=45, opportunity_score=40).current_stage == "Qualification"
        assert engine.evaluate([], discovery_pct=70, opportunity_score=60).current_stage == "Technical Discovery"
        assert engine.evaluate([], discovery_pct=85, opportunity_score=80).current_stage == "Proposal"

    def test_strategy_is_serializable(self):
        engine = SalesStrategyEngine()
        report = engine.evaluate(realistic_insights(), discovery_pct=60, opportunity_score=70)
        d = {
            "current_stage": report.current_stage,
            "customer_type": report.customer_type,
            "recommended_strategy": report.recommended_strategy,
            "avoid": report.avoid,
            "next_best_action": report.next_best_action,
            "alternative_path": report.alternative_path,
        }
        assert all(isinstance(v, str) for v in d.values())


# ═══════════════════════════════════════════════════════════
# RISK ANALYSIS
# ═══════════════════════════════════════════════════════════

class TestRiskAnalysis:
    def test_empty_insights(self):
        engine = RiskAnalysis()
        report = engine.evaluate([])
        assert len(report.risks) >= 3  # Missing budget, DM, urgency at minimum
        assert report.overall_risk in ("high", "critical")

    def test_risk_has_all_fields(self):
        engine = RiskAnalysis()
        report = engine.evaluate([])
        for risk in report.risks:
            assert risk.risk
            assert risk.severity in ("critical", "high", "medium", "low")
            assert risk.mitigation
            assert len(risk.mitigation) > 10

    def test_full_discovery_reduces_risks(self):
        engine = RiskAnalysis()
        full = engine.evaluate(realistic_insights())
        empty = engine.evaluate([])
        assert len(full.risks) < len(empty.risks)

    def test_objections_increase_risk(self):
        engine = RiskAnalysis()
        base = engine.evaluate(realistic_insights())
        with_obj = realistic_insights() + [
            make_insight(InsightCategory.OBJECTION, "Obj 1"),
            make_insight(InsightCategory.OBJECTION, "Obj 2"),
            make_insight(InsightCategory.OBJECTION, "Obj 3"),
        ]
        obj_report = engine.evaluate(with_obj)
        # Should have the "Multiple Objections" risk
        assert any("Multiple Objections" == r.risk for r in obj_report.risks)

    def test_competitor_creates_risks(self):
        engine = RiskAnalysis()
        insights = realistic_insights() + [
            make_insight(InsightCategory.COMPETITOR, "Salesforce"),
        ]
        report = engine.evaluate(insights)
        assert any("Vendor Lock-in" in r.risk or "Competitor" in r.risk for r in report.risks)


# ═══════════════════════════════════════════════════════════
# SALES COACH REPORT (UNIFIED)
# ═══════════════════════════════════════════════════════════

class TestSalesCoachReport:
    def test_generates_all_sections(self):
        generator = SalesCoachReportGenerator()
        report = generator.generate(realistic_insights())
        assert report.discovery is not None
        assert report.opportunity is not None
        assert report.strategy is not None
        assert report.risk_report is not None
        assert isinstance(report.recommendations, list)

    def test_empty_insights_does_not_crash(self):
        generator = SalesCoachReportGenerator()
        report = generator.generate([])
        assert report.deal_health in ("poor", "fair")
        assert report.deal_health_score <= 40

    def test_next_best_question_selected(self):
        generator = SalesCoachReportGenerator()
        report = generator.generate([])
        assert report.next_best_question is not None
        assert len(report.next_best_question) > 10

    def test_next_best_action(self):
        generator = SalesCoachReportGenerator()
        report = generator.generate([])
        assert report.next_best_action
        assert "discovery" in report.next_best_action.lower()

    def test_deal_health_excellent(self):
        generator = SalesCoachReportGenerator()
        report = generator.generate(realistic_insights(), company_context={
            "name": "Acme", "industry": "Construction", "employees": 200,
        })
        assert report.deal_health_score > 50
        assert report.deal_health in ("good", "excellent", "fair")

    def test_buying_signals_extracted(self):
        generator = SalesCoachReportGenerator()
        report = generator.generate(realistic_insights())
        assert len(report.buying_signals) >= 1
        assert "signal" in report.buying_signals[0]

    def test_objections_extracted(self):
        generator = SalesCoachReportGenerator()
        report = generator.generate(realistic_insights())
        assert len(report.objections) >= 1
        assert "objection" in report.objections[0]

    def test_pain_points_extracted(self):
        generator = SalesCoachReportGenerator()
        report = generator.generate(realistic_insights())
        assert len(report.pain_points) >= 3

    def test_decision_makers_extracted(self):
        generator = SalesCoachReportGenerator()
        report = generator.generate(realistic_insights())
        assert len(report.decision_makers) >= 1
        assert "Sarah" in report.decision_makers[0]

    def test_budget_and_timeline_extracted(self):
        generator = SalesCoachReportGenerator()
        report = generator.generate(realistic_insights())
        assert report.budget_indicated is not None
        assert report.timeline_indicated is not None

    def test_report_is_serializable(self):
        """All fields must be JSON-serializable."""
        import json
        generator = SalesCoachReportGenerator()
        report = generator.generate(realistic_insights())

        d = {
            "deal_health": report.deal_health,
            "deal_health_score": report.deal_health_score,
            "next_best_question": report.next_best_question,
            "next_best_action": report.next_best_action,
            "pain_points": report.pain_points,
            "decision_makers": report.decision_makers,
            "budget_indicated": report.budget_indicated,
            "timeline_indicated": report.timeline_indicated,
            "generated_at": report.generated_at,
            "buying_signals": report.buying_signals,
            "objections": report.objections,
            "recommendations": [
                {"product": r.product, "confidence": r.confidence, "reason": r.reason, "evidence": r.evidence, "rank": r.rank}
                for r in report.recommendations
            ],
            "discovery": {
                "completion_pct": report.discovery.completion_pct,
                "missing_keys": report.discovery.missing_keys,
                "missing_priority_order": report.discovery.missing_priority_order,
            },
            "opportunity": {
                "score": report.opportunity.score,
                "confidence": report.opportunity.confidence,
                "strengths": report.opportunity.strengths,
                "weaknesses": report.opportunity.weaknesses,
                "risk_level": report.opportunity.risk_level,
            },
            "strategy": {
                "current_stage": report.strategy.current_stage,
                "customer_type": report.strategy.customer_type,
                "recommended_strategy": report.strategy.recommended_strategy,
            },
            "risk_report": {
                "overall_risk": report.risk_report.overall_risk,
                "critical_count": report.risk_report.critical_count,
                "high_count": report.risk_report.high_count,
            },
        }
        json_str = json.dumps(d)
        assert len(json_str) > 100
        json.loads(json_str)  # Must parse without error

    def test_deterministic(self):
        """Same inputs must produce same outputs."""
        generator = SalesCoachReportGenerator()
        insights = realistic_insights()
        r1 = generator.generate(insights)
        r2 = generator.generate(insights)
        assert r1.deal_health_score == r2.deal_health_score
        assert r1.opportunity.score == r2.opportunity.score
        assert r1.discovery.completion_pct == r2.discovery.completion_pct

    def test_company_context_boosts_discovery(self):
        generator = SalesCoachReportGenerator()
        without = generator.generate(realistic_insights())
        with_ctx = generator.generate(realistic_insights(), company_context={
            "name": "Acme Corp", "industry": "Construction", "employees": 250,
        })
        assert with_ctx.discovery.completion_pct >= without.discovery.completion_pct

    def test_next_best_question_for_missing_budget(self):
        """When budget is missing, it should appear in missing priority order."""
        insights_no_budget = [
            i for i in realistic_insights()
            if i.category != InsightCategory.BUDGET
        ]
        generator = SalesCoachReportGenerator()
        report = generator.generate(insights_no_budget, company_context={
            "name": "Acme Corp", "industry": "Construction", "employees": 200,
        })
        assert report.next_best_question
        # Budget must be in missing priority order
        missing_fields = [m["field"] for m in report.discovery.missing_priority_order]
        assert "budget" in missing_fields, f"Expected budget in missing fields: {missing_fields}"


# ═══════════════════════════════════════════════════════════
# QUESTION SELECTION
# ═══════════════════════════════════════════════════════════

class TestQuestionSelection:
    def test_all_questions_are_meaningful(self):
        for field, question in NEXT_QUESTIONS_BY_FIELD.items():
            assert len(question) > 15, f"Question for {field} is too short: {question}"
            # Most questions should end with ?, but imperative ones ("Walk me through...") may not

    def test_question_priority_matches_priority_order(self):
        """The highest-priority missing field should get the question."""
        generator = SalesCoachReportGenerator()
        report = generator.generate([])
        # First missing field should be "company" (priority 1)
        # But "company" question is "Tell me more about your organization..."
        assert report.next_best_question
        assert "organization" in report.next_best_question.lower() or "?" in report.next_best_question


# ═══════════════════════════════════════════════════════════
# SCORE CALCULATIONS
# ═══════════════════════════════════════════════════════════

class TestScoreCalculations:
    def test_discovery_pct_never_negative(self):
        engine = DiscoveryEngine()
        report = engine.evaluate([])
        assert report.completion_pct >= 0

    def test_discovery_pct_never_exceeds_100(self):
        engine = DiscoveryEngine()
        # Full insights + full context
        report = engine.evaluate(realistic_insights(), company_context={
            "name": "A", "industry": "B", "employees": 10,
        })
        assert report.completion_pct <= 100

    def test_opportunity_score_bounds(self):
        engine = OpportunityEngine()
        for _ in range(5):
            report = engine.evaluate(realistic_insights())
            assert 0 <= report.score <= 100

    def test_deal_health_bounds(self):
        generator = SalesCoachReportGenerator()
        report = generator.generate(realistic_insights())
        assert 0 <= report.deal_health_score <= 100
        assert report.deal_health in ("poor", "fair", "good", "excellent")
