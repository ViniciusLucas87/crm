"""
AI Sales Copilot — Decision Engine.

Continuously analyzes conversation context and generates structured
coaching recommendations. This is NOT a chatbot — it's a real-time
sales engineer that observes, reasons, and proactively coaches.

Architecture:
    Channels → TranscriptProvider → ConversationEngine → DecisionEngine → Copilot UI
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from app.application.llm.provider import LLMMessage

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# TYPES
# ═══════════════════════════════════════════════════════════

class DiscoveryField(StrEnum):
    COMPANY_SIZE = "company_size"
    INDUSTRY = "industry"
    DECISION_MAKER = "decision_maker"
    CURRENT_SOFTWARE = "current_software"
    CURRENT_PROCESS = "current_process"
    PAIN_POINTS = "pain_points"
    BUDGET = "budget"
    TIMELINE = "timeline"
    AUTHORITY = "authority"
    URGENCY = "urgency"
    BUYING_MOTIVATION = "buying_motivation"
    TECHNICAL_CONSTRAINTS = "technical_constraints"
    SECURITY_REQUIREMENTS = "security_requirements"
    INTEGRATIONS = "integrations"
    COMPLIANCE = "compliance"


class FieldStatus(StrEnum):
    KNOWN = "known"
    UNKNOWN = "unknown"
    ESTIMATED = "estimated"
    VERIFIED = "verified"


class AlertLevel(StrEnum):
    POSITIVE = "positive"
    WARNING = "warning"
    CRITICAL = "critical"
    INFO = "info"


@dataclass
class DiscoveryItem:
    field: str
    status: FieldStatus = FieldStatus.UNKNOWN
    value: str | None = None
    confidence: int = 0


@dataclass
class CoachAlert:
    level: AlertLevel
    message: str
    detail: str | None = None


@dataclass
class CoachRecommendation:
    """Structured coaching output from the Decision Engine."""
    conversation_stage: str = "discovery"
    discovery_progress: int = 0
    qualification_progress: int = 0

    # ── Key signals ──
    pain_points: list[str] = field(default_factory=list)
    buying_signals: list[str] = field(default_factory=list)
    objections: list[str] = field(default_factory=list)
    competitor_mentions: list[str] = field(default_factory=list)

    # ── Recommendations ──
    suggested_question: str | None = None
    suggested_product: str | None = None
    suggested_case_study: str | None = None
    suggested_next_step: str | None = None
    current_strategy: str | None = None
    alternative_strategy: str | None = None

    # ── Deal metrics ──
    estimated_deal_score: int = 0
    estimated_close_probability: int = 0
    budget_indicated: str | None = None
    timeline_indicated: str | None = None
    decision_maker_identified: bool = False

    # ── Discovery ──
    discovery_fields: list[DiscoveryItem] = field(default_factory=list)
    missing_information: list[str] = field(default_factory=list)

    # ── Alerts ──
    alerts: list[CoachAlert] = field(default_factory=list)

    # ── Integration opportunities ──
    integration_opportunities: list[str] = field(default_factory=list)

    # ── Raw ──
    raw_analysis: dict[str, Any] = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════
# DECISION ENGINE
# ═══════════════════════════════════════════════════════════

COPILOT_SYSTEM_PROMPT = """You are an AI Sales Copilot for Pacific North Systems — a technology consulting firm specializing in field service software, workflow automation, inspection platforms, and AI-powered operations.

You are NOT a chatbot. You are an invisible sales coach. You do not greet. You do not chat. You analyze the conversation and provide structured coaching output.

Analyze the conversation context and provide:

1. CONVERSATION STAGE: discovery | qualification | proposal | negotiation | closing
2. DISCOVERY PROGRESS: percentage 0-100
3. QUALIFICATION PROGRESS: percentage 0-100
4. PAIN POINTS: list of detected pain points
5. BUYING SIGNALS: list of detected buying signals
6. OBJECTIONS: list of detected objections
7. COMPETITOR MENTIONS: list of competitors mentioned
8. RECOMMENDATIONS:
   - suggested_question: the single best question to ask right now
   - suggested_product: which PNS service best fits
   - suggested_case_study: what case study to reference
   - suggested_next_step: what action to take next
   - current_strategy: current recommended approach
   - alternative_strategy: backup approach
9. DEAL METRICS:
   - estimated_deal_score: 0-100
   - estimated_close_probability: 0-100
   - budget_indicated: budget range or null
   - timeline_indicated: timeline or null
   - decision_maker_identified: true/false
10. MISSING INFORMATION: what key info is still unknown
11. ALERTS: subtle coaching alerts (positive/warning/critical/info)
12. INTEGRATION OPPORTUNITIES: potential integrations

IMPORTANT: If the customer mentions a competitor's software (ServiceTitan, Salesforce, Housecall Pro, Jobber, etc.), do NOT recommend replacing it. Instead, recommend integration, workflow automation, or complementary services.

