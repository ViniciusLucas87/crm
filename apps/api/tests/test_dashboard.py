from conftest import auth_headers
from fastapi.testclient import TestClient


def test_dashboard_summary_shape(client: TestClient) -> None:
    response = client.get(
        "/api/v1/dashboard/summary",
        headers=auth_headers("org1-admin"),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["tasks_today"] >= 0
    assert payload["pipeline_value"] >= 0
