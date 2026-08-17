"""
Celery tasks for the Intelligence Pipeline.

Each task enriches one lead independently using AI.
Workers process jobs concurrently — one failure never blocks others.
"""

import json
import logging
import os
import time
import uuid
from datetime import UTC, datetime

from celery import Celery
from celery.signals import worker_process_init

logger = logging.getLogger(__name__)

# ── Celery app (shared with celery_app.py via imports) ──

celery_app = Celery(
    "pns_worker",
    broker=f"redis://:{os.environ.get('REDIS_PASSWORD', 'redis_dev')}@redis:6379/0",
    backend=f"redis://:{os.environ.get('REDIS_PASSWORD', 'redis_dev')}@redis:6379/1",
)

# ── Lazy imports to avoid import errors at worker startup ──
# API code is available because worker Dockerfile copies apps/api/ too.

_db_session_factory = None
_llm_config = None


@worker_process_init.connect
def init_worker(**kwargs):
    """Initialize DB session factory and LLM config once per worker process."""
    global _db_session_factory, _llm_config
    from app.infrastructure.db.session import SessionLocal
    from app.application.llm.provider import LLMConfig
    import os
    _db_session_factory = SessionLocal
    _llm_config = LLMConfig(
        provider="openai",
        model="deepseek-chat",
        api_key=os.environ.get("DEEPSEEK_API_KEY", ""),
        api_base="https://api.deepseek.com/v1",
        temperature=0.3,
        max_tokens=1536,
    )


# ── Enrichment prompt (same as LLMDiscoveryProvider.enrich) ──

