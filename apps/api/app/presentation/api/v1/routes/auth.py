from fastapi import APIRouter, Depends

from app.infrastructure.auth.clerk import AuthContext, get_auth_context

router = APIRouter()


@router.get("/me", response_model=AuthContext)
def me(context: AuthContext = Depends(get_auth_context)) -> AuthContext:
    return context
