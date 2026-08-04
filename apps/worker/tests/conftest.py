"""Worker test fixtures — disposable PostgreSQL database with per-test
TRUNCATE isolation.

Creates a unique test database on the existing postgres container,
runs Alembic migrations against *that database only*, and truncates
all user tables between tests.  No connection to pns_crm ever occurs.

Architecture:
  1. Session-scoped _pg_test_database: CREATE DATABASE, set DATABASE_URL
     env so alembic/env.py targets the test DB, run migrations, verify
     tables exist.  On teardown: DROP DATABASE.
  2. Function-scoped _worker_test_session (autouse): TRUNCATE all
     user tables (RESTART IDENTITY CASCADE) before and after each test,
     preserving alembic_version.  Monkeypatch SessionLocal and
     worker_tasks._db_factory to bind to the test DB.
"""

import logging
import os as _os
import uuid
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.db.base import Base
from app.infrastructure.db import models as _models  # noqa: F401

# ── Pytest configuration ──
pytest.register_assert_rewrite("worker_tasks")


def pytest_configure(config):
    config.option.asyncio_default_fixture_loop_scope = "function"


# ── Shared state ──
_test_db_name: str | None = None
_test_db_url: str | None = None
_prior_db_url: str | None = None

PG_ADMIN_URL = _os.environ.get(
    "WORKER_TEST_PG_ADMIN_URL",
    "postgresql+psycopg://postgres:postgres@postgres:5432/postgres",
)


def _database_url(database_name: str) -> str:
    parsed = urlsplit(PG_ADMIN_URL)
    return urlunsplit(
        (parsed.scheme, parsed.netloc, f"/{database_name}", parsed.query, parsed.fragment)
    )

# Tables to keep between tests
_KEEP_TABLES = {"alembic_version"}


def _all_user_tables(engine) -> list[str]:
    """Return every table in the public schema except the keep-list."""
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT tablename FROM pg_tables "
                "WHERE schemaname = 'public' AND tablename != ALL (:keep)"
            ),
            {"keep": list(_KEEP_TABLES)},
        ).fetchall()
    return [r[0] for r in rows]


def _truncate_user_tables(engine) -> None:
    """TRUNCATE all user tables with RESTART IDENTITY CASCADE."""
    tables = _all_user_tables(engine)
    if not tables:
        return
    names = ", ".join(tables)
    with engine.connect() as conn:
        conn.execute(text(f"TRUNCATE TABLE {names} RESTART IDENTITY CASCADE"))
        conn.commit()


def _assert_test_database(engine) -> None:
    """Fail-closed: verify we are connected to a pns_worker_test_ database."""
    with engine.connect() as conn:
        db_name = conn.execute(text("SELECT current_database()")).scalar()
        assert db_name.startswith("pns_worker_test_"), (
            f"SAFETY: connected to {db_name}, not a worker test database"
        )


def _run_migrations(db_url: str) -> None:
    """Apply Alembic migrations to the test database.

    Sets DATABASE_URL in the environment so alembic/env.py (which calls
    get_settings()) uses the test URL, then clears the settings cache
    and restores the original value afterward.
    """
    from alembic.config import Config
    from alembic import command

    global _prior_db_url
    _prior_db_url = _os.environ.get("DATABASE_URL")

    _os.environ["DATABASE_URL"] = db_url
    try:
        from app.core.config import get_settings
        get_settings.cache_clear()
    except Exception:
        pass

    try:
        api_root = Path(__file__).resolve().parents[2] / "api"
        if not api_root.exists():
            api_root = Path("/app/api")
        alembic_cfg = Config(str(api_root / "alembic.ini"))
        alembic_cfg.set_main_option("script_location", str(api_root / "alembic"))
        alembic_cfg.set_main_option("sqlalchemy.url", db_url)
        command.upgrade(alembic_cfg, "head")
    finally:
        if _prior_db_url is not None:
            _os.environ["DATABASE_URL"] = _prior_db_url
        else:
            _os.environ.pop("DATABASE_URL", None)
        try:
            from app.core.config import get_settings
            get_settings.cache_clear()
        except Exception:
            pass


@pytest.fixture(scope="session")
def _pg_test_database():
    """Session-scoped: create a unique test DB, migrate, drop at exit."""
    global _test_db_name, _test_db_url

    _test_db_name = f"pns_worker_test_{uuid.uuid4().hex[:8]}"
    _test_db_url = _database_url(_test_db_name)

    admin = create_engine(PG_ADMIN_URL, isolation_level="AUTOCOMMIT")
    try:
        with admin.connect() as conn:
            conn.execute(text(f"CREATE DATABASE {_test_db_name}"))
            logging.info("Worker test database created: %s", _test_db_name)

        _run_migrations(_test_db_url)
        logging.info("Worker test migrations applied: %s", _test_db_name)

        # Verify tables exist
        verify_engine = create_engine(_test_db_url)
        _assert_test_database(verify_engine)
        with verify_engine.connect() as conn:
            alembic_rows = conn.execute(
                text("SELECT version_num FROM alembic_version")
            ).fetchall()
            assert len(alembic_rows) >= 1, "alembic_version is empty — migrations failed"
            call_table = conn.execute(
                text(
                    "SELECT EXISTS (SELECT FROM information_schema.tables "
                    "WHERE table_name = 'calls')"
                )
            ).scalar()
            assert call_table, "calls table missing after migration"
            outbox_table = conn.execute(
                text(
                    "SELECT EXISTS (SELECT FROM information_schema.tables "
                    "WHERE table_name = 'outbox_events')"
                )
            ).scalar()
            assert outbox_table, "outbox_events table missing after migration"
            logging.info(
                "Verified test DB %s: alembic head=%s, calls=%s, outbox=%s",
                _test_db_name,
                alembic_rows[0][0],
                call_table,
                outbox_table,
            )
        verify_engine.dispose()
    except Exception:
        admin.dispose()
        raise
    admin.dispose()

    yield _test_db_url

    # Teardown
    admin = create_engine(PG_ADMIN_URL, isolation_level="AUTOCOMMIT")
    try:
        with admin.connect() as conn:
            conn.execute(
                text(
                    f"SELECT pg_terminate_backend(pg_stat_activity.pid) "
                    f"FROM pg_stat_activity "
                    f"WHERE pg_stat_activity.datname = '{_test_db_name}' "
                    f"AND pid <> pg_backend_pid()"
                )
            )
            conn.execute(text(f"DROP DATABASE IF EXISTS {_test_db_name}"))
            logging.info("Worker test database dropped: %s", _test_db_name)
    finally:
        admin.dispose()
        _test_db_name = None
        _test_db_url = None


@pytest.fixture(autouse=True)
def _worker_test_session(_pg_test_database, monkeypatch: pytest.MonkeyPatch):
    """Per-test: truncate user tables, monkeypatch DB access, yield, truncate.

    Uses TRUNCATE RESTART IDENTITY CASCADE because worker code calls
    db.commit() (breaking transaction-wrap).  No test data persists
    between tests.
    """
    engine = create_engine(_pg_test_database)
    _assert_test_database(engine)

    # Clean before the test
    _truncate_user_tables(engine)

    TestSessionLocal = sessionmaker(
        bind=engine, autocommit=False, autoflush=False, class_=Session
    )

    monkeypatch.setattr(
        "app.infrastructure.db.session.SessionLocal", TestSessionLocal
    )

    import worker_tasks

    monkeypatch.setattr(worker_tasks, "_db_factory", TestSessionLocal)
    worker_tasks._overlap_locks_held.clear()

    yield

    # Clean after the test
    _truncate_user_tables(engine)
    engine.dispose()

