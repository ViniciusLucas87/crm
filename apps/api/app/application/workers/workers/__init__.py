"""Autonomous Knowledge Workers — All 12 Workers"""
from app.application.workers.workers.company_enrichment import create_company_enrichment_worker
from app.application.workers.workers.fact_verification import create_fact_verification_worker
from app.application.workers.workers.entity_resolution import create_entity_resolution_worker
from app.application.workers.workers.relationship_discovery import create_relationship_discovery_worker
from app.application.workers.workers.technology_detection import create_technology_detection_worker
from app.application.workers.workers.buying_signal_detector import create_buying_signal_detector_worker
from app.application.workers.workers.knowledge_decay import create_knowledge_decay_worker
from app.application.workers.workers.reasoning import create_reasoning_worker
from app.application.workers.workers.timeline_generator import create_timeline_generator_worker
from app.application.workers.workers.opportunity_scoring import create_opportunity_scoring_worker
from app.application.workers.workers.search_indexer import create_search_indexer_worker
from app.application.workers.workers.recommendation_engine import create_recommendation_engine_worker

ALL_WORKER_FACTORIES = [create_company_enrichment_worker, create_fact_verification_worker,
    create_entity_resolution_worker, create_relationship_discovery_worker,
    create_technology_detection_worker, create_buying_signal_detector_worker,
    create_knowledge_decay_worker, create_reasoning_worker,
    create_timeline_generator_worker, create_opportunity_scoring_worker,
    create_search_indexer_worker, create_recommendation_engine_worker]

__all__ = ["ALL_WORKER_FACTORIES"] + [f.__name__ for f in ALL_WORKER_FACTORIES]
