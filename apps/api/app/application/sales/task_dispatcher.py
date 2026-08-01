"""
Intelligence Pipeline — task dispatcher.

Sends enrichment jobs to Celery workers from the API layer.
Provider-agnostic: any future provider queues jobs the same way.
"""

import uuid
import logging
from celery import Celery

logger = logging.getLogger(__name__)

# Celery app for sending tasks (not running workers)
celery_app = Celery(
    "pns_dispatcher",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/1",
)

# Import tasks so they're registered
celery_app.conf.imports = ("tasks",)


def queue_enrichment(
    lead_id: int,
    organization_id: int,
    company_name: str,
    industry: str = "",
    city: str = "",
    province: str = "",
    employees: int | None = None,
    description: str = "",
    priority: int = 0,
) -> str:
    """
    Queue an AI enrichment job for a single lead.

    Returns the Celery task ID (used as the job ID).
    """
    job_id = str(uuid.uuid4())
    celery_app.send_task(
        "intelligence.enrich_lead",
        kwargs={
            "lead_id": lead_id,
            "organization_id": organization_id,
            "company_name": company_name,
            "industry": industry,
            "city": city,
            "province": province,
            "employees": employees,
            "description": description,
        },
        task_id=job_id,
        priority=priority,
    )
    logger.info("Queued enrichment job %s for lead %d (%s)", job_id, lead_id, company_name)
    return job_id


def queue_bulk_enrichment(jobs: list[dict]) -> list[dict]:
    """
    Queue multiple enrichment jobs at once.

    Each job dict: {lead_id, organization_id, company_name, industry, city, ...}
    Returns list of {job_id, lead_id}.
    """
    results = []
    for job in jobs:
        job_id = queue_enrichment(**job, priority=job.get("priority", 0))
        results.append({"job_id": job_id, "lead_id": job["lead_id"]})
    return results
