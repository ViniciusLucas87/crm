"""
Call Session Manager — owns call lifecycle, timers, participants, recording state.

This is the intelligence pipeline anchor. Every CallSession is designed so
future AI stages (transcription → conversation intelligence → CRM intelligence)
can consume it exactly like the Lead Intelligence pipeline.

Architecture:
    CRM → TelephonyService → CallSessionManager → CallProvider → Telnyx
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import StrEnum
from typing import Any, Callable

from app.application.telephony import CallProvider, CallResult, CallState

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# PIPELINE-READY TYPES
# ═══════════════════════════════════════════════════════════

class RecordingState(StrEnum):
    """Recording lifecycle — designed for future transcription pipeline."""
    NONE = "none"
    REQUESTED = "requested"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class TranscriptStatus(StrEnum):
    """Transcript pipeline stages (not implemented yet)."""
    NONE = "none"
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class AIStatus(StrEnum):
    """AI analysis pipeline stages (not implemented yet)."""
    NONE = "none"
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Participant:
    """A person on the call."""
    name: str = ""
    phone_number: str = ""
    role: str = "unknown"  # caller, callee, transferred
    user_id: str | None = None
    contact_id: int | None = None


@dataclass
class CallSession:
    """Complete call session — the intelligence pipeline anchor.

    Designed so future stages (transcription, conversation analysis,
    pain points, buying signals, decision makers) can consume this
    without schema changes.
    """

    # ── Identity ──
    session_id: str = field(default_factory=lambda: f"call_{uuid.uuid4().hex[:12]}")
    provider: str = ""
    provider_call_id: str | None = None

    # ── CRM linkage ──
    organization_id: int | None = None
    company_id: int | None = None
    contact_id: int | None = None
    activity_id: int | None = None

    # ── Call details ──
    direction: str = "outbound"
    status: CallState = CallState.IDLE
    phone_number: str = ""
    caller_id: str | None = None

    # ── Timing ──
    started_at: datetime | None = None
    answered_at: datetime | None = None
    ended_at: datetime | None = None
    duration_seconds: int = 0

    # ── Participants ──
    participants: list[Participant] = field(default_factory=list)

    # ── Recording ──
    recording_state: RecordingState = RecordingState.NONE
    recording_id: str | None = None
    recording_url: str | None = None

    # ── Pipeline stages (future) ──
    transcript_status: TranscriptStatus = TranscriptStatus.NONE
    ai_status: AIStatus = AIStatus.NONE

    # ── Extensible metadata ──
    provider_metadata: dict[str, Any] = field(default_factory=dict)
    pipeline_data: dict[str, Any] = field(default_factory=dict)

    # ── Error ──
    error: str | None = None

    @property
    def is_active(self) -> bool:
        return self.status in (CallState.DIALING, CallState.RINGING, CallState.CONNECTED, CallState.ON_HOLD)

    def to_db_dict(self) -> dict[str, Any]:
        """Serialize to dict matching the Call model columns."""
        import json
        return {
            "session_id": self.session_id,
            "provider": self.provider,
            "provider_call_id": self.provider_call_id,
            "organization_id": self.organization_id,
            "company_id": self.company_id,
            "contact_id": self.contact_id,
            "activity_id": self.activity_id,
            "direction": self.direction,
            "status": self.status.value if isinstance(self.status, CallState) else self.status,
            "phone_number": self.phone_number,
            "caller_id": self.caller_id,
            "started_at": self.started_at,
            "answered_at": self.answered_at,
            "ended_at": self.ended_at,
            "duration_seconds": self.duration_seconds,
            "recording_url": self.recording_url,
            "recording_status": self.recording_state.value,
            "transcript_status": self.transcript_status.value,
            "ai_status": self.ai_status.value,
            "provider_metadata": json.dumps(self.provider_metadata) if self.provider_metadata else None,
        }


# ═══════════════════════════════════════════════════════════
# CALL SESSION MANAGER
# ═══════════════════════════════════════════════════════════

class CallSessionManager:
    """Manages all active call sessions.

    Owns: call lifecycle, timers, participants, recording state,
          mute/hold/reconnect, CRM synchronization.

    The provider only talks to Telnyx. This manager handles everything else.
    """

    def __init__(self, provider: CallProvider) -> None:
        self._provider = provider
        self._sessions: dict[str, CallSession] = {}
        self._by_provider_id: dict[str, CallSession] = {}
        self._on_state_change: Callable[[CallSession], None] | None = None

    @property
    def provider(self) -> CallProvider:
        return self._provider

    @property
    def active_sessions(self) -> list[CallSession]:
        return [s for s in self._sessions.values() if s.is_active]

    def on_state_change(self, callback: Callable[[CallSession], None]) -> None:
        """Register a callback invoked on every state transition."""
        self._on_state_change = callback

    # ── Session lifecycle ──────────────────────────────────

    def create_session(
        self,
        phone_number: str,
        direction: str = "outbound",
        company_id: int | None = None,
        contact_id: int | None = None,
        organization_id: int | None = None,
        caller_id: str | None = None,
    ) -> CallSession:
        """Create a new call session."""
        session = CallSession(
            provider=self._provider.provider_name,
            direction=direction,
            phone_number=phone_number,
            company_id=company_id,
            contact_id=contact_id,
            organization_id=organization_id,
            caller_id=caller_id,
            participants=[Participant(phone_number=phone_number, role="callee")],
        )
        self._sessions[session.session_id] = session
        logger.info("CallSession created: %s → %s (%s)", session.session_id, phone_number, direction)
        return session

    def get_session(self, session_id: str) -> CallSession | None:
        return self._sessions.get(session_id)

    def get_session_by_provider_id(self, provider_call_id: str) -> CallSession | None:
        return self._by_provider_id.get(provider_call_id)

    # ── State transitions ──────────────────────────────────

    def transition(self, session: CallSession, to: CallState) -> None:
        """Transition a session to a new state."""
        old = session.status
        session.status = to

        now = datetime.now(UTC)
        if to == CallState.CONNECTED and not session.answered_at:
            session.answered_at = now
        elif to in (CallState.ENDED, CallState.FAILED, CallState.MISSED):
            session.ended_at = now
            if session.answered_at:
                session.duration_seconds = int((now - session.answered_at).total_seconds())

        logger.info("CallSession %s: %s → %s", session.session_id, old, to)

        if self._on_state_change:
            self._on_state_change(session)

    # ── Provider integration ───────────────────────────────

    async def start_outbound(self, session: CallSession, caller_id: str | None = None) -> CallResult:
        """Initiate outbound call through the provider."""
        self.transition(session, CallState.DIALING)
        session.started_at = datetime.now(UTC)

        result = await self._provider.start_call(session.phone_number, caller_id or session.caller_id)
        if result.provider_call_id:
            session.provider_call_id = result.provider_call_id
            self._by_provider_id[result.provider_call_id] = session

        if result.status == "failed":
            self.transition(session, CallState.FAILED)
            session.error = result.error
        elif result.status == "connected":
            self.transition(session, CallState.CONNECTED)

        return result

    async def end_call(self, session: CallSession) -> CallResult:
        """End a call through the provider."""
        if session.provider_call_id:
            result = await self._provider.end_call(session.provider_call_id)
            self._by_provider_id.pop(session.provider_call_id, None)
        else:
            result = CallResult(provider=self._provider.provider_name, status="ended")

        self.transition(session, CallState.ENDED)
        return result

    async def mute(self, session: CallSession, muted: bool = True) -> bool:
        if session.provider_call_id:
            return await self._provider.mute(session.provider_call_id, muted)
        return True

    async def hold(self, session: CallSession) -> bool:
        if session.provider_call_id:
            ok = await self._provider.hold(session.provider_call_id)
            if ok:
                self.transition(session, CallState.ON_HOLD)
            return ok
        self.transition(session, CallState.ON_HOLD)
        return True

    async def resume(self, session: CallSession) -> bool:
        if session.provider_call_id:
            ok = await self._provider.resume(session.provider_call_id)
            if ok:
                self.transition(session, CallState.CONNECTED)
            return ok
        self.transition(session, CallState.CONNECTED)
        return True

    async def start_recording(self, session: CallSession) -> str:
        session.recording_state = RecordingState.REQUESTED
        if session.provider_call_id:
            rec_id = await self._provider.start_recording(session.provider_call_id)
            if rec_id:
                session.recording_id = rec_id
                session.recording_state = RecordingState.IN_PROGRESS
                logger.info("Recording started: %s on %s", rec_id, session.session_id)
            return rec_id
        return ""

    async def stop_recording(self, session: CallSession) -> str | None:
        if session.recording_id and session.provider_call_id:
            url = await self._provider.stop_recording(session.provider_call_id, session.recording_id)
            if url:
                session.recording_url = url
                session.recording_state = RecordingState.COMPLETED
                logger.info("Recording completed: %s → %s", session.recording_id, url)
            return url
        return None

    # ── Webhook handling ───────────────────────────────────

    def handle_webhook_event(self, event_type: str, provider_call_id: str, payload: dict) -> CallSession | None:
        """Process a provider webhook event, updating the matching session."""
        session = self._by_provider_id.get(provider_call_id)
        if not session:
            logger.warning("Webhook for unknown call: %s (%s)", provider_call_id, event_type)
            return None

        mapping = {
            "call.initiated": CallState.DIALING,
            "call.answered": CallState.CONNECTED,
            "call.hangup": CallState.ENDED,
            "call.failed": CallState.FAILED,
            "call.missed": CallState.MISSED,
        }

        target = mapping.get(event_type)
        if target:
            self.transition(session, target)

        # Recording webhooks
        if event_type == "call.recording.saved":
            session.recording_url = (
                payload.get("recording_urls", {}).get("mp3", "")
                or payload.get("recording_url", "")
            )
            session.recording_state = RecordingState.COMPLETED

        return session

    # ── Cleanup ────────────────────────────────────────────

    def remove_session(self, session_id: str) -> None:
        session = self._sessions.pop(session_id, None)
        if session and session.provider_call_id:
            self._by_provider_id.pop(session.provider_call_id, None)

    def cleanup_stale(self, max_age_seconds: int = 3600) -> int:
        """Remove sessions older than max_age_seconds that are not active."""
        now = time.time()
        stale = [
            sid for sid, s in self._sessions.items()
            if not s.is_active and s.ended_at
            and (now - s.ended_at.timestamp()) > max_age_seconds
        ]
        for sid in stale:
            self.remove_session(sid)
        return len(stale)
