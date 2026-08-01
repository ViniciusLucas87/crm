import logging
from app.application.workers.framework import BaseWorker, WorkerConfig, WorkerPriority, ScheduleType
from app.application.workers.events import WORKER_EVENT_SUBSCRIPTIONS
logger = logging.getLogger(__name__)
SIGNAL_KW = {"budget_approved":["budget approved","funding secured","we have budget"],"urgent_need":["urgent","asap","immediately","this quarter"],"growing":["growing fast","expanding","hiring","scaling"],"digital_transformation":["digital transformation","modernize","automate"],"manual_processes":["manual process","spreadsheet","paper","excel"],"evaluating":["evaluating","looking at","comparing","researching"],"replacing":["replacing","migrating from","switching from"],"ai_interest":["ai ","artificial intelligence","machine learning"]}
def create_buying_signal_detector_worker(db_factory) -> BaseWorker:
    return BuyingSignalDetectorWorker(WorkerConfig(name="buying_signal_detector", description="Detects buying signals from content", priority=WorkerPriority.HIGH, concurrency=2, max_retries=3, schedule=ScheduleType.EVENT_TRIGGERED, supported_events=[e.value for e in WORKER_EVENT_SUBSCRIPTIONS["buying_signal_detector"]], capabilities=["buying_signal_detection"]), db_factory)
class BuyingSignalDetectorWorker(BaseWorker):
    async def execute(self) -> None:
        db = self._db_factory()
        try:
            from app.infrastructure.db.knowledge_graph import KnowledgeFact
            from app.application.knowledge.service import KnowledgeService
            knowledge = KnowledgeService(db)
            facts = db.query(KnowledgeFact).filter(KnowledgeFact.entity_type.in_(["company","signal","transcript"]), KnowledgeFact.created_at.isnot(None)).order_by(KnowledgeFact.created_at.desc()).limit(30).all()
            for fact in facts:
                text = f"{fact.key} {fact.value}".lower()
                for sig_type, keywords in SIGNAL_KW.items():
                    for kw in keywords:
                        if kw in text:
                            knowledge.set_fact(entity_type=fact.entity_type, entity_id=fact.entity_id, key=f"buying_signal_{sig_type}", value="true", source="buying_signal_detector_worker", confidence=0.6)
                            self._metrics.facts_created += 1
                            break
        finally: db.close()
