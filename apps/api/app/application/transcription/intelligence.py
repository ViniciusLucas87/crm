"""
Conversation Intelligence — transforms transcripts into structured business knowledge.

This is the core intelligence layer between raw transcription and the Decision Engine.
Every insight includes confidence, evidence, and transcript reference.

Architecture:
    Transcript → ConversationIntelligence → Structured Insights → Decision Engine
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import StrEnum
from typing import Any

from app.application.llm.provider import LLMConfig, LLMMessage, create_provider
from app.application.transcription import TranscriptSegment

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# INSIGHT TYPES
# ═══════════════════════════════════════════════════════════

class InsightCategory(StrEnum):
    PAIN_POINT = "pain_point"
    CURRENT_SOFTWARE = "current_software"
    CURRENT_PROCESS = "current_process"
    DECISION_MAKER = "decision_maker"
    BUDGET = "budget"
    TIMELINE = "timeline"
    URGENCY = "urgency"
    BUYING_SIGNAL = "buying_signal"
    OBJECTION = "objection"
    COMPETITOR = "competitor"
    INTEGRATION = "integration"
    GOAL = "goal"
    RISK = "risk"
    COMPLIANCE = "compliance"
    CONSTRAINT = "constraint"
    ACTION_ITEM = "action_item"
    QUESTION = "question"
    COMMITMENT = "commitment"


@dataclass
class ConversationInsight:
    """A single business insight extracted from transcript with evidence."""
    category: InsightCategory
    value: str
    confidence: int  # 0-100
    evidence: str  # quote from transcript
    speaker: str = "Unknown"
    timestamp: str = ""  # ISO timestamp
    segment_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class IntelligenceReport:
    """Complete intelligence extracted from a conversation."""
    insights: list[ConversationInsight] = field(default_factory=list)
    pain_points: list[str] = field(default_factory=list)
    current_software: list[str] = field(default_factory=list)
    current_process: list[str] = field(default_factory=list)
    decision_makers: list[str] = field(default_factory=list)
    budget_indicated: str | None = None
    timeline_indicated: str | None = None
    buying_signals: list[str] = field(default_factory=list)
    objections: list[str] = field(default_factory=list)
    competitors: list[str] = field(default_factory=list)
    goals: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    action_items: list[str] = field(default_factory=list)
    questions_asked: list[str] = field(default_factory=list)
    commitments: list[str] = field(default_factory=list)
    summary: str = ""
    transcript_length: int = 0
    analyzed_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


# ═══════════════════════════════════════════════════════════
# INTELLIGENCE EXTRACTOR
# ═══════════════════════════════════════════════════════════

EXTRACTOR_SYSTEM_PROMPT = """You are a Conversation Intelligence system for Pacific North Systems — a technology consulting firm.

Analyze the following transcript and extract structured business intelligence. Only extract information that is explicitly stated in the transcript. Never hallucinate.

For each finding, include:
- category: the type of insight
- value: what was said
- confidence: 0-100 based on clarity
- evidence: exact quote from transcript
- speaker: who said it

Categories to detect:
- pain_point: problems, frustrations, challenges
- current_software: software/tools they currently use
- current_process: how things work today
- decision_maker: person with authority (name, title)
- budget: any mention of money, budget, cost
- timeline: any mention of when, deadlines, timing
- urgency: any indication of urgency level
- buying_signal: positive indicators of interest
- objection: concerns, hesitations, pushback
- competitor: other companies/solutions mentioned
- integration: systems that need to connect
- goal: what they want to achieve
- risk: potential problems with the deal
- action_item: follow-up tasks mentioned
- question: important questions asked

