"""
Recommendation Engine — ranked product matching with confidence and reasoning.

Consumes ConversationInsights. Extends deterministic keyword matching
with confidence scoring, ranked output, and business rationale.

Architecture:
    ConversationInsights → RecommendationEngine → list[ProductRecommendation]
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any

from app.application.transcription.intelligence import ConversationInsight, InsightCategory


# ── Keyword → Product mapping with reasoning templates ──

PRODUCT_MAPPING: dict[str, dict[str, Any]] = {
    "Inspection Platform": {
        "keywords": ["inspection", "inspections", "field inspection", "site inspection", "audit"],
        "reason": "Manual inspections referenced — Inspection Platform provides mobile-first inspection management.",
    },
    "Operations Dashboard": {
        "keywords": ["spreadsheet", "excel", "dashboard", "reporting", "visibility", "tracking", "overview"],
        "reason": "Spreadsheet-driven operations detected — Operations Dashboard provides real-time visibility.",
    },
    "Document AI": {
        "keywords": ["paper", "paperwork", "document", "form", "data entry", "scan", "compliance"],
        "reason": "High paperwork volume detected — Document AI automates document processing and data extraction.",
    },
    "Workflow Automation": {
        "keywords": ["workflow", "automation", "manual process", "manual processes", "duplicate", "double entry"],
        "reason": "Manual workflows detected — Workflow Automation streamlines repetitive processes.",
    },
    "Custom CRM": {
        "keywords": ["crm", "customer management", "contact management", "lead tracking", "spreadsheet"],
        "reason": "CRM gaps detected — Custom CRM centralizes customer data and pipeline management.",
    },
    "Field Service Management": {
        "keywords": ["dispatch", "scheduling", "field", "technician", "truck", "mobile", "route"],
        "reason": "Field operations referenced — Field Service Management optimizes dispatch and scheduling.",
    },
    "Client Portal": {
        "keywords": ["client", "customer portal", "self-service", "communication", "follow-up"],
        "reason": "Client communication gaps — Client Portal provides self-service and automated follow-ups.",
    },
    "AI Assistant": {
        "keywords": ["ai", "automation", "data entry", "assistant", "chatbot"],
        "reason": "Efficiency gaps detected — AI Assistant augments team productivity.",
    },
    "Custom Integration": {
        "keywords": ["integration", "integrate", "disconnected", "multiple system", "silo"],
        "reason": "Disconnected systems detected — Custom Integration connects existing software investments.",
    },
    "Analytics Platform": {
        "keywords": ["analytics", "reporting", "report", "metrics", "kpi", "business intelligence"],
        "reason": "Reporting gaps — Analytics Platform provides comprehensive business intelligence.",
    },
    "Internal Tools": {
        "keywords": ["internal", "custom tool", "legacy", "build", "in-house"],
        "reason": "Custom/legacy tools referenced — Internal Tools replace outdated bespoke systems.",
    },
    "Scheduling Engine": {
        "keywords": ["schedule", "scheduling", "booking", "appointment", "calendar"],
        "reason": "Scheduling challenges — Scheduling Engine automates booking and resource allocation.",
    },
    "Compliance Tools": {
        "keywords": ["compliance", "regulatory", "regulation", "safety", "audit trail"],
        "reason": "Compliance requirements — Compliance Tools ensure regulatory adherence and audit readiness.",
    },
}


@dataclass
class ProductRecommendation:
    product: str
    confidence: int  # 0-100
    reason: str
    evidence: list[str] = field(default_factory=list)
    rank: int = 0


class RecommendationEngine:
    """Ranked product recommendations from structured ConversationInsights.

    Matches pain points and current software mentions to PNS products
    with confidence scoring and business rationale. Never returns more
    than five recommendations.
    """

    MAX_RECOMMENDATIONS = 5

    def recommend(
        self,
        insights: list[ConversationInsight],
    ) -> list[ProductRecommendation]:
        """Generate ranked product recommendations.

        Args:
            insights: ConversationInsights from the frozen pipeline
        """
        now = datetime.now(UTC).isoformat()

        # Collect all relevant text
        relevant_insights = [
            i for i in insights
            if i.category in (
                InsightCategory.PAIN_POINT,
                InsightCategory.CURRENT_SOFTWARE,
                InsightCategory.CURRENT_PROCESS,
                InsightCategory.GOAL,
                InsightCategory.CONSTRAINT,
            )
        ]

        # Score each product
        scored: dict[str, dict] = {}
        for ins in relevant_insights:
            text = ins.value.lower()
            for product, mapping in PRODUCT_MAPPING.items():
                for kw in mapping["keywords"]:
                    if kw in text:
                        if product not in scored:
                            scored[product] = {"hits": 0, "evidence": [], "reason": mapping["reason"]}
                        scored[product]["hits"] += 1
                        if ins.value not in scored[product]["evidence"]:
                            scored[product]["evidence"].append(ins.value)

        if not scored:
            return []

        # Convert to recommendations with confidence
        max_hits = max(s["hits"] for s in scored.values())
        recommendations: list[ProductRecommendation] = []
        for product, data in scored.items():
            confidence = min(98, int((data["hits"] / max(max_hits, 1)) * 100))
            # Bonus for multiple evidence items
            if len(data["evidence"]) >= 2:
                confidence = min(98, confidence + 10)

            recommendations.append(ProductRecommendation(
                product=product,
                confidence=confidence,
                reason=data["reason"],
                evidence=data["evidence"],
                rank=0,
            ))

        # Sort by confidence descending, cap at 5
        recommendations.sort(key=lambda r: r.confidence, reverse=True)
        for i, rec in enumerate(recommendations[:self.MAX_RECOMMENDATIONS]):
            rec.rank = i + 1

        return recommendations[:self.MAX_RECOMMENDATIONS]


# Singleton
_recommendation_engine: RecommendationEngine | None = None


def get_recommendation_engine() -> RecommendationEngine:
    global _recommendation_engine
    if _recommendation_engine is None:
        _recommendation_engine = RecommendationEngine()
    return _recommendation_engine
