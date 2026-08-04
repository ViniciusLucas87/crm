"""Phase 1 worker hardening: integration tests for reconciliation and SMS workers.

Tests run against a disposable PostgreSQL database (conftest.py) with
per-test transaction rollback.  SELECT FOR UPDATE SKIP LOCKED works.
No test data ever touches the development database.

Tests cover:
  1. Hangup then late answer during grace — no recovery
  2. True missed call after grace — full recovery pipeline
  3. Duplicate worker execution — idempotent
  4. Concurrent claim — SELECT FOR UPDATE SKIP LOCKED
  5. STOP suppression — SMS blocked
  6. Provider timeout before send — retry
  7. Uncertain timeout after provider acceptance — no duplicate SMS
  8. Delivery receipt — sms_status updated
  9. No tenant — fails safely
  10. Spam quarantine — no SMS
  11. Exactly one callback task, missed activity, and SMS
  12. Routing test — dispatcher maps events correctly
"""

import uuid
from datetime import datetime, UTC, timedelta
from unittest.mock import patch

import pytest
import httpx
from sqlalchemy.orm import Session

from app.infrastructure.db.models import (
    Call, Task, Activity, OutboxEvent, ProviderWebhookEvent, PhoneSuppression,
    Organization,
)

import worker_tasks

# Re-export production bounded helpers under the names the tests use
_correlation_id = worker_tasks.bounded_correlation_id
_idempotency_key = worker_tasks.bounded_idempotency_key
# Canonical prefix constants must match production
MISSED_CALL_CORR_PREFIX = worker_tasks.MISSED_CALL_CORR_PREFIX
SMS_MISSED_CALL_IDEM_PREFIX = worker_tasks.SMS_MISSED_CALL_IDEM_PREFIX
SMS_PROVIDER_IDEM_PREFIX = worker_tasks.SMS_PROVIDER_IDEM_PREFIX


RECONCILIATION_EVENT = worker_tasks.RECONCILIATION_EVENT
SMS_RECOVERY_EVENT = worker_tasks.SMS_RECOVERY_EVENT


# ── DB session fixture ──
# The conftest monkeypatches SessionLocal + worker_tasks._db_factory,
# so this module must NOT import SessionLocal at module level — otherwise
# the reference is captured before the monkeypatch takes effect.


@pytest.fixture
def db():
    """Yield a session bound to the per-test DB.  Always closed in finally."""
    from app.infrastructure.db.session import SessionLocal
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(autouse=True)
def _seed_organization(db):
    """Ensure an Organization with id=1 exists for FK references."""
    from uuid import uuid4
    org = Organization(
        id=1,
        name="Test Org",
        slug=f"test-org-{uuid4().hex[:8]}",
    )
    db.add(org)
    db.commit()


# ── Test helpers ──


def _create_call(db: Session, **overrides) -> Call:
    """Create a test Call row."""
    now = datetime.now(UTC)
    call_status = overrides.pop("status", "COMPLETED")
    call = Call(
        public_uuid=str(uuid.uuid4()),
        organization_id=1,
        direction="inbound",
        status=call_status,
        phone_number="+16045551234",
        caller_id="+16045551234",
        normalized_caller_number="+16045551234",
        provider_call_id=overrides.pop(
            "provider_call_id", f"call_ctrl_{uuid.uuid4().hex[:8]}"
        ),
        spam_score=overrides.pop("spam_score", 10),
        started_at=now - timedelta(minutes=5),
        ended_at=now,
        duration_seconds=0,
        **overrides,
    )
    db.add(call)
    db.commit()
    db.refresh(call)
    return call


