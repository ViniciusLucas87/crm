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

from app.application.llm.provider import LLMConfig, LLMMessage
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
        # Kept for backwards-compatible construction only.  Credentials are
        # deliberately ignored: all requests must go through LLMGateway.
        self._configured = True

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

        try:
            from app.application.llm.gateway import FEATURE_OUTPUT_TOKENS, GatewayConfig, get_llm_gateway
            gateway = get_llm_gateway()
            messages = [
                LLMMessage(role="system", content=ENRICHMENT_SYSTEM_PROMPT),
                LLMMessage(role="user", content=prompt),
            ]
            gcfg = GatewayConfig(
                feature="enrichment", organization_id=context.get("_org_id", 1),
                temperature=0.3, max_tokens=FEATURE_OUTPUT_TOKENS.get("enrichment", 600),
            )
            resp = await gateway.chat(messages, gcfg)
            result = EnrichmentResult(
                enriched=resp.model not in ("disabled", "redis_unavailable", "budget_blocked", "error", "lock_timeout"),
                content=resp.content,
                model_used=resp.model,
            )
        except Exception as e:
            result = EnrichmentResult(enriched=False, content="", model_used=None)

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
            "outreach": self._outreach(ctx),
        }
        if enrichment_type in prompts:
            return prompts[enrichment_type]
        if enrichment_type in {
            "website_analysis", "business_analysis", "industry_detection",
            "technology_detection", "buying_signals", "decision_makers",
            "operational_challenges", "opportunity_analysis",
            "recommended_services", "opportunity_scoring", "confidence_scoring",
        }:
            return self._research_stage(enrichment_type, ctx)
        return ""

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

    def _research_stage(self, stage: str, ctx: str) -> str:
        instructions = {
            "website_analysis": "Summarize verified website evidence, including services, contact channels, operational clues, and explicit source URLs.",
            "business_analysis": "Summarize the business model, customers, likely workflows, and clearly separate facts from inferences.",
            "industry_detection": "Identify the most specific supported industry and explain the evidence.",
            "technology_detection": "Identify only technologies or digital-process clues supported by the supplied evidence.",
            "buying_signals": "List concrete buying signals, their evidence, strength, and why they matter to PNS.",
            "decision_makers": "Return JSON with a decision_makers array. Each item must contain name, role, email, phone, source_url, confidence, and evidence. Use null when unknown.",
            "operational_challenges": "List likely operational challenges, marking each as verified or inferred and citing the supporting evidence.",
            "opportunity_analysis": "Assess PNS fit, entry project, expected value, sales difficulty, risks, and next best action.",
            "recommended_services": "Recommend at most three PNS services, each tied to a specific supported pain point.",
            "opportunity_scoring": "Return JSON with opportunity_score from 0-100 and a concise evidence-based rationale.",
            "confidence_scoring": "Return JSON with confidence_score from 0-100, missing evidence, and the next research action.",
        }
        return f"""Lead research stage: {stage}

CRM and website evidence:
{ctx}

Task: {instructions[stage]}
Do not claim that a website was read unless website_evidence is present. Preserve source URLs. Do not invent people, emails, phone numbers, technologies, or business facts.
{ANTI_HALLUCINATION_FOOTER}"""

    def _outreach(self, ctx: str) -> str:
        return f"""Create a personalized, evidence-based first-touch outreach package for Pacific North Systems.

Lead context:
{ctx}

Respond with valid JSON only using exactly these keys:
{{"primary_contact":null,"recommended_strategy":"","cold_email":"","linkedin_message":"","cold_call_script":"","discovery_questions":[],"pain_points":[],"recommended_services":"","potential_objections":[],"suggested_responses":[],"recommended_next_action":""}}

Requirements:
- Reference only facts supported by the supplied research.
- Cold email must be under 120 words, plain language, and use one low-friction question.
- Cold call opening must be under 30 seconds, then ask a discovery question.
- If no named contact is verified, use the best supported role without inventing a name.
- Never fabricate customer results, savings percentages, or social proof.
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
        _enrichment_service = EnrichmentService()
    return _enrichment_service
