"""
Execution Log & Retry Engine.

Execution Log: Auditable record of every agent execution.
Retry Engine: Exponential backoff with max retries.
"""

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


# ── Execution Log ──

@dataclass
class ExecutionRecord:
    """Immutable record of a single agent execution."""
    execution_id: str
    agent_name: str
    goal: str
    started_at: float
    completed_at: float | None = None
    status: str = "running"  # running, completed, failed, cancelled
    tools_called: list[str] = field(default_factory=list)
    reasoning_summary: str = ""
    result: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    error: str | None = None
    execution_time_ms: int = 0

    def complete(self, result: dict[str, Any], reasoning: str, confidence: float = 1.0) -> None:
        self.completed_at = time.time()
        self.status = "completed"
        self.result = result
        self.reasoning_summary = reasoning
        self.confidence = confidence
        self.execution_time_ms = int((self.completed_at - self.started_at) * 1000)

    def fail(self, error: str) -> None:
        self.completed_at = time.time()
        self.status = "failed"
        self.error = error
        self.execution_time_ms = int((self.completed_at - self.started_at) * 1000)

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "agent": self.agent_name,
            "goal": self.goal,
            "status": self.status,
            "tools_called": self.tools_called,
            "reasoning": self.reasoning_summary,
            "confidence": self.confidence,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
            "started_at": self.started_at,
        }


class ExecutionLog:
    """Stores and retrieves execution records for auditability."""

    def __init__(self, max_records: int = 1000) -> None:
        self._records: dict[str, ExecutionRecord] = {}
        self._max_records = max_records

    def start(self, agent_name: str, goal: str) -> ExecutionRecord:
        record = ExecutionRecord(
            execution_id=str(uuid.uuid4())[:8],
            agent_name=agent_name,
            goal=goal,
            started_at=time.time(),
        )
        self._records[record.execution_id] = record
        self._trim()
        return record

    def get(self, execution_id: str) -> ExecutionRecord | None:
        return self._records.get(execution_id)

    def list_recent(self, limit: int = 20) -> list[ExecutionRecord]:
        return sorted(self._records.values(), key=lambda r: r.started_at, reverse=True)[:limit]

    def list_by_agent(self, agent_name: str, limit: int = 20) -> list[ExecutionRecord]:
        return sorted(
            [r for r in self._records.values() if r.agent_name == agent_name],
            key=lambda r: r.started_at, reverse=True,
        )[:limit]

    def _trim(self) -> None:
        if len(self._records) > self._max_records:
            sorted_records = sorted(self._records.items(), key=lambda x: x[1].started_at)
            for key, _ in sorted_records[:len(self._records) - self._max_records]:
                del self._records[key]


# ── Global execution log ──

_execution_log: ExecutionLog | None = None


def get_execution_log() -> ExecutionLog:
    global _execution_log
    if _execution_log is None:
        _execution_log = ExecutionLog()
    return _execution_log


# ── Retry Engine ──

@dataclass
class RetryConfig:
    max_retries: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 30.0
    backoff_multiplier: float = 2.0
    retryable_errors: tuple[type[Exception], ...] = (TimeoutError, ConnectionError, OSError)


class RetryEngine:
    """Exponential backoff retry engine for agent tool calls."""

    def __init__(self, config: RetryConfig | None = None) -> None:
        self._config = config or RetryConfig()

    async def execute_with_retry(self, fn, *args, **kwargs) -> Any:
        """Execute a function with exponential backoff retry."""
        last_error: Exception | None = None

        for attempt in range(self._config.max_retries + 1):
            try:
                result = fn(*args, **kwargs)
                if asyncio.iscoroutine(result):
                    result = await result
                return result
            except self._config.retryable_errors as e:
                last_error = e
                if attempt < self._config.max_retries:
                    delay = min(
                        self._config.base_delay_seconds * (self._config.backoff_multiplier ** attempt),
                        self._config.max_delay_seconds,
                    )
                    await asyncio.sleep(delay)
            except Exception as e:
                raise e

        raise last_error or RuntimeError("Max retries exceeded")

    def execute_with_retry_sync(self, fn, *args, **kwargs) -> Any:
        """Synchronous version of execute_with_retry."""
        last_error: Exception | None = None
        import time as _time

        for attempt in range(self._config.max_retries + 1):
            try:
                return fn(*args, **kwargs)
            except self._config.retryable_errors as e:
                last_error = e
                if attempt < self._config.max_retries:
                    delay = min(
                        self._config.base_delay_seconds * (self._config.backoff_multiplier ** attempt),
                        self._config.max_delay_seconds,
                    )
                    _time.sleep(delay)
            except Exception as e:
                raise e

        raise last_error or RuntimeError("Max retries exceeded")
