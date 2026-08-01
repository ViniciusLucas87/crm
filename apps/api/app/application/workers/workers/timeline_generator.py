import logging
from app.application.workers.framework import BaseWorker, WorkerConfig, WorkerPriority, ScheduleType
from app.application.workers.events import WORKER_EVENT_SUBSCRIPTIONS
logger = logging.getLogger(__name__)
def create_timeline_generator_worker(db_factory) -> BaseWorker:
    return TimelineGeneratorWorker(WorkerConfig(name="timeline_generator", description="Auto-builds company history timelines", priority=WorkerPriority.LOW, concurrency=1, max_retries=3, schedule=ScheduleType.HOURLY, supported_events=[e.value for e in WORKER_EVENT_SUBSCRIPTIONS["timeline_generator"]], capabilities=["timeline_creation"]), db_factory)
class TimelineGeneratorWorker(BaseWorker):
    async def execute(self) -> None:
        db = self._db_factory()
        try:
            from app.infrastructure.db.knowledge_graph import KnowledgeEvent
            from app.application.knowledge.service import KnowledgeService
            knowledge = KnowledgeService(db)
            events = db.query(KnowledgeEvent).filter(KnowledgeEvent.entity_type == "company").order_by(KnowledgeEvent.created_at.desc()).limit(50).all()
            for event in events:
                knowledge.set_fact(entity_type="company", entity_id=event.entity_id, key=f"timeline_{event.event_type}", value=event.description or event.event_type, source="timeline_generator_worker", confidence=0.95)
                self._metrics.facts_created += 1
        finally: db.close()
