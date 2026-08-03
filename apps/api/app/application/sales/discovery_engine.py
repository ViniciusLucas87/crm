"""
AI Prospect Discovery Engine.

Provider-abstraction architecture for discovering companies.

DiscoveryProvider (abstract)
  └── LLMDiscoveryProvider (DeepSeek — current default)
  └── [future] GoogleMapsProvider
  └── [future] ClearbitProvider
  └── [future] LinkedInEnrichmentProvider

The engine:
  1. Accepts search criteria from the user
  2. Uses a DiscoveryProvider to find matching companies
  3. Creates Lead records with AI-generated research
  4. Deduplicates against existing leads and CRM companies
  5. Returns enriched leads ready for review
"""

import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.application.llm.provider import LLMMessage
from app.infrastructure.db.models import Company, Lead, LeadTimelineEvent

logger = logging.getLogger(__name__)


# ── Data Types ──

@dataclass
class DiscoveredCompany:
    name: str
    industry: str = ""
    city: str = ""
    province: str = ""
    country: str = ""
    website: str = ""
    employees: int | None = None
    description: str = ""
    executive_summary: str = ""
    opportunity_score: int = 50
    confidence_score: int = 60
    buying_signals: str = ""
    recommended_services: str = ""
    estimated_deal_low: int | None = None
    estimated_deal_high: int | None = None
    technology_maturity: str = ""
    decision_makers_data: str = ""
    revenue_estimate: str = ""
    linkedin_url: str = ""
    explainability: str = ""  # JSON
    pns_fit_data: str = ""  # JSON: pns_fit_analysis + outreach_strategy
    pns_fit_score: int = 50  # PNS ICP fit score


@dataclass
class DiscoveryCriteria:
    industry: str = ""
    city: str = ""
    province: str = ""
    country: str = ""
    min_employees: int | None = None
    max_employees: int | None = None
    keyword: str = ""
    business_type: str = ""
    count: int = 5
    organization_id: int = 1
    excluded_names: list[str] = field(default_factory=list)


@dataclass
class DiscoveryResult:
    criteria: DiscoveryCriteria
    companies: list[DiscoveredCompany] = field(default_factory=list)
    leads_created: int = 0
    duplicates_skipped: int = 0
    total_time_ms: int = 0
    stage: str = "complete"  # "searching", "researching", "complete", "error"
    progress_pct: int = 100
    message: str = ""


# ── Provider Abstraction ──

class DiscoveryProvider(ABC):
    """Abstract provider for company discovery.

    Future providers (Google Maps, Clearbit, etc.) implement this interface.
    """

    @abstractmethod
    async def discover(self, criteria: DiscoveryCriteria) -> list[DiscoveredCompany]:
        """Find companies matching the given criteria."""
        ...

    @abstractmethod
    async def enrich(self, company: DiscoveredCompany) -> DiscoveredCompany:
        """Enrich a company with AI research."""
        ...


# ── LLM Discovery Provider ──

DISCOVERY_SYSTEM_PROMPT = """You are an expert sales researcher for Pacific North Systems, a custom software development company.

Your job is to discover REAL companies that match the user's search criteria.
Return ONLY real, verifiable businesses. Do not invent fictional companies.

For each company provide:
- Name (the actual registered business name)
- Industry (specific subcategory)
- City and Province/State
- A realistic employee count estimate
- A brief business description (1-2 sentences about what they actually do)
- What operational challenges they likely face
- What Pacific North Systems services would help them
- An opportunity score (0-100) based on how likely they need custom software
- Estimated deal value range (in USD)

Focus on companies that would genuinely benefit from custom software: field service platforms, workflow automation, inspection applications, document management, client portals, etc.

Respond with valid JSON only: {"companies": [{"name": "...", "industry": "...", ...}]}"""


