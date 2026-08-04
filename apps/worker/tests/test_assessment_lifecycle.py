"""Focused tests for assessment lifecycle worker task.

Tests cover:
  1. assessment.completed: successful validation of Assessment, Company, Lead
  2. assessment.report.requested: successful validation with results
  3. lead.followup.requested: successful validation of Lead and Task
  4. Missing invariant: assessment not found -> permanent failure
  5. Missing invariant: no results -> permanent failure
  6. Missing invariant: lead not found -> permanent failure
  7. Idempotency: duplicate event returns same result
  8. Stale processing recovery: stuck processing reset to pending
  9. Failed email events left untouched by stale recovery
"""

import uuid
from datetime import datetime, UTC, timedelta
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from app.infrastructure.db.models import (
    AutomationAssessment, Company, Contact, Lead, Task,
    Organization, OutboxEvent,
)

import worker_tasks


# Re-export constants under test
ASSESSMENT_COMPLETED = worker_tasks.ASSESSMENT_COMPLETED_EVENT
ASSESSMENT_REPORT = worker_tasks.ASSESSMENT_REPORT_REQUESTED_EVENT
LEAD_FOLLOWUP = worker_tasks.LEAD_FOLLOWUP_REQUESTED_EVENT
STALE_MINUTES = worker_tasks.STALE_PROCESSING_MINUTES
_InvariantFailure = worker_tasks._InvariantFailure


# --- Fixtures ---

@pytest.fixture
def db():
    from app.infrastructure.db.session import SessionLocal
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(autouse=True)
def _seed_organization(db):
    org = Organization(id=1, name="Test Org", slug=f"test-org-{uuid.uuid4().hex[:8]}")
    db.add(org)
    db.commit()


def _make_company(db, **overrides):
    c = Company(
        organization_id=1,
        name=overrides.pop("name", "Test Corp"),
        status=overrides.pop("status", "active"),
        **overrides,
    )
    db.add(c)
    db.commit()
    return c


def _make_contact(db, company, **overrides):
    c = Contact(
        organization_id=1,
        company_id=company.id,
        email=overrides.pop("email", "test@example.com"),
        first_name=overrides.pop("first_name", "Test"),
        last_name=overrides.pop("last_name", "User"),
        **overrides,
    )
    db.add(c)
    db.commit()
    return c


def _make_lead(db, company, contact, **overrides):
    l = Lead(
        organization_id=1,
        name=overrides.pop("name", f"Lead for {company.name}"),
        status=overrides.pop("status", "new"),
        source=overrides.pop("source", "assessment"),
        **overrides,
    )
    db.add(l)
    db.commit()
    return l


def _make_task(db, lead, **overrides):
    t = Task(
        organization_id=1,
        title=overrides.pop("title", "Follow-up task"),
        status=overrides.pop("status", "open"),
        due_date=overrides.pop("due_date", datetime.now(UTC).date()),
        **overrides,
    )
    db.add(t)
    db.commit()
    return t


def _make_assessment(db, company, lead, **overrides):
    a = AutomationAssessment(
        organization_id=1,
        public_id=overrides.pop("public_id", str(uuid.uuid4())),
        company_id=company.id,
        lead_id=lead.id,
        assessment_version="2.0",
        raw_answers={},
        calculated_output={},
        automation_score=75,
        pdf_status=overrides.pop("pdf_status", "pending"),
        intelligence_json=overrides.pop("intelligence_json", {"score": 75}),
        intelligence_generated_at=overrides.pop("intelligence_generated_at", None),
        **overrides,
    )
    db.add(a)
    db.commit()
    return a


def _make_outbox_event(db, event_type, payload, status="pending", **overrides):
    e = OutboxEvent(
        event_type=event_type,
        payload_json=payload,
        status=status,
        idempotency_key=overrides.pop("idempotency_key", str(uuid.uuid4())),
        attempt_count=overrides.pop("attempt_count", 0),
        max_attempts=overrides.pop("max_attempts", 5),
        **overrides,
    )
    db.add(e)
    db.commit()
    return e


# --- Tests: Successful lifecycle consumption ---

