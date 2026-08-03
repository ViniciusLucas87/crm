import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.infrastructure.auth import clerk as clerk_auth
from app.infrastructure.db.base import Base
from app.infrastructure.db import models as _models  # noqa: F401 - register all tables
from app.infrastructure.db.session import get_db_session
from app.main import app

TOKEN_CLAIMS = {
    "org1-admin": {
        "sub": "user_org1_admin",
        "email": "admin@pacificnorthsystems.com",
        "name": "Org One Admin",
        "org_id": "org_1",
        "org_slug": "pacific-north-systems",
        "org_name": "Pacific North Systems",
        "org_role": "admin",
    },
    "org1-member": {
        "sub": "user_org1_member",
        "email": "member@pacificnorthsystems.com",
        "name": "Org One Member",
        "org_id": "org_1",
        "org_slug": "pacific-north-systems",
        "org_name": "Pacific North Systems",
        "org_role": "member",
    },
    "org2-admin": {
        "sub": "user_org2_admin",
        "email": "admin@otherorg.test",
        "name": "Org Two Admin",
        "org_id": "org_2",
        "org_slug": "other-org",
        "org_name": "Other Org",
        "org_role": "admin",
    },
}


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    previous_issuer = os.environ.get("CLERK_ISSUER")
    previous_jwks = os.environ.get("CLERK_JWKS_URL")
    os.environ["CLERK_ISSUER"] = "https://clerk.test"
    os.environ["CLERK_JWKS_URL"] = "https://clerk.test/.well-known/jwks.json"
    get_settings.cache_clear()

    def fake_decode(token: str) -> dict[str, str]:
        if token not in TOKEN_CLAIMS:
            raise clerk_auth.HTTPException(status_code=401, detail="Invalid Clerk token")
        return TOKEN_CLAIMS[token]

    monkeypatch.setattr(clerk_auth, "_decode_clerk_token", fake_decode)

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    testing_session_local = sessionmaker(
        bind=engine, autocommit=False, autoflush=False, class_=Session
    )
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr("app.infrastructure.db.session.SessionLocal", testing_session_local)

    def override_db() -> Generator[Session, None, None]:
        session = testing_session_local()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db_session] = override_db

    with TestClient(app) as api_client:
        yield api_client

    app.dependency_overrides.clear()
    if previous_issuer is None:
        os.environ.pop("CLERK_ISSUER", None)
    else:
        os.environ["CLERK_ISSUER"] = previous_issuer
    if previous_jwks is None:
        os.environ.pop("CLERK_JWKS_URL", None)
    else:
        os.environ["CLERK_JWKS_URL"] = previous_jwks
    get_settings.cache_clear()
