"""
LLM Budget admin endpoint — Sprint: Production Cost Hardening
Registered in health router.
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/health/llm-budget")
def health_llm_budget() -> dict:
    """Return current LLM budget and usage summary."""
    try:
        from app.application.llm.gateway import get_budget_summary
        return get_budget_summary()
    except Exception:
        return {"status": "unavailable"}
