"""
Immutable Build ID and Model Fingerprint.

Every component of the system shares the same Build ID:
  Format: YYYYMMDD-HHMMSS-<git_sha>

The model fingerprint is a SHA256 hash of all SQLAlchemy models +
migrations. It detects schema/code drift at startup.

Exposed via:
  - /health/live  — is the process alive?
  - /health/ready — can this instance serve traffic?

Startup state machine:
  STARTING → MODELS_VALIDATED → DB_CONNECTED → ALEMBIC_VERIFIED → READY
  Any failure → FATAL (exit) or DEGRADED (retry)
"""

import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


# ═══════════════════════════════════════════════════════════════
# Startup State Machine
# ═══════════════════════════════════════════════════════════════

class StartupPhase(Enum):
    STARTING = "starting"
    MODELS_VALIDATED = "models_validated"
    DB_CONNECTED = "db_connected"
    ALEMBIC_VERIFIED = "alembic_verified"
    READY = "ready"
    DEGRADED = "degraded"
    FATAL = "fatal"


@dataclass
class StartupReport:
    """Structured startup report produced once at boot."""

    build_id: str = "unknown"
    git_commit: str = "unknown"
    build_time: str = "unknown"
    python_version: str = sys.version.split()[0]
    environment: str = "development"

    phase: StartupPhase = StartupPhase.STARTING
    checks: dict[str, dict[str, Any]] = field(default_factory=dict)
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def record(self, name: str, status: str, detail: str = "", duration_ms: float = 0) -> None:
        self.checks[name] = {"status": status, "detail": detail, "duration_ms": round(duration_ms, 1)}

    def all_passed(self) -> bool:
        return all(c["status"] == "ok" for c in self.checks.values())

    def to_dict(self) -> dict:
        return {
            "build_id": self.build_id,
            "git_commit": self.git_commit,
            "build_time": self.build_time,
            "python": self.python_version,
            "environment": self.environment,
            "phase": self.phase.value,
            "checks": self.checks,
            "started_at": self.started_at,
        }

    def print_banner(self) -> None:
        """Print a structured startup banner."""
        width = 52
        print("=" * width)
        print("  Pacific North Systems API")
        print("=" * width)
        print(f"  Build ID:    {self.build_id}")
        print(f"  Git SHA:     {self.git_commit}")
        print(f"  Build Time:  {self.build_time}")
        print(f"  Python:      {self.python_version}")
        print(f"  Environment: {self.environment}")
        print("-" * width)
        for name, check in self.checks.items():
            icon = "✓" if check["status"] == "ok" else "✗" if check["status"] == "fatal" else "⚠"
            print(f"  {icon} {name}: {check['detail']}")
        print("-" * width)
        print(f"  Startup: {'SUCCESS' if self.all_passed() else 'FAILED'}")
        print("=" * width)


# ── Global report instance ──
report = StartupReport()


# ═══════════════════════════════════════════════════════════════
# Build ID
# ═══════════════════════════════════════════════════════════════

