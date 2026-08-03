from fastapi.testclient import TestClient


def test_health_ok(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    payload = response.json()
    # Local tests intentionally run without Redis/DeepSeek, so the comprehensive
    # endpoint may be degraded while the API process itself remains healthy.
    assert payload["status"] in {"healthy", "degraded"}
    assert payload["phase"] in {"ready", "starting"}
    assert isinstance(payload["checks"], dict)
    assert "model_fingerprint" in payload
