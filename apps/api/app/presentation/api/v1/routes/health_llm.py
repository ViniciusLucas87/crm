"""LLM Budget admin endpoint — owner/admin only, 403 for members."""
from fastapi import APIRouter, Depends, HTTPException

from app.infrastructure.auth.clerk import AuthContext, require_permission

router = APIRouter()


@router.get("/health/llm-budget")
async def health_llm_budget(
    ctx: AuthContext = Depends(require_permission("companies:read")),
) -> dict:
    """Return current LLM budget and usage. Requires owner or admin role."""
    if ctx.role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    try:
        from app.application.llm.gateway import get_budget_summary
        return await get_budget_summary()
    except Exception:
        return {"status": "unavailable"}
