"""
Demand Intelligence Engine — Signal Pipeline

Transforms raw signals → classified signals → Knowledge Graph facts → CRM leads.

Architecture:
    Signal Provider → RawSignal → classify() → ClassifiedSignal
        → Knowledge Graph (facts + relationships)
        → Lead (optional auto-import)
        → Demand Dashboard
"""

import json
import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.application.demand.provider import (
    ClassifiedSignal, RawSignal, SignalSource, classify_signal,
    PainType, Urgency, RecommendedAction,
)
from app.application.knowledge.service import KnowledgeService
from app.infrastructure.db.demand_signal import DemandSignal

logger = logging.getLogger(__name__)


class SignalPipeline:
    """End-to-end signal processing pipeline.

    Handles: classification → knowledge graph persistence → lead generation.
    """

    def __init__(self, db: Session):
        self._db = db
        self._knowledge = KnowledgeService(db)

    def process(self, raw: RawSignal) -> ClassifiedSignal:
        """Process a raw signal through the entire pipeline."""
        # 1. Classify
        signal = classify_signal(raw)

        # 2. Write to Knowledge Graph
        self._to_knowledge_graph(signal)

        # 3. Score
        signal.lead_score = self._calculate_lead_score(signal)
        signal.recommended_action = self._determine_action(signal.lead_score)

        # 4. Record event
        self._knowledge.record_event(
            entity_type="signal", entity_id=0,
            event_type="signal_processed",
            description=f"Signal from {signal.source.value}: {signal.title[:100]}",
            payload_json=json.dumps({
                "pain_type": signal.pain_type.value if signal.pain_type else None,
                "lead_score": signal.lead_score,
                "action": signal.recommended_action.value,
            }),
        )

        return signal

    def _to_knowledge_graph(self, signal: ClassifiedSignal):
        """Write signal data to the Knowledge Graph."""
        entity_id = hash(signal.source_url) & 0x7FFFFFFF

        facts = [
            ("source_url", signal.source_url, signal.confidence),
            ("pain_type", signal.pain_type.value if signal.pain_type else "unknown", signal.confidence),
            ("buying_intent", str(signal.buying_intent), signal.confidence),
            ("lead_score", str(signal.lead_score), signal.confidence),
            ("recommended_action", signal.recommended_action.value, signal.confidence),
        ]

        if signal.company_name:
            facts.append(("company_name", signal.company_name, signal.confidence))
        if signal.author:
            facts.append(("author", signal.author, signal.confidence))
        if signal.author_title:
            facts.append(("author_title", signal.author_title, signal.confidence))
        if signal.location:
            facts.append(("location", signal.location, signal.confidence))

        for key, value, conf in facts:
            try:
                self._knowledge.set_fact(
                    entity_type="signal", entity_id=entity_id,
                    key=key, value=value,
                    source="demand_engine", confidence=conf,
                )
            except Exception:
                pass  # Already exists

        # Add technology/competitor relationships if company known
        if signal.company_name and signal.technologies_mentioned:
            for tech in signal.technologies_mentioned[:3]:
                try:
                    self._knowledge.set_fact(
                        entity_type="signal", entity_id=entity_id,
                        key=f"tech_mention_{tech}", value=tech,
                        source="demand_engine", confidence=0.6,
                    )
                except Exception:
                    pass

    def _calculate_lead_score(self, signal: ClassifiedSignal) -> int:
        """Calculate comprehensive lead score from multiple dimensions."""
        score = 0

        # Intent strength (0-30)
        if signal.buying_intent >= 80:
            score += 30
        elif signal.buying_intent >= 60:
            score += 20
        elif signal.buying_intent >= 40:
            score += 10

        # Pain severity (0-20)
        critical_pains = {PainType.REPLACING_SOFTWARE, PainType.ERP_REPLACEMENT, PainType.EVALUATING_VENDORS}
        high_pains = {PainType.SOFTWARE_NEED, PainType.AI_LOOKING, PainType.INSPECTION_SOFTWARE}
        if signal.pain_type in critical_pains:
            score += 20
        elif signal.pain_type in high_pains:
            score += 12

        # Company identified (0-15)
        if signal.company_name:
            score += 15

        # Decision maker identified (0-15)
        if signal.author and signal.author_title:
            score += 15
        elif signal.author:
            score += 8

        # Recency (0-10) — signals from last 30 days
        try:
            if signal.published_at:
                published = datetime.fromisoformat(signal.published_at.replace("Z", "+00:00"))
                days_ago = (datetime.now(UTC) - published).days
                if days_ago <= 1: score += 10
                elif days_ago <= 7: score += 7
                elif days_ago <= 30: score += 4
        except Exception:
            pass

        # Confidence adjustment (0-10)
        score += int(signal.confidence * 10)

        return min(100, max(0, score))

    def _determine_action(self, score: int) -> RecommendedAction:
        if score >= 85: return RecommendedAction.PHONE_CALL
        if score >= 70: return RecommendedAction.CREATE_PROPOSAL
        if score >= 60: return RecommendedAction.LINKEDIN_MESSAGE
        if score >= 45: return RecommendedAction.COLD_EMAIL
        if score >= 30: return RecommendedAction.MONITOR
        return RecommendedAction.NOT_QUALIFIED


