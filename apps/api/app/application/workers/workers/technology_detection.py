import logging
from app.application.workers.framework import BaseWorker, WorkerConfig, WorkerPriority, ScheduleType
from app.application.workers.events import WORKER_EVENT_SUBSCRIPTIONS
logger = logging.getLogger(__name__)
KNOWN_TECH = ["QuickBooks","Procore","Jobber","Buildertrend","ServiceTitan","Microsoft 365","Google Workspace","HubSpot","Salesforce","Azure","AWS","Cloudflare","Slack","Zoom","Monday.com","Asana","Jira","Zendesk","Stripe","Shopify","WordPress"]
def create_technology_detection_worker(db_factory) -> BaseWorker:
    return TechnologyDetectionWorker(WorkerConfig(name="technology_detection", description="Detects technologies used by companies", priority=WorkerPriority.NORMAL, concurrency=2, max_retries=3, schedule=ScheduleType.EVENT_TRIGGERED, supported_events=[e.value for e in WORKER_EVENT_SUBSCRIPTIONS["technology_detection"]], capabilities=["tech_detection"]), db_factory)
class TechnologyDetectionWorker(BaseWorker):
    async def execute(self) -> None:
        db = self._db_factory()
        try:
            from app.infrastructure.db.knowledge_graph import KnowledgeFact
            from app.application.knowledge.service import KnowledgeService
            knowledge = KnowledgeService(db)
            facts = db.query(KnowledgeFact).filter(KnowledgeFact.entity_type.in_(["company","signal","lead"]), KnowledgeFact.created_at.isnot(None)).order_by(KnowledgeFact.created_at.desc()).limit(50).all()
            for fact in facts:
                text = f"{fact.key} {fact.value}".lower()
                for tech in KNOWN_TECH:
                    if tech.lower() in text:
                        knowledge.set_fact(entity_type=fact.entity_type, entity_id=fact.entity_id, key="uses_technology", value=tech, source="technology_detection_worker", confidence=0.65)
                        self._metrics.facts_created += 1
        finally: db.close()
