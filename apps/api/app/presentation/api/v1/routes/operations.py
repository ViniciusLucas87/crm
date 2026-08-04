"""Operational status - protected monitoring dashboard.

Returns safe summaries without secrets or PII.  Uses real runtime
checks for DB/Redis connectivity and worker heartbeat via Celery
control.inspect().ping().  Backup freshness is checked from the
S3/R2 .last_backup marker using configured settings (no secrets
in responses).  Overall status degrades when any check fails or
is unavailable.
"""

import json as _json
import os
from datetime import datetime, UTC, timedelta

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.infrastructure.auth.clerk import AuthContext, require_permission
from app.infrastructure.db.session import get_db_session
from app.infrastructure.db.models import OutboxEvent

router = APIRouter()

STATUS_THRESHOLD_FAILED_OUTBOX = 100
BACKUP_STALE_HOURS = 25  # backups older than this are stale
BACKUP_CHECK_TIMEOUT = 3  # seconds for S3/R2 fetch


class StatusResponse(BaseModel):
    status: str
    build_id: str
    git_commit: str
    environment: str
    db_status: str
    db_latency_ms: float
    redis_status: str
    outbox_pending: int
    outbox_failed: int
    backups_ok: bool | None = None
    backup_last_ts: str | None = None
    worker_status: str = "unknown"
    worker_heartbeat_ms: float | None = None
    generated_at: str


def _ping_worker() -> tuple[str, float | None]:
    """Ping Celery workers via control.inspect().ping() with strict timeout.
    Returns (status, latency_ms).  Requires at least one worker reply for 'running'."""
    try:
        from celery import Celery
        redis_password = os.getenv("REDIS_PASSWORD", "redis_dev")
        broker = os.getenv("REDIS_URL", f"redis://:{redis_password}@redis:6379/0")
        celery = Celery("pns_worker", broker=broker)
        t0 = datetime.now(UTC)
        insp = celery.control.inspect(timeout=2)
        pings = insp.ping()
        latency = (datetime.now(UTC) - t0).total_seconds() * 1000
        if pings and len(pings) > 0:
            # At least one worker responded
            return ("running", round(latency, 1))
        # Worker process exists but no reply
        return ("stale", None)
    except Exception:
        return ("unknown", None)


def _check_backup_freshness() -> tuple[bool | None, str | None]:
    """Check backup freshness from S3/R2 .last_backup marker.
    Returns (backups_ok, last_ts_iso).
      - True  = fresh (within BACKUP_STALE_HOURS)
      - False = stale (marker exists but too old)
      - None  = unavailable (bucket unreachable or marker missing)
    No AWS secrets appear in responses."""
    bucket = os.getenv("BACKUP_S3_BUCKET")
    endpoint = os.getenv("BACKUP_S3_ENDPOINT")
    region = os.getenv("BACKUP_S3_REGION", "auto")
    if not bucket or not endpoint:
        return (None, None)

    try:
        import boto3
        from botocore.config import Config as BotoConfig
        from botocore.exceptions import BotoCoreError, ClientError

        s3 = boto3.client(
            "s3",
            endpoint_url=endpoint,
            region_name=region,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", ""),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", ""),
            config=BotoConfig(
                connect_timeout=BACKUP_CHECK_TIMEOUT,
                read_timeout=BACKUP_CHECK_TIMEOUT,
                retries={"max_attempts": 0},
            ),
        )
        resp = s3.get_object(Bucket=bucket, Key="backups/.last_backup")
        ts_raw = resp["Body"].read().decode("utf-8").strip()
        if not ts_raw:
            return (None, None)
        last_ts = datetime.fromisoformat(ts_raw).replace(tzinfo=UTC)
        age = datetime.now(UTC) - last_ts
        fresh = age < timedelta(hours=BACKUP_STALE_HOURS)
        return (fresh, last_ts.isoformat())
    except (BotoCoreError, ClientError, ValueError, OSError):
        return (None, None)
    except Exception:
        return (None, None)


@router.get("/status", response_model=StatusResponse)
def operational_status(
    context: AuthContext = Depends(require_permission("dashboard:read")),
    db: Session = Depends(get_db_session),
) -> StatusResponse:
    now = datetime.now(UTC)

    db_ok = False
    db_latency = -1.0
    try:
        t0 = datetime.now(UTC)
        db.execute(text("SELECT 1"))
        db_latency = (datetime.now(UTC) - t0).total_seconds() * 1000
        db_ok = True
    except Exception:
        pass

    redis_ok = False
    try:
        import redis as _redis
        r = _redis.from_url(
            os.getenv("REDIS_URL", "redis://redis:6379/0"),
            socket_timeout=2, socket_connect_timeout=2,
        )
        redis_ok = r.ping()
        r.close()
    except Exception:
        pass

    outbox_pending = db.query(func.count(OutboxEvent.id)).filter(
        OutboxEvent.status == "pending"
    ).scalar() or 0
    outbox_failed = db.query(func.count(OutboxEvent.id)).filter(
        OutboxEvent.status == "failed"
    ).scalar() or 0

    worker_status, worker_heartbeat_ms = _ping_worker()
    backups_ok, backup_last_ts = _check_backup_freshness()

    build_id = os.getenv("BUILD_ID", "unknown")
    git_commit = os.getenv("GIT_COMMIT", "unknown")
    environment = os.getenv("PNS_ENV", "development")
    try:
        with open("/app/version.json") as f:
            v = _json.load(f)
        build_id = v.get("image_version", build_id)
        git_commit = v.get("git_commit", git_commit)
    except Exception:
        pass

    # --- Degradation logic ---
    issues = 0
    if not db_ok:
        issues += 1
    if not redis_ok:
        issues += 1
    if outbox_failed >= STATUS_THRESHOLD_FAILED_OUTBOX:
        issues += 1
    if backups_ok is False:
        issues += 1
    # Unknown backup status is not healthy because it cannot be verified.
    if backups_ok is None:
        issues += 1
    # Unknown or stale worker is not healthy
    if worker_status in ("unknown", "stale"):
        issues += 1

    if issues == 0:
        overall = "healthy"
    elif db_ok and issues <= 2:
        overall = "degraded"
    else:
        overall = "unhealthy"

    return StatusResponse(
        status=overall,
        build_id=build_id,
        git_commit=git_commit,
        environment=environment,
        db_status="connected" if db_ok else "disconnected",
        db_latency_ms=round(db_latency, 1),
        redis_status="connected" if redis_ok else "disconnected",
        outbox_pending=outbox_pending,
        outbox_failed=outbox_failed,
        backups_ok=backups_ok,
        backup_last_ts=backup_last_ts,
        worker_status=worker_status,
        worker_heartbeat_ms=worker_heartbeat_ms,
        generated_at=now.isoformat(),
    )
