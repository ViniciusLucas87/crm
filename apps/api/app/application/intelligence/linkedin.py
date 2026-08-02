"""
LinkedIn Intelligence Provider.

Uses LLM to research company leadership and organizational structure.
Produces normalized contact and org data with full provenance.
"""

import json
import logging
from typing import Any

from app.application.intelligence import IntelligenceProvider

logger = logging.getLogger(__name__)

LINKEDIN_PROMPT = """You are a business intelligence researcher analyzing a company's LinkedIn presence.

Company:
Name: {name}
City: {city}, {province}
Industry: {industry}
Employees: {employees}
Website: {website}

Using your knowledge of this business, provide the most accurate LinkedIn-related information. Focus on decision-makers and organizational structure. If uncertain, leave fields null.

Respond with JSON only:
{{
  "linkedin_url": "https://linkedin.com/company/...",
  "company_size_on_linkedin": "11-50",
  "employee_count_on_linkedin": 45,
  "headquarters": "City, Province",
  "company_description": "LinkedIn description",
  "specialties": ["Specialty 1"],
  "decision_makers": [
    {{"name": "John Smith", "role": "Owner", "confidence": 90, "likely_decision_maker": true}},
    {{"name": "Jane Doe", "role": "Operations Manager", "confidence": 75, "likely_decision_maker": true}}
  ],
  "departments": ["Operations", "Sales", "Field Service"],
  "growth_indicators": {{
    "hiring_now": true,
    "recent_hires_count": 5,
    "hiring_roles": ["Electrician", "Project Coordinator"],
    "new_office_locations": []
  }},
  "recommended_contact": {{
    "name": "John Smith",
    "role": "Owner",
    "confidence": 92,
    "reason": "Small business — owner typically handles software purchasing decisions directly."
  }}
}}"""


class LinkedInProvider(IntelligenceProvider):
    """Collects LinkedIn company and people data via LLM research."""

    def __init__(self, api_key: str = "", model: str = "deepseek-chat") -> None:
        self._api_key = api_key
        self._model = model

    @property
    def provider_name(self) -> str:
        return "linkedin"

    @property
    def stage_name(self) -> str:
        return "LinkedIn Intelligence"

    async def collect(self, company: dict[str, Any]) -> dict[str, Any]:
        from app.application.llm.gateway import get_llm_gateway, GatewayConfig
        from app.application.llm.provider import LLMMessage

        prompt = LINKEDIN_PROMPT.format(
            name=company.get("name", ""),
            city=company.get("city", ""),
            province=company.get("province", ""),
            industry=company.get("industry", ""),
            employees=company.get("employees", "unknown"),
            website=company.get("website", "unknown"),
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
            "linkedin_url": raw.get("linkedin_url"),
            "company_size_on_linkedin": raw.get("company_size_on_linkedin"),
            "employee_count_on_linkedin": raw.get("employee_count_on_linkedin"),
            "headquarters": raw.get("headquarters"),
            "company_description": raw.get("company_description"),
            "specialties": raw.get("specialties", []),
            "decision_makers": raw.get("decision_makers", []),
            "departments": raw.get("departments", []),
            "growth_indicators": raw.get("growth_indicators", {}),
            "recommended_contact": raw.get("recommended_contact", {}),
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
