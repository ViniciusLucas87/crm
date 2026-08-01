"""
Sprint 43 + 44 — AI Coach & Post-Call Intelligence API

REST + WebSocket endpoints for:
  - Real-time coaching during calls
  - Post-call intelligence generation
  - Approval queue management
"""

import json
import logging
import os
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Query, Request, WebSocket, WebSocketDisconnect

from app.application.llm.provider import LLMConfig
from app.application.transcription.coach import CoachEngine, get_coach_engine, remove_coach_engine, CoachEventType, CoachSeverity
from app.application.transcription.postcall import PostCallPipeline, DeliverableStatus
from app.infrastructure.auth.clerk import AuthContext, require_permission
from app.infrastructure.db.session import get_db_session
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter()

# ── In-memory approval queue (replace with DB in production) ──
_approval_queue: list[dict[str, Any]] = []


def _get_llm_config() -> LLMConfig:
    return LLMConfig(
        provider=os.getenv("LLM_PROVIDER", "openai"),
        api_key=os.getenv("LLM_API_KEY", os.getenv("OPENAI_API_KEY", "")),
        model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
    )


# ═══════════════════════════════════════════════════════════
# SPRINT 43 — Real-Time Coaching
# ═══════════════════════════════════════════════════════════

@router.websocket("/coach/ws/{call_id}")
async def coach_websocket(websocket: WebSocket, call_id: int):
    """WebSocket for real-time AI coaching during a call.

    Client sends transcript segments:
      {"type": "segment", "speaker": "...", "text": "...", "is_final": true, ...}

    Server sends coaching events:
      {"type": "coach_event", "event_type": "objection_detected", ...}
    """
    await websocket.accept()
    session_id = f"coach-{call_id}-{datetime.now(UTC).timestamp():.0f}"
    engine = get_coach_engine(session_id)
    segment_buffer: list[str] = []

    async def send_event(event):
        try:
            await websocket.send_json({
                "type": "coach_event",
                "event_type": event.type.value,
                "severity": event.severity.value,
                "title": event.title,
                "description": event.description,
                "suggestion": event.suggestion,
                "evidence": event.evidence,
                "confidence": event.confidence,
                "timestamp": event.timestamp,
                "metadata": event.metadata,
            })
        except Exception:
            pass

    engine.subscribe(send_event)

    try:
        await websocket.send_json({"type": "connected", "session_id": session_id})

        while True:
            try:
                data = await websocket.receive_json()
            except WebSocketDisconnect:
                break

            msg_type = data.get("type", "")
            if msg_type == "segment":
                segment = {
                    "speaker": data.get("speaker", "Unknown"),
                    "text": data.get("text", ""),
                    "start": data.get("start", 0),
                    "end": data.get("end", 0),
                    "is_final": data.get("is_final", True),
                    "confidence": data.get("confidence", 1.0),
                    "source_role": data.get("source_role", "unknown"),
                    # Sprint 47.4 — latency timestamps from frontend
                    "audio_end_at": data.get("audio_end_at", 0),
                    "deepgram_final_at": data.get("deepgram_final_at", 0),
                    "normalized_at": data.get("normalized_at", 0),
                }
                await engine.process_segment(segment)

            elif msg_type == "health":
                health = engine.get_health()
                await websocket.send_json({
                    "type": "health",
                    "talk_ratio": health.talk_ratio,
                    "engagement_score": health.engagement_score,
                    "rapport_score": health.rapport_score,
                    "overall_health": health.overall_health,
                    "objections_handled": health.objections_handled,
                    "positive_signals": health.positive_signals,
                    "topics_covered": len(health.topics_covered),
                })
            elif msg_type == "opportunity":
                score = engine.get_opportunity_score()
                await websocket.send_json({"type": "opportunity", **score})
            elif msg_type == "reminders":
                reminders = engine.get_reminders()
                await websocket.send_json({"type": "reminders", "reminders": reminders})
            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})
            # Sprint 46 — enhanced copilot
            elif msg_type == "discovery":
                items = engine.get_discovery()
                await websocket.send_json({"type": "discovery", "items": items})
            elif msg_type == "stage":
                progress = engine.get_stage_progress()
                await websocket.send_json({"type": "stage", **progress})
            elif msg_type == "signals":
                signals = engine.get_buying_signals()
                await websocket.send_json({"type": "signals", "signals": signals})
            elif msg_type == "knowledge":
                facts = engine.get_knowledge_extracted()
                await websocket.send_json({"type": "knowledge", "facts": facts[-20:]})
            elif msg_type == "score":
                await websocket.send_json({"type": "score_requested"})
            # Sprint 47 — ConversationState
            elif msg_type == "state":
                state_data = engine.get_conversation_state()
                await websocket.send_json({"type": "conversation_state", **state_data})
            # Sprint 47.4 — Latency + Backpressure
            elif msg_type == "latency":
                from app.application.transcription.latency import get_latency_report
                report = get_latency_report(session_id)
                await websocket.send_json({"type": "latency", **report.to_dict()})
            elif msg_type == "backpressure":
                await websocket.send_json({"type": "backpressure", **engine.get_backpressure_stats()})

    except Exception as e:
        logger.error("Coach WebSocket error: %s", e)
    finally:
        remove_coach_engine(session_id)
        try:
            await websocket.close()
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════
# SPRINT 44 — Post-Call Intelligence
# ═══════════════════════════════════════════════════════════

