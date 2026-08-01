from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import logging

# ── Configure all worker loggers at INFO level ──
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
for logger_name in ["pns.workers", "worker", "app.application.workers"]:
    logging.getLogger(logger_name).setLevel(logging.INFO)

from app.core.build_id import run_startup_checks
from app.core.config import get_settings
from app.presentation.api.v1.router import api_router

# ── Fail-fast startup validation ──
startup_report = run_startup_checks()

settings = get_settings()

# ── Worker Manager (global, initialized at startup) ──
# Workers are now Celery tasks (see apps/worker/worker_tasks.py).
# FastAPI enqueues work. Celery executes it.
worker_manager = None  # Kept for health/metrics API compatibility


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    global worker_manager
    root = logging.getLogger()

    # Worker Manager (thin — workers execute via Celery, scheduled by Celery Beat)
    from app.infrastructure.db.session import SessionLocal
    from app.application.workers import WorkerManager
    from app.application.workers.persistence import ensure_worker_schedule
    from app.application.workers.workers import ALL_WORKER_FACTORIES

    root.info("═══ WORKER MANAGER STARTUP ═══")
    worker_manager = WorkerManager(SessionLocal)
    queue_by_worker = {
        "company_enrichment": "normal",
        "fact_verification": "high",
        "entity_resolution": "normal",
        "relationship_discovery": "normal",
        "technology_detection": "normal",
        "buying_signal_detector": "high",
        "knowledge_decay": "low",
        "reasoning": "normal",
        "timeline_generator": "low",
        "opportunity_scoring": "high",
        "search_indexer": "background",
        "recommendation_engine": "normal",
    }
    db = SessionLocal()
    try:
        for factory in ALL_WORKER_FACTORIES:
            worker = factory(SessionLocal)
            worker_manager.register(worker)
            ensure_worker_schedule(
                db,
                worker_name=worker.config.name,
                queue_name=queue_by_worker.get(worker.config.name, "normal"),
                schedule_type=worker.config.schedule.value,
                cron_expr=worker.config.schedule_cron,
            )
    finally:
        db.close()

    root.info(f"✅ WorkerManager: {len(worker_manager._workers)} workers registered")
    root.info("   Workers execute via Celery (see apps/worker/worker_tasks.py)")
    root.info("   Celery Beat schedule: 12 workers on crontab intervals")

    yield

    if worker_manager:
        root.info("Shutting down workers...")
        await worker_manager.stop_all()
        root.info("✅ All workers stopped")


app = FastAPI(
    title="Pacific North Systems OS API",
    version="0.1.0",
    lifespan=lifespan,
)

app.state.startup_report = startup_report

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