Output valid JSON matching this structure:
{
  "conversation_stage": "discovery",
  "discovery_progress": 30,
  "qualification_progress": 15,
  "pain_points": [],
  "buying_signals": [],
  "objections": [],
  "competitor_mentions": [],
  "suggested_question": null,
  "suggested_product": null,
  "suggested_case_study": null,
  "suggested_next_step": null,
  "current_strategy": null,
  "alternative_strategy": null,
  "estimated_deal_score": 0,
  "estimated_close_probability": 0,
  "budget_indicated": null,
  "timeline_indicated": null,
  "decision_maker_identified": false,
  "missing_information": [],
  "alerts": [],
  "integration_opportunities": []
}
"""


class DecisionEngine:
    """Real-time sales coaching engine.

    Analyzes conversation context and generates structured recommendations.
    Designed to be called every few seconds during a live call/meeting.
    """

    def __init__(self, llm_api_key: str | None = None):
        # Compatibility parameter only.  The gateway owns credentials and budget.
        self._configured = True

    async def analyze(
        self,
        transcript: str = "",
        company_context: dict[str, Any] | None = None,
        conversation_history: list[dict] | None = None,
        previous_recommendations: dict | None = None,
    ) -> CoachRecommendation:
        """Analyze the current conversation state and return coaching recommendations."""
        from app.application.llm.gateway import get_llm_gateway, GatewayConfig

        context_parts = []
        if company_context:
            context_parts.append(f"Company: {json.dumps(company_context)}")
        if conversation_history:
            context_parts.append(f"History: {json.dumps(conversation_history[-3:])}")
        if previous_recommendations:
            context_parts.append(f"Previous State: {json.dumps(previous_recommendations)}")
        if transcript:
            context_parts.append(f"Recent Transcript: {transcript}")
        else:
            context_parts.append("No transcript yet. Analyze based on company context only.")

        user_prompt = "\n\n".join(context_parts)

        try:
            gateway = get_llm_gateway()
            gcfg = GatewayConfig(feature="coaching", organization_id=1, temperature=0.3, max_tokens=1500)
            resp = await gateway.chat(
                messages=[
                    LLMMessage(role="system", content=COPILOT_SYSTEM_PROMPT),
                    LLMMessage(role="user", content=user_prompt),
                ],
                config=gcfg,
            )

            data = self._parse_response(resp.content)
            return self._build_recommendation(data)

        except Exception as e:
            logger.error("DecisionEngine analysis failed: %s", e)
            return self._empty_recommendation(error=str(e))

    def _parse_response(self, response: str) -> dict:
        """Extract JSON from LLM response."""
        # Try direct JSON parse
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Try extracting from code blocks
        import re
        match = re.search(r'\{[\s\S]*\}', response)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        logger.warning("DecisionEngine: could not parse LLM response")
        return {}

    def _build_recommendation(self, data: dict) -> CoachRecommendation:
        """Build a CoachRecommendation from parsed LLM data."""
        alerts = []
        for a in data.get("alerts", []):
            if isinstance(a, dict):
                alerts.append(CoachAlert(
                    level=AlertLevel(a.get("level", "info")),
                    message=a.get("message", ""),
                    detail=a.get("detail"),
                ))

        discovery_fields = self._build_discovery_fields(data, {})
        missing = data.get("missing_information", [])

        return CoachRecommendation(
            conversation_stage=data.get("conversation_stage", "discovery"),
            discovery_progress=data.get("discovery_progress", 0),
            qualification_progress=data.get("qualification_progress", 0),
            pain_points=data.get("pain_points", []),
            buying_signals=data.get("buying_signals", []),
            objections=data.get("objections", []),
            competitor_mentions=data.get("competitor_mentions", []),
            suggested_question=data.get("suggested_question"),
            suggested_product=data.get("suggested_product"),
            suggested_case_study=data.get("suggested_case_study"),
            suggested_next_step=data.get("suggested_next_step"),
            current_strategy=data.get("current_strategy"),
            alternative_strategy=data.get("alternative_strategy"),
            estimated_deal_score=data.get("estimated_deal_score", 0),
            estimated_close_probability=data.get("estimated_close_probability", 0),
            budget_indicated=data.get("budget_indicated"),
            timeline_indicated=data.get("timeline_indicated"),
            decision_maker_identified=data.get("decision_maker_identified", False),
            discovery_fields=discovery_fields,
            missing_information=missing if isinstance(missing, list) else [],
            alerts=alerts,
            integration_opportunities=data.get("integration_opportunities", []),
            raw_analysis=data,
        )

    def _build_discovery_fields(self, data: dict, _context: dict) -> list[DiscoveryItem]:
        """Build discovery field status from LLM output and known context."""
        fields = []
        for field in DiscoveryField:
            fields.append(DiscoveryItem(
                field=field.value,
                status=FieldStatus.UNKNOWN,
                confidence=0,
            ))

        # Mark fields from known context
        known = data.get("discovery_fields", {})
        if isinstance(known, dict):
            for item in fields:
                if item.field in known:
                    f = known[item.field]
                    if isinstance(f, dict):
                        item.status = FieldStatus(f.get("status", "unknown"))
                        item.value = f.get("value")
                        item.confidence = f.get("confidence", 0)
        return fields

    def _empty_recommendation(self, error: str | None = None) -> CoachRecommendation:
        """Return an empty recommendation when analysis can't run."""
        return CoachRecommendation(
            alerts=[CoachAlert(level=AlertLevel.INFO, message="Copilot initializing…", detail=error)] if error else [],
            raw_analysis={"error": error} if error else {},
        )


# Singleton
_engine: DecisionEngine | None = None


def get_decision_engine(api_key: str | None = None) -> DecisionEngine:
    global _engine
    if _engine is None:
        _engine = DecisionEngine()
    return _engine
