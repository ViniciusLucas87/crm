import logging
from app.application.workers.framework import BaseWorker, WorkerConfig, WorkerPriority, ScheduleType
from app.application.workers.events import WORKER_EVENT_SUBSCRIPTIONS
logger = logging.getLogger(__name__)
def create_reasoning_worker(db_factory) -> BaseWorker:
    return ReasoningWorker(WorkerConfig(name="reasoning", description="Generates AI insights from graph patterns", priority=WorkerPriority.NORMAL, concurrency=1, max_retries=3, schedule=ScheduleType.EVENT_TRIGGERED, supported_events=[e.value for e in WORKER_EVENT_SUBSCRIPTIONS["reasoning"]], capabilities=["pattern_detection","insight_generation"]), db_factory)
class ReasoningWorker(BaseWorker):
    async def execute(self) -> None:
        db = self._db_factory()
        try:
            from app.infrastructure.db.knowledge_graph import KnowledgeFact
            from app.application.knowledge.service import KnowledgeService
            knowledge = KnowledgeService(db)
            companies = db.query(KnowledgeFact).filter(KnowledgeFact.entity_type == "company").distinct(KnowledgeFact.entity_id).limit(20).all()
            seen = set()
            for fact in companies:
                if fact.entity_id in seen: continue
                seen.add(fact.entity_id)
                facts = db.query(KnowledgeFact).filter(KnowledgeFact.entity_type == "company", KnowledgeFact.entity_id == fact.entity_id).all()
                fmap = {f.key: f.value for f in facts}
                if any("hiring" in str(v).lower() for v in fmap.values()):
                    knowledge.set_fact(entity_type="company", entity_id=fact.entity_id, key="insight_growth", value="Company showing hiring signals", source="reasoning_worker", confidence=0.55)
                    self._metrics.insights_generated += 1
                has_manual = any("manual" in str(v).lower() or "spreadsheet" in str(v).lower() for v in fmap.values())
                has_growth = any(k.startswith("buying_signal_grow") for k in fmap)
                if has_manual and has_growth:
                    knowledge.set_fact(entity_type="company", entity_id=fact.entity_id, key="insight_digital_transformation", value="Manual processes + growth signals", source="reasoning_worker", confidence=0.6)
                    self._metrics.insights_generated += 1
        finally: db.close()
