"""
Knowledge Graph API — Central intelligence layer.

Endpoints:
  GET  /knowledge/snapshot/{entity_type}/{entity_id}  — full knowledge bundle
  GET  /knowledge/facts/{entity_type}/{entity_id}     — list facts
  POST /knowledge/facts                               — upsert fact
  GET  /knowledge/facts/{fact_id}/history             — fact version history
  GET  /knowledge/relationships/{entity_type}/{entity_id} — list relationships  
  POST /knowledge/relationships                       — add relationship
  GET  /knowledge/events/{entity_type}/{entity_id}    — list events
  GET  /knowledge/search?q=                           — search facts
  GET  /knowledge/stats                               — graph statistics
  GET  /knowledge/search?entity_type=&q=              — semantic search
"""

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.application.knowledge.service import KnowledgeService
from app.infrastructure.auth.clerk import AuthContext, require_permission
from app.infrastructure.db.session import get_db_session

router = APIRouter()

# ── Request Models ──

class SetFactRequest(BaseModel):
    entity_type: str
    entity_id: int
    key: str
    value: str
    source: str = "system"
    source_detail: str | None = None
    confidence: float = 0.5
    value_type: str = "string"

class AddRelationshipRequest(BaseModel):
    from_type: str
    from_id: int
    relationship_type: str
    to_type: str
    to_id: int
    confidence: float = 0.5
    source: str = "system"


# ═══════════════════════════════════════════════════════════
# KNOWLEDGE SNAPSHOT — single endpoint for AI context
# ═══════════════════════════════════════════════════════════

@router.get("/snapshot/{entity_type}/{entity_id}")
def get_snapshot(
    entity_type: str,
    entity_id: int,
    auth: AuthContext = Depends(require_permission("read:companies")),
    db: Session = Depends(get_db_session),
):
    """Return the complete knowledge bundle for any entity.

    This is the single endpoint every AI module should call to get context
    about a company, person, opportunity, etc.
    """
    svc = KnowledgeService(db)
    return svc.get_snapshot(entity_type, entity_id)


# ═══════════════════════════════════════════════════════════
# FACTS
# ═══════════════════════════════════════════════════════════

@router.get("/facts/{entity_type}/{entity_id}")
def get_facts(
    entity_type: str,
    entity_id: int,
    auth: AuthContext = Depends(require_permission("read:companies")),
    db: Session = Depends(get_db_session),
):
    svc = KnowledgeService(db)
    facts = svc.get_facts(entity_type, entity_id)
    return {
        "facts": [
            {
                "id": f.id, "key": f.key, "value": f.value,
                "source": f.source, "confidence": f.confidence,
                "verified": f.verified, "status": f.status,
                "updated_at": f.updated_at.isoformat() if f.updated_at else None,
            }
            for f in facts
        ]
    }


@router.post("/facts")
def set_fact(
    req: SetFactRequest,
    auth: AuthContext = Depends(require_permission("write:companies")),
    db: Session = Depends(get_db_session),
):
    svc = KnowledgeService(db)
    fact = svc.set_fact(
        entity_type=req.entity_type, entity_id=req.entity_id,
        key=req.key, value=req.value, source=req.source,
        source_detail=req.source_detail, confidence=req.confidence,
        value_type=req.value_type, created_by=auth.user_id,
    )
    return {"id": fact.id, "key": fact.key, "value": fact.value, "confidence": fact.confidence}


@router.get("/facts/{fact_id}/history")
def get_fact_history(
    fact_id: int,
    auth: AuthContext = Depends(require_permission("read:companies")),
    db: Session = Depends(get_db_session),
):
    svc = KnowledgeService(db)
    history = svc.get_fact_history(fact_id)
    return {
        "history": [
            {
                "previous_value": h.previous_value, "new_value": h.new_value,
                "previous_confidence": h.previous_confidence, "new_confidence": h.new_confidence,
                "changed_by": h.changed_by, "created_at": h.created_at.isoformat(),
            }
            for h in history
        ]
    }


# ═══════════════════════════════════════════════════════════
# RELATIONSHIPS
# ═══════════════════════════════════════════════════════════

@router.get("/relationships/{entity_type}/{entity_id}")
def get_relationships(
    entity_type: str,
    entity_id: int,
    auth: AuthContext = Depends(require_permission("read:companies")),
    db: Session = Depends(get_db_session),
):
    svc = KnowledgeService(db)
    rels = svc.get_relationships(entity_type, entity_id)
    return {
        "relationships": [
            {
                "id": r.id, "from": f"{r.from_type}#{r.from_id}",
                "type": r.relationship_type, "to": f"{r.to_type}#{r.to_id}",
                "confidence": r.confidence, "source": r.source,
            }
            for r in rels
        ]
    }


@router.post("/relationships")
def add_relationship(
    req: AddRelationshipRequest,
    auth: AuthContext = Depends(require_permission("write:companies")),
    db: Session = Depends(get_db_session),
):
    svc = KnowledgeService(db)
    rel = svc.add_relationship(
        from_type=req.from_type, from_id=req.from_id,
        relationship_type=req.relationship_type,
        to_type=req.to_type, to_id=req.to_id,
        confidence=req.confidence, source=req.source,
    )
    return {"id": rel.id, "relationship_type": rel.relationship_type}


# ═══════════════════════════════════════════════════════════
# EVENTS
# ═══════════════════════════════════════════════════════════

@router.get("/events/{entity_type}/{entity_id}")
def get_events(
    entity_type: str,
    entity_id: int,
    limit: int = Query(100, ge=1, le=500),
    auth: AuthContext = Depends(require_permission("read:companies")),
    db: Session = Depends(get_db_session),
):
    svc = KnowledgeService(db)
    events = svc.get_events(entity_type, entity_id, limit)
    return {
        "events": [
            {
                "id": e.id, "event_type": e.event_type,
                "description": e.description, "actor_type": e.actor_type,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in events
        ]
    }


# ═══════════════════════════════════════════════════════════
# SEARCH + STATS
# ═══════════════════════════════════════════════════════════

@router.get("/search")
def search_knowledge(
    q: str = Query(..., min_length=2),
    entity_type: str | None = Query(None),
    limit: int = Query(50),
    auth: AuthContext = Depends(require_permission("read:companies")),
    db: Session = Depends(get_db_session),
):
    svc = KnowledgeService(db)
    results = svc.search_facts(q, limit)
    return {
        "results": [
            {"key": f.key, "value": f.value, "entity": f"{f.entity_type}#{f.entity_id}",
             "confidence": f.confidence, "source": f.source}
            for f in results
        ]
    }


@router.get("/stats")
def get_stats(
    auth: AuthContext = Depends(require_permission("read:companies")),
    db: Session = Depends(get_db_session),
):
    svc = KnowledgeService(db)
    return svc.get_graph_stats()
