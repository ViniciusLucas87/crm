"""
LLM Governance Gateway v3 — Production Cost Hardening
Central entry point for ALL LLM calls (normal + tool-calling + streaming).
Async Redis, atomic Lua reservations, refund on failure,
distributed SF locks with atomic release, full cache keys, configurable pricing.
"""

from __future__ import annotations

import asyncio, hashlib, json, logging, os, time, uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, AsyncIterator

from app.application.llm.provider import LLMConfig, LLMMessage, LLMResponse, create_provider

logger = logging.getLogger(__name__)

# ============================================================
# CONFIG -- defaults: $0.50/day, $10.00/month
# ============================================================

def _env_bool(k: str, d: bool) -> bool: return os.getenv(k, str(d)).lower() in ("true","1","yes")
def _env_int(k: str, d: int) -> int: return int(os.getenv(k, str(d)))
def _env_float(k: str, d: float) -> float: return float(os.getenv(k, str(d)))

LLM_ENABLED        = _env_bool("LLM_ENABLED", True)
LLM_FLASH_MODEL    = os.getenv("LLM_FLASH_MODEL", "deepseek-v4-flash")
# Cost-first production default: Pro must be explicitly enabled by configuration.
LLM_PRO_MODEL      = os.getenv("LLM_PRO_MODEL", "deepseek-v4-flash")
LLM_PRO_FEATURES   = set(os.getenv("LLM_PRO_FEATURES","").split(",")) if os.getenv("LLM_PRO_FEATURES") else {"proposal"}

LLM_MAX_INPUT_TOKENS   = _env_int("LLM_MAX_INPUT_TOKENS", 8000)
LLM_OUT_CLASSIFICATION = _env_int("LLM_OUTPUT_CLASSIFICATION", 300)
LLM_OUT_COACHING       = _env_int("LLM_OUTPUT_COACHING", 200)
LLM_OUT_ENRICHMENT     = _env_int("LLM_OUTPUT_ENRICHMENT", 600)
LLM_OUT_DISCOVERY      = _env_int("LLM_OUTPUT_DISCOVERY", 1200)
LLM_OUT_PROPOSAL       = _env_int("LLM_OUTPUT_PROPOSAL", 800)
LLM_OUT_MCP            = 2000

FEATURE_OUTPUT_TOKENS = {
    "coaching":LLM_OUT_COACHING, "classification":LLM_OUT_CLASSIFICATION,
    "enrichment":LLM_OUT_ENRICHMENT, "discovery":LLM_OUT_DISCOVERY, "proposal":LLM_OUT_PROPOSAL,
    "mcp":LLM_OUT_MCP, "default":LLM_OUT_CLASSIFICATION,
}
# Hard per-request context ceilings. A single feature should never inherit the
# full global context window unless it genuinely needs it.
FEATURE_INPUT_TOKENS = {
    "coaching": 3000, "classification": 2500, "enrichment": 2000,
    "discovery": 3000, "proposal": 6000, "mcp": 4000, "default": 2500,
}
FEATURE_CACHE_TTL = {
    "enrichment":86400, "discovery":86400, "coaching":60, "classification":3600,
    "proposal":3600, "mcp":300, "default":3600,
}
# ═══════════════════════════════════════════════════════════
# RESERVATION INPUT CALC — use actual message token count as floor
# ═══════════════════════════════════════════════════════════

# Feature floors: minimum tokens to reserve per feature (conservative estimate).
# Used only when actual message tokens are below this floor.
_FEATURE_INPUT_FLOOR = {
    "coaching": 3000, "classification": 4000, "enrichment": 2000, "discovery": 1200,
    "proposal": 6000, "mcp": 6000, "default": 4000,
}


def _reserve_input(
    messages: list[LLMMessage],
    feature: str,
    max_input: int = LLM_MAX_INPUT_TOKENS,
) -> int:
    """Reserve max(actual bounded token count, feature floor), capped at max_input.
    Guarantees: reserved >= actual usage, no unaccounted overage.
    """
    feature_floor = _FEATURE_INPUT_FLOOR.get(feature, _FEATURE_INPUT_FLOOR["default"])
    actual_est = _est_tok(messages)  # already bounded by truncation
    return min(max(actual_est, feature_floor), max_input)


