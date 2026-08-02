"""
LLM Governance Gateway — Sprint: Production Cost Hardening

Centralized entry point for ALL LLM calls in the CRM.
No direct provider calls may bypass this gateway.

Features:
  - Model routing: flash/cheap by default, Pro only for allowlist
  - per-request token caps (input 8K, output feature-specific)
  - Redis cache with feature TTL + single-flight deduplication
  - Budget/circuit breaker (global + per-org daily/monthly)
  - Retry policy (only 429/5xx, max 1 paid retry)
  - Usage logging to ai_request_logs
  - LLM_ENABLED kill switch with deterministic fallbacks
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from typing import Any

import redis

from app.application.llm.provider import (
    LLMConfig,
    LLMMessage,
    LLMProvider,
    LLMResponse,
    create_provider,
)

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════
# CONFIGURATION (from env vars with safe defaults)
# ═══════════════════════════════════════════════════════════

@lru_cache
def _get_redis() -> redis.Redis | None:
    url = os.getenv("REDIS_URL", "")
    if not url:
        return None
    try:
        return redis.Redis.from_url(url, socket_timeout=2, socket_connect_timeout=2)
    except Exception:
        return None


def _env_bool(key: str, default: bool = True) -> bool:
    return os.getenv(key, str(default).lower()).lower() in ("true", "1", "yes")


def _env_int(key: str, default: int) -> int:
    return int(os.getenv(key, str(default)))


def _env_float(key: str, default: float) -> float:
    return float(os.getenv(key, str(default)))


# ── Model routing ──
LLM_FLASH_MODEL = os.getenv("LLM_FLASH_MODEL", "deepseek-chat")  # cheap default
LLM_PRO_MODEL = os.getenv("LLM_PRO_MODEL", "deepseek-chat")       # explicit allowlist only
LLM_REASONING_MODEL = os.getenv("LLM_REASONING_MODEL", "deepseek-chat")

# Features that may use the Pro model
LLM_PRO_FEATURES: set[str] = set(
    os.getenv("LLM_PRO_FEATURES", "proposal_studio,executive_summary").split(",")
)

# ── Token limits ──
LLM_MAX_INPUT_TOKENS = _env_int("LLM_MAX_INPUT_TOKENS", 8000)
LLM_OUTPUT_CLASSIFICATION = _env_int("LLM_OUTPUT_CLASSIFICATION", 300)
LLM_OUTPUT_COACHING = _env_int("LLM_OUTPUT_COACHING", 200)
LLM_OUTPUT_ENRICHMENT = _env_int("LLM_OUTPUT_ENRICHMENT", 600)
LLM_OUTPUT_PROPOSAL = _env_int("LLM_OUTPUT_PROPOSAL", 800)

# Feature → output token cap
FEATURE_OUTPUT_TOKENS: dict[str, int] = {
    "coaching_whisper": LLM_OUTPUT_COACHING,
    "coaching_deep": LLM_OUTPUT_COACHING,
    "classification_pain": LLM_OUTPUT_CLASSIFICATION,
    "classification_buying_signal": LLM_OUTPUT_CLASSIFICATION,
    "classification_objection": LLM_OUTPUT_CLASSIFICATION,
    "classification_stage": LLM_OUTPUT_CLASSIFICATION,
    "enrichment_company": LLM_OUTPUT_ENRICHMENT,
    "enrichment_lead": LLM_OUTPUT_ENRICHMENT,
    "enrichment_google_maps": LLM_OUTPUT_ENRICHMENT,
    "enrichment_website": LLM_OUTPUT_ENRICHMENT,
    "enrichment_reviews": LLM_OUTPUT_ENRICHMENT,
    "enrichment_linkedin": LLM_OUTPUT_ENRICHMENT,
    "proposal_studio": LLM_OUTPUT_PROPOSAL,
    "executive_summary": LLM_OUTPUT_PROPOSAL,
    "default": LLM_OUTPUT_CLASSIFICATION,
}

# ── Cache TTLs ──
FEATURE_CACHE_TTL: dict[str, int] = {
    "enrichment_company": 86400,       # 24h
    "enrichment_google_maps": 86400,   # 24h
    "enrichment_website": 43200,       # 12h
    "enrichment_reviews": 86400,       # 24h
    "enrichment_linkedin": 86400,      # 24h
    "coaching_whisper": 60,            # 1min (conversational)
    "coaching_deep": 300,              # 5min
    "classification_pain": 3600,       # 1h
    "classification_buying_signal": 3600,
    "classification_objection": 3600,
    "classification_stage": 3600,
    "proposal_studio": 3600,
    "executive_summary": 3600,
    "default": 3600,
}

# ── Budget ──
LLM_ENABLED = _env_bool("LLM_ENABLED", True)
LLM_GLOBAL_DAILY_COST_LIMIT = _env_float("LLM_GLOBAL_DAILY_COST_LIMIT", 2.50)  # $2.50/day
LLM_GLOBAL_MONTHLY_COST_LIMIT = _env_float("LLM_GLOBAL_MONTHLY_COST_LIMIT", 50.00)
LLM_ORG_DAILY_COST_LIMIT = _env_float("LLM_ORG_DAILY_COST_LIMIT", 1.00)

# ── Retry ──
LLM_MAX_RETRIES = _env_int("LLM_MAX_RETRIES", 1)
LLM_RETRY_BASE_SECONDS = _env_float("LLM_RETRY_BASE_SECONDS", 2.0)

# Estimated cost per 1K tokens (DeepSeek pricing)
COST_PER_1K_INPUT = 0.00014   # $0.14/M input
COST_PER_1K_OUTPUT = 0.00028  # $0.28/M output
COST_PER_1K_CACHE_HIT = 0.000014  # $0.014/M cache hit


# ═══════════════════════════════════════════════════════════
# GATEWAY
# ═══════════════════════════════════════════════════════════

@dataclass
class GatewayConfig:
    """Configuration for a single LLM gateway call."""
    feature: str = "default"
    model: str | None = None   # None = route automatically
    max_tokens: int | None = None
    temperature: float = 0.3
    organization_id: int = 1
    cache_ttl: int | None = None  # None = use default for feature
    bypass_cache: bool = False
    job_id: str | None = None


@dataclass
class GatewayResponse:
    content: str
    usage: dict[str, int] = field(default_factory=dict)
    cached: bool = False
    deduped: bool = False
    model: str = ""
    cost_estimate: float = 0.0
    latency_ms: float = 0.0


class LLMGateway:
    """Centralized LLM gateway — ALL LLM calls must go through here."""

    def __init__(self) -> None:
        self._redis = _get_redis()
        self._active_locks: set[str] = set()

    async def chat(
        self,
        messages: list[LLMMessage],
        config: GatewayConfig | None = None,
    ) -> GatewayResponse:
        """Send a chat completion with full governance."""
        config = config or GatewayConfig()
        feature = config.feature
        org_id = config.organization_id
        start_time = time.monotonic()

        # ── 1. Kill switch ──
        if not LLM_ENABLED:
            return GatewayResponse(
                content=_fallback_response(feature, messages),
                model="fallback",
                cached=False,
                cost_estimate=0,
            )

        # ── 2. Model routing ──
        model = config.model or _route_model(feature)

        # ── 3. Token cap ──
        output_tokens = config.max_tokens or FEATURE_OUTPUT_TOKENS.get(feature, FEATURE_OUTPUT_TOKENS["default"])
        messages = _truncate_messages(messages, LLM_MAX_INPUT_TOKENS)

        # ── 4. Cache check ──
        cache_key = _cache_key(feature, model, messages)
        ttl = config.cache_ttl or FEATURE_CACHE_TTL.get(feature, FEATURE_CACHE_TTL["default"])
        if not config.bypass_cache and self._redis:
            cached = self._redis.get(cache_key)
            if cached:
                elapsed = (time.monotonic() - start_time) * 1000
                await _log_usage(org_id, feature, model, input_tokens=0, output_tokens=0,
                                 cached=True, deduped=False, cost=0, latency_ms=elapsed,
                                 job_id=config.job_id, success=True)
                return GatewayResponse(
                    content=cached.decode("utf-8"),
                    cached=True,
                    model=model,
                    cost_estimate=COST_PER_1K_CACHE_HIT,
                    latency_ms=elapsed,
                )

        # ── 5. Single-flight deduplication ──
        lock_key = f"llm:lock:{cache_key}"
        if self._redis:
            # If another request is already computing this, wait briefly for result
            if self._redis.exists(lock_key):
                for _ in range(30):  # wait up to 3s
                    await _async_sleep(0.1)
                    cached = self._redis.get(cache_key)
                    if cached:
                        elapsed = (time.monotonic() - start_time) * 1000
                        await _log_usage(org_id, feature, model, input_tokens=0, output_tokens=0,
                                         cached=True, deduped=True, cost=0, latency_ms=elapsed,
                                         job_id=config.job_id, success=True)
                        return GatewayResponse(
                            content=cached.decode("utf-8"),
                            cached=True,
                            deduped=True,
                            model=model,
                            cost_estimate=0,
                            latency_ms=elapsed,
                        )
            self._redis.setex(lock_key, 30, "1")

        # ── 6. Budget check ──
        budget_ok, budget_reason = await _check_budget(org_id)
        if not budget_ok:
            if self._redis:
                self._redis.delete(lock_key)
            logger.warning("LLM budget blocked: org=%s reason=%s", org_id, budget_reason)
            return GatewayResponse(
                content=_fallback_response(feature, messages),
                model="budget_blocked",
                cost_estimate=0,
            )

        # ── 7. Execute with retry ──
        try:
            response, retries = await _call_with_retry(messages, model, output_tokens, config.temperature)
            elapsed = (time.monotonic() - start_time) * 1000
            usage = response.usage or {}

            # ── 8. Cache result ──
            if self._redis and not config.bypass_cache:
                self._redis.setex(cache_key, ttl, response.content)

            # ── 9. Track cost ──
            input_toks = usage.get("prompt_tokens", 0)
            output_toks = usage.get("completion_tokens", 0)
            cost = (input_toks / 1000 * COST_PER_1K_INPUT) + (output_toks / 1000 * COST_PER_1K_OUTPUT)

            await _log_usage(org_id, feature, model, input_tokens=input_toks, output_tokens=output_toks,
                             cached=False, deduped=False, cost=cost, latency_ms=elapsed,
                             job_id=config.job_id, success=True, retries=retries)

            return GatewayResponse(
                content=response.content,
                usage=usage,
                model=model,
                cost_estimate=cost,
                latency_ms=elapsed,
            )

        except Exception as exc:
            elapsed = (time.monotonic() - start_time) * 1000
            await _log_usage(org_id, feature, model, input_tokens=0, output_tokens=0,
                             cached=False, deduped=False, cost=0, latency_ms=elapsed,
                             job_id=config.job_id, success=False, error=str(exc)[:200])
            logger.error("LLM gateway call failed: feature=%s model=%s error=%s", feature, model, str(exc)[:200])
            return GatewayResponse(
                content=_fallback_response(feature, messages),
                model="error",
                cost_estimate=0,
            )
        finally:
            if self._redis:
                self._redis.delete(lock_key)


# ═══════════════════════════════════════════════════════════
# MODEL ROUTING
# ═══════════════════════════════════════════════════════════

def _route_model(feature: str) -> str:
    """Route to flash/cheap model by default. Pro only for allowlist."""
    if feature in LLM_PRO_FEATURES:
        return LLM_PRO_MODEL
    return LLM_FLASH_MODEL


# ═══════════════════════════════════════════════════════════
# TOKEN MANAGEMENT
# ═══════════════════════════════════════════════════════════

def _estimate_tokens(messages: list[LLMMessage]) -> int:
    """Rough token estimate: ~4 chars per token."""
    total = sum(len(m.content or "") for m in messages)
    return total // 4


def _truncate_messages(messages: list[LLMMessage], max_tokens: int) -> list[LLMMessage]:
    """Truncate message history to fit within token budget."""
    total = _estimate_tokens(messages)
    if total <= max_tokens:
        return messages

    # Always keep system message + last user message
    result: list[LLMMessage] = []
    system = next((m for m in messages if m.role == "system"), None)
    if system:
        result.append(system)

    # Keep last N messages from end
    remaining = max_tokens - _estimate_tokens(result) - 200  # reserve 200 for output
    kept: list[LLMMessage] = []
    for m in reversed(messages):
        if m.role == "system":
            continue
        msg_tokens = _estimate_tokens([m])
        if remaining - msg_tokens >= 0:
            kept.insert(0, m)
            remaining -= msg_tokens
        else:
            # Truncate this message
            chars = remaining * 4
            truncated = LLMMessage(role=m.role, content=f"{m.content[:chars]}... [truncated]")
            kept.insert(0, truncated)
            break

    return result + kept


# ═══════════════════════════════════════════════════════════
# CACHE
# ═══════════════════════════════════════════════════════════

def _cache_key(feature: str, model: str, messages: list[LLMMessage]) -> str:
    """Deterministic cache key: feature + model + content hash."""
    content = json.dumps([{"role": m.role, "content": m.content[:200]} for m in messages], sort_keys=True)
    content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
    return f"llm:cache:{feature}:{model}:{content_hash}"


# ═══════════════════════════════════════════════════════════
# BUDGET / CIRCUIT BREAKER
# ═══════════════════════════════════════════════════════════

async def _check_budget(org_id: int) -> tuple[bool, str]:
    """Check global and org-level budget. Returns (allowed, reason)."""
    if not LLM_ENABLED:
        return False, "llm_disabled"

    r = _get_redis()
    if not r:
        return True, "no_redis"

    today = datetime.now(UTC).strftime("%Y-%m-%d")
    month = datetime.now(UTC).strftime("%Y-%m")

    # Global daily
    global_daily_key = f"llm:budget:global:daily:{today}"
    global_daily = float(r.get(global_daily_key) or 0)
    if global_daily >= LLM_GLOBAL_DAILY_COST_LIMIT:
        return False, f"global_daily_limit: {global_daily:.2f} >= {LLM_GLOBAL_DAILY_COST_LIMIT:.2f}"

    # Global monthly
    global_monthly_key = f"llm:budget:global:monthly:{month}"
    global_monthly = float(r.get(global_monthly_key) or 0)
    if global_monthly >= LLM_GLOBAL_MONTHLY_COST_LIMIT:
        return False, f"global_monthly_limit: {global_monthly:.2f} >= {LLM_GLOBAL_MONTHLY_COST_LIMIT:.2f}"

    # Org daily
    org_daily_key = f"llm:budget:org:{org_id}:daily:{today}"
    org_daily = float(r.get(org_daily_key) or 0)
    if org_daily >= LLM_ORG_DAILY_COST_LIMIT:
        return False, f"org_daily_limit: org={org_id} {org_daily:.2f} >= {LLM_ORG_DAILY_COST_LIMIT:.2f}"

    return True, "ok"


async def _track_budget(org_id: int, cost: float) -> None:
    """Track cost against budgets."""
    if cost <= 0:
        return
    r = _get_redis()
    if not r:
        return

    today = datetime.now(UTC).strftime("%Y-%m-%d")
    month = datetime.now(UTC).strftime("%Y-%m")
    ttl = 86400 * 32  # ~32 days

    r.incrbyfloat(f"llm:budget:global:daily:{today}", cost)
    r.expire(f"llm:budget:global:daily:{today}", ttl)
    r.incrbyfloat(f"llm:budget:global:monthly:{month}", cost)
    r.expire(f"llm:budget:global:monthly:{month}", ttl)
    r.incrbyfloat(f"llm:budget:org:{org_id}:daily:{today}", cost)
    r.expire(f"llm:budget:org:{org_id}:daily:{today}", ttl)

    # Alert thresholds
    pct = (float(r.get(f"llm:budget:global:daily:{today}") or 0) / LLM_GLOBAL_DAILY_COST_LIMIT * 100) if LLM_GLOBAL_DAILY_COST_LIMIT > 0 else 0
    if pct >= 80:
        logger.warning("LLM budget alert: daily at %.0f%% ($%.2f/$%.2f)", pct, global_daily_val(r, today), LLM_GLOBAL_DAILY_COST_LIMIT)


def global_daily_val(r, today: str) -> float:
    return float(r.get(f"llm:budget:global:daily:{today}") or 0)


# ═══════════════════════════════════════════════════════════
# RETRY POLICY
# ═══════════════════════════════════════════════════════════

RETRYABLE_STATUSES = {429, 500, 502, 503, 504}

async def _call_with_retry(
    messages: list[LLMMessage],
    model: str,
    max_tokens: int,
    temperature: float,
) -> tuple[LLMResponse, int]:
    """Call LLM with bounded retry for transient failures only."""
    import random

    config = LLMConfig(
        provider="openai",
        model=model,
        api_key=os.getenv("DEEPSEEK_API_KEY", ""),
        api_base="https://api.deepseek.com/v1",
        temperature=temperature,
        max_tokens=max_tokens,
    )
    provider = create_provider(config)
    last_exc = None

    for attempt in range(LLM_MAX_RETRIES + 1):
        try:
            response = await provider.chat(messages)
            return response, attempt
        except Exception as exc:
            last_exc = exc
            status = _extract_http_status(exc)

            # Never retry 4xx (except 429), auth errors, budget errors, parse errors
            if status is not None and status not in RETRYABLE_STATUSES:
                raise
            if attempt >= LLM_MAX_RETRIES:
                raise

            # Exponential backoff with jitter
            delay = LLM_RETRY_BASE_SECONDS * (2 ** attempt) + random.uniform(0, 1)
            logger.warning("LLM retry %d/%d: feature=unknown model=%s error=%s delay=%.1fs",
                           attempt + 1, LLM_MAX_RETRIES, model, str(exc)[:100], delay)
            await _async_sleep(delay)

    raise last_exc or RuntimeError("LLM retry exhausted")


def _extract_http_status(exc: Exception) -> int | None:
    """Extract HTTP status from various exception types."""
    exc_str = str(exc)
    if "429" in exc_str: return 429
    if "500" in exc_str: return 500
    if "502" in exc_str: return 502
    if "503" in exc_str: return 503
    if "504" in exc_str: return 504
    if "401" in exc_str: return 401
    if "403" in exc_str: return 403
    if "400" in exc_str: return 400
    if "404" in exc_str: return 404
    try:
        return getattr(exc, "status_code", None) or getattr(exc, "http_status", None)
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════
# FALLBACKS
# ═══════════════════════════════════════════════════════════

def _fallback_response(feature: str, messages: list[LLMMessage]) -> str:
    """Return a safe deterministic fallback when LLM is unavailable."""
    user_msg = next((m.content for m in reversed(messages) if m.role == "user"), "")

    if "coaching" in feature:
        return json.dumps({"type": "observation", "message": "Stay engaged with the prospect. Listen for pain points and buying signals.", "confidence": 0.5, "priority": "medium"})
    if "classification" in feature:
        return json.dumps({"result": "unknown", "confidence": 0.0, "reason": "llm_unavailable"})
    if "enrichment" in feature:
        return json.dumps({"summary": "LLM enrichment temporarily unavailable.", "status": "pending"})
    if "proposal" in feature:
        return "Proposal generation is temporarily unavailable. Please use the template-based proposal builder."

    return json.dumps({"status": "llm_unavailable", "message": "AI features are temporarily unavailable. Deterministic CRM features remain operational."})


# ═══════════════════════════════════════════════════════════
# USAGE LOGGING
# ═══════════════════════════════════════════════════════════

async def _log_usage(
    org_id: int, feature: str, model: str,
    input_tokens: int, output_tokens: int,
    cached: bool, deduped: bool, cost: float, latency_ms: float,
    job_id: str | None, success: bool, retries: int = 0,
    error: str | None = None,
) -> None:
    """Log LLM usage to ai_request_logs (fire-and-forget)."""
    try:
        # Track budget (async, fire-and-forget)
        if cost > 0 and not cached:
            import asyncio
            asyncio.create_task(_track_budget(org_id, cost))

        # Log to DB (non-blocking)
        import asyncio
        asyncio.create_task(_write_usage_log(
            org_id, feature, model, input_tokens, output_tokens,
            cached, deduped, cost, latency_ms, job_id, success, retries, error,
        ))
    except Exception:
        pass


async def _write_usage_log(
    org_id: int, feature: str, model: str,
    input_tokens: int, output_tokens: int,
    cached: bool, deduped: bool, cost: float, latency_ms: float,
    job_id: str | None, success: bool, retries: int, error: str | None,
) -> None:
    """Write usage record to database."""
    try:
        from app.infrastructure.db.session import SessionLocal
        from app.infrastructure.db.models import AIRequestLog
        db = SessionLocal()
        try:
            log = AIRequestLog(
                organization_id=org_id,
                request_id=job_id or str(uuid.uuid4()),
                feature=feature[:50],
                provider="deepseek",
                model=model[:50],
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                estimated_cost=cost,
                latency_ms=int(latency_ms),
                success=success,
                error_message=error[:500] if error else None,
            )
            db.add(log)
            db.commit()
        finally:
            db.close()
    except Exception as e:
        logger.debug("Failed to write usage log: %s", e)


# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════

async def _async_sleep(seconds: float) -> None:
    import asyncio
    await asyncio.sleep(seconds)


# ═══════════════════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════════════════

_gateway: LLMGateway | None = None


def get_llm_gateway() -> LLMGateway:
    global _gateway
    if _gateway is None:
        _gateway = LLMGateway()
    return _gateway


# ═══════════════════════════════════════════════════════════
# ADMIN: Budget / Usage Summary
# ═══════════════════════════════════════════════════════════

def get_budget_summary() -> dict:
    """Return current budget status for admin dashboard."""
    r = _get_redis()
    if not r:
        return {"status": "redis_unavailable"}

    today = datetime.now(UTC).strftime("%Y-%m-%d")
    month = datetime.now(UTC).strftime("%Y-%m")

    daily = float(r.get(f"llm:budget:global:daily:{today}") or 0)
    monthly = float(r.get(f"llm:budget:global:monthly:{month}") or 0)

    return {
        "status": "ok",
        "llm_enabled": LLM_ENABLED,
        "daily_cost": round(daily, 4),
        "daily_limit": LLM_GLOBAL_DAILY_COST_LIMIT,
        "daily_pct": round(daily / LLM_GLOBAL_DAILY_COST_LIMIT * 100, 1) if LLM_GLOBAL_DAILY_COST_LIMIT > 0 else 0,
        "monthly_cost": round(monthly, 4),
        "monthly_limit": LLM_GLOBAL_MONTHLY_COST_LIMIT,
        "monthly_pct": round(monthly / LLM_GLOBAL_MONTHLY_COST_LIMIT * 100, 1) if LLM_GLOBAL_MONTHLY_COST_LIMIT > 0 else 0,
        "flash_model": LLM_FLASH_MODEL,
        "pro_model": LLM_PRO_MODEL,
    }
