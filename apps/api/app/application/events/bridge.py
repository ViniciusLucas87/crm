"""
Event Bridge — Wire existing CRUD operations into the Worker Event Bus.

Every create/update/delete in the system publishes an immutable event
so that Autonomous Knowledge Workers can react.

Usage (in any route):
    from app.application.events.bridge import emit
    emit(db, EventType.COMPANY_CREATED, "company", new_company.id, {"name": new_company.name})
"""

from __future__ import annotations

import logging
import os
from typing import Any

from sqlalchemy.orm import Session

from app.application.workers.persistence import create_worker_job
from app.application.workers.events import Event, EventBus, EventType
from app.application.workers.events import WORKER_EVENT_SUBSCRIPTIONS

logger = logging.getLogger(__name__)

QUEUE_BY_WORKER = {
    "company_enrichment": "normal",
    "fact_verification": "high",
    "entity_resolution": "normal",
    "relationship_discovery": "normal",
    "technology_detection": "normal",
    "buying_signal_detector": "high",
    "knowledge_decay": "low",
    "reasoning": "normal",
    "timeline_generator": "low",
    "opportunity_scoring": "high",
    "search_indexer": "background",
    "recommendation_engine": "normal",
}


def emit(
    db: Session,
    event_type: EventType,
    entity_type: str,
    entity_id: int,
    payload: dict[str, Any] | None = None,
    source: str = "api",
) -> None:
    """Publish an event to the Knowledge Graph event log.

    Non-blocking — failures are logged but never raised.
    """
    try:
        bus = EventBus(db)
        bus.publish(Event(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload or {},
            source=source,
        ))
        _dispatch_workers(db, event_type, entity_type, entity_id, payload or {})
    except Exception as exc:
        logger.warning(f"Failed to emit {event_type.value} for {entity_type}#{entity_id}: {exc}")


def _dispatch_workers(
    db: Session,
    event_type: EventType,
    entity_type: str,
    entity_id: int,
    payload: dict[str, Any],
) -> None:
    from celery import Celery

    redis_password = os.getenv("REDIS_PASSWORD", "redis_dev")
    broker_url = f"redis://:{redis_password}@redis:6379/0"
    celery = Celery("pns_worker", broker=broker_url)

    for worker_name, subscribed_events in WORKER_EVENT_SUBSCRIPTIONS.items():
        if event_type not in subscribed_events:
            continue
        queue = QUEUE_BY_WORKER.get(worker_name, "normal")
        job = create_worker_job(
            db,
            worker_name=worker_name,
            queue_name=queue,
            trigger_type="event",
            event_type=event_type.value,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload,
            priority=queue,
        )
        try:
            async_result = celery.send_task(
                f"workers.{worker_name}",
                kwargs={
                    "event_type": event_type.value,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "payload": payload,
                    "job_id": job.id,
                },
                queue=queue,
            )
            job.task_id = async_result.id
            db.commit()
            logger.info(
                "Dispatched %s for %s/%s#%s to queue=%s task_id=%s",
                worker_name,
                event_type.value,
                entity_type,
                entity_id,
                queue,
                async_result.id,
            )
        except Exception as exc:
            job.status = "failed"
            db.commit()
            logger.warning(
                "Failed to dispatch %s for %s/%s#%s: %s",
                worker_name,
                event_type.value,
                entity_type,
                entity_id,
                exc,
            )
