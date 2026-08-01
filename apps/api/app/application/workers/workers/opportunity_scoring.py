import logging
from app.application.workers.framework import BaseWorker, WorkerConfig, WorkerPriority, ScheduleType
from app.application.workers.events import WORKER_EVENT_SUBSCRIPTIONS
logger = logging.getLogger(__name__)
def create_opportunity_scoring_worker(db_factory) -> BaseWorker:
    return OpportunityScoringWorker(WorkerConfig(name="opportunity_scoring", description="Continuously scores opportunities", priority=WorkerPriority.HIGH, concurrency=2, max_retries=3, schedule=ScheduleType.EVENT_TRIGGERED, supported_events=[e.value for e in WORKER_EVENT_SUBSCRIPTIONS["opportunity_scoring"]], capabilities=["opportunity_scoring","risk_assessment"]), db_factory)
class OpportunityScoringWorker(BaseWorker):
    async def execute(self) -> None:
        db = self._db_factory()
        try:
            from app.infrastructure.db.knowledge_graph import KnowledgeFact
            from app.application.knowledge.service import KnowledgeService
            knowledge = KnowledgeService(db)
            opps = db.query(KnowledgeFact).filter(KnowledgeFact.entity_type == "opportunity", KnowledgeFact.key == "status").limit(20).all()
            for opp in opps:
                facts = db.query(KnowledgeFact).filter(KnowledgeFact.entity_type == "opportunity", KnowledgeFact.entity_id == opp.entity_id).all()
                fmap = {f.key: f.value for f in facts}
                score = 50 + len([k for k in fmap if k.startswith("buying_signal_")]) * 10
                if any("budget" in k for k in fmap): score += 15
                if any("urgent" in str(v).lower() for v in fmap.values()): score += 20
                score = min(100, max(0, score))
                for key, val in [("opportunity_score", score), ("health_score", 70), ("risk_score", 30)]:
                    knowledge.set_fact(entity_type="opportunity", entity_id=opp.entity_id, key=key, value=str(val), source="opportunity_scoring_worker", confidence=0.7)
                self._metrics.facts_created += 3
        finally: db.close()