def _reserve_output(feature: str, config_max: int | None = None) -> int:
    """Reserve max(config_max, feature output cap)."""
    feature_cap = FEATURE_OUTPUT_TOKENS.get(feature, FEATURE_OUTPUT_TOKENS["default"])
    return max(config_max or 0, feature_cap)

LLM_GLOBAL_DAILY_LIMIT    = _env_float("LLM_GLOBAL_DAILY_COST_LIMIT", 0.10)
LLM_GLOBAL_MONTHLY_LIMIT  = _env_float("LLM_GLOBAL_MONTHLY_COST_LIMIT", 2.00)
LLM_ORG_DAILY_LIMIT       = _env_float("LLM_ORG_DAILY_COST_LIMIT", 0.10)
LLM_ORG_MONTHLY_LIMIT     = _env_float("LLM_ORG_MONTHLY_COST_LIMIT", 2.00)
LLM_ORG_DAILY_REQUESTS    = _env_int("LLM_ORG_DAILY_REQUESTS", 100)
LLM_ORG_DAILY_IN_TOKENS   = _env_int("LLM_ORG_DAILY_INPUT_TOKENS", 500000)
LLM_ORG_DAILY_OUT_TOKENS  = _env_int("LLM_ORG_DAILY_OUTPUT_TOKENS", 100000)

LLM_MAX_RETRIES       = _env_int("LLM_MAX_RETRIES", 1)
LLM_RETRY_BASE_SEC    = _env_float("LLM_RETRY_BASE_SECONDS", 2.0)
LLM_LOCK_TIMEOUT_SEC  = _env_int("LLM_LOCK_TIMEOUT_SEC", 30)
LLM_LOCK_WAIT_SEC     = _env_int("LLM_LOCK_WAIT_SEC", 3)

# MODEL_PRICING — per 1K tokens, configurable via env overrides.
# deepseek-reasoner output is $2.19/M → $0.00219/K (was incorrectly 2.19)
MODEL_PRICING: dict[str, dict[str, float]] = {
    "deepseek-v4-flash":{"input":float(os.getenv("LLM_PRICE_DS_V4_FLASH_IN","0.00014")),
                         "output":float(os.getenv("LLM_PRICE_DS_V4_FLASH_OUT","0.00028")),
                         "cache_hit":float(os.getenv("LLM_PRICE_DS_V4_FLASH_CACHE","0.0000028"))},
    "deepseek-v4-pro":  {"input":float(os.getenv("LLM_PRICE_DS_V4_PRO_IN","0.000435")),
                         "output":float(os.getenv("LLM_PRICE_DS_V4_PRO_OUT","0.00087")),
                         "cache_hit":float(os.getenv("LLM_PRICE_DS_V4_PRO_CACHE","0.000003625"))},
    "deepseek-chat":    {"input":float(os.getenv("LLM_PRICE_DS_CHAT_IN","0.00014")),
                         "output":float(os.getenv("LLM_PRICE_DS_CHAT_OUT","0.00028")),
                         "cache_hit":float(os.getenv("LLM_PRICE_DS_CHAT_CACHE","0.000014"))},
    "deepseek-reasoner":{"input":float(os.getenv("LLM_PRICE_DS_R1_IN","0.00055")),
                         "output":float(os.getenv("LLM_PRICE_DS_R1_OUT","0.00219")),
                         "cache_hit":float(os.getenv("LLM_PRICE_DS_R1_CACHE","0.00014"))},
    "gpt-4o":{"input":0.0025,"output":0.01,"cache_hit":0.00125},
    "gpt-4o-mini":{"input":0.00015,"output":0.0006,"cache_hit":0.000075},
    "default":{"input":0.0005,"output":0.001,"cache_hit":0.00005},
}

# ═══════════════════════════════════════════════════════════
# ASYNC REDIS (fail-closed)
# ═══════════════════════════════════════════════════════════

_redis: Any = None

def _get_redis():
    global _redis
    if _redis is not None: return _redis
    url = os.getenv("REDIS_URL", "")
    if not url: _redis = False; return False
    try:
        import redis.asyncio as aioredis
        _redis = aioredis.from_url(url, socket_timeout=3, socket_connect_timeout=2, retry_on_timeout=True, health_check_interval=30)
        return _redis
    except Exception: _redis = False; return False


def _reset_redis() -> None:
    """Drop a stale async Redis client so the next command reconnects cleanly."""
    global _redis
    _redis = None


