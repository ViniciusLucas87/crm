"""
LLM Enrichment Service.

Takes structured CRM context and uses the LLM to produce
richer explanations, stronger recommendations, and clearer insights.
All prompts use shared components for consistency and reliability.

Consumers: Company Analysis, Daily Brief, Meeting Prep, Proposal Builder, Pipeline Coach
Fallback: Returns EnrichmentResult(enriched=False) when LLM unavailable.
"""

import json
import time
from dataclasses import dataclass
from typing import Any

from app.application.llm.provider import LLMConfig, LLMMessage, create_provider
from app.application.llm.prompt_components import (
    ANTI_HALLUCINATION_FOOTER,
    ENRICHMENT_SYSTEM_PROMPT,
    build_prompt,
)


@dataclass
class EnrichmentResult:
    enriched: bool
    content: str
    model_used: str | None
    confidence: str = "medium"


def _compact_json(obj: dict[str, Any]) -> str:
    return json.dumps(obj, default=str, separators=(",", ":"))


class EnrichmentService:
    """LLM enrichment for structured CRM data."""

    def __init__(self, api_key: str = "", provider: str = "deepseek", model: str = "deepseek-chat") -> None:
        self._configured = bool(api_key)
        self._config = LLMConfig(
            provider=provider, model=model, api_key=api_key,
            api_base="https://api.deepseek.com/v1" if provider == "deepseek" else None,
            temperature=0.3, max_tokens=1024,
        )

    @property
    def available(self) -> bool:
        return self._configured

    async def enrich(self, enrichment_type: str, context: dict[str, Any]) -> EnrichmentResult:
        return await self._do_enrich(enrichment_type, context)

    def enrich_sync(self, enrichment_type: str, context: dict[str, Any]) -> EnrichmentResult:
        import asyncio
        return asyncio.run(self._do_enrich(enrichment_type, context))

    async def _do_enrich(self, enrichment_type: str, context: dict[str, Any]) -> EnrichmentResult:
        if not self._configured:
            return EnrichmentResult(enriched=False, content="", model_used=None)
        prompt = self._get_prompt(enrichment_type, context)
        if not prompt:
            return EnrichmentResult(enriched=False, content="", model_used=None)

        start = time.time()
        success = True
        error_msg = ""
        try:
            llm = create_provider(self._config)
            messages = [
                LLMMessage(role="system", content=ENRICHMENT_SYSTEM_PROMPT),
                LLMMessage(role="user", content=prompt),
            ]
            response = await llm.chat(messages)
            result = EnrichmentResult(enriched=True, content=response.content, model_used=self._config.model)
        except Exception as e:
            success = False
            error_msg = str(e)
            result = EnrichmentResult(enriched=False, content="", model_used=None)

        # Async telemetry — never blocks
        latency = int((time.time() - start) * 1000)
        try:
            from app.infrastructure.telemetry import get_telemetry
            get_telemetry().log_request(
                org_id=context.get("_org_id", 0),
                feature=enrichment_type,
                provider=self._config.provider,
                model=self._config.model,
                prompt_name=enrichment_type,
                input_tokens=len(prompt) // 4,
                output_tokens=len(result.content) // 4 if result.content else 0,
                latency_ms=latency,
                success=success,
                fallback_used=not result.enriched,
                error_message=error_msg,
            )
        except Exception:
            pass

        return result

    def _get_prompt(self, enrichment_type: str, context: dict[str, Any]) -> str:
        ctx = _compact_json(context)
        prompts: dict[str, str] = {
            "daily_brief": self._daily_brief(ctx),
            "company_analysis": self._company_analysis(ctx),
            "company_analysis_full": self._company_analysis_full(ctx, context),
            "meeting_prep": self._meeting_prep(ctx),
            "proposal": self._proposal_short(ctx),
            "proposal_full": self._proposal_full(ctx, context),
            "pipeline": self._pipeline(ctx),
            "next_action": self._next_action(ctx),
            "executive_summary": self._executive_summary(ctx),
        }
        return prompts.get(enrichment_type, "")

    # ── Short Enrichment Prompts ──

    def _daily_brief(self, ctx: str) -> str:
        return f"""Analyze this daily briefing data:
{ctx}

Provide:
1. Most important priority today (or "No clear priority" if none)
2. Company needing attention (with reason, or "None identified")
3. One specific action (or "No specific action indicated")
{ANTI_HALLUCINATION_FOOTER}"""

    def _company_analysis(self, ctx: str) -> str:
        return f"""Company data:
{ctx}

Provide: 1) Strongest reason this is (or isn't) a good prospect, 2) Conversation starter for first call, 3) Biggest risk.
{ANTI_HALLUCINATION_FOOTER}"""

    def _meeting_prep(self, ctx: str) -> str:
        return f"""Meeting context:
{ctx}

Provide: 1) The ONE question to impress the prospect, 2) Most likely objection + counter, 3) Closing statement referencing their industry.
{ANTI_HALLUCINATION_FOOTER}"""

    def _proposal_short(self, ctx: str) -> str:
        return f"""Proposal context:
{ctx}

Provide: 1) Strongest value proposition, 2) One customization to stand out, 3) ROI argument most likely to resonate.
{ANTI_HALLUCINATION_FOOTER}"""

    def _pipeline(self, ctx: str) -> str:
        return f"""Pipeline data:
{ctx}

Provide: 1) Pipeline health (1 sentence), 2) Deal most likely to close (with reason), 3) Deal most at risk (with specific action).
{ANTI_HALLUCINATION_FOOTER}"""

    def _next_action(self, ctx: str) -> str:
        return f"""Context:
{ctx}

Recommend the single most impactful action. Be specific (company, action, outcome). If unclear, say so.
{ANTI_HALLUCINATION_FOOTER}"""

    def _executive_summary(self, ctx: str) -> str:
        return f"""Write a 3-4 sentence executive summary for a business intelligence report.

Platform data:
{ctx}

Cover: overall health, AI performance, cost efficiency, and key trends.
Be concise, data-driven, executive-friendly prose. No bullet points.
{ANTI_HALLUCINATION_FOOTER}"""

    # ── Full Enrichment Prompts (JSON output) ──

    def _company_analysis_full(self, ctx: str, context: dict[str, Any]) -> str:
        name = context.get("name", "Unknown")
        industry = context.get("industry", "Unknown")
        services = ", ".join(context.get("recommended_services", ["Custom CRM"]))
        return build_prompt(
            role=f"You are a senior business analyst at Pacific North Systems. Analyze {name} ({industry}).",
            goal="Generate a comprehensive company analysis using only the provided CRM data.",
            context=ctx,
            output_format=f"""Respond with valid JSON only:
{{"executive_summary":"2-3 sentence synthesis","business_model":"Likely model","growth_indicators":"Growth signals","operational_challenges":"3-5 challenges for {industry}","software_opportunities":"Using: {services}","conversation_topics":"3-5 topics","discovery_questions":"3-5 questions","business_risks":"2-3 risks"}}""",
        )

    def _proposal_full(self, ctx: str, context: dict[str, Any]) -> str:
        name = context.get("name", "Unknown")
        services = context.get("services", "Custom CRM, Client Portal")
        tier = context.get("pricing_tier", "Professional")
        return build_prompt(
            role=f"You are a senior proposal writer at Pacific North Systems. Write a proposal for {name}.",
            goal="Generate a complete proposal using only the provided CRM context.",
            context=ctx,
            output_format=f"""Respond with valid JSON only:
{{"executive_summary":"overview","current_situation":"assessment","business_challenges":"key challenges","proposed_solution":"using {services}","deliverables":["d1","d2"],"timeline":"estimate","expected_roi":"ROI narrative","investment_justification":"{tier} tier justification","next_steps":["step1","step2"]}}""",
        )


# ── Global instance ──

_enrichment_service: EnrichmentService | None = None


def get_enrichment_service() -> EnrichmentService:
    global _enrichment_service
    if _enrichment_service is None:
        import os
        api_key = os.getenv("DEEPSEEK_API_KEY", "")
        _enrichment_service = EnrichmentService(api_key=api_key)
    return _enrichment_service
