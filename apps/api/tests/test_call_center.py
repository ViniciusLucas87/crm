from fastapi.testclient import TestClient

from tests.conftest import auth_headers


def test_browser_call_is_saved_and_appears_in_history(client: TestClient) -> None:
    created = client.post(
        "/api/v1/telephony/calls/browser",
        headers=auth_headers("org1-admin"),
        json={"phone_number": "+16045550123"},
    )
    assert created.status_code == 200
    call_id = created.json()["id"]

    updated = client.patch(
        f"/api/v1/telephony/calls/browser/{call_id}",
        headers=auth_headers("org1-admin"),
        json={"status": "ended", "duration_seconds": 42},
    )
    assert updated.status_code == 200

    history = client.get("/api/v1/telephony/history", headers=auth_headers("org1-admin"))
    assert history.status_code == 200
    item = history.json()["items"][0]
    assert item["kind"] == "call"
    assert item["direction"] == "outbound"
    assert item["phone_number"] == "+16045550123"
    assert item["duration_seconds"] == 42


def test_call_center_history_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/telephony/history")
    assert response.status_code == 401


def test_browser_call_history_is_tenant_scoped(client: TestClient) -> None:
    client.post(
        "/api/v1/telephony/calls/browser",
        headers=auth_headers("org1-admin"),
        json={"phone_number": "+16045550124"},
    )

    other_org = client.get("/api/v1/telephony/history", headers=auth_headers("org2-admin"))
    assert other_org.status_code == 200
    assert other_org.json()["items"] == []
