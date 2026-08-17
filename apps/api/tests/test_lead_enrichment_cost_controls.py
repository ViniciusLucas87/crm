from unittest.mock import patch

from conftest import auth_headers


def test_ai_discovered_lead_enrichment_is_queued_once_on_approval(client):
    headers = auth_headers("org1-admin")
    created = client.post(
        "/api/v1/leads/",
        json={"name": "Approval Gated Lead", "source": "ai_discovery"},
        headers=headers,
    )
    assert created.status_code == 200
    lead_id = created.json()["id"]

    with patch(
        "app.application.sales.task_dispatcher.queue_enrichment",
        return_value="approval-gated-job",
    ) as queue:
        approved = client.post(
            f"/api/v1/leads/{lead_id}/status",
            params={"status": "approved"},
            headers=headers,
        )
        approved_again = client.post(
            f"/api/v1/leads/{lead_id}/status",
            params={"status": "approved"},
            headers=headers,
        )

    assert approved.status_code == 200
    assert approved.json()["enrichment_job_id"] == "approval-gated-job"
    assert approved_again.status_code == 200
    assert approved_again.json()["enrichment_job_id"] is None
    queue.assert_called_once()


def test_manual_lead_approval_does_not_spend_ai_credits(client):
    headers = auth_headers("org1-admin")
    created = client.post(
        "/api/v1/leads/",
        json={"name": "Manual Lead", "source": "manual"},
        headers=headers,
    )
    lead_id = created.json()["id"]

    with patch("app.application.sales.task_dispatcher.queue_enrichment") as queue:
        approved = client.post(
            f"/api/v1/leads/{lead_id}/status",
            params={"status": "approved"},
            headers=headers,
        )

    assert approved.status_code == 200
    assert approved.json()["enrichment_job_id"] is None
    queue.assert_not_called()
