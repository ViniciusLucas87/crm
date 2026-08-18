"""
Call Provider — abstract interface for telephony.

Every telephony provider (Telnyx, Twilio, Vonage, etc.)
implements this interface. CRM code never calls a provider directly.

Pattern follows IntelligenceProvider for consistency.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)
DEFAULT_ORG_ID = 1


class CallState(StrEnum):
    IDLE = "idle"
    DIALING = "dialing"
    RINGING = "ringing"
    CONNECTED = "connected"
    ON_HOLD = "on_hold"
    ENDED = "ended"
    FAILED = "failed"
    MISSED = "missed"


class CallDirection(StrEnum):
    OUTBOUND = "outbound"
    INBOUND = "inbound"


@dataclass
class CallResult:
    """Normalized output from any Call Provider."""
    provider: str
    provider_call_id: str | None = None
    status: str = "idle"
    direction: str = "outbound"
    phone_number: str = ""
    duration_seconds: int = 0
    recording_url: str | None = None
    recording_status: str = "none"
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class CallProvider(ABC):
    """Abstract interface for all Telephony Providers.

    Usage:
        class TelnyxProvider(CallProvider):
            @property
            def provider_name(self) -> str: return "telnyx"

            async def initialize(self, config: dict) -> bool: ...
            async def start_call(self, to_number: str, from_number: str) -> CallResult: ...
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique identifier: 'telnyx', 'twilio', 'vonage', etc."""
        ...

    @abstractmethod
    async def initialize(self, config: dict[str, str]) -> bool:
        """Initialize the provider with API keys and connection settings."""
        ...

    @abstractmethod
    async def start_call(self, to_number: str, caller_id: str | None = None) -> CallResult:
        """Initiate an outbound call. Returns call result with provider_call_id."""
        ...

    @abstractmethod
    async def end_call(self, provider_call_id: str) -> CallResult:
        """End an active call."""
        ...

    async def answer_call(self, provider_call_id: str) -> CallResult:
        """Answer an incoming call (optional — browser-based only)."""
        return CallResult(provider=self.provider_name, status="connected")

    async def mute(self, provider_call_id: str, muted: bool = True) -> bool:
        """Mute/unmute. Default: browser handles this."""
        return True

    async def hold(self, provider_call_id: str) -> bool:
        """Place call on hold."""
        return True

    async def resume(self, provider_call_id: str) -> bool:
        """Resume from hold."""
        return True

    async def start_recording(self, provider_call_id: str) -> str:
        """Start recording. Returns recording ID."""
        return ""

    async def stop_recording(self, provider_call_id: str, recording_id: str) -> str | None:
        """Stop recording. Returns recording URL when available."""
        return None

    @abstractmethod
    async def get_call_status(self, provider_call_id: str) -> CallResult:
        """Get current call status."""
        ...

    async def generate_token(self, user_id: str) -> dict[str, Any]:
        """Generate a client token for browser-based calling."""
        return {"token": "", "expires_at": ""}


def create_call_provider(name: str, config: dict[str, str]) -> CallProvider:
    """Factory: create a CallProvider by name."""
    if name == "telnyx":
        from app.application.telephony.telnyx import TelnyxProvider
        return TelnyxProvider(config)
    if name == "mock":
        return MockCallProvider()
    raise ValueError(f"Unknown call provider: {name}")


# ═══════════════════════════════════════════════════════════
# CALL STATE MACHINE
# ═══════════════════════════════════════════════════════════

# Valid transitions from each state
CALL_TRANSITIONS: dict[CallState, set[CallState]] = {
    CallState.IDLE:       {CallState.DIALING, CallState.RINGING},
    CallState.DIALING:    {CallState.RINGING, CallState.CONNECTED, CallState.FAILED, CallState.ENDED},
    CallState.RINGING:    {CallState.CONNECTED, CallState.MISSED, CallState.FAILED, CallState.ENDED},
    CallState.CONNECTED:  {CallState.ON_HOLD, CallState.ENDED, CallState.FAILED},
    CallState.ON_HOLD:    {CallState.CONNECTED, CallState.ENDED, CallState.FAILED},
    CallState.ENDED:      set(),
    CallState.FAILED:     {CallState.IDLE},
    CallState.MISSED:     {CallState.IDLE},
}


class CallStateMachine:
    """Enforces valid call state transitions."""

    def __init__(self, initial: CallState = CallState.IDLE) -> None:
        self._state = initial

    @property
    def state(self) -> CallState:
        return self._state

    def transition(self, to: CallState) -> bool:
        """Attempt transition. Returns True if valid, False if rejected."""
        valid = CALL_TRANSITIONS.get(self._state, set())
        if to not in valid:
            return False
        self._state = to
        return True

    def force(self, to: CallState) -> None:
        """Force a state transition (for webhook events)."""
        self._state = to


# ═══════════════════════════════════════════════════════════
# FEATURE FLAGS
# ═══════════════════════════════════════════════════════════

import os as _os


def is_telephony_enabled() -> bool:
    return _os.environ.get("ENABLE_TELEPHONY", "true").lower() == "true"


def is_webrtc_enabled() -> bool:
    return _os.environ.get("ENABLE_WEBRTC", "false").lower() == "true"


def is_recording_enabled() -> bool:
    return _os.environ.get("ENABLE_RECORDING", "false").lower() == "true"


def is_incoming_enabled() -> bool:
    return _os.environ.get("ENABLE_INCOMING_CALLS", "false").lower() == "true"


# ═══════════════════════════════════════════════════════════
# TELEPHONY SERVICE (only public API — delegates to CallSessionManager)
# ═══════════════════════════════════════════════════════════

class TelephonyService:
    """Facade for all telephony operations.

    CRM code calls this service. The service delegates to CallSessionManager,
    which manages the provider. No other code should import provider classes directly.

    Architecture:
        CRM → TelephonyService → CallSessionManager → CallProvider → Telnyx
    """

    def __init__(self, provider: CallProvider) -> None:
        from app.application.telephony.session_manager import CallSessionManager
        self._session_mgr = CallSessionManager(provider)
        self._initialized = False

    @property
    def provider_name(self) -> str:
        return self._session_mgr.provider.provider_name

    @property
    def available(self) -> bool:
        return self._initialized

    # ── Lifecycle ──────────────────────────────────────────

    async def initialize(self, config: dict[str, str]) -> bool:
        self._initialized = await self._session_mgr.provider.initialize(config)
        return self._initialized

    async def shutdown(self) -> None:
        """Clean up provider resources."""
        provider = self._session_mgr.provider
        if hasattr(provider, "shutdown"):
            await provider.shutdown()

    # ── Browser registration ───────────────────────────────

    async def register_device(self, user_id: str) -> dict[str, Any]:
        """Register a browser softphone. Returns client token (never API key)."""
        if not is_webrtc_enabled():
            return {"token": "", "reason": "WebRTC disabled"}
        return await self._session_mgr.provider.generate_token(user_id)

    async def generate_token(self, user_id: str) -> dict[str, Any]:
        """Generate a client token for browser-based calling."""
        return await self.register_device(user_id)

    # ── Call operations ────────────────────────────────────

    async def start_call(
        self, to_number: str, caller_id: str | None = None,
        company_id: int | None = None, contact_id: int | None = None,
        organization_id: int | None = None,
    ) -> CallResult:
        """Initiate an outbound call. Persists Call row + in-memory session."""
        if not is_telephony_enabled():
            return CallResult(provider=self.provider_name, status="failed", error="Telephony disabled")

        # ── Sprint 48.1: Persist call to DB ──
        from app.infrastructure.db.session import SessionLocal
        from app.application.telephony.call_lifecycle import CallLifecycleService
        db = SessionLocal()
        try:
            lifecycle = CallLifecycleService(db)
            entities = lifecycle.resolve_entities(to_number, company_id, contact_id)
            call_record = lifecycle.create_call(
                direction="outbound",
                phone_number=to_number,
                caller_id=caller_id,
                company_id=entities.get("company_id"),
                contact_id=entities.get("contact_id"),
                organization_id=organization_id or DEFAULT_ORG_ID,
            )
            db.commit()
            call_uuid = call_record.public_uuid
            call_db_id = call_record.id
        except Exception as exc:
            db.rollback()
            logger.error("Failed to persist call: %s", exc)
            call_uuid = None
            call_db_id = None
        finally:
            db.close()

        # ── In-memory session (for WebRTC control) ──
        session = self._session_mgr.create_session(
            phone_number=to_number,
            direction="outbound",
            company_id=company_id,
            contact_id=contact_id,
            organization_id=organization_id,
            caller_id=caller_id,
        )
        # Link in-memory session to persistent record
        session.pipeline_data["call_uuid"] = call_uuid
        session.pipeline_data["call_db_id"] = call_db_id
        result = await self._session_mgr.start_outbound(session, caller_id)
        return result

    async def end_call(self, provider_call_id: str) -> CallResult:
        """End a call by provider ID."""
        session = self._session_mgr.get_session_by_provider_id(provider_call_id)
        if session:
            return await self._session_mgr.end_call(session)
        return await self._session_mgr.provider.end_call(provider_call_id)

    async def answer_call(self, provider_call_id: str) -> CallResult:
        return await self._session_mgr.provider.answer_call(provider_call_id)

    async def mute(self, provider_call_id: str, muted: bool = True) -> bool:
        session = self._session_mgr.get_session_by_provider_id(provider_call_id)
        if session:
            return await self._session_mgr.mute(session, muted)
        return await self._session_mgr.provider.mute(provider_call_id, muted)

    async def hold(self, provider_call_id: str) -> bool:
        session = self._session_mgr.get_session_by_provider_id(provider_call_id)
        if session:
            return await self._session_mgr.hold(session)
        return await self._session_mgr.provider.hold(provider_call_id)

    async def resume(self, provider_call_id: str) -> bool:
        session = self._session_mgr.get_session_by_provider_id(provider_call_id)
        if session:
            return await self._session_mgr.resume(session)
        return await self._session_mgr.provider.resume(provider_call_id)

    async def start_recording(self, provider_call_id: str) -> str:
        if not is_recording_enabled():
            return ""
        session = self._session_mgr.get_session_by_provider_id(provider_call_id)
        if session:
            return await self._session_mgr.start_recording(session)
        return await self._session_mgr.provider.start_recording(provider_call_id)

    async def stop_recording(self, provider_call_id: str, recording_id: str) -> str | None:
        session = self._session_mgr.get_session_by_provider_id(provider_call_id)
        if session:
            return await self._session_mgr.stop_recording(session)
        return await self._session_mgr.provider.stop_recording(provider_call_id, recording_id)

    async def get_call_status(self, provider_call_id: str) -> CallResult:
        return await self._session_mgr.provider.get_call_status(provider_call_id)

    # ── Session access ─────────────────────────────────────

    def get_session(self, session_id: str):
        """Get a CallSession by session ID."""
        return self._session_mgr.get_session(session_id)

    def get_active_sessions(self):
        """Get all active call sessions."""
        return self._session_mgr.active_sessions

    # ── Webhook handling ───────────────────────────────────

    def handle_webhook_event(self, event_type: str, provider_call_id: str, payload: dict) -> dict:
        """Handle provider webhook events through the session manager."""
        session = self._session_mgr.handle_webhook_event(event_type, provider_call_id, payload)
        state = session.status.value if session else "unknown"
        return {"state": state, "event": event_type, "session_id": session.session_id if session else None}

    def verify_webhook_signature(self, payload: bytes, signature_header: str, timestamp: str = "") -> bool:
        """Verify webhook signature using the provider's verification method."""
        provider = self._session_mgr.provider
        if hasattr(provider, "verify_webhook_signature"):
            return provider.verify_webhook_signature(payload, signature_header, timestamp)
        return True  # Provider doesn't support verification


