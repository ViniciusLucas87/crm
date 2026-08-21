"""Shared, conservative renderers for transactional operational emails."""

from __future__ import annotations

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape


def make_usage_alert(config: dict, payload: dict) -> MIMEMultipart:
    business_name = escape(str(payload.get("business_name") or "your business"))
    used = int(payload.get("messages_used") or 0)
    limit = int(payload.get("message_limit") or 0)
    threshold = int(payload.get("threshold_percent") or 0)
    subject = f"Never Miss usage update for {business_name}"
    text = (
        f"Never Miss has sent {used} of {limit} included recovery texts for {business_name} this month. "
        "Automatic recovery texts stop at the plan limit. Please contact Pacific North Systems if you need help reviewing usage."
    )
    html = f"<p>{escape(text)}</p><p>Usage threshold: {threshold}%.</p>"
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{config['from_name']} <{config['from_email']}>"
    msg["To"] = str(payload["contact_email"])
    msg["X-PNS-Message-Type"] = "never-miss-usage-alert"
    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))
    return msg


def make_outreach_email(config: dict, payload: dict) -> MIMEMultipart:
    body = str(payload["body_text"])
    msg = MIMEMultipart("alternative")
    msg["Subject"] = str(payload["subject"])
    msg["From"] = f"{config['from_name']} <{config['from_email']}>"
    msg["To"] = str(payload["contact_email"])
    msg["X-PNS-Message-Type"] = "approved-outreach"
    msg.attach(MIMEText(body, "plain"))
    msg.attach(MIMEText("<p>" + escape(body).replace("\n", "<br>") + "</p>", "html"))
    return msg
