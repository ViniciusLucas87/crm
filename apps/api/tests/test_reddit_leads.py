from fastapi.testclient import TestClient

from tests.conftest import auth_headers


def test_reddit_opportunity_requires_permission_before_contact(client: TestClient) -> None:
    headers = auth_headers("org1-admin")

    campaigns = client.get("/api/v1/reddit/campaigns", headers=headers)
    assert campaigns.status_code == 200
    campaign = campaigns.json()["items"][0]
    assert campaign["product_code"] == "never_miss"

    created = client.post(
        "/api/v1/reddit/opportunities",
        headers=headers,
        json={
            "campaign_id": campaign["id"],
            "community": "Contractor",
            "author_handle": "busy_builder",
            "post_title": "Missing calls while I am on site",
            "post_excerpt": "I cannot answer every customer call while I am working.",
            "source_url": "https://www.reddit.com/r/Contractor/comments/example",
            "relevance_score": 88,
            "relevance_reason": "The author describes the exact missed call problem.",
            "detected_signals": ["missed calls"],
        },
    )
    assert created.status_code == 200
    opportunity_id = created.json()["id"]

    drafted = client.post(f"/api/v1/reddit/opportunities/{opportunity_id}/draft", headers=headers)
    assert drafted.status_code == 200
    assert "built a small solution" in drafted.json()["public_reply_draft"]
    assert "Pacific North Systems" not in drafted.json()["public_reply_draft"]
    assert "Never Miss" not in drafted.json()["public_reply_draft"]

    blocked = client.post(
        f"/api/v1/reddit/opportunities/{opportunity_id}/mark-contacted",
        headers=headers,
    )
    assert blocked.status_code == 409

    approved = client.post(
        f"/api/v1/reddit/opportunities/{opportunity_id}/approve-dm",
        headers=headers,
        json={
            "human_approved": True,
            "permission_basis": "The author replied and asked me to send setup details.",
        },
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "dm_ready"

    contacted = client.post(
        f"/api/v1/reddit/opportunities/{opportunity_id}/mark-contacted",
        headers=headers,
    )
    assert contacted.status_code == 200
    assert contacted.json()["status"] == "contacted"


def test_reddit_status_disallows_automated_unsolicited_messages(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/reddit/status", headers=auth_headers("org1-member"))
    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "human_approved_outreach"
    assert "No automated unsolicited private messages" in payload["rules"]


def test_reddit_status_reports_pending_commercial_approval(
    client: TestClient, monkeypatch,
) -> None:
    monkeypatch.setenv("REDDIT_ACCESS_STATUS", "pending_approval")
    response = client.get("/api/v1/reddit/status", headers=auth_headers("org1-member"))
    assert response.status_code == 200
    payload = response.json()
    assert payload["access_status"] == "pending_approval"
    assert "Approval is pending" in payload["message"]
    assert "Manual conversation intake remains available" in payload["message"]
