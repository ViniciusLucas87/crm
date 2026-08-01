import logging
from app.application.workers.framework import BaseWorker, WorkerConfig, WorkerPriority, ScheduleType
from app.application.workers.events import WORKER_EVENT_SUBSCRIPTIONS
logger = logging.getLogger(__name__)
def create_recommendation_engine_worker(db_factory) -> BaseWorker:
    return RecommendationEngineWorker(WorkerConfig(name="recommendation_engine", description="Generates actionable recommendations", priority=WorkerPriority.NORMAL, concurrency=1, max_retries=3, schedule=ScheduleType.EVENT_TRIGGERED, supported_events=[e.value for e in WORKER_EVENT_SUBSCRIPTIONS["recommendation_engine"]], capabilities=["recommendation_generation"]), db_factory)
class RecommendationEngineWorker(BaseWorker):
    async def execute(self) -> None:
        db = self._db_factory()
        try:
            from app.infrastructure.db.knowledge_graph import KnowledgeFact
            from app.application.knowledge.service import KnowledgeService
            knowledge = KnowledgeService(db)
            opps = db.query(KnowledgeFact).filter(KnowledgeFact.entity_type == "opportunity").distinct(KnowledgeFact.entity_id).limit(20).all()
            seen = set()
            for opp in opps:
                if opp.entity_id in seen: continue
                seen.add(opp.entity_id)
                facts = db.query(KnowledgeFact).filter(KnowledgeFact.entity_type == "opportunity", KnowledgeFact.entity_id == opp.entity_id).all()
                fmap = {f.key: f.value for f in facts}
                has_signals = any(k.startswith("buying_signal_") for k in fmap)
                score = int(fmap.get("opportunity_score", "0"))
                rec = "monitor"
                if score >= 70 and has_signals: rec = "call_soon"
                elif 40 <= score < 70 and any("evaluat" in str(v).lower() for v in fmap.values()): rec = "research_more"
                elif score < 30: rec = "monitor"
                knowledge.set_fact(entity_type="opportunity", entity_id=opp.entity_id, key="recommendation", value=rec, source="recommendation_engine_worker", confidence=0.7)
                self._metrics.insights_generated += 1
        finally: db.close()