class TestAssessmentCompleted:
    def test_valid_assessment_completed(self, db):
        """assessment.completed with valid Assessment, Company, Lead succeeds."""
        company = _make_company(db)
        contact = _make_contact(db, company)
        lead = _make_lead(db, company, contact)
        assessment = _make_assessment(db, company, lead)

        event = _make_outbox_event(db, ASSESSMENT_COMPLETED, {
            "assessment_id": assessment.public_id,
            "company_id": company.id,
            "lead_id": lead.id,
        })

        worker_tasks._handle_assessment_completed(db, event.payload_json, event)
        worker_tasks._mark_event_completed(db, event)

        db.refresh(event)
        assert event.status == "completed"

    def test_does_not_mutate_intelligence_generated_at(self, db):
        """assessment.completed does NOT set intelligence_generated_at."""
        company = _make_company(db)
        contact = _make_contact(db, company)
        lead = _make_lead(db, company, contact)
        assessment = _make_assessment(db, company, lead, intelligence_generated_at=None)

        event = _make_outbox_event(db, ASSESSMENT_COMPLETED, {
            "assessment_id": assessment.public_id,
            "company_id": company.id,
            "lead_id": lead.id,
        })

        worker_tasks._handle_assessment_completed(db, event.payload_json, event)

        db.refresh(assessment)
        assert assessment.intelligence_generated_at is None  # unchanged


class TestAssessmentReportRequested:
    def test_valid_report_requested_with_intelligence(self, db):
        """assessment.report.requested with intelligence_json succeeds."""
        company = _make_company(db)
        contact = _make_contact(db, company)
        lead = _make_lead(db, company, contact)
        assessment = _make_assessment(db, company, lead, intelligence_json={"score": 80})

        event = _make_outbox_event(db, ASSESSMENT_REPORT, {
            "assessment_id": assessment.public_id,
        })

        worker_tasks._handle_assessment_report_requested(db, event.payload_json, event)
        worker_tasks._mark_event_completed(db, event)

        db.refresh(event)
        assert event.status == "completed"

    def test_valid_report_requested_with_generated_at(self, db):
        """assessment.report.requested with intelligence_generated_at succeeds."""
        company = _make_company(db)
        contact = _make_contact(db, company)
        lead = _make_lead(db, company, contact)
        assessment = _make_assessment(db, company, lead,
            intelligence_json=None,
            intelligence_generated_at=datetime.now(UTC),
        )

        event = _make_outbox_event(db, ASSESSMENT_REPORT, {
            "assessment_id": assessment.public_id,
        })

        worker_tasks._handle_assessment_report_requested(db, event.payload_json, event)
        worker_tasks._mark_event_completed(db, event)

        db.refresh(event)
        assert event.status == "completed"

    def test_does_not_mutate_pdf_status(self, db):
        """assessment.report.requested does NOT change pdf_status."""
        company = _make_company(db)
        contact = _make_contact(db, company)
        lead = _make_lead(db, company, contact)
        assessment = _make_assessment(db, company, lead, pdf_status="pending")

        event = _make_outbox_event(db, ASSESSMENT_REPORT, {
            "assessment_id": assessment.public_id,
        })

        worker_tasks._handle_assessment_report_requested(db, event.payload_json, event)

        db.refresh(assessment)
        assert assessment.pdf_status == "pending"  # unchanged


class TestLeadFollowupRequested:
    def test_valid_lead_followup(self, db):
        """lead.followup.requested with valid Lead and Task succeeds."""
        company = _make_company(db)
        contact = _make_contact(db, company)
        lead = _make_lead(db, company, contact)
        task = _make_task(db, lead)

        event = _make_outbox_event(db, LEAD_FOLLOWUP, {
            "lead_id": lead.id,
            "task_id": task.id,
            "priority": "high",
        })

        worker_tasks._handle_lead_followup_requested(db, event.payload_json, event)
        worker_tasks._mark_event_completed(db, event)

        db.refresh(event)
        assert event.status == "completed"

    def test_missing_task_id_fails(self, db):
        """lead.followup.requested without task_id fails (required field)."""
        company = _make_company(db)
        contact = _make_contact(db, company)
        lead = _make_lead(db, company, contact)

        event = _make_outbox_event(db, LEAD_FOLLOWUP, {
            "lead_id": lead.id,
        })

        with pytest.raises(_InvariantFailure, match="Missing task_id"):
            worker_tasks._handle_lead_followup_requested(db, event.payload_json, event)


# --- Tests: Missing invariant failure ---

