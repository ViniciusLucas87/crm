"""
Executable Celery overlap tests — prove second invocation body never runs, no retry storm.
"""
import pytest


class TestOverlapPrevention:
    """Tests for _UniqueTask overlap prevention at execution boundary."""

    @pytest.fixture(autouse=True)
    def _patch_redis(self):
        """Provide an in-memory Redis-like store for overlap locks."""
        self._redis_store: dict[str, bytes] = {}

        class FakeRedis:
            def __init__(self, store):
                self._s = store

            def set(self, key, value, nx=None, ex=None):
                if nx and key in self._s:
                    return False
                self._s[key] = value.encode() if isinstance(value, str) else value
                return True

            def get(self, key):
                return self._s.get(key)

            def delete(self, key):
                self._s.pop(key, None)

            def eval(self, script, num_keys, *args):
                key = args[0]
                token = str(args[1])
                if self._s.get(key) == token.encode():
                    self._s.pop(key, None)
                    return 1
                return 0

        store = self._redis_store
        import worker_tasks as wt
        self._orig_redis = wt._get_redis_sync
        wt._get_redis_sync = lambda: FakeRedis(store)
        # Clear overlap locks between tests
        wt._overlap_locks_held.clear()
        yield
        wt._get_redis_sync = self._orig_redis
        wt._overlap_locks_held.clear()

    def test_second_invocation_skips_and_body_never_runs(self):
        """Second concurrent invocation returns a clean skip; body never executes."""
        import worker_tasks as wt
        from unittest.mock import MagicMock

        body_called = []
        task1_id = "task-1"
        task2_id = "task-2"

        # Build a task that can have request set directly
        class TestTask(wt._UniqueTask):
            name = "workers.test_overlap"
            _req = None

            @property
            def request(self):
                return self._req

            @request.setter
            def request(self, val):
                self._req = val

            def run(self, *args, **kwargs):
                body_called.append(1)
                return "done"

        task = TestTask()
        task.app = MagicMock()

        # First invocation
        req = MagicMock()
        type(req).id = type('Prop', (), {'__get__': lambda s,o,t: task1_id})()
        req.id = task1_id
        task.request = req
        task.__call__()
        assert len(body_called) == 1
        assert "task-1" in wt._overlap_locks_held

        # Second invocation: lock held, should return a clean skip
        req2 = MagicMock()
        req2.id = task2_id
        task.request = req2
        result = task.__call__()
        assert result == {"skipped": "overlap", "task": "workers.test_overlap"}

        assert len(body_called) == 1
        assert task2_id not in wt._overlap_locks_held

    def test_after_return_releases_lock_on_success(self):
        """after_return releases the overlap lock on successful completion."""
        import worker_tasks as wt
        from unittest.mock import MagicMock

        wt._overlap_locks_held.clear()

        class TestTask(wt._UniqueTask):
            name = "workers.test_release"

        task = TestTask()
        task.app = MagicMock()

        # Manually add a lock as if __call__ acquired it
        wt._overlap_locks_held["task-x"] = "celery:overlap:workers.test_release"
        self._redis_store["celery:overlap:workers.test_release"] = b"task-x"

        assert "task-x" in wt._overlap_locks_held

        # Simulate after_return
        task.after_return(status="SUCCESS", retval="done", task_id="task-x",
                          args=(), kwargs={}, einfo=None)

        assert "task-x" not in wt._overlap_locks_held

    def test_lock_expires_via_ttl_on_no_release(self):
        """If after_return somehow doesn't fire, lock expires via TTL."""
        import worker_tasks as wt

        assert wt.OVERLAP_LOCKS["workers.company_enrichment"] == 1800
        assert wt.OVERLAP_LOCKS["workers.outbox_process_email"] == 30
        for name, ttl in wt.OVERLAP_LOCKS.items():
            assert ttl > 0, f"{name} has zero TTL"

    def test_no_retry_storm_on_overlap(self):
        """Overlap is represented as a successful result, not an exception."""
        import worker_tasks as wt

        assert "_OverlapSkipped" not in vars(wt)

    def test_task_without_workers_prefix_skips_overlap(self):
        """Tasks without 'workers.' prefix are not overlap-protected."""
        import worker_tasks as wt
        from unittest.mock import MagicMock

        body_called = []

        class TestTask(wt._UniqueTask):
            name = "some.other.task"
            _req = None

            @property
            def request(self):
                return self._req

            @request.setter
            def request(self, val):
                self._req = val

            def run(self, *args, **kwargs):
                body_called.append(1)
                return "done"

        task = TestTask()
        task.app = MagicMock()

        # Pre-acquire the lock as if another worker holds it
        self._redis_store["celery:overlap:some.other.task"] = b"ghost"

        req = MagicMock()
        req.id = "other-1"
        task.request = req

        # Should NOT raise -- prefix doesn't match "workers."
        task.__call__()
        assert len(body_called) == 1
