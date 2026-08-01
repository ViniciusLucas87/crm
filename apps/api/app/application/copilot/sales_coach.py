"""
AI Sales Coach — real-time coaching engine.

Consumes structured ConversationInsights from the frozen pipeline.
Never analyzes raw transcript. Recommends next best action,
discovery questions, product matches, and deal health scoring.

Architecture:
    ConversationInsights → SalesCoach → CoachingOutput → Copilot UI
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any

from app.application.transcription.intelligence import ConversationInsight, InsightCategory

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# PRODUCT MATCHING
# ═══════════════════════════════════════════════════════════

PAIN_POINT_TO_PRODUCT: dict[str, list[str]] = {
    "manual inspection": ["Inspection Platform", "Document AI"],
    "manual inspections": ["Inspection Platform", "Document AI"],
    "paperwork": ["Document AI", "Workflow Automation"],
    "paper": ["Document AI"],
    "scheduling": ["Workflow Automation", "Operations Dashboard"],
    "dispatch": ["Field Service Management", "Workflow Automation"],
    "spreadsheet": ["Operations Dashboard", "Custom CRM"],
    "excel": ["Operations Dashboard", "Custom CRM"],
    "disconnected": ["Custom Integration", "Operations Dashboard"],
    "integration": ["Custom Integration", "API Platform"],
    "reporting": ["Operations Dashboard", "Analytics Platform"],
    "communication": ["Client Portal", "Internal Tools"],
    "tracking": ["Field Service Management", "Operations Dashboard"],
    "compliance": ["Document AI", "Inspection Platform"],
    "safety": ["Inspection Platform", "Compliance Tools"],
    "data entry": ["Document AI", "AI Assistant"],
    "duplicate": ["Workflow Automation", "Custom CRM"],
    "follow-up": ["Client Portal", "CRM Platform"],
}

PNS_PRODUCTS = [
    "Inspection Platform",
    "Operations Dashboard",
    "Document AI",
    "Workflow Automation",
    "Custom CRM",
    "Field Service Management",
    "Client Portal",
    "AI Assistant",
    "Custom Integration",
    "Analytics Platform",
    "Internal Tools",
    "Scheduling Engine",
    "Compliance Tools",
]


def match_products(pain_points: list[str]) -> list[dict[str, Any]]:
    """Match detected pain points to PNS products with confidence scores."""
    scored: dict[str, int] = {}
    evidence: dict[str, list[str]] = {}

    for point in pain_points:
        point_lower = point.lower()
        for keyword, products in PAIN_POINT_TO_PRODUCT.items():
            if keyword in point_lower:
                for product in products:
                    scored[product] = scored.get(product, 0) + 1
                    if point not in evidence.get(product, []):
                        evidence.setdefault(product, []).append(point)

    results = sorted(
        [{"product": p, "score": min(s, 5), "evidence": evidence.get(p, [])} for p, s in scored.items()],
        key=lambda x: x["score"],
        reverse=True,
    )
    return results[:5]


# ═══════════════════════════════════════════════════════════
# COACHING OUTPUT
# ═══════════════════════════════════════════════════════════

DISCOVERY_FIELDS = [
    "company_size", "industry", "current_process", "current_software",
    "decision_maker", "budget", "timeline", "pain_points",
    "business_goal", "technical_constraints", "implementation_window",
    "roi_expectations", "approval_process", "urgency",
]

NEXT_QUESTIONS = {
    "decision_maker": "Who normally approves technology purchases like this?",
    "budget": "Do you have a budget allocated for this type of solution?",
    "timeline": "When would you ideally want to have something in place?",
    "current_software": "What tools are you currently using for this?",
    "current_process": "Walk me through how this works today.",
    "pain_points": "What's costing your team the most time right now?",
    "roi_expectations": "What would success look like 6 months after implementation?",
    "approval_process": "What does the approval process look like on your end?",
    "technical_constraints": "Are there any technical requirements or constraints we should know about?",
    "implementation_window": "How quickly would you need to be up and running?",
    "urgency": "What happens if nothing changes in the next 6 months?",
}

OBJECTION_RESPONSES: dict[str, str] = {
    "budget": "Focus on ROI. Ask: 'What would solving this problem be worth to your business?'",
    "timing": "Suggest phased rollout. Ask: 'Could we start with a pilot?'",
    "trust": "Offer references and case studies. Ask: 'Would it help to speak with a similar customer?'",
    "complexity": "Emphasize onboarding support. Ask: 'What would make implementation feel manageable?'",
    "competition": "Differentiate on service and outcomes. Ask: 'What's most important to you in a partner?'",
    "current_vendor": "Explore gaps. Ask: 'What would your current solution need to do better?'",
}


@dataclass
class CoachingOutput:
    """Complete coaching state for the Copilot UI."""
    # ── Progress ──
    discovery_progress: int = 0
    qualification_progress: int = 0
    deal_health: str = "unknown"

    # ── Discovery ──
    discovery_fields: list[dict[str, Any]] = field(default_factory=list)
    missing_fields: list[str] = field(default_factory=list)

    # ── Signals ──
    buying_signals: list[dict[str, Any]] = field(default_factory=list)
    objections: list[dict[str, Any]] = field(default_factory=list)
    urgency: str = "unknown"

    # ── Recommendations ──
    next_best_action: str = "Continue discovery"
    suggested_question: str | None = None
    suggested_products: list[dict[str, Any]] = field(default_factory=list)

    # ── Insights ──
    pain_points: list[str] = field(default_factory=list)
    current_software: list[str] = field(default_factory=list)
    decision_makers: list[str] = field(default_factory=list)
    budget_indicated: str | None = None
    timeline_indicated: str | None = None

    # ── Timing ──
    generated_at: str = ""


# ═══════════════════════════════════════════════════════════
# SALES COACH
# ═══════════════════════════════════════════════════════════

class SalesCoach:
    """Real-time AI Sales Coach.

    Consumes ConversationInsights from the frozen pipeline.
    Produces structured coaching output every few seconds.
    Never analyzes raw transcript.
    """

    def __init__(self) -> None:
        self._previous_output: CoachingOutput | None = None

    def analyze(self, insights: list[ConversationInsight]) -> CoachingOutput:
        """Analyze structured insights and produce coaching recommendations.

        Args:
            insights: ConversationInsights from the frozen intelligence pipeline
        """
        output = CoachingOutput(generated_at=datetime.now(UTC).isoformat())

        # ── Categorize insights ──
        pain_points = [i.value for i in insights if i.category == InsightCategory.PAIN_POINT]
        current_software = [i.value for i in insights if i.category == InsightCategory.CURRENT_SOFTWARE]
        decision_makers = [i.value for i in insights if i.category == InsightCategory.DECISION_MAKER]
        buying_signals = [i for i in insights if i.category == InsightCategory.BUYING_SIGNAL]
        objections = [i for i in insights if i.category == InsightCategory.OBJECTION]
        budget = next((i.value for i in insights if i.category == InsightCategory.BUDGET), None)
        timeline = next((i.value for i in insights if i.category == InsightCategory.TIMELINE), None)
        goals = [i.value for i in insights if i.category == InsightCategory.GOAL]
        risks = [i.value for i in insights if i.category == InsightCategory.RISK]

        output.pain_points = pain_points
        output.current_software = current_software
        output.decision_makers = decision_makers
        output.budget_indicated = budget
        output.timeline_indicated = timeline

        # ── Discovery progress ──
        output.discovery_fields = self._compute_discovery(insights, pain_points, current_software, decision_makers, budget, timeline, goals)
        known_count = sum(1 for f in output.discovery_fields if f["known"])
        output.discovery_progress = int((known_count / len(DISCOVERY_FIELDS)) * 100) if DISCOVERY_FIELDS else 0
        output.missing_fields = [f["field"] for f in output.discovery_fields if not f["known"]]

        # ── Qualification ──
        q_signals = len(buying_signals) + (1 if budget else 0) + (1 if timeline else 0) + (1 if decision_makers else 0)
        output.qualification_progress = min(q_signals * 20, 100)

        # ── Deal health ──
        output.deal_health = self._compute_deal_health(output.discovery_progress, output.qualification_progress, len(risks), len(objections))

        # ── Buying signals ──
        output.buying_signals = [
            {"signal": s.value, "confidence": s.confidence, "evidence": s.evidence or ""}
            for s in buying_signals
        ]

        # ── Objections ──
        output.objections = [
            {
                "objection": o.value,
                "confidence": o.confidence,
                "evidence": o.evidence or "",
                "response": OBJECTION_RESPONSES.get(o.value.lower()[:20], "Acknowledge and explore further."),
            }
            for o in objections
        ]

        # ── Urgency ──
        if timeline and any(w in str(timeline).lower() for w in ["immediately", "asap", "urgent"]):
            output.urgency = "high"
        elif timeline:
            output.urgency = "medium"
        elif risks:
            output.urgency = "medium"
        else:
            output.urgency = "low"

        # ── Suggested question ──
        output.suggested_question = self._pick_next_question(output.missing_fields)

        # ── Product matching ──
        output.suggested_products = match_products(pain_points)

        # ── Next best action ──
        output.next_best_action = self._determine_next_action(output)

        self._previous_output = output
        return output

    def _compute_discovery(self, insights, pain_points, software, decision_makers, budget, timeline, goals) -> list[dict]:
        fields = []
        field_map = {
            "pain_points": bool(pain_points),
            "current_software": bool(software),
            "decision_maker": bool(decision_makers),
            "budget": bool(budget),
            "timeline": bool(timeline),
            "business_goal": bool(goals),
            "current_process": any(i.category == InsightCategory.CURRENT_PROCESS for i in insights),
            "urgency": any(i.category == InsightCategory.URGENCY for i in insights),
            "technical_constraints": any(i.category == InsightCategory.CONSTRAINT for i in insights),
            "implementation_window": bool(timeline),
            "roi_expectations": False,
            "approval_process": False,
            "company_size": False,
            "industry": False,
        }
        for field in DISCOVERY_FIELDS:
            fields.append({"field": field, "known": field_map.get(field, False)})
        return fields

    def _compute_deal_health(self, discovery: int, qualification: int, risks: int, objections: int) -> str:
        score = (discovery + qualification) // 2
        score -= risks * 10
        score -= objections * 5
        if score >= 75:
            return "excellent"
        elif score >= 50:
            return "good"
        elif score >= 25:
            return "fair"
        return "poor"

    def _pick_next_question(self, missing: list[str]) -> str | None:
        priority = ["decision_maker", "budget", "timeline", "pain_points", "current_process", "current_software"]
        for field in priority:
            if field in missing and field in NEXT_QUESTIONS:
                return NEXT_QUESTIONS[field]
        for field in missing:
            if field in NEXT_QUESTIONS:
                return NEXT_QUESTIONS[field]
        return "What would success look like for this project?"

    def _determine_next_action(self, output: CoachingOutput) -> str:
        if output.discovery_progress < 40:
            return "Continue discovery — focus on pain points and current process"
        if output.discovery_progress < 70:
            return "Explore budget and timeline"
        if output.qualification_progress < 40:
            return "Qualify — identify decision maker and urgency"
        if output.qualification_progress < 70:
            return "Discuss ROI and technical requirements"
        if output.objections:
            return "Address objections before proceeding"
        if output.discovery_progress >= 80 and output.qualification_progress >= 60:
            return "Schedule technical demo"
        if output.discovery_progress >= 90 and output.qualification_progress >= 80:
            return "Generate proposal"
        return "Continue discovery"


# Singleton
_coach: SalesCoach | None = None


def get_sales_coach() -> SalesCoach:
    global _coach
    if _coach is None:
        _coach = SalesCoach()
    return _coach
