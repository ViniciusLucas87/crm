"""
Autonomous Knowledge Workers — Management API

Endpoints:
  GET  /workers              — list all workers with status
  GET  /workers/health       — health check for all workers
  GET  /workers/metrics      — aggregate metrics
  POST /workers/{name}/start — start a worker
  POST /workers/{name}/stop  — stop a worker
  POST /workers/{name}/pause — pause a worker
  POST /workers/{name}/resume— resume a worker
  POST /workers/{name}/restart — restart a worker
  GET  /workers/dead-letter  — dead letter queue
  POST /workers/dead-letter/{index}/replay — replay dead letter
"""

import os
import logging

from celery import Celery
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.auth.clerk import AuthContext, require_permission
from app.infrastructure.db.models import WorkerDeadLetter, WorkerFailure, WorkerJob, WorkerMetricSnapshot, WorkerSchedule
from app.infrastructure.db.session import get_db_session

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_manager():
    """Get the global WorkerManager instance."""
    from app.main import worker_manager
    if worker_manager is None:
        raise HTTPException(status_code=503, detail="Worker manager not initialized")
    return worker_manager


def _get_celery() -> Celery:
    redis_password = os.getenv("REDIS_PASSWORD", "redis_dev")
    return Celery("pns_worker", broker=f"redis://:{redis_password}@redis:6379/0")


@router.get("")
def list_workers(
    auth: AuthContext = Depends(require_permission("read:companies")),
    session: Session = Depends(get_db_session),
):
    """List all registered workers with status and configuration."""
    mgr = _get_manager()
    schedules = {
        row.worker_name: row
        for row in session.execute(select(WorkerSchedule)).scalars().all()
    }
    snapshots = {
        row.worker_name: row
        for row in session.execute(select(WorkerMetricSnapshot)).scalars().all()
    }
    return {
        "workers": [
            {
                "name": w.config.name,
                "description": w.config.description,
                "status": "running" if schedules.get(w.config.name, None) is None or schedules[w.config.name].enabled else "paused",
                "priority": w.config.priority.name,
                "schedule": schedules.get(w.config.name).schedule_type if schedules.get(w.config.name) else w.config.schedule.value,
                "concurrency": w.config.concurrency,
                "healthy": snapshots.get(w.config.name).last_heartbeat_at is not None if snapshots.get(w.config.name) else True,
                "capabilities": w.config.capabilities,
                "supported_events": w.config.supported_events[:5],
                "worker_id": w.worker_id,
                "queue": schedules.get(w.config.name).queue_name if schedules.get(w.config.name) else "normal",
                "heartbeat": snapshots.get(w.config.name).last_heartbeat_at.isoformat() if snapshots.get(w.config.name) and snapshots.get(w.config.name).last_heartbeat_at else None,
                "current_job_id": snapshots.get(w.config.name).current_job_id if snapshots.get(w.config.name) else None,
            }
            for w in mgr._workers.values()
        ],
        "total": len(mgr._workers),
    }


@router.get("/health")
async def worker_health(
    auth: AuthContext = Depends(require_permission("read:companies")),
    session: Session = Depends(get_db_session),
):
    """Health check for all workers."""
    mgr = _get_manager()
    import asyncio
    rows = session.execute(select(WorkerMetricSnapshot)).scalars().all()
    result = {
        row.worker_name: {
            "worker": row.worker_name,
            "status": "running",
            "healthy": row.last_heartbeat_at is not None,
            "last_heartbeat": row.last_heartbeat_at.isoformat() if row.last_heartbeat_at else None,
            "current_job_id": row.current_job_id,
            "queue_depth": row.queue_depth,
            "last_error": row.last_error,
        }
        for row in rows
    }
    return {"manager_running": mgr._running, "workers": result}


@router.get("/metrics")
def worker_metrics(
    auth: AuthContext = Depends(require_permission("read:companies")),
    session: Session = Depends(get_db_session),
):
    """Aggregate metrics across all workers."""
    rows = session.execute(select(WorkerMetricSnapshot)).scalars().all()
    failures = session.execute(select(WorkerFailure)).scalars().all()
    dead_letters = session.execute(select(WorkerDeadLetter)).scalars().all()
    aggregate = {
        "jobs_processed": sum(row.jobs_processed for row in rows),
        "jobs_succeeded": sum(row.jobs_succeeded for row in rows),
        "jobs_failed": sum(row.jobs_failed for row in rows),
        "retries": sum(row.retries for row in rows),
        "facts_created": sum(row.facts_created for row in rows),
        "facts_verified": sum(row.facts_verified for row in rows),
        "relationships_created": sum(row.relationships_created for row in rows),
        "insights_generated": sum(row.insights_generated for row in rows),
        "entities_enriched": sum(row.entities_enriched for row in rows),
        "queue_depth": sum(row.queue_depth for row in rows),
        "failures": len(failures),
    }
    return {
        "aggregate": aggregate,
        "workers": {
            row.worker_name: {
                "status": "running",
                "healthy": row.last_heartbeat_at is not None,
                "jobs_processed": row.jobs_processed,
                "jobs_succeeded": row.jobs_succeeded,
                "jobs_failed": row.jobs_failed,
                "retries": row.retries,
                "avg_runtime_ms": row.avg_runtime_ms,
                "last_run": row.last_run_at.isoformat() if row.last_run_at else None,
                "last_error": row.last_error,
                "facts_created": row.facts_created,
                "facts_verified": row.facts_verified,
                "relationships_created": row.relationships_created,
                "insights_generated": row.insights_generated,
                "entities_enriched": row.entities_enriched,
                "queue_depth": row.queue_depth,
                "heartbeat": row.last_heartbeat_at.isoformat() if row.last_heartbeat_at else None,
                "current_job_id": row.current_job_id,
            }
            for row in rows
        },
        "dead_letter_count": len(dead_letters),
        "manager_running": True,
    }


