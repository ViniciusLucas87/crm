import logging
from datetime import UTC, datetime, timedelta
from app.application.workers.framework import BaseWorker, WorkerConfig, WorkerPriority, ScheduleType
from app.application.workers.events import Event, EventBus, EventType
logger = logging.getLogger(__name__)
def create_knowledge_decay_worker(db_factory) -> BaseWorker:
    return KnowledgeDecayWorker(WorkerConfig(name="knowledge_decay", description="Ages knowledge and reduces confidence", priority=WorkerPriority.LOW, concurrency=1, max_retries=3, schedule=ScheduleType.DAILY, supported_events=["fact_created","fact_updated"], capabilities=["confidence_decay","stale_detection"]), db_factory)
class KnowledgeDecayWorker(BaseWorker):
    async def execute(self) -> None:
        db = self._db_factory()
        try:
            from app.infrastructure.db.knowledge_graph import KnowledgeFact
            bus = EventBus(db)
            threshold = datetime.now(UTC) - timedelta(days=7)
            stale = db.query(KnowledgeFact).filter(KnowledgeFact.confidence > 0.2, KnowledgeFact.updated_at < threshold).order_by(KnowledgeFact.updated_at.asc()).limit(20).all()
            for fact in stale:
                days_old = (datetime.now(UTC) - fact.updated_at).days
                decay = min(0.05, days_old * 0.005)
                fact.confidence = max(0.1, fact.confidence - decay)
                db.commit()
                bus.publish(Event(event_type=EventType.KNOWLEDGE_DECAYED, entity_type=fact.entity_type, entity_id=fact.entity_id, payload={"fact_id":fact.id,"key":fact.key}, source="knowledge_decay_worker"))
                self._metrics.facts_verified += 1
        finally: db.close()
