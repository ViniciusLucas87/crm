"""
Simple in-memory rate limiter for FastAPI.

Production should use Redis-backed rate limiting (e.g., slowapi with Redis).
This implementation is suitable for single-process deployments.
"""

import time
from collections import defaultdict

from fastapi import Request, HTTPException


class RateLimiter:
    """Token-bucket rate limiter using in-memory storage."""

    def __init__(self, requests: int = 100, window_seconds: int = 60):
        self._requests = requests
        self._window = window_seconds
        self._buckets: dict[str, list[float]] = defaultdict(list)

    def _clean(self, key: str, now: float) -> None:
        cutoff = now - self._window
        self._buckets[key] = [t for t in self._buckets[key] if t > cutoff]

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        self._clean(key, now)
        if len(self._buckets[key]) >= self._requests:
            return False
        self._buckets[key].append(now)
        return True


# Pre-configured limiters
_default_limiter = RateLimiter(requests=200, window_seconds=60)   # 200 req/min general
_write_limiter = RateLimiter(requests=50, window_seconds=60)       # 50 req/min writes
_telephony_limiter = RateLimiter(requests=10, window_seconds=60)   # 10 calls/min
_auth_limiter = RateLimiter(requests=30, window_seconds=60)        # 30 auth attempts/min


async def rate_limit_middleware(request: Request, call_next):
    """FastAPI middleware that applies rate limiting based on path."""
    path = request.url.path

    # Skip health checks
    if path.endswith("/health") or path.endswith("/docs") or path.endswith("/openapi.json"):
        return await call_next(request)

    # Determine client key (IP or user)
    client_ip = request.client.host if request.client else "unknown"
    key = f"{client_ip}:{path}"

    # Select limiter based on path
    if "/telephony/call" in path and request.method == "POST":
        limiter = _telephony_limiter
    elif request.method in ("POST", "PUT", "PATCH", "DELETE"):
        limiter = _write_limiter
    elif "/auth/" in path:
        limiter = _auth_limiter
    else:
        limiter = _default_limiter

    if not limiter.is_allowed(key):
        raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")

    return await call_next(request)