Output valid JSON:
{
  "insights": [
    {"category": "pain_point", "value": "...", "confidence": 85, "evidence": "...", "speaker": "Speaker 0"}
  ],
  "summary": "Brief 2-3 sentence summary of the conversation"
}
"""


class ConversationIntelligence:
    """Extracts structured business insights from conversation transcripts.

    Uses LLM to analyze transcript text and extract pain points, buying signals,
    decision makers, objections, budget, timeline, and more. Every insight includes
    evidence and transcript reference.
    """

    def __init__(self, api_key: str | None = None):
        self._api_key = api_key
        self._provider = None

    def _get_provider(self):
        if self._provider is None and self._api_key:
            try:
                config = LLMConfig(
                    provider="deepseek",
                    model="deepseek-chat",
                    api_key=self._api_key,
                    temperature=0.1,
                    max_tokens=2000,
                )
                self._provider = create_provider(config)
            except (ValueError, Exception):
                logger.warning("ConversationIntelligence: provider not available")
                return None
        return self._provider

    async def analyze(
        self,
        segments: list[TranscriptSegment],
        previous_insights: list[ConversationInsight] | None = None,
    ) -> IntelligenceReport:
        """Analyze transcript segments and extract business intelligence.

        Args:
            segments: Transcript segments to analyze
            previous_insights: Previously extracted insights for continuity
        """
        provider = self._get_provider()
        if not provider or not segments:
            return IntelligenceReport(
                analyzed_at=datetime.now(UTC).isoformat(),
            )

        # Build transcript text with speaker labels
        transcript_text = "\n".join(
            f"[{s.speaker}] ({s.start:.1f}s): {s.text}"
            for s in segments
        )

        previous_context = ""
        if previous_insights:
            prev_summary = "\n".join(
                f"- [{i.category.value}] {i.value}" for i in previous_insights[-10:]
            )
            previous_context = f"\nPreviously extracted insights:\n{prev_summary}\n"

        user_prompt = f"{previous_context}\nTranscript:\n{transcript_text}"

        try:
            response = await provider.chat(
                messages=[
                    LLMMessage(role="system", content=EXTRACTOR_SYSTEM_PROMPT),
                    LLMMessage(role="user", content=user_prompt[:8000]),
                ],
            )
            data = self._parse_json(response.content)
            return self._build_report(data, segments)

        except Exception as e:
            logger.error("ConversationIntelligence analysis failed: %s", e)
            return IntelligenceReport(analyzed_at=datetime.now(UTC).isoformat())

    def _parse_json(self, text: str) -> dict:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            import re
            match = re.search(r'\{[\s\S]*\}', text)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
        return {}

    def _build_report(self, data: dict, segments: list[TranscriptSegment]) -> IntelligenceReport:
        insights: list[ConversationInsight] = []
        for item in data.get("insights", []):
            if not isinstance(item, dict):
                continue
            cat = item.get("category", "")
            try:
                category = InsightCategory(cat)
            except ValueError:
                continue
            insights.append(ConversationInsight(
                category=category,
                value=str(item.get("value", "")),
                confidence=int(item.get("confidence", 50)),
                evidence=str(item.get("evidence", "")),
                speaker=str(item.get("speaker", "Unknown")),
            ))

        # Categorize
        def values(cat: InsightCategory) -> list[str]:
            return [i.value for i in insights if i.category == cat]

        return IntelligenceReport(
            insights=insights,
            pain_points=values(InsightCategory.PAIN_POINT),
            current_software=values(InsightCategory.CURRENT_SOFTWARE),
            current_process=values(InsightCategory.CURRENT_PROCESS),
            decision_makers=values(InsightCategory.DECISION_MAKER),
            budget_indicated=values(InsightCategory.BUDGET)[0] if values(InsightCategory.BUDGET) else None,
            timeline_indicated=values(InsightCategory.TIMELINE)[0] if values(InsightCategory.TIMELINE) else None,
            buying_signals=values(InsightCategory.BUYING_SIGNAL),
            objections=values(InsightCategory.OBJECTION),
            competitors=values(InsightCategory.COMPETITOR),
            goals=values(InsightCategory.GOAL),
            risks=values(InsightCategory.RISK),
            action_items=values(InsightCategory.ACTION_ITEM),
            questions_asked=values(InsightCategory.QUESTION),
            commitments=values(InsightCategory.COMMITMENT),
            summary=data.get("summary", ""),
            transcript_length=sum(len(s.text) for s in segments),
            analyzed_at=datetime.now(UTC).isoformat(),
        )


# Singleton
_intelligence: ConversationIntelligence | None = None


def get_conversation_intelligence(api_key: str | None = None) -> ConversationIntelligence:
    global _intelligence
    if _intelligence is None:
        import os
        key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        _intelligence = ConversationIntelligence(api_key=key)
    return _intelligence
