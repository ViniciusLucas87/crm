"""Paid subscription fulfillment and zero-touch activation tests."""

import hashlib
import hmac
import json
import time


CHECKOUT = {
    "id": "cs_test_never_miss_001",
    "payment_status": "paid",
    "payment_link": "plink_basic",
    "customer": "cus_001",
    "subscription": "sub_001",
    "customer_details": {
        "email": "owner@example.ca",
        "name": "Taylor Owner",
        "phone": "+16045550101",
    },
}


def _post_checkout_webhook(client, monkeypatch, checkout=CHECKOUT, event_id="evt_checkout_001"):
    secret = "whsec_test"
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", secret)
    monkeypatch.setenv("STRIPE_NEVER_MISS_PAYMENT_LINK_ID", "plink_basic")
    monkeypatch.setenv("STRIPE_NEVER_MISS_PLUS_PAYMENT_LINK_ID", "plink_plus")
    body = json.dumps({
        "id": event_id,
        "type": "checkout.session.completed",
        "livemode": False,
        "data": {"object": checkout},
    }).encode()
    timestamp = int(time.time())
    signature = hmac.new(secret.encode(), f"{timestamp}.".encode() + body, hashlib.sha256).hexdigest()
    return client.post(
        "/api/v1/subscriptions/stripe/webhook",
        content=body,
        headers={"Content-Type": "application/json", "Stripe-Signature": f"t={timestamp},v1={signature}"},
    )


def test_checkout_exchange_is_idempotent(client, monkeypatch):
    assert _post_checkout_webhook(client, monkeypatch).status_code == 200
    first = client.post("/api/v1/subscriptions/onboarding/exchange", json={"checkout_session_id": CHECKOUT["id"]})
    second = client.post("/api/v1/subscriptions/onboarding/exchange", json={"checkout_session_id": CHECKOUT["id"]})
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["token"]
    assert second.json()["token"]


def test_checkout_redirect_does_not_invalidate_email_link(client, monkeypatch):
    assert _post_checkout_webhook(client, monkeypatch).status_code == 200
    from app.infrastructure.db.models import ProductSubscription
    from app.infrastructure.db.session import SessionLocal

    session = SessionLocal()
    subscription = session.query(ProductSubscription).filter_by(stripe_checkout_session_id=CHECKOUT["id"]).one()
    original_email_hash = subscription.onboarding_token_hash
    session.close()

    response = client.post("/api/v1/subscriptions/onboarding/exchange", json={"checkout_session_id": CHECKOUT["id"]})
    assert response.status_code == 200

    session = SessionLocal()
    subscription = session.query(ProductSubscription).filter_by(stripe_checkout_session_id=CHECKOUT["id"]).one()
    assert subscription.onboarding_token_hash == original_email_hash
    assert subscription.redirect_token_hash
    session.close()


def test_paid_customer_can_activate_without_staff(client, monkeypatch):
    assert _post_checkout_webhook(client, monkeypatch).status_code == 200
    monkeypatch.setattr(
        "app.presentation.api.v1.routes.subscriptions._provision_telnyx_number",
        lambda area_code, reference: ("+16045550999", "order_001"),
    )
    exchange = client.post("/api/v1/subscriptions/onboarding/exchange", json={"checkout_session_id": CHECKOUT["id"]})
    token = exchange.json()["token"]
    activation = client.post(
        f"/api/v1/subscriptions/onboarding/{token}/activate",
        json={
            "business_name": "Taylor Plumbing",
            "contact_name": "Taylor Owner",
            "notification_phone": "+1 604 555 0101",
            "existing_business_phone": "+1 604 555 0102",
            "preferred_area_code": "604",
            "recovery_message": "Hi, this is Taylor Plumbing. Sorry we missed your call. Reply with what you need. Reply STOP to opt out.",
            "timezone": "America/Vancouver",
            "website_url": None,
            "consent_to_text_callers": True,
            "accept_terms": True,
        },
    )
    assert activation.status_code == 200, activation.text
    assert activation.json()["status"] == "active"
    assert activation.json()["assigned_phone"] == "+16045550999"
    assert activation.json()["management_token"]