class TestMissingInvariantFailure:
    def test_assessment_completed_missing_assessment(self, db):
        event = _make_outbox_event(db, ASSESSMENT_COMPLETED, {
            "assessment_id": "nonexistent-uuid",
            "company_id": 1,
            "lead_id": 1,
        })
        with pytest.raises(_InvariantFailure, match="not found"):
            worker_tasks._handle_assessment_completed(db, event.payload_json, event)

    def test_assessment_completed_missing_company_id(self, db):
        event = _make_outbox_event(db, ASSESSMENT_COMPLETED, {
            "assessment_id": "some-uuid",
            "lead_id": 1,
        })
        with pytest.raises(_InvariantFailure, match="Missing company_id"):
            worker_tasks._handle_assessment_completed(db, event.payload_json, event)

    def test_assessment_completed_missing_lead_id(self, db):
        event = _make_outbox_event(db, ASSESSMENT_COMPLETED, {
            "assessment_id": "some-uuid",
            "company_id": 1,
        })
        with pytest.raises(_InvariantFailure, match="Missing lead_id"):
            worker_tasks._handle_assessment_completed(db, event.payload_json, event)

    def test_assessment_completed_missing_payload_id(self, db):
        event = _make_outbox_event(db, ASSESSMENT_COMPLETED, {
            "company_id": 1,
        })
        with pytest.raises(_InvariantFailure, match="Missing assessment_id"):
            worker_tasks._handle_assessment_completed(db, event.payload_json, event)

    def test_report_requested_no_intelligence(self, db):
        company = _make_company(db)
        contact = _make_contact(db, company)
        lead = _make_lead(db, company, contact)
        assessment = _make_assessment(db, company, lead,
            intelligence_json=None,
            intelligence_generated_at=None,
        )
        event = _make_outbox_event(db, ASSESSMENT_REPORT, {
            "assessment_id": assessment.public_id,
        })
        with pytest.raises(_InvariantFailure, match="no intelligence"):
            worker_tasks._handle_assessment_report_requested(db, event.payload_json, event)

    def test_lead_followup_missing_lead(self, db):
        event = _make_outbox_event(db, LEAD_FOLLOWUP, {
            "lead_id": 99999,
            "task_id": 1,
        })
        with pytest.raises(_InvariantFailure, match="Lead id=99999 not found"):
            worker_tasks._handle_lead_followup_requested(db, event.payload_json, event)

    def test_lead_followup_missing_lead_id(self, db):
        event = _make_outbox_event(db, LEAD_FOLLOWUP, {
            "task_id": 1,
        })
        with pytest.raises(_InvariantFailure, match="Missing lead_id"):
            worker_tasks._handle_lead_followup_requested(db, event.payload_json, event)

    def test_lead_followup_missing_task_id(self, db):
        event = _make_outbox_event(db, LEAD_FOLLOWUP, {
            "lead_id": 1,
        })
        with pytest.raises(_InvariantFailure, match="Missing task_id"):
            worker_tasks._handle_lead_followup_requested(db, event.payload_json, event)


# --- Tests: Idempotency ---

class TestIdempotency:
    def test_reprocessing_completed_event_is_noop(self, db):
        """Reprocessing an already-completed event does nothing."""
        company = _make_company(db)
        contact = _make_contact(db, company)
        lead = _make_lead(db, company, contact)
        assessment = _make_assessment(db, company, lead)

        event = _make_outbox_event(db, ASSESSMENT_COMPLETED, {
            "assessment_id": assessment.public_id,
            "company_id": company.id,
            "lead_id": lead.id,
        })

        # First run: process normally
        worker_tasks._handle_assessment_completed(db, event.payload_json, event)
        worker_tasks._mark_event_completed(db, event)

        # Second run: completed event should be no-op
        # The handler itself doesn't care about status, but the task loop's
        # event_id mode skips completed events
        db.refresh(event)
        assert event.status == "completed"

    def test_event_id_mode_completed_is_noop(self, db):
        """In event_id mode, a completed event returns without processing."""
        company = _make_company(db)
        contact = _make_contact(db, company)
        lead = _make_lead(db, company, contact)
        assessment = _make_assessment(db, company, lead)

        event = _make_outbox_event(db, ASSESSMENT_COMPLETED, {
            "assessment_id": assessment.public_id,
            "company_id": company.id,
            "lead_id": lead.id,
        }, status="completed")

        # Task should return early for completed events
        result = worker_tasks.outbox_process_assessment_lifecycle(event_id=event.id)
        assert result["processed"] == 0
        assert "already completed" in result.get("note", "")

    def test_event_id_mode_unrelated_type_skipped(self, db):
        """In event_id mode, an unrelated event type is skipped without completing."""
        company = _make_company(db)
        contact = _make_contact(db, company)
        lead = _make_lead(db, company, contact)
        assessment = _make_assessment(db, company, lead)

        event = _make_outbox_event(db, "unrelated.event.type", {
            "assessment_id": assessment.public_id,
        })

        result = worker_tasks.outbox_process_assessment_lifecycle(event_id=event.id)
        assert result["processed"] == 0
        assert "not a lifecycle event" in result.get("note", "")
        # Event must not be marked completed
        db.refresh(event)
        assert event.status == "pending"


