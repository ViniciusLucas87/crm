"""
Website Intelligence Provider.

Uses LLM to analyze a company's public website presence.
Produces normalized business data with full provenance tracking.
"""

import json
import logging
from typing import Any

from app.application.intelligence import IntelligenceProvider

logger = logging.getLogger(__name__)

WEBSITE_PROMPT = """You are a business intelligence researcher. Analyze this company's public website and online presence.

Company:
Name: {name}
City: {city}, {province}
Industry: {industry}
Website: {website}
Employees: {employees}

Using your knowledge, provide the most accurate website-related business information. If uncertain, leave fields null.

Respond with JSON only:
{{
  "phone_numbers": ["+1-xxx-xxx-xxxx"],
  "general_email": "info@...",
  "sales_email": "sales@...",
  "support_email": "support@...",
  "contact_page_url": "https://...",
  "website_title": "Company Name - Tagline",
  "about_page_url": "https://...",
  "services": ["Service 1", "Service 2"],
  "industries_served": ["Industry 1"],
  "office_locations": ["City, Province"],
  "leadership_page_url": "https://...",
  "careers_page_url": "https://...",
  "certifications": ["Cert 1"],
  "technology_references": ["Tech 1"],
  "portfolio_url": "https://...",
  "testimonials_present": true
}}"""


class WebsiteIntelligenceProvider(IntelligenceProvider):
    """Collects website business data via LLM research."""

    def __init__(self, api_key: str = "", model: str = "deepseek-chat") -> None:
        self._api_key = api_key
        self._model = model

    @property
    def provider_name(self) -> str:
        return "website"

    @property
    def stage_name(self) -> str:
        return "Website Intelligence"

    async def collect(self, company: dict[str, Any]) -> dict[str, Any]:
        from app.application.llm.gateway import get_llm_gateway, GatewayConfig
        from app.application.llm.provider import LLMMessage

        prompt = WEBSITE_PROMPT.format(
            name=company.get("name", ""),
            city=company.get("city", ""),
            province=company.get("province", ""),
            industry=company.get("industry", ""),
            website=company.get("website", "unknown"),
            employees=company.get("employees", "unknown"),
        )

        gateway = get_llm_gateway()
        gcfg = GatewayConfig(feature="enrichment", organization_id=company.get("organization_id", 1), temperature=0.2)
        messages = [
            LLMMessage(role="system", content="You are a business intelligence researcher. Return JSON only."),
            LLMMessage(role="user", content=prompt),
        ]
        resp = await gateway.chat(messages, gcfg)
        return self._parse_json(resp.content)

    def normalize(self, raw: dict[str, Any]) -> dict[str, Any]:
        return {
            "phone_numbers": raw.get("phone_numbers", []),
            "general_email": raw.get("general_email"),
            "sales_email": raw.get("sales_email"),
            "support_email": raw.get("support_email"),
            "contact_page_url": raw.get("contact_page_url"),
            "website_title": raw.get("website_title"),
            "about_page_url": raw.get("about_page_url"),
            "services": raw.get("services", []),
            "industries_served": raw.get("industries_served", []),
            "office_locations": raw.get("office_locations", []),
            "leadership_page_url": raw.get("leadership_page_url"),
            "careers_page_url": raw.get("careers_page_url"),
            "certifications": raw.get("certifications", []),
            "technology_references": raw.get("technology_references", []),
            "portfolio_url": raw.get("portfolio_url"),
            "testimonials_present": raw.get("testimonials_present"),
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
