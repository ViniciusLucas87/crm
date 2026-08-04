"""
Telnyx Call Provider.

Isolated implementation — all Telnyx-specific code lives here.
CRM code never imports this directly.

Uses modern browser authentication (client tokens, not SIP credentials).
API keys never leave the backend.
"""

import base64
import hashlib
import hmac
import json
import logging
import uuid
from typing import Any

import httpx

from app.application.telephony import CallProvider, CallResult

logger = logging.getLogger(__name__)

TELNYX_API_BASE = "https://api.telnyx.com/v2"


class TelnyxProvider(CallProvider):
    """Telnyx telephony provider.

    Authenticates via API key. Generates temporary client tokens
    for browser-based calling. Supports webhook signature verification.
    """

    def __init__(self, config: dict[str, str]) -> None:
        self._api_key = config.get("api_key", "")
        self._application_id = config.get("application_id", "")
        self._connection_id = config.get("connection_id", "")
        self._phone_number = config.get("phone_number", "")
        self._webhook_secret = config.get("webhook_secret", "")
        self._public_url = config.get("public_url", "")
        self._initialized = False
        self._http: httpx.AsyncClient | None = None

    @property
    def provider_name(self) -> str:
        return "telnyx"

    async def initialize(self, config: dict[str, str]) -> bool:
        """Initialize Telnyx client with API key and application ID."""
        self._api_key = config.get("api_key", self._api_key)
        self._application_id = config.get("application_id", self._application_id)
        self._connection_id = config.get("connection_id", self._connection_id)
        self._phone_number = config.get("phone_number", self._phone_number)
        self._webhook_secret = config.get("webhook_secret", self._webhook_secret)
        self._public_url = config.get("public_url", self._public_url)

        if not self._api_key:
            logger.error("Telnyx: missing TELNYX_API_KEY")
            return False
        if not self._connection_id:
            logger.error("Telnyx: missing TELNYX_CONNECTION_ID")
            return False

        self._http = httpx.AsyncClient(
            base_url=TELNYX_API_BASE,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=30.0,
        )

        # Verify the credential connection used by browser calling.
        try:
            r = await self._http.get(f"/connections/{self._connection_id}")
            if r.status_code == 200:
                connection = r.json().get("data", {})
                logger.info(
                    "Telnyx initialized: connection=%s type=%s",
                    connection.get("connection_name", "unknown"),
                    connection.get("record_type", "unknown"),
                )
            else:
                logger.warning("Telnyx: connection check HTTP %s, continuing", r.status_code)
        except Exception as e:
            logger.warning("Telnyx: connectivity check failed (%s), continuing", e)

        self._initialized = True
        return True

    async def generate_token(self, user_id: str) -> dict[str, Any]:
        """Generate a WebRTC telephony credential for browser-based calling.

        Uses Telnyx's Telephony Credentials API (POST /v2/telephony_credentials).
        This is the correct current endpoint per official Telnyx docs:
        https://developers.telnyx.com/api/webrtc/create-telephony-credential

        The old client_state + client_token flow is deprecated and returns 404.
        """
        if not self._initialized or not self._http:
            return {
                "token": "",
                "error": "Provider not initialized",
                "provider": "telnyx",
                "diagnostics": {"initialized": False},
            }

        import time as _time
        t0 = _time.monotonic()
        correlation_id = f"telnyx-token-{user_id}-{int(t0*1000)}"
        endpoint = "/telephony_credentials"

        try:
            payload = {
                "connection_id": self._connection_id,
            }
            logger.info(
                "Telnyx: POST %s | correlation=%s | connection_id=%s | user=%s",
                endpoint, correlation_id,
                self._connection_id[:8] + "..." if self._connection_id else "missing",
                user_id,
            )

            r = await self._http.post(endpoint, json=payload)
            elapsed_ms = (_time.monotonic() - t0) * 1000
            resp_text = r.text[:1000]

            logger.info(
                "Telnyx: POST %s completed | correlation=%s | status=%s | elapsed=%.0fms | body=%s",
                endpoint, correlation_id, r.status_code, elapsed_ms, resp_text,
            )

            if r.status_code not in (200, 201):
                logger.error(
                    "Telnyx: telephony_credentials failed | correlation=%s | status=%s | body=%s",
                    correlation_id, r.status_code, r.text,
                )
                return {
                    "token": "",
                    "error": f"Telephony credentials failed: HTTP {r.status_code}",
                    "provider": "telnyx",
                    "diagnostics": {
                        "endpoint": f"{TELNYX_API_BASE}{endpoint}",
                        "status": r.status_code,
                        "response_body": r.text[:500],
                        "elapsed_ms": round(elapsed_ms, 1),
                        "correlation_id": correlation_id,
                    },
                }

            data = r.json()
            # Telnyx returns { "data": { "sip_username", "sip_password", "id", ... } }
            # The @telnyx/webrtc SDK expects login_token = base64("sip_username:sip_password")
            inner = data.get("data", {})
            sip_username = inner.get("sip_username", "")
            sip_password = inner.get("sip_password", "")
            # Build the SDK-compatible login token
            if sip_username and sip_password:
                raw = f"{sip_username}:{sip_password}"
                login_token = base64.b64encode(raw.encode()).decode()
            else:
                login_token = inner.get("token") or data.get("token", "")

            logger.info(
                "Telnyx: telephony credential created | correlation=%s | credential_id=%s | has_credentials=%s",
                correlation_id,
                inner.get("id", ""),
                bool(sip_username and sip_password),
            )

            return {
                "token": login_token,
                "sip_username": sip_username,
                "sip_password": sip_password,
                "connection_id": self._connection_id,
                "credential_id": inner.get("id", ""),
                "expires_at": inner.get("expires_at") or data.get("expires_at", ""),
                "provider": "telnyx",
                "diagnostics": {
                    "endpoint": f"{TELNYX_API_BASE}{endpoint}",
                    "status": r.status_code,
                    "elapsed_ms": round(elapsed_ms, 1),
                    "correlation_id": correlation_id,
                    "has_credentials": bool(sip_username and sip_password),
                    "credential_id": inner.get("id", ""),
                },
            }

        except Exception as exc:
            elapsed_ms = (_time.monotonic() - t0) * 1000
            logger.error(
                "Telnyx: telephony_credentials exception | correlation=%s | error=%s | elapsed=%.0fms",
                correlation_id, exc, elapsed_ms,
            )
            return {
                "token": "",
                "error": f"Telephony credentials exception: {type(exc).__name__}",
                "provider": "telnyx",
                "diagnostics": {
                    "endpoint": f"{TELNYX_API_BASE}{endpoint}",
                    "exception": str(exc),
                    "elapsed_ms": round(elapsed_ms, 1),
                    "correlation_id": correlation_id,
                },
            }

        except httpx.RequestError as e:
            logger.error("Telnyx: token request failed: %s", e)
            return {"token": "", "error": str(e)}

    async def start_call(self, to_number: str, caller_id: str | None = None) -> CallResult:
        """Initiate an outbound call via Telnyx Voice API."""
        if not self._initialized or not self._http:
            return CallResult(provider="telnyx", status="failed", error="Provider not initialized")

        from_number = caller_id or self._phone_number
        call_ref = f"telnyx_{uuid.uuid4().hex[:16]}"

        # Telnyx requires client_state to be a valid base64 string
        import base64
        client_state_b64 = base64.b64encode(call_ref.encode()).decode()

        try:
            payload = {
                "connection_id": self._connection_id,
                "to": to_number,
                "from": from_number,
                "from_display_name": "Pacific North Systems",
                "client_state": client_state_b64,
                "webhook_url": f"{self._public_url}/api/v1/telephony/webhook" if self._public_url else None,
                "webhook_url_method": "POST",
            }
            logger.info("Telnyx: creating call: %s", json.dumps({k: v for k, v in payload.items() if k != "client_state"}, default=str))
            r = await self._http.post("/calls", json=payload)

            if r.status_code in (200, 201):
                data = r.json().get("data", {})
                actual_id = data.get("call_control_id") or data.get("id") or call_ref
                logger.info("Telnyx: outbound call %s → %s (%s)", from_number, to_number, actual_id)
                return CallResult(
                    provider="telnyx",
                    provider_call_id=actual_id,
                    status="dialing",
                    direction="outbound",
                    phone_number=to_number,
                    metadata={"telnyx_call_control_id": actual_id},
                )
            else:
                detail = ""
                try:
                    detail = r.json().get("errors", [{}])[0].get("detail", r.text)
                except Exception:
                    detail = r.text
                logger.error("Telnyx: call create failed (HTTP %s): %s", r.status_code, detail)
                return CallResult(provider="telnyx", status="failed", error=f"Call failed: {detail}")

        except httpx.RequestError as e:
            logger.error("Telnyx: call request failed: %s", e)
            return CallResult(provider="telnyx", status="failed", error=str(e))

    async def end_call(self, provider_call_id: str) -> CallResult:
        """End an active Telnyx call."""
        if not self._http:
            return CallResult(provider="telnyx", status="failed", error="Provider not initialized")

        try:
            r = await self._http.post(f"/calls/{provider_call_id}/actions/hangup")
            logger.info("Telnyx: ended call %s (HTTP %s)", provider_call_id, r.status_code)
            return CallResult(provider="telnyx", provider_call_id=provider_call_id, status="ended")
        except httpx.RequestError as e:
            logger.error("Telnyx: hangup failed: %s", e)
            return CallResult(provider="telnyx", provider_call_id=provider_call_id, status="failed", error=str(e))

    async def get_call_status(self, provider_call_id: str) -> CallResult:
        """Get current call status from Telnyx."""
        if not self._http:
            return CallResult(provider="telnyx", status="failed", error="Provider not initialized")

        try:
            r = await self._http.get(f"/calls/{provider_call_id}")
            if r.status_code == 200:
                data = r.json().get("data", {})
                return CallResult(
                    provider="telnyx",
                    provider_call_id=provider_call_id,
                    status=data.get("status", "unknown"),
                    metadata={"raw": data},
                )
            return CallResult(provider="telnyx", provider_call_id=provider_call_id, status="unknown")
        except httpx.RequestError as e:
            return CallResult(provider="telnyx", status="failed", error=str(e))

    async def start_recording(self, provider_call_id: str) -> str:
        """Start recording on a Telnyx call."""
        if not self._http:
            return ""
        try:
            r = await self._http.post(
                f"/calls/{provider_call_id}/actions/record_start",
                json={"format": "mp3", "channels": "dual"},
            )
            if r.status_code in (200, 201):
                rec_id = f"rec_{provider_call_id}"
                logger.info("Telnyx: recording started on %s", provider_call_id)
                return rec_id
            logger.warning("Telnyx: recording start failed (HTTP %s)", r.status_code)
            return ""
        except httpx.RequestError as e:
            logger.error("Telnyx: recording request failed: %s", e)
            return ""

    async def stop_recording(self, provider_call_id: str, recording_id: str) -> str | None:
        """Stop recording on a Telnyx call. Recording URL arrives via webhook."""
        if not self._http:
            return None
        try:
            r = await self._http.post(f"/calls/{provider_call_id}/actions/record_stop")
            logger.info("Telnyx: recording stopped on %s", provider_call_id)
            return None  # URL comes via webhook
        except httpx.RequestError as e:
            logger.error("Telnyx: stop recording failed: %s", e)
            return None

    def verify_webhook_signature(
        self, payload: bytes, signature_header: str, timestamp_header: str = ""
    ) -> bool:
        """Verify Telnyx webhook signature using HMAC-SHA256.

        Telnyx format: t=<timestamp>,v1=<signature>
        Computes: HMAC-SHA256(webhook_secret, timestamp.payload)
        """
        if not self._webhook_secret:
            logger.debug("Telnyx: skipping webhook verification (no secret)")
            return True

        if not signature_header:
            logger.warning("Telnyx: missing webhook signature header")
            return False

        parts = {}
        for part in signature_header.split(","):
            kv = part.split("=", 1)
            if len(kv) == 2:
                parts[kv[0].strip()] = kv[1].strip()

        telnyx_sig = parts.get("v1", "")
        telnyx_ts = parts.get("t", timestamp_header)

        if not telnyx_sig:
            logger.warning("Telnyx: no v1 signature in header")
            return False

        signed_payload = f"{telnyx_ts}.{payload.decode('utf-8')}"
        expected = hmac.new(
            self._webhook_secret.encode("utf-8"),
            signed_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        valid = hmac.compare_digest(expected, telnyx_sig)
        if not valid:
            logger.warning("Telnyx: webhook signature verification FAILED")
        return valid

    async def shutdown(self) -> None:
        """Close the HTTP client."""
        if self._http:
            await self._http.aclose()
            self._http = None