# ═══════════════════════════════════════════════════════════
# ATOMIC REDIS LUA — reservation + release
# ═══════════════════════════════════════════════════════════

LUA_RESERVE = """
-- KEYS[1..7]: cost:global:daily, cost:global:monthly, cost:org:daily, cost:org:monthly,
--             req:org:daily, in:org:daily, out:org:daily
-- ARGV[1..7]: daily_cost_limit, monthly_cost_limit, org_daily_cost_limit, org_monthly_cost_limit,
--             req_limit, in_tok_limit, out_tok_limit
-- ARGV[8]: conservative cost to reserve
-- ARGV[9]: conservative input tokens to reserve
-- ARGV[10]: conservative output tokens to reserve
-- ARGV[11]: expire TTL seconds
-- Returns: {"ok"} or {"blocked", reason}
local gd  = tonumber(redis.call('GET', KEYS[1]) or '0')
local gm  = tonumber(redis.call('GET', KEYS[2]) or '0')
local od  = tonumber(redis.call('GET', KEYS[3]) or '0')
local om  = tonumber(redis.call('GET', KEYS[4]) or '0')
local rq  = tonumber(redis.call('GET', KEYS[5]) or '0')
local itk = tonumber(redis.call('GET', KEYS[6]) or '0')
local otk = tonumber(redis.call('GET', KEYS[7]) or '0')

local dc_lim  = tonumber(ARGV[1])
local mc_lim  = tonumber(ARGV[2])
local odc_lim = tonumber(ARGV[3])
local omc_lim = tonumber(ARGV[4])
local rq_lim  = tonumber(ARGV[5])
local itk_lim = tonumber(ARGV[6])
local otk_lim = tonumber(ARGV[7])
local res_cost = tonumber(ARGV[8])
local res_in   = tonumber(ARGV[9])
local res_out  = tonumber(ARGV[10])
local ttl      = tonumber(ARGV[11])

if gd + res_cost > dc_lim then  return {'blocked','global_daily'} end
if gm + res_cost > mc_lim then  return {'blocked','global_monthly'} end
if od + res_cost > odc_lim then return {'blocked','org_daily'} end
if om + res_cost > omc_lim then return {'blocked','org_monthly'} end
if rq + 1 > rq_lim then          return {'blocked','org_requests'} end
if itk + res_in > itk_lim then   return {'blocked','org_input_tokens'} end
if otk + res_out > otk_lim then  return {'blocked','org_output_tokens'} end

redis.call('INCRBYFLOAT', KEYS[1], res_cost)
redis.call('INCRBYFLOAT', KEYS[2], res_cost)
redis.call('INCRBYFLOAT', KEYS[3], res_cost)
redis.call('INCRBYFLOAT', KEYS[4], res_cost)
redis.call('INCR',        KEYS[5])
redis.call('INCRBY',      KEYS[6], res_in)
redis.call('INCRBY',      KEYS[7], res_out)
for _, k in ipairs(KEYS) do redis.call('EXPIRE', k, ttl) end
return {'ok'}
"""

LUA_REFUND = """
-- Refund over-reserved cost/tokens after actual usage known.
-- Subtracts (reserved - actual) from each counter, floor at 0.
-- KEYS same as reserve. ARGV[1]=reserved_cost, ARGV[2]=actual_cost,
-- ARGV[3]=reserved_in, ARGV[4]=actual_in, ARGV[5]=reserved_out, ARGV[6]=actual_out, ARGV[7]=ttl
local rc = tonumber(ARGV[1]); local ac = tonumber(ARGV[2])
local ri = tonumber(ARGV[3]); local ai = tonumber(ARGV[4])
local ro_ = tonumber(ARGV[5]); local ao = tonumber(ARGV[6])
local ttl = tonumber(ARGV[7])
local refund_c = math.max(0, rc - ac)
local refund_i = math.max(0, ri - ai)
local refund_o = math.max(0, ro_ - ao)

for _, k in ipairs({KEYS[1],KEYS[2],KEYS[3],KEYS[4]}) do
    redis.call('INCRBYFLOAT', k, -refund_c)
end
redis.call('INCRBY', KEYS[6], -refund_i)
redis.call('INCRBY', KEYS[7], -refund_o)
for _, k in ipairs(KEYS) do redis.call('EXPIRE', k, ttl) end
return {'ok'}
"""

