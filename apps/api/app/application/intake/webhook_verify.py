"""
Telnyx webhook signature verification (Ed25519).
Verifies raw request body against Telnyx public key.
"""

import base64
import hashlib
import json
import logging
import os
from datetime import UTC, datetime, timedelta

logger = logging.getLogger(__name__)

# Public key from https://telnyx.com/webhook-signing-public-key
# Ed25519 public key in base64
TELNYX_PUBLIC_KEY = os.getenv(
    "TELNYX_WEBHOOK_PUBLIC_KEY",
    "",  # Must be set via environment
)


def verify_webhook_signature(
    raw_body: bytes,
    signature_header: str,
    timestamp_header: str,
) -> bool:
    """Verify Telnyx Ed25519 webhook signature.
    
    Args:
        raw_body: Raw request body bytes (must not be parsed/decoded first)
        signature_header: telnyx-signature-ed25519 header value
        timestamp_header: telnyx-timestamp header value
    
    Returns True if signature is valid and timestamp is within tolerance.
    """
    if not TELNYX_PUBLIC_KEY:
        logger.error("TELNYX_WEBHOOK_PUBLIC_KEY not configured")
        return False

    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        from cryptography.exceptions import InvalidSignature
    except ImportError:
        logger.error("cryptography package not installed; cannot verify webhooks")
        return False

    # Verify timestamp freshness (5-minute tolerance)
    try:
        ts = int(timestamp_header)
        event_time = datetime.fromtimestamp(ts, tz=UTC)
        now = datetime.now(UTC)
        if abs((now - event_time).total_seconds()) > 300:
            logger.warning("webhook timestamp %s is outside 5-minute tolerance", ts)
            return False
    except (ValueError, TypeError):
        logger.warning("invalid webhook timestamp: %s", timestamp_header)
        return False

    # Decode signature and public key
    try:
        signature_bytes = base64.b64decode(signature_header)
        public_key_bytes = base64.b64decode(TELNYX_PUBLIC_KEY)
    except Exception as e:
        logger.error("failed to decode webhook signature or public key: %s", e)
        return False

    # Telnyx API v2 signs the timestamp, a pipe separator, and the raw body.
    try:
        public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
        signed_payload = f"{timestamp_header}|{raw_body.decode('utf-8')}".encode("utf-8")
        public_key.verify(signature_bytes, signed_payload)
        return True
    except InvalidSignature:
        logger.warning("invalid Telnyx webhook signature")
        return False
    except Exception as e:
        logger.error("webhook verification error: %s", e)
        return False