ENRICHMENT_PROMPT = """You are the AI Business Development Director for Pacific North Systems, a founder-led custom software company in Vancouver BC.

PNS Profile: custom software, AI automation, workflow automation, inspection software, dashboards, internal tools, reporting, document AI, CRM, integrations, IT consulting/support.
Business Stage: founder-led, relationship-first, direct sales. Goal: land smaller projects ($3K-$20K), expand into larger ($20K-$100K+), build long-term partnerships.
ICP: 10-150 employees, owner/founder accessible, manual processes (Excel/paper/email/WhatsApp), construction/property/HVAC/electrical/restoration/manufacturing/engineering/marine/field service, Metro Vancouver.

Company to evaluate:
Name: {name}
Industry: {industry}
City: {city}, {province}
Employees: {employees}
Description: {description}

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


# ── Helpers ──

def _parse_json(content: str) -> dict:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        return json.loads(content)


def _build_pns_fit_data(data: dict) -> str:
    return json.dumps({
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


# ── Pipeline orchestration ──

def _enqueue_next_stage(lead_id: int, org_id: int, stage_name: str) -> str:
    """Queue the next intelligence stage for a lead."""
    from app.infrastructure.db.models import EnrichmentJob

    job_id = str(uuid.uuid4())
    db = _db_session_factory()
    try:
        db.add(EnrichmentJob(
            id=job_id, organization_id=org_id, lead_id=lead_id,
            discovery_source="ai_discovery", status="queued", priority=1,
        ))
        db.commit()
    finally:
        db.close()

    celery_app.send_task(
        stage_name,
        kwargs={"lead_id": lead_id, "organization_id": org_id},
        task_id=job_id,
        priority=1,
    )
    logger.info("Queued %s for lead %d (job %s)", stage_name, lead_id, job_id)
    return job_id


# ── Retry schedule ──

RETRY_DELAYS = [0, 30, 120, 600]  # seconds: immediate, 30s, 2m, 10m


# ═══════════════════════════════════════════════════════════
# ENRICHMENT TASK
# ═══════════════════════════════════════════════════════════

@celery_app.task(
    name="intelligence.enrich_lead",
    bind=True,
    max_retries=0,
    default_retry_delay=30,
    acks_late=True,
    reject_on_worker_lost=True,
)
def enrich_lead(self, lead_id: int, organization_id: int, company_name: str,
                 industry: str = "", city: str = "", province: str = "",
                 employees: int | None = None, description: str = "") -> dict:
    """
    Enrich a single lead with AI intelligence.

    This task runs entirely in a background Celery worker.
    One failed enrichment never blocks other jobs.
    """
    from app.infrastructure.db.models import Lead, EnrichmentJob, LeadTimelineEvent
    from sqlalchemy import update

    job_id = self.request.id
    db = _db_session_factory()
    start_time = time.time()

    try:
        # ── Update job status to running ──
        db.execute(
            update(EnrichmentJob)
            .where(EnrichmentJob.id == job_id)
            .values(status="running", started_at=datetime.now(UTC), attempts=EnrichmentJob.attempts + 1,
                    worker_id=self.request.hostname)
        )
        db.execute(
            update(Lead)
            .where(Lead.id == lead_id)
            .values(enrichment_status="processing", enrichment_job_id=job_id)
        )
        db.commit()

        # ── Call LLM via gateway ──
        prompt = ENRICHMENT_PROMPT.format(
            name=company_name, industry=industry, city=city,
            province=province, employees=employees or "unknown",
            description=description or "unknown",
        )

        from app.application.llm.gateway import get_llm_gateway, GatewayConfig
        from app.application.llm.provider import LLMMessage as LLMMsg

        gateway = get_llm_gateway()
        messages = [
            LLMMsg(role="system", content="You are an expert B2B sales researcher. Return JSON only. Explain every score and recommendation."),
            LLMMsg(role="user", content=prompt),
        ]
        gcfg = GatewayConfig(feature="enrichment", organization_id=1, temperature=0.3)
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            gresp = loop.run_until_complete(gateway.chat(messages, gcfg))
        finally:
            loop.close()

        unavailable_models = {
            "disabled", "redis_unavailable", "budget_blocked", "error", "lock_timeout",
        }
        if gresp.model in unavailable_models:
            reason = f"LLM enrichment deferred: {gresp.model}"
            db.execute(
                update(EnrichmentJob).where(EnrichmentJob.id == job_id)
                .values(status="deferred", completed_at=datetime.now(UTC), error_message=reason)
            )
            db.execute(
                update(Lead).where(Lead.id == lead_id)
                .values(enrichment_status="pending")
            )
            db.add(LeadTimelineEvent(
                organization_id=organization_id,
                lead_id=lead_id,
                event_type="ai_enrichment_deferred",
                description=reason,
            ))
            db.commit()
            return {"status": "deferred", "lead_id": lead_id, "reason": gresp.model}

        data = _parse_json(gresp.content)

        # ── Update lead with enrichment data ──
        explainability = json.dumps({
            "score_breakdown": data.get("fit_factors", []),
            "confidence_factors": [],
            "signal_evidence": [],
            "service_reasoning": [],
        })

        db.execute(
            update(Lead)
            .where(Lead.id == lead_id)
            .values(
                executive_summary=data.get("executive_summary", ""),
                buying_signals=data.get("buying_signals", ""),
                recommended_services=data.get("recommended_services", ""),
                technology_maturity=data.get("technology_maturity", "medium"),
                estimated_deal_low=data.get("estimated_deal_low"),
                estimated_deal_high=data.get("estimated_deal_high"),
                opportunity_score=data.get("opportunity_score", 50),
                confidence_score=data.get("confidence_score", 60),
                revenue_estimate=data.get("revenue_estimate", ""),
                research_data=explainability,
                pns_fit_score=data.get("pns_fit_score", 50),
                pns_fit_data=_build_pns_fit_data(data),
                enrichment_status="complete",
                status="ready_for_review",
                last_researched_at=datetime.now(UTC),
            )
        )

        # ── Timeline event ──
        db.add(LeadTimelineEvent(
            organization_id=organization_id, lead_id=lead_id,
            event_type="ai_enrichment_complete",
            description=f"AI enrichment completed. PNS Fit: {data.get('pns_fit_score', 50)}/100. Recommendation: {data.get('founder_recommendation', 'LATER')}",
            metadata_json=json.dumps({"pns_fit_score": data.get("pns_fit_score"), "duration_ms": int((time.time() - start_time) * 1000)}),
        ))

        # ── Mark job complete ──
        elapsed_ms = int((time.time() - start_time) * 1000)
        db.execute(
            update(EnrichmentJob)
            .where(EnrichmentJob.id == job_id)
            .values(status="completed", completed_at=datetime.now(UTC), processing_time_ms=elapsed_ms)
        )
        db.commit()

        logger.info("Enrichment complete for lead %d (%s): PNS Fit %d", lead_id, company_name, data.get("pns_fit_score", 50))
        return {"status": "completed", "lead_id": lead_id, "pns_fit_score": data.get("pns_fit_score")}

    except Exception as exc:
        db.rollback()
        elapsed_ms = int((time.time() - start_time) * 1000)

        # ── Retry logic ──
        attempt = self.request.retries
        if attempt < self.max_retries:
            retry_delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
            db.execute(
                update(EnrichmentJob)
                .where(EnrichmentJob.id == job_id)
                .values(status="retrying", error_message=str(exc)[:500], attempts=attempt + 1)
            )
            db.execute(
                update(Lead)
                .where(Lead.id == lead_id)
                .values(enrichment_status="retrying")
            )
            db.commit()
            logger.warning("Enrichment failed for lead %d (attempt %d/%d): %s", lead_id, attempt + 1, self.max_retries, exc)
            raise self.retry(exc=exc, countdown=retry_delay)

        # ── Max retries exceeded ──
        db.execute(
            update(EnrichmentJob)
            .where(EnrichmentJob.id == job_id)
            .values(status="failed", error_message=str(exc)[:500], processing_time_ms=elapsed_ms)
        )
        db.execute(
            update(Lead)
            .where(Lead.id == lead_id)
            .values(enrichment_status="failed")
        )
        db.commit()
        logger.error("Enrichment permanently failed for lead %d: %s", lead_id, exc)
        return {"status": "failed", "lead_id": lead_id, "error": str(exc)[:200]}

    finally:
        db.close()


# ── Simple tasks ──

@celery_app.task(name="intelligence.ping")
def ping() -> str:
    return "pong"


# ═══════════════════════════════════════════════════════════
# GOOGLE MAPS INTELLIGENCE STAGE
# ═══════════════════════════════════════════════════════════

@celery_app.task(
    name="intelligence.google_maps",
    bind=True,
    max_retries=0,
    default_retry_delay=30,
    acks_late=True,
    reject_on_worker_lost=True,
)
def google_maps_intel(self, lead_id: int, organization_id: int) -> dict:
    """
    Google Maps Intelligence Stage.

    Collects Google Maps / Google Business Profile data for a lead.
    Runs as a background Celery task — independent of AI Research.
    """
    from app.infrastructure.db.models import Lead, EnrichmentJob, LeadTimelineEvent
    from app.application.intelligence.google_maps import GoogleMapsProvider
    from sqlalchemy import update, select
    import os

    job_id = self.request.id
    db = _db_session_factory()
    start_time = time.time()

    try:
        # ── Get lead data ──
        lead = db.execute(
            select(Lead).where(Lead.id == lead_id, Lead.organization_id == organization_id)
        ).scalar_one_or_none()

        if not lead:
            return {"status": "skipped", "lead_id": lead_id, "reason": "Lead not found"}

        # ── Update job + lead status ──
        db.execute(
            update(EnrichmentJob)
            .where(EnrichmentJob.id == job_id)
            .values(status="running", started_at=datetime.now(UTC), attempts=EnrichmentJob.attempts + 1,
                    worker_id=self.request.hostname)
        )
        db.commit()

        # ── Build company dict ──
        company = {
            "name": lead.name,
            "city": lead.city or "",
            "province": lead.province or "",
            "industry": lead.industry or "",
            "website": lead.website or "",
            "employees": lead.employees,
            "description": lead.description or "",
        }

        # ── Execute provider ──
        import asyncio
        provider = GoogleMapsProvider(api_key=os.environ.get("DEEPSEEK_API_KEY", ""))

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(provider.execute(company))
        finally:
            loop.close()

        # ── Store result ──
        google_maps_json = result.to_json()

        db.execute(
            update(Lead)
            .where(Lead.id == lead_id)
            .values(google_maps_data=google_maps_json)
        )

        # ── Timeline event ──
        event_desc = (
            f"Google Maps Intelligence: {result.data.get('primary_category', 'Unknown category')}. "
            f"Rating: {result.data.get('rating', 'N/A')} ({result.data.get('review_count', 0)} reviews). "
            f"Status: {result.status}"
        )
        db.add(LeadTimelineEvent(
            organization_id=organization_id, lead_id=lead_id,
            event_type="google_maps_complete",
            description=event_desc,
            metadata_json=json.dumps({
                "provider": result.provider_name,
                "status": result.status,
                "duration_ms": result.processing_time_ms,
                "rating": result.data.get("rating"),
                "review_count": result.data.get("review_count"),
            }),
        ))

        # ── Mark job complete ──
        elapsed_ms = int((time.time() - start_time) * 1000)
        db.execute(
            update(EnrichmentJob)
            .where(EnrichmentJob.id == job_id)
            .values(status="completed", completed_at=datetime.now(UTC), processing_time_ms=elapsed_ms)
        )
        db.commit()

        # ── Queue next stage: Website Intelligence ──
        _enqueue_next_stage(lead_id, organization_id, "intelligence.website")

        logger.info("Google Maps complete for lead %d: category=%s, rating=%s",
                     lead_id, result.data.get("primary_category"), result.data.get("rating"))
        return {"status": "completed", "lead_id": lead_id, "provider": "google_maps"}

    except Exception as exc:
        db.rollback()
        elapsed_ms = int((time.time() - start_time) * 1000)

        attempt = self.request.retries
        if attempt < self.max_retries:
            retry_delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
            db.execute(
                update(EnrichmentJob)
                .where(EnrichmentJob.id == job_id)
                .values(status="retrying", error_message=str(exc)[:500], attempts=attempt + 1)
            )
            db.commit()
            logger.warning("Google Maps failed for lead %d (attempt %d/%d): %s", lead_id, attempt + 1, self.max_retries, exc)
            raise self.retry(exc=exc, countdown=retry_delay)

        db.execute(
            update(EnrichmentJob)
            .where(EnrichmentJob.id == job_id)
            .values(status="failed", error_message=str(exc)[:500], processing_time_ms=elapsed_ms)
        )
        db.commit()
        logger.error("Google Maps permanently failed for lead %d: %s", lead_id, exc)
        return {"status": "failed", "lead_id": lead_id, "error": str(exc)[:200]}

    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
# PRODUCT RECOMMENDATION & OUTREACH STAGE
# ═══════════════════════════════════════════════════════════

PRODUCT_CATALOG = [
    "Field Inspection Platform",
    "Operations Dashboard",
    "AI Document Processing",
    "Custom CRM",
    "Scheduling & Dispatch System",
    "Client Portal",
    "Maintenance Management System",
    "Quote & Estimate Generator",
    "Asset Tracking",
    "Workflow Automation",
    "Reporting Dashboard",
    "AI Business Assistant",
]

PRODUCT_RECOMMENDATION_PROMPT = """You are a senior sales engineer at Pacific North Systems, a custom software company in Vancouver BC.

