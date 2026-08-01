"""
Demand Intelligence API — Discover buying signals across the internet.

Endpoints:
  POST /demand/search          — execute a search across all providers
  GET  /demand/signals         — list processed signals
  GET  /demand/stats           — demand statistics
  GET  /demand/pain-types      — list all pain types with patterns
  POST /demand/classify        — classify a raw signal (test endpoint)
  POST /demand/process         — full pipeline: classify → graph → store
"""

import logging
import asyncio

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.application.demand.pipeline import (
    SignalPipeline, get_signals, get_demand_stats, store_signal,
)
from app.application.demand.live_providers import ProviderRegistry
from app.application.demand.provider import (
    BUYING_SIGNAL_PATTERNS, SIGNAL_PRIORITY_SCORES,
    PainType, RawSignal, SignalSource, classify_signal,
)
from app.infrastructure.auth.clerk import AuthContext, require_permission
from app.infrastructure.db.session import get_db_session

logger = logging.getLogger(__name__)
router = APIRouter()

# ── Request Models ──

class SearchRequest(BaseModel):
    query: str
    sources: list[str] | None = None  # e.g., ["reddit", "linkedin", "indeed"]
    industries: list[str] | None = None
    locations: list[str] | None = None
    pain_types: list[str] | None = None
    min_score: int = 0


class RawSignalInput(BaseModel):
    source: str
    source_url: str = ""
    title: str
    content: str
    author: str | None = None
    author_title: str | None = None
    company_name: str | None = None
    published_at: str | None = None
    location: str | None = None


# ═══════════════════════════════════════════════════════════
# SEARCH
# ═══════════════════════════════════════════════════════════

@router.post("/search")
def search_signals(
    req: SearchRequest,
    auth: AuthContext = Depends(require_permission("read:companies")),
    db: Session = Depends(get_db_session),
):
    """Execute a search across signal providers.

    Uses live providers with graceful fallback. No hardcoded mock signals.
    """
    registry = ProviderRegistry(db)
    raw_signals = asyncio.run(registry.search(
        req.query,
        sources=req.sources,
        filters={
            "industries": req.industries,
            "locations": req.locations,
            "pain_types": req.pain_types,
            "min_score": req.min_score,
        },
    ))
    results = []
    for raw in raw_signals[:25]:
        classified = classify_signal(raw)
        if req.min_score and classified.lead_score < req.min_score:
            continue
        stored = store_signal(classified, db)
        results.append(stored)

    return {"results": results, "total": len(results)}


# ═══════════════════════════════════════════════════════════
# SIGNALS
# ═══════════════════════════════════════════════════════════

@router.get("/signals")
def list_signals(
    pain_type: str | None = Query(None),
    source: str | None = Query(None),
    min_score: int = Query(0),
    limit: int = Query(50, ge=1, le=200),
    auth: AuthContext = Depends(require_permission("read:companies")),
    db: Session = Depends(get_db_session),
):
    """List processed signals with optional filters."""
    filters = {}
    if pain_type: filters["pain_type"] = pain_type
    if source: filters["source"] = source
    if min_score: filters["min_score"] = min_score
    return {"signals": get_signals(db, filters, limit)}


@router.get("/stats")
def get_stats(
    auth: AuthContext = Depends(require_permission("read:companies")),
    db: Session = Depends(get_db_session),
):
    """Get demand intelligence statistics."""
    return get_demand_stats(db)


@router.get("/pain-types")
def list_pain_types(
    auth: AuthContext = Depends(require_permission("read:companies")),
):
    """List all pain types with keyword patterns and priority scores."""
    return {
        "pain_types": [
            {
                "type": pt.value,
                "patterns": BUYING_SIGNAL_PATTERNS.get(pt, []),
                "priority_score": SIGNAL_PRIORITY_SCORES.get(pt, 40),
            }
            for pt in PainType
        ]
    }


@router.post("/classify")
def classify_raw_signal(
    req: RawSignalInput,
    auth: AuthContext = Depends(require_permission("read:companies")),
):
    """Classify a raw signal (for testing)."""
    source = next((ss for ss in SignalSource if ss.value == req.source), SignalSource.OTHER)
    raw = RawSignal(
        source=source, source_url=req.source_url,
        title=req.title, content=req.content,
        author=req.author, author_title=req.author_title,
        company_name=req.company_name, published_at=req.published_at,
        location=req.location,
    )
    classified = classify_signal(raw)
    return {
        "pain_type": classified.pain_type.value if classified.pain_type else None,
        "buying_intent": classified.buying_intent,
        "lead_score": classified.lead_score,
        "urgency": classified.urgency.value,
        "recommended_action": classified.recommended_action.value,
        "confidence": classified.confidence,
        "keywords": classified.keywords,
    }


@router.post("/process")
def process_signal(
    req: RawSignalInput,
    auth: AuthContext = Depends(require_permission("write:companies")),
    db: Session = Depends(get_db_session),
):
    """Full pipeline: classify → knowledge graph → store."""
    source = next((ss for ss in SignalSource if ss.value == req.source), SignalSource.OTHER)
    raw = RawSignal(
        source=source, source_url=req.source_url,
        title=req.title, content=req.content,
        author=req.author, author_title=req.author_title,
        company_name=req.company_name, published_at=req.published_at,
        location=req.location,
    )
    pipeline = SignalPipeline(db)
    signal = pipeline.process(raw)
    stored = store_signal(signal, db)
    return stored
