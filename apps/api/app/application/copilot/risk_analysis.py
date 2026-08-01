"""
Risk Analysis — detects and scores deal risks.

Consumes ConversationInsights. Identifies missing budget, unknown decision
makers, weak urgency, vendor lock-in, and other deal risks. Provides
severity and recommended mitigation for each.

Architecture:
    ConversationInsights → RiskAnalysis → list[DealRisk]
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC

from app.application.transcription.intelligence import ConversationInsight, InsightCategory


@dataclass
class DealRisk:
    risk: str
    severity: str  # critical, high, medium, low
    mitigation: str


# ── Risk detection rules ──

RISK_RULES: list[dict] = [
    {
        "name": "Missing Budget",
        "check": lambda cat: InsightCategory.BUDGET not in cat,
        "severity": "high",
        "mitigation": "Explore budget in next conversation. Ask: 'Do you have a budget allocated for this initiative?'",
    },
    {
        "name": "Unknown Decision Maker",
        "check": lambda cat: InsightCategory.DECISION_MAKER not in cat,
        "severity": "high",
        "mitigation": "Identify the economic buyer. Ask: 'Who besides yourself would be involved in this decision?'",
    },
    {
        "name": "Weak Urgency",
        "check": lambda cat: InsightCategory.URGENCY not in cat,
        "severity": "medium",
        "mitigation": "Build urgency by quantifying the cost of inaction. Ask: 'What happens if nothing changes in the next 6 months?'",
    },
    {
        "name": "No Executive Involvement",
        "check": lambda cat: InsightCategory.DECISION_MAKER not in cat,
        "severity": "medium",
        "mitigation": "Request executive sponsor engagement. Suggest an executive briefing.",
    },
    {
        "name": "No Implementation Timeline",
        "check": lambda cat: InsightCategory.TIMELINE not in cat,
        "severity": "medium",
        "mitigation": "Propose a phased timeline. Ask: 'When would you ideally want to have something in place?'",
    },
    {
        "name": "Weak Pain Points",
        "check": lambda cat: len(cat.get(InsightCategory.PAIN_POINT, [])) < 2,
        "severity": "medium",
        "mitigation": "Deepen discovery. Explore operational friction, time lost, and cost of current process.",
    },
    {
        "name": "Existing Vendor Lock-in",
        "check": lambda cat: InsightCategory.COMPETITOR in cat,
        "severity": "medium",
        "mitigation": "Explore gaps in current vendor relationship. Ask: 'What would your current solution need to do better?'",
    },
    {
        "name": "Multiple Objections",
        "check": lambda cat: len(cat.get(InsightCategory.OBJECTION, [])) >= 3,
        "severity": "high",
        "mitigation": "Address objections systematically. Prioritize budget and trust objections first.",
    },
    {
        "name": "No Goals Articulated",
        "check": lambda cat: InsightCategory.GOAL not in cat,
        "severity": "medium",
        "mitigation": "Clarify success criteria. Ask: 'What would success look like 6 months after implementation?'",
    },
    {
        "name": "Competitor Mention",
        "check": lambda cat: InsightCategory.COMPETITOR in cat,
        "severity": "low",
        "mitigation": "Differentiate on service, outcomes, and partnership. Avoid negative competitor mentions.",
    },
    {
        "name": "Scope Uncertainty",
        "check": lambda cat: (
            InsightCategory.CURRENT_PROCESS not in cat and
            InsightCategory.CURRENT_SOFTWARE not in cat
        ),
        "severity": "low",
        "mitigation": "Clarify scope through process walkthrough. Document current state before proposing solution.",
    },
]


@dataclass
class RiskReport:
    """Complete deal risk assessment."""
    risks: list[DealRisk] = field(default_factory=list)
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    overall_risk: str = "low"
    generated_at: str = ""


class RiskAnalysis:
    """Detects and scores deal risks from structured ConversationInsights.

    Evaluates missing information, objection patterns, competitor presence,
    and other risk factors. Returns severity and mitigation for each.
    """

    def evaluate(self, insights: list[ConversationInsight]) -> RiskReport:
        """Analyze risks from structured insights.

        Args:
            insights: ConversationInsights from the frozen pipeline
        """
        now = datetime.now(UTC).isoformat()

        # Build category lookup
        by_category: dict[InsightCategory, list[ConversationInsight]] = {}
        for ins in insights:
            by_category.setdefault(ins.category, []).append(ins)

        risks: list[DealRisk] = []
        for rule in RISK_RULES:
            if rule["check"](by_category):
                risks.append(DealRisk(
                    risk=rule["name"],
                    severity=rule["severity"],
                    mitigation=rule["mitigation"],
                ))

        critical = sum(1 for r in risks if r.severity == "critical")
        high = sum(1 for r in risks if r.severity == "high")
        medium = sum(1 for r in risks if r.severity == "medium")
        low = sum(1 for r in risks if r.severity == "low")

        # Overall risk
        if critical >= 1 or high >= 3:
            overall = "critical"
        elif high >= 1 or medium >= 3:
            overall = "high"
        elif medium >= 1 or low >= 2:
            overall = "medium"
        else:
            overall = "low"

        return RiskReport(
            risks=risks,
            critical_count=critical,
            high_count=high,
            medium_count=medium,
            low_count=low,
            overall_risk=overall,
            generated_at=now,
        )


# Singleton
_risk_analysis: RiskAnalysis | None = None


def get_risk_analysis() -> RiskAnalysis:
    global _risk_analysis
    if _risk_analysis is None:
        _risk_analysis = RiskAnalysis()
    return _risk_analysis
