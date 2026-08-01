"""
Sprint 47.4 — Latency Instrumentation

Records timestamps at every stage of the pipeline:
  audio_end → deepgram_final → normalized → coach_received → 
  state_updated → llm_started → llm_first_token → llm_completed → 
  frontend_received → frontend_rendered

Reports p50/p95 for each segment.
"""

from __future__ import annotations

import statistics
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SegmentLatency:
    """Latency trace for a single finalized transcript segment."""
    segment_id: str = ""
    
    # Timestamps (epoch ms)
    audio_end_at: float = 0.0
    deepgram_final_at: float = 0.0
    normalized_at: float = 0.0
    coach_received_at: float = 0.0
    state_updated_at: float = 0.0
    llm_started_at: float = 0.0
    llm_first_token_at: float = 0.0
    llm_completed_at: float = 0.0
    frontend_received_at: float = 0.0
    frontend_rendered_at: float = 0.0
    
    # Derived latencies (ms)
    @property
    def transcription_latency(self) -> float:
        if self.audio_end_at and self.deepgram_final_at:
            return self.deepgram_final_at - self.audio_end_at
        return 0.0
    
    @property
    def normalization_latency(self) -> float:
        if self.deepgram_final_at and self.normalized_at:
            return self.normalized_at - self.deepgram_final_at
        return 0.0
    
    @property
    def transport_latency(self) -> float:
        if self.normalized_at and self.coach_received_at:
            return self.coach_received_at - self.normalized_at
        return 0.0
    
    @property
    def state_update_latency(self) -> float:
        if self.coach_received_at and self.state_updated_at:
            return self.state_updated_at - self.coach_received_at
        return 0.0
    
    @property
    def llm_ttft(self) -> float:
        """Time to first token."""
        if self.llm_started_at and self.llm_first_token_at:
            return self.llm_first_token_at - self.llm_started_at
        return 0.0
    
    @property
    def llm_total_latency(self) -> float:
        if self.llm_started_at and self.llm_completed_at:
            return self.llm_completed_at - self.llm_started_at
        return 0.0
    
    @property
    def render_latency(self) -> float:
        if self.frontend_received_at and self.frontend_rendered_at:
            return self.frontend_rendered_at - self.frontend_received_at
        return 0.0
    
    @property
    def end_to_end_latency(self) -> float:
        if self.audio_end_at and self.frontend_rendered_at:
            return self.frontend_rendered_at - self.audio_end_at
        return 0.0
    
    def to_dict(self) -> dict:
        return {
            "segment_id": self.segment_id,
            "latencies_ms": {
                "transcription": round(self.transcription_latency),
                "normalization": round(self.normalization_latency),
                "transport": round(self.transport_latency),
                "state_update": round(self.state_update_latency),
                "llm_ttft": round(self.llm_ttft),
                "llm_total": round(self.llm_total_latency),
                "render": round(self.render_latency),
                "end_to_end": round(self.end_to_end_latency),
            },
        }


@dataclass
class LatencyReport:
    """Aggregated latency report for a session."""
    session_id: str = ""
    segments: deque[SegmentLatency] = field(default_factory=lambda: deque(maxlen=200))
    
    def record(self, sl: SegmentLatency):
        self.segments.append(sl)
    
    def get_p50_p95(self) -> dict:
        if not self.segments:
            return {"p50_ms": 0, "p95_ms": 0, "sample_count": 0}
        
        e2e = [s.end_to_end_latency for s in self.segments if s.end_to_end_latency > 0]
        if not e2e:
            return {"p50_ms": 0, "p95_ms": 0, "sample_count": 0}
        
        sorted_e2e = sorted(e2e)
        n = len(sorted_e2e)
        p50 = sorted_e2e[int(n * 0.50)] if n > 0 else 0
        p95 = sorted_e2e[int(n * 0.95)] if n > 1 else sorted_e2e[-1] if n == 1 else 0
        
        # Per-stage p50
        stages = {
            "transcription": [s.transcription_latency for s in self.segments if s.transcription_latency > 0],
            "normalization": [s.normalization_latency for s in self.segments if s.normalization_latency > 0],
            "transport": [s.transport_latency for s in self.segments if s.transport_latency > 0],
            "state_update": [s.state_update_latency for s in self.segments if s.state_update_latency > 0],
            "llm_ttft": [s.llm_ttft for s in self.segments if s.llm_ttft > 0],
            "llm_total": [s.llm_total_latency for s in self.segments if s.llm_total_latency > 0],
            "render": [s.render_latency for s in self.segments if s.render_latency > 0],
        }
        
        def _median(vals):
            if not vals:
                return 0
            sv = sorted(vals)
            return sv[len(sv) // 2]
        
        return {
            "p50_ms": round(p50),
            "p95_ms": round(p95),
            "sample_count": n,
            "breakdown_p50_ms": {k: round(_median(v)) for k, v in stages.items()},
        }
    
    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            **self.get_p50_p95(),
            "recent_traces": [s.to_dict() for s in list(self.segments)[-5:]],
        }


# Global latency reports per session
_latency_reports: dict[str, LatencyReport] = {}


def get_latency_report(session_id: str) -> LatencyReport:
    if session_id not in _latency_reports:
        _latency_reports[session_id] = LatencyReport(session_id=session_id)
    return _latency_reports[session_id]


def remove_latency_report(session_id: str):
    _latency_reports.pop(session_id, None)


def now_ms() -> float:
    return time.time() * 1000
