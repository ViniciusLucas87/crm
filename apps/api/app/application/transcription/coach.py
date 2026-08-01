"""
Sprint 43 — AI Live Sales Coach

Real-time conversation intelligence that consumes transcript events
and emits coaching suggestions, warnings, and opportunity insights.

Architecture:
    Transcript Segment → CoachEngine → Coaching Event → Live Side Panel

Never blocks audio. All processing is async and streaming-based.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import StrEnum
from typing import Any

from app.application.llm.provider import LLMConfig, LLMMessage, create_provider
from app.application.transcription.conversation_state import (
    ConversationState, GPSEngine, PriorityEngine, detect_competitor,
)
from app.application.transcription.fast_coach import FastCoachEngine
from app.application.transcription.dedup import DedupEngine
from app.application.transcription.latency import (
    SegmentLatency, LatencyReport, get_latency_report, remove_latency_report, now_ms,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# COACHING EVENT TYPES
# ═══════════════════════════════════════════════════════════

class CoachEventType(StrEnum):
    # Sprint 43 — original
    OBJECTION_DETECTED = "objection_detected"
    BUDGET_MENTIONED = "budget_mentioned"
    TIMELINE_MENTIONED = "timeline_mentioned"
    DECISION_MAKER_IDENTIFIED = "decision_maker_identified"
    PAIN_POINT_DETECTED = "pain_point_detected"
    BUYING_SIGNAL = "buying_signal"
    COMPETITOR_MENTIONED = "competitor_mentioned"
    SENTIMENT_SHIFT = "sentiment_shift"
    RISK_ALERT = "risk_alert"
    COACH_SUGGESTION = "coach_suggestion"
    NEXT_QUESTION = "next_question"
    MISSING_TOPIC = "missing_topic"
    REMINDER = "reminder"
    CONVERSATION_HEALTH = "conversation_health"
    OPPORTUNITY_SCORE = "opportunity_score"
    # Sprint 46 — Live Copilot 2.0
    AI_WHISPER = "ai_whisper"
    DISCOVERY_UPDATE = "discovery_update"
    BUYING_SIGNAL_DETECTED = "buying_signal_detected"
    OBJECTION_RESPONSE = "objection_response"
    NEXT_BEST_QUESTION = "next_best_question"
    CONVERSATION_STAGE = "conversation_stage"
    CONVERSATION_SCORE = "conversation_score"
    KNOWLEDGE_EXTRACTED = "knowledge_extracted"
    CONVERSATION_OPENING = "conversation_opening"


class CoachSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    SUCCESS = "success"


@dataclass
class CoachEvent:
    """A single coaching event emitted during a live call."""
    type: CoachEventType
    severity: CoachSeverity = CoachSeverity.INFO
    title: str = ""
    description: str = ""
    suggestion: str = ""
    evidence: str = ""  # quote from transcript
    confidence: int = 50  # 0-100
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationHealth:
    """Real-time conversation health metrics."""
    talk_ratio: float = 0.5
    questions_asked: int = 0
    objections_handled: int = 0
    positive_signals: int = 0
    negative_signals: int = 0
    engagement_score: int = 50
    rapport_score: int = 50
    overall_health: str = "neutral"

    # Sprint 43 enhanced — discovery tracking
    budget_discussed: bool = False
    timeline_discussed: bool = False
    decision_makers_identified: int = 0
    pain_points_found: int = 0
    competitors_detected: int = 0
    topics_covered: set = field(default_factory=set)


# ═══════════════════════════════════════════════════════════
# MISSING DISCOVERY TOPICS — what should have been discussed
# ═══════════════════════════════════════════════════════════

DISCOVERY_TOPICS = {
    "budget": {"label": "Budget & Authority", "icon": "💰", "category": "qualification"},
    "timeline": {"label": "Timeline & Urgency", "icon": "⏰", "category": "qualification"},
    "decision_process": {"label": "Decision Process", "icon": "👥", "category": "qualification"},
    "pain_points": {"label": "Pain Points", "icon": "🎯", "category": "discovery"},
    "current_solution": {"label": "Current Solution", "icon": "🔧", "category": "discovery"},
    "success_criteria": {"label": "Success Criteria", "icon": "✅", "category": "discovery"},
    "integration_needs": {"label": "Integration Needs", "icon": "🔌", "category": "technical"},
    "security_compliance": {"label": "Security & Compliance", "icon": "🛡️", "category": "technical"},
    "stakeholders": {"label": "Key Stakeholders", "icon": "👤", "category": "qualification"},
    "competitors": {"label": "Competitive Landscape", "icon": "🏢", "category": "positioning"},
    "roi": {"label": "ROI / Business Case", "icon": "📊", "category": "value"},
    "next_steps": {"label": "Next Steps", "icon": "➡️", "category": "closing"},
}

TOPIC_KEYWORDS = {
    "budget": ["budget", "cost", "price", "pricing", "spend", "invest"],
    "timeline": ["timeline", "deadline", "when", "quarter", "month", "soon"],
    "decision_process": ["decision", "approval", "sign off", "my boss", "committee"],
    "pain_points": ["problem", "challenge", "issue", "struggling", "pain", "headache"],
    "current_solution": ["currently using", "current provider", "existing", "we use"],
    "success_criteria": ["success", "kpi", "goal", "metric", "measure", "outcome"],
    "integration_needs": ["integration", "api", "connect", "sync", "work with"],
    "security_compliance": ["security", "compliance", "gdpr", "soc2", "hipaa", "data"],
    "stakeholders": ["ceo", "cto", "cfo", "vp", "director", "manager", "team"],
    "competitors": ["salesforce", "hubspot", "zoho", "competitor", "alternative"],
    "roi": ["roi", "return", "savings", "efficiency", "pay for itself", "worth"],
    "next_steps": ["next steps", "follow up", "demo", "trial", "proposal"],
}


# ═══════════════════════════════════════════════════════════
# COACH ENGINE
# ═══════════════════════════════════════════════════════════

class CoachEngine:
    """Real-time sales coaching engine.

    Consumes transcript segments and emits coaching events.
    Uses keyword detection for instant feedback and LLM for deeper analysis.
    """

    # ── Keyword patterns for instant detection ──

    OBJECTION_PATTERNS = [
        "too expensive", "not in budget", "can't afford", "price is",
        "cheaper", "competitor", "already using", "not interested",
        "not a priority", "think about it", "call me back",
        "send me information", "talk to my", "need to discuss",
    ]

    BUDGET_PATTERNS = [
        "budget", "cost", "price", "pricing", "spend",
        "invest", "dollars", "$", "money", "afford",
    ]

    TIMELINE_PATTERNS = [
        "timeline", "deadline", "by when", "next month", "next quarter",
        "q1", "q2", "q3", "q4", "soon", "urgent", "asap",
        "by end of", "by the end", "by next", "within",
    ]

    DECISION_MAKER_PATTERNS = [
        "decision maker", "decision-maker", "my boss", "my manager",
        "the ceo", "the cto", "the cfo", "the vp", "the director",
        "I need to run this by", "approval from", "sign off",
    ]

    PAIN_POINT_PATTERNS = [
        "problem", "issue", "challenge", "struggling", "pain",
        "headache", "frustrating", "difficult", "hard to",
        "can't keep up", "falling behind", "losing", "wasting",
    ]

    BUYING_SIGNAL_PATTERNS = [
        "sounds good", "interesting", "tell me more", "how does it work",
        "how soon", "what's next", "next steps", "let's move forward",
        "I like", "this could work", "when can we start",
    ]

    COMPETITOR_PATTERNS = [
        "salesforce", "hubspot", "zoho", "pipedrive", "monday",
        "asana", "clickup", "notion", "airtable", "competitor",
        "other solution", "current provider", "existing vendor",
    ]

    def __init__(self, llm_config: LLMConfig | None = None, session_id: str = ""):
        self._llm_config = llm_config
        self._session_id = session_id
        self._segments: list[dict] = []
        self._health = ConversationHealth()
        self._events: list[CoachEvent] = []
        self._subscribers: list = []
        # Sprint 47 — ConversationState replaces scattered fields
        self._state = ConversationState()
        self._gps = GPSEngine()
        self._priority = PriorityEngine()
        # Sprint 47.4 — Fast path + dedup + latency
        self._fast = FastCoachEngine()
        self._dedup = DedupEngine()
        self._latency = get_latency_report(session_id) if session_id else LatencyReport()
        # Legacy compat
        self._agent_utterances = 0
        self._customer_utterances = 0
        self._agent_words = 0
        self._customer_words = 0
        self._discovery: dict[str, str] = {}
        self._discovery_confidence: dict[str, int] = {}
        self._stage: str = "opening"
        self._stage_triggered: set[str] = set()
        self._whisper_cooldown = 0
        self._last_whisper_text = ""
        self._extracted_knowledge: list[dict] = []
        self._buying_signals_found: list[dict] = []
        self._objections_found: list[dict] = []
        # Sprint 47.4 — Backpressure + LLM streaming
        self._llm_active: bool = False
        self._llm_queued: bool = False
        self._llm_last_call: float = 0.0
        self._llm_min_interval: float = 0.8  # 800ms min between LLM calls
        self._llm_max_wait: float = 2.0       # 2s max wait for meaningful update
        self._pending_llm_context: str = ""
        self._llm_requests_started: int = 0
        self._llm_requests_cancelled: int = 0
        self._llm_requests_merged: int = 0
        self._llm_requests_completed: int = 0

    # ── Sprint 46 — Buying signal patterns ──
    GROWTH_PATTERNS = ["growing", "growth", "expanding", "scaling", "hiring", "new offices", "more customers"]
    MANUAL_WORK_PATTERNS = ["manually", "spreadsheet", "excel", "paper", "print", "copy paste", "data entry"]
    PROCESS_PATTERNS = ["process", "workflow", "automation", "efficiency", "bottleneck", "slow", "takes too long"]

    # ── Sprint 46 — Conversation stages ──
    STAGE_ORDER = ["opening", "rapport", "discovery", "pain_points", "current_process",
                   "budget", "timeline", "decision_maker", "solution_alignment", "closing"]
    
    DISCOVERY_CHECKLIST = {
        "decision_maker": {"label": "Decision Maker", "icon": "👤"},
        "current_software": {"label": "Current Software", "icon": "💻"},
        "pain_points": {"label": "Pain Points", "icon": "🎯"},
        "budget": {"label": "Budget", "icon": "💰"},
        "timeline": {"label": "Timeline", "icon": "⏰"},
        "authority": {"label": "Authority", "icon": "👥"},
        "existing_process": {"label": "Current Process", "icon": "🔄"},
        "success_metrics": {"label": "Success Metrics", "icon": "📊"},
        "buying_signals": {"label": "Buying Signals", "icon": "✅"},
    }
    
    STAGE_TRIGGERS = {
        "opening": ["hi", "hello", "thanks for", "appreciate", "introduce", "meeting"],
        "rapport": ["how are you", "busy", "weekend", "family", "weather"],
        "discovery": ["tell me about", "how do you", "what are you", "current", "process"],
        "pain_points": ["challenge", "problem", "issue", "struggling", "pain", "difficult"],
        "current_process": ["workflow", "currently", "how do you currently", "steps"],
        "budget": ["budget", "cost", "price", "pricing", "spend", "invest", "dollar"],
        "timeline": ["timeline", "deadline", "when", "quarter", "urgent", "soon"],
        "decision_maker": ["decision", "approval", "boss", "manager", "sign off", "cto", "ceo"],
        "solution_alignment": ["solution", "platform", "system", "would help", "could solve"],
        "closing": ["next steps", "follow up", "demo", "proposal", "trial", "start"],
    }

    def subscribe(self, callback):
        """Subscribe to coaching events."""
        self._subscribers.append(callback)

    async def _emit(self, event: CoachEvent):
        self._events.append(event)
        for cb in self._subscribers:
            try:
                await cb(event)
            except Exception:
                pass

    async def process_segment(self, segment: dict) -> list[CoachEvent]:
        """Process a single transcript segment and return new coaching events.
        
        Sprint 47.4: Fast path (deterministic) → emit immediately.
        Then debounce LLM for AI refinement if needed.
        """
        try:
            return await self._process_segment_impl(segment)
        except Exception as e:
            logger.error("CoachEngine.process_segment failed: %s", e, exc_info=True)
            return []
    
    async def _process_segment_impl(self, segment: dict) -> list[CoachEvent]:
        text = segment.get("text", "").lower()
        speaker = segment.get("speaker", "Unknown")
        is_final = segment.get("is_final", False)
        new_events: list[CoachEvent] = []
        
        # ── LATENCY: Record coach_received_at ──
        sl = SegmentLatency(
            segment_id=segment.get("id", f"seg-{len(self._segments)}"),
            coach_received_at=now_ms(),
        )
        if segment.get("audio_end_at"):
            sl.audio_end_at = segment["audio_end_at"]
        if segment.get("deepgram_final_at"):
            sl.deepgram_final_at = segment["deepgram_final_at"]
        if segment.get("normalized_at"):
            sl.normalized_at = segment["normalized_at"]

        # ── DEDUP: Only process unique finals ──
        if is_final:
            dedup_result = self._dedup.process(segment)
            if dedup_result in ("duplicate", "out_of_order"):
                return new_events
            # dedup_result is "new_final" — continue processing
        
        # Track speaker stats
        is_customer = "1" in speaker or "customer" in speaker.lower()
        if is_customer:
            self._customer_utterances += 1
            self._customer_words += len(text.split())
        else:
            self._agent_utterances += 1
            self._agent_words += len(text.split())

        # Update talk ratio
        total = self._agent_words + self._customer_words
        if total > 0:
            self._health.talk_ratio = self._agent_words / total
            if self._health.talk_ratio > 0.7:
                self._health.overall_health = "at_risk"
            elif self._health.talk_ratio < 0.3:
                self._health.overall_health = "at_risk"
            else:
                self._health.overall_health = "good"

        if not is_final:
            return new_events

        self._segments.append(segment)
        
        # ── Sprint 47.4: FAST PATH — deterministic, sub-150ms ──
        fast_result = self._fast.process(segment)
        if fast_result:
            sl.state_updated_at = now_ms()
            # Support both old FastCoachResult and new CoachingRecommendation
            key = getattr(fast_result, 'semantic_key', None) or getattr(fast_result, 'key', '')
            detail = getattr(fast_result, 'reason', None) or getattr(fast_result, 'detail', '')
            wording = getattr(fast_result, 'suggested_wording', None) or getattr(fast_result, 'action', None) or detail
            evidence = getattr(fast_result, 'evidence', None) or segment.get("text", "")
            alternatives = getattr(fast_result, 'alternatives', None) or []
            expected = getattr(fast_result, 'expected_outcome', None) or ""
            transition = getattr(fast_result, 'transition', None) or ""
            expires = getattr(fast_result, 'expires_when', None) or ""
            
            whisper = CoachEvent(
                type=CoachEventType.AI_WHISPER,
                severity=(CoachSeverity.CRITICAL if fast_result.priority == "critical"
                          else CoachSeverity.WARNING if fast_result.priority == "high"
                          else CoachSeverity.INFO),
                title=fast_result.title,
                description=detail,
                suggestion=wording,
                evidence=evidence,
                confidence=fast_result.confidence,
                metadata={
                    "priority": fast_result.priority,
                    "key": key,
                    "category": getattr(fast_result, 'category', ''),
                    "source": "fast",
                    "stage": getattr(fast_result, 'stage', ''),
                    "transition": transition,
                    "alternatives": alternatives,
                    "expected_outcome": expected,
                    "expires_when": expires,
                    "dedup": self._dedup.counters.to_dict(),
                    # Sprint 47.6 — stale prevention
                    "created_at": now_ms(),
                    "based_on_segment": len(self._segments),
                    "relevance_version": len(self._segments),
                },
            )
            new_events.append(whisper)
            await self._emit(whisper)
        
        # Record the fast-coach state update time
        sl.state_updated_at = now_ms()

        # ── Sprint 47 — Incremental state update ──
        self.update_state_from_segment(segment.get("text", ""), speaker)

        # ── Sprint 46 — Enhanced analysis (lightweight, no LLM) ──
        discovery_events = self._update_discovery(segment.get("text", ""), speaker)
        new_events.extend(discovery_events)
        for evt in discovery_events:
            await self._emit(evt)

        signal_events = self._detect_buying_signals(segment.get("text", ""), speaker)
        new_events.extend(signal_events)
        for evt in signal_events:
            await self._emit(evt)

        obj_resp = self._get_objection_response(segment.get("text", ""))
        if obj_resp:
            self._objections_found.append({"text": segment.get("text", "")[:120], "type": obj_resp.metadata.get("objection_type", "")})
            new_events.append(obj_resp)
            await self._emit(obj_resp)

        facts = self._extract_knowledge(segment.get("text", ""), speaker)
        self._extracted_knowledge.extend(facts)

        # ── Sprint 47.4: EVENT-DRIVEN LLM — debounced, streaming, backpressure ──
        should_llm = self._should_trigger_llm(segment)
        if should_llm:
            self._schedule_llm(segment)
        
        # ── GPS + Stage (periodic, lightweight) ──
        if len(self._segments) % 3 == 0:
            stage_evt = self._update_stage()
            if stage_evt:
                new_events.append(stage_evt)
                await self._emit(stage_evt)
                gps_data = self._gps.calculate(self._state)
                await self._emit(CoachEvent(
                    type=CoachEventType.CONVERSATION_STAGE,
                    severity=CoachSeverity.INFO,
                    title="GPS Update",
                    description=f"→ {gps_data['current_destination']}",
                    confidence=85,
                    metadata={"gps": gps_data},
                ))

        # ── Deal health (every 8 segments) ──
        if len(self._segments) % 8 == 0:
            score_evt = self._get_conversation_score()
            new_events.append(score_evt)
            await self._emit(score_evt)
        
        # ── LATENCY: Record and log ──
        self._latency.record(sl)
        if len(self._segments) % 5 == 0:
            report = self._latency.get_p50_p95()
            logger.info(
                "Coach latency p50=%dms p95=%dms (n=%d) dedup: %s",
                report["p50_ms"], report["p95_ms"], report["sample_count"],
                self._dedup.counters.to_dict(),
            )

        return new_events

    # ═══════════════════════════════════════════════════════════
    # SPRINT 47.4 — EVENT-DRIVEN LLM TRIGGERS
    # ═══════════════════════════════════════════════════════════

    def _should_trigger_llm(self, segment: dict) -> bool:
        """Determine if this segment warrants an LLM call."""
        text = segment.get("text", "").lower()
        role = segment.get("source_role", segment.get("speaker", "unknown"))
        is_prospect = role in ("prospect", "customer", "1") or "customer" in str(role).lower()
        
        triggers = [
            # Prospect completes a meaningful statement
            is_prospect and len(text.split()) > 5,
            # Objection detected
            any(kw in text for kw in ("too expensive", "not in budget", "can't afford", "competitor", "not interested", "think about it")),
            # Pain point detected
            any(kw in text for kw in ("problem", "challenge", "issue", "struggling", "pain", "headache", "frustrating")),
            # Buying signal
            any(kw in text for kw in ("sounds good", "interesting", "tell me more", "next steps", "when can we start", "i like")),
            # Stage change trigger
            any(kw in text for kw in ("budget", "timeline", "decision", "approval", "next steps")),
            # Decision maker mentioned
            any(kw in text for kw in ("ceo", "cto", "cfo", "my boss", "manager", "director")),
            # Current recommendation is stale (>5 segments since last LLM)
            self._llm_requests_completed == 0 and len(self._segments) >= 5,
            # Confidence is low and reasoning needed
            self._state.deal_risk > 70,
        ]
        return any(triggers)
    
    def _schedule_llm(self, segment: dict):
        """Debounced LLM scheduling with backpressure.
        
        Rules:
        - Minimum 800ms between LLM calls
        - At most 1 active + 1 queued
        - Merge context when multiple segments arrive
        - Cancel superseded requests
        """
        now = now_ms() / 1000.0
        
        # If an LLM call is active, queue one more (merging context)
        if self._llm_active:
            if not self._llm_queued:
                self._llm_queued = True
                self._pending_llm_context = " ".join(
                    s.get("text", "") for s in self._segments[-8:]
                )
                self._llm_requests_merged += 1
            else:
                # Already queued — update context with latest
                self._pending_llm_context = " ".join(
                    s.get("text", "") for s in self._segments[-8:]
                )
                self._llm_requests_merged += 1
            return
        
        # Check minimum interval
        elapsed = now - self._llm_last_call
        if elapsed < self._llm_min_interval:
            # Too soon — queue if not already
            if not self._llm_queued:
                self._llm_queued = True
                self._pending_llm_context = " ".join(
                    s.get("text", "") for s in self._segments[-8:]
                )
                self._llm_requests_merged += 1
            return
        
        # OK to launch
        context = " ".join(s.get("text", "") for s in self._segments[-8:])
        import asyncio
        asyncio.create_task(self._run_llm_with_backpressure(context))
    
    async def _run_llm_with_backpressure(self, context: str):
        """Execute LLM call with streaming, then check for queued work."""
        self._llm_active = True
        self._llm_last_call = now_ms() / 1000.0
        self._llm_requests_started += 1
        
        try:
            await self._generate_streaming_insight(context)
        except Exception as e:
            logger.warning("LLM streaming insight failed: %s", e)
        finally:
            self._llm_active = False
            self._llm_requests_completed += 1
            
            # Process queued request if any
            if self._llm_queued:
                self._llm_queued = False
                queued_context = self._pending_llm_context
                self._pending_llm_context = ""
                # Ensure minimum interval before next call
                elapsed = (now_ms() / 1000.0) - self._llm_last_call
                if elapsed < self._llm_min_interval and queued_context:
                    import asyncio
                    await asyncio.sleep(self._llm_min_interval - elapsed)
                if queued_context:
                    import asyncio
                    asyncio.create_task(self._run_llm_with_backpressure(queued_context))
    
    async def _generate_streaming_insight(self, transcript_text: str):
        """Stream LLM response token by token. Updates the same coach card.
        
        Uses structured output: {action, question, reason, confidence}
        Sends partial tokens via WebSocket as they arrive.
        """
        if not self._llm_config or len(transcript_text) < 100:
            return
        
        try:
            provider = create_provider(self._llm_config)
            
            # Compact prompt — incremental state, not full transcript
            state = self._state
            context = {
                "stage": state.current_stage,
                "discovery_done": state.discovery_count,
                "discovery_total": state.discovery_total,
                "talk_ratio": round(state.talk_ratio * 100),
                "buying_signals": len(state.buying_signals),
                "objections": len(state.active_objections),
                "missing_discovery": [
                    k for k, v in {
                        "decision_maker": state.decision_maker,
                        "budget": state.budget,
                        "timeline": state.timeline,
                        "pain_points": state.pain_points,
                    }.items() if v == "unknown"
                ],
            }
            
            messages = [
                LLMMessage(role="system", content=(
                    "You are a senior B2B sales coach for Pacific North Systems, a custom software and automation company. "
                    "Your job is to provide ONE precise, immediately usable recommendation for the seller. "
                    "Ground your advice in the latest prospect statement. Provide EXACT wording the seller can say. "
                    "Explain why this matters. Avoid generic advice. Do not repeat questions already answered. "
                    "Adapt to the company and industry context provided. "
                    "Move the conversation toward discovery and a concrete next step. Be concise.\n\n"
                    "Respond in JSON:\n"
                    "{\"title\":\"<short action phrase>\",\"suggested_wording\":\"<exact words to say>\","
                    "\"reason\":\"<why this move now>\",\"evidence\":\"<what triggered this>\","
                    "\"expected_outcome\":\"<what this should achieve>\",\"alternatives\":[\"<alt1>\",\"<alt2>\"],"
                    "\"priority\":\"critical|high|medium|low\",\"confidence\":<0-100>}\n\n"
                    "REQUIREMENTS: suggested_wording must NOT be empty. evidence must reference the prospect statement. "
                    "Do NOT produce labels like 'Build Rapport' or 'Ask an open question'. "
                    "Provide specific, actionable language the seller can use immediately."
                )),
                LLMMessage(role="user", content=(
                    f"Company context: {json.dumps(context)}\n"
                    f"Recent conversation:\n{transcript_text[-2000:]}"
                )),
            ]
            
            # ── LATENCY: Record LLM start ──
            llm_start = now_ms()
            
            # Stream tokens
            full_response = ""
            first_token_sent = False
            async for token in provider.chat_stream(
                messages,
                temperature=0.3,
                max_tokens=200,
            ):
                full_response += token
                
                if not first_token_sent and len(full_response) > 10:
                    first_token_sent = True
                    # ── LATENCY: First token ──
                    ttft = now_ms() - llm_start
                    logger.info("LLM TTFT: %.0fms", ttft)
                    
                    # Try to parse partial JSON for early rendering
                    partial = self._try_extract_action(full_response)
                    if partial:
                        await self._emit(CoachEvent(
                            type=CoachEventType.AI_WHISPER,
                            severity=CoachSeverity.INFO,
                            title=partial.get("action", "AI Insight"),
                            description=partial.get("reason", ""),
                            suggestion=partial.get("question", ""),
                            evidence=partial.get("evidence", ""),
                            confidence=partial.get("confidence", 70),
                            metadata={
                                "source": "ai_streaming",
                                "key": "ai_insight",
                                "partial": True,
                                "llm_ttft_ms": round(ttft),
                                "evidence": partial.get("evidence", ""),
                                "expected_outcome": partial.get("expected_outcome", ""),
                                "alternatives": partial.get("alternatives", []),
                            },
                        ))
            
            # ── LATENCY: LLM completed ──
            llm_done = now_ms()
            logger.info("LLM total: %.0fms, TTFT: calculated above", llm_done - llm_start)
            
            # Final parsed response
            final = self._try_extract_action(full_response)
            if final:
                await self._emit(CoachEvent(
                    type=CoachEventType.AI_WHISPER,
                    severity=CoachSeverity.INFO,
                    title=final.get("action", "AI Insight"),
                    description=final.get("reason", ""),
                    suggestion=final.get("question", ""),
                    evidence=final.get("evidence", ""),
                    confidence=final.get("confidence", 75),
                    metadata={
                        "source": "ai",
                        "key": "ai_insight",
                        "partial": False,
                        "llm_total_ms": round(llm_done - llm_start),
                        "evidence": final.get("evidence", ""),
                        "expected_outcome": final.get("expected_outcome", ""),
                        "alternatives": final.get("alternatives", []),
                    },
                ))
        
        except Exception as e:
            logger.warning("Streaming LLM failed: %s", e)
    
    def _try_extract_action(self, text: str) -> dict | None:
        """Try to extract structured action from (possibly partial) JSON.
        Sprint 47.5 — handles new schema with suggested_wording, evidence, alternatives."""
        try:
            data = json.loads(text.strip())
            return {
                "action": data.get("title", data.get("action", "")),
                "question": data.get("suggested_wording", data.get("question", "")),
                "reason": data.get("reason", ""),
                "evidence": data.get("evidence", ""),
                "expected_outcome": data.get("expected_outcome", ""),
                "alternatives": data.get("alternatives", []),
                "confidence": data.get("confidence", 70),
            }
        except json.JSONDecodeError:
            result = {}
            for field in ["title", "suggested_wording", "action", "question", "reason", "evidence", "expected_outcome"]:
                import re
                m = re.search(rf'"{field}"\s*:\s*"([^"]*)', text)
                if m:
                    if field in ("title", "action"):
                        result["action"] = result.get("action") or m.group(1)
                    elif field in ("suggested_wording", "question"):
                        result["question"] = result.get("question") or m.group(1)
                    else:
                        result[field] = m.group(1)
            if result:
                result["confidence"] = 60
                return result
        return None
    
    def get_backpressure_stats(self) -> dict:
        """Return backpressure metrics."""
        return {
            "requests_started": self._llm_requests_started,
            "requests_cancelled": self._llm_requests_cancelled,
            "requests_merged": self._llm_requests_merged,
            "requests_completed": self._llm_requests_completed,
            "active": self._llm_active,
            "queued": self._llm_queued,
        }

    async def generate_deep_insight(self, transcript_text: str) -> CoachEvent | None:
        """Legacy method — now delegates to streaming insight."""
        if not self._llm_config or len(transcript_text) < 200:
            return None

        try:
            provider = create_provider(self._llm_config)
            messages = [
                LLMMessage(role="system", content=(
                    "You are a sales coach analyzing a live conversation. "
                    "Identify: (1) the top objection, (2) the strongest buying signal, "
                    "(3) one suggested next question the agent should ask. "
                    "Respond in JSON: {\"objection\":\"...\", \"buying_signal\":\"...\", \"next_question\":\"...\"}"
                )),
                LLMMessage(role="user", content=f"Transcript:\n{transcript_text[-3000:]}"),
            ]
            response = await provider.chat(messages, temperature=0.3, max_tokens=200)
            data = json.loads(response.content)

            suggestions = []
            if data.get("objection"):
                suggestions.append(f"🛑 Handle objection: {data['objection']}")
            if data.get("buying_signal"):
                suggestions.append(f"✅ Build on signal: {data['buying_signal']}")
            if data.get("next_question"):
                suggestions.append(f"❓ Next question: {data['next_question']}")

            if suggestions:
                evt = CoachEvent(
                    type=CoachEventType.COACH_SUGGESTION,
                    severity=CoachSeverity.INFO,
                    title="AI Coach Insight",
                    description="\n".join(suggestions),
                    confidence=60,
                )
                await self._emit(evt)
                return evt
        except Exception as e:
            logger.warning("Coach LLM insight failed: %s", e)

        return None

    def _get_missing_topics(self) -> list[dict]:
        """Return discovery topics that haven't been discussed yet."""
        missing = []
        for topic_id, info in DISCOVERY_TOPICS.items():
            if topic_id not in self._health.topics_covered:
                missing.append({"id": topic_id, "label": info["label"], "icon": info["icon"], "category": info["category"]})
        return missing

    def get_opportunity_score(self) -> dict:
        """Calculate real-time opportunity score from conversation signals."""
        signals = self._health.positive_signals
        objections = self._health.objections_handled
        topics = len(self._health.topics_covered)
        engagement = self._health.engagement_score
        rapport = self._health.rapport_score

        base = 40
        score = base + (signals * 4) - (objections * 6) + (topics * 2) + (engagement // 10) + (rapport // 10)
        score = max(0, min(100, score))

        stage = "discovery" if topics < 4 else "qualification" if topics < 8 else "proposal"

        return {
            "score": score,
            "stage": stage,
            "signals": signals,
            "objections": objections,
            "topics_covered": topics,
            "total_topics": len(DISCOVERY_TOPICS),
            "recommendation": "pursue" if score >= 65 else "nurture" if score >= 40 else "review",
        }

    def get_reminders(self) -> list[dict]:
        """Get reminder cards for the agent based on conversation state."""
        reminders = []
        health = self._health

        if health.talk_ratio > 0.65:
            reminders.append({"icon": "🎤", "text": "You're talking too much. Ask an open question.", "priority": "high"})
        if health.objections_handled > 0 and health.objections_handled % 3 == 0:
            reminders.append({"icon": "🛡️", "text": f"{health.objections_handled} objections so far — stay calm and validate.", "priority": "medium"})
        if health.positive_signals >= 3:
            reminders.append({"icon": "✅", "text": "Strong signals detected — consider moving toward close.", "priority": "high"})
        missing = self._get_missing_topics()
        if len(missing) > 8:
            reminders.append({"icon": "📋", "text": f"Only {len(self._health.topics_covered)}/{len(DISCOVERY_TOPICS)} topics covered — broaden discovery.", "priority": "medium"})
        if health.engagement_score < 40:
            reminders.append({"icon": "⚡", "text": "Engagement dropping — try changing pace or topic.", "priority": "high"})
        if health.rapport_score < 40:
            reminders.append({"icon": "🤝", "text": "Rapport is low — find common ground or empathize.", "priority": "high"})

        return reminders

    # ═══════════════════════════════════════════════════════════
    # SPRINT 46 — ENHANCED METHODS
    # ═══════════════════════════════════════════════════════════

    def _update_discovery(self, text: str, speaker: str) -> list[CoachEvent]:
        """Update discovery tracker based on transcript text."""
        events: list[CoachEvent] = []
        is_customer = "1" in speaker or "customer" in speaker.lower()

        patterns = {
            "decision_maker": ["ceo", "cto", "cfo", "vp", "director", "manager", "decision", "approval"],
            "current_software": ["using", "software", "platform", "system", "tool", "currently", "provider"],
            "pain_points": ["problem", "challenge", "issue", "struggling", "pain", "headache", "frustrated"],
            "budget": ["budget", "cost", "price", "pricing", "spend", "invest", "dollars", "money"],
            "timeline": ["timeline", "deadline", "quarter", "month", "week", "soon", "urgent"],
            "authority": ["decision", "approval", "sign off", "boss", "my manager", "need to check"],
            "existing_process": ["process", "workflow", "steps", "how we do", "currently", "manual"],
            "success_metrics": ["success", "kpi", "goal", "metric", "measure", "outcome", "result"],
            "buying_signals": ["sounds good", "interesting", "tell me more", "next steps", "when can we", "like this"],
        }

        changed = False
        for key, keywords in patterns.items():
            if any(kw in text.lower() for kw in keywords):
                old_status = self._discovery[key]
                new_status = "confirmed" if is_customer else "partial"
                if old_status == "unknown":
                    self._discovery[key] = new_status
                    self._discovery_confidence[key] = 70 if is_customer else 40
                    changed = True
                elif old_status == "partial" and is_customer:
                    self._discovery[key] = "confirmed"
                    self._discovery_confidence[key] = min(100, self._discovery_confidence[key] + 25)
                    changed = True

        if changed:
            items = [{"id": k, "label": self.DISCOVERY_CHECKLIST.get(k, {}).get("label", k),
                       "status": self._discovery[k], "confidence": self._discovery_confidence[k]}
                     for k in self._discovery]
            events.append(CoachEvent(
                type=CoachEventType.DISCOVERY_UPDATE,
                severity=CoachSeverity.INFO,
                title="Discovery Updated",
                description=f"Discovery tracker updated ({sum(1 for v in self._discovery.values() if v != 'unknown')}/{len(self._discovery)} items)",
                confidence=80,
                metadata={"items": items},
            ))
        return events

    def _detect_buying_signals(self, text: str, speaker: str) -> list[CoachEvent]:
        """Detect buying signals with evidence and confidence."""
        events: list[CoachEvent] = []
        signal_patterns = [
            (self.GROWTH_PATTERNS, "Growth", "Company shows growth indicators — potential need for scaling"),
            (self.MANUAL_WORK_PATTERNS, "Manual Work", "Manual processes detected — automation opportunity"),
            (["scheduling", "schedule", "calendar", "booking"], "Scheduling Issues", "Scheduling challenges mentioned"),
            (["communication", "email", "teams", "slack", "messages"], "Communication", "Communication workflow discussed"),
            (["compliance", "regulation", "gdpr", "hipaa", "security"], "Compliance", "Compliance/regulatory needs detected"),
            (["report", "reporting", "dashboard", "analytics", "data"], "Reporting", "Reporting/analytics needs mentioned"),
            (["digital", "transform", "modernize", "upgrade", "cloud"], "Digital Transformation", "Digital transformation initiative"),
        ]

        for patterns, signal_type, description in signal_patterns:
            if any(p in text.lower() for p in patterns):
                evidence = text[:120]
                sig = {"type": signal_type, "description": description, "evidence": evidence, "confidence": 75}
                self._buying_signals_found.append(sig)
                events.append(CoachEvent(
                    type=CoachEventType.BUYING_SIGNAL_DETECTED,
                    severity=CoachSeverity.SUCCESS,
                    title=f"Buying Signal: {signal_type}",
                    description=description,
                    suggestion=description,
                    evidence=evidence,
                    confidence=75,
                    metadata={"signal_type": signal_type},
                ))
                break  # one signal per segment max
        return events

    def _get_objection_response(self, text: str) -> CoachEvent | None:
        """Generate objection response suggestion."""
        objection_map = {
            "budget": ("Budget Concern", "Acknowledge budget constraints. Ask: 'What budget range were you considering?' Share flexible pricing options.", "Focus on ROI, not price"),
            "timing": ("Timing Concern", "Validate their timeline. Ask: 'What would make this more urgent?' Offer phased approach.", "Create urgency with value"),
            "already have": ("Existing Solution", "Don't criticize competitor. Ask: 'What's one thing you wish your current solution did better?'", "Differentiate on unique value"),
            "approval": ("Approval Needed", "Offer to join a call with the decision maker. Ask: 'What information would help them decide?'", "Make them your champion"),
            "busy": ("Too Busy", "Respect their time. Suggest: 'Would a 15-min focused demo next week work better?'", "Shorten commitment"),
            "competitor": ("Competitor Mentioned", "Acknowledge competition positively. Ask: 'What made you consider alternatives?'", "Find their unmet need"),
        }

        for key, (title, suggestion, angle) in objection_map.items():
            triggers = {
                "budget": ["too expensive", "not in budget", "can't afford", "price", "cost"],
                "timing": ["not now", "later", "next year", "not ready", "think about"],
                "already have": ["already using", "already have", "current provider", "existing"],
                "approval": ["need to check", "my boss", "approval", "run this by"],
                "busy": ["busy", "no time", "too much", "swamped", "schedule"],
                "competitor": ["salesforce", "hubspot", "zoho", "competitor", "other vendor"],
            }
            if any(t in text.lower() for t in triggers.get(key, [])):
                return CoachEvent(
                    type=CoachEventType.OBJECTION_RESPONSE,
                    severity=CoachSeverity.WARNING if key != "competitor" else CoachSeverity.INFO,
                    title=title,
                    description=suggestion,
                    suggestion=angle,
                    evidence=text[:120],
                    confidence=80,
                    metadata={"objection_type": key},
                )
        return None

    def _get_next_best_question(self) -> CoachEvent | None:
        """Calculate the next best question based on conversation state."""
        # Priority: fill unknown discovery items
        unknown = [k for k, v in self._discovery.items() if v == "unknown"]
        questions = {
            "decision_maker": "Who else would be involved in evaluating a solution like this?",
            "current_software": "What software are you currently using to manage this?",
            "pain_points": "What's the biggest challenge your team faces right now?",
            "budget": "Have you allocated budget for solving this problem?",
            "timeline": "What's your timeline for making a decision?",
            "authority": "Who would need to approve this purchase?",
            "existing_process": "Can you walk me through your current process?",
            "success_metrics": "How would you measure success for this project?",
            "buying_signals": "",  # skip — this is derived
        }

        if unknown:
            top = unknown[0]
            q = questions.get(top, f"Tell me more about {top.replace('_', ' ')}")
            stage_idx = self.STAGE_ORDER.index(self._stage) if self._stage in self.STAGE_ORDER else 0
            return CoachEvent(
                type=CoachEventType.NEXT_BEST_QUESTION,
                severity=CoachSeverity.INFO,
                title="Next Best Question",
                description=q,
                suggestion=f"Ask this now — it fills a gap in discovery ({self._stage} stage)",
                confidence=min(90, 50 + (len(self._segments) // 2)),
                metadata={"stage": self._stage, "missing_item": top, "stage_index": stage_idx},
            )

        # All known — suggest based on stage
        stage_questions = {
            "opening": "Can you tell me a bit about your role and what you're responsible for?",
            "rapport": "How has business been going this quarter?",
            "discovery": "What's one process you wish was more efficient?",
            "pain_points": "How is that challenge impacting your team's productivity?",
            "current_process": "What happens after [key step] in your workflow?",
            "budget": "How do you typically evaluate ROI for tools like this?",
            "timeline": "If we could solve this by next month, would that work?",
            "decision_maker": "Would it help if I prepared a summary for your leadership?",
            "solution_alignment": "Would you like to see how this would work for your specific use case?",
            "closing": "What would you need to feel confident moving forward?",
        }
        q = stage_questions.get(self._stage, "What else would be helpful to discuss?")
        return CoachEvent(
            type=CoachEventType.NEXT_BEST_QUESTION,
            severity=CoachSeverity.INFO,
            title="Next Best Question",
            description=q,
            suggestion=f"Natural next step for {self._stage} stage",
            confidence=70,
            metadata={"stage": self._stage},
        )

    def _update_stage(self) -> CoachEvent | None:
        """Track and update conversation stage."""
        # Build full recent text
        recent = " ".join(s.get("text", "") for s in self._segments[-5:]).lower()

        for stage in self.STAGE_ORDER:
            if stage in self._stage_triggered:
                continue
            triggers = self.STAGE_TRIGGERS.get(stage, [])
            if any(t in recent for t in triggers):
                self._stage = stage
                self._stage_triggered.add(stage)
                progress = {s: "completed" if s in self._stage_triggered else ("in_progress" if s == stage else "not_started")
                           for s in self.STAGE_ORDER}
                return CoachEvent(
                    type=CoachEventType.CONVERSATION_STAGE,
                    severity=CoachSeverity.INFO,
                    title=f"Stage: {stage.replace('_', ' ').title()}",
                    description=f"Conversation advanced to {stage.replace('_', ' ')}",
                    confidence=75,
                    metadata={"stage": stage, "progress": progress, "stage_order": self.STAGE_ORDER},
                )
        return None

    def _get_conversation_score(self) -> CoachEvent:
        """Generate meaningful conversation metrics from ConversationState."""
        state = self._state
        state.discovery_quality = int(state.discovery_count / max(1, state.discovery_total) * 100)
        state.buying_intent = min(100, len(state.buying_signals) * 15)
        state.information_completeness = int(state.discovery_count / max(1, state.discovery_total) * 100)
        state.deal_risk = max(0, 100 - state.discovery_quality + len(state.active_objections) * 10)
        state.close_probability = int((state.discovery_quality * 0.4 + state.buying_intent * 0.3 + state.information_completeness * 0.3))
        state.momentum = "up" if len(state.buying_signals) > len(state.active_objections) else "down" if state.active_objections else "stable"

        return CoachEvent(
            type=CoachEventType.CONVERSATION_SCORE,
            severity=CoachSeverity.INFO,
            title="Conversation Score",
            description=f"Discovery: {state.discovery_quality}% | Intent: {state.buying_intent}% | Close: {state.close_probability}%",
            confidence=80,
            metadata={
                "discovery_quality": state.discovery_quality,
                "buying_intent": state.buying_intent,
                "information_completeness": state.information_completeness,
                "risk": state.deal_risk,
                "close_probability": state.close_probability,
                "momentum": state.momentum,
            },
        )

    def _extract_knowledge(self, text: str, speaker: str) -> list[dict]:
        """Extract knowledge facts from transcript for Knowledge Graph."""
        facts = []
        extraction_patterns = [
            (["we use", "using", "our current", "our platform"], "current_software"),
            (["employees", "people", "team of", "staff of"], "company_size"),
            (["department", "division", "business unit"], "departments"),
            (["integrate", "integration", "connect with", "api"], "integrations"),
            (["competitor", "alternative", "other vendor", "salesforce", "hubspot"], "competitors"),
            (["manual", "paper", "excel", "spreadsheet", "data entry"], "manual_processes"),
            (["compliance", "regulation", "gdpr", "hipaa", "soc2"], "compliance_needs"),
        ]
        for patterns, fact_type in extraction_patterns:
            if any(p in text.lower() for p in patterns):
                facts.append({"type": fact_type, "evidence": text[:200], "speaker": speaker,
                              "confidence": 70, "timestamp": datetime.now(UTC).isoformat()})
        return facts

    def _generate_whisper(self) -> CoachEvent | None:
        """Generate ONE concise AI whisper — never spam."""
        self._whisper_cooldown -= 1
        if self._whisper_cooldown > 0:
            return None

        # Don't repeat the same whisper
        whispers = []

        # Check discovery gaps
        unknown = [k for k, v in self._discovery.items() if v == "unknown"]
        if unknown:
            whispers.append(("Ask about " + unknown[0].replace("_", " "), "Fill discovery gap", 80))

        # Check talk ratio
        if self._health.talk_ratio > 0.7:
            whispers.append(("Let the customer speak — ask an open question", "Talk ratio too high", 85))

        # Check buying signals
        if len(self._buying_signals_found) >= 2 and self._stage not in ("solution_alignment", "closing"):
            whispers.append(("Strong interest — consider presenting the solution", "Multiple buying signals", 75))

        # Check objections
        if len(self._objections_found) >= 2 and len(self._objections_found) > len(self._buying_signals_found):
            whispers.append(("Address objections before moving forward", "Objections outweigh signals", 80))

        if not whispers:
            return None

        text, reason, confidence = whispers[0]
        if text == self._last_whisper_text:
            return None

        self._whisper_cooldown = 6  # Wait ~6 segments before next whisper
        self._last_whisper_text = text

        return CoachEvent(
            type=CoachEventType.AI_WHISPER,
            severity=CoachSeverity.INFO,
            title="AI Whisper",
            description=text,
            suggestion=reason,
            confidence=confidence,
            metadata={"priority": "high" if confidence > 80 else "medium"},
        )

    def get_discovery(self) -> list[dict]:
        return [{"id": k, "label": self.DISCOVERY_CHECKLIST.get(k, {}).get("label", k),
                 "status": self._discovery[k], "confidence": self._discovery_confidence[k]}
                for k in self._discovery]

    def get_stage_progress(self) -> dict:
        return {"current": self._stage, "completed": list(self._stage_triggered),
                "stages": [{"id": s, "status": "completed" if s in self._stage_triggered else
                           ("in_progress" if s == self._stage else "not_started")}
                          for s in self.STAGE_ORDER]}

    def get_buying_signals(self) -> list[dict]:
        return list(self._buying_signals_found)

    def get_knowledge_extracted(self) -> list[dict]:
        return list(self._extracted_knowledge)

    def get_conversation_state(self) -> dict:
        """Sprint 47.4 — return full state with latency + backpressure + dedup metrics."""
        gps_data = self._gps.calculate(self._state)
        rec = self._priority.evaluate(self._state)
        fast_state = self._fast.get_state()
        latency_report = self._latency.get_p50_p95()
        return {
            "state": self._state.to_dict(),
            "gps": gps_data,
            "recommendation": rec,
            "competitor": None,
            "fast_coach": fast_state,
            "latency": latency_report,
            "backpressure": self.get_backpressure_stats(),
            "dedup": self._dedup.counters.to_dict(),
        }

    def update_state_from_segment(self, text: str, speaker: str) -> None:
        """Incrementally update ConversationState from transcript."""
        s = self._state
        is_customer = "1" in speaker or "customer" in speaker.lower()
        wc = len(text.split())
        if is_customer:
            s.customer_words += wc
            s.customer_utterances += 1
        else:
            s.agent_words += wc
            s.agent_utterances += 1
        t = text.lower()
        if any(kw in t for kw in ["ceo", "cto", "director", "manager", "decision", "approval"]):
            s.decision_maker = "confirmed" if is_customer else "partial"
        if any(kw in t for kw in ["using", "software", "platform", "system", "tool"]):
            s.current_software = "confirmed" if is_customer else "partial"
        if any(kw in t for kw in ["problem", "challenge", "issue", "pain", "struggling"]):
            s.pain_points = "confirmed" if is_customer else "partial"
        if any(kw in t for kw in ["budget", "cost", "price", "spend", "invest"]):
            s.budget = "confirmed" if is_customer else "partial"
        if any(kw in t for kw in ["timeline", "deadline", "quarter", "month", "soon"]):
            s.timeline = "confirmed" if is_customer else "partial"
        comp = detect_competitor(text)
        if comp and comp["name"].lower() not in [c.lower() for c in s.competitors_detected]:
            s.competitors_detected.append(comp["name"])
            s.competitors = "confirmed"
        s.touch()

    def get_health(self) -> ConversationHealth:
        return self._health

    def get_events(self) -> list[CoachEvent]:
        return list(self._events)

    def reset(self):
        self._segments.clear()
        self._health = ConversationHealth()
        self._events.clear()
        self._agent_utterances = 0
        self._customer_utterances = 0
        self._agent_words = 0
        self._customer_words = 0
        # Sprint 46 reset
        self._discovery = {k: "unknown" for k in self._discovery}
        self._discovery_confidence = {k: 0 for k in self._discovery_confidence}
        self._stage = "opening"
        self._stage_triggered.clear()
        self._whisper_cooldown = 0
        self._last_whisper_text = ""
        self._extracted_knowledge.clear()
        self._buying_signals_found.clear()
        self._objections_found.clear()


# ═══════════════════════════════════════════════════════════
# SESSION MANAGER
# ═══════════════════════════════════════════════════════════

_coach_sessions: dict[str, CoachEngine] = {}


def get_coach_engine(session_id: str) -> CoachEngine:
    """Get or create a coach engine for a session."""
    if session_id not in _coach_sessions:
        llm_config = LLMConfig(
            provider=os.getenv("LLM_PROVIDER", "openai"),
            api_key=os.getenv("LLM_API_KEY", os.getenv("OPENAI_API_KEY", "")),
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        )
        _coach_sessions[session_id] = CoachEngine(llm_config=llm_config, session_id=session_id)
    return _coach_sessions[session_id]


def remove_coach_engine(session_id: str):
    engine = _coach_sessions.pop(session_id, None)
    if engine:
        engine.reset()
    remove_latency_report(session_id)