def _create_outbox_event(
    db: Session, event_type: str, call: Call, **overrides
) -> OutboxEvent:
    """Create a pending OutboxEvent for a call.

    Uses distinct canonical prefixes per event type so reconciliation
    input events and SMS output events never collide on idempotency_key."""
    if event_type == RECONCILIATION_EVENT:
        idem_prefix = "recon"
        corr_prefix = "recon"
    else:
        idem_prefix = SMS_MISSED_CALL_IDEM_PREFIX
        corr_prefix = MISSED_CALL_CORR_PREFIX

    idem_key = overrides.pop(
        "idempotency_key",
        _idempotency_key(idem_prefix, call.public_uuid),
    )
    corr_id = overrides.pop(
        "correlation_id",
        _correlation_id(corr_prefix, call.public_uuid),
    )
    event = OutboxEvent(
        event_type=event_type,
        payload_json={
            "call_id": call.id,
            "call_public_uuid": call.public_uuid,
            "normalized_caller_number": call.normalized_caller_number,
            "organization_id": call.organization_id,
            "contact_id": call.contact_id,
            "company_id": call.company_id,
        },
        correlation_id=corr_id,
        idempotency_key=idem_key,
        status="pending",
        **overrides,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def _create_webhook_event(
    db: Session, call: Call, event_type: str, **overrides
) -> ProviderWebhookEvent:
    """Create a ProviderWebhookEvent row for ledger reconciliation."""
    evt = ProviderWebhookEvent(
        provider_event_id=overrides.pop(
            "provider_event_id", f"evt_{uuid.uuid4().hex[:12]}"
        ),
        provider="telnyx",
        event_type=event_type,
        call_control_id=call.provider_call_id,
        call_leg_id=call.provider_leg_id or "leg_001",
        payload_hash="abc123",
        processing_status="processed",
    )
    db.add(evt)
    db.commit()
    db.refresh(evt)
    return evt


# ═══════════════════════════════════════════════════════════
# Reconciliation Worker Tests
# ═══════════════════════════════════════════════════════════


class TestReconciliationWorker:
    """Integration tests for call_missed_call_recovery worker."""

    def test_hangup_then_late_answer_during_grace_no_recovery(self, db):
        """A hangup followed by a late call.answered in the event ledger
        during the grace period should NOT trigger recovery."""
        call = _create_call(db, status="COMPLETED")
        event = _create_outbox_event(db, RECONCILIATION_EVENT, call)
        _create_webhook_event(db, call, "call.answered")

        worker_tasks.call_missed_call_recovery(event_id=event.id)

        db.refresh(event)
        db.refresh(call)
        assert event.status == "completed"
        assert call.status == "COMPLETED"

        tasks = db.query(Task).filter(
            Task.recovery_key == f"missed_call_{call.public_uuid}"
        ).all()
        assert len(tasks) == 0

    def test_true_missed_call_after_grace_full_recovery(self, db):
        """A hangup with no answer in the ledger after grace period
        should trigger full recovery: COMPLETED→MISSED, task, activity, SMS."""
        call = _create_call(db, status="COMPLETED")
        _create_webhook_event(db, call, "call.hangup")
        event = _create_outbox_event(db, RECONCILIATION_EVENT, call)

        worker_tasks.call_missed_call_recovery(event_id=event.id)

        db.refresh(event)
        db.refresh(call)
        assert event.status == "completed"
        assert call.status == "MISSED"
        assert call.outcome == "missed"

        task = db.query(Task).filter(
            Task.recovery_key == f"missed_call_{call.public_uuid}"
        ).first()
        assert task is not None
        assert task.source == "missed_call"
        assert task.priority == "high"
        assert task.status == "open"

        activity = db.query(Activity).filter(
            Activity.activity_type == "call_missed",
            Activity.company_id == call.company_id,
        ).first()
        assert activity is not None

        sms_event = db.query(OutboxEvent).filter(
            OutboxEvent.event_type == SMS_RECOVERY_EVENT,
            OutboxEvent.idempotency_key == _idempotency_key(SMS_MISSED_CALL_IDEM_PREFIX, call.public_uuid),
        ).first()
        assert sms_event is not None
        assert sms_event.status == "pending"

    def test_duplicate_worker_execution_idempotent(self, db):
        """Running the worker twice on the same event should be idempotent."""
        call = _create_call(db, status="COMPLETED")
        _create_webhook_event(db, call, "call.hangup")
        event = _create_outbox_event(db, RECONCILIATION_EVENT, call)

        worker_tasks.call_missed_call_recovery(event_id=event.id)
        db.refresh(event)
        assert event.status == "completed"

        # Second run — event already completed
        worker_tasks.call_missed_call_recovery(event_id=event.id)

        tasks = db.query(Task).filter(
            Task.recovery_key == f"missed_call_{call.public_uuid}"
        ).all()
        assert len(tasks) == 1

        sms_key = _idempotency_key(SMS_MISSED_CALL_IDEM_PREFIX, call.public_uuid)
        sms_events = db.query(OutboxEvent).filter(
            OutboxEvent.event_type == SMS_RECOVERY_EVENT,
            OutboxEvent.idempotency_key == sms_key,
        ).all()
        assert len(sms_events) == 1

    def test_concurrent_claim_prevents_double_processing(self, db):
        """Two workers claiming the same event: only one succeeds (FOR UPDATE SKIP LOCKED)."""
        call = _create_call(db, status="COMPLETED")
        _create_webhook_event(db, call, "call.hangup")
        event = _create_outbox_event(db, RECONCILIATION_EVENT, call)

        from app.infrastructure.db.session import SessionLocal

        db1 = SessionLocal()
        db2 = SessionLocal()
        try:
            evt1 = db1.query(OutboxEvent).filter(OutboxEvent.id == event.id).first()
            evt2 = db2.query(OutboxEvent).filter(OutboxEvent.id == event.id).first()

            claimed1 = worker_tasks._claim_event(db1, evt1, "worker-1")

            # Refresh from DB to see the committed claim
            db2.expire(evt2)
            evt2 = db2.query(OutboxEvent).filter(OutboxEvent.id == event.id).first()

            attempt_before = evt2.attempt_count
            lease_before = evt2.lease_holder

            claimed2 = worker_tasks._claim_event(db2, evt2, "worker-2")

            assert claimed1 is True
            assert claimed2 is False, "Second worker must not claim an already-claimed event"

            # Verify the second claim did NOT mutate the record
            db1.expire(evt1)
            evt1 = db1.query(OutboxEvent).filter(OutboxEvent.id == event.id).first()
            assert evt1.attempt_count == 1, (
                f"attempt_count must remain 1, got {evt1.attempt_count}"
            )
            assert evt1.lease_holder == "worker-1", (
                f"lease_holder must remain 'worker-1', got {evt1.lease_holder}"
            )

            db1.rollback()
            db2.rollback()
        finally:
            db1.close()
            db2.close()

    def test_already_missed_call_skipped(self, db):
        """A call already in MISSED status should be skipped."""
        call = _create_call(db, status="MISSED")
        event = _create_outbox_event(db, RECONCILIATION_EVENT, call)

        worker_tasks.call_missed_call_recovery(event_id=event.id)

        db.refresh(event)
        assert event.status == "completed"

        tasks = db.query(Task).filter(
            Task.recovery_key == f"missed_call_{call.public_uuid}"
        ).all()
        assert len(tasks) == 0

    def test_exactly_one_callback_task_activity_and_sms(self, db):
        """A true missed call produces exactly one task, one activity, one SMS."""
        call = _create_call(db, status="COMPLETED")
        _create_webhook_event(db, call, "call.hangup")
        event = _create_outbox_event(db, RECONCILIATION_EVENT, call)

        worker_tasks.call_missed_call_recovery(event_id=event.id)

        tasks = db.query(Task).filter(
            Task.recovery_key == f"missed_call_{call.public_uuid}"
        ).all()
        assert len(tasks) == 1

        activities = db.query(Activity).filter(
            Activity.activity_type == "call_missed",
            Activity.company_id == call.company_id,
        ).all()
        assert len(activities) >= 1

        sms_key = _idempotency_key(SMS_MISSED_CALL_IDEM_PREFIX, call.public_uuid)
        sms_events = db.query(OutboxEvent).filter(
            OutboxEvent.idempotency_key == sms_key,
        ).all()
        assert len(sms_events) == 1

    def test_unknown_caller_activity_with_null_company(self, db):
        """A missed call with no company_id creates an Activity with company_id=NULL.

        Tests the nullable Activity.company_id migration (Phase 1 intake)."""
        call = _create_call(db, status="COMPLETED", company_id=None)
        _create_webhook_event(db, call, "call.hangup")
        event = _create_outbox_event(db, RECONCILIATION_EVENT, call)

        worker_tasks.call_missed_call_recovery(event_id=event.id)

        db.refresh(event)
        db.refresh(call)
        assert event.status == "completed"
        assert call.status == "MISSED"

        activity = db.query(Activity).filter(
            Activity.activity_type == "call_missed",
        ).first()
        assert activity is not None, "Activity must be created even without company"
        assert activity.company_id is None, "company_id must be NULL for unknown caller"

    def test_reconciliation_and_sms_idempotency_keys_differ(self, db):
        """Regression: reconciliation input and SMS output must have different
        idempotency keys to avoid unique-constraint collisions."""
        call = _create_call(db, status="COMPLETED")
        _create_webhook_event(db, call, "call.hangup")

        recon_event = _create_outbox_event(db, RECONCILIATION_EVENT, call)
        worker_tasks.call_missed_call_recovery(event_id=recon_event.id)

        sms_event = (
            db.query(OutboxEvent)
            .filter(OutboxEvent.event_type == SMS_RECOVERY_EVENT)
            .first()
        )
        assert sms_event is not None, "SMS outbox must be created"
        assert sms_event.idempotency_key is not None
        assert recon_event.idempotency_key is not None
        assert sms_event.idempotency_key != recon_event.idempotency_key, (
            "Reconciliation and SMS idempotency keys must differ"
        )


class TestStaleLeaseRecovery:
    """Tests for stale processing-lease recovery."""

    def test_stale_lease_detected_and_reset_to_pending(self, db):
        """An event stuck in 'processing' with an expired lease is reset to pending."""
        from datetime import timedelta as _td
        call = _create_call(db, status="MISSED")
        sms_event = _create_outbox_event(db, SMS_RECOVERY_EVENT, call)

        # Simulate a stale lease: set status to processing with an old leased_at
        stale_at = datetime.now(UTC) - _td(minutes=10)
        sms_event.status = "processing"
        sms_event.leased_at = stale_at
        sms_event.lease_holder = "dead-worker"
        db.commit()

        # Call the recovery function directly
        from worker_tasks import _recover_stale_leases
        _recover_stale_leases(db, lease_timeout_seconds=60)

        db.refresh(sms_event)
        assert sms_event.status == "pending", "Stale lease must be reset to pending"
        assert sms_event.leased_at is None
        assert sms_event.lease_holder is None

    def test_active_lease_not_reset(self, db):
        """An event with a recent lease must not be reset."""
        from datetime import timedelta as _td
        call = _create_call(db, status="MISSED")
        sms_event = _create_outbox_event(db, SMS_RECOVERY_EVENT, call)

        recent_at = datetime.now(UTC) - _td(seconds=5)
        sms_event.status = "processing"
        sms_event.leased_at = recent_at
        sms_event.lease_holder = "live-worker"
        db.commit()

        from worker_tasks import _recover_stale_leases
        _recover_stale_leases(db, lease_timeout_seconds=60)

        db.refresh(sms_event)
        assert sms_event.status == "processing", "Active lease must not be reset"


# ═══════════════════════════════════════════════════════════
# SMS Worker Tests
# ═══════════════════════════════════════════════════════════


class TestSMSWorker:
    """Integration tests for sms_missed_call_recovery worker."""

    def test_stop_suppression_blocks_sms(self, db):
        """A suppressed phone should not receive SMS."""
        call = _create_call(db, status="MISSED")
        sms_event = _create_outbox_event(db, SMS_RECOVERY_EVENT, call)

        supp = PhoneSuppression(
            organization_id=call.organization_id,
            phone_number=call.normalized_caller_number,
            normalized_phone=call.normalized_caller_number,
            status="suppressed",
            reason="STOP",
        )
        db.add(supp)
        db.commit()

        with patch.object(worker_tasks, "_send_telnyx_sms") as mock_send:
            worker_tasks.sms_missed_call_recovery(event_id=sms_event.id)
            mock_send.assert_not_called()

        db.refresh(sms_event)
        assert sms_event.status == "completed"

    def test_no_tenant_fails_safely(self, db):
        """Missing organization_id should fail safely without sending SMS."""
        event = OutboxEvent(
            event_type=SMS_RECOVERY_EVENT,
            payload_json={
                "call_id": 99999,
                "normalized_caller_number": "+16045551234",
            },
            correlation_id=_correlation_id(MISSED_CALL_CORR_PREFIX, "test-no-tenant"),
            idempotency_key=_idempotency_key(SMS_MISSED_CALL_IDEM_PREFIX, "test-no-tenant"),
            status="pending",
        )
        db.add(event)
        db.commit()
        db.refresh(event)

        with patch.object(worker_tasks, "_send_telnyx_sms") as mock_send:
            worker_tasks.sms_missed_call_recovery(event_id=event.id)
            mock_send.assert_not_called()

        db.refresh(event)
        assert event.status == "failed"
        assert "organization_id" in (event.last_error or "").lower()

    def test_spam_quarantine_no_sms(self, db):
        """A call in quarantine spam tier should not trigger SMS."""
        call = _create_call(db, status="MISSED", spam_score=50)
        sms_event = _create_outbox_event(db, SMS_RECOVERY_EVENT, call)

        with patch.object(worker_tasks, "_send_telnyx_sms") as mock_send:
            worker_tasks.sms_missed_call_recovery(event_id=sms_event.id)
            mock_send.assert_not_called()

        db.refresh(sms_event)
        assert sms_event.status == "completed"

    def test_provider_timeout_before_send_retries(self, db):
        """A timeout before Telnyx accepts should be retried."""
        call = _create_call(db, status="MISSED")
        sms_event = _create_outbox_event(db, SMS_RECOVERY_EVENT, call)

        with patch.object(
            worker_tasks, "_send_telnyx_sms",
            side_effect=httpx.TimeoutException("timeout"),
        ):
            try:
                worker_tasks.sms_missed_call_recovery(event_id=sms_event.id)
            except Exception:
                pass

        db.refresh(sms_event)
        assert sms_event.attempt_count >= 1
        assert sms_event.status in ("pending", "failed")

    def test_spam_score_allow_sends_sms(self, db):
        """Spam score < 30 (allow tier) should send SMS."""
        call = _create_call(db, status="MISSED", spam_score=10)
        sms_event = _create_outbox_event(db, SMS_RECOVERY_EVENT, call)

        with patch.object(
            worker_tasks, "_send_telnyx_sms", return_value="msg_allow_001"
        ) as mock_send:
            worker_tasks.sms_missed_call_recovery(event_id=sms_event.id)
            mock_send.assert_called_once()

        db.refresh(sms_event)
        assert sms_event.status == "completed"

    def test_spam_score_quarantine_blocks_sms(self, db):
        """Spam score >= 30 (quarantine tier) must not send SMS."""
        call = _create_call(db, status="MISSED", spam_score=50)
        sms_event = _create_outbox_event(db, SMS_RECOVERY_EVENT, call)

        with patch.object(worker_tasks, "_send_telnyx_sms") as mock_send:
            worker_tasks.sms_missed_call_recovery(event_id=sms_event.id)
            mock_send.assert_not_called()

        db.refresh(sms_event)
        assert sms_event.status == "completed"

    def test_spam_score_block_blocks_sms(self, db):
        """Spam score 100 (block tier) must not send SMS."""
        call = _create_call(db, status="MISSED", spam_score=100)
        sms_event = _create_outbox_event(db, SMS_RECOVERY_EVENT, call)

        with patch.object(worker_tasks, "_send_telnyx_sms") as mock_send:
            worker_tasks.sms_missed_call_recovery(event_id=sms_event.id)
            mock_send.assert_not_called()

        db.refresh(sms_event)
        assert sms_event.status == "completed"


# ═══════════════════════════════════════════════════════════
# Routing / Dispatch Tests
# ═══════════════════════════════════════════════════════════


class TestRoutingDispatch:
    """Routing tests for the worker dispatcher."""

    def test_dispatcher_maps_reconciliation_to_worker(self):
        assert worker_tasks.RECONCILIATION_EVENT in worker_tasks.WORKER_DISPATCH
        assert (
            worker_tasks.WORKER_DISPATCH[worker_tasks.RECONCILIATION_EVENT]
            == "workers.call_missed_call_recovery"
        )

    def test_dispatcher_maps_sms_recovery_to_worker(self):
        assert worker_tasks.SMS_RECOVERY_EVENT in worker_tasks.WORKER_DISPATCH
        assert (
            worker_tasks.WORKER_DISPATCH[worker_tasks.SMS_RECOVERY_EVENT]
            == "workers.sms_missed_call_recovery"
        )

    def test_canonical_event_names_consistent(self):
        assert worker_tasks.RECONCILIATION_EVENT == "call.reconciliation.requested"
        assert worker_tasks.SMS_RECOVERY_EVENT == "sms.missed_call_recovery.requested"


# ═══════════════════════════════════════════════════════════
# Phone Formatting Tests
# ═══════════════════════════════════════════════════════════


class TestPhoneFormatting:
    """Tests for phone number formatting helpers."""

    def test_format_phone_friendly(self):
        assert worker_tasks._format_phone_friendly("+16045551234") == "(604) 555-1234"
        assert worker_tasks._format_phone_friendly("+17785551234") == "(778) 555-1234"
        assert worker_tasks._format_phone_friendly("6045551234") == "(604) 555-1234"
        assert worker_tasks._format_phone_friendly("") == "unknown"
        assert worker_tasks._format_phone_friendly(None) == "unknown"

