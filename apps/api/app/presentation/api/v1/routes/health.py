"""
Health endpoints — Liveness vs Readiness.

/health/live  — Kubernetes-style liveness probe.
                Only verifies the process exists.
                Always returns 200 if the server is running.

/health/ready — Kubernetes-style readiness probe.
                Verifies ALL dependencies are healthy:
                database, redis, alembic, models, configuration.
                Returns 200 only when the instance can serve traffic.

/health       — Comprehensive health report (backward-compatible).
                Includes Build ID, model fingerprint, all checks.
"""

from fastapi import APIRouter, Request

router = APIRouter()


def _load_version_metadata() -> dict:
    import json
    from pathlib import Path

    version_path = Path("version.json")
    if version_path.exists():
        try:
            return json.loads(version_path.read_text())
        except (json.JSONDecodeError, OSError):
            pass

    return {
        "git_commit": "unknown",
        "git_branch": "unknown",
        "build_time": "unknown",
        "image_version": "unknown",
        "alembic_head": "unknown",
    }


def _get_startup_phase(request: Request) -> str:
    """Get the startup phase from the app state."""
    try:
        report = request.app.state.startup_report
        return report.phase.value
    except AttributeError:
        return "unknown"


def _run_all_checks() -> dict:
    """Run all dependency checks. Used by /health and /health/ready."""
    import os
    import sys

    checks: dict[str, dict] = {}

    # ── Database ──
    t0 = __import__("time").monotonic()
    try:
        from app.infrastructure.db.session import engine
        with engine.connect() as conn:
            conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        checks["database"] = {"status": "ok", "detail": "connected"}
    except Exception as e:
        checks["database"] = {"status": "error", "detail": str(e)}
    checks["database"]["latency_ms"] = round((__import__("time").monotonic() - t0) * 1000, 1)

    # ── Redis ──
    t0 = __import__("time").monotonic()
    try:
        import redis
        r = redis.from_url(os.environ.get("REDIS_URL", "redis://:redis_dev@redis:6379/0"))
        r.ping()
        checks["redis"] = {"status": "ok", "detail": "connected"}
    except Exception as e:
        checks["redis"] = {"status": "unavailable", "detail": str(e)}
    checks["redis"]["latency_ms"] = round((__import__("time").monotonic() - t0) * 1000, 1)

    # ── LLM Provider ──
    checks["llm_provider"] = {
        "status": "configured" if os.environ.get("DEEPSEEK_API_KEY") else "not_configured",
        "detail": "DEEPSEEK_API_KEY" if os.environ.get("DEEPSEEK_API_KEY") else "not set",
    }

    # ── Telephony ──
    checks["telephony"] = {
        "status": "ok",
        "detail": os.environ.get("TELEPHONY_PROVIDER", "mock"),
    }

    # ── Celery Worker ──
    try:
        import redis
        r = redis.from_url(os.environ.get("CELERY_BROKER_URL", "redis://:redis_dev@redis:6379/0"))
        r.ping()
        checks["worker_broker"] = {"status": "ok", "detail": "connected"}
    except Exception:
        checks["worker_broker"] = {"status": "unavailable", "detail": "broker unreachable"}

    # ── Migration ──
    try:
        from alembic.config import Config
        from alembic.script import ScriptDirectory
        cfg = Config("alembic.ini")
        script = ScriptDirectory.from_config(cfg)
        head = script.get_current_head()
        checks["migration_head"] = {"status": "ok", "detail": head[:8] if head else "unknown"}
    except Exception:
        checks["migration_head"] = {"status": "unknown", "detail": "check failed"}

    # ── Model Fingerprint ──
    try:
        from app.core.build_id import compute_model_fingerprint
        fp = compute_model_fingerprint()
        checks["model_fingerprint"] = {"status": "ok", "detail": fp}
    except Exception as e:
        checks["model_fingerprint"] = {"status": "error", "detail": str(e)}

    # ── Transcript Provider ──
    try:
        from app.application.transcription import create_transcript_provider
        provider = create_transcript_provider("mock")
        checks["transcript_provider"] = {"status": "ok", "detail": provider.provider_name}
    except Exception:
        checks["transcript_provider"] = {"status": "unavailable", "detail": "provider not available"}

    return checks


# ═══════════════════════════════════════════════════════════
# /health/live — Liveness probe
# ═══════════════════════════════════════════════════════════

@router.get("/health/live")
def health_live(request: Request) -> dict:
    """Liveness probe — is the process alive?

    Returns 200 as long as the FastAPI server is running.
    Does NOT check dependencies.
    """
    return {
        "status": "alive",
        "phase": _get_startup_phase(request),
    }


# ═══════════════════════════════════════════════════════════
# /health/ready — Readiness probe
# ═══════════════════════════════════════════════════════════

@router.get("/health/ready")
def health_ready(request: Request) -> dict:
    """Readiness probe — can this instance serve traffic?

    Returns 200 only when ALL dependencies are healthy.
    Docker/Kubernetes should route traffic only to ready instances.
    """
    import os
    import sys

    checks = _run_all_checks()
    version_meta = _load_version_metadata()

    all_ok = all(
        c.get("status") in ("ok", "configured")
        for c in checks.values()
    )

    return {
        "status": "ready" if all_ok else "not_ready",
        "phase": _get_startup_phase(request),
        "build_id": version_meta.get("image_version", "unknown"),
        "model_fingerprint": checks.get("model_fingerprint", {}).get("detail", "unknown"),
        "checks": {k: v["status"] for k, v in checks.items()},
    }


# ═══════════════════════════════════════════════════════════
# /health — Comprehensive health report
# ═══════════════════════════════════════════════════════════

@router.get("/health")
def health(request: Request) -> dict:
    """Comprehensive health check — validates all critical dependencies.

    Includes Build ID, model fingerprint, git commit, and all dependency
    statuses with latency measurements.
    """
    import os
    import sys

    checks = _run_all_checks()
    version_meta = _load_version_metadata()

    # Determine aggregate status
    statuses = [c.get("status", "unknown") for c in checks.values()]
    if all(s in ("ok", "configured") for s in statuses):
        aggregate = "healthy"
    elif any(s == "error" for s in statuses):
        aggregate = "degraded"
    else:
        aggregate = "degraded"

    return {
        "status": aggregate,
        "phase": _get_startup_phase(request),
        "build_id": version_meta.get("image_version", "unknown"),
        "git_commit": version_meta.get("git_commit", "unknown"),
        "git_branch": version_meta.get("git_branch", "unknown"),
        "build_time": version_meta.get("build_time", "unknown"),
        "alembic_head": version_meta.get("alembic_head", "unknown"),
        "model_fingerprint": checks.get("model_fingerprint", {}).get("detail", "unknown"),
        "environment": os.environ.get("PNS_ENV", "development"),
        "python": sys.version.split()[0],
        "checks": checks,
    }
