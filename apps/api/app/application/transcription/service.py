"""
Transcription Service — orchestrates live transcription.

Architecture:
    Browser audio → WebSocket → TranscriptionService → TranscriptProvider → DB persistence

This service manages:
  - Provider lifecycle (connect, stream, disconnect)
  - Transcript persistence (create, append utterances, finalize)
  - Multiple concurrent sessions
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from fastapi import WebSocket

from app.application.transcription import (
    TranscriptCallback,
    TranscriptEvent,
    TranscriptEventType,
    TranscriptProvider,
    TranscriptSegment,
    create_transcript_provider,
)
from app.infrastructure.repositories.transcript import TranscriptRepository

logger = logging.getLogger(__name__)


@dataclass
class TranscriptionSession:
    """A single live transcription session connected to a provider."""

    session_id: str
    provider: TranscriptProvider
    transcript_id: int
    organization_id: int
    source_role: str = "agent"
    speaker_label: str = "PNS Agent"
    websocket: WebSocket | None = None
    segments: list[dict[str, Any]] = field(default_factory=list)
    full_text: str = ""
    word_count: int = 0
    utterance_count: int = 0
    start_time: float = 0.0
    connected: bool = False
    streaming: bool = False


class TranscriptionService:
    """Orchestrator for live transcription sessions."""

    def __init__(self, repo: TranscriptRepository, provider_config: dict[str, Any] | None = None):
        self._repo = repo
        self._provider_config = provider_config or {}
        self._sessions: dict[str, TranscriptionSession] = {}
        self._provider_name = self._provider_config.get("provider", "deepgram")

    def get_or_create_provider(self) -> TranscriptProvider:
        return create_transcript_provider(self._provider_name, self._provider_config)

    async def start_session(
        self,
        session_id: str,
        organization_id: int,
        *,
        call_id: int | None = None,
        company_id: int | None = None,
        contact_id: int | None = None,
        conversation_id: int | None = None,
        source_role: str = "agent",
        websocket: WebSocket | None = None,
    ) -> TranscriptionSession:
        """Create a transcript record and connect to the transcription provider."""
        # Create transcript DB record
        transcript = self._repo.create_transcript(
            organization_id=organization_id,
            call_id=call_id,
            company_id=company_id,
            contact_id=contact_id,
            conversation_id=conversation_id,
            provider=self._provider_name,
        )

        # Create provider and connect
        provider = self.get_or_create_provider()
        api_key = self._provider_config.get("api_key", "")
        if not api_key:
            self._repo.update_transcript_status(transcript.id, "failed")
            raise RuntimeError(
                f"Transcription API key not configured. Set TRANSCRIPTION_API_KEY or {self._provider_name.upper()}_API_KEY in .env"
            )
        connected = await provider.connect(self._provider_config)
        if not connected:
            self._repo.update_transcript_status(transcript.id, "failed")
            raise RuntimeError(f"Failed to connect to transcription provider: {self._provider_name}")

        speaker_label = "PNS Agent" if source_role == "agent" else "Prospect"
        session = TranscriptionSession(
            session_id=session_id,
            provider=provider,
            transcript_id=transcript.id,
            organization_id=organization_id,
            source_role=source_role,
            speaker_label=speaker_label,
            websocket=websocket,
            start_time=datetime.now(UTC).timestamp(),
            connected=True,
        )
        self._sessions[session_id] = session
        logger.info("Transcription session %s started (transcript_id=%d, role=%s, label=%s)",
                     session_id, transcript.id, source_role, speaker_label)
        return session

    async def start_streaming(self, session_id: str) -> None:
        """Begin streaming audio for transcription."""
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        async def on_event(event: TranscriptEvent) -> None:
            await self._handle_event(session_id, event)

        await session.provider.start_streaming(on_event)
        session.streaming = True

    async def _handle_event(self, session_id: str, event: TranscriptEvent) -> None:
        """Handle transcript events — persist segments and forward to WebSocket."""
        session = self._sessions.get(session_id)
        if not session:
            return

        if event.type == TranscriptEventType.PARTIAL and event.segment:
            # Forward partial to WebSocket — use session speaker_label (deterministic)
            if session.websocket:
                try:
                    await session.websocket.send_json({
                        "type": "partial",
                        "session_id": session_id,
                        "transcript_id": session.transcript_id,
                        "speaker": session.speaker_label,
                        "text": event.segment.text,
                        "start": event.segment.start,
                        "end": event.segment.end,
                        "confidence": event.segment.confidence,
                    })
                except Exception:
                    pass

        elif event.type == TranscriptEventType.FINAL and event.segment:
            seg = event.segment
            # Override Deepgram diarization with deterministic source_role label
            speaker = session.speaker_label
            # Persist utterance
            words_json = json.dumps([{
                "word": w.word,
                "start": w.start,
                "end": w.end,
                "confidence": w.confidence,
            } for w in seg.words]) if seg.words else None

            self._repo.add_utterance(
                organization_id=session.organization_id,
                transcript_id=session.transcript_id,
                speaker=speaker,
                text=seg.text,
                is_final=True,
                confidence=seg.confidence,
                start_time=seg.start,
                end_time=seg.end,
                words_json=words_json,
                language=seg.language,
                segment_id=seg.id,
                sequence=session.utterance_count,
            )

            session.segments.append({
                "speaker": speaker,
                "text": seg.text,
                "start": seg.start,
                "end": seg.end,
                "confidence": seg.confidence,
                "is_final": True,
            })
            session.full_text += seg.text + " "
            session.word_count += len(seg.words) if seg.words else len(seg.text.split())
            session.utterance_count += 1

            # Forward to WebSocket
            if session.websocket:
                try:
                    await session.websocket.send_json({
                        "type": "final",
                        "session_id": session_id,
                        "transcript_id": session.transcript_id,
                        "speaker": speaker,
                        "text": seg.text,
                        "start": seg.start,
                        "end": seg.end,
                        "confidence": seg.confidence,
                        "words": [{"word": w.word, "start": w.start, "end": w.end} for w in seg.words],
                        "utterance_number": session.utterance_count,
                    })
                except Exception:
                    pass

        elif event.type == TranscriptEventType.ERROR:
            logger.error("Transcript error for session %s: %s", session_id, event.error)
            if session.websocket:
                try:
                    await session.websocket.send_json({"type": "error", "error": event.error})
                except Exception:
                    pass

        elif event.type == TranscriptEventType.CONNECTED:
            logger.info("Transcript provider connected for session %s", session_id)

        elif event.type == TranscriptEventType.DISCONNECTED:
            logger.info("Transcript provider disconnected for session %s", session_id)
            session.streaming = False

    async def stop_session(self, session_id: str) -> dict[str, Any]:
        """Stop streaming, finalize transcript, and disconnect."""
        session = self._sessions.pop(session_id, None)
        if not session:
            return {"status": "not_found"}

        try:
            await session.provider.stop_streaming()
        except Exception:
            pass
        try:
            await session.provider.disconnect()
        except Exception:
            pass

        duration = int(datetime.now(UTC).timestamp() - session.start_time)
        self._repo.complete_transcript(
            session.transcript_id,
            full_text=session.full_text.strip(),
            word_count=session.word_count,
            utterance_count=session.utterance_count,
            duration_seconds=duration,
        )

        logger.info("Transcription session %s completed: %d utterances, %d words",
                     session_id, session.utterance_count, session.word_count)

        return {
            "transcript_id": session.transcript_id,
            "utterances": session.utterance_count,
            "words": session.word_count,
            "duration_seconds": duration,
            "segments": session.segments,
        }

    def get_session(self, session_id: str) -> TranscriptionSession | None:
        return self._sessions.get(session_id)

    def list_sessions(self) -> list[str]:
        return list(self._sessions.keys())
