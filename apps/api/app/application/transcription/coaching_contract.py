"""
Sprint 47.5 — Rich Coaching Output Contract

Every coaching recommendation must contain actionable wording, evidence, 
expected outcomes, and an expiration condition. No more label-only cards.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any


@dataclass
class CoachingRecommendation:
    """A complete, actionable coaching recommendation.
    
    Every field must be populated. Cards without suggested_wording are incomplete.
    """
    
    # ── Required fields ──
    semantic_key: str                        # Stable dedup key
    title: str                               # Short action phrase
    action: str                              # What the seller should do
    suggested_wording: str                   # Exact language the seller can use
    reason: str                              # Why this is the best move now
    evidence: str                            # The prospect statement or context that triggered it
    expected_outcome: str                    # What information or progress this should produce
    
    # ── Priority ──
    priority: str = "medium"                 # critical | high | medium | low
    confidence: int = 75                     # 0-100
    
    # ── Alternatives ──
    alternatives: list[str] = field(default_factory=list)  # 2-4 alternative questions
    
    # ── Lifecycle ──
    expires_when: str = ""                   # Condition that makes this recommendation obsolete
    source: str = "deterministic"            # deterministic | ai | rapport
    category: str = ""                       # stage | objection | discovery_gap | buying_signal | etc.
    
    # ── Stage context ──
    stage: str = ""                          # Current conversation stage
    transition: str = ""                     # Natural transition from current stage
    
    # ── Timestamp ──
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    
    def to_dict(self) -> dict:
        return {
            "semantic_key": self.semantic_key,
            "title": self.title,
            "action": self.action,
            "suggested_wording": self.suggested_wording,
            "reason": self.reason,
            "evidence": self.evidence,
            "expected_outcome": self.expected_outcome,
            "priority": self.priority,
            "confidence": self.confidence,
            "alternatives": self.alternatives,
            "expires_when": self.expires_when,
            "source": self.source,
            "category": self.category,
            "stage": self.stage,
            "transition": self.transition,
            "timestamp": self.timestamp,
        }
    
    @classmethod
    def from_legacy(cls, key: str, title: str, detail: str, action: str | None = None,
                    priority: str = "medium", confidence: int = 75,
                    category: str = "", stage: str = "") -> "CoachingRecommendation":
        """Convert a legacy FastCoachResult into the new contract."""
        return cls(
            semantic_key=key,
            title=title,
            action=title,
            suggested_wording=action or detail,
            reason=detail,
            evidence="",
            expected_outcome="",
            priority=priority,
            confidence=confidence,
            category=category,
            stage=stage,
            source="deterministic",
        )
    
    def is_valid(self) -> bool:
        """Check if this recommendation meets the minimum quality bar."""
        if not self.suggested_wording:
            return False
        if not self.evidence:
            return False
        if not self.title or self.title in ("Build Rapport", "Ask an open question",
                                             "Discuss pain points", "Move to discovery",
                                             "Talk less", "Let the prospect speak"):
            # These are labels, not coaching
            return False
        if self.suggested_wording in ("Can you tell me more about that?",
                                       "Tell me more about that."):
            return False
        return True
