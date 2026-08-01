"""
Telemetry Service.

Async, non-blocking observability layer. Logs every AI request,
MCP tool call, and computes daily metrics. Failures here never
affect the user experience.

Architecture:
    AI Request → TelemetryService.log_request() [async, fire-and-forget]
    MCP Tool   → TelemetryService.log_tool()     [async, fire-and-forget]
"""

import datetime
import threading
import time
import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.infrastructure.db.models import AIRequestLog, DailyMetrics, MCPToolLog


class TelemetryService:
    """Async telemetry — never blocks the caller."""

    def __init__(self, session_factory) -> None:
        self._session_factory = session_factory
        self._executor = _BackgroundExecutor()

    def log_request(
        self,
        org_id: int,
        feature: str,
        provider: str,
        model: str,
        prompt_name: str = "",
        input_tokens: int = 0,
        output_tokens: int = 0,
        latency_ms: int = 0,
        success: bool = True,
        fallback_used: bool = False,
        error_message: str = "",
        parse_success: bool | None = None,
        parse_method: str = "",
    ) -> None:
        """Log an AI request asynchronously."""
        total_tokens = input_tokens + output_tokens
        # DeepSeek pricing estimate
        cost = (input_tokens / 1_000_000 * 0.14) + (output_tokens / 1_000_000 * 0.28)

        def _write():
            try:
                session = self._session_factory()
                log = AIRequestLog(
                    organization_id=org_id,
                    request_id=str(uuid.uuid4())[:12],
                    feature=feature,
                    provider=provider,
                    model=model,
                    prompt_name=prompt_name,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=total_tokens,
                    estimated_cost=round(cost, 6),
                    latency_ms=latency_ms,
                    success=success,
                    fallback_used=fallback_used,
                    error_message=error_message[:500] if error_message else None,
                    parse_success=parse_success,
                    parse_method=parse_method,
                )
                session.add(log)
                session.commit()
                session.close()
            except Exception:
                pass  # Telemetry failure must never propagate

        self._executor.submit(_write)

    def log_tool(
        self,
        org_id: int,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
        execution_time_ms: int = 0,
        success: bool = True,
        error_message: str = "",
    ) -> None:
        """Log an MCP tool execution asynchronously."""
        import json
        args_str = json.dumps(arguments, default=str)[:2000] if arguments else None

        def _write():
            try:
                session = self._session_factory()
                log = MCPToolLog(
                    organization_id=org_id,
                    tool_name=tool_name,
                    arguments=args_str,
                    execution_time_ms=execution_time_ms,
                    success=success,
                    error_message=error_message[:500] if error_message else None,
                )
                session.add(log)
                session.commit()
                session.close()
            except Exception:
                pass

        self._executor.submit(_write)

    def get_stats(self, org_id: int, days: int = 7) -> dict[str, Any]:
        """Get telemetry stats for dashboard display."""
        session = self._session_factory()
        try:
            cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)

            total_requests = session.execute(
                select(func.count(AIRequestLog.id)).where(
                    AIRequestLog.organization_id == org_id,
                    AIRequestLog.created_at >= cutoff,
                )
            ).scalar_one()

            total_tokens = session.execute(
                select(func.sum(AIRequestLog.total_tokens)).where(
                    AIRequestLog.organization_id == org_id,
                    AIRequestLog.created_at >= cutoff,
                )
            ).scalar_one() or 0

            total_cost = session.execute(
                select(func.sum(AIRequestLog.estimated_cost)).where(
                    AIRequestLog.organization_id == org_id,
                    AIRequestLog.created_at >= cutoff,
                )
            ).scalar_one() or 0

            success_count = session.execute(
                select(func.count(AIRequestLog.id)).where(
                    AIRequestLog.organization_id == org_id,
                    AIRequestLog.created_at >= cutoff,
                    AIRequestLog.success == True,
                )
            ).scalar_one()

            fallback_count = session.execute(
                select(func.count(AIRequestLog.id)).where(
                    AIRequestLog.organization_id == org_id,
                    AIRequestLog.created_at >= cutoff,
                    AIRequestLog.fallback_used == True,
                )
            ).scalar_one()

            avg_latency = session.execute(
                select(func.avg(AIRequestLog.latency_ms)).where(
                    AIRequestLog.organization_id == org_id,
                    AIRequestLog.created_at >= cutoff,
                )
            ).scalar_one() or 0

            by_feature = session.execute(
                select(AIRequestLog.feature, func.count(AIRequestLog.id))
                .where(AIRequestLog.organization_id == org_id, AIRequestLog.created_at >= cutoff)
                .group_by(AIRequestLog.feature)
            ).all()

            by_provider = session.execute(
                select(AIRequestLog.provider, func.count(AIRequestLog.id), func.sum(AIRequestLog.estimated_cost))
                .where(AIRequestLog.organization_id == org_id, AIRequestLog.created_at >= cutoff)
                .group_by(AIRequestLog.provider)
            ).all()

            tool_usage = session.execute(
                select(MCPToolLog.tool_name, func.count(MCPToolLog.id))
                .where(MCPToolLog.organization_id == org_id, MCPToolLog.created_at >= cutoff)
                .group_by(MCPToolLog.tool_name)
                .order_by(func.count(MCPToolLog.id).desc())
                .limit(10)
            ).all()

            health_score = self._compute_health(success_count, total_requests, fallback_count, avg_latency)

            return {
                "period_days": days,
                "total_requests": total_requests,
                "total_tokens": total_tokens,
                "total_cost": round(float(total_cost), 4),
                "avg_latency_ms": int(avg_latency),
                "success_count": success_count,
                "fallback_count": fallback_count,
                "success_rate": round(success_count / max(total_requests, 1) * 100, 1),
                "fallback_rate": round(fallback_count / max(total_requests, 1) * 100, 1),
                "health_score": health_score,
                "by_feature": [{"feature": f, "count": c} for f, c in by_feature],
                "by_provider": [{"provider": p, "count": c, "cost": round(float(co or 0), 4)} for p, c, co in by_provider],
                "top_tools": [{"tool": t, "count": c} for t, c in tool_usage],
            }
        finally:
            session.close()

    def _compute_health(self, success_count: int, total: int, fallback: int, avg_latency: float) -> int:
        if total == 0:
            return 100
        success_score = min(40, int(success_count / total * 40))
        fallback_penalty = min(20, int(fallback / max(total, 1) * 100))
        latency_score = 20 if avg_latency < 3000 else 15 if avg_latency < 5000 else 10 if avg_latency < 8000 else 5
        return min(100, success_score + latency_score + 20 - fallback_penalty + 10)


class _BackgroundExecutor:
    """Simple background thread executor for fire-and-forget telemetry."""

    def __init__(self):
        self._threads: list[threading.Thread] = []

    def submit(self, fn):
        t = threading.Thread(target=fn, daemon=True)
        t.start()
        self._threads.append(t)
        # Clean up finished threads
        self._threads = [t for t in self._threads if t.is_alive()]


# ── Global instance ──

_telemetry: TelemetryService | None = None


def get_telemetry() -> TelemetryService:
    global _telemetry
    if _telemetry is None:
        from app.infrastructure.db.session import SessionLocal
        _telemetry = TelemetryService(SessionLocal)
    return _telemetry