class LLMDiscoveryProvider(DiscoveryProvider):
    """Uses an LLM (DeepSeek) to discover and research companies."""

    def __init__(self, api_key: str = "", model: str = "deepseek-chat") -> None:
        self._api_key = api_key
        self._model = model
        self._configured = bool(api_key)

    @property
    def available(self) -> bool:
        return self._configured

    async def discover(self, criteria: DiscoveryCriteria) -> list[DiscoveredCompany]:
        if not self._configured:
            return self._fallback_discover(criteria)

        parts = []
        if criteria.industry:
            parts.append(f"Industry: {criteria.industry}")
        if criteria.city:
            parts.append(f"City: {criteria.city}")
        if criteria.province:
            parts.append(f"Province/State: {criteria.province}")
        if criteria.min_employees and criteria.max_employees:
            parts.append(f"Employees: {criteria.min_employees}-{criteria.max_employees}")
        elif criteria.min_employees:
            parts.append(f"Minimum employees: {criteria.min_employees}")
        if criteria.keyword:
            parts.append(f"Keywords: {criteria.keyword}")

        query = "Find exactly " + (f"{criteria.count} " if criteria.count else "5 ")
        query += "real companies matching: " + "; ".join(parts) if parts else "companies in the Pacific Northwest"
        query += ". Return JSON with company name, industry, city, province, employees, website, and description."
        if criteria.excluded_names:
            query += " Do not return any of these companies already in our CRM: " + "; ".join(criteria.excluded_names[:100]) + "."
        query += f" The companies array must contain {criteria.count or 5} distinct, non-empty results."

        try:
            from app.application.llm.gateway import get_llm_gateway, GatewayConfig
            gateway = get_llm_gateway()
            gcfg = GatewayConfig(
                feature="discovery",
                organization_id=criteria.organization_id,
                temperature=0.55,
                max_tokens=1200,
                bypass_cache=True,
            )
            messages = [
                LLMMessage(role="system", content=DISCOVERY_SYSTEM_PROMPT),
                LLMMessage(role="user", content=query),
            ]
            resp = await gateway.chat(messages, gcfg)

            if resp.model in {"disabled", "redis_unavailable", "budget_blocked", "error", "lock_timeout"}:
                logger.warning("LLM discovery unavailable: %s", resp.model)
                return []

            companies = self._parse_companies(resp.content)
            return companies[: criteria.count or 5]
        except Exception as e:
            logger.exception("LLM discovery failed: %s", e)
            return self._fallback_discover(criteria)

    async def enrich(self, company: DiscoveredCompany) -> DiscoveredCompany:
        if not self._configured:
            company.executive_summary = self._fallback_summary(company)
            return company

        prompt = f"""You are the AI Business Development Director for Pacific North Systems, a founder-led custom software company in Vancouver BC.

PNS Profile: custom software, AI automation, workflow automation, inspection software, dashboards, internal tools, reporting, document AI, CRM, integrations, IT consulting/support.
Business Stage: founder-led, relationship-first, direct sales. Goal: land smaller projects ($3K-$20K), expand into larger ($20K-$100K+), build long-term partnerships.
ICP: 10-150 employees, owner/founder accessible, manual processes (Excel/paper/email/WhatsApp), construction/property/HVAC/electrical/restoration/manufacturing/engineering/marine/field service, Metro Vancouver.

Company to evaluate:
Name: {company.name}
Industry: {company.industry}
City: {company.city}, {company.province}
Employees: {company.employees or 'unknown'}
Description: {company.description or 'unknown'}

Act as Pacific North Systems' founder. Think about: would I spend MY limited time pursuing this company? Respond with JSON only:

{{
  "executive_summary": "2-3 sentence briefing",
  "buying_signals": "signals detected",
  "recommended_services": "relevant PNS services",
  "technology_maturity": "low/medium/high",
  "estimated_deal_low": 0,
  "estimated_deal_high": 0,
  "opportunity_score": 0,
  "confidence_score": 0,
  "revenue_estimate": "range",

  "founder_recommendation": "YES/LATER/NO",
  "founder_advice": "If I were running PNS today, here is exactly what I would do and why...",
  "pursue_rationale": "why this recommendation",

  "pns_fit_score": 0,
  "fit_factors": [
    {{"factor": "Company size", "score": 0, "max": 25, "rationale": "why"}},
    {{"factor": "Industry match", "score": 0, "max": 20, "rationale": "why"}},
    {{"factor": "Geographic proximity", "score": 0, "max": 15, "rationale": "why"}},
    {{"factor": "Manual processes / tech gap", "score": 0, "max": 15, "rationale": "why"}},
    {{"factor": "Decision accessibility", "score": 0, "max": 15, "rationale": "why"}},
    {{"factor": "First project fit", "score": 0, "max": 10, "rationale": "why"}}
  ],

  "sales_difficulty": "very_easy/easy/moderate/difficult/enterprise",
  "estimated_sales_cycle": "2 weeks/1 month/3 months/6 months/12+ months",
  "sales_difficulty_rationale": "why",

  "first_project": {{
    "name": "Inspection Platform/Workflow Automation/etc.",
    "rationale": "why this is the best entry point",
    "estimated_value": 0,
    "timeline": "4-6 weeks",
    "chance_of_success": 0,
    "expansion_potential": "high/medium/low"
  }},

  "return_on_founder_time": {{
    "estimated_hours": 0,
    "expected_value": 0,
    "hourly_return": 0,
    "comparison": "vs average opportunity"
  }},

  "next_best_action": "Call Owner/Send LinkedIn/Visit Office/Research More/Wait/Reject",
  "next_action_rationale": "why this action",

  "why_pns": ["reason 1", "reason 2"],
  "risk_factors": ["risk 1 if any"],

  "outreach_strategy": {{
    "decision_maker": "title",
    "channel": "email/phone/LinkedIn",
    "opening_message": "personalized opening",
    "discovery_questions": ["q1", "q2"],
    "likely_objections": ["obj1"],
    "objection_responses": ["resp1"]
  }},

  "market_intelligence": {{
    "market_maturity": "emerging/growing/mature",
    "digital_maturity": "low/medium/high",
    "common_pain_points": ["point 1"],
    "addressable_market_estimate": "description"
  }}
}}"""

        try:
            from app.application.llm.gateway import get_llm_gateway, GatewayConfig
            gateway = get_llm_gateway()
            gcfg = GatewayConfig(feature="enrichment", organization_id=1, temperature=0.3, max_tokens=1536)
            messages = [
                LLMMessage(role="system", content="You are an expert B2B sales researcher. Return JSON only. Explain every score and recommendation."),
                LLMMessage(role="user", content=prompt),
            ]
            resp = await gateway.chat(messages, gcfg)

            data = self._parse_json(resp.content)

            company.executive_summary = data.get("executive_summary", "") or self._fallback_summary(company)
            company.buying_signals = data.get("buying_signals", "") or ""
            company.recommended_services = data.get("recommended_services", "") or ""
            company.technology_maturity = data.get("technology_maturity", "") or "medium"
            company.estimated_deal_low = data.get("estimated_deal_low")
            company.estimated_deal_high = data.get("estimated_deal_high")
            company.opportunity_score = data.get("opportunity_score", 50)
            company.confidence_score = data.get("confidence_score", 60)
            company.revenue_estimate = data.get("revenue_estimate", "") or ""

            # Store all enrichment data as combined JSON
            company.explainability = json.dumps({
                "score_breakdown": data.get("score_breakdown", data.get("fit_factors", [])),
                "confidence_factors": data.get("confidence_factors", []),
                "signal_evidence": data.get("signal_evidence", []),
                "service_reasoning": data.get("service_reasoning", []),
            })

            # Store PNS fit data with founder mode fields
            company.pns_fit_data = json.dumps({
                "founder_recommendation": data.get("founder_recommendation", "LATER"),
                "founder_advice": data.get("founder_advice", ""),
                "pursue_rationale": data.get("pursue_rationale", ""),
                "pns_fit_score": data.get("pns_fit_score", 50),
                "fit_factors": data.get("fit_factors", []),
                "sales_difficulty": data.get("sales_difficulty", "moderate"),
                "estimated_sales_cycle": data.get("estimated_sales_cycle", "3 months"),
                "sales_difficulty_rationale": data.get("sales_difficulty_rationale", ""),
                "first_project": data.get("first_project", {}),
                "return_on_founder_time": data.get("return_on_founder_time", {}),
                "next_best_action": data.get("next_best_action", ""),
                "next_action_rationale": data.get("next_action_rationale", ""),
                "why_pns": data.get("why_pns", []),
                "risk_factors": data.get("risk_factors", []),
                "outreach_strategy": data.get("outreach_strategy", {}),
                "market_intelligence": data.get("market_intelligence", {}),
            })
            company.pns_fit_score = data.get("pns_fit_score", 50)

        except Exception as e:
            logger.exception("LLM enrich failed for %s: %s", company.name, e)
            company.executive_summary = self._fallback_summary(company)

        return company

    def _parse_json(self, content: str) -> dict:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            return json.loads(content)
            company.estimated_deal_high = data.get("estimated_deal_high")
            company.opportunity_score = data.get("opportunity_score", 50)
            company.confidence_score = data.get("confidence_score", 60)
            company.revenue_estimate = data.get("revenue_estimate", "") or ""

        except Exception as e:
            logger.exception("LLM enrich failed for %s: %s", company.name, e)
            company.executive_summary = self._fallback_summary(company)

        return company

    def _parse_companies(self, content: str) -> list[DiscoveredCompany]:
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            data = json.loads(content)

        companies_raw = data.get("companies", data if isinstance(data, list) else [data])
        if not isinstance(companies_raw, list):
            companies_raw = [companies_raw]

        result: list[DiscoveredCompany] = []
        for c in companies_raw:
            if not isinstance(c, dict):
                continue
            name = str(c.get("name", "")).strip()
            if not name:
                continue
            result.append(DiscoveredCompany(
                name=name,
                industry=str(c.get("industry", "")).strip(),
                city=str(c.get("city", "")).strip(),
                province=str(c.get("province", c.get("state", ""))).strip(),
                country=str(c.get("country", "")).strip(),
                website=str(c.get("website", "")).strip(),
                employees=c.get("employees"),
                description=str(c.get("description", "")).strip(),
                opportunity_score=int(c.get("opportunity_score", c.get("score", 50))),
                confidence_score=int(c.get("confidence_score", c.get("confidence", 60))),
                buying_signals=str(c.get("buying_signals", "")).strip(),
                recommended_services=str(c.get("recommended_services", "")).strip(),
                estimated_deal_low=c.get("estimated_deal_low"),
                estimated_deal_high=c.get("estimated_deal_high"),
                technology_maturity=str(c.get("technology_maturity", "")).strip(),
                revenue_estimate=str(c.get("revenue_estimate", "")).strip(),
            ))
        return result

    def _fallback_discover(self, criteria: DiscoveryCriteria) -> list[DiscoveredCompany]:
        """Return empty when LLM is unavailable — provider will be plugged in later."""
        return []

    def _fallback_summary(self, company: DiscoveredCompany) -> str:
        ind = company.industry or "its industry"
        city = company.city or "its region"
        emp = f"approximately {company.employees} employees" if company.employees else "an unknown number of employees"
        return (
            f"{company.name} operates in {ind} based in {city} with {emp}. "
            f"The company likely faces operational challenges common to {ind} businesses, "
            f"including manual workflow coordination, limited technology infrastructure, "
            f"and opportunity for process automation. "
            f"Pacific North Systems could support {company.name} with custom software "
            f"solutions tailored to their specific operational needs."
        )


