from datetime import UTC, datetime


def test_cleanup_policy_is_bounded_and_preserves_audit_history():
    from operational_cleanup import RETENTION_DAYS

    assert RETENTION_DAYS["worker_success"] == 7
    assert RETENTION_DAYS["worker_failure"] == 90
    assert RETENTION_DAYS["ai_requests"] == 180
    assert "knowledge_events" not in RETENTION_DAYS
    assert "knowledge_fact_history" not in RETENTION_DAYS


def test_dry_run_counts_without_deleting_or_committing():
    from operational_cleanup import cleanup_operational_history

    class Query:
        def filter(self, *_args):
            return self

        def count(self):
            return 2

        def delete(self, **_kwargs):
            raise AssertionError("dry run must not delete")

    class Session:
        committed = False
        rolled_back = False

        def query(self, _model):
            return Query()

        def commit(self):
            self.committed = True

        def rollback(self):
            self.rolled_back = True

    db = Session()
    result = cleanup_operational_history(db, now=datetime(2026, 8, 13, tzinfo=UTC), dry_run=True)

    assert result["total_deleted"] == 14
    assert result["dry_run"] is True
    assert db.rolled_back is True
    assert db.committed is False


def test_nightly_schedule_and_overlap_lock_exist():
    import worker_tasks as wt

    schedule = wt.celery_app.conf.beat_schedule["operational-cleanup-nightly"]
    assert schedule["task"] == "workers.operational_cleanup"
    assert schedule["options"]["queue"] == "low"
    assert wt.OVERLAP_LOCKS["workers.operational_cleanup"] == 7200
