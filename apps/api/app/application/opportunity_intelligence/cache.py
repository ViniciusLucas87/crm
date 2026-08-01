"""
Cache layer for OpportunityIntelligence.

Target: <50ms response for cached lookups.
Invalidates on: conversation change, proposal regeneration, activity creation, opportunity update.

Architecture:
    In-memory LRU dict (no Redis dependency) with TTL-based expiry.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

from app.domain.opportunity_intelligence import OpportunityIntelligence

logger = logging.getLogger(__name__)

TTL_SECONDS = 300  # 5 minutes


class OpportunityIntelligenceCache:
    """Thread-safe in-memory cache for OpportunityIntelligence objects.

    Invalidate on:
        - Conversation changes (new insights)
        - Proposal regenerated
        - Activity created
        - Opportunity updated
    """

    def __init__(self, ttl: int = TTL_SECONDS):
        self._ttl = ttl
        self._store: dict[str, tuple[OpportunityIntelligence, float]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> OpportunityIntelligence | None:
        """Get cached intelligence. Returns None if expired or missing."""
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            intelligence, expires_at = entry
            if time.time() > expires_at:
                del self._store[key]
                return None
            return intelligence

    def set(self, key: str, intelligence: OpportunityIntelligence) -> None:
        """Store intelligence with TTL."""
        with self._lock:
            self._store[key] = (intelligence, time.time() + self._ttl)

    def invalidate(self, key: str) -> None:
        """Remove a specific key from cache."""
        with self._lock:
            self._store.pop(key, None)

    def invalidate_by_company(self, company_id: int) -> None:
        """Invalidate all cached entries for a company."""
        with self._lock:
            keys_to_delete = [k for k in self._store if k.endswith(f":{company_id}")]
            for k in keys_to_delete:
                del self._store[k]
            if keys_to_delete:
                logger.debug("Cache invalidated for company %d (%d entries)", company_id, len(keys_to_delete))

    def invalidate_all(self) -> None:
        """Clear entire cache."""
        with self._lock:
            self._store.clear()
            logger.debug("Entire OpportunityIntelligence cache cleared")

    def stats(self) -> dict[str, Any]:
        """Return cache statistics."""
        with self._lock:
            return {
                "size": len(self._store),
                "ttl": self._ttl,
                "keys": list(self._store.keys()),
            }

    @staticmethod
    def make_key(opportunity_id: int, organization_id: int) -> str:
        return f"oi:{organization_id}:{opportunity_id}"


# Global singleton
_cache: OpportunityIntelligenceCache | None = None


def get_opportunity_intelligence_cache() -> OpportunityIntelligenceCache:
    global _cache
    if _cache is None:
        _cache = OpportunityIntelligenceCache()
    return _cache


def invalidate_for_company(company_id: int) -> None:
    """Called when company data changes — invalidates all related caches."""
    get_opportunity_intelligence_cache().invalidate_by_company(company_id)


def invalidate_all() -> None:
    """Called on major system events."""
    get_opportunity_intelligence_cache().invalidate_all()
