from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.application.sales.actions import ActionEngine, ActionResponse
from app.infrastructure.auth.clerk import AuthContext, require_permission
from app.infrastructure.db.session import get_db_session

router = APIRouter()


@router.get("/actions/recommendations", response_model=ActionResponse)
def get_recommendations(
    company_id: int | None = Query(default=None),
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
) -> ActionResponse:
    engine = ActionEngine(session)
    return engine.get_recommendations(ctx.organization_id, company_id=company_id)
