"""Bounded retention for generated operational history.

This module intentionally knows nothing about CRM business entities. It only
prunes telemetry, worker runtime history, and already-processed delivery logs.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import and_, or_


def _days(name: str, default: int) -> int:
    return max(1, int(os.getenv(name, str(default))))


RETENTION_DAYS = {
    "worker_success": _days("CLEANUP_WORKER_SUCCESS_DAYS", 7),
    "worker_failure": _days("CLEANUP_WORKER_FAILURE_DAYS", 90),
    "outbox_completed": _days("CLEANUP_OUTBOX_COMPLETED_DAYS", 30),
    "outbox_failed": _days("CLEANUP_OUTBOX_FAILED_DAYS", 90),
    "webhook_processed": _days("CLEANUP_WEBHOOK_PROCESSED_DAYS", 180),
    "ai_requests": _days("CLEANUP_AI_REQUEST_DAYS", 180),
    "mcp_tools": _days("CLEANUP_MCP_TOOL_DAYS", 90),
}


def _prune(query: Any, *, dry_run: bool) -> int:
    count = query.count()
    if count and not dry_run:
        query.delete(synchronize_session=False)
    return count


def cleanup_operational_history(
    db: Any,
    *,
    now: datetime | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Prune generated history while preserving active work and CRM records."""
    from app.infrastructure.db.models import (
        AIRequestLog,
        MCPToolLog,
        OutboxEvent,
        ProviderWebhookEvent,
        WorkerFailure,
        WorkerJob,
        WorkerRun,
    )

    current = now or datetime.now(UTC)
    cutoff = {key: current - timedelta(days=days) for key, days in RETENTION_DAYS.items()}
    deleted: dict[str, int] = {}

    # Runs and failures are removed before jobs so their foreign keys never
    # interfere with pruning terminal jobs.
    deleted["worker_runs"] = _prune(
        db.query(WorkerRun).filter(or_(
            and_(WorkerRun.status == "succeeded", WorkerRun.finished_at < cutoff["worker_success"]),
            and_(WorkerRun.status == "failed", WorkerRun.finished_at < cutoff["worker_failure"]),
        )),
        dry_run=dry_run,
    )
    deleted["worker_failures"] = _prune(
        db.query(WorkerFailure).filter(WorkerFailure.created_at < cutoff["worker_failure"]),
        dry_run=dry_run,
    )
    deleted["worker_jobs"] = _prune(
        db.query(WorkerJob).filter(or_(
            and_(WorkerJob.status == "succeeded", WorkerJob.finished_at < cutoff["worker_success"]),
            and_(WorkerJob.status == "failed", WorkerJob.finished_at < cutoff["worker_failure"]),
        )),
        dry_run=dry_run,
    )
    deleted["outbox_events"] = _prune(
        db.query(OutboxEvent).filter(or_(
            and_(OutboxEvent.status == "completed", OutboxEvent.updated_at < cutoff["outbox_completed"]),
            and_(OutboxEvent.status == "failed", OutboxEvent.updated_at < cutoff["outbox_failed"]),
        )),
        dry_run=dry_run,
    )
    deleted["provider_webhook_events"] = _prune(
        db.query(ProviderWebhookEvent).filter(
            ProviderWebhookEvent.processing_status == "processed",
            ProviderWebhookEvent.created_at < cutoff["webhook_processed"],
        ),
        dry_run=dry_run,
    )
    deleted["ai_request_logs"] = _prune(
        db.query(AIRequestLog).filter(AIRequestLog.created_at < cutoff["ai_requests"]),
        dry_run=dry_run,
    )
    deleted["mcp_tool_logs"] = _prune(
        db.query(MCPToolLog).filter(MCPToolLog.created_at < cutoff["mcp_tools"]),
        dry_run=dry_run,
    )
    if dry_run:
        db.rollback()
    else:
        db.commit()

    return {
        "dry_run": dry_run,
        "deleted": deleted,
        "total_deleted": sum(deleted.values()),
        "retention_days": dict(RETENTION_DAYS),
    }
