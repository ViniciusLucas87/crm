"""
Opportunity Engine — scores deal quality 0-100.

Consumes ConversationInsights. Evaluates pain severity, buying signals,
decision maker engagement, timeline clarity, budget confidence, and urgency.

Architecture:
    ConversationInsights → OpportunityEngine → OpportunityReport
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any

from app.application.transcription.intelligence import ConversationInsight, InsightCategory


@dataclass
class OpportunityReport:
    """Scored opportunity assessment with strengths, weaknesses, and risk level."""
    score: int = 0
    confidence: int = 0
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    risk_level: str = "unknown"
    recommended_milestone: str = "Discovery"
    buying_signals_count: int = 0
    objections_count: int = 0
    generated_at: str = ""


class OpportunityEngine:
    """Scores deal quality from structured ConversationInsights.

    Produces a 0-100 Opportunity Score considering pain severity,
    buying signals, decision maker engagement, timeline clarity,
    budget confidence, and implementation urgency.
    """

    def evaluate(
        self,
        insights: list[ConversationInsight],
        discovery_pct: int = 0,
    ) -> OpportunityReport:
        """Score the opportunity.

        Args:
            insights: ConversationInsights from the frozen pipeline
            discovery_pct: Discovery completion percentage (0-100)
        """
        now = datetime.now(UTC).isoformat()
        by_category: dict[InsightCategory, list[ConversationInsight]] = {}
        for ins in insights:
            by_category.setdefault(ins.category, []).append(ins)

        pain_points = by_category.get(InsightCategory.PAIN_POINT, [])
        buying_signals = by_category.get(InsightCategory.BUYING_SIGNAL, [])
        decision_makers = by_category.get(InsightCategory.DECISION_MAKER, [])
        objections = by_category.get(InsightCategory.OBJECTION, [])
        goals = by_category.get(InsightCategory.GOAL, [])
        budget_ins = by_category.get(InsightCategory.BUDGET, [])
        timeline_ins = by_category.get(InsightCategory.TIMELINE, [])
        urgency_ins = by_category.get(InsightCategory.URGENCY, [])
        risks = by_category.get(InsightCategory.RISK, [])
        current_software = by_category.get(InsightCategory.CURRENT_SOFTWARE, [])
        current_process = by_category.get(InsightCategory.CURRENT_PROCESS, [])

        strengths: list[str] = []
        weaknesses: list[str] = []
        score = 30  # baseline

        # ── Pain point severity (0-25) ──
        if len(pain_points) >= 3:
            score += 25
            strengths.append("Multiple pain points identified — strong problem signal")
        elif len(pain_points) >= 1:
            score += 15
            strengths.append("Pain points identified")
            if len(pain_points) < 2:
                weaknesses.append("Limited pain points — may indicate shallow discovery")
        else:
            weaknesses.append("No pain points identified — discovery incomplete")

        # Check pain severity keywords
        severe_keywords = ["manual", "double", "duplicate", "lost", "slow", "error", "frustrating"]
        severe_count = sum(
            1 for p in pain_points
            if any(kw in p.value.lower() for kw in severe_keywords)
        )
        if severe_count >= 2:
            score += 5
            strengths.append("Severe operational pain detected — high urgency potential")

        # ── Buying signals (0-15) ──
        if len(buying_signals) >= 2:
            score += 15
            strengths.append("Strong buying signals — prospect is actively evaluating")
        elif len(buying_signals) == 1:
            score += 8
            strengths.append("Buying signal detected")
        else:
            weaknesses.append("No buying signals — prospect may be information-gathering only")

        # ── Decision maker (0-15) ──
        if len(decision_makers) >= 1:
            score += 15
            strengths.append("Decision maker identified — deal is qualifiable")
        else:
            weaknesses.append("Decision maker unknown — cannot qualify opportunity")

        # ── Budget (0-10) ──
        if budget_ins:
            score += 10
            strengths.append("Budget discussed — prospect has financial commitment")
        else:
            weaknesses.append("Budget unknown — financial commitment unclear")

        # ── Timeline (0-10) ──
        if timeline_ins:
            score += 10
            strengths.append("Timeline discussed — implementation window understood")
        else:
            weaknesses.append("Timeline unknown — cannot plan resource allocation")

        # ── Urgency (0-5) ──
        if urgency_ins:
            score += 5
            strengths.append("Urgency expressed — deal velocity likely high")

        # ── Goals (0-5) ──
        if goals:
            score += 5
            strengths.append("Goals articulated — solution alignment possible")

        # ── Deductions ──
        score -= len(objections) * 5
        if len(objections) >= 1:
            weaknesses.append(f"{len(objections)} objection(s) raised — needs resolution")

        if risks:
            score -= len(risks) * 3
            if len(risks) >= 2:
                weaknesses.append("Multiple risks identified")

        # Clamp
        score = max(0, min(score, 100))

        # ── Risk Level ──
        if score >= 80:
            risk_level = "low"
        elif score >= 55:
            risk_level = "medium"
        elif score >= 30:
            risk_level = "high"
        else:
            risk_level = "critical"

        # ── Recommended Milestone ──
        if discovery_pct < 40:
            milestone = "Discovery"
        elif discovery_pct < 70:
            milestone = "Technical Discovery"
        elif score >= 75:
            milestone = "Proposal"
        elif score >= 50:
            milestone = "Demo"
        else:
            milestone = "Re-qualification"

        # ── Confidence ──
        # Higher when we have more data points
        signal_count = (
            len(pain_points) + len(buying_signals) + len(decision_makers) +
            len(goals) + len(budget_ins) + len(timeline_ins)
        )
        confidence = min(90, signal_count * 8)

        return OpportunityReport(
            score=score,
            confidence=confidence,
            strengths=strengths,
            weaknesses=weaknesses,
            risk_level=risk_level,
            recommended_milestone=milestone,
            buying_signals_count=len(buying_signals),
            objections_count=len(objections),
            generated_at=now,
        )


# Singleton
_opportunity_engine: OpportunityEngine | None = None


def get_opportunity_engine() -> OpportunityEngine:
    global _opportunity_engine
    if _opportunity_engine is None:
        _opportunity_engine = OpportunityEngine()
    return _opportunity_engine
