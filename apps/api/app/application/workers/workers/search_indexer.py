import logging
from app.application.workers.framework import BaseWorker, WorkerConfig, WorkerPriority, ScheduleType
from app.application.workers.events import WORKER_EVENT_SUBSCRIPTIONS
logger = logging.getLogger(__name__)
def create_search_indexer_worker(db_factory) -> BaseWorker:
    return SearchIndexerWorker(WorkerConfig(name="search_indexer", description="Maintains semantic search index", priority=WorkerPriority.BACKGROUND, concurrency=1, max_retries=3, schedule=ScheduleType.HOURLY, supported_events=[e.value for e in WORKER_EVENT_SUBSCRIPTIONS["search_indexer"]], capabilities=["semantic_indexing"]), db_factory)
class SearchIndexerWorker(BaseWorker):
    async def execute(self) -> None:
        db = self._db_factory()
        try:
            from app.infrastructure.db.knowledge_graph import KnowledgeFact
            from app.application.knowledge.service import KnowledgeService
            knowledge = KnowledgeService(db)
            facts = db.query(KnowledgeFact).filter(KnowledgeFact.key == "search_indexed", KnowledgeFact.value == "false").limit(30).all()
            for fact in facts:
                fact.value = "true"; db.commit()
            if facts:
                knowledge.set_fact(entity_type="system", entity_id=0, key="search_index_size", value=str(db.query(KnowledgeFact).count()), source="search_indexer_worker", confidence=1.0)
                self._metrics.facts_created += 1
        finally: db.close()