LUA_SAFE_DEL = """
-- Atomically delete key only if its value matches token.
if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('DEL', KEYS[1])
else
    return 0
end
"""


# ═══════════════════════════════════════════════════════════
# GATEWAY CONFIG + RESPONSE
# ═══════════════════════════════════════════════════════════

@dataclass
class GatewayConfig:
    feature: str = "default"
    model: str | None = None
    max_tokens: int | None = None
    temperature: float = 0.3
    organization_id: int = 1
    bypass_cache: bool = False
    job_id: str | None = None
    tools: list[dict[str, Any]] | None = None
    tool_choice: str | dict[str, Any] | None = None

@dataclass
class GatewayToolCall:
    id: str
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)

@dataclass
class GatewayResponse:
    content: str = ""
    model: str = ""
    cached: bool = False
    deduped: bool = False
    usage: dict[str, int] = field(default_factory=dict)
    cost: float = 0.0
    latency_ms: float = 0.0
    tool_calls: list[GatewayToolCall] = field(default_factory=list)
    finish_reason: str = ""

    @property
    def has_tool_calls(self) -> bool: return bool(self.tool_calls)


# ═══════════════════════════════════════════════════════════
# GATEWAY CLASS
# ═══════════════════════════════════════════════════════════

class LLMGateway:
    """Centralized LLM gateway. Every call goes through budget, cache, dedupe, retry."""

    async def chat(
        self, messages: list[LLMMessage],
        config: GatewayConfig | None = None,
    ) -> GatewayResponse:
        cfg = config or GatewayConfig()
        f, org, t0 = cfg.feature, cfg.organization_id, time.monotonic()
        if not LLM_ENABLED:
            return GatewayResponse(content=_fallback(f), model="disabled")

        model = cfg.model or (LLM_PRO_MODEL if f in LLM_PRO_FEATURES else LLM_FLASH_MODEL)
        max_out = _reserve_output(f, cfg.max_tokens)
        input_cap = min(LLM_MAX_INPUT_TOKENS, FEATURE_INPUT_TOKENS.get(f, FEATURE_INPUT_TOKENS["default"]))
        messages = _truncate(messages, input_cap)
        cache_key = _cache_key(f, model, messages, cfg.temperature, max_out, cfg.tools or [], cfg.tool_choice)

        r = _get_redis()
        if r is False:
            return GatewayResponse(content=_fallback(f), model="redis_unavailable")

        # ── Cache hit (wrapped: Redis failure → fallback) ──
        if not cfg.bypass_cache:
            try:
                cv = await r.get(cache_key)
                if cv:
                    try:
                        data = json.loads(cv)
                        return GatewayResponse(
                            content=data.get("content",""), model=model, cached=True,
                            latency_ms=(time.monotonic()-t0)*1000,
                            tool_calls=[GatewayToolCall(**tc) for tc in data.get("tool_calls",[])],
                            finish_reason=data.get("finish_reason",""),
                        )
                    except Exception:
                        pass  # corrupt cache → fetch fresh
            except Exception:
                pass  # Redis read failed → fetch fresh (not fatal with lock below)

        # ── Distributed single-flight lock (wrapped) ──
        lk = f"llm:lock:{cache_key}"; lt = str(uuid.uuid4())
        try:
            acq = await r.set(lk, lt, nx=True, ex=LLM_LOCK_TIMEOUT_SEC)
        except Exception as exc:
            logger.warning("LLM Redis lock failed; reconnecting once: %s", str(exc)[:200])
            _reset_redis()
            r = _get_redis()
            if r is False:
                return GatewayResponse(content=_fallback(f), model="redis_unavailable")
            try:
                acq = await r.set(lk, lt, nx=True, ex=LLM_LOCK_TIMEOUT_SEC)
            except Exception as retry_exc:
                logger.error("LLM Redis lock unavailable after reconnect: %s", str(retry_exc)[:200])
                return GatewayResponse(content=_fallback(f), model="redis_unavailable")

        if not acq:
            for _ in range(int(LLM_LOCK_WAIT_SEC * 10)):
                await asyncio.sleep(0.1)
                try:
                    cv = await r.get(cache_key)
                    if cv:
                        try:
                            data = json.loads(cv)
                            return GatewayResponse(
                                content=data.get("content",""), model=model, cached=True, deduped=True,
                                latency_ms=(time.monotonic()-t0)*1000,
                                tool_calls=[GatewayToolCall(**tc) for tc in data.get("tool_calls",[])],
                                finish_reason=data.get("finish_reason",""),
                            )
                        except Exception:
                            break
                except Exception:
                    pass
            return GatewayResponse(content=_fallback(f), model="lock_timeout")

        # ── Atomic reservation ──
        try:
            res_in = _reserve_input(messages, f, input_cap)
            res_out = max_out
            p = MODEL_PRICING.get(model, MODEL_PRICING["default"])
            res_cost = (res_in/1000)*p["input"] + (res_out/1000)*p["output"]

            budget_keys = _budget_keys(org)
            try:
                res = await _eval_lua(r, LUA_RESERVE, len(budget_keys),
                    *budget_keys,
                    str(LLM_GLOBAL_DAILY_LIMIT), str(LLM_GLOBAL_MONTHLY_LIMIT),
                    str(LLM_ORG_DAILY_LIMIT), str(LLM_ORG_MONTHLY_LIMIT),
                    str(LLM_ORG_DAILY_REQUESTS), str(LLM_ORG_DAILY_IN_TOKENS), str(LLM_ORG_DAILY_OUT_TOKENS),
                    str(res_cost), str(res_in), str(res_out), "2592000")
            except Exception as exc:
                logger.error("LLM Redis budget reservation failed: %s", str(exc)[:200])
                return GatewayResponse(content=_fallback(f), model="redis_unavailable")

            if not res or res[0] != b'ok':
                return GatewayResponse(content=_fallback(f), model="budget_blocked")

            # ── Provider call ──
            try:
                resp, retries = await _call_llm(
                    messages, model, max_out, cfg.temperature,
                    tools=cfg.tools, tool_choice=cfg.tool_choice,
                )
            except Exception:
                await _refund_lua_safe(r, budget_keys, res_cost, 0, res_in, 0, res_out, 0)
                raise

            content = resp.content or ""
            raw_tool_calls = resp.tool_calls or []
            tool_calls = [GatewayToolCall(id=tc.id, name=tc.name, arguments=tc.arguments) for tc in raw_tool_calls]
            finish_reason = resp.finish_reason or ""
            u = resp.usage or {}
            it = u.get("prompt_tokens", 0) or u.get("input_tokens", 0)
            ot = u.get("completion_tokens", 0) or u.get("output_tokens", 0)
            ct = u.get("cached_tokens", 0) or u.get("cache_read_input_tokens", 0)

            # ── Refund over-reserved (actual ≤ reserved guaranteed by _reserve_input) ──
            actual_cost = _cost(model, it, ot, ct)
            if actual_cost < res_cost or it < res_in or ot < res_out:
                await _refund_lua_safe(r, budget_keys, res_cost, actual_cost, res_in, it, res_out, ot)

            # ── Cache ──
            try:
                ttl_val = FEATURE_CACHE_TTL.get(f, FEATURE_CACHE_TTL["default"])
                cv_payload = json.dumps({
                    "content": content,
                    "tool_calls": [{"id": tc.id, "name": tc.name, "arguments": tc.arguments} for tc in tool_calls],
                    "finish_reason": finish_reason,
                })
                await r.setex(cache_key, ttl_val, cv_payload)
            except Exception:
                pass

            # ── Log ──
            await _log(org, f, model, it, ot, ct, actual_cost,
                       (time.monotonic()-t0)*1000, cfg.job_id, True, retries)

            return GatewayResponse(
                content=content, model=model, usage=u, cost=actual_cost,
                latency_ms=(time.monotonic()-t0)*1000,
                tool_calls=tool_calls, finish_reason=finish_reason,
            )

        except Exception as e:
            await _log(org, f, model, 0, 0, 0, 0, 0, cfg.job_id, False, 0, str(e)[:200])
            logger.error("LLM gateway fail: feature=%s model=%s err=%s", f, model, str(e)[:200])
            return GatewayResponse(content=_fallback(f), model="error")
        finally:
            try:
                await _eval_lua(r, LUA_SAFE_DEL, 1, lk, lt)
            except Exception:
                pass

    async def chat_stream(
        self, messages: list[LLMMessage],
        config: GatewayConfig | None = None,
    ) -> AsyncIterator[str]:
        """Governed streaming — atomic reservation, truncation, budget, refund.
        Retry: only if zero tokens yielded (no duplicate output)."""
        cfg = config or GatewayConfig()
        f, org = cfg.feature, cfg.organization_id
        if not LLM_ENABLED:
            yield _fallback(f); return

        model = cfg.model or LLM_FLASH_MODEL
        max_out = _reserve_output(f, cfg.max_tokens)
        input_cap = min(LLM_MAX_INPUT_TOKENS, FEATURE_INPUT_TOKENS.get(f, FEATURE_INPUT_TOKENS["default"]))
        messages = _truncate(messages, input_cap)

        r = _get_redis()
        if r is False:
            yield _fallback(f); return

        res_in = _reserve_input(messages, f, input_cap)
        res_out = max_out
        p = MODEL_PRICING.get(model, MODEL_PRICING["default"])
        res_cost = (res_in/1000)*p["input"] + (res_out/1000)*p["output"]
        budget_keys = _budget_keys(org)
        reserved = False

        try:
            try:
                res = await _eval_lua(r, LUA_RESERVE, len(budget_keys),
                    *budget_keys,
                    str(LLM_GLOBAL_DAILY_LIMIT), str(LLM_GLOBAL_MONTHLY_LIMIT),
                    str(LLM_ORG_DAILY_LIMIT), str(LLM_ORG_MONTHLY_LIMIT),
                    str(LLM_ORG_DAILY_REQUESTS), str(LLM_ORG_DAILY_IN_TOKENS), str(LLM_ORG_DAILY_OUT_TOKENS),
                    str(res_cost), str(res_in), str(res_out), "2592000")
            except Exception:
                yield _fallback(f); return

            if not res or res[0] != b'ok':
                yield _fallback(f); return
            reserved = True

            collected = ""
            yielded_any = False
            async for token in _call_llm_stream(messages, model, max_out, cfg.temperature):
                collected += token
                yielded_any = True
                yield token

            # Account: use bounded reserve input (not feature constant)
            actual_out = len(collected) // 4
            actual_cost = _cost(model, res_in, actual_out, 0)
            if actual_cost < res_cost or actual_out < res_out:
                await _refund_lua_safe(r, budget_keys, res_cost, actual_cost, res_in, res_in, res_out, actual_out)

            await _log(org, f, model, res_in, actual_out, 0, actual_cost, 0, cfg.job_id, True, 0)

        except Exception as e:
            if reserved:
                await _refund_lua_safe(r, budget_keys, res_cost, 0, res_in, 0, res_out, 0)
            logger.error("LLM stream fail: feature=%s err=%s", f, str(e)[:200])