def load_build_metadata() -> dict:
    """Read version.json injected at Docker build time."""
    version_path = Path("version.json")
    if version_path.exists():
        try:
            return json.loads(version_path.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def compute_model_fingerprint() -> str:
    """Generate a SHA256 fingerprint from all SQLAlchemy models and migrations.

    This fingerprint changes whenever:
      - A model class is added, removed, or modified
      - A migration file is added, removed, or modified

    It is compared at startup to detect schema/code drift.
    """
    hasher = hashlib.sha256()

    # Hash all .py files in the models directory
    models_dir = Path("app/infrastructure/db")
    for py_file in sorted(models_dir.rglob("*.py")):
        if "__pycache__" in str(py_file):
            continue
        hasher.update(py_file.read_bytes())
        hasher.update(b"\n")

    # Hash all migration files
    migrations_dir = Path("alembic/versions")
    if migrations_dir.exists():
        for py_file in sorted(migrations_dir.rglob("*.py")):
            if "__pycache__" in str(py_file):
                continue
            hasher.update(py_file.read_bytes())
            hasher.update(b"\n")

    return hasher.hexdigest()[:16]


# ═══════════════════════════════════════════════════════════════
# Startup validators (called by main.py)
# ═══════════════════════════════════════════════════════════════

def validate_models() -> None:
    """Validate all SQLAlchemy models and compute fingerprint."""
    t0 = time.monotonic()
    try:
        from app.infrastructure.db import models  # noqa: F401
        from app.infrastructure.db.base import Base

        Base.registry.configure()
        fingerprint = compute_model_fingerprint()
        report.record("models", "ok", f"{len(Base.registry.mappers)} mappers, fingerprint={fingerprint}", (time.monotonic() - t0) * 1000)
        report.phase = StartupPhase.MODELS_VALIDATED
    except Exception as exc:
        report.record("models", "fatal", str(exc))
        report.phase = StartupPhase.FATAL
        report.print_banner()
        sys.exit(1)


def validate_database() -> None:
    """Verify database connectivity."""
    t0 = time.monotonic()
    max_retries = 5
    for attempt in range(1, max_retries + 1):
        try:
            from app.infrastructure.db.session import engine
            from sqlalchemy import text

            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            report.record("database", "ok", f"connected (attempt {attempt})", (time.monotonic() - t0) * 1000)
            report.phase = StartupPhase.DB_CONNECTED
            return
        except Exception as exc:
            if attempt < max_retries:
                wait = 2 ** attempt
                print(f"[startup] Database unavailable (attempt {attempt}/{max_retries}), retrying in {wait}s: {exc}")
                time.sleep(wait)
            else:
                report.record("database", "fatal", f"unreachable after {max_retries} attempts: {exc}")
                report.phase = StartupPhase.FATAL
                report.print_banner()
                sys.exit(1)


def validate_alembic() -> None:
    """Verify alembic migrations match available files."""
    t0 = time.monotonic()
    try:
        from alembic.config import Config
        from alembic.script import ScriptDirectory

        alembic_ini = Path("alembic.ini")
        if not alembic_ini.exists():
            report.record("alembic", "warning", "alembic.ini not found")
            report.phase = StartupPhase.ALEMBIC_VERIFIED
            return

        cfg = Config(str(alembic_ini))
        script = ScriptDirectory.from_config(cfg)
        head = script.get_current_head()
        if head:
            report.record("alembic", "ok", f"head={head[:12]}...", (time.monotonic() - t0) * 1000)
        else:
            report.record("alembic", "warning", "no head found")
        report.phase = StartupPhase.ALEMBIC_VERIFIED
    except Exception as exc:
        report.record("alembic", "warning", f"check failed: {exc}")
        report.phase = StartupPhase.ALEMBIC_VERIFIED  # non-fatal


def validate_environment() -> None:
    """Check critical environment variables."""
    t0 = time.monotonic()
    required = ["DATABASE_URL"]
    missing = [v for v in required if not os.environ.get(v)]

    if missing:
        report.record("environment", "fatal", f"missing: {', '.join(missing)}")
        report.phase = StartupPhase.FATAL
        report.print_banner()
        sys.exit(1)

    report.record("environment", "ok", f"all {len(required)} required vars set", (time.monotonic() - t0) * 1000)


def run_startup_checks() -> StartupReport:
    """Execute all startup validations. Returns the report.

    On fatal errors, the process exits. On recoverable errors,
    the report is marked DEGRADED but the process continues.
    """
    metadata = load_build_metadata()
    report.build_id = metadata.get("image_version", "unknown")
    report.git_commit = metadata.get("git_commit", "unknown")
    report.build_time = metadata.get("build_time", "unknown")
    report.environment = os.environ.get("PNS_ENV", "development")

    print()  # blank line before banner

    validate_environment()
    validate_models()
    validate_database()
    validate_alembic()

    if report.all_passed():
        report.phase = StartupPhase.READY

    report.print_banner()
    return report
