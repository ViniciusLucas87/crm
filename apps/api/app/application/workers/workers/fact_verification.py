"""Worker 2 — Fact Verification"""
import logging
from app.application.workers.framework import BaseWorker, WorkerConfig, WorkerPriority, ScheduleType
from app.application.workers.events import WORKER_EVENT_SUBSCRIPTIONS
logger = logging.getLogger(__name__)

def create_fact_verification_worker(db_factory) -> BaseWorker:
    return FactVerificationWorker(WorkerConfig(name="fact_verification",
        description="Cross-source fact verification and confidence adjustment",
        priority=WorkerPriority.HIGH, concurrency=2, max_retries=3,
        schedule=ScheduleType.EVENT_TRIGGERED,
        supported_events=[e.value for e in WORKER_EVENT_SUBSCRIPTIONS["fact_verification"]],
        capabilities=["cross_source_verification", "confidence_adjustment"]), db_factory)

class FactVerificationWorker(BaseWorker):
    async def execute(self) -> None:
        db = self._db_factory()
        try:
            from app.infrastructure.db.knowledge_graph import KnowledgeFact
            facts = db.query(KnowledgeFact).filter(KnowledgeFact.confidence < 0.7).order_by(KnowledgeFact.confidence.asc()).limit(10).all()
            for fact in facts:
                corroborated = db.query(KnowledgeFact).filter(
                    KnowledgeFact.entity_type == fact.entity_type, KnowledgeFact.entity_id == fact.entity_id,
                    KnowledgeFact.key == fact.key, KnowledgeFact.source != fact.source, KnowledgeFact.id != fact.id).first()
                fact.confidence = min(1.0, fact.confidence + 0.15) if corroborated else max(0.1, fact.confidence - 0.02)
                db.commit()
                self._metrics.facts_verified += 1
        finally: db.close()
