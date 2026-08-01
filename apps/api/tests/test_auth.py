from conftest import auth_headers
from fastapi.testclient import TestClient


def test_auth_me_returns_actor(client: TestClient) -> None:
    response = client.get(
        "/api/v1/auth/me",
        headers=auth_headers("org1-admin"),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["email"] == "admin@pacificnorthsystems.com"
    assert payload["role"] == "admin"
    assert payload["organization_slug"] == "pacific-north-systems"
    assert "dashboard:read" in payload["permissions"]


def test_auth_me_requires_bearer_token(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing authorization header"


def test_auth_me_rejects_invalid_token(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me", headers=auth_headers("invalid-token"))
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid Clerk token"
