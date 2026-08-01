from collections.abc import Callable
from functools import lru_cache
from typing import Any

import httpx
from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.infrastructure.db.models import Organization, OrganizationMembership, User
from app.infrastructure.db.session import get_db_session

ROLE_PERMISSIONS: dict[str, set[str]] = {
    "admin": {
        "dashboard:read",
        "companies:read",
        "companies:write",
        "telephony:read",
        "telephony:write",
    },
    "manager": {
        "dashboard:read",
        "companies:read",
        "companies:write",
        "telephony:read",
        "telephony:write",
    },
    "member": {
        "dashboard:read",
        "companies:read",
        "telephony:read",
    },
}


class AuthContext(BaseModel):
    user_id: int
    email: str
    role: str
    organization_id: int
    organization_slug: str
    permissions: list[str]


def _normalize_role(role: str | None) -> str:
    if role is None:
        return "member"

    normalized = role.lower().replace("org:", "").replace("organization:", "")
    if normalized in ROLE_PERMISSIONS:
        return normalized
    return "member"


def _extract_bearer_token(authorization: str | None) -> str | None:
    if authorization is None:
        return None
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
        )
    return authorization.split(" ", maxsplit=1)[1]


@lru_cache(maxsize=1)
def _fetch_jwks() -> dict[str, Any]:
    settings = get_settings()
    if settings.clerk_jwks_url is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Missing Clerk JWKS URL"
        )
    response = httpx.get(settings.clerk_jwks_url, timeout=5)
    response.raise_for_status()
    return response.json()


def _decode_clerk_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    if settings.clerk_issuer is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Missing Clerk issuer"
        )

    try:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        if not kid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token key id"
            )

        jwks = _fetch_jwks()
        key = next((item for item in jwks.get("keys", []) if item.get("kid") == kid), None)
        if key is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Unable to match signing key"
            )

        return jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            issuer=settings.clerk_issuer,
            audience=settings.clerk_issuer,
        )
    except HTTPException:
        raise
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Clerk token"
        ) from exc


def _get_or_create_default_org(session: Session) -> Organization:
    organizations = session.execute(select(Organization).order_by(Organization.id.asc())).scalars().all()
    if len(organizations) == 1:
        return organizations[0]
    if len(organizations) > 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization context is required",
        )

    org = Organization(name="Pacific North Systems", slug="pacific-north-systems")
    session.add(org)
    session.commit()
    session.refresh(org)
    return org


def _get_or_create_organization(
    session: Session,
    *,
    clerk_org_id: str | None,
    slug: str | None,
    name: str | None,
) -> Organization:
    if clerk_org_id is None:
        return _get_or_create_default_org(session)

    existing = (
        session.execute(select(Organization).where(Organization.clerk_org_id == clerk_org_id))
        .scalars()
        .first()
    )
    resolved_slug = slug or clerk_org_id.lower().replace("org_", "org-")
    resolved_name = name or resolved_slug.replace("-", " ").title()

    if existing is not None:
        changed = False
        if existing.slug != resolved_slug:
            existing.slug = resolved_slug
            changed = True
        if existing.name != resolved_name:
            existing.name = resolved_name
            changed = True
        if changed:
            session.add(existing)
            session.commit()
            session.refresh(existing)
        return existing

    org = Organization(clerk_org_id=clerk_org_id, name=resolved_name, slug=resolved_slug)
    session.add(org)
    session.commit()
    session.refresh(org)
    return org


def _get_or_create_user(
    session: Session,
    *,
    clerk_user_id: str,
    email: str,
    full_name: str | None,
) -> User:
    existing = (
        session.execute(select(User).where(User.clerk_user_id == clerk_user_id)).scalars().first()
    )
    if existing is not None:
        if existing.email != email or existing.full_name != full_name:
            existing.email = email
            existing.full_name = full_name
            session.add(existing)
            session.commit()
            session.refresh(existing)
        return existing

    user = User(clerk_user_id=clerk_user_id, email=email, full_name=full_name)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def _get_or_create_membership(
    session: Session, *, organization_id: int, user_id: int, role: str
) -> OrganizationMembership:
    existing = (
        session.execute(
            select(OrganizationMembership).where(
                OrganizationMembership.organization_id == organization_id,
                OrganizationMembership.user_id == user_id,
            )
        )
        .scalars()
        .first()
    )
    if existing is not None:
        if existing.role != role and role != "member":
            existing.role = role
            session.add(existing)
            session.commit()
            session.refresh(existing)
        return existing

    membership = OrganizationMembership(
        organization_id=organization_id, user_id=user_id, role=role
    )
    session.add(membership)
    session.commit()
    session.refresh(membership)
    return membership


def verify_clerk_token(authorization: str | None = Header(default=None)) -> None:
    settings = get_settings()
    token = _extract_bearer_token(authorization)

    if settings.clerk_issuer and settings.clerk_jwks_url:
        if token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authorization header"
            )
        _decode_clerk_token(token)


def get_auth_context(
    session: Session = Depends(get_db_session),
    authorization: str | None = Header(default=None),
) -> AuthContext:
    settings = get_settings()
    token = _extract_bearer_token(authorization)

    if settings.clerk_issuer and settings.clerk_jwks_url:
        if token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authorization header"
            )
        claims = _decode_clerk_token(token)
        clerk_user_id = str(claims.get("sub", ""))
        if not clerk_user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing required claims"
            )
        email = str(claims.get("email") or f"{clerk_user_id}@clerk.user")
        clerk_org_id = claims.get("org_id")
        org_slug = claims.get("org_slug")
        org_name = claims.get("org_name")
        role = _normalize_role(str(claims.get("org_role")) if claims.get("org_role") else None)
        full_name = claims.get("name")
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is not configured",
        )

    org = _get_or_create_organization(
        session,
        clerk_org_id=str(clerk_org_id) if clerk_org_id else None,
        slug=str(org_slug) if org_slug else None,
        name=str(org_name) if org_name else None,
    )
    user = _get_or_create_user(
        session,
        clerk_user_id=clerk_user_id,
        email=email,
        full_name=str(full_name) if full_name else None,
    )
    membership = _get_or_create_membership(
        session,
        organization_id=org.id,
        user_id=user.id,
        role=role,
    )
    permissions = sorted(ROLE_PERMISSIONS.get(membership.role, set()))

    return AuthContext(
        user_id=user.id,
        email=user.email,
        role=membership.role,
        organization_id=org.id,
        organization_slug=org.slug,
        permissions=permissions,
    )


def require_permission(permission: str) -> Callable[[AuthContext], AuthContext]:
    def _require(ctx: AuthContext = Depends(get_auth_context)) -> AuthContext:
        if permission not in set(ctx.permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
        return ctx

    return _require
