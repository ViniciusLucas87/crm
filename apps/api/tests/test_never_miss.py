def _auth(token: str = "org1-admin") -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_product_configuration_is_isolated_by_organization(client):
    response = client.put(
        "/api/v1/products/never_miss/configuration",
        headers=_auth(),
        json={
            "enabled": True,
            "plan": "never_miss",
            "business_name": "North Shore Plumbing",
            "business_phone": "+16045550101",
            "notification_phone": "+16045550102",
            "recovery_message": "Thanks for calling. How can we help?",
            "business_hours_json": {"timezone": "America/Vancouver"},
            "monthly_call_limit": 50,
            "monthly_message_limit": 100,
        },
    )
    assert response.status_code == 200
    assert response.json()["business_name"] == "North Shore Plumbing"

    other = client.get("/api/v1/products/never_miss/configuration", headers=_auth("org2-admin"))
    assert other.status_code == 200
    assert other.json()["business_name"] is None
    assert other.json()["enabled"] is False


def test_public_intake_requires_active_hashed_key(client):
    key_response = client.post("/api/v1/products/never_miss_plus/intake-key", headers=_auth())
    assert key_response.status_code == 200
    intake_key = key_response.json()["intake_key"]

    config = client.get("/api/v1/products/never_miss/configuration", headers=_auth()).json()
    config.update({"enabled": True, "plan": "never_miss_plus", "business_name": "Pilot Business"})
    config.pop("product_code", None)
    config.pop("intake_key_configured", None)
    config.pop("updated_at", None)
    enabled = client.put(
        "/api/v1/products/never_miss/configuration",
        headers=_auth(),
        json=config,
    )
    assert enabled.status_code == 200

    payload = {
        "source": "website",
        "external_id": "website-form-123",
        "name": "Alex Smith",
        "email": "alex@example.com",
        "summary": "Needs a callback",
    }
    denied = client.post("/api/v1/products/never_miss_plus/public-intake", json=payload)
    assert denied.status_code == 401

    accepted = client.post(
        "/api/v1/products/never_miss_plus/public-intake",
        headers={"X-PNS-Intake-Key": intake_key},
        json=payload,
    )
    assert accepted.status_code == 202
    assert accepted.json()["status"] == "new"

    duplicate = client.post(
        "/api/v1/products/never_miss_plus/public-intake",
        headers={"X-PNS-Intake-Key": intake_key},
        json=payload,
    )
    assert duplicate.status_code == 202
    assert duplicate.json()["id"] == accepted.json()["id"]


def test_inbox_update_is_tenant_scoped(client):
    created = client.post(
        "/api/v1/products/never_miss_plus/intake",
        headers=_auth(),
        json={"source": "manual", "name": "Test Lead", "phone": "+16045550199"},
    )
    assert created.status_code == 200
    record_id = created.json()["id"]

    updated = client.patch(
        f"/api/v1/products/never_miss_plus/inbox/{record_id}",
        headers=_auth(),
        json={"status": "contacted", "next_action": "Call tomorrow"},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "contacted"

    forbidden = client.patch(
        f"/api/v1/products/never_miss_plus/inbox/{record_id}",
        headers=_auth("org2-admin"),
        json={"status": "won"},
    )
    assert forbidden.status_code == 404

    inbox = client.get("/api/v1/products/never_miss_plus/inbox", headers=_auth())
    assert inbox.status_code == 200
    assert inbox.json()["items"][0]["next_action"] == "Call tomorrow"
