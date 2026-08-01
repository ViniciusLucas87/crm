"""
Sales Coach Report — unified output from all coaching engines.

Orchestrates DiscoveryEngine, OpportunityEngine, RecommendationEngine,
SalesStrategyEngine, and RiskAnalysis into a single serializable report.

Architecture:
    ConversationInsights → SalesCoachReport (all engines) → Copilot UI
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any

from app.application.transcription.intelligence import ConversationInsight, InsightCategory

from app.application.copilot.discovery_engine import DiscoveryEngine, DiscoveryReport
from app.application.copilot.opportunity_engine import OpportunityEngine, OpportunityReport
from app.application.copilot.recommendation_engine import RecommendationEngine, ProductRecommendation
from app.application.copilot.sales_strategy_engine import SalesStrategyEngine, StrategyReport
from app.application.copilot.risk_analysis import RiskAnalysis, RiskReport, DealRisk


# ── Next Best Question ──

NEXT_QUESTIONS_BY_FIELD: dict[str, str] = {
    "decision_maker": "Who approves software purchases at your organization?",
    "budget": "Do you have a budget allocated for this type of solution?",
    "timeline": "When would you ideally want to have something in place?",
    "current_process": "Walk me through how this currently works day-to-day.",
    "current_software": "What tools are you using today to manage this?",
    "pain_points": "What's costing your team the most time right now?",
    "goals": "What would success look like six months after implementation?",
    "technical_constraints": "Are there any security or compliance requirements we should consider?",
    "implementation_window": "How quickly would you need to be up and running?",
    "roi_expectations": "How are you measuring return on investment for this initiative?",
    "urgency": "What happens if nothing changes in the next six months?",
    "employees": "How many people would be using this system?",
    "industry": "What industry do you primarily operate in?",
    "company": "Tell me more about your organization and what you do.",
}


@dataclass
class SalesCoachReport:
    """Unified coaching report from all intelligence engines.

    Deterministic and fully serializable. Consumes ConversationInsights
    from the frozen pipeline. Never analyzes raw transcript.
    """

    # ── Discovery ──
    discovery: DiscoveryReport | None = None

    # ── Opportunity ──
    opportunity: OpportunityReport | None = None

    # ── Recommendations ──
    recommendations: list[ProductRecommendation] = field(default_factory=list)

    # ── Strategy ──
    strategy: StrategyReport | None = None

    # ── Risks ──
    risk_report: RiskReport | None = None

    # ── Signals ──
    buying_signals: list[dict[str, Any]] = field(default_factory=list)
    objections: list[dict[str, Any]] = field(default_factory=list)

    # ── Guidance ──
    next_best_question: str | None = None
    next_best_action: str = "Continue discovery"

    # ── Deal Health ──
    deal_health: str = "unknown"
    deal_health_score: int = 0

    # ── Raw ──
    pain_points: list[str] = field(default_factory=list)
    decision_makers: list[str] = field(default_factory=list)
    budget_indicated: str | None = None
    timeline_indicated: str | None = None

    # ── Meta ──
    generated_at: str = ""


class SalesCoachReportGenerator:
    """Generates unified SalesCoachReport from all engines.

    Orchestrates DiscoveryEngine, OpportunityEngine, RecommendationEngine,
    SalesStrategyEngine, and RiskAnalysis. No LLM calls — purely deterministic.
    """

    def __init__(self):
        self._discovery_engine = DiscoveryEngine()
        self._opportunity_engine = OpportunityEngine()
        self._recommendation_engine = RecommendationEngine()
        self._strategy_engine = SalesStrategyEngine()
        self._risk_analysis = RiskAnalysis()

    def generate(
        self,
        insights: list[ConversationInsight],
        company_context: dict[str, Any] | None = None,
    ) -> SalesCoachReport:
        """Generate complete coaching report.

        Args:
            insights: ConversationInsights from the frozen pipeline
            company_context: Optional company data
        """
        now = datetime.now(UTC).isoformat()

        # ── Categorize insights ──
        by_category: dict[InsightCategory, list[ConversationInsight]] = {}
        for ins in insights:
            by_category.setdefault(ins.category, []).append(ins)

        pain_points = by_category.get(InsightCategory.PAIN_POINT, [])
        buying_signals = by_category.get(InsightCategory.BUYING_SIGNAL, [])
        objections = by_category.get(InsightCategory.OBJECTION, [])
        decision_makers = by_category.get(InsightCategory.DECISION_MAKER, [])
        budget = next((i.value for i in by_category.get(InsightCategory.BUDGET, [])), None)
        timeline = next((i.value for i in by_category.get(InsightCategory.TIMELINE, [])), None)

        # ── Run all engines ──
        discovery = self._discovery_engine.evaluate(insights, company_context)
        opportunity = self._opportunity_engine.evaluate(insights, discovery.completion_pct)
        recommendations = self._recommendation_engine.recommend(insights)
        strategy = self._strategy_engine.evaluate(insights, discovery.completion_pct, opportunity.score)
        risk_report = self._risk_analysis.evaluate(insights)

        # ── Buying signals ──
        bs = [
            {"signal": s.value, "confidence": s.confidence, "evidence": s.evidence or ""}
            for s in buying_signals
        ]

        # ── Objections with strategies ──
        obj = [
            {
                "objection": o.value,
                "confidence": o.confidence,
                "evidence": o.evidence or "",
            }
            for o in objections
        ]

        # ── Next Best Question ──
        question = self._pick_best_question(discovery)

        # ── Next Best Action ──
        action = self._determine_action(discovery, opportunity, risk_report)

        # ── Deal Health ──
        health_score = self._compute_deal_health(discovery, opportunity, risk_report)
        health = (
            "excellent" if health_score >= 80
            else "good" if health_score >= 60
            else "fair" if health_score >= 35
            else "poor"
        )

        return SalesCoachReport(
            discovery=discovery,
            opportunity=opportunity,
            recommendations=recommendations,
            strategy=strategy,
            risk_report=risk_report,
            buying_signals=bs,
            objections=obj,
            next_best_question=question,
            next_best_action=action,
            deal_health=health,
            deal_health_score=health_score,
            pain_points=[p.value for p in pain_points],
            decision_makers=[d.value for d in decision_makers],
            budget_indicated=budget,
            timeline_indicated=timeline,
            generated_at=now,
        )

    def _pick_best_question(self, discovery: DiscoveryReport) -> str | None:
        """Select the single highest-value question based on missing info priority."""
        if not discovery.missing_priority_order:
            return "What would success look like for this project?"

        # Pick highest-priority missing field with a question
        for missing in discovery.missing_priority_order:
            field_key = missing["field"]
            if field_key in NEXT_QUESTIONS_BY_FIELD:
                return NEXT_QUESTIONS_BY_FIELD[field_key]

        return NEXT_QUESTIONS_BY_FIELD.get(
            discovery.missing_priority_order[0]["field"],
            "What would success look like for this project?",
        )

    def _determine_action(
        self,
        discovery: DiscoveryReport,
        opportunity: OpportunityReport,
        risk_report: RiskReport,
    ) -> str:
        """Determine the next best action based on all engine outputs."""
        if risk_report.critical_count >= 1:
            return "Address critical risks before proceeding"
        if discovery.completion_pct < 30:
            return "Continue discovery — focus on pain points and current process"
        if discovery.completion_pct < 60:
            return "Explore budget, timeline, and decision maker"
        if discovery.completion_pct < 80:
            return "Technical discovery — discuss integration, constraints, and requirements"
        if opportunity.score >= 75:
            return "Schedule proposal review"
        if opportunity.score >= 50:
            return "Schedule technical demo"
        if risk_report.high_count >= 1:
            return "Mitigate risks before advancing"
        return "Continue discovery"

    def _compute_deal_health(
        self,
        discovery: DiscoveryReport,
        opportunity: OpportunityReport,
        risk_report: RiskReport,
    ) -> int:
        """Compute deal health score (0-100)."""
        score = discovery.completion_pct * 0.3 + opportunity.score * 0.4
        # Penalize risks
        score -= risk_report.critical_count * 15
        score -= risk_report.high_count * 8
        score -= risk_report.medium_count * 4
        return max(0, min(int(score), 100))


# Singleton
_generator: SalesCoachReportGenerator | None = None


def get_coach_report_generator() -> SalesCoachReportGenerator:
    global _generator
    if _generator is None:
        _generator = SalesCoachReportGenerator()
    return _generator