@router.post("/postcall/generate/{transcript_id}")
async def generate_postcall(
    transcript_id: int,
    auth: AuthContext = Depends(require_permission("telephony:write")),
    db: Session = Depends(get_db_session),
):
    """Generate all post-call deliverables from a completed transcript."""
    from app.infrastructure.repositories.transcript import TranscriptRepository
    repo = TranscriptRepository(db)
    transcript = repo.get_transcript(transcript_id)
    if not transcript:
        return {"error": "Transcript not found"}, 404

    segments = repo.get_final_segments(transcript_id)
    transcript_text = " ".join(s.text for s in segments)

    # Get coach events if available
    coach_events: list[dict] = []

    pipeline = PostCallPipeline(_get_llm_config())
    report = await pipeline.generate_all(
        transcript_text=transcript_text,
        coach_events=coach_events,
        call_id=transcript.call_id,
        transcript_id=transcript_id,
        company_id=transcript.company_id,
    )

    # Add to approval queue
    for d in report.deliverables:
        _approval_queue.append({
            "id": d.id,
            "transcript_id": transcript_id,
            "call_id": transcript.call_id,
            "type": d.type.value,
            "status": d.status.value,
            "content": d.content,
            "generated_at": d.generated_at,
        })

    return {
        "transcript_id": transcript_id,
        "deliverables": [
            {"id": d.id, "type": d.type.value, "content_preview": d.content[:200]}
            for d in report.deliverables
        ],
        "total": len(report.deliverables),
    }


@router.get("/postcall/queue")
async def get_approval_queue(
    status: str | None = Query(None),
    auth: AuthContext = Depends(require_permission("read:telephony")),
):
    """Get the approval queue of generated deliverables."""
    items = _approval_queue
    if status:
        items = [i for i in items if i["status"] == status]
    return {
        "items": items[-50:],  # Last 50
        "total": len(items),
        "pending": sum(1 for i in _approval_queue if i["status"] == "pending"),
        "approved": sum(1 for i in _approval_queue if i["status"] == "approved"),
        "rejected": sum(1 for i in _approval_queue if i["status"] == "rejected"),
    }


@router.post("/postcall/queue/{item_id}/approve")
async def approve_deliverable(
    item_id: str,
    auth: AuthContext = Depends(require_permission("write:telephony")),
):
    """Approve a deliverable from the queue."""
    for item in _approval_queue:
        if item["id"] == item_id:
            item["status"] = "approved"
            return {"id": item_id, "status": "approved"}
    return {"error": "Item not found"}, 404


@router.post("/postcall/queue/{item_id}/reject")
async def reject_deliverable(
    item_id: str,
    auth: AuthContext = Depends(require_permission("write:telephony")),
):
    """Reject a deliverable from the queue."""
    for item in _approval_queue:
        if item["id"] == item_id:
            item["status"] = "rejected"
            return {"id": item_id, "status": "rejected"}
    return {"error": "Item not found"}, 404
