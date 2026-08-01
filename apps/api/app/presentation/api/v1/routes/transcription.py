"""
Transcription API — REST endpoints and WebSocket for live transcription.

Endpoints:
  - GET  /api/v1/transcription/config          — provider config info
  - GET  /api/v1/transcription/transcripts      — list transcripts
  - GET  /api/v1/transcription/transcripts/{id} — get transcript with utterances
  - GET  /api/v1/transcription/search           — search transcripts
  - POST /api/v1/transcription/start            — start transcription session
  - POST /api/v1/transcription/{session_id}/stop — stop transcription session
  - WS   /api/v1/transcription/ws/{session_id}  — WebSocket for audio streaming
"""

import asyncio
import base64
import gc
import json
import logging
import os
import uuid
from functools import lru_cache

from fastapi import APIRouter, Depends, Query, Request, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.application.transcription.service import TranscriptionService
from app.infrastructure.auth.clerk import AuthContext, require_permission
from app.infrastructure.db.session import get_db_session
from app.infrastructure.repositories.transcript import TranscriptRepository

logger = logging.getLogger(__name__)
router = APIRouter()

# ── Service factory ──

@lru_cache()
def get_transcription_service() -> TranscriptionService:
    """Get or create the transcription service (one per process)."""
    from app.infrastructure.db.session import SessionLocal
    db = SessionLocal()
    repo = TranscriptRepository(db)
    config = {
        "provider": os.getenv("TRANSCRIPTION_PROVIDER", "deepgram"),
        "api_key": os.getenv("DEEPGRAM_API_KEY", os.getenv("TRANSCRIPTION_API_KEY", "")),
        "model": os.getenv("TRANSCRIPTION_MODEL", "nova-2"),
        "language": os.getenv("TRANSCRIPTION_LANGUAGE", "en"),
        "diarize": True,
        "punctuate": True,
        "interim_results": True,
    }
    return TranscriptionService(repo, config)


# ═══════════════════════════════════════════════════════════
# REST ENDPOINTS
# ═══════════════════════════════════════════════════════════

@router.get("/config")
async def get_config(auth: AuthContext = Depends(require_permission("telephony:read"))):
    """Return provider configuration (no secrets)."""
    svc = get_transcription_service()
    provider = svc.get_or_create_provider()
    langs = await provider.get_supported_languages()
    return {
        "provider": provider.provider_name,
        "supported_languages": langs,
        "features": {
            "diarization": True,
            "partial_transcripts": True,
            "punctuation": True,
        },
    }


@router.get("/transcripts")
async def list_transcripts(
    request: Request,
    call_id: int | None = Query(None),
    company_id: int | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    auth: AuthContext = Depends(require_permission("telephony:read")),
    db: Session = Depends(get_db_session),
):
    """List transcripts for the organization."""
    repo = TranscriptRepository(db)
    if call_id:
        transcripts = repo.get_transcripts_by_call(call_id)
    elif company_id:
        transcripts = repo.get_transcripts_by_company(company_id, limit)
    else:
        transcripts = repo.get_transcripts_by_org(auth.organization_id, limit, offset)

    return {
        "transcripts": [
            {
                "id": t.id,
                "call_id": t.call_id,
                "company_id": t.company_id,
                "provider": t.provider,
                "language": t.language,
                "status": t.status,
                "word_count": t.word_count,
                "utterance_count": t.utterance_count,
                "started_at": t.started_at.isoformat() if t.started_at else None,
                "ended_at": t.ended_at.isoformat() if t.ended_at else None,
                "duration_seconds": t.duration_seconds,
                "recording_url": t.recording_url,
            }
            for t in transcripts
        ],
        "total": repo.count_transcripts_by_org(auth.organization_id),
    }


@router.get("/transcripts/{transcript_id}")
async def get_transcript(
    transcript_id: int,
    auth: AuthContext = Depends(require_permission("telephony:read")),
    db: Session = Depends(get_db_session),
):
    """Get a full transcript with all utterances."""
    repo = TranscriptRepository(db)
    transcript = repo.get_transcript(transcript_id)
    if not transcript:
        return {"error": "Transcript not found"}, 404
    if transcript.organization_id != auth.organization_id:
        return {"error": "Unauthorized"}, 403

    utterances = repo.get_final_segments(transcript_id)
    return {
        "id": transcript.id,
        "call_id": transcript.call_id,
        "company_id": transcript.company_id,
        "provider": transcript.provider,
        "language": transcript.language,
        "status": transcript.status,
        "full_text": transcript.full_text,
        "word_count": transcript.word_count,
        "utterance_count": transcript.utterance_count,
        "started_at": transcript.started_at.isoformat() if transcript.started_at else None,
        "ended_at": transcript.ended_at.isoformat() if transcript.ended_at else None,
        "duration_seconds": transcript.duration_seconds,
        "recording_url": transcript.recording_url,
        "utterances": [
            {
                "id": u.id,
                "speaker": u.speaker,
                "speaker_label": u.speaker_label,
                "text": u.text,
                "confidence": float(u.confidence) if u.confidence else 0.0,
                "start_seconds": float(u.start_time) if u.start_time else 0.0,
                "end_seconds": float(u.end_time) if u.end_time else 0.0,
                "words": json.loads(u.words_json) if u.words_json else [],
            }
            for u in utterances
        ],
    }