# ═══════════════════════════════════════════════════════════
# MOCK CALL PROVIDER (dev / testing / CI)
# ═══════════════════════════════════════════════════════════

class MockCallProvider(CallProvider):
    """Simulates a full telephony provider with no external account.

    Supports: dialing → ringing → connected → ended.
    Generates fake call IDs, simulates duration, recording URLs.
    """

    def __init__(self) -> None:
        self._call_id = 0
        self._calls: dict[str, dict] = {}

    @property
    def provider_name(self) -> str:
        return "mock"

    async def initialize(self, config: dict[str, str]) -> bool:
        return True

    async def start_call(self, to_number: str, caller_id: str | None = None) -> CallResult:
        self._call_id += 1
        cid = f"mock_call_{self._call_id}"
        self._calls[cid] = {"to": to_number, "from": caller_id or "+1-555-0000", "status": "dialing", "start": __import__("time").time()}
        return CallResult(provider="mock", provider_call_id=cid, status="dialing", direction="outbound", phone_number=to_number)

    async def end_call(self, provider_call_id: str) -> CallResult:
        call = self._calls.pop(provider_call_id, {})
        dur = int(__import__("time").time() - call.get("start", 0)) if call.get("start") else 0
        return CallResult(provider="mock", provider_call_id=provider_call_id, status="ended", direction="outbound", phone_number=call.get("to", ""), duration_seconds=dur)

    async def get_call_status(self, provider_call_id: str) -> CallResult:
        call = self._calls.get(provider_call_id)
        return CallResult(provider="mock", provider_call_id=provider_call_id, status=call.get("status", "ended") if call else "ended")

    async def start_recording(self, provider_call_id: str) -> str:
        return f"mock_rec_{provider_call_id}"

    async def stop_recording(self, provider_call_id: str, recording_id: str) -> str | None:
        return f"https://mock-recordings.pns.local/{recording_id}.mp3"

    async def generate_token(self, user_id: str) -> dict[str, Any]:
        return {"token": f"mock_token_{user_id}", "expires_at": "3600", "provider": "mock"}
