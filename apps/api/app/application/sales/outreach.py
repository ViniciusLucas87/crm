"""
Outreach Generator.

Generates AI-powered outreach content for approved leads:
- Cold email
- LinkedIn message
- Cold call script
- Discovery questions
- Pain points + solutions
- Objection handling
- Recommended next action
"""

import json
from typing import Any

from app.application.llm.enrichment import EnrichmentService
from app.infrastructure.db.models import Lead


class OutreachGenerator:
    """Generates multi-channel outreach content for qualified leads."""

    def __init__(self, enrichment: EnrichmentService | None = None) -> None:
        self._enrichment = enrichment

    async def generate(self, lead: Lead) -> dict[str, Any]:
        """Generate full outreach package for a lead."""
        context = self._lead_context(lead)

        outreach: dict[str, Any] = {
            "primary_contact": None,
            "recommended_strategy": "Research-based consultative approach",
            "cold_email": "",
            "linkedin_message": "",
            "cold_call_script": "",
            "discovery_questions": [],
            "pain_points": [],
            "recommended_services": lead.recommended_services or "",
            "potential_objections": [],
            "suggested_responses": [],
            "recommended_next_action": "Send personalized cold email introducing Pacific North Systems' services.",
        }

        if self._enrichment and self._enrichment.available:
            result = await self._enrichment.enrich("outreach", context)
            if result.enriched:
                try:
                    parsed = json.loads(result.content)
                    outreach.update({k: v for k, v in parsed.items() if k in outreach})
                except (json.JSONDecodeError, TypeError):
                    outreach["cold_email"] = result.content
        else:
            outreach.update(self._fallback_outreach(lead))

        return outreach

    def generate_sync(self, lead: Lead) -> dict[str, Any]:
        """Synchronous fallback generation."""
        context = self._lead_context(lead)

        if self._enrichment and self._enrichment.available:
            result = self._enrichment.enrich_sync("outreach", context)
            if result.enriched:
                try:
                    parsed = json.loads(result.content)
                    base = self._fallback_outreach(lead)
                    base.update({k: v for k, v in parsed.items() if k in base})
                    return base
                except (json.JSONDecodeError, TypeError):
                    pass

        return self._fallback_outreach(lead)

    def _lead_context(self, lead: Lead) -> dict[str, Any]:
        return {
            "name": lead.name,
            "industry": lead.industry or "",
            "website": lead.website or "",
            "city": lead.city or "",
            "employees": lead.employees,
            "description": lead.description or "",
            "opportunity_score": lead.opportunity_score,
            "buying_signals": lead.buying_signals or "",
            "executive_summary": lead.executive_summary or "",
        }

    def _fallback_outreach(self, lead: Lead) -> dict[str, Any]:
        ind = lead.industry or "your industry"
        name = lead.name
        city = lead.city or "your area"

        return {
            "primary_contact": "Decision maker (to be identified)",
            "recommended_strategy": "Research-based consultative approach — reference industry trends and operational challenges.",
            "cold_email": (
                f"Subject: Streamlining operations at {name}\n\n"
                f"Hi [First Name],\n\n"
                f"I've been researching {name} and noticed the impressive work you're doing in {ind}. "
                f"Companies in {ind} often face challenges with [operational inefficiency / manual processes / scaling technology].\n\n"
                f"Pacific North Systems specializes in custom software solutions that help {ind} companies "
                f"[automate workflows / modernize operations / improve efficiency]. "
                f"We've helped similar organizations reduce operational overhead by 30-40%.\n\n"
                f"Would you be open to a brief conversation about how we might support {name}'s growth?\n\n"
                f"Best regards,\n[Your Name]"
            ),
            "linkedin_message": (
                f"Hi [First Name], I came across {name} and was impressed by your work in {ind}. "
                f"I specialize in custom software for {ind} companies — would you be open to connecting?"
            ),
            "cold_call_script": (
                f"Hi [First Name], this is [Your Name] from Pacific North Systems. "
                f"I'm reaching out because we specialize in custom software for {ind} companies like {name}. "
                f"We've helped similar organizations [reduce costs / improve efficiency / modernize operations]. "
                f"Do you have a few minutes to discuss whether this might be relevant for {name}?"
            ),
            "discovery_questions": [
                f"How do you currently manage [core operations] at {name}?",
                "What are the biggest operational challenges you're facing?",
                "Are there any manual processes you'd like to automate?",
                "What technology investments are you considering in the next 12 months?",
                "Who else is involved in technology purchasing decisions?",
            ],
            "pain_points": [
                "Manual operational processes limiting growth",
                "Lack of integrated technology platform",
                "Difficulty scaling with current tools",
                "Data silos between departments",
            ],
            "potential_objections": [
                "We're not looking for new technology right now",
                "We already have a technology partner",
                "Budget constraints",
                "We're too small for custom software",
            ],
            "suggested_responses": [
                "Many of our clients said the same thing before seeing how much time they could save. Would a 15-minute demo be worthwhile?",
                "We often complement existing technology partners by filling specialized gaps.",
                "Our solutions typically pay for themselves within 6-12 months through efficiency gains.",
                "We work with companies of all sizes — our solutions scale with you.",
            ],
            "recommended_next_action": f"Send personalized outreach email to {name}'s decision maker within 48 hours.",
        }
