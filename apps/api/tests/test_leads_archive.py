from conftest import auth_headers


def test_archived_lead_leaves_active_pipeline(client):
    headers = auth_headers("org1-admin")
    archived_lead = client.post(
        "/api/v1/leads/", json={"name": "Archive Me"}, headers=headers
    )
    active_lead = client.post(
        "/api/v1/leads/", json={"name": "Keep Me"}, headers=headers
    )
    assert archived_lead.status_code == 200
    assert active_lead.status_code == 200

    response = client.post(
        "/api/v1/leads/bulk",
        json={"ids": [archived_lead.json()["id"]], "action": "archive"},
        headers=headers,
    )
    assert response.status_code == 200

    active = client.get("/api/v1/leads/", params={"status": "active"}, headers=headers)
    assert active.status_code == 200
    active_names = {lead["name"] for lead in active.json()["items"]}
    assert "Archive Me" not in active_names
    assert "Keep Me" in active_names

    archived = client.get(
        "/api/v1/leads/", params={"status": "archived"}, headers=headers
    )
    assert archived.status_code == 200
    assert {lead["name"] for lead in archived.json()["items"]} == {"Archive Me"}
