"""Paid subscription fulfillment and zero-touch activation tests."""

import hashlib
import hmac
import json
import time
from types import SimpleNamespace

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


def test_activation_email_explains_unanswered_only_forwarding(client, monkeypatch):
    """The setup email must prevent accidental all-call forwarding."""
    sent: dict = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

    def fake_post(*args, **kwargs):
        sent.update(kwargs["json"])
        return FakeResponse()

    monkeypatch.setenv("RESEND_API_KEY", "re_test")
    monkeypatch.setenv("MARKETING_SITE_URL", "https://www.pacificnorthsystems.com")
    monkeypatch.setattr("app.presentation.api.v1.routes.subscriptions.httpx.post", fake_post)

    from app.presentation.api.v1.routes.subscriptions import _email_activation_link

    _email_activation_link(SimpleNamespace(customer_email="owner@example.ca"), "safe-token")

    assert "unanswered calls only" in sent["html"]
    assert "Always forward" in sent["html"]
    assert "unanswered-calls-only.svg" in sent["html"]


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


def _post_stripe_event(client, event_type, obj, event_id):
    secret = "whsec_test"
    body = json.dumps({
        "id": event_id,
        "type": event_type,
        "livemode": False,
        "data": {"object": obj},
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
    headers = {"X-Never-Miss-Token": management_token}
    status = client.post("/api/v1/subscriptions/manage/session", headers=headers)
    assert status.status_code == 200
    assert status.json()["enabled"] is True
    updated = client.patch(
        "/api/v1/subscriptions/manage/settings",
        headers=headers,
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
    status = client.post(
        "/api/v1/subscriptions/manage/session", headers={"X-Never-Miss-Token": management_token}
    )
    assert status.status_code == 200
    assert status.json()["status"] == "cancelled"
    assert status.json()["enabled"] is False
    assert status.json()["assigned_phone"] == "+16045550999"


def test_subscription_update_reconciles_billing_state(client, monkeypatch):
    assert _post_checkout_webhook(client, monkeypatch).status_code == 200
    secret = "whsec_test"
    body = json.dumps({
        "id": "evt_subscription_updated_001",
        "type": "customer.subscription.updated",
        "livemode": False,
        "data": {"object": {"id": CHECKOUT["subscription"], "status": "past_due"}},
    }).encode()
    timestamp = int(time.time())
    signature = hmac.new(secret.encode(), f"{timestamp}.".encode() + body, hashlib.sha256).hexdigest()
    response = client.post(
        "/api/v1/subscriptions/stripe/webhook",
        content=body,
        headers={"Content-Type": "application/json", "Stripe-Signature": f"t={timestamp},v1={signature}"},
    )
    assert response.status_code == 200
    from app.infrastructure.db.models import ProductSubscription
    from app.infrastructure.db.session import SessionLocal

    session = SessionLocal()
    subscription = session.query(ProductSubscription).filter_by(stripe_subscription_id=CHECKOUT["subscription"]).one()
    assert subscription.status == "past_due"
    session.close()


def test_trial_lifecycle_keeps_service_available_and_opens_scoped_billing_portal(client, monkeypatch):
    trial_checkout = {
        **CHECKOUT,
        "id": "cs_test_trial_001",
        "subscription": "sub_trial_001",
        "payment_status": "no_payment_required",
    }
    assert _post_checkout_webhook(client, monkeypatch, trial_checkout, "evt_checkout_trial_001").status_code == 200
    assert _post_stripe_event(
        client,
        "customer.subscription.updated",
        {
            "id": trial_checkout["subscription"],
            "status": "trialing",
            "trial_end": 1_800_000_000,
            "current_period_end": 1_800_000_000,
            "cancel_at_period_end": False,
        },
        "evt_subscription_trialing_001",
    ).status_code == 200
    monkeypatch.setattr(
        "app.presentation.api.v1.routes.subscriptions._provision_telnyx_number",
        lambda area_code, reference: ("+16045550998", "order_trial_001"),
    )
    token = client.post(
        "/api/v1/subscriptions/onboarding/exchange", json={"checkout_session_id": trial_checkout["id"]}
    ).json()["token"]
    activation = client.post(
        f"/api/v1/subscriptions/onboarding/{token}/activate",
        json={
            "business_name": "Trial Plumbing",
            "contact_name": "Taylor Owner",
            "notification_phone": "+16045550101",
            "existing_business_phone": "+16045550102",
            "preferred_area_code": "604",
            "recovery_message": "Hi, Trial Plumbing missed your call. Tell us what you need. Reply STOP to opt out.",
            "timezone": "America/Vancouver",
            "website_url": None,
            "consent_to_text_callers": True,
            "accept_terms": True,
        },
    )
    assert activation.status_code == 200, activation.text
    assert activation.json()["status"] == "active"  # setup completion, not billing state
    headers = {"X-Never-Miss-Token": activation.json()["management_token"]}
    account = client.post("/api/v1/subscriptions/manage/session", headers=headers)
    assert account.status_code == 200
    assert account.json()["status"] == "trialing"
    assert account.json()["enabled"] is True
    assert account.json()["trial_ends_at"].startswith("2027-")

    class FakePortalResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"url": "https://billing.stripe.com/session/test"}

    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_example")
    monkeypatch.setattr(
        "app.presentation.api.v1.routes.subscriptions.httpx.post",
        lambda *args, **kwargs: FakePortalResponse(),
    )
    portal = client.post("/api/v1/subscriptions/manage/billing-portal", headers=headers)
    assert portal.status_code == 200
    assert portal.json()["url"] == "https://billing.stripe.com/session/test"


def test_renewal_failure_and_period_end_cancellation_are_reconciled(client, monkeypatch):
    """Exercise the three billing events that a live trial must survive."""
    assert _post_checkout_webhook(client, monkeypatch).status_code == 200

    paid = _post_stripe_event(
        client,
        "invoice.paid",
        {"id": "in_renewal_001", "subscription": CHECKOUT["subscription"]},
        "evt_invoice_paid_001",
    )
    assert paid.status_code == 200

    cancellation_scheduled = _post_stripe_event(
        client,
        "customer.subscription.updated",
        {
            "id": CHECKOUT["subscription"],
            "status": "active",
            "current_period_end": 1_800_000_000,
            "cancel_at_period_end": True,
        },
        "evt_cancel_at_period_end_001",
    )
    assert cancellation_scheduled.status_code == 200

    failed = _post_stripe_event(
        client,
        "invoice.payment_failed",
        {"id": "in_failed_001", "subscription": CHECKOUT["subscription"]},
        "evt_invoice_failed_001",
    )
    assert failed.status_code == 200

    from app.infrastructure.db.models import ProductSubscription
    from app.infrastructure.db.session import SessionLocal

    session = SessionLocal()
    subscription = session.query(ProductSubscription).filter_by(stripe_subscription_id=CHECKOUT["subscription"]).one()
    assert subscription.status == "past_due"
    assert subscription.cancel_at_period_end is True
    assert subscription.current_period_ends_at.year == 2027
    session.close()


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


def test_stripe_webhook_accepts_the_isolated_test_secret(client, monkeypatch):
    """Sandbox verification must not require replacing the live signing secret."""
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_live")
    monkeypatch.setenv("STRIPE_WEBHOOK_TEST_SECRET", "whsec_test")
    body = json.dumps({
        "id": "evt_test_secret_001",
        "type": "customer.subscription.updated",
        "data": {"object": {"id": "sub_missing", "status": "trialing"}},
    }).encode()
    timestamp = int(time.time())
    signature = hmac.new(
        b"whsec_test", f"{timestamp}.".encode() + body, hashlib.sha256
    ).hexdigest()
    response = client.post(
        "/api/v1/subscriptions/stripe/webhook",
        content=body,
        headers={"Content-Type": "application/json", "Stripe-Signature": f"t={timestamp},v1={signature}"},
    )
    assert response.status_code == 200


def test_management_link_request_does_not_reveal_customer_existence(client, monkeypatch):
    monkeypatch.setattr(
        "app.presentation.api.v1.routes.subscriptions._allow_management_link_request", lambda email: True
    )
    known = client.post("/api/v1/subscriptions/manage/request-link", json={"email": "owner@example.ca"})
    unknown = client.post("/api/v1/subscriptions/manage/request-link", json={"email": "nobody@example.ca"})
    assert known.status_code == 202
    assert unknown.status_code == 202
    assert known.json() == unknown.json()


def test_management_link_request_rejects_invalid_email_and_rate_limit(client, monkeypatch):
    invalid = client.post("/api/v1/subscriptions/manage/request-link", json={"email": "not-an-email"})
    assert invalid.status_code == 422
    monkeypatch.setattr(
        "app.presentation.api.v1.routes.subscriptions._allow_management_link_request", lambda email: False
    )
    blocked = client.post("/api/v1/subscriptions/manage/request-link", json={"email": "owner@example.ca"})
    assert blocked.status_code == 429
    assert blocked.headers["retry-after"] == "3600"