# ── Discovery Engine ──

class DiscoveryEngine:
    """Orchestrates the AI discovery → lead creation → background enrichment pipeline."""

    def __init__(self, session: Session, provider: DiscoveryProvider) -> None:
        self._session = session
        self._provider = provider

    async def discover(
        self, organization_id: int, criteria: DiscoveryCriteria
    ) -> DiscoveryResult:
        """Discover companies, create leads immediately, queue background enrichment."""
        start = time.time()
        result = DiscoveryResult(criteria=criteria)

        # Stage 1: Discover companies (fast — no enrichment)
        result.stage = "searching"
        result.progress_pct = 20
        criteria.organization_id = organization_id
        criteria.excluded_names = self._existing_company_names(organization_id)
        companies = await self._provider.discover(criteria)
        if not companies:
            result.stage = "complete"
            result.message = "No companies found. Try different search criteria."
            result.total_time_ms = int((time.time() - start) * 1000)
            return result

        result.stage = "creating"
        result.progress_pct = 30

        # Stage 2: Create leads immediately + queue background enrichment
        from app.application.sales.task_dispatcher import queue_enrichment
        from app.infrastructure.db.models import EnrichmentJob

        total = len(companies)
        for i, company in enumerate(companies):
            # Dedup check
            if self._is_duplicate(organization_id, company.name, company.website):
                result.duplicates_skipped += 1
                continue

            # Create lead immediately (no enrichment — just discovery data)
            lead = self._create_lead_fast(organization_id, company)

            # Create enrichment job record
            job_id = queue_enrichment(
                lead_id=lead.id,
                organization_id=organization_id,
                company_name=company.name,
                industry=company.industry or "",
                city=company.city or "",
                province=company.province or "",
                employees=company.employees,
                description=company.description or "",
            )
            self._session.add(EnrichmentJob(
                id=job_id, organization_id=organization_id, lead_id=lead.id,
                discovery_source="ai_discovery", status="queued", priority=0,
            ))
            self._session.commit()

            result.companies.append(company)
            result.leads_created += 1
            result.progress_pct = 30 + int((i + 1) / total * 70)

        result.stage = "complete"
        result.progress_pct = 100
        result.message = (
            f"Discovered {len(companies)} companies. "
            f"Created {result.leads_created} leads. "
            f"Skipped {result.duplicates_skipped} duplicates. "
            f"AI enrichment running in background."
        )
        result.total_time_ms = int((time.time() - start) * 1000)

        return result

    def _existing_company_names(self, org_id: int) -> list[str]:
        """Names to exclude so repeated discovery searches produce new prospects."""
        lead_names = self._session.execute(
            select(Lead.name).where(Lead.organization_id == org_id).limit(100)
        ).scalars().all()
        company_names = self._session.execute(
            select(Company.name).where(
                Company.organization_id == org_id,
                Company.is_archived.is_(False),
            ).limit(100)
        ).scalars().all()
        return sorted({str(name).strip() for name in [*lead_names, *company_names] if name and str(name).strip()})

    def _create_lead_fast(self, org_id: int, company: DiscoveredCompany) -> Lead:
        """Create a lead immediately with discovery data only — enrichment comes later."""
        lead = Lead(
            organization_id=org_id,
            name=company.name,
            industry=company.industry or None,
            website=company.website or None,
            employees=company.employees,
            city=company.city or None,
            province=company.province or None,
            country=company.country or None,
            description=company.description or None,
            revenue_estimate=company.revenue_estimate or None,
            opportunity_score=company.opportunity_score,
            confidence_score=company.confidence_score,
            status="new",
            source="ai_discovery",
            enrichment_status="pending",
        )
        self._session.add(lead)
        self._session.commit()
        self._session.refresh(lead)

        # Timeline event
        self._session.add(LeadTimelineEvent(
            organization_id=org_id, lead_id=lead.id,
            event_type="ai_discovered",
            description=f"Discovered by AI Prospect Discovery Engine. Enrichment queued.",
            metadata_json=json.dumps({
                "opportunity_score": company.opportunity_score,
                "industry": company.industry,
                "city": company.city,
            }),
        ))
        self._session.commit()
        return lead

    def _is_duplicate(self, org_id: int, name: str, website: str) -> bool:
        # Check existing leads
        lead_exists = self._session.execute(
            select(func.count(Lead.id)).where(
                Lead.organization_id == org_id,
                Lead.name.ilike(name),
            )
        ).scalar_one()
        if lead_exists:
            return True

        # Check CRM companies
        if website:
            crm_exists = self._session.execute(
                select(func.count(Company.id)).where(
                    Company.organization_id == org_id,
                    Company.is_archived.is_(False),
                    or_(Company.name.ilike(name), Company.website == website),
                )
            ).scalar_one()
            if crm_exists:
                return True

        return False

    def _create_lead(self, org_id: int, company: DiscoveredCompany) -> None:
        lead = Lead(
            organization_id=org_id,
            name=company.name,
            industry=company.industry or None,
            website=company.website or None,
            employees=company.employees,
            city=company.city or None,
            province=company.province or None,
            country=company.country or None,
            description=company.description or None,
            revenue_estimate=company.revenue_estimate or None,
            opportunity_score=company.opportunity_score,
            confidence_score=company.confidence_score,
            buying_signals=company.buying_signals or None,
            recommended_services=company.recommended_services or None,
            executive_summary=company.executive_summary or None,
            estimated_deal_low=company.estimated_deal_low,
            estimated_deal_high=company.estimated_deal_high,
            technology_maturity=company.technology_maturity or None,
            linkedin_url=company.linkedin_url or None,
            research_data=company.explainability or None,  # explainability JSON
            pns_fit_score=company.pns_fit_score,
            pns_fit_data=company.pns_fit_data or None,
            status="ready_for_review",
            source="ai_discovery",
            last_researched_at=datetime.now(UTC),
        )
        self._session.add(lead)
        self._session.commit()
        self._session.refresh(lead)

        # Timeline event
        self._session.add(LeadTimelineEvent(
            organization_id=org_id, lead_id=lead.id,
            event_type="ai_discovered",
            description=f"Discovered by AI Prospect Discovery Engine",
            metadata_json=json.dumps({
                "opportunity_score": company.opportunity_score,
                "industry": company.industry,
                "city": company.city,
            }),
        ))
        self._session.commit()