# ═══════════════════════════════════════════════════════════
# LUA HELPERS
# ═══════════════════════════════════════════════════════════

async def _eval_lua(r, script: str, num_keys: int, *args):
    """Execute a Lua script via EVAL. All args must be bytes or strings."""
    if not hasattr(r, '_lua_sha'):
        r._lua_sha = {}
    sha_key = script[:40]
    if sha_key not in r._lua_sha:
        r._lua_sha[sha_key] = await r.script_load(script)
    sha = r._lua_sha[sha_key]
    try:
        return await r.evalsha(sha, num_keys, *args)
    except Exception:
        # Script not found in Redis (e.g. after restart) — reload
        r._lua_sha[sha_key] = await r.script_load(script)
        return await r.evalsha(r._lua_sha[sha_key], num_keys, *args)


async def _refund_lua_safe(r, budget_keys: list, res_cost: float, actual_cost: float,
                       res_in: int, actual_in: int, res_out: int, actual_out: int) -> None:
    try:
        await _eval_lua(r, LUA_REFUND, len(budget_keys),
            *budget_keys,
            str(res_cost), str(actual_cost),
            str(res_in), str(actual_in),
            str(res_out), str(actual_out), "2592000")
    except Exception:
        logger.warning("Lua refund failed (non-fatal)")


