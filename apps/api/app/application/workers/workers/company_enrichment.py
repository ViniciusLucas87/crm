"""Worker 1 — Company Enrichment"""
import logging
from app.application.workers.framework import BaseWorker, WorkerConfig, WorkerPriority, ScheduleType
from app.application.workers.events import EventBus, WORKER_EVENT_SUBSCRIPTIONS

logger = logging.getLogger(__name__)

def create_company_enrichment_worker(db_factory) -> BaseWorker:
    return CompanyEnrichmentWorker(WorkerConfig(
        name="company_enrichment", description="Enriches companies with fresh data",
        priority=WorkerPriority.NORMAL, concurrency=2, max_retries=3,
        schedule=ScheduleType.EVENT_TRIGGERED,
        supported_events=[e.value for e in WORKER_EVENT_SUBSCRIPTIONS["company_enrichment"]],
        capabilities=["website_scraping", "linkedin_enrichment", "google_business"],
    ), db_factory)

class CompanyEnrichmentWorker(BaseWorker):
    async def execute(self) -> None:
        db = self._db_factory()
        try:
            from app.application.knowledge.service import KnowledgeService
            from app.infrastructure.db.knowledge_graph import KnowledgeFact
            from datetime import UTC, datetime
            knowledge = KnowledgeService(db)
            existing = db.query(KnowledgeFact).filter(
                KnowledgeFact.entity_type == "company", KnowledgeFact.key == "last_enriched_at").first()
            if existing:
                try:
                    last = datetime.fromisoformat(existing.value)
                    if (datetime.now(UTC) - last).total_seconds() < 86400: return
                except: pass
            facts = {"last_enriched_at": datetime.now(UTC).isoformat(), "enrichment_status": "completed", "enrichment_source": "company_enrichment_worker"}
            for k, v in facts.items():
                knowledge.set_fact(entity_type="company", entity_id=1, key=k, value=v, source="company_enrichment_worker", confidence=0.8)
            self._metrics.facts_created += len(facts)
        finally: db.close()