@router.get("/search")
async def search_transcripts(
    q: str = Query(..., min_length=2),
    limit: int = Query(20, ge=1, le=100),
    auth: AuthContext = Depends(require_permission("telephony:read")),
    db: Session = Depends(get_db_session),
):
    """Search transcripts by text content."""
    repo = TranscriptRepository(db)
    results = repo.search_transcripts(auth.organization_id, q, limit)
    return {
        "results": [
            {
                "id": t.id,
                "call_id": t.call_id,
                "company_id": t.company_id,
                "full_text": (t.full_text or "")[:500],
                "word_count": t.word_count,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in results
        ]
    }


@router.post("/start")
async def start_transcription(
    request: Request,
    call_id: int | None = None,
    company_id: int | None = None,
    contact_id: int | None = None,
    conversation_id: int | None = None,
    source_role: str = "agent",
    auth: AuthContext = Depends(require_permission("companies:read")),
):
    """Start a new transcription session. Returns session_id for WebSocket connection.
    
    source_role: "agent" (mic) or "prospect" (remote track) — determines speaker label.
    Two simultaneous sessions with different roles produce correctly attributed transcripts.
    """
    session_id = str(uuid.uuid4())
    svc = get_transcription_service()
    session = await svc.start_session(
        session_id=session_id,
        organization_id=auth.organization_id,
        call_id=call_id,
        company_id=company_id,
        contact_id=contact_id,
        conversation_id=conversation_id,
        source_role=source_role,
    )
    return {
        "session_id": session_id,
        "transcript_id": session.transcript_id,
        "provider": svc._provider_name,
        "source_role": source_role,
        "speaker_label": session.speaker_label,
    }


@router.post("/{session_id}/stop")
async def stop_transcription(
    session_id: str,
    auth: AuthContext = Depends(require_permission("telephony:write")),
):
    """Stop a transcription session and finalize the transcript."""
    svc = get_transcription_service()
    result = await svc.stop_session(session_id)

    # Emit event for workers
    from app.infrastructure.db.session import SessionLocal
    from app.application.events.bridge import emit
    from app.application.workers.events import EventType
    db = SessionLocal()
    try:
        emit(db, EventType.TRANSCRIPT_COMPLETED, "transcript", hash(session_id) & 0x7FFFFFFF,
             {"session_id": session_id, "segments_count": result.get("segments_count", 0) if isinstance(result, dict) else 0})
    finally:
        db.close()

    return result


# ═══════════════════════════════════════════════════════════
# WEBSOCKET — Live Audio Streaming
# ═══════════════════════════════════════════════════════════

@router.websocket("/ws/{session_id}")
async def transcription_websocket(websocket: WebSocket, session_id: str):
    """WebSocket for live audio streaming to transcription provider.

    Client sends:
      - {"type": "audio", "data": "<base64-encoded pcm audio>"}
      - {"type": "ping"}

    Server sends:
      - {"type": "partial", "speaker": "...", "text": "...", ...}
      - {"type": "final", "speaker": "...", "text": "...", "words": [...], ...}
      - {"type": "error", "error": "..."}
      - {"type": "connected"}
    """
    await websocket.accept()

    svc = get_transcription_service()
    session = svc.get_session(session_id)

    if not session:
        await websocket.send_json({"type": "error", "error": "Session not found"})
        await websocket.close()
        return

    # Attach WebSocket to session for forwarding events
    session.websocket = websocket

    try:
        await svc.start_streaming(session_id)
        await websocket.send_json({"type": "connected", "session_id": session_id})

        while True:
            try:
                data = await websocket.receive_json()
            except WebSocketDisconnect:
                break

            msg_type = data.get("type", "")
            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
            elif msg_type == "audio":
                # Decode base64 PCM audio and send to provider
                audio_data = data.get("data", "")
                if audio_data:
                    try:
                        audio_bytes = base64.b64decode(audio_data)
                        await session.provider.send_audio(audio_bytes)
                        if not hasattr(session, '_chunk_count'):
                            session._chunk_count = 0
                        session._chunk_count += 1
                        if session._chunk_count % 100 == 0:
                            logger.info("Audio chunks received for session %s: %d (%d bytes each)",
                                       session_id, session._chunk_count, len(audio_bytes))
                    except Exception as exc:
                        logger.warning("Audio decode/send error: %s", exc)

    except Exception as e:
        logger.error("WebSocket error for session %s: %s", session_id, e)
    finally:
        try:
            await svc.stop_session(session_id)
        except Exception:
            pass
        try:
            await websocket.close()
        except Exception:
            pass
