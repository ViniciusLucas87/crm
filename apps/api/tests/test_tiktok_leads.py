from fastapi.testclient import TestClient

from tests.conftest import auth_headers


def test_tiktok_lead_requires_human_approval_before_contact(client: TestClient) -> None:
    headers = auth_headers("org1-admin")
    campaign = client.get("/api/v1/tiktok/campaigns", headers=headers).json()["items"][0]
    created = client.post(
        "/api/v1/tiktok/opportunities",
        headers=headers,
        json={
            "campaign_id": campaign["id"],
            "community": "Canadian home services",
            "author_handle": "busy_service_owner",
            "post_title": "Calls come in while I am on jobs",
            "post_excerpt": "The owner says customers call while the crew is on site.",
            "source_url": "https://www.tiktok.com/@busy_service_owner/video/123",
            "relevance_score": 86,
            "relevance_reason": "Specific public missed-call pain from a service business owner.",
            "detected_signals": ["calls while working", "missed calls"],
        },
    )
    assert created.status_code == 200
    item_id = created.json()["id"]

    drafted = client.post(f"/api/v1/tiktok/opportunities/{item_id}/draft", headers=headers)
    assert drafted.status_code == 200
    assert "Pacific North Systems" in drafted.json()["public_reply_draft"]

    blocked = client.post(f"/api/v1/tiktok/opportunities/{item_id}/mark-contacted", headers=headers)
    assert blocked.status_code == 409

    approved = client.post(
        f"/api/v1/tiktok/opportunities/{item_id}/approve-dm",
        headers=headers,
        json={
            "human_approved": True,
            "permission_basis": "Reviewed the post and personalized TikTok contact.",
        },
    )
    assert approved.status_code == 200
    contacted = client.post(
        f"/api/v1/tiktok/opportunities/{item_id}/mark-contacted", headers=headers
    )
    assert contacted.status_code == 200
    assert contacted.json()["status"] == "contacted"


def test_tiktok_status_disallows_bulk_social_actions(client: TestClient) -> None:
    response = client.get("/api/v1/tiktok/status", headers=auth_headers("org1-member"))
    assert response.status_code == 200
    assert response.json()["mode"] == "human_approved_outreach"
    assert "No scraping or bulk following" in response.json()["rules"]