def _budget_keys(org: int) -> list[str]:
    td = datetime.now(UTC).strftime("%Y-%m-%d")
    tm = datetime.now(UTC).strftime("%Y-%m")
    return [
        f"llm:cost:global:daily:{td}", f"llm:cost:global:monthly:{tm}",
        f"llm:cost:org:{org}:daily:{td}", f"llm:cost:org:{org}:monthly:{tm}",
        f"llm:req:org:{org}:daily:{td}",
        f"llm:in:org:{org}:daily:{td}", f"llm:out:org:{org}:daily:{td}",
    ]


# ═══════════════════════════════════════════════════════════
# TOKENS
# ═══════════════════════════════════════════════════════════

def _est_tok(msgs: list[LLMMessage]) -> int:
    return sum(len(m.content or "") for m in msgs) // 4

def _truncate(msgs: list[LLMMessage], max_t: int) -> list[LLMMessage]:
    if _est_tok(msgs) <= max_t:
        return msgs
    r: list[LLMMessage] = []
    s = next((m for m in msgs if m.role == "system"), None)
    if s:
        r.append(s)
    rem = max_t - _est_tok(r) - 200
    k: list[LLMMessage] = []
    for m in reversed(msgs):
        if m.role == "system":
            continue
        mt = _est_tok([m])
        if rem - mt >= 0:
            k.insert(0, m); rem -= mt
        else:
            k.insert(0, LLMMessage(role=m.role, content=m.content[:rem*4] + "... [truncated]"))
            break
    return r + k


