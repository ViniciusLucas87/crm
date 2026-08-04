"""Cryptographic verification tests for Telnyx API v2 webhooks."""

import base64
from datetime import UTC, datetime

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.application.intake import webhook_verify


def _key_pair(monkeypatch):
    private_key = Ed25519PrivateKey.generate()
    public_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    monkeypatch.setattr(
        webhook_verify,
        "TELNYX_PUBLIC_KEY",
        base64.b64encode(public_bytes).decode(),
    )
    return private_key


def test_valid_telnyx_signature_uses_pipe_separator(monkeypatch):
    private_key = _key_pair(monkeypatch)
    body = b'{"data":{"event_type":"call.initiated"}}'
    timestamp = str(int(datetime.now(UTC).timestamp()))
    signature = private_key.sign(f"{timestamp}|{body.decode()}".encode())

    assert webhook_verify.verify_webhook_signature(
        body,
        base64.b64encode(signature).decode(),
        timestamp,
    )


def test_dot_separator_signature_is_rejected(monkeypatch):
    private_key = _key_pair(monkeypatch)
    body = b'{"data":{"event_type":"call.initiated"}}'
    timestamp = str(int(datetime.now(UTC).timestamp()))
    signature = private_key.sign(f"{timestamp}.{body.decode()}".encode())

    assert not webhook_verify.verify_webhook_signature(
        body,
        base64.b64encode(signature).decode(),
        timestamp,
    )


def test_stale_signature_is_rejected(monkeypatch):
    private_key = _key_pair(monkeypatch)
    body = b"{}"
    timestamp = "1"
    signature = private_key.sign(f"{timestamp}|{body.decode()}".encode())

    assert not webhook_verify.verify_webhook_signature(
        body,
        base64.b64encode(signature).decode(),
        timestamp,
    )