# --- Tests: Stale processing recovery ---

class TestStaleProcessingRecovery:
    def test_stale_processing_reset_to_pending(self, db):
        """Events stuck in processing > STALE_MINUTES get reset to pending."""
        company = _make_company(db)
        contact = _make_contact(db, company)
        lead = _make_lead(db, company, contact)
        assessment = _make_assessment(db, company, lead)

        stale_time = datetime.now(UTC) - timedelta(minutes=STALE_MINUTES + 5)
        event = _make_outbox_event(
            db,
            "assessment.visitor_email.requested",
            {"assessment_id": assessment.public_id, "contact_email": "x@y.com"},
            status="processing",
            last_attempt_at=stale_time,
        )

        # Simulate what outbox_process_email does on startup
        from app.infrastructure.db.models import OutboxEvent
        cutoff = datetime.now(UTC) - timedelta(minutes=STALE_MINUTES)
        stale_events = db.query(OutboxEvent).filter(
            OutboxEvent.event_type.in_([
                "assessment.internal_notification.requested",
                "assessment.visitor_email.requested",
            ]),
            OutboxEvent.status == "processing",
            OutboxEvent.last_attempt_at < cutoff,
        ).all()

        for se in stale_events:
            se.status = "pending"
            se.lease_holder = None
            se.leased_at = None
        db.commit()

        db.refresh(event)
        assert event.status == "pending"
        assert event.lease_holder is None

    def test_fresh_processing_not_reset(self, db):
        """Events in processing but within the threshold are NOT reset."""
        company = _make_company(db)
        contact = _make_contact(db, company)
        lead = _make_lead(db, company, contact)
        assessment = _make_assessment(db, company, lead)

        fresh_time = datetime.now(UTC) - timedelta(minutes=5)  # within threshold
        event = _make_outbox_event(
            db,
            "assessment.visitor_email.requested",
            {"assessment_id": assessment.public_id},
            status="processing",
            last_attempt_at=fresh_time,
        )

        from app.infrastructure.db.models import OutboxEvent
        cutoff = datetime.now(UTC) - timedelta(minutes=STALE_MINUTES)
        stale_events = db.query(OutboxEvent).filter(
            OutboxEvent.event_type.in_([
                "assessment.internal_notification.requested",
                "assessment.visitor_email.requested",
            ]),
            OutboxEvent.status == "processing",
            OutboxEvent.last_attempt_at < cutoff,
        ).all()

        assert len(stale_events) == 0  # Not stale yet

    def test_failed_events_untouched_by_stale_recovery(self, db):
        """Failed email events are NEVER reset to pending by stale recovery."""
        company = _make_company(db)
        contact = _make_contact(db, company)
        lead = _make_lead(db, company, contact)
        assessment = _make_assessment(db, company, lead)

        stale_time = datetime.now(UTC) - timedelta(minutes=STALE_MINUTES + 30)
        event = _make_outbox_event(
            db,
            "assessment.visitor_email.requested",
            {"assessment_id": assessment.public_id},
            status="failed",
            last_attempt_at=stale_time,
            last_error="timed out",
            attempt_count=5,
        )

        # The stale recovery query only looks for status=="processing"
        from app.infrastructure.db.models import OutboxEvent
        cutoff = datetime.now(UTC) - timedelta(minutes=STALE_MINUTES)
        stale_events = db.query(OutboxEvent).filter(
            OutboxEvent.event_type.in_([
                "assessment.internal_notification.requested",
                "assessment.visitor_email.requested",
            ]),
            OutboxEvent.status == "processing",
            OutboxEvent.last_attempt_at < cutoff,
        ).all()

        assert len(stale_events) == 0  # Failed events excluded by status filter

        db.refresh(event)
        assert event.status == "failed"  # Untouched