# ═══════════════════════════════════════════════════════════
# CACHE KEY — full hash of messages + params + tools
# ═══════════════════════════════════════════════════════════

def _cache_key(feature: str, model: str, msgs: list[LLMMessage],
               temperature: float, max_tokens: int, tools: list[dict[str, Any]],
               tool_choice: str | dict[str, Any] | None) -> str:
    payload = {
        "feature": feature, "model": model,
        "temperature": temperature, "max_tokens": max_tokens,
        "messages": [{"role": m.role, "content": m.content or ""} for m in msgs],
        "tools": [json.dumps(t, sort_keys=True) for t in tools],
        "tool_choice": json.dumps(tool_choice, sort_keys=True) if tool_choice else None,
    }
    raw = json.dumps(payload, sort_keys=True)
    h = hashlib.sha256(raw.encode()).hexdigest()
    return f"llm:cache:{feature}:{model}:{h[:32]}"


# ═══════════════════════════════════════════════════════════
# PROVIDER CALLS (provider construction remains isolated in provider.py)
# ═══════════════════════════════════════════════════════════

RETRYABLE = {429, 500, 502, 503, 504}

async def _call_llm(
    msgs: list[LLMMessage], model: str, max_tok: int, temp: float,
    tools: list[dict[str, Any]] | None = None,
    tool_choice: str | dict[str, Any] | None = None,
) -> tuple[LLMResponse, int]:
    import random
    cfg = LLMConfig(
        provider="openai", model=model,
        api_key=os.getenv("DEEPSEEK_API_KEY",""),
        api_base="https://api.deepseek.com/v1",
        temperature=temp, max_tokens=max_tok,
    )
    prov = create_provider(cfg)
    last: Exception | None = None
    for att in range(LLM_MAX_RETRIES + 1):
        try:
            resp = await prov.chat(msgs, tools=tools, tool_choice=tool_choice)
            return resp, att
        except Exception as e:
            last = e
            st = _http_status(e)
            if st is not None and st not in RETRYABLE:
                raise
            if att >= LLM_MAX_RETRIES:
                raise
            await asyncio.sleep(LLM_RETRY_BASE_SEC * (2**att) + random.uniform(0, 1))
    raise last or RuntimeError("LLM exhausted")


async def _call_llm_stream(
    msgs: list[LLMMessage], model: str, max_tok: int, temp: float,
) -> AsyncIterator[str]:
    """Stream with retry only if zero chunks emitted (prevents duplicate output)."""
    import random
    cfg = LLMConfig(
        provider="openai", model=model,
        api_key=os.getenv("DEEPSEEK_API_KEY",""),
        api_base="https://api.deepseek.com/v1",
        temperature=temp, max_tokens=max_tok,
    )
    prov = create_provider(cfg)
    last: Exception | None = None
    for att in range(LLM_MAX_RETRIES + 1):
        yielded_any = False
        try:
            async for token in prov.chat_stream(msgs):
                yielded_any = True
                yield token
            return
        except Exception as e:
            last = e
            if yielded_any:
                raise  # don't retry — tokens were already emitted
            st = _http_status(e)
            if st is not None and st not in RETRYABLE:
                raise
            if att >= LLM_MAX_RETRIES:
                raise
            await asyncio.sleep(LLM_RETRY_BASE_SEC * (2**att) + random.uniform(0, 1))
    raise last or RuntimeError("LLM stream exhausted")


