"""
Google Maps Intelligence Provider.

Uses LLM (DeepSeek) to research a company's Google Maps presence.
Produces normalized business data with full provenance tracking.

This is Stage 3 in the Intelligence Pipeline (after AI Research).
"""

import json
import logging
from typing import Any

from app.application.intelligence import IntelligenceProvider

logger = logging.getLogger(__name__)

# ── Prompt for Google Maps data collection ──

GOOGLE_MAPS_PROMPT = """You are a business intelligence researcher. Your job is to find the Google Maps / Google Business Profile information for a specific company.

Company to research:
Name: {name}
City: {city}, {province}
Industry: {industry}
Website: {website}
Employees: {employees}
Description: {description}

Using your knowledge of this business, provide the most accurate Google Maps / Google Business Profile data you can. If you are uncertain about a field, leave it null. Do not invent fake data — only provide information you are reasonably confident about.

Respond with JSON only:
{{
  "google_place_id": "ChI... (if known, otherwise null)",
  "google_maps_url": "https://maps.google.com/?cid=... (if known, otherwise null)",
  "primary_category": "e.g., Electrical Contractor, HVAC Contractor",
  "secondary_categories": ["category 1", "category 2"],
  "rating": 4.3,
  "review_count": 47,
  "business_status": "OPERATIONAL",
  "formatted_address": "full address if known",
  "formatted_phone_number": "+1-xxx-xxx-xxxx if known",
  "website": "confirmed website URL",
  "opening_hours": {{
    "monday": "8:00 AM – 5:00 PM",
    "tuesday": "8:00 AM – 5:00 PM",
    "wednesday": "8:00 AM – 5:00 PM",
    "thursday": "8:00 AM – 5:00 PM",
    "friday": "8:00 AM – 5:00 PM",
    "saturday": "Closed",
    "sunday": "Closed"
  }},
  "latitude": 49.2827,
  "longitude": -123.1207,
  "service_area": "Metro Vancouver and surrounding areas (if applicable)",
  "business_description": "Brief Google Maps description of the business",
  "photos_count": 12
}}

Return ONLY valid JSON. No markdown, no explanation."""


class GoogleMapsProvider(IntelligenceProvider):
    """Collects Google Maps business profile data via LLM research.

    This provider uses the LLM's knowledge of real businesses to produce
    structured Google Maps data. In production, this would be replaced
    with actual Google Places API calls — the interface contract remains identical.
    """

    def __init__(self, api_key: str = "", model: str = "deepseek-chat") -> None:
        self._api_key = api_key
        self._model = model

    @property
    def provider_name(self) -> str:
        return "google_maps"

    @property
    def stage_name(self) -> str:
        return "Google Maps Intelligence"

    async def collect(self, company: dict[str, Any]) -> dict[str, Any]:
        """Query LLM for Google Maps business profile data."""
        from app.application.llm.provider import LLMConfig, LLMMessage, create_provider

        prompt = GOOGLE_MAPS_PROMPT.format(
            name=company.get("name", ""),
            city=company.get("city", ""),
            province=company.get("province", ""),
            industry=company.get("industry", ""),
            website=company.get("website", "unknown"),
            employees=company.get("employees", "unknown"),
            description=company.get("description", "unknown"),
        )

        llm = create_provider(
            LLMConfig(
                provider="openai",
                model=self._model,
                api_key=self._api_key,
                api_base="https://api.deepseek.com/v1",
                temperature=0.2,
                max_tokens=1024,
            )
        )

        messages = [
            LLMMessage(
                role="system",
                content="You are a business intelligence researcher. Return JSON only.",
            ),
            LLMMessage(role="user", content=prompt),
        ]

        response = await llm.chat(messages)
        return self._parse_json(response.content)

    def normalize(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """Transform LLM response into provider-independent schema."""
        return {
            "place_id": raw_data.get("google_place_id"),
            "maps_url": raw_data.get("google_maps_url"),
            "primary_category": raw_data.get("primary_category"),
            "secondary_categories": raw_data.get("secondary_categories", []),
            "rating": raw_data.get("rating"),
            "review_count": raw_data.get("review_count"),
            "business_status": raw_data.get("business_status", "OPERATIONAL"),
            "formatted_address": raw_data.get("formatted_address"),
            "formatted_phone_number": raw_data.get("formatted_phone_number"),
            "website": raw_data.get("website"),
            "opening_hours": raw_data.get("opening_hours", {}),
            "latitude": raw_data.get("latitude"),
            "longitude": raw_data.get("longitude"),
            "service_area": raw_data.get("service_area"),
            "business_description": raw_data.get("business_description"),
            "photos_count": raw_data.get("photos_count"),
        }

    def validate(self, data: dict[str, Any]) -> list[str]:
        """Validate that essential normalized fields are present."""
        errors = []
        if not data.get("primary_category"):
            errors.append("Missing primary_category")
        if not data.get("formatted_address"):
            errors.append("Missing formatted_address")
        return errors

    def _parse_json(self, content: str) -> dict:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            return json.loads(content)
