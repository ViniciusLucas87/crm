"""Durable monthly usage notifications for Never Miss."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime


def queue_usage_alert(db, subscription_model, outbox_model, config, organization_id: int, messages_used: int, threshold_percent: int) -> None:
    """Queue one alert per threshold and billing month, without interrupting recovery."""
    subscription = db.query(subscription_model).filter(
        subscription_model.organization_id == organization_id,
    ).order_by(subscription_model.created_at.desc()).first()
    if not subscription or not subscription.customer_email:
        return

    month_key = datetime.now(UTC).strftime("%Y-%m")
    settings = dict(config.business_hours_json or {})
    sent = dict(settings.get("usage_alerts") or {})
    sent_for_month = set(sent.get(month_key) or [])
    if threshold_percent in sent_for_month:
        return

    digest = hashlib.sha256(f"{organization_id}:{month_key}:{threshold_percent}".encode()).hexdigest()
    db.add(outbox_model(
        event_type="never_miss.usage_alert.requested",
        payload_json={
            "organization_id": organization_id,
            "contact_email": subscription.customer_email,
            "business_name": subscription.business_name or config.business_name,
            "messages_used": messages_used,
            "message_limit": config.monthly_message_limit,
            "threshold_percent": threshold_percent,
        },
        correlation_id=digest[:64],
        idempotency_key=f"nm-usage-{digest}",
    ))
    sent_for_month.add(threshold_percent)
    sent[month_key] = sorted(sent_for_month)
    settings["usage_alerts"] = sent
    config.business_hours_json = settings