PNS builds: {catalog}

Company to recommend for:
Name: {name}
Industry: {industry}
City: {city}, {province}
Employees: {employees}
Description: {description}
Google Maps Category: {gmaps_category}
AI Research Summary: {summary}
PNS Fit Score: {pns_fit}/100
Founder Recommendation: {founder_rec}

Your job: recommend the SINGLE best product for the FIRST conversation with this company. Choose from the PNS catalog only. The goal is to start a relationship with a realistic, achievable project — not the biggest possible deal.

Respond with JSON only:
{{
  "recommended_product": "Field Inspection Platform",
  "reason": "2-3 sentences explaining why this product fits this specific company, referencing their industry, size, and operational patterns.",
  "estimated_price_low": 8000,
  "estimated_price_high": 15000,
  "development_time": "4-6 weeks",
  "confidence": 91,

  "email_pitch": "A personalized cold email. Max 150 words. Friendly, professional. Mention one observation about their business. Explain one problem the software solves. Invite to a short conversation. No exaggerated claims. No AI-sounding marketing language.",

  "phone_pitch": "A conversational phone opening. Max 30 seconds spoken. Structure: greeting, reason for calling, one observation, value proposition, question."
}}"""


@celery_app.task(
    name="intelligence.product_recommendation",
    bind=True,
    max_retries=0,
    default_retry_delay=60,
    acks_late=True,
    reject_on_worker_lost=True,
)
def product_recommendation(self, lead_id: int, organization_id: int) -> dict:
    """
    Product Recommendation & Outreach Stage.

    Recommends the best first product and generates email + phone pitches.
    Consumes all existing intelligence (AI Research, Google Maps, PNS Fit).
    """
    from app.application.llm.provider import LLMMessage
    from app.infrastructure.db.models import Lead, EnrichmentJob, LeadTimelineEvent
    from sqlalchemy import update, select
    import asyncio

    job_id = self.request.id
    db = _db_session_factory()
    start_time = time.time()

    try:
        lead = db.execute(
            select(Lead).where(Lead.id == lead_id, Lead.organization_id == organization_id)
        ).scalar_one_or_none()
        if not lead:
            return {"status": "skipped", "lead_id": lead_id, "reason": "Lead not found"}

        db.execute(
            update(EnrichmentJob)
            .where(EnrichmentJob.id == job_id)
            .values(status="running", started_at=datetime.now(UTC), attempts=EnrichmentJob.attempts + 1,
                    worker_id=self.request.hostname)
        )
        db.commit()

        # Parse existing intelligence
        gmaps_data = {}
        if lead.google_maps_data:
            try: gmaps_data = json.loads(lead.google_maps_data)
            except json.JSONDecodeError: pass

        pns_fit_data = {}
        if lead.pns_fit_data:
            try: pns_fit_data = json.loads(lead.pns_fit_data)
            except json.JSONDecodeError: pass

        prompt = PRODUCT_RECOMMENDATION_PROMPT.format(
            catalog=", ".join(PRODUCT_CATALOG),
            name=lead.name,
            industry=lead.industry or "Unknown",
            city=lead.city or "",
            province=lead.province or "",
            employees=lead.employees or "unknown",
            description=lead.description or "No description available",
            gmaps_category=gmaps_data.get("data", {}).get("primary_category", "Unknown"),
            summary=lead.executive_summary or "No AI research summary available",
            pns_fit=lead.pns_fit_score or 50,
            founder_rec=pns_fit_data.get("founder_recommendation", "LATER"),
        )

        from app.application.llm.gateway import get_llm_gateway, GatewayConfig
        gateway = get_llm_gateway()
        gcfg = GatewayConfig(feature="enrichment", organization_id=1, temperature=0.3)
        messages = [
            LLMMessage(role="system", content="You are a senior sales engineer. Return JSON only."),
            LLMMessage(role="user", content=prompt),
        ]

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            gresp = loop.run_until_complete(gateway.chat(messages, gcfg))
        finally:
            loop.close()

        data = _parse_json(gresp.content)

        rec_json = json.dumps({
            "recommended_product": data.get("recommended_product", ""),
            "reason": data.get("reason", ""),
            "estimated_price_low": data.get("estimated_price_low"),
            "estimated_price_high": data.get("estimated_price_high"),
            "development_time": data.get("development_time", ""),
            "confidence": data.get("confidence", 50),
            "email_pitch": data.get("email_pitch", ""),
            "phone_pitch": data.get("phone_pitch", ""),
        })

        db.execute(
            update(Lead).where(Lead.id == lead_id)
            .values(product_recommendation_data=rec_json)
        )

        db.add(LeadTimelineEvent(
            organization_id=organization_id, lead_id=lead_id,
            event_type="product_recommendation",
            description=f"Recommended: {data.get('recommended_product', 'N/A')}. Confidence: {data.get('confidence', '?')}%",
            metadata_json=json.dumps({"product": data.get("recommended_product"), "confidence": data.get("confidence")}),
        ))

        elapsed_ms = int((time.time() - start_time) * 1000)
        db.execute(
            update(EnrichmentJob).where(EnrichmentJob.id == job_id)
            .values(status="completed", completed_at=datetime.now(UTC), processing_time_ms=elapsed_ms)
        )
        db.commit()

        logger.info("Product recommendation complete for lead %d: %s (confidence %d%%)",
                     lead_id, data.get("recommended_product"), data.get("confidence", 0))
        return {"status": "completed", "lead_id": lead_id, "product": data.get("recommended_product")}

    except Exception as exc:
        db.rollback()
        elapsed_ms = int((time.time() - start_time) * 1000)
        attempt = self.request.retries
        if attempt < self.max_retries:
            retry_delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
            db.execute(
                update(EnrichmentJob).where(EnrichmentJob.id == job_id)
                .values(status="retrying", error_message=str(exc)[:500], attempts=attempt + 1)
            )
            db.commit()
            logger.warning("Product recommendation failed for lead %d (attempt %d/%d): %s", lead_id, attempt + 1, self.max_retries, exc)
            raise self.retry(exc=exc, countdown=retry_delay)

        db.execute(
            update(EnrichmentJob).where(EnrichmentJob.id == job_id)
            .values(status="failed", error_message=str(exc)[:500], processing_time_ms=elapsed_ms)
        )
        db.commit()
        logger.error("Product recommendation permanently failed for lead %d: %s", lead_id, exc)
        return {"status": "failed", "lead_id": lead_id, "error": str(exc)[:200]}

    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
# GENERIC INTELLIGENCE STAGE RUNNER
# ═══════════════════════════════════════════════════════════

def _run_intelligence_stage(
    self, lead_id: int, organization_id: int,
    provider_class, column_name: str, provider_label: str,
    extra_company_fields: dict | None = None,
) -> dict:
    """Generic runner for any IntelligenceProvider stage. Avoids boilerplate."""
    from app.infrastructure.db.models import Lead, EnrichmentJob, LeadTimelineEvent
    from sqlalchemy import update, select
    import asyncio, os

    job_id = self.request.id
    db = _db_session_factory()
    start_time = time.time()

    try:
        lead = db.execute(
            select(Lead).where(Lead.id == lead_id, Lead.organization_id == organization_id)
        ).scalar_one_or_none()
        if not lead:
            return {"status": "skipped", "lead_id": lead_id, "reason": "Lead not found"}

        db.execute(
            update(EnrichmentJob).where(EnrichmentJob.id == job_id)
            .values(status="running", started_at=datetime.now(UTC), attempts=EnrichmentJob.attempts + 1, worker_id=self.request.hostname)
        )
        db.commit()

        company = {
            "name": lead.name, "city": lead.city or "", "province": lead.province or "",
            "industry": lead.industry or "", "website": lead.website or "",
            "employees": lead.employees, "description": lead.description or "",
        }
        if extra_company_fields:
            company.update(extra_company_fields)

        provider = provider_class(api_key=os.environ.get("DEEPSEEK_API_KEY", ""))
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(provider.execute(company))
        finally:
            loop.close()

        result_json = result.to_json()
        db.execute(update(Lead).where(Lead.id == lead_id).values(**{column_name: result_json}))

        db.add(LeadTimelineEvent(
            organization_id=organization_id, lead_id=lead_id,
            event_type=f"{provider_label.lower().replace(' ', '_')}_complete",
            description=f"{provider_label}: {result.status}",
            metadata_json=json.dumps({"provider": result.provider_name, "status": result.status, "duration_ms": result.processing_time_ms}),
        ))

        elapsed_ms = int((time.time() - start_time) * 1000)
        db.execute(
            update(EnrichmentJob).where(EnrichmentJob.id == job_id)
            .values(status="completed", completed_at=datetime.now(UTC), processing_time_ms=elapsed_ms)
        )
        db.commit()

        # Queue next stage
        _enqueue_next_stage(lead_id, organization_id, _NEXT_STAGE.get(provider_label))

        logger.info("%s complete for lead %d", provider_label, lead_id)
        return {"status": "completed", "lead_id": lead_id, "provider": result.provider_name}

    except Exception as exc:
        db.rollback()
        elapsed_ms = int((time.time() - start_time) * 1000)
        attempt = self.request.retries
        if attempt < self.max_retries:
            retry_delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
            db.execute(update(EnrichmentJob).where(EnrichmentJob.id == job_id).values(status="retrying", error_message=str(exc)[:500], attempts=attempt + 1))
            db.commit()
            logger.warning("%s failed for lead %d (attempt %d/%d): %s", provider_label, lead_id, attempt + 1, self.max_retries, exc)
            raise self.retry(exc=exc, countdown=retry_delay)
        db.execute(update(EnrichmentJob).where(EnrichmentJob.id == job_id).values(status="failed", error_message=str(exc)[:500], processing_time_ms=elapsed_ms))
        db.commit()
        logger.error("%s permanently failed for lead %d: %s", provider_label, lead_id, exc)
        return {"status": "failed", "lead_id": lead_id, "error": str(exc)[:200]}
    finally:
        db.close()


# Stage chain: each stage queues the next
_NEXT_STAGE = {
    "Google Maps Intelligence": "intelligence.website",
    "Website Intelligence": "intelligence.google_reviews",
    "Google Reviews Intelligence": "intelligence.linkedin",
    "LinkedIn Intelligence": "intelligence.product_recommendation",
}


# ═══════════════════════════════════════════════════════════
# WEBSITE INTELLIGENCE
# ═══════════════════════════════════════════════════════════

@celery_app.task(name="intelligence.website", bind=True, max_retries=0, default_retry_delay=30, acks_late=True, reject_on_worker_lost=True)
def website_intel(self, lead_id: int, organization_id: int) -> dict:
    from app.application.intelligence.website import WebsiteIntelligenceProvider
    return _run_intelligence_stage(self, lead_id, organization_id, WebsiteIntelligenceProvider, "website_data", "Website Intelligence")


# ═══════════════════════════════════════════════════════════
# GOOGLE REVIEWS INTELLIGENCE
# ═══════════════════════════════════════════════════════════

@celery_app.task(name="intelligence.google_reviews", bind=True, max_retries=0, default_retry_delay=30, acks_late=True, reject_on_worker_lost=True)
def google_reviews_intel(self, lead_id: int, organization_id: int) -> dict:
    from app.application.intelligence.google_reviews import GoogleReviewsProvider

    # Pass Google Maps data for richer review analysis
    db = _db_session_factory()
    extra = {}
    try:
        from sqlalchemy import select
        from app.infrastructure.db.models import Lead
        lead = db.execute(select(Lead).where(Lead.id == lead_id)).scalar_one_or_none()
        if lead and lead.google_maps_data:
            import json as _json
            gmaps = _json.loads(lead.google_maps_data)
            extra["gmaps_rating"] = gmaps.get("data", {}).get("rating", "unknown")
            extra["gmaps_review_count"] = gmaps.get("data", {}).get("review_count", "unknown")
            extra["gmaps_category"] = gmaps.get("data", {}).get("primary_category", "unknown")
    finally:
        db.close()

    return _run_intelligence_stage(self, lead_id, organization_id, GoogleReviewsProvider, "reviews_data", "Google Reviews Intelligence", extra)


# ═══════════════════════════════════════════════════════════
# LINKEDIN INTELLIGENCE
# ═══════════════════════════════════════════════════════════

@celery_app.task(name="intelligence.linkedin", bind=True, max_retries=0, default_retry_delay=30, acks_late=True, reject_on_worker_lost=True)
def linkedin_intel(self, lead_id: int, organization_id: int) -> dict:
    from app.application.intelligence.linkedin import LinkedInProvider
    return _run_intelligence_stage(self, lead_id, organization_id, LinkedInProvider, "linkedin_data", "LinkedIn Intelligence")


@celery_app.task(name="intelligence.bulk_enrich")
def bulk_enrich(jobs: list[dict]) -> dict:
    """Queue multiple enrichment jobs and return immediately."""
    queued = []
    for job in jobs:
        task = enrich_lead.apply_async(
            kwargs=job["kwargs"],
            task_id=job.get("job_id", str(uuid.uuid4())),
            priority=job.get("priority", 0),
        )
        queued.append({"job_id": task.id, "lead_id": job["kwargs"]["lead_id"]})
    return {"queued": len(queued), "jobs": queued}
