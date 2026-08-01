"""
AI Enrichment Endpoint.

Provides LLM-powered enrichment for existing AI page data.
Lightweight — enriches data already fetched by the page.
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.application.llm.enrichment import EnrichmentResult, get_enrichment_service
from app.infrastructure.auth.clerk import AuthContext, require_permission

router = APIRouter(prefix="/enrich", tags=["enrich"])


@router.post("/{enrichment_type}")
async def enrich_data(
    enrichment_type: str,
    request: Request,
    ctx: AuthContext = Depends(require_permission("companies:read")),
) -> dict:
    """Enrich structured data with LLM-generated insights."""
    body = await request.json()
    context = body.get("context", {})
    svc = get_enrichment_service()
    result = await svc.enrich(enrichment_type, context)
    return {
        "enriched": result.enriched,
        "content": result.content,
        "confidence": result.confidence,
        "model": result.model_used,
    }
