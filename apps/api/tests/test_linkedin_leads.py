from fastapi.testclient import TestClient

from tests.conftest import auth_headers


def test_linkedin_human_reviewed_outreach_flow(client: TestClient) -> None:
    headers = auth_headers("org1-admin")
    campaign = client.get("/api/v1/linkedin/campaigns", headers=headers).json()["items"][0]
    created = client.post(
        "/api/v1/linkedin/opportunities",
        headers=headers,
        json={
            "campaign_id": campaign["id"],
            "community": "British Columbia",
            "author_handle": "Jordan Owner",
            "post_title": "Owner at Example Electric",
            "post_excerpt": "Public company research confirms a small field team and phone-first enquiries.",
            "source_url": "https://www.linkedin.com/in/jordan-owner",
            "relevance_score": 82,
            "relevance_reason": "Canadian contractor owner with a documented missed-call problem.",
            "detected_signals": ["missed calls"],
        },
    )
    assert created.status_code == 200
    item_id = created.json()["id"]
    drafted = client.post(f"/api/v1/linkedin/opportunities/{item_id}/draft", headers=headers)
    assert drafted.status_code == 200
    assert "I am Vini, founder of Pacific North Systems" in drafted.json()["public_reply_draft"]
    assert "Open to connecting?" in drafted.json()["public_reply_draft"]
    blocked = client.post(f"/api/v1/linkedin/opportunities/{item_id}/mark-contacted", headers=headers)
    assert blocked.status_code == 409
    approved = client.post(
        f"/api/v1/linkedin/opportunities/{item_id}/approve-dm",
        headers=headers,
        json={"human_approved": True, "permission_basis": "Verified owner and reviewed a relevant public business need."},
    )
    assert approved.status_code == 200
    contacted = client.post(f"/api/v1/linkedin/opportunities/{item_id}/mark-contacted", headers=headers)
    assert contacted.status_code == 200


def test_social_channels_are_isolated(client: TestClient) -> None:
    headers = auth_headers("org1-admin")
    client.get("/api/v1/reddit/campaigns", headers=headers)
    client.get("/api/v1/linkedin/campaigns", headers=headers)
    reddit = client.get("/api/v1/reddit/opportunities", headers=headers).json()["items"]
    linkedin = client.get("/api/v1/linkedin/opportunities", headers=headers).json()["items"]
    assert all(item["channel"] == "reddit" for item in reddit)
    assert all(item["channel"] == "linkedin" for item in linkedin)
