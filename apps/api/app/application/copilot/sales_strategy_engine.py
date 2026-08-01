"""
Sales Strategy Engine — recommends conversation strategy.

Consumes ConversationInsights. Determines customer type, current stage,
recommended strategy, what to avoid, next best action, and alternative path.

Architecture:
    ConversationInsights → SalesStrategyEngine → StrategyReport
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC

from app.application.transcription.intelligence import ConversationInsight, InsightCategory


# ── Strategy definitions by customer type ──

STRATEGIES = {
    "operational": {
        "focus": "Focus on operational efficiency before discussing technology.",
        "avoid": "Pricing discussion until business impact is understood.",
        "next_action": "Explore current workflow in detail.",
        "alternative": "Schedule technical workshop.",
    },
    "technical": {
        "focus": "Lead with architecture and integration capabilities.",
        "avoid": "Business jargon — stay technically precise.",
        "next_action": "Share system architecture overview.",
        "alternative": "Offer proof-of-concept engagement.",
    },
    "executive": {
        "focus": "Focus on business outcomes and ROI.",
        "avoid": "Deep technical details — keep at strategic level.",
        "next_action": "Schedule executive briefing.",
        "alternative": "Share industry benchmark report.",
    },
    "financial": {
        "focus": "Emphasize cost savings and measurable ROI.",
        "avoid": "Feature lists — focus on value and payback period.",
        "next_action": "Present ROI calculator.",
        "alternative": "Arrange reference call with similar customer.",
    },
    "unknown": {
        "focus": "Continue discovery to identify customer type.",
        "avoid": "Premature solution discussion.",
        "next_action": "Ask about current process and pain points.",
        "alternative": "Share relevant case study.",
    },
}


@dataclass
class StrategyReport:
    current_stage: str = "Discovery"
    customer_type: str = "unknown"
    recommended_strategy: str = ""
    avoid: str = ""
    next_best_action: str = ""
    alternative_path: str = ""
    generated_at: str = ""


class SalesStrategyEngine:
    """Recommends conversation strategy based on structured insights.

    Determines the customer persona (operational, technical, executive,
    financial) and recommends corresponding sales approach including
    what to focus on and what to avoid.
    """

    def evaluate(
        self,
        insights: list[ConversationInsight],
        discovery_pct: int = 0,
        opportunity_score: int = 0,
    ) -> StrategyReport:
        """Determine sales strategy.

        Args:
            insights: ConversationInsights from the frozen pipeline
            discovery_pct: Discovery completion percentage
            opportunity_score: Opportunity score (0-100)
        """
        now = datetime.now(UTC).isoformat()
        by_category: dict[InsightCategory, list[ConversationInsight]] = {}
        for ins in insights:
            by_category.setdefault(ins.category, []).append(ins)

        # ── Determine current stage ──
        stage = self._determine_stage(discovery_pct, opportunity_score, by_category)

        # ── Determine customer type ──
        customer_type = self._determine_customer_type(by_category)

        # ── Select strategy ──
        strategy = STRATEGIES.get(customer_type, STRATEGIES["unknown"])

        return StrategyReport(
            current_stage=stage,
            customer_type=customer_type,
            recommended_strategy=strategy["focus"],
            avoid=strategy["avoid"],
            next_best_action=strategy["next_action"],
            alternative_path=strategy["alternative"],
            generated_at=now,
        )

    def _determine_stage(self, discovery_pct, opportunity_score, by_category) -> str:
        if discovery_pct < 30:
            return "Discovery"
        if discovery_pct < 60:
            return "Qualification"
        if discovery_pct < 80:
            return "Technical Discovery"
        if opportunity_score >= 75:
            return "Proposal"
        if opportunity_score >= 50:
            return "Evaluation"
        return "Discovery"

    def _determine_customer_type(self, by_category) -> str:
        # Count keyword signals for each type
        all_text = " ".join(
            i.value.lower()
            for cat_ins in by_category.values()
            for i in cat_ins
        )

        scores = {"operational": 0, "technical": 0, "executive": 0, "financial": 0}

        # Operational signals
        op_keywords = ["process", "workflow", "manual", "day-to-day", "operation", "efficiency", "team", "staff"]
        scores["operational"] = sum(1 for kw in op_keywords if kw in all_text)

        # Technical signals
        tech_keywords = ["integration", "api", "system", "architecture", "security", "cloud", "database", "infrastructure"]
        scores["technical"] = sum(1 for kw in tech_keywords if kw in all_text)

        # Executive signals
        exec_keywords = ["roi", "growth", "strategy", "revenue", "market", "competitive", "scale", "vision"]
        scores["executive"] = sum(1 for kw in exec_keywords if kw in all_text)

        # Financial signals
        fin_keywords = ["budget", "cost", "saving", "investment", "payback", "roi", "reduce cost", "expense"]
        scores["financial"] = sum(1 for kw in fin_keywords if kw in all_text)

        # Find max
        max_type = max(scores, key=scores.get)
        if scores[max_type] == 0:
            return "unknown"
        return max_type


# Singleton
_sales_strategy_engine: SalesStrategyEngine | None = None


def get_sales_strategy_engine() -> SalesStrategyEngine:
    global _sales_strategy_engine
    if _sales_strategy_engine is None:
        _sales_strategy_engine = SalesStrategyEngine()
    return _sales_strategy_engine
