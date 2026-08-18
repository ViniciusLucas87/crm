from datetime import date, timedelta

from tests.conftest import auth_headers


def _payload(**overrides):
    payload = {
        "contractor_name": "Pacific Test Plumbing",
        "contractor_phone": "+16045550100",
        "contractor_email": "service@example.test",
        "customer_name": "Jordan Customer",
        "customer_phone": "+16045550101",
        "service_address": "100 Test Street, Vancouver",
        "job_title": "Hot water tank service",
        "job_summary": "Inspected the tank, replaced the valve and confirmed normal operation.",
        "completed_on": date.today().isoformat(),
        "invoice_reference": "INV-100",
        "warranty_summary": "Parts and labour are covered for one year.",
        "warranty_expires_on": (date.today() + timedelta(days=365)).isoformat(),
        "maintenance_instructions": "Check around the tank monthly for moisture.",
        "next_service_on": (date.today() + timedelta(days=180)).isoformat(),
        "customer_consented_to_reminders": True,
        "work_photo_urls": ["https://example.test/photo.jpg"],
    }
    payload.update(overrides)
    return payload


def test_create_and_open_private_service_record(client):
    response = client.post(
        "/api/v1/never-forget/records",
        headers=auth_headers("org1-admin"),
        json=_payload(),
    )
    assert response.status_code == 201, response.text
    created = response.json()
    assert "/service-record/" in created["customer_record_url"]
    token = created["customer_record_url"].rsplit("/", 1)[-1]

    public = client.get(f"/api/v1/never-forget/public/{token}")
    assert public.status_code == 200
    assert public.json()["job_title"] == "Hot water tank service"
    assert "customer_phone" not in public.json()
    assert "public_token_hash" not in public.json()

    action = client.post(
        f"/api/v1/never-forget/public/{token}/actions",
        json={"action_type": "request_service", "note": "Please call me next week."},
    )
    assert action.status_code == 202

    summary = client.get("/api/v1/never-forget/summary", headers=auth_headers("org1-admin")).json()
    assert summary["records"] == 1
    assert summary["scheduled_reminders"] == 1
    assert summary["open_customer_requests"] == 1
    assert summary["live_messages_enabled"] is False


def test_stop_reminders_cancels_pending_delivery(client):
    response = client.post(
        "/api/v1/never-forget/records",
        headers=auth_headers("org1-admin"),
        json=_payload(),
    )
    token = response.json()["customer_record_url"].rsplit("/", 1)[-1]
    stopped = client.post(
        f"/api/v1/never-forget/public/{token}/actions",
        json={"action_type": "stop_reminders"},
    )
    assert stopped.status_code == 202
    summary = client.get("/api/v1/never-forget/summary", headers=auth_headers("org1-admin")).json()
    assert summary["scheduled_reminders"] == 0


def test_records_are_organization_scoped_and_members_cannot_create(client):
    created = client.post(
        "/api/v1/never-forget/records",
        headers=auth_headers("org1-admin"),
        json=_payload(customer_consented_to_reminders=False),
    )
    assert created.status_code == 201
    other = client.get("/api/v1/never-forget/records", headers=auth_headers("org2-admin"))
    assert other.json()["total"] == 0
    forbidden = client.post(
        "/api/v1/never-forget/records",
        headers=auth_headers("org1-member"),
        json=_payload(),
    )
    assert forbidden.status_code == 403


def test_invalid_service_dates_are_rejected(client):
    response = client.post(
        "/api/v1/never-forget/records",
        headers=auth_headers("org1-admin"),
        json=_payload(next_service_on=(date.today() - timedelta(days=1)).isoformat()),
    )
    assert response.status_code == 422
