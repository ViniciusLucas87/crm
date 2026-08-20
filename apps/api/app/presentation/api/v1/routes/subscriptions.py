"""Stripe fulfillment and self-service activation for Never Miss."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import time
from datetime import UTC, datetime, timedelta

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import case, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.infrastructure.db.models import (
    Call,
    Organization,
    ProductConfiguration,
    ProductSubscription,
    StripeWebhookEvent,
    Task,
)
from app.infrastructure.db.session import get_db_session

router = APIRouter(prefix="/subscriptions")
_E164 = re.compile(r"^\+[1-9]\d{7,14}$")
_AREA_CODE = re.compile(r"^\d{3}$")


class ActivationInput(BaseModel):
    business_name: str = Field(min_length=2, max_length=255)
    contact_name: str = Field(min_length=2, max_length=255)
    notification_phone: str = Field(max_length=50)
    existing_business_phone: str = Field(max_length=50)
    preferred_area_code: str = Field(pattern=r"^\d{3}$")
    recovery_message: str = Field(min_length=20, max_length=500)
    timezone: str = Field(default="America/Vancouver", max_length=80)
    website_url: str | None = Field(default=None, max_length=500)
    consent_to_text_callers: bool
    accept_terms: bool


class CheckoutExchangeInput(BaseModel):
    checkout_session_id: str = Field(min_length=10, max_length=255)


class ManagementLinkInput(BaseModel):
    email: str = Field(min_length=5, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ManagementUpdateInput(BaseModel):
    notification_phone: str | None = Field(default=None, max_length=50)
    existing_business_phone: str | None = Field(default=None, max_length=50)
    recovery_message: str | None = Field(default=None, min_length=20, max_length=500)
    timezone: str | None = Field(default=None, max_length=80)
    website_url: str | None = Field(default=None, max_length=500)
    enabled: bool | None = None


class RecoveryVerificationInput(BaseModel):
    call_public_uuid: str = Field(min_length=8, max_length=64)
    confirmed_recovery_text_received: bool
    confirmed_callback_task_visible: bool


def _stripe_timestamp(value: object) -> datetime | None:
    try:
        return datetime.fromtimestamp(int(value), UTC) if value else None
    except (TypeError, ValueError, OSError):
        return None


def _apply_subscription_lifecycle(subscription: ProductSubscription, stripe_subscription: dict) -> None:
    """Mirror the billing lifecycle while keeping service enabled during a trial."""
    stripe_status = str(stripe_subscription.get("status") or "")
    subscription.status = {
        "active": "active",
        "trialing": "trialing",
        "past_due": "past_due",
        "unpaid": "past_due",
        "canceled": "cancelled",
        "paused": "cancelled",
    }.get(stripe_status, subscription.status)
    subscription.trial_ends_at = _stripe_timestamp(stripe_subscription.get("trial_end"))
    subscription.current_period_ends_at = _stripe_timestamp(stripe_subscription.get("current_period_end"))
    subscription.cancel_at_period_end = bool(stripe_subscription.get("cancel_at_period_end"))


def _set_service_enabled(session: Session, subscription: ProductSubscription) -> None:
    if not subscription.organization_id:
        return
    config = session.execute(select(ProductConfiguration).where(
        ProductConfiguration.organization_id == subscription.organization_id,
        ProductConfiguration.product_code == "never_miss",
    )).scalar_one_or_none()
    if config:
        config.enabled = subscription.status in {"active", "trialing"}


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _normalize_phone(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    if len(digits) == 10:
        digits = "1" + digits
    normalized = "+" + digits
    if not _E164.fullmatch(normalized):
        raise HTTPException(422, "Enter a valid phone number including country code")
    return normalized


def _plan_for_payment_link(payment_link_id: str | None) -> str | None:
    mapping = {
        os.getenv("STRIPE_NEVER_MISS_PAYMENT_LINK_ID", ""): "never_miss",
        os.getenv("STRIPE_NEVER_MISS_PLUS_PAYMENT_LINK_ID", ""): "never_miss_plus",
    }
    return mapping.get(payment_link_id or "")


def _verify_stripe_signature(payload: bytes, header: str, secret: str) -> None:
    values: dict[str, list[str]] = {}
    for part in header.split(","):
        key, _, value = part.partition("=")
        values.setdefault(key, []).append(value)
    try:
        timestamp = int(values["t"][0])
    except (KeyError, ValueError, IndexError) as exc:
        raise HTTPException(400, "Invalid Stripe signature") from exc
    if abs(int(time.time()) - timestamp) > 300:
        raise HTTPException(400, "Expired Stripe signature")
    signed = f"{timestamp}.".encode() + payload
    expected = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    if not any(hmac.compare_digest(expected, candidate) for candidate in values.get("v1", [])):
        raise HTTPException(400, "Invalid Stripe signature")


def _issue_token(subscription: ProductSubscription, *, channel: str = "email") -> str:
    token = secrets.token_urlsafe(40)
    expires_at = datetime.now(UTC) + timedelta(hours=24)
    if channel == "redirect":
        subscription.redirect_token_hash = _sha256(token)
        subscription.redirect_token_expires_at = expires_at
    else:
        subscription.onboarding_token_hash = _sha256(token)
        subscription.onboarding_token_expires_at = expires_at
    return token


def _issue_management_token(subscription: ProductSubscription) -> str:
    token = secrets.token_urlsafe(40)
    subscription.management_token_hash = _sha256(token)
    subscription.management_token_expires_at = datetime.now(UTC) + timedelta(minutes=30)
    return token


def _allow_management_link_request(email: str) -> bool:
    """Apply global and per-email limits before any database lookup or email delivery."""
    redis_url = os.getenv("REDIS_URL", "")
    if not redis_url:
        return os.getenv("PNS_ENV", "development").lower() != "production"
    try:
        import redis

        client = redis.from_url(redis_url, socket_connect_timeout=2, socket_timeout=2)
        email_key = f"security:never-miss:manage-email:{_sha256(email)}"
        global_key = "security:never-miss:manage-global"
        pipeline = client.pipeline(transaction=True)
        pipeline.incr(email_key)
        pipeline.expire(email_key, 3600, nx=True)
        pipeline.incr(global_key)
        pipeline.expire(global_key, 60, nx=True)
        email_count, _, global_count, _ = pipeline.execute()
        return int(email_count) <= 3 and int(global_count) <= 120
    except Exception:
        # In production, an unavailable guard must not turn into an unlimited email endpoint.
        return os.getenv("PNS_ENV", "development").lower() != "production"


def _fulfill_checkout(session: Session, checkout: dict) -> tuple[ProductSubscription, str | None]:
    session_id = checkout.get("id")
    payment_link_id = checkout.get("payment_link")
    plan = _plan_for_payment_link(payment_link_id)
    if not session_id or not plan:
        raise HTTPException(400, "Checkout does not belong to a Never Miss plan")
    if checkout.get("payment_status") not in {"paid", "no_payment_required"}:
        raise HTTPException(409, "Payment is not confirmed")

    existing = session.execute(
        select(ProductSubscription).where(ProductSubscription.stripe_checkout_session_id == session_id)
    ).scalar_one_or_none()
    if existing:
        return existing, None

    details = checkout.get("customer_details") or {}
    email = details.get("email") or checkout.get("customer_email")
    if not email:
        raise HTTPException(400, "Stripe checkout is missing the customer email")
    token_holder = ProductSubscription(
        stripe_checkout_session_id=session_id,
        stripe_customer_id=checkout.get("customer"),
        stripe_subscription_id=checkout.get("subscription"),
        stripe_payment_link_id=payment_link_id,
        plan=plan,
        # Stripe reports a zero-dollar trial checkout as no_payment_required.
        # Treat it as a usable trial until the subscription lifecycle event
        # supplies the canonical Stripe timestamps.
        status="trialing" if checkout.get("payment_status") == "no_payment_required" else "paid",
        customer_email=email.lower(),
        customer_name=details.get("name"),
        notification_phone=details.get("phone"),
    )
    token = _issue_token(token_holder)
    session.add(token_holder)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        found = session.execute(
            select(ProductSubscription).where(ProductSubscription.stripe_checkout_session_id == session_id)
        ).scalar_one()
        return found, None
    session.refresh(token_holder)
    return token_holder, token


def _email_activation_link(subscription: ProductSubscription, token: str) -> None:
    api_key = os.getenv("RESEND_API_KEY", "")
    site_url = os.getenv("MARKETING_SITE_URL", "https://www.pacificnorthsystems.com").rstrip("/")
    if not api_key:
        return
    link = f"{site_url}/never-miss/activate?token={token}"
    httpx.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "from": os.getenv("RESEND_FROM_EMAIL", "Pacific North Systems <hello@pacificnorthsystems.com>"),
            "to": [subscription.customer_email],
            "subject": "Activate your Never Miss service",
            "html": (
                "<h1>Your Never Miss trial is confirmed</h1>"
                "<p>Complete the short setup to activate your Never Miss phone workflow.</p>"
                f'<p><a href="{link}">Activate Never Miss</a></p>'
                "<p>This private link expires in 24 hours.</p>"
            ),
        },
        timeout=5,
    ).raise_for_status()


def _email_management_link(subscription: ProductSubscription, token: str) -> None:
    api_key = os.getenv("RESEND_API_KEY", "")
    if not api_key:
        return
    site_url = os.getenv("MARKETING_SITE_URL", "https://www.pacificnorthsystems.com").rstrip("/")
    # A URL fragment is handled only by the browser and is never sent to web access logs.
    link = f"{site_url}/never-miss/manage#token={token}"
    httpx.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "from": os.getenv("RESEND_FROM_EMAIL", "Pacific North Systems <hello@pacificnorthsystems.com>"),
            "to": [subscription.customer_email],
            "subject": "Your secure Never Miss account link",
            "html": (
                "<h1>Manage Never Miss</h1>"
                "<p>Use this private link to update your service, pause automatic replies, or manage billing.</p>"
                f'<p><a href="{link}">Open my Never Miss account</a></p>'
                "<p>This link expires in 30 minutes. If you did not request it, you can ignore this email.</p>"
            ),
        },
        timeout=5,
    ).raise_for_status()


def _management_subscription(session: Session, token: str) -> ProductSubscription:
    subscription = session.execute(select(ProductSubscription).where(
        ProductSubscription.management_token_hash == _sha256(token)
    )).scalar_one_or_none()
    if not subscription or not subscription.management_token_expires_at:
        raise HTTPException(404, "This account link is invalid")
    expires = subscription.management_token_expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=UTC)
    if expires < datetime.now(UTC):
        raise HTTPException(410, "This account link has expired. Request a fresh link.")
    return subscription


def _management_payload(session: Session, subscription: ProductSubscription) -> dict:
    config = None
    if subscription.organization_id:
        config = session.execute(select(ProductConfiguration).where(
            ProductConfiguration.organization_id == subscription.organization_id,
            ProductConfiguration.product_code == "never_miss",
        )).scalar_one_or_none()
    settings = config.business_hours_json or {} if config else {}
    month_start = datetime.now(UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    calls_this_month = 0
    messages_this_month = 0
    last_call_at = None
    recent_recovery_tests: list[dict] = []
    if subscription.organization_id:
        calls = session.execute(
            select(Call).where(
                Call.organization_id == subscription.organization_id,
                Call.direction == "inbound",
                Call.created_at >= month_start,
            ).order_by(Call.created_at.desc())
        ).scalars().all()
        calls_this_month = len(calls)
        messages_this_month = sum(1 for call in calls if call.sms_sent_at is not None)
        last_call_at = calls[0].created_at.isoformat() if calls else None
        recovered_calls = [call for call in calls if call.sms_sent_at is not None][:5]
        for call in recovered_calls:
            callback_exists = session.execute(select(Task.id).where(
                Task.organization_id == subscription.organization_id,
                Task.recovery_key == f"missed_call_{call.public_uuid}",
            )).scalar_one_or_none() is not None
            recent_recovery_tests.append({
                "call_public_uuid": call.public_uuid,
                "detected_at": call.created_at.isoformat(),
                "sms_sent_at": call.sms_sent_at.isoformat() if call.sms_sent_at else None,
                "callback_task_created": callback_exists,
            })
    recovery_test = settings.get("recovery_test") if isinstance(settings.get("recovery_test"), dict) else None
    return {
        "plan": subscription.plan,
        "status": subscription.status,
        "business_name": subscription.business_name,
        "customer_email": subscription.customer_email,
        "assigned_phone": subscription.assigned_phone,
        "existing_business_phone": subscription.existing_phone,
        "notification_phone": subscription.notification_phone,
        "recovery_message": config.recovery_message if config else None,
        "enabled": bool(config.enabled) if config else False,
        "timezone": settings.get("timezone"),
        "website_url": settings.get("website_url"),
        "billing_portal_available": bool(subscription.stripe_customer_id and os.getenv("STRIPE_SECRET_KEY")),
        "support_email": os.getenv("SUPPORT_EMAIL", "hello@pacificnorthsystems.com"),
        "calls_this_month": calls_this_month,
        "messages_this_month": messages_this_month,
        "monthly_call_limit": config.monthly_call_limit if config else 0,
        "monthly_message_limit": config.monthly_message_limit if config else 0,
        "last_call_at": last_call_at,
        "setup_ready": bool(subscription.assigned_phone and subscription.existing_phone and config and config.enabled),
        "recovery_test": recovery_test,
        "recent_recovery_tests": recent_recovery_tests,
        "trial_ends_at": subscription.trial_ends_at.isoformat() if subscription.trial_ends_at else None,
        "current_period_ends_at": subscription.current_period_ends_at.isoformat() if subscription.current_period_ends_at else None,
        "cancel_at_period_end": subscription.cancel_at_period_end,
    }


def _email_cancellation_instructions(subscription: ProductSubscription) -> None:
    api_key = os.getenv("RESEND_API_KEY", "")
    if not api_key:
        return
    site_url = os.getenv("MARKETING_SITE_URL", "https://www.pacificnorthsystems.com").rstrip("/")
    httpx.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "from": os.getenv("RESEND_FROM_EMAIL", "Pacific North Systems <hello@pacificnorthsystems.com>"),
            "to": [subscription.customer_email],
            "subject": "Your Never Miss service has been cancelled",
            "html": (
                "<h1>Your Never Miss subscription is cancelled</h1>"
                "<p>Automatic missed-call replies have been turned off.</p>"
                "<p><strong>Important:</strong> remove unanswered-call forwarding from your phone or carrier account so unanswered callers return to your normal voicemail.</p>"
                f'<p>Your service history is retained. <a href="{site_url}/never-miss/manage">Open your account</a> if you need your records or support.</p>'
            ),
        },
        timeout=5,
    ).raise_for_status()


@router.post("/stripe/webhook", include_in_schema=False)
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(default=None),
    session: Session = Depends(get_db_session),
):
    secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    if not secret or not stripe_signature:
        raise HTTPException(503 if not secret else 400, "Stripe webhook is not configured")
    raw = await request.body()
    _verify_stripe_signature(raw, stripe_signature, secret)
    try:
        event = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(400, "Invalid JSON") from exc
    event_id = event.get("id")
    if not event_id:
        raise HTTPException(400, "Missing Stripe event ID")
    if session.execute(select(StripeWebhookEvent).where(StripeWebhookEvent.stripe_event_id == event_id)).scalar_one_or_none():
        return {"received": True, "duplicate": True}

    event_type = event.get("type", "unknown")
    obj = (event.get("data") or {}).get("object") or {}
    token = None
    subscription = None
    if event_type in {"checkout.session.completed", "checkout.session.async_payment_succeeded"}:
        subscription, token = _fulfill_checkout(session, obj)
    elif event_type in {"customer.subscription.deleted", "customer.subscription.paused", "invoice.payment_failed"}:
        stripe_subscription_id = obj.get("subscription") if event_type.startswith("invoice.") else obj.get("id")
        subscription = session.execute(
            select(ProductSubscription).where(ProductSubscription.stripe_subscription_id == stripe_subscription_id)
        ).scalar_one_or_none()
        if subscription:
            subscription.status = "past_due" if event_type == "invoice.payment_failed" else "cancelled"
            if subscription.organization_id:
                config = session.execute(select(ProductConfiguration).where(
                    ProductConfiguration.organization_id == subscription.organization_id,
                    ProductConfiguration.product_code == "never_miss",
                )).scalar_one_or_none()
                if config:
                    config.enabled = False
    elif event_type in {"customer.subscription.created", "customer.subscription.updated"}:
        subscription = session.execute(
            select(ProductSubscription).where(ProductSubscription.stripe_subscription_id == obj.get("id"))
        ).scalar_one_or_none()
        if subscription:
            _apply_subscription_lifecycle(subscription, obj)
            _set_service_enabled(session, subscription)
    elif event_type == "invoice.paid":
        stripe_subscription_id = obj.get("subscription")
        subscription = session.execute(
            select(ProductSubscription).where(ProductSubscription.stripe_subscription_id == stripe_subscription_id)
        ).scalar_one_or_none()
        if subscription and subscription.activated_at:
            subscription.status = "active"
            _set_service_enabled(session, subscription)

    session.add(StripeWebhookEvent(
        stripe_event_id=event_id,
        event_type=event_type,
        livemode=bool(event.get("livemode")),
    ))
    session.commit()
    if event_type == "customer.subscription.deleted" and subscription:
        try:
            _email_cancellation_instructions(subscription)
        except Exception:
            pass
    if subscription and token:
        try:
            _email_activation_link(subscription, token)
        except Exception:
            # Payment fulfillment remains durable; the Stripe redirect is the second delivery path.
            pass
    return {"received": True}


@router.post("/onboarding/exchange")
def exchange_checkout_session(
    payload: CheckoutExchangeInput,
    session: Session = Depends(get_db_session),
):
    # The signed webhook is the authority. Payment Links wait briefly for the
    # checkout.session.completed webhook before redirecting here, so no broad
    # Stripe API key is required in our runtime.
    subscription = session.execute(
        select(ProductSubscription).where(
            ProductSubscription.stripe_checkout_session_id == payload.checkout_session_id
        )
    ).scalar_one_or_none()
    if subscription is None:
        raise HTTPException(409, "Payment confirmation is still arriving. Please try again in a few seconds.")
    if subscription.status in {"active", "trialing"} and subscription.assigned_phone:
        management_token = _issue_management_token(subscription)
        session.commit()
        return {
            # This value describes completed setup, not the billing status.
            "status": "active",
            "token": None,
            "plan": subscription.plan,
            "assigned_phone": subscription.assigned_phone,
            "forward_from": subscription.existing_phone,
            "management_token": management_token,
        }
    token = _issue_token(subscription, channel="redirect")
    session.commit()
    return {"status": subscription.status, "token": token}


@router.post("/manage/request-link", status_code=202)
def request_management_link(payload: ManagementLinkInput, session: Session = Depends(get_db_session)):
    # Always return the same response so this endpoint cannot be used to discover customers.
    email = payload.email.strip().lower()
    if not _allow_management_link_request(email):
        raise HTTPException(429, "Too many requests. Please wait before requesting another link.", headers={"Retry-After": "3600"})
    subscription = session.execute(
        select(ProductSubscription)
        .where(ProductSubscription.customer_email == email)
        .order_by(
            case((ProductSubscription.status == "active", 0), (ProductSubscription.status == "paid", 1), else_=2),
            ProductSubscription.created_at.desc(),
        )
    ).scalars().first()
    if subscription:
        token = _issue_management_token(subscription)
        session.commit()
        try:
            _email_management_link(subscription, token)
        except Exception:
            pass
    return {"message": "If that email has a Never Miss account, a secure link is on its way."}


@router.post("/manage/session")
def management_status(
    x_never_miss_token: str = Header(min_length=20, max_length=255),
    session: Session = Depends(get_db_session),
):
    token = x_never_miss_token
    return _management_payload(session, _management_subscription(session, token))


@router.post("/manage/billing-portal")
def create_billing_portal_session(
    x_never_miss_token: str = Header(min_length=20, max_length=255),
    session: Session = Depends(get_db_session),
):
    """Create a short-lived, customer-scoped Stripe portal session."""
    subscription = _management_subscription(session, x_never_miss_token)
    stripe_key = os.getenv("STRIPE_SECRET_KEY", "")
    if not stripe_key or not subscription.stripe_customer_id:
        raise HTTPException(503, "Billing self-service is not available yet. Contact support for help.")
    site_url = os.getenv("MARKETING_SITE_URL", "https://www.pacificnorthsystems.com").rstrip("/")
    try:
        response = httpx.post(
            "https://api.stripe.com/v1/billing_portal/sessions",
            headers={"Authorization": f"Bearer {stripe_key}"},
            data={
                "customer": subscription.stripe_customer_id,
                "return_url": f"{site_url}/never-miss/manage",
            },
            timeout=10,
        )
        response.raise_for_status()
        url = response.json().get("url")
    except httpx.HTTPError as exc:
        raise HTTPException(502, "Could not open billing self-service. Please try again shortly.") from exc
    if not isinstance(url, str) or not url.startswith("https://"):
        raise HTTPException(502, "Billing self-service returned an invalid URL")
    return {"url": url}


@router.patch("/manage/settings")
def update_management(
    payload: ManagementUpdateInput,
    x_never_miss_token: str = Header(min_length=20, max_length=255),
    session: Session = Depends(get_db_session),
):
    token = x_never_miss_token
    subscription = _management_subscription(session, token)
    if not subscription.organization_id:
        raise HTTPException(409, "Finish activation before changing service settings")
    config = session.execute(select(ProductConfiguration).where(
        ProductConfiguration.organization_id == subscription.organization_id,
        ProductConfiguration.product_code == "never_miss",
    )).scalar_one_or_none()
    if not config:
        raise HTTPException(404, "Never Miss configuration was not found")
    if payload.enabled is True and subscription.status not in {"active", "trialing"}:
        raise HTTPException(409, "Billing must be active before automatic replies can be enabled")
    if payload.notification_phone is not None:
        value = _normalize_phone(payload.notification_phone)
        subscription.notification_phone = value
        config.notification_phone = value
    if payload.existing_business_phone is not None:
        value = _normalize_phone(payload.existing_business_phone)
        subscription.existing_phone = value
        settings = dict(config.business_hours_json or {})
        settings["existing_business_phone"] = value
        config.business_hours_json = settings
    if payload.recovery_message is not None:
        config.recovery_message = payload.recovery_message.strip()
    if payload.timezone is not None or payload.website_url is not None:
        settings = dict(config.business_hours_json or {})
        if payload.timezone is not None:
            settings["timezone"] = payload.timezone
        if payload.website_url is not None:
            settings["website_url"] = payload.website_url or None
        config.business_hours_json = settings
    if payload.enabled is not None:
        config.enabled = payload.enabled
    session.commit()
    return _management_payload(session, subscription)


@router.post("/manage/verify-recovery")
def verify_recovery_test(
    payload: RecoveryVerificationInput,
    x_never_miss_token: str = Header(min_length=20, max_length=255),
    session: Session = Depends(get_db_session),
):
    """Record a customer-confirmed, end-to-end missed-call recovery test."""
    if not payload.confirmed_recovery_text_received or not payload.confirmed_callback_task_visible:
        raise HTTPException(422, "Confirm both the recovery text and callback task before completing the test")
    subscription = _management_subscription(session, x_never_miss_token)
    if not subscription.organization_id:
        raise HTTPException(409, "Finish activation before running a recovery test")
    config = session.execute(select(ProductConfiguration).where(
        ProductConfiguration.organization_id == subscription.organization_id,
        ProductConfiguration.product_code == "never_miss",
    )).scalar_one_or_none()
    call = session.execute(select(Call).where(
        Call.organization_id == subscription.organization_id,
        Call.public_uuid == payload.call_public_uuid,
        Call.sms_sent_at.is_not(None),
        Call.sms_status == "sent",
    )).scalar_one_or_none()
    if not config or not call:
        raise HTTPException(409, "That call is not a completed recovery test yet. Refresh after the text arrives.")
    callback_exists = session.execute(select(Task.id).where(
        Task.organization_id == subscription.organization_id,
        Task.recovery_key == f"missed_call_{call.public_uuid}",
    )).scalar_one_or_none()
    if not callback_exists:
        raise HTTPException(409, "The callback task is not ready yet. Refresh in a moment.")
    settings = dict(config.business_hours_json or {})
    settings["recovery_test"] = {
        "verified_at": datetime.now(UTC).isoformat(),
        "call_public_uuid": call.public_uuid,
    }
    config.business_hours_json = settings
    session.commit()
    return _management_payload(session, subscription)


def _subscription_for_token(session: Session, token: str) -> ProductSubscription:
    token_hash = _sha256(token)
    subscription = session.execute(
        select(ProductSubscription).where(
            (ProductSubscription.onboarding_token_hash == token_hash)
            | (ProductSubscription.redirect_token_hash == token_hash)
        )
    ).scalar_one_or_none()
    if not subscription:
        raise HTTPException(404, "This activation link is invalid")
    expires = (
        subscription.onboarding_token_expires_at
        if subscription.onboarding_token_hash == token_hash
        else subscription.redirect_token_expires_at
    )
    if not expires:
        raise HTTPException(404, "This activation link is invalid")
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=UTC)
    if expires < datetime.now(UTC) and subscription.status not in {"active", "trialing"}:
        raise HTTPException(410, "This activation link has expired")
    return subscription


@router.get("/onboarding/{token}")
def onboarding_status(token: str, session: Session = Depends(get_db_session)):
    subscription = _subscription_for_token(session, token)
    return {
        "plan": subscription.plan,
        "status": subscription.status,
        "customer_name": subscription.customer_name,
        "business_name": subscription.business_name,
        "notification_phone": subscription.notification_phone,
        "assigned_phone": subscription.assigned_phone,
    }


def _slug(session: Session, business_name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", business_name.lower()).strip("-")[:90] or "customer"
    candidate = base
    suffix = 2
    while session.execute(select(Organization).where(Organization.slug == candidate)).scalar_one_or_none():
        candidate = f"{base}-{suffix}"
        suffix += 1
    return candidate


def _provision_telnyx_number(area_code: str, reference: str) -> tuple[str, str]:
    if os.getenv("TELNYX_AUTO_PROVISION_ENABLED", "false").lower() != "true":
        raise RuntimeError("Automatic number provisioning is not enabled")
    api_key = os.getenv("TELNYX_API_KEY", "")
    # New customer numbers must receive inbound Call Control webhooks. The
    # credential connection is outbound-only and would immediately reject calls.
    connection_id = os.getenv("TELNYX_APPLICATION_ID", "") or os.getenv("TELNYX_CONNECTION_ID", "")
    messaging_profile_id = os.getenv("TELNYX_MESSAGING_PROFILE_ID", "")
    if not all((api_key, connection_id, messaging_profile_id)):
        raise RuntimeError("Telnyx provisioning credentials are incomplete")
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    search = httpx.get(
        "https://api.telnyx.com/v2/available_phone_numbers",
        headers=headers,
        params={
            "filter[country_code]": "CA",
            "filter[national_destination_code]": area_code,
            "filter[phone_number_type]": "local",
            "filter[features][]": "sms,voice",
            "page[size]": 5,
        },
        timeout=15,
    )
    search.raise_for_status()
    choices = search.json().get("data") or []
    if not choices:
        raise RuntimeError("No phone number is currently available in that area code")
    phone = choices[0]["phone_number"]
    order = httpx.post(
        "https://api.telnyx.com/v2/number_orders",
        headers=headers,
        json={
            "phone_numbers": [{"phone_number": phone}],
            "connection_id": connection_id,
            "messaging_profile_id": messaging_profile_id,
            "customer_reference": reference,
        },
        timeout=20,
    )
    order.raise_for_status()
    data = order.json().get("data") or {}
    return phone, str(data.get("id") or "")


@router.post("/onboarding/{token}/activate")
def activate_subscription(token: str, payload: ActivationInput, session: Session = Depends(get_db_session)):
    subscription = _subscription_for_token(session, token)
    if subscription.status in {"active", "trialing"} and subscription.assigned_phone:
        return {"status": "active", "assigned_phone": subscription.assigned_phone, "plan": subscription.plan}
    if not payload.accept_terms or not payload.consent_to_text_callers:
        raise HTTPException(422, "Consent and service terms are required")
    notification_phone = _normalize_phone(payload.notification_phone)
    existing_phone = _normalize_phone(payload.existing_business_phone)

    billing_status = subscription.status
    subscription.status = "provisioning"
    subscription.business_name = payload.business_name.strip()
    subscription.customer_name = payload.contact_name.strip()
    subscription.notification_phone = notification_phone
    subscription.existing_phone = existing_phone
    subscription.onboarding_data_json = payload.model_dump(exclude={"accept_terms"})
    subscription.last_error = None
    session.commit()

    try:
        if subscription.assigned_phone:
            assigned_phone = subscription.assigned_phone
            order_id = subscription.telnyx_number_order_id or ""
        else:
            assigned_phone, order_id = _provision_telnyx_number(payload.preferred_area_code, f"pns-subscription-{subscription.id}")
            # Persist the purchased asset before any later database work. A safe
            # retry must reuse this number instead of purchasing another one.
            subscription.assigned_phone = assigned_phone
            subscription.telnyx_number_order_id = order_id
            session.commit()
        organization = Organization(name=payload.business_name.strip(), slug=_slug(session, payload.business_name))
        session.add(organization)
        session.flush()
        limits = (50, 100) if subscription.plan == "never_miss" else (250, 500)
        config = ProductConfiguration(
            organization_id=organization.id,
            product_code="never_miss",
            enabled=True,
            plan=subscription.plan,
            business_name=payload.business_name.strip(),
            business_phone=assigned_phone,
            notification_phone=notification_phone,
            recovery_message=payload.recovery_message.strip(),
            business_hours_json={"timezone": payload.timezone, "existing_business_phone": existing_phone, "website_url": payload.website_url},
            monthly_call_limit=limits[0],
            monthly_message_limit=limits[1],
        )
        session.add(config)
        subscription.organization_id = organization.id
        subscription.status = "trialing" if billing_status == "trialing" else "active"
        subscription.activated_at = datetime.now(UTC)
        management_token = _issue_management_token(subscription)
        session.commit()
        try:
            _email_management_link(subscription, management_token)
        except Exception:
            pass
        return {
            "status": "active",
            "plan": subscription.plan,
            "assigned_phone": assigned_phone,
            "forward_from": existing_phone,
            "management_token": management_token,
            "next_step": "Forward unanswered calls from your business number to your new Never Miss number, then place one unanswered test call.",
        }
    except Exception as exc:
        session.rollback()
        subscription = _subscription_for_token(session, token)
        subscription.status = "failed"
        subscription.last_error = str(exc)[:1000]
        session.commit()
        raise HTTPException(503, "We saved your setup, but automatic phone activation did not finish. Please retry shortly.") from exc
