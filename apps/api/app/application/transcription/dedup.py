"""
Sprint 47.4 — Transcript Deduplication Engine

Ensures only one finalized segment per utterance reaches the Coach.
Uses stable keys: callId + sessionId + sourceRole + utteranceId (or derived hash).

Counters:
  segments_received, interims_updated, finals_created,
  duplicates_dropped, out_of_order_dropped
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any


@dataclass
class DedupCounters:
    segments_received: int = 0
    interims_updated: int = 0
    finals_created: int = 0
    duplicates_dropped: int = 0
    out_of_order_dropped: int = 0
    
    def to_dict(self) -> dict:
        return {
            "segments_received": self.segments_received,
            "interims_updated": self.interims_updated,
            "finals_created": self.finals_created,
            "duplicates_dropped": self.duplicates_dropped,
            "out_of_order_dropped": self.out_of_order_dropped,
        }


class DedupEngine:
    """Deduplicates transcript segments by stable key.
    
    One instance per call session. Thread-safe for single-producer.
    """
    
    def __init__(self):
        self._finals: set[str] = set()           # finalized segment keys
        self._interims: dict[str, dict] = {}     # interim segments by key
        self._last_end_time: dict[str, float] = {}  # per-role: last segment end time
        self.counters = DedupCounters()
    
    def _make_key(self, segment: dict) -> str:
        """Derive a stable dedup key.
        
        Priority: utteranceId > sessionId+role+start_window+text_hash
        """
        # If provider provides an utterance ID, use it
        uid = segment.get("utterance_id") or segment.get("utteranceId") or segment.get("id")
        if uid:
            return f"uid:{uid}"
        
        # Derive from session + role + start window + text hash
        sid = segment.get("session_id", segment.get("sessionId", "unknown"))
        role = segment.get("source_role", segment.get("speaker", "unknown"))
        start = segment.get("start", 0)
        text = segment.get("text", "")
        
        # Quantize start time to 2-second windows for fuzzy matching
        start_window = int(float(start) / 2.0)
        text_hash = hashlib.md5(text.strip().lower().encode()).hexdigest()[:8]
        
        return f"derived:{sid}:{role}:{start_window}:{text_hash}"
    
    def process(self, segment: dict) -> str:
        """Process a segment. Returns: 'new_final' | 'updated_interim' | 'duplicate' | 'out_of_order' | 'skipped_interim'"""
        self.counters.segments_received += 1
        
        is_final = segment.get("is_final", segment.get("isFinal", False))
        key = self._make_key(segment)
        role = segment.get("source_role", segment.get("speaker", "unknown"))
        end_time = segment.get("end", 0)
        
        # Out-of-order check: segment ends before last seen for this role
        if role in self._last_end_time and end_time < self._last_end_time[role] - 5.0:
            self.counters.out_of_order_dropped += 1
            return "out_of_order"
        
        if is_final:
            if key in self._finals:
                self.counters.duplicates_dropped += 1
                return "duplicate"
            
            # New final — remove any matching interim, add to finals
            self._interims.pop(key, None)
            self._finals.add(key)
            self._last_end_time[role] = max(self._last_end_time.get(role, 0), end_time)
            self.counters.finals_created += 1
            return "new_final"
        else:
            # Interim — update or create
            if key in self._finals:
                # Final already exists, don't overwrite with interim
                return "skipped_interim"
            
            self._interims[key] = segment
            self._last_end_time[role] = max(self._last_end_time.get(role, 0), end_time)
            self.counters.interims_updated += 1
            return "updated_interim"
    
    def reset(self):
        self._finals.clear()
        self._interims.clear()
        self._last_end_time.clear()
        self.counters = DedupCounters()