# ── DB-backed signal persistence ──


def store_signal(signal: ClassifiedSignal, db: Session) -> dict[str, Any]:
    """Persist a processed signal to the database."""
    import json as _json

    ds = DemandSignal(
        source=signal.source.value,
        source_url=signal.source_url,
        title=signal.title,
        content=signal.content[:2000],
        author=signal.author,
        author_title=signal.author_title,
        company_name=signal.company_name,
        location=signal.location,
        pain_type=signal.pain_type.value if signal.pain_type else None,
        urgency=signal.urgency.value,
        buying_intent=signal.buying_intent,
        lead_score=signal.lead_score,
        recommended_action=signal.recommended_action.value,
        confidence=signal.confidence,
        technologies=_json.dumps(signal.technologies_mentioned),
        keywords=_json.dumps(signal.keywords),
        published_at=(
            datetime.fromisoformat(signal.published_at.replace("Z", "+00:00"))
            if signal.published_at else None
        ),
        processed_at=datetime.now(UTC),
    )
    db.add(ds)
    db.commit()
    db.refresh(ds)

    return {
        "id": ds.id,
        "source": ds.source,
        "source_url": ds.source_url,
        "title": ds.title,
        "content": ds.content,
        "author": ds.author,
        "company_name": ds.company_name,
        "pain_type": ds.pain_type,
        "urgency": ds.urgency,
        "buying_intent": ds.buying_intent,
        "lead_score": ds.lead_score,
        "recommended_action": ds.recommended_action,
        "confidence": ds.confidence,
        "technologies": signal.technologies_mentioned,
        "keywords": signal.keywords,
        "processed_at": ds.processed_at.isoformat() if ds.processed_at else None,
    }


def get_signals(db: Session, filters: dict[str, Any] | None = None, limit: int = 50) -> list[dict[str, Any]]:
    """Query signals from the database with optional filters."""
    import json as _json

    q = db.query(DemandSignal)
    if filters:
        if "pain_type" in filters:
            q = q.filter(DemandSignal.pain_type == filters["pain_type"])
        if "source" in filters:
            q = q.filter(DemandSignal.source == filters["source"])
        if "min_score" in filters:
            q = q.filter(DemandSignal.lead_score >= filters["min_score"])
    q = q.order_by(DemandSignal.lead_score.desc(), DemandSignal.created_at.desc()).limit(limit)
    return [_signal_to_dict(s) for s in q.all()]


def get_demand_stats(db: Session) -> dict[str, Any]:
    """Compute demand intelligence statistics from the database."""
    total = db.query(func.count(DemandSignal.id)).scalar() or 0
    if total == 0:
        return {"total_signals": 0, "by_pain": {}, "by_source": {}, "high_intent": 0, "avg_score": 0, "top_signals": []}

    high_intent = db.query(func.count(DemandSignal.id)).filter(DemandSignal.lead_score >= 70).scalar() or 0
    avg_score = db.query(func.avg(DemandSignal.lead_score)).scalar() or 0

    by_pain_rows = db.query(DemandSignal.pain_type, func.count(DemandSignal.id)).group_by(DemandSignal.pain_type).all()
    by_pain = {row[0] or "unknown": row[1] for row in by_pain_rows}

    by_source_rows = db.query(DemandSignal.source, func.count(DemandSignal.id)).group_by(DemandSignal.source).all()
    by_source = {row[0]: row[1] for row in by_source_rows}

    top = db.query(DemandSignal).order_by(DemandSignal.lead_score.desc()).limit(10).all()

    return {
        "total_signals": total,
        "by_pain": by_pain,
        "by_source": by_source,
        "high_intent": high_intent,
        "avg_score": round(avg_score, 1),
        "top_signals": [_signal_to_dict(s) for s in top],
    }


def _signal_to_dict(ds: DemandSignal) -> dict[str, Any]:
    """Convert a DemandSignal model to a dictionary."""
    import json as _json

    return {
        "id": ds.id,
        "source": ds.source,
        "source_url": ds.source_url,
        "title": ds.title,
        "content": ds.content,
        "author": ds.author,
        "author_title": ds.author_title,
        "company_name": ds.company_name,
        "location": ds.location,
        "pain_type": ds.pain_type,
        "urgency": ds.urgency,
        "buying_intent": ds.buying_intent,
        "lead_score": ds.lead_score,
        "recommended_action": ds.recommended_action,
        "confidence": ds.confidence,
        "technologies": _json.loads(ds.technologies) if ds.technologies else [],
        "keywords": _json.loads(ds.keywords) if ds.keywords else [],
        "published_at": ds.published_at.isoformat() if ds.published_at else None,
        "processed_at": ds.processed_at.isoformat() if ds.processed_at else None,
        "created_at": ds.created_at.isoformat() if ds.created_at else None,
    }