def _http_status(e: Exception) -> int | None:
    s = str(e)
    for c in ["429","500","502","503","504","401","403","400","404"]:
        if c in s:
            return int(c)
    return getattr(e, "status_code", None) or getattr(e, "http_status", None)


# ═══════════════════════════════════════════════════════════
# FALLBACK + COST + LOG
# ═══════════════════════════════════════════════════════════

def _fallback(feature: str) -> str:
    if "coaching" in feature:
        return json.dumps({"type":"observation","message":"Stay engaged with the prospect.","confidence":0.5})
    if "classification" in feature:
        return json.dumps({"result":"unknown","confidence":0.0})
    if "discovery" in feature:
        return json.dumps({"companies": [], "status": "llm_unavailable"})
    if "enrichment" in feature:
        return json.dumps({"summary":"LLM temporarily unavailable.","status":"pending"})
    if "proposal" in feature or "mcp" in feature:
        return json.dumps({"status":"llm_unavailable","message":"Service temporarily unavailable. Please try again shortly."})
    return json.dumps({"status":"llm_unavailable"})

def _cost(model: str, in_tok: int, out_tok: int, cache_tok: int) -> float:
    p = MODEL_PRICING.get(model, MODEL_PRICING["default"])
    return (in_tok/1000)*p["input"] + (out_tok/1000)*p["output"] + (cache_tok/1000)*p["cache_hit"]


async def _log(org: int, feature: str, model: str, in_tok: int, out_tok: int, cache_tok: int,
               cost: float, latency_ms: float, job_id: str | None, ok: bool, retries: int,
               error: str | None = None) -> None:
    try:
        asyncio.create_task(_write_log(org, feature, model, in_tok, out_tok, cache_tok,
                                        cost, latency_ms, job_id, ok, retries, error))
    except Exception:
        pass


async def _write_log(org: int, feature: str, model: str, in_tok: int, out_tok: int, cache_tok: int,
                     cost: float, latency_ms: float, job_id: str | None, ok: bool, retries: int,
                     error: str | None) -> None:
    try:
        from app.infrastructure.db.session import SessionLocal
        from app.infrastructure.db.models import AIRequestLog
        db = SessionLocal()
        try:
            le = AIRequestLog(
                organization_id=org,
                request_id=job_id or str(uuid.uuid4()),
                feature=feature[:50],
                provider="deepseek",
                model=model[:50],
                input_tokens=in_tok,
                output_tokens=out_tok,
                total_tokens=in_tok + out_tok + cache_tok,
                estimated_cost=cost,
                latency_ms=int(latency_ms),
                success=ok,
                error_message=error[:500] if error else None,
            )
            db.add(le)
            db.commit()
        finally:
            db.close()
    except Exception as e:
        logger.debug("Usage log write failed: %s", e)


# ═══════════════════════════════════════════════════════════
# SINGLETON + ADMIN
# ═══════════════════════════════════════════════════════════

_gateway: LLMGateway | None = None

def get_llm_gateway() -> LLMGateway:
    global _gateway
    if _gateway is None:
        _gateway = LLMGateway()
    return _gateway


async def get_budget_summary() -> dict:
    r = _get_redis()
    if not r:
        return {"status": "redis_unavailable"}
    td = datetime.now(UTC).strftime("%Y-%m-%d")
    tm = datetime.now(UTC).strftime("%Y-%m")
    d, m = await asyncio.gather(
        r.get(f"llm:cost:global:daily:{td}"),
        r.get(f"llm:cost:global:monthly:{tm}"),
    )
    dc = float(d or 0)
    mc = float(m or 0)
    return {
        "status": "ok",
        "llm_enabled": LLM_ENABLED,
        "daily_cost": round(dc, 4),
        "daily_limit": LLM_GLOBAL_DAILY_LIMIT,
        "daily_pct": round(dc / LLM_GLOBAL_DAILY_LIMIT * 100, 1) if LLM_GLOBAL_DAILY_LIMIT > 0 else 0,
        "monthly_cost": round(mc, 4),
        "monthly_limit": LLM_GLOBAL_MONTHLY_LIMIT,
        "monthly_pct": round(mc / LLM_GLOBAL_MONTHLY_LIMIT * 100, 1) if LLM_GLOBAL_MONTHLY_LIMIT > 0 else 0,
        "flash_model": LLM_FLASH_MODEL,
        "pro_model": LLM_PRO_MODEL,
    }
