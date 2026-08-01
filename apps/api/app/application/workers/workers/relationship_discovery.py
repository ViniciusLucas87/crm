import logging
from app.application.workers.framework import BaseWorker, WorkerConfig, WorkerPriority, ScheduleType
from app.application.workers.events import WORKER_EVENT_SUBSCRIPTIONS
logger = logging.getLogger(__name__)
def create_relationship_discovery_worker(db_factory) -> BaseWorker:
    return RelationshipDiscoveryWorker(WorkerConfig(name="relationship_discovery", description="Infers relationships between entities", priority=WorkerPriority.NORMAL, concurrency=1, max_retries=3, schedule=ScheduleType.EVENT_TRIGGERED, supported_events=[e.value for e in WORKER_EVENT_SUBSCRIPTIONS["relationship_discovery"]], capabilities=["relationship_inference"]), db_factory)
class RelationshipDiscoveryWorker(BaseWorker):
    async def execute(self) -> None:
        db = self._db_factory()
        try:
            from app.infrastructure.db.knowledge_graph import KnowledgeFact
            from app.application.knowledge.service import KnowledgeService
            knowledge = KnowledgeService(db)
            contacts = db.query(KnowledgeFact).filter(KnowledgeFact.entity_type == "contact", KnowledgeFact.key == "company_name").limit(20).all()
            for fact in contacts:
                company = db.query(KnowledgeFact).filter(KnowledgeFact.entity_type == "company", KnowledgeFact.key == "name", KnowledgeFact.value == fact.value).first()
                if company:
                    knowledge.add_relationship(from_type="contact", from_id=fact.entity_id, to_type="company", to_id=company.entity_id, rel_type="works_for", properties={"discovered_by": "relationship_discovery_worker"})
                    self._metrics.relationships_created += 1
        finally: db.close()