@router.post("/{name}/start")
def start_worker(name: str, auth: AuthContext = Depends(require_permission("write:companies")), session: Session = Depends(get_db_session)):
    """Start a specific worker."""
    mgr = _get_manager()
    worker = mgr._workers.get(name)
    if not worker:
        raise HTTPException(status_code=404, detail=f"Worker '{name}' not found")
    schedule = session.execute(select(WorkerSchedule).where(WorkerSchedule.worker_name == name)).scalar_one_or_none()
    if schedule:
        schedule.enabled = True
        session.commit()
    celery = _get_celery()
    queue = schedule.queue_name if schedule else "normal"
    result = celery.send_task(f"workers.{name}", queue=queue)
    return {"status": "enqueued", "worker": name, "task_id": result.id}


@router.post("/{name}/stop")
def stop_worker(name: str, auth: AuthContext = Depends(require_permission("write:companies")), session: Session = Depends(get_db_session)):
    """Stop a specific worker."""
    mgr = _get_manager()
    if name not in mgr._workers:
        raise HTTPException(status_code=404, detail=f"Worker '{name}' not found")
    schedule = session.execute(select(WorkerSchedule).where(WorkerSchedule.worker_name == name)).scalar_one_or_none()
    if schedule:
        schedule.enabled = False
        session.commit()
    return {"status": "stopping", "worker": name}


@router.post("/{name}/pause")
def pause_worker(name: str, auth: AuthContext = Depends(require_permission("write:companies")), session: Session = Depends(get_db_session)):
    mgr = _get_manager()
    if name not in mgr._workers:
        raise HTTPException(status_code=404, detail=f"Worker '{name}' not found")
    schedule = session.execute(select(WorkerSchedule).where(WorkerSchedule.worker_name == name)).scalar_one_or_none()
    if schedule:
        schedule.enabled = False
        session.commit()
    return {"status": "pausing", "worker": name}


@router.post("/{name}/resume")
def resume_worker(name: str, auth: AuthContext = Depends(require_permission("write:companies")), session: Session = Depends(get_db_session)):
    mgr = _get_manager()
    if name not in mgr._workers:
        raise HTTPException(status_code=404, detail=f"Worker '{name}' not found")
    schedule = session.execute(select(WorkerSchedule).where(WorkerSchedule.worker_name == name)).scalar_one_or_none()
    if schedule:
        schedule.enabled = True
        session.commit()
    return {"status": "resuming", "worker": name}


@router.post("/{name}/restart")
def restart_worker(name: str, auth: AuthContext = Depends(require_permission("write:companies")), session: Session = Depends(get_db_session)):
    """Restart a specific worker."""
    mgr = _get_manager()
    if name not in mgr._workers:
        raise HTTPException(status_code=404, detail=f"Worker '{name}' not found")
    schedule = session.execute(select(WorkerSchedule).where(WorkerSchedule.worker_name == name)).scalar_one_or_none()
    if schedule:
        schedule.enabled = True
        session.commit()
    celery = _get_celery()
    queue = schedule.queue_name if schedule else "normal"
    result = celery.send_task(f"workers.{name}", queue=queue)
    return {"status": "restarting", "worker": name, "task_id": result.id}


@router.get("/dead-letter")
def dead_letter_queue(
    auth: AuthContext = Depends(require_permission("read:companies")),
    session: Session = Depends(get_db_session),
):
    """View the dead letter queue."""
    rows = session.execute(select(WorkerDeadLetter).order_by(WorkerDeadLetter.failed_at.desc())).scalars().all()
    return {"items": [
        {
            "id": row.id,
            "worker": row.worker_name,
            "task_id": row.task_id,
            "queue": row.queue_name,
            "payload_json": row.payload_json,
            "error_message": row.error_message,
            "status": row.status,
            "failed_at": row.failed_at.isoformat() if row.failed_at else None,
            "replayed_at": row.replayed_at.isoformat() if row.replayed_at else None,
        }
        for row in rows
    ]}


@router.post("/dead-letter/{index}/replay")
def replay_dead_letter(index: int, auth: AuthContext = Depends(require_permission("write:companies")), session: Session = Depends(get_db_session)):
    """Replay a dead letter item."""
    row = session.get(WorkerDeadLetter, index)
    if row is None:
        raise HTTPException(status_code=404, detail=f"No dead letter with id {index}")
    celery = _get_celery()
    result = celery.send_task(f"workers.{row.worker_name}", kwargs={"payload": row.payload_json or {}, "task_id": row.task_id}, queue=row.queue_name)
    row.status = "replayed"
    from datetime import UTC, datetime
    row.replayed_at = datetime.now(UTC)
    session.commit()
    return {"status": "replayed", "id": row.id, "task_id": result.id}
