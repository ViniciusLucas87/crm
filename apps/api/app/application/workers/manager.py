"""Autonomous Knowledge Workers — Manager"""
from __future__ import annotations
import asyncio, logging
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any, Callable
from sqlalchemy.orm import Session
from app.application.workers.events import Event, EventBus, EventType
from app.application.workers.framework import BaseWorker, WorkerConfig, WorkerMetrics, WorkerPriority, WorkerStatus, ScheduleType

logger = logging.getLogger(__name__)

class WorkerManager:
    def __init__(self, db_session_factory: Callable[[], Session]):
        self._db_factory = db_session_factory; self._workers: dict[str, BaseWorker] = {}
        self._running = False; self._monitor_task: asyncio.Task | None = None
        self._dead_letter: list[dict[str, Any]] = []

    def register(self, worker: BaseWorker) -> None:
        self._workers[worker.config.name] = worker
        logger.info(f"Registered worker: {worker.config.name}")

    async def start_all(self) -> None:
        self._running = True
        sorted_workers = sorted(self._workers.values(), key=lambda w: w.config.priority.value)
        for worker in sorted_workers:
            await worker.start()
        self._monitor_task = asyncio.create_task(self._health_monitor())
        db = self._db_factory()
        try:
            bus = EventBus(db)
            bus.publish(Event(event_type=EventType.WORKER_STARTED, entity_type="system", entity_id=0,
                payload={"workers": list(self._workers.keys())}, source="worker_manager"))
        finally: db.close()
        logger.info(f"WorkerManager started {len(self._workers)} workers")

    async def stop_all(self) -> None:
        self._running = False
        if self._monitor_task and not self._monitor_task.done(): self._monitor_task.cancel()
        for worker in self._workers.values(): await worker.stop()
        logger.info("WorkerManager stopped all workers")

    async def restart_worker(self, name: str) -> None:
        worker = self._workers.get(name)
        if worker: await worker.stop(); await worker.start()

    async def pause_worker(self, name: str) -> None:
        w = self._workers.get(name)
        if w: await w.pause()

    async def resume_worker(self, name: str) -> None:
        w = self._workers.get(name)
        if w: await w.resume()

    async def _health_monitor(self) -> None:
        while self._running:
            for name, worker in list(self._workers.items()):
                if not worker.is_healthy and worker.status != WorkerStatus.STOPPED:
                    logger.warning(f"Worker {name} unhealthy — restarting")
                    try: await self.restart_worker(name)
                    except Exception as exc: logger.error(f"Failed restart {name}: {exc}")
            await asyncio.sleep(10.0)

    def get_health(self) -> dict[str, Any]:
        health_data = {}
        for name, w in self._workers.items():
            try:
                health_data[name] = {"worker": w.config.name, "status": w.status.value, "healthy": w.is_healthy}
            except Exception:
                health_data[name] = {"worker": w.config.name, "status": w.status.value, "healthy": w.is_healthy}
        return {"manager_running": self._running, "workers": health_data}

    def get_metrics(self) -> dict[str, Any]:
        total = defaultdict(int); workers_detail = {}
        for name, w in self._workers.items():
            m = w.metrics
            workers_detail[name] = {"status": w.status.value, "healthy": w.is_healthy,
                "jobs_processed": m.jobs_processed, "jobs_succeeded": m.jobs_succeeded,
                "jobs_failed": m.jobs_failed, "retries": m.retries, "avg_runtime_ms": round(m.avg_runtime_ms, 1),
                "last_run": m.last_run_at.isoformat() if m.last_run_at else None, "last_error": m.last_error,
                "facts_created": m.facts_created, "facts_verified": m.facts_verified,
                "relationships_created": m.relationships_created, "insights_generated": m.insights_generated,
                "entities_enriched": m.entities_enriched}
            for k in ["jobs_processed", "jobs_succeeded", "jobs_failed", "retries", "facts_created", "facts_verified", "relationships_created", "insights_generated", "entities_enriched"]:
                total[k] += getattr(m, k, 0)
        return {"aggregate": dict(total), "workers": workers_detail, "dead_letter_count": len(self._dead_letter),
                "manager_running": self._running, "timestamp": datetime.now(UTC).isoformat()}

    def add_dead_letter(self, worker_name: str, event: dict[str, Any], error: str) -> None:
        self._dead_letter.append({"worker": worker_name, "event": event, "error": error, "failed_at": datetime.now(UTC).isoformat()})
        if len(self._dead_letter) > 1000: self._dead_letter = self._dead_letter[-500:]

    def get_dead_letter(self, limit: int = 50) -> list[dict[str, Any]]:
        return self._dead_letter[-limit:]

    def replay_dead_letter(self, index: int) -> bool:
        if 0 <= index < len(self._dead_letter):
            self._dead_letter.pop(index); return True
        return False
