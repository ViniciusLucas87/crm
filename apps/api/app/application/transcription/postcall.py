"""
Sprint 44 — Autonomous Post-Call Intelligence

When a call ends, the CRM updates itself.

Architecture:
    Transcript + Coach Events → PostCallPipeline → Auto-generated deliverables

Generates:
    - Meeting summary
    - Action items
    - Follow-up email draft
    - Proposal draft
    - Opportunity update
    - CRM notes
    - Tasks
    - Risk assessment
    - Deal score

Everything enters an approval queue — nothing is sent automatically.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import StrEnum
from typing import Any

from app.application.llm.provider import LLMConfig, LLMMessage, create_provider

logger = logging.getLogger(__name__)


class DeliverableStatus(StrEnum):
    PENDING = "pending"
    GENERATED = "generated"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"


class DeliverableType(StrEnum):
    MEETING_SUMMARY = "meeting_summary"
    ACTION_ITEMS = "action_items"
    FOLLOW_UP_EMAIL = "follow_up_email"
    PROPOSAL_DRAFT = "proposal_draft"
    CRM_NOTES = "crm_notes"
    TASKS = "tasks"
    RISK_ASSESSMENT = "risk_assessment"
    DEAL_SCORE = "deal_score"
    EXECUTIVE_SUMMARY = "executive_summary"
    NEXT_STEPS = "next_steps"


@dataclass
class PostCallDeliverable:
    """A single auto-generated deliverable awaiting approval."""
    id: str = ""
    type: DeliverableType = DeliverableType.MEETING_SUMMARY
    status: DeliverableStatus = DeliverableStatus.PENDING
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass
class PostCallReport:
    """Complete post-call intelligence report."""
    call_id: int | None = None
    transcript_id: int | None = None
    company_id: int | None = None
    deliverables: list[PostCallDeliverable] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class PostCallPipeline:
    """Generates all post-call deliverables from transcript + coach events."""

    def __init__(self, llm_config: LLMConfig):
        self._llm_config = llm_config

    async def generate_all(
        self,
        transcript_text: str,
        coach_events: list[dict],
        company_name: str = "",
        contact_name: str = "",
        call_id: int | None = None,
        transcript_id: int | None = None,
        company_id: int | None = None,
    ) -> PostCallReport:
        """Generate all post-call deliverables."""
        report = PostCallReport(
            call_id=call_id,
            transcript_id=transcript_id,
            company_id=company_id,
        )

        if not transcript_text.strip():
            return report

        tasks = [
            self._generate_meeting_summary(transcript_text, company_name, contact_name),
            self._generate_action_items(transcript_text),
            self._generate_follow_up_email(transcript_text, company_name, contact_name),
            self._generate_crm_notes(transcript_text, coach_events),
            self._generate_tasks(transcript_text),
            self._generate_risk_assessment(transcript_text, coach_events),
            self._generate_deal_score(transcript_text, coach_events),
            self._generate_next_steps(transcript_text),
        ]

        results = []
        for task in tasks:
            try:
                result = await task
                if result:
                    results.append(result)
            except Exception as e:
                logger.warning("Post-call generation failed for a deliverable: %s", e)

        report.deliverables = results
        return report

    async def _llm_generate(self, system: str, prompt: str, max_tokens: int = 500) -> str:
        """Run an LLM generation with error handling."""
        try:
            provider = create_provider(self._llm_config)
            messages = [
                LLMMessage(role="system", content=system),
                LLMMessage(role="user", content=prompt),
            ]
            response = await provider.complete(messages, temperature=0.3, max_tokens=max_tokens)
            return response.content.strip()
        except Exception as e:
            logger.error("LLM generation failed: %s", e)
            return ""

    async def _generate_meeting_summary(self, transcript: str, company: str, contact: str) -> PostCallDeliverable:
        system = "You are an executive assistant. Write a concise meeting summary from this sales call transcript. Include: key topics discussed, decisions made, and overall outcome."
        prompt = f"Company: {company}\nContact: {contact}\n\nTranscript:\n{transcript[-4000:]}"
        content = await self._llm_generate(system, prompt, 400)
        return PostCallDeliverable(
            id=f"summary-{datetime.now(UTC).timestamp():.0f}",
            type=DeliverableType.MEETING_SUMMARY,
            content=content,
        ) if content else None

    async def _generate_action_items(self, transcript: str) -> PostCallDeliverable:
        system = "Extract action items from this sales call transcript. Output as a JSON array of strings: [\"Action 1\", \"Action 2\", ...]"
        prompt = f"Transcript:\n{transcript[-4000:]}"
        content = await self._llm_generate(system, prompt, 300)
        return PostCallDeliverable(
            id=f"actions-{datetime.now(UTC).timestamp():.0f}",
            type=DeliverableType.ACTION_ITEMS,
            content=content,
        ) if content else None

    async def _generate_follow_up_email(self, transcript: str, company: str, contact: str) -> PostCallDeliverable:
        system = "You are a sales professional. Write a warm, professional follow-up email based on this sales call. Include a subject line. Reference specific points from the conversation."
        prompt = f"Company: {company}\nContact: {contact}\n\nConversation:\n{transcript[-4000:]}"
        content = await self._llm_generate(system, prompt, 500)
        return PostCallDeliverable(
            id=f"email-{datetime.now(UTC).timestamp():.0f}",
            type=DeliverableType.FOLLOW_UP_EMAIL,
            content=content,
        ) if content else None

    async def _generate_crm_notes(self, transcript: str, coach_events: list[dict]) -> PostCallDeliverable:
        objections = [e for e in coach_events if e.get("type") == "objection_detected"]
        buying_signals = [e for e in coach_events if e.get("type") == "buying_signal"]
        pain_points = [e for e in coach_events if e.get("type") == "pain_point_detected"]

        notes = ["## Call Summary\n"]
        if pain_points:
            notes.append("### Pain Points\n" + "\n".join(f"- {p.get('description', '')}" for p in pain_points))
        if objections:
            notes.append("### Objections\n" + "\n".join(f"- {o.get('description', '')}" for o in objections))
        if buying_signals:
            notes.append("### Buying Signals\n" + "\n".join(f"- {b.get('description', '')}" for b in buying_signals))

        return PostCallDeliverable(
            id=f"notes-{datetime.now(UTC).timestamp():.0f}",
            type=DeliverableType.CRM_NOTES,
            content="\n\n".join(notes),
        )

    async def _generate_tasks(self, transcript: str) -> PostCallDeliverable:
        system = "Extract specific tasks and next steps from this transcript. Output as JSON array: [{\"title\":\"...\", \"priority\":\"high|medium|low\", \"due_hint\":\"...\"}]"
        prompt = f"Transcript:\n{transcript[-4000:]}"
        content = await self._llm_generate(system, prompt, 300)
        return PostCallDeliverable(
            id=f"tasks-{datetime.now(UTC).timestamp():.0f}",
            type=DeliverableType.TASKS,
            content=content,
        ) if content else None

    async def _generate_risk_assessment(self, transcript: str, coach_events: list[dict]) -> PostCallDeliverable:
        system = "Assess deal risk from this sales conversation. Output JSON: {\"risk_level\":\"low|medium|high\", \"risk_factors\":[\"factor1\",...], \"mitigation\":\"...\"}"
        prompt = f"Coach events: {json.dumps(coach_events[-20:])}\n\nTranscript:\n{transcript[-3000:]}"
        content = await self._llm_generate(system, prompt, 300)
        return PostCallDeliverable(
            id=f"risk-{datetime.now(UTC).timestamp():.0f}",
            type=DeliverableType.RISK_ASSESSMENT,
            content=content,
        ) if content else None

    async def _generate_deal_score(self, transcript: str, coach_events: list[dict]) -> PostCallDeliverable:
        positive = sum(1 for e in coach_events if e.get("type") in ("buying_signal", "pain_point_detected"))
        negative = sum(1 for e in coach_events if e.get("type") in ("objection_detected", "competitor_mentioned"))
        base = 50 + (positive * 5) - (negative * 8)
        score = max(0, min(100, base))
        return PostCallDeliverable(
            id=f"deal-{datetime.now(UTC).timestamp():.0f}",
            type=DeliverableType.DEAL_SCORE,
            content=json.dumps({
                "score": score,
                "positive_signals": positive,
                "negative_signals": negative,
                "recommendation": "pursue" if score >= 60 else "nurture" if score >= 30 else "review",
            }),
        )

    async def _generate_next_steps(self, transcript: str) -> PostCallDeliverable:
        system = "Based on this sales call, suggest 3-5 concrete next steps. Output as a numbered list."
        prompt = f"Transcript:\n{transcript[-4000:]}"
        content = await self._llm_generate(system, prompt, 300)
        return PostCallDeliverable(
            id=f"nextsteps-{datetime.now(UTC).timestamp():.0f}",
            type=DeliverableType.NEXT_STEPS,
            content=content,
        ) if content else None