def test_customer_can_manage_settings_and_pause_service(client, monkeypatch):
    assert _post_checkout_webhook(client, monkeypatch).status_code == 200
    monkeypatch.setattr(
        "app.presentation.api.v1.routes.subscriptions._provision_telnyx_number",
        lambda area_code, reference: ("+16045550999", "order_001"),
    )
    token = client.post(
        "/api/v1/subscriptions/onboarding/exchange", json={"checkout_session_id": CHECKOUT["id"]}
    ).json()["token"]
    activation = client.post(
        f"/api/v1/subscriptions/onboarding/{token}/activate",
        json={
            "business_name": "Taylor Plumbing",
            "contact_name": "Taylor Owner",
            "notification_phone": "+16045550101",
            "existing_business_phone": "+16045550102",
            "preferred_area_code": "604",
            "recovery_message": "Hi, this is Taylor Plumbing. Sorry we missed your call. Reply STOP to opt out.",
            "timezone": "America/Vancouver",
            "website_url": None,
            "consent_to_text_callers": True,
            "accept_terms": True,
        },
    )
    management_token = activation.json()["management_token"]
    status = client.get(f"/api/v1/subscriptions/manage/{management_token}")
    assert status.status_code == 200
    assert status.json()["enabled"] is True
    updated = client.patch(
        f"/api/v1/subscriptions/manage/{management_token}",
        json={
            "notification_phone": "+16045550103",
            "recovery_message": "Hi, Taylor Plumbing missed your call. Tell us what you need. Reply STOP to opt out.",
            "enabled": False,
        },
    )
    assert updated.status_code == 200
    assert updated.json()["notification_phone"] == "+16045550103"
    assert updated.json()["enabled"] is False


def test_cancellation_webhook_disables_service_but_keeps_customer_record(client, monkeypatch):
    assert _post_checkout_webhook(client, monkeypatch).status_code == 200
    monkeypatch.setattr(
        "app.presentation.api.v1.routes.subscriptions._provision_telnyx_number",
        lambda area_code, reference: ("+16045550999", "order_001"),
    )
    token = client.post(
        "/api/v1/subscriptions/onboarding/exchange", json={"checkout_session_id": CHECKOUT["id"]}
    ).json()["token"]
    activation = client.post(
        f"/api/v1/subscriptions/onboarding/{token}/activate",
        json={
            "business_name": "Taylor Plumbing",
            "contact_name": "Taylor Owner",
            "notification_phone": "+16045550101",
            "existing_business_phone": "+16045550102",
            "preferred_area_code": "604",
            "recovery_message": "Hi, this is Taylor Plumbing. Sorry we missed your call. Reply STOP to opt out.",
            "timezone": "America/Vancouver",
            "website_url": None,
            "consent_to_text_callers": True,
            "accept_terms": True,
        },
    )
    management_token = activation.json()["management_token"]
    secret = "whsec_test"
    body = json.dumps({
        "id": "evt_subscription_deleted_001",
        "type": "customer.subscription.deleted",
        "livemode": False,
        "data": {"object": {"id": CHECKOUT["subscription"]}},
    }).encode()
    timestamp = int(time.time())
    signature = hmac.new(secret.encode(), f"{timestamp}.".encode() + body, hashlib.sha256).hexdigest()
    response = client.post(
        "/api/v1/subscriptions/stripe/webhook",
        content=body,
        headers={"Content-Type": "application/json", "Stripe-Signature": f"t={timestamp},v1={signature}"},
    )
    assert response.status_code == 200
    status = client.get(f"/api/v1/subscriptions/manage/{management_token}")
    assert status.status_code == 200
    assert status.json()["status"] == "cancelled"
    assert status.json()["enabled"] is False
    assert status.json()["assigned_phone"] == "+16045550999"


def test_plus_plan_uses_the_same_reliable_onboarding(client, monkeypatch):
    plus_checkout = {
        **CHECKOUT,
        "id": "cs_test_never_miss_plus_001",
        "payment_link": "plink_plus",
        "subscription": "sub_plus_001",
    }
    assert _post_checkout_webhook(client, monkeypatch, plus_checkout, "evt_checkout_plus_001").status_code == 200
    exchange = client.post(
        "/api/v1/subscriptions/onboarding/exchange",
        json={"checkout_session_id": plus_checkout["id"]},
    )
    assert exchange.status_code == 200
    status = client.get(f"/api/v1/subscriptions/onboarding/{exchange.json()['token']}")
    assert status.status_code == 200
    assert status.json()["plan"] == "never_miss_plus"


def test_unpaid_checkout_is_not_fulfilled(client, monkeypatch):
    unpaid = {**CHECKOUT, "payment_status": "unpaid", "id": "cs_test_unpaid_001"}
    webhook = _post_checkout_webhook(client, monkeypatch, unpaid, "evt_unpaid_001")
    assert webhook.status_code == 409
    response = client.post("/api/v1/subscriptions/onboarding/exchange", json={"checkout_session_id": "cs_test_unpaid_001"})
    assert response.status_code == 409


def test_stripe_webhook_fails_closed_without_signature(client, monkeypatch):
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test")
    response = client.post(
        "/api/v1/subscriptions/stripe/webhook",
        content=json.dumps({"id": "evt_1", "type": "checkout.session.completed"}),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400
