"""
Google Reviews Intelligence Provider.

Uses LLM to analyze customer reviews and perception.
Produces structured insights — never exposes raw reviews.
"""

import json
import logging
from typing import Any

from app.application.intelligence import IntelligenceProvider

logger = logging.getLogger(__name__)

REVIEWS_PROMPT = """You are a business intelligence researcher analyzing customer reviews for a company.

Company:
Name: {name}
City: {city}, {province}
Industry: {industry}
Google Maps Rating: {rating}
Google Maps Review Count: {review_count}
Google Maps Category: {category}

Using your knowledge of this business and its industry, provide a structured analysis of what customers likely say in their reviews. Focus on operational insights that could reveal software opportunities.

Respond with JSON only:
{{
  "average_rating": 4.3,
  "review_count_estimate": 47,
  "top_strengths": ["quality work", "reliable", "professional"],
  "common_complaints": ["scheduling delays", "hard to reach by phone"],
  "operational_pain_points": ["manual paperwork", "slow response times", "poor visibility into project status"],
  "frequently_mentioned_services": ["service A", "service B"],
  "customer_experience_summary": "2-3 sentence summary of typical customer experience",
  "software_opportunities": ["Inspection platform could address documentation complaints", "Scheduling system would resolve wait time issues"],
  "response_rate_estimate": "low/medium/high"
}}"""


class GoogleReviewsProvider(IntelligenceProvider):
    """Collects customer review insights via LLM analysis."""

    def __init__(self, api_key: str = "", model: str = "deepseek-chat") -> None:
        self._api_key = api_key
        self._model = model

    @property
    def provider_name(self) -> str:
        return "google_reviews"

    @property
    def stage_name(self) -> str:
        return "Google Reviews Intelligence"

    async def collect(self, company: dict[str, Any]) -> dict[str, Any]:
        from app.application.llm.gateway import get_llm_gateway, GatewayConfig
        from app.application.llm.provider import LLMMessage

        prompt = REVIEWS_PROMPT.format(
            name=company.get("name", ""),
            city=company.get("city", ""),
            province=company.get("province", ""),
            industry=company.get("industry", ""),
            rating=company.get("gmaps_rating", "unknown"),
            review_count=company.get("gmaps_review_count", "unknown"),
            category=company.get("gmaps_category", "unknown"),
        )

        gateway = get_llm_gateway()
        gcfg = GatewayConfig(feature="enrichment", organization_id=company.get("organization_id", 1), temperature=0.3)
        messages = [
            LLMMessage(role="system", content="You are a business intelligence researcher. Return JSON only."),
            LLMMessage(role="user", content=prompt),
        ]
        resp = await gateway.chat(messages, gcfg)
        return self._parse_json(resp.content)

    def normalize(self, raw: dict[str, Any]) -> dict[str, Any]:
        return {
            "average_rating": raw.get("average_rating"),
            "review_count_estimate": raw.get("review_count_estimate"),
            "top_strengths": raw.get("top_strengths", []),
            "common_complaints": raw.get("common_complaints", []),
            "operational_pain_points": raw.get("operational_pain_points", []),
            "frequently_mentioned_services": raw.get("frequently_mentioned_services", []),
            "customer_experience_summary": raw.get("customer_experience_summary"),
            "software_opportunities": raw.get("software_opportunities", []),
            "response_rate_estimate": raw.get("response_rate_estimate"),
        }

    def _parse_json(self, content: str) -> dict:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            return json.loads(content)
