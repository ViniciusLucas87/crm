"""Autonomous Knowledge Workers — Event System"""
from __future__ import annotations
import json, logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class EventType(str, Enum):
    COMPANY_CREATED = "company_created"; COMPANY_UPDATED = "company_updated"; COMPANY_ARCHIVED = "company_archived"
    CONTACT_CREATED = "contact_created"; CONTACT_UPDATED = "contact_updated"
    LEAD_IMPORTED = "lead_imported"; LEAD_CONVERTED = "lead_converted"
    OPPORTUNITY_CREATED = "opportunity_created"; OPPORTUNITY_UPDATED = "opportunity_updated"
    OPPORTUNITY_WON = "opportunity_won"; OPPORTUNITY_LOST = "opportunity_lost"
    FACT_CREATED = "fact_created"; FACT_UPDATED = "fact_updated"; FACT_EXPIRED = "fact_expired"
    FACT_VERIFIED = "fact_verified"; FACT_CONFLICT = "fact_conflict"
    RELATIONSHIP_CREATED = "relationship_created"; RELATIONSHIP_REMOVED = "relationship_removed"
    ENTITY_MERGED = "entity_merged"; KNOWLEDGE_DECAYED = "knowledge_decayed"
    TRANSCRIPT_COMPLETED = "transcript_completed"; CALL_STARTED = "call_started"; CALL_ENDED = "call_ended"
    EMAIL_SENT = "email_sent"; MEETING_SCHEDULED = "meeting_scheduled"
    PROPOSAL_GENERATED = "proposal_generated"; INSIGHT_GENERATED = "insight_generated"
    RECOMMENDATION_CREATED = "recommendation_created"; BUYING_SIGNAL_DETECTED = "buying_signal_detected"
    TASK_COMPLETED = "task_completed"; TASK_CREATED = "task_created"
    PIPELINE_STAGE_CHANGED = "pipeline_stage_changed"; ACTIVITY_LOGGED = "activity_logged"
    WORKER_STARTED = "worker_started"; WORKER_STOPPED = "worker_stopped"
    WORKER_ERROR = "worker_error"; SYSTEM_ALERT = "system_alert"

WORKER_EVENT_SUBSCRIPTIONS: dict[str, list[EventType]] = {
    "company_enrichment": [EventType.COMPANY_CREATED, EventType.COMPANY_UPDATED, EventType.LEAD_IMPORTED, EventType.FACT_EXPIRED],
    # FACT_UPDATED is intentionally excluded: verification updates confidence,
    # which would otherwise dispatch another verification job indefinitely.
    "fact_verification": [EventType.FACT_CREATED, EventType.TRANSCRIPT_COMPLETED, EventType.KNOWLEDGE_DECAYED],
    "entity_resolution": [EventType.COMPANY_CREATED, EventType.LEAD_IMPORTED, EventType.CONTACT_CREATED],
    "relationship_discovery": [EventType.FACT_CREATED, EventType.TRANSCRIPT_COMPLETED, EventType.PROPOSAL_GENERATED, EventType.MEETING_SCHEDULED],
    "technology_detection": [EventType.COMPANY_CREATED, EventType.COMPANY_UPDATED, EventType.TRANSCRIPT_COMPLETED, EventType.LEAD_IMPORTED],
    "buying_signal_detector": [EventType.BUYING_SIGNAL_DETECTED, EventType.TRANSCRIPT_COMPLETED, EventType.EMAIL_SENT, EventType.MEETING_SCHEDULED, EventType.PROPOSAL_GENERATED, EventType.TASK_CREATED],
    # Decay is a daily maintenance job. Event-triggering it on every fact write
    # creates a self-amplifying update loop and unnecessary database load.
    "knowledge_decay": [],
    "reasoning": [EventType.FACT_CREATED, EventType.FACT_VERIFIED, EventType.RELATIONSHIP_CREATED, EventType.TRANSCRIPT_COMPLETED, EventType.BUYING_SIGNAL_DETECTED, EventType.OPPORTUNITY_UPDATED],
    "timeline_generator": [EventType.COMPANY_CREATED, EventType.LEAD_IMPORTED, EventType.CALL_ENDED, EventType.PROPOSAL_GENERATED, EventType.OPPORTUNITY_WON, EventType.OPPORTUNITY_LOST, EventType.TASK_COMPLETED, EventType.PIPELINE_STAGE_CHANGED],
    "opportunity_scoring": [EventType.OPPORTUNITY_CREATED, EventType.OPPORTUNITY_UPDATED, EventType.FACT_CREATED, EventType.BUYING_SIGNAL_DETECTED, EventType.CALL_ENDED, EventType.PROPOSAL_GENERATED],
    "search_indexer": [EventType.FACT_CREATED, EventType.FACT_UPDATED, EventType.RELATIONSHIP_CREATED, EventType.INSIGHT_GENERATED, EventType.TRANSCRIPT_COMPLETED],
    "recommendation_engine": [EventType.FACT_CREATED, EventType.BUYING_SIGNAL_DETECTED, EventType.OPPORTUNITY_UPDATED, EventType.CALL_ENDED, EventType.PROPOSAL_GENERATED, EventType.INSIGHT_GENERATED],
}

@dataclass
class Event:
    event_type: EventType; entity_type: str; entity_id: int
    payload: dict[str, Any] = field(default_factory=dict)
    source: str = "system"; timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    correlation_id: str | None = None

class EventBus:
    def __init__(self, db: Session):
        self._db = db
        from app.application.knowledge.service import KnowledgeService
        self._knowledge = KnowledgeService(db)

    def publish(self, event: Event) -> None:
        try:
            self._knowledge.record_event(entity_type=event.entity_type, entity_id=event.entity_id,
                event_type=event.event_type.value,
                description=f"[{event.source}] {event.event_type.value}: {event.entity_type}#{event.entity_id}",
                payload_json=json.dumps({**event.payload, "source": event.source, "correlation_id": event.correlation_id}))
        except Exception as exc:
            logger.error(f"Failed to publish event: {exc}")

    def get_pending_events(self, event_types: list[EventType], limit: int = 10, since: datetime | None = None) -> list[dict[str, Any]]:
        from app.infrastructure.db.knowledge_graph import KnowledgeEvent
        type_values = [et.value for et in event_types]
        q = self._db.query(KnowledgeEvent).filter(KnowledgeEvent.event_type.in_(type_values))
        if since: q = q.filter(KnowledgeEvent.created_at > since)
        q = q.order_by(KnowledgeEvent.created_at.asc()).limit(limit)
        return [{"id": e.id, "event_type": e.event_type, "entity_type": e.entity_type, "entity_id": e.entity_id,
                 "description": e.description, "payload": json.loads(e.payload_json) if e.payload_json else {},
                 "created_at": e.created_at.isoformat() if e.created_at else None} for e in q.all()]
