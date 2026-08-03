"""
Knowledge Service — Central Graph API.

This is the single entry point for ALL AI modules to read from and write to
the Knowledge Graph. No module should own its own business memory.

Architecture:
    KnowledgeService
        ├─ get_facts(entity_type, entity_id) → list[KnowledgeFact]
        ├─ get_relationships(entity_type, entity_id) → list[KnowledgeRelationship]
        ├─ get_events(entity_type, entity_id) → list[KnowledgeEvent]
        ├─ get_snapshot(entity_type, entity_id) → full knowledge bundle
        ├─ set_fact(...) → upsert with versioning
        ├─ add_relationship(...) → create connection
        └─ record_event(...) → immutable log entry
"""

import json
import logging
from datetime import UTC, datetime
from typing import Any, Sequence

from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import Session

from app.infrastructure.db.knowledge_graph import (
    KnowledgeFact,
    KnowledgeFactHistory,
    KnowledgeRelationship,
    KnowledgeEvent,
)
from app.application.workers.events import EventType

logger = logging.getLogger(__name__)


class KnowledgeService:
    """Central Knowledge Graph API."""

    def __init__(self, db: Session):
        self._db = db

    # ── Facts ──

    def get_facts(self, entity_type: str, entity_id: int) -> list[KnowledgeFact]:
        return list(self._db.scalars(
            select(KnowledgeFact).where(
                KnowledgeFact.entity_type == entity_type,
                KnowledgeFact.entity_id == entity_id,
                KnowledgeFact.status == "active",
            )
        ).all())

    def get_fact(self, entity_type: str, entity_id: int, key: str) -> KnowledgeFact | None:
        return self._db.scalar(
            select(KnowledgeFact).where(
                KnowledgeFact.entity_type == entity_type,
                KnowledgeFact.entity_id == entity_id,
                KnowledgeFact.key == key,
                KnowledgeFact.status == "active",
            )
        )

    def set_fact(
        self,
        entity_type: str,
        entity_id: int,
        key: str,
        value: str,
        *,
        source: str = "system",
        source_detail: str | None = None,
        confidence: float = 0.5,
        value_type: str = "string",
        created_by: str | None = None,
    ) -> KnowledgeFact:
        """Upsert a fact with automatic versioning.

        If the fact already exists, creates a history entry before updating.
        Returns the fact (new or updated).
        """
        existing = self._db.scalar(
            select(KnowledgeFact).where(
                KnowledgeFact.entity_type == entity_type,
                KnowledgeFact.entity_id == entity_id,
                KnowledgeFact.key == key,
            )
        )

        if existing:
            new_value = str(value)
            changed = any((
                existing.value != new_value,
                existing.confidence != confidence,
                existing.source != source,
                existing.source_detail != source_detail,
                existing.value_type != value_type,
                existing.status != "active",
                existing.manual_override,
            ))

            # Worker tasks are intentionally idempotent. Emitting FACT_UPDATED for
            # a no-op write creates recursive event fan-out between workers.
            if not changed:
                return existing

            # Record history before updating
            if existing.value != new_value or existing.confidence != confidence:
                history = KnowledgeFactHistory(
                    fact_id=existing.id,
                    previous_value=existing.value,
                    new_value=new_value,
                    previous_confidence=existing.confidence,
                    new_confidence=confidence,
                    previous_source=existing.source,
                    new_source=source,
                    changed_by=created_by,
                )
                self._db.add(history)

            existing.value = new_value
            existing.confidence = confidence
            existing.source = source
            existing.source_detail = source_detail
            existing.value_type = value_type
            existing.updated_by = created_by
            existing.updated_at = datetime.now(UTC)
            if existing.manual_override:
                existing.manual_override = False  # Reset override if system updates
            self._db.flush()

            self.record_event(
                entity_type=entity_type, entity_id=entity_id,
                event_type="fact_updated",
                description=f"Fact '{key}' updated: {existing.value}",
                payload_json=json.dumps({"key": key, "value": new_value, "confidence": confidence}),
            )
            return existing

        # Create new fact
        fact = KnowledgeFact(
            entity_type=entity_type,
            entity_id=entity_id,
            key=key,
            value=str(value),
            value_type=value_type,
            source=source,
            source_detail=source_detail,
            confidence=confidence,
            created_by=created_by,
            updated_by=created_by,
        )
        self._db.add(fact)
        self._db.flush()

        self.record_event(
            entity_type=entity_type, entity_id=entity_id,
            event_type="fact_created",
            description=f"Fact '{key}' created: {value}",
            payload_json=json.dumps({"key": key, "value": str(value), "confidence": confidence}),
        )
        return fact

    def get_fact_history(self, fact_id: int) -> list[KnowledgeFactHistory]:
        return list(self._db.scalars(
            select(KnowledgeFactHistory).where(KnowledgeFactHistory.fact_id == fact_id).order_by(KnowledgeFactHistory.created_at.desc())
        ).all())

    def search_facts(self, query: str, limit: int = 50) -> list[KnowledgeFact]:
        return list(self._db.scalars(
            select(KnowledgeFact).where(
                and_(
                    KnowledgeFact.status == "active",
                    or_(
                        KnowledgeFact.key.ilike(f"%{query}%"),
                        KnowledgeFact.value.ilike(f"%{query}%"),
                    ),
                )
            ).order_by(KnowledgeFact.confidence.desc()).limit(limit)
        ).all())

    def get_facts_by_source(self, source: str, limit: int = 50) -> list[KnowledgeFact]:
        return list(self._db.scalars(
            select(KnowledgeFact).where(KnowledgeFact.source == source, KnowledgeFact.status == "active").limit(limit)
        ).all())

    # ── Relationships ──

    def get_relationships(self, entity_type: str, entity_id: int) -> list[KnowledgeRelationship]:
        """Get all relationships for an entity (both directions)."""
        return list(self._db.scalars(
            select(KnowledgeRelationship).where(
                and_(
                    KnowledgeRelationship.status == "active",
                    or_(
                        and_(KnowledgeRelationship.from_type == entity_type, KnowledgeRelationship.from_id == entity_id),
                        and_(KnowledgeRelationship.to_type == entity_type, KnowledgeRelationship.to_id == entity_id),
                    ),
                )
            )
        ).all())

    def add_relationship(
        self,
        from_type: str, from_id: int,
        relationship_type: str,
        to_type: str, to_id: int,
        *,
        confidence: float = 0.5,
        source: str = "system",
        metadata: dict | None = None,
    ) -> KnowledgeRelationship:
        existing = self._db.scalar(
            select(KnowledgeRelationship).where(
                KnowledgeRelationship.from_type == from_type,
                KnowledgeRelationship.from_id == from_id,
                KnowledgeRelationship.to_type == to_type,
                KnowledgeRelationship.to_id == to_id,
                KnowledgeRelationship.relationship_type == relationship_type,
            )
        )
        if existing:
            existing.metadata_json = json.dumps(metadata) if metadata else existing.metadata_json
            existing.confidence = confidence
            self._db.flush()
            return existing

        rel = KnowledgeRelationship(
            from_type=from_type, from_id=from_id,
            relationship_type=relationship_type,
            to_type=to_type, to_id=to_id,
            confidence=confidence, source=source,
            metadata_json=json.dumps(metadata) if metadata else None,
        )
        self._db.add(rel)
        self._db.flush()

        self.record_event(
            entity_type=from_type, entity_id=from_id,
            event_type="relationship_created",
            description=f"{from_type}#{from_id} --[{relationship_type}]--> {to_type}#{to_id}",
        )
        return rel

    def remove_relationship(self, relationship_id: int) -> None:
        rel = self._db.get(KnowledgeRelationship, relationship_id)
        if rel:
            rel.status = "removed"
            self._db.flush()
            self.record_event(
                entity_type=rel.from_type, entity_id=rel.from_id,
                event_type="relationship_removed",
                description=f"Relationship {rel.relationship_type} removed",
            )

    # ── Events ──

    def get_events(self, entity_type: str, entity_id: int, limit: int = 100) -> list[KnowledgeEvent]:
        return list(self._db.scalars(
            select(KnowledgeEvent).where(
                KnowledgeEvent.entity_type == entity_type,
                KnowledgeEvent.entity_id == entity_id,
            ).order_by(KnowledgeEvent.created_at.desc()).limit(limit)
        ).all())

    def record_event(
        self,
        entity_type: str,
        entity_id: int,
        event_type: str,
        description: str = "",
        payload_json: str | None = None,
        actor_type: str = "system",
        actor_id: str | None = None,
        organization_id: int | None = None,
    ) -> KnowledgeEvent:
        event = KnowledgeEvent(
            entity_type=entity_type, entity_id=entity_id,
            event_type=event_type, description=description,
            payload_json=payload_json, actor_type=actor_type,
            actor_id=actor_id, organization_id=organization_id,
        )
        self._db.add(event)
        self._db.flush()
        try:
            matched_event = next((member for member in EventType if member.value == event_type), None)
            if matched_event is not None:
                from app.application.events.bridge import _dispatch_workers

                _dispatch_workers(
                    self._db,
                    matched_event,
                    entity_type,
                    entity_id,
                    json.loads(payload_json) if payload_json else {},
                )
        except Exception as exc:
            logger.debug("Skipping worker dispatch for knowledge event %s: %s", event_type, exc)
        return event

    def get_recent_events(self, limit: int = 50) -> list[KnowledgeEvent]:
        return list(self._db.scalars(
            select(KnowledgeEvent).order_by(KnowledgeEvent.created_at.desc()).limit(limit)
        ).all())

    # ── Snapshot — full knowledge bundle ──

    def get_snapshot(self, entity_type: str, entity_id: int) -> dict[str, Any]:
        """Return complete knowledge about an entity.

        This is the single endpoint every AI module should call to get
        context about a company, person, opportunity, etc.
        """
        facts = self.get_facts(entity_type, entity_id)
        relationships = self.get_relationships(entity_type, entity_id)
        events = self.get_events(entity_type, entity_id, limit=20)

        return {
            "entity": {"type": entity_type, "id": entity_id},
            "facts": [
                {
                    "key": f.key,
                    "value": f.value,
                    "value_type": f.value_type,
                    "source": f.source,
                    "source_detail": f.source_detail,
                    "confidence": f.confidence,
                    "verified": f.verified,
                    "updated_at": f.updated_at.isoformat() if f.updated_at else None,
                }
                for f in facts
            ],
            "relationships": [
                {
                    "from": f"{r.from_type}#{r.from_id}",
                    "type": r.relationship_type,
                    "to": f"{r.to_type}#{r.to_id}",
                    "confidence": r.confidence,
                }
                for r in relationships
            ],
            "recent_events": [
                {
                    "type": e.event_type,
                    "description": e.description,
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                }
                for e in events
            ],
            "stats": {
                "total_facts": len(facts),
                "avg_confidence": sum(f.confidence for f in facts) / len(facts) if facts else 0,
                "total_relationships": len(relationships),
                "total_events": len(events),
            },
        }

    # ── Graph statistics ──

    def get_graph_stats(self) -> dict[str, Any]:
        return {
            "total_facts": self._db.scalar(select(func.count()).select_from(KnowledgeFact).where(KnowledgeFact.status == "active")) or 0,
            "total_relationships": self._db.scalar(select(func.count()).select_from(KnowledgeRelationship).where(KnowledgeRelationship.status == "active")) or 0,
            "total_events": self._db.scalar(select(func.count()).select_from(KnowledgeEvent)) or 0,
        }
