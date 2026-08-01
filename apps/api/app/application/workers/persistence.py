import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.db.models import (
    WorkerDeadLetter,
    WorkerFailure,
    WorkerJob,
    WorkerMetricSnapshot,
    WorkerRun,
    WorkerSchedule,
)


def ensure_worker_schedule(
    session: Session,
    *,
    worker_name: str,
    queue_name: str,
    schedule_type: str,
    cron_expr: str | None = None,
) -> WorkerSchedule:
    schedule = session.execute(
        select(WorkerSchedule).where(WorkerSchedule.worker_name == worker_name)
    ).scalar_one_or_none()
    if schedule is None:
        schedule = WorkerSchedule(
            worker_name=worker_name,
            queue_name=queue_name,
            schedule_type=schedule_type,
            cron_expr=cron_expr,
            enabled=True,
        )
        session.add(schedule)
    else:
        schedule.queue_name = queue_name
        schedule.schedule_type = schedule_type
        schedule.cron_expr = cron_expr
    session.commit()
    session.refresh(schedule)
    return schedule


def create_worker_job(
    session: Session,
    *,
    worker_name: str,
    queue_name: str,
    trigger_type: str,
    event_type: str | None = None,
    entity_type: str | None = None,
    entity_id: int | None = None,
    payload: dict[str, Any] | None = None,
    priority: str = "normal",
    task_id: str | None = None,
) -> WorkerJob:
    job = WorkerJob(
        worker_name=worker_name,
        task_id=task_id,
        queue_name=queue_name,
        trigger_type=trigger_type,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        payload_json=json.dumps(payload or {}),
        priority=priority,
        status="queued",
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def start_worker_run(session: Session, *, worker_name: str, task_id: str | None, job_id: int | None) -> WorkerRun:
    run = WorkerRun(
        worker_name=worker_name,
        task_id=task_id,
        job_id=job_id,
        status="running",
        started_at=datetime.now(UTC),
        heartbeat_at=datetime.now(UTC),
    )
    session.add(run)
    session.commit()
    session.refresh(run)
    _update_metric_snapshot(
        session,
        worker_name=worker_name,
        current_job_id=job_id,
        last_heartbeat_at=run.heartbeat_at,
    )
    return run


def heartbeat_worker_run(session: Session, *, run_id: int) -> None:
    run = session.get(WorkerRun, run_id)
    if run is None:
        return
    run.heartbeat_at = datetime.now(UTC)
    session.commit()
    _update_metric_snapshot(
        session,
        worker_name=run.worker_name,
        current_job_id=run.job_id,
        last_heartbeat_at=run.heartbeat_at,
    )


def finish_worker_run(
    session: Session,
    *,
    run_id: int,
    success: bool,
    result: dict[str, Any] | None = None,
    error_message: str | None = None,
) -> None:
    run = session.get(WorkerRun, run_id)
    if run is None:
        return
    now = datetime.now(UTC)
    run.finished_at = now
    run.status = "succeeded" if success else "failed"
    run.error_message = error_message
    run.result_json = json.dumps(result or {})
    run.runtime_ms = int((now - run.started_at).total_seconds() * 1000)

    if run.job_id:
        job = session.get(WorkerJob, run.job_id)
        if job is not None:
            job.status = run.status
            job.started_at = run.started_at
            job.finished_at = now

    session.commit()

    metrics = result or {}
    _update_metric_snapshot(
        session,
        worker_name=run.worker_name,
        current_job_id=None,
        jobs_processed_delta=1,
        jobs_succeeded_delta=1 if success else 0,
        jobs_failed_delta=0 if success else 1,
        avg_runtime_ms=run.runtime_ms,
        facts_created_delta=int(metrics.get("facts_created", 0)),
        facts_verified_delta=int(metrics.get("facts_verified", 0)),
        relationships_created_delta=int(metrics.get("relationships_created", 0)),
        insights_generated_delta=int(metrics.get("insights_generated", 0)),
        entities_enriched_delta=int(metrics.get("entities_enriched", 0)),
        last_run_at=now,
        last_error=error_message,
    )


def record_worker_failure(
    session: Session,
    *,
    worker_name: str,
    task_id: str | None,
    job_id: int | None,
    error_type: str | None,
    error_message: str,
    traceback_text: str | None = None,
    retry_count: int = 0,
    payload: dict[str, Any] | None = None,
    queue_name: str = "normal",
) -> None:
    failure = WorkerFailure(
        worker_name=worker_name,
        task_id=task_id,
        job_id=job_id,
        error_type=error_type,
        error_message=error_message,
        traceback_text=traceback_text,
        retry_count=retry_count,
    )
    session.add(failure)
    session.flush()

    if retry_count >= 3:
        dead_letter = WorkerDeadLetter(
            worker_name=worker_name,
            task_id=task_id,
            queue_name=queue_name,
            payload_json=json.dumps(payload or {}),
            error_message=error_message,
            status="queued",
        )
        session.add(dead_letter)

    session.commit()
    _update_metric_snapshot(
        session,
        worker_name=worker_name,
        retries_delta=max(retry_count, 1),
        last_error=error_message,
    )


def get_metric_snapshot(session: Session, worker_name: str) -> WorkerMetricSnapshot | None:
    return session.execute(
        select(WorkerMetricSnapshot).where(WorkerMetricSnapshot.worker_name == worker_name)
    ).scalar_one_or_none()


def _update_metric_snapshot(
    session: Session,
    *,
    worker_name: str,
    current_job_id: int | None = None,
    jobs_processed_delta: int = 0,
    jobs_succeeded_delta: int = 0,
    jobs_failed_delta: int = 0,
    retries_delta: int = 0,
    avg_runtime_ms: int | None = None,
    facts_created_delta: int = 0,
    facts_verified_delta: int = 0,
    relationships_created_delta: int = 0,
    insights_generated_delta: int = 0,
    entities_enriched_delta: int = 0,
    queue_depth: int | None = None,
    last_heartbeat_at: datetime | None = None,
    last_run_at: datetime | None = None,
    last_error: str | None = None,
) -> WorkerMetricSnapshot:
    snap = session.execute(
        select(WorkerMetricSnapshot).where(WorkerMetricSnapshot.worker_name == worker_name)
    ).scalar_one_or_none()
    if snap is None:
        snap = WorkerMetricSnapshot(worker_name=worker_name)
        session.add(snap)
        session.flush()

    snap.current_job_id = current_job_id
    snap.jobs_processed += jobs_processed_delta
    snap.jobs_succeeded += jobs_succeeded_delta
    snap.jobs_failed += jobs_failed_delta
    snap.retries += retries_delta
    snap.facts_created += facts_created_delta
    snap.facts_verified += facts_verified_delta
    snap.relationships_created += relationships_created_delta
    snap.insights_generated += insights_generated_delta
    snap.entities_enriched += entities_enriched_delta
    if avg_runtime_ms is not None:
        if snap.jobs_succeeded > 0:
            snap.avg_runtime_ms = int(
                ((snap.avg_runtime_ms * max(snap.jobs_succeeded - jobs_succeeded_delta, 0)) + avg_runtime_ms)
                / max(snap.jobs_succeeded, 1)
            )
        else:
            snap.avg_runtime_ms = avg_runtime_ms
    if queue_depth is not None:
        snap.queue_depth = queue_depth
    if last_heartbeat_at is not None:
        snap.last_heartbeat_at = last_heartbeat_at
    if last_run_at is not None:
        snap.last_run_at = last_run_at
    if last_error is not None:
        snap.last_error = last_error
    session.commit()
    session.refresh(snap)
    return snap