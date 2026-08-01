"""Autonomous Knowledge Workers — Core Framework"""

from __future__ import annotations
import asyncio, logging, time, uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)

class WorkerStatus(str, Enum):
    STOPPED = "stopped"; STARTING = "starting"; RUNNING = "running"; PAUSED = "paused"; STOPPING = "stopping"; ERROR = "error"

class WorkerPriority(int, Enum):
    CRITICAL = 0; HIGH = 1; NORMAL = 2; LOW = 3; BACKGROUND = 4

class ScheduleType(str, Enum):
    IMMEDIATE = "immediate"; HOURLY = "hourly"; DAILY = "daily"; WEEKLY = "weekly"; MONTHLY = "monthly"; EVENT_TRIGGERED = "event_triggered"; MANUAL = "manual"

@dataclass
class WorkerConfig:
    name: str; description: str = ""; priority: WorkerPriority = WorkerPriority.NORMAL
    concurrency: int = 1; max_retries: int = 3; retry_backoff_seconds: float = 60.0
    heartbeat_interval_seconds: float = 30.0; schedule: ScheduleType = ScheduleType.EVENT_TRIGGERED
    schedule_cron: str | None = None; supported_events: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list); dead_letter_max: int = 100

@dataclass
class WorkerMetrics:
    jobs_processed: int = 0; jobs_succeeded: int = 0; jobs_failed: int = 0; retries: int = 0
    dead_letter_count: int = 0; avg_runtime_ms: float = 0.0
    last_run_at: datetime | None = None; last_error: str | None = None
    facts_created: int = 0; facts_verified: int = 0; relationships_created: int = 0
    insights_generated: int = 0; entities_enriched: int = 0

    def record_success(self, runtime_ms: float):
        self.jobs_processed += 1; self.jobs_succeeded += 1; self.last_run_at = datetime.now(UTC)
        n = self.jobs_succeeded; self.avg_runtime_ms = (self.avg_runtime_ms * (n - 1) + runtime_ms) / n

    def record_failure(self, error: str):
        self.jobs_processed += 1; self.jobs_failed += 1; self.last_error = error; self.last_run_at = datetime.now(UTC)

class BaseWorker(ABC):
    def __init__(self, config: WorkerConfig, db_session_factory: Callable):
        self.config = config; self._db_factory = db_session_factory
        self._status = WorkerStatus.STOPPED; self._metrics = WorkerMetrics()
        self._last_heartbeat: datetime | None = None; self._id = str(uuid.uuid4())[:8]
        self._shutdown_event = asyncio.Event(); self._task: asyncio.Task | None = None
        self.logger = logging.getLogger(f"worker.{config.name}")

    @property
    def worker_id(self) -> str: return self._id
    @property
    def status(self) -> WorkerStatus: return self._status
    @property
    def metrics(self) -> WorkerMetrics: return self._metrics
    @property
    def is_healthy(self) -> bool:
        if self._status != WorkerStatus.RUNNING: return False
        if self._last_heartbeat is None: return False
        elapsed = (datetime.now(UTC) - self._last_heartbeat).total_seconds()
        return elapsed < self.config.heartbeat_interval_seconds * 3

    async def start(self) -> None:
        if self._status in (WorkerStatus.RUNNING, WorkerStatus.STARTING): return
        self._status = WorkerStatus.STARTING; self._shutdown_event.clear()
        self._task = asyncio.create_task(self._run_loop())
        self._status = WorkerStatus.RUNNING
        self.logger.info(f"Worker {self.config.name} started (id={self._id})")

    async def stop(self) -> None:
        if self._status == WorkerStatus.STOPPED: return
        self._status = WorkerStatus.STOPPING; self._shutdown_event.set()
        if self._task and not self._task.done():
            self._task.cancel()
            try: await self._task
            except asyncio.CancelledError: pass
        self._status = WorkerStatus.STOPPED
        self.logger.info(f"Worker {self.config.name} stopped")

    async def pause(self) -> None:
        if self._status == WorkerStatus.RUNNING: self._status = WorkerStatus.PAUSED
    async def resume(self) -> None:
        if self._status == WorkerStatus.PAUSED: self._status = WorkerStatus.RUNNING

    async def _run_loop(self) -> None:
        while not self._shutdown_event.is_set():
            try:
                self._last_heartbeat = datetime.now(UTC)
                if self._status == WorkerStatus.RUNNING:
                    t0 = time.monotonic()
                    try:
                        await self.execute()
                        self._metrics.record_success((time.monotonic() - t0) * 1000)
                    except Exception as exc:
                        self._metrics.record_failure(str(exc))
                        self.logger.error(f"Worker {self.config.name} failed: {exc}")
                        self._metrics.retries += 1
                        if self._metrics.retries > self.config.max_retries:
                            self._status = WorkerStatus.ERROR
                        await asyncio.sleep(self.config.retry_backoff_seconds * min(self._metrics.retries, 10))
                await asyncio.sleep(1.0)
            except asyncio.CancelledError: break
            except Exception: await asyncio.sleep(5.0)

    @abstractmethod
    async def execute(self) -> None: ...

    async def health_check(self) -> dict[str, Any]:
        return {"worker": self.config.name, "status": self._status.value, "healthy": self.is_healthy,
                "last_heartbeat": self._last_heartbeat.isoformat() if self._last_heartbeat else None}
