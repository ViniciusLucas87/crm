"""
Discovery Engine — tracks completeness of sales discovery.

Consumes ConversationInsights. Computes completion %, identifies missing
fields, and explains WHY each missing field matters to the opportunity.

Architecture:
    ConversationInsights → DiscoveryEngine → DiscoveryReport
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any

from app.application.transcription.intelligence import ConversationInsight, InsightCategory

# ── Field definitions with business rationale ──

DISCOVERY_FIELDS = {
    "company": {
        "label": "Company",
        "category": None,
        "reason": "Cannot qualify without understanding what the company does.",
        "priority": 1,
    },
    "industry": {
        "label": "Industry",
        "category": None,
        "reason": "Different industries have different regulatory and operational requirements that affect solution design.",
        "priority": 2,
    },
    "employees": {
        "label": "Employees",
        "category": None,
        "reason": "Team size determines license count, training scope, and rollout complexity.",
        "priority": 3,
    },
    "current_process": {
        "label": "Current Process",
        "category": InsightCategory.CURRENT_PROCESS,
        "reason": "Must understand existing workflow to design the right replacement.",
        "priority": 4,
    },
    "current_software": {
        "label": "Current Software",
        "category": InsightCategory.CURRENT_SOFTWARE,
        "reason": "Integration requirements and migration strategy depend on the existing technology stack.",
        "priority": 5,
    },
    "pain_points": {
        "label": "Pain Points",
        "category": InsightCategory.PAIN_POINT,
        "reason": "Without knowing the pain, you're selling blind. Pain drives urgency and budget.",
        "priority": 6,
    },
    "goals": {
        "label": "Goals",
        "category": InsightCategory.GOAL,
        "reason": "Defines success criteria and aligns the proposed solution with business outcomes.",
        "priority": 7,
    },
    "decision_maker": {
        "label": "Decision Maker",
        "category": InsightCategory.DECISION_MAKER,
        "reason": "Cannot qualify opportunity without identifying who approves purchases.",
        "priority": 8,
    },
    "budget": {
        "label": "Budget",
        "category": InsightCategory.BUDGET,
        "reason": "Required before discussing implementation investment and scope.",
        "priority": 9,
    },
    "timeline": {
        "label": "Timeline",
        "category": InsightCategory.TIMELINE,
        "reason": "Needed to recommend phased deployment and align resources.",
        "priority": 10,
    },
    "technical_constraints": {
        "label": "Technical Constraints",
        "category": InsightCategory.CONSTRAINT,
        "reason": "Security, compliance, or infrastructure constraints may disqualify certain solutions.",
        "priority": 11,
    },
    "implementation_window": {
        "label": "Implementation Window",
        "category": InsightCategory.TIMELINE,
        "reason": "Determines project phasing and resource allocation.",
        "priority": 12,
    },
    "roi_expectations": {
        "label": "ROI Expectations",
        "category": InsightCategory.GOAL,
        "reason": "Defines the value proposition and justifies the investment to economic buyers.",
        "priority": 13,
    },
    "urgency": {
        "label": "Urgency",
        "category": InsightCategory.URGENCY,
        "reason": "Urgency drives deal velocity. Without it, opportunities stall.",
        "priority": 14,
    },
}


@dataclass
class FieldStatus:
    field_key: str
    label: str
    known: bool
    value: str | None = None
    evidence: str | None = None
    confidence: int = 0
    priority: int = 99


@dataclass
class DiscoveryReport:
    """Complete discovery assessment with rationale for each missing field."""
    fields: list[FieldStatus] = field(default_factory=list)
    completion_pct: int = 0
    missing_keys: list[str] = field(default_factory=list)
    missing_priority_order: list[dict[str, str]] = field(default_factory=list)
    generated_at: str = ""


class DiscoveryEngine:
    """Evaluates discovery completeness from structured ConversationInsights.

    Tracks which fields are known, computes completion percentage,
    and explains WHY each missing field matters.
    """

    def evaluate(
        self,
        insights: list[ConversationInsight],
        company_context: dict[str, Any] | None = None,
    ) -> DiscoveryReport:
        """Evaluate discovery completeness.

        Args:
            insights: ConversationInsights from the frozen pipeline
            company_context: Optional company data (name, industry, etc.)
        """
        ctx = company_context or {}
        now = datetime.now(UTC).isoformat()

        # Build quick lookup by category
        by_category: dict[InsightCategory, list[ConversationInsight]] = {}
        for ins in insights:
            by_category.setdefault(ins.category, []).append(ins)

        fields: list[FieldStatus] = []
        for key, defn in DISCOVERY_FIELDS.items():
            known = False
            value = None
            evidence = None
            confidence = 0

            # Check company context first
            if key == "company" and ctx.get("name"):
                known = True
                value = ctx["name"]
            elif key == "industry" and ctx.get("industry"):
                known = True
                value = ctx["industry"]
            elif key == "employees" and ctx.get("employees"):
                known = True
                value = str(ctx["employees"])

            # Check insights by category
            cat = defn["category"]
            if cat and cat in by_category:
                ins = by_category[cat][0]
                known = True
                value = ins.value
                evidence = ins.evidence
                confidence = ins.confidence

            fields.append(FieldStatus(
                field_key=key,
                label=defn["label"],
                known=known,
                value=value,
                evidence=evidence,
                confidence=confidence,
                priority=defn["priority"],
            ))

        known_count = sum(1 for f in fields if f.known)
        completion = int((known_count / len(fields)) * 100) if fields else 0
        missing_keys = [f.field_key for f in fields if not f.known]

        # Missing fields with reasons, in priority order
        missing_priority = sorted(
            [
                {
                    "field": f.field_key,
                    "label": f.label,
                    "reason": DISCOVERY_FIELDS[f.field_key]["reason"],
                    "priority": f.priority,
                }
                for f in fields if not f.known
            ],
            key=lambda x: x["priority"],
        )

        return DiscoveryReport(
            fields=fields,
            completion_pct=completion,
            missing_keys=missing_keys,
            missing_priority_order=missing_priority,
            generated_at=now,
        )


# Singleton
_discovery_engine: DiscoveryEngine | None = None


def get_discovery_engine() -> DiscoveryEngine:
    global _discovery_engine
    if _discovery_engine is None:
        _discovery_engine = DiscoveryEngine()
    return _discovery_engine
