"""Worker 3 — Entity Resolution"""
import logging
from app.application.workers.framework import BaseWorker, WorkerConfig, WorkerPriority, ScheduleType
from app.application.workers.events import WORKER_EVENT_SUBSCRIPTIONS
logger = logging.getLogger(__name__)

def create_entity_resolution_worker(db_factory) -> BaseWorker:
    return EntityResolutionWorker(WorkerConfig(name="entity_resolution",
        description="Detects and merges duplicate entities",
        priority=WorkerPriority.NORMAL, concurrency=1, max_retries=3,
        schedule=ScheduleType.DAILY,
        supported_events=[e.value for e in WORKER_EVENT_SUBSCRIPTIONS["entity_resolution"]],
        capabilities=["duplicate_detection", "entity_merging"]), db_factory)

class EntityResolutionWorker(BaseWorker):
    async def execute(self) -> None:
        db = self._db_factory()
        try:
            from app.infrastructure.db.knowledge_graph import KnowledgeFact
            from app.application.knowledge.service import KnowledgeService
            knowledge = KnowledgeService(db)
            names = db.query(KnowledgeFact).filter(KnowledgeFact.entity_type == "company", KnowledgeFact.key == "name").all()
            seen = {}
            for f in names:
                n = f.value.lower().strip().rstrip(".")
                for s in [" inc", " ltd", " llc", " corp", " limited", " incorporated"]:
                    n = n.replace(s, "")
                seen.setdefault(n, []).append(f)
            for n, facts in seen.items():
                if len(facts) > 1:
                    ids = set(f.entity_id for f in facts)
                    if len(ids) > 1:
                        knowledge.set_fact(entity_type="system", entity_id=0, key="potential_duplicate",
                            value=f"companies:{','.join(map(str,sorted(ids)))}", source="entity_resolution_worker", confidence=0.6)
                        self._metrics.insights_generated += 1
        finally: db.close()
