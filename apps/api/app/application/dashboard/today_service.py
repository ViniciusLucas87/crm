"""Today workspace service — aggregates attention items across the CRM.

All queries are organization-scoped.  Lookups use the authenticated
organization_id, never cross-tenant.  Activity creation includes durable
audit records.
"""

import logging
import re as _re
import uuid
from datetime import date, datetime, UTC, timedelta

from sqlalchemy.orm import Session

from app.domain.dashboard.today_entities import (
    TodayLeadItem,
    TodayMissedCallItem,
    TodayReplyItem,
    TodayTaskItem,
    TodayWorkspaceResponse,
    FollowUpRequest,
    FollowUpResponse,
)
from app.infrastructure.db.models import (
    Activity,
    Call,
    Company,
    Contact,
    EmailMessage,
    Lead,
    Task,
)

logger = logging.getLogger(__name__)
_TOMORROW = date.today() + timedelta(days=1)


class TodayService:
    """Aggregates everything that needs attention in a tenant's workspace."""

    def __init__(self, db: Session, organization_id: int) -> None:
        self._db = db
        self._org_id = organization_id
        self._today = date.today()

    def get_workspace(self) -> TodayWorkspaceResponse:
        return TodayWorkspaceResponse(
            assessment_leads=self._get_assessment_leads(),
            missed_calls=self._get_missed_calls(),
            inbound_replies=self._get_inbound_replies(),
            overdue_follow_ups=self._get_overdue(),
            due_today=self._get_due_today(),
            upcoming=self._get_upcoming(),
            leads_no_next_action=self._get_leads_no_next_action(),
        )

    # ── Assessment Leads ──

    def _get_assessment_leads(self) -> list[TodayLeadItem]:
        leads = (
            self._db.query(Lead)
            .filter(
                Lead.organization_id == self._org_id,
                Lead.status.in_(["new", "ready_for_review"]),
            )
            .order_by(Lead.created_at.desc())
            .limit(20)
            .all()
        )
        return [
            TodayLeadItem(
                id=l.id,
                lead_id=l.id,
                name=l.name or "",
                company_name=l.name or "",
                industry=l.industry,
                opportunity_score=l.opportunity_score or 0,
                status=l.status or "new",
                created_at=l.created_at,
                owner_user_id=l.owner_user_id,
                reason="Ready for review" if l.status == "ready_for_review" else "New assessment submitted",
            )
            for l in leads
        ]

    # ── Missed Calls ──

    def _get_missed_calls(self) -> list[TodayMissedCallItem]:
        calls = (
            self._db.query(Call)
            .filter(
                Call.organization_id == self._org_id,
                Call.status == "MISSED",
                Call.sms_status != "suppressed",
            )
            .order_by(Call.ended_at.desc().nullslast())
            .limit(20)
            .all()
        )
        items = []
        for c in calls:
            caller_display = self._format_phone(c.normalized_caller_number or c.phone_number or "")
            company_name = None
            contact_name = None
            if c.company_id:
                company = self._db.query(Company).filter(
                    Company.id == c.company_id, Company.organization_id == self._org_id
                ).first()
                company_name = company.name if company else None
            if c.contact_id:
                contact = self._db.query(Contact).filter(
                    Contact.id == c.contact_id, Contact.organization_id == self._org_id
                ).first()
                contact_name = f"{contact.first_name} {contact.last_name}".strip() if contact else None
            recovery = (
                self._db.query(Task)
                .filter(
                    Task.recovery_key == f"missed_call_{c.public_uuid}",
                    Task.organization_id == self._org_id,
                )
                .first()
            )
            items.append(
                TodayMissedCallItem(
                    id=c.id,
                    call_uuid=c.public_uuid or "",
                    caller_number=c.normalized_caller_number or c.phone_number or "",
                    caller_display=caller_display,
                    called_at=c.ended_at or c.started_at or c.created_at,
                    spam_score=c.spam_score,
                    company_id=c.company_id,
                    company_name=company_name,
                    contact_id=c.contact_id,
                    contact_name=contact_name,
                    recovery_task_id=recovery.id if recovery else None,
                    reason="Missed inbound call — needs callback",
                )
            )
        return items

    # ── Inbound Replies ──

    def _get_inbound_replies(self) -> list[TodayReplyItem]:
        emails = (
            self._db.query(EmailMessage)
            .filter(
                EmailMessage.organization_id == self._org_id,
                EmailMessage.direction == "inbound",
                EmailMessage.status.in_(["received", "unread"]),
            )
            .order_by(EmailMessage.received_at.desc().nullslast())
            .limit(20)
            .all()
        )
        items = []
        for e in emails:
            company_name = None
            contact_name = None
            if e.company_id:
                company = self._db.query(Company).filter(Company.id == e.company_id).first()
                company_name = company.name if company else None
            items.append(
                TodayReplyItem(
                    id=e.id,
                    email_uuid=e.public_uuid or "",
                    from_address=e.from_address or "",
                    subject=e.subject,
                    received_at=e.received_at or e.created_at,
                    company_id=e.company_id,
                    company_name=company_name,
                    reason=(
                        "New Upwork message notification — open Upwork to respond"
                        if e.channel == "upwork"
                        else "New inbound reply — needs response"
                    ),
                )
            )
        return items

    # ── Tasks ──

    def _base_task_query(self):
        return (
            self._db.query(Task)
            .filter(
                Task.organization_id == self._org_id,
                Task.is_completed.is_(False),
            )
        )

    def _get_overdue(self) -> list[TodayTaskItem]:
        tasks = (
            self._base_task_query()
            .filter(Task.due_date < self._today)
            .order_by(Task.due_date.asc(), Task.priority == "high")
            .limit(30)
            .all()
        )
        return [self._task_to_item(t, "Overdue") for t in tasks]

    def _get_due_today(self) -> list[TodayTaskItem]:
        tasks = (
            self._base_task_query()
            .filter(Task.due_date == self._today)
            .order_by(Task.priority == "high")
            .limit(30)
            .all()
        )
        return [self._task_to_item(t, "Due today") for t in tasks]

    def _get_upcoming(self) -> list[TodayTaskItem]:
        tasks = (
            self._base_task_query()
            .filter(Task.due_date > self._today)
            .order_by(Task.due_date.asc())
            .limit(30)
            .all()
        )
        return [self._task_to_item(t, "Upcoming") for t in tasks]

    def _get_leads_no_next_action(self) -> list[TodayTaskItem]:
        """Leads with no open task.  Uses the recovery_key pattern
        (f'lead_next_step_{lead_id}') to detect existing follow-ups."""
        leads = (
            self._db.query(Lead)
            .filter(
                Lead.organization_id == self._org_id,
                Lead.status.in_(["new", "ready_for_review", "approved"]),
            )
            .all()
        )
        items = []
        for lead in leads:
            key = f"lead_next_step_{lead.id}"
            existing = (
                self._db.query(Task)
                .filter(
                    Task.organization_id == self._org_id,
                    Task.recovery_key == key,
                    Task.is_completed.is_(False),
                )
                .first()
            )
            if existing is not None:
                continue
            items.append(
                TodayTaskItem(
                    id=0,
                    lead_id=lead.id,
                    title=f"Review lead: {lead.name or 'Untitled'}",
                    priority="medium",
                    status="open",
                    due_date=self._today,
                    company_name=lead.name or "",
                    reason="No next action",
                    source="lead",
                )
            )
        return items[:20]

    def _task_to_item(self, task: Task, reason: str) -> TodayTaskItem:
        company_name = self._lookup_company_name(task.company_id)
        contact_name = self._lookup_contact_name(task.contact_id)
        contact_email = None
        contact_phone = None
        if task.contact_id:
            contact = (
                self._db.query(Contact)
                .filter(Contact.id == task.contact_id, Contact.organization_id == self._org_id)
                .first()
            )
            if contact:
                contact_email = contact.email
                contact_phone = contact.phone or contact.mobile
        return TodayTaskItem(
            id=task.id,
            lead_id=task.lead_id,
            title=task.title,
            description=task.description,
            priority=task.priority or "medium",
            status=task.status or "open",
            due_date=task.due_date,
            is_completed=task.is_completed,
            source=task.source,
            company_id=task.company_id,
            company_name=company_name,
            contact_id=task.contact_id,
            contact_name=contact_name,
            contact_email=contact_email,
            contact_phone=contact_phone,
            owner_user_id=task.owner_user_id,
            reason=reason,
        )

    # ── Follow-up Actions ──

    def complete_follow_up(self, task_id: int, request: FollowUpRequest, actor_user_id: str | None = None) -> FollowUpResponse:
        """Complete a follow-up task. Requires next_step_title or terminal_outcome.
        Records a FollowUpAction audit entry."""
        task = self._get_task(task_id)
        if task is None:
            raise ValueError("Task not found")
        if task.is_completed:
            return FollowUpResponse(task_id=task_id, action="completed",
                                    message="Task was already completed")
        idem_key = request.idempotency_key or f"complete_{task_id}_{uuid.uuid4().hex[:12]}"
        if self._follow_up_action_exists(idem_key):
            return FollowUpResponse(task_id=task_id, action="completed",
                                    message="Task was already completed (replay)")
        if not request.next_step_title and not request.terminal_outcome:
            raise ValueError(
                "Please provide a next step title or select a terminal outcome "
                "(won, lost, disqualified, or archived) to close this follow up."
            )

        old_state = f"status={task.status},due_date={task.due_date}"
        task.is_completed = True
        task.status = "completed"
        if actor_user_id:
            task.owner_user_id = actor_user_id

        activity = Activity(
            organization_id=self._org_id, company_id=task.company_id,
            contact_id=task.contact_id, activity_type="follow_up",
            subject=f"Completed: {task.title}",
            body=request.notes or f"Task '{task.title}' completed.",
            completed_at=datetime.now(UTC),
        )
        self._db.add(activity)
        self._db.flush()

        next_task_id = None
        new_state = f"status=completed,terminal={request.terminal_outcome}"
        if request.next_step_title:
            next_task = Task(
                organization_id=self._org_id, company_id=task.company_id,
                contact_id=task.contact_id, title=request.next_step_title,
                priority=request.next_step_priority or "medium", status="open",
                due_date=request.next_step_due_date or (date.today() + timedelta(days=1)),
                source="follow_up", owner_user_id=actor_user_id,
            )
            self._db.add(next_task)
            self._db.flush()
            next_task_id = next_task.id
            new_state += f",next_task_id={next_task_id}"

        self._record_follow_up_action("task", task.id, "completed", old_state, new_state,
                                       request.notes, actor_user_id,
                                       request.idempotency_key or f"complete_{task_id}_{uuid.uuid4().hex[:12]}")
        self._db.commit()
        msg = "Task completed"
        if next_task_id:
            msg += " and next step created"
        if request.terminal_outcome:
            msg += f" — outcome: {request.terminal_outcome}"
        return FollowUpResponse(task_id=task_id, action="completed",
                                activity_id=activity.id, next_task_id=next_task_id, message=msg)

    def reschedule_follow_up(self, task_id: int, request: FollowUpRequest, actor_user_id: str | None = None) -> FollowUpResponse:
        task = self._get_task(task_id)
        if task is None:
            raise ValueError("Task not found")
        if not request.new_due_date:
            raise ValueError("A new due date is required to reschedule")
        idem_key = request.idempotency_key or f"reschedule_{task_id}_{uuid.uuid4().hex[:12]}"
        if self._follow_up_action_exists(idem_key):
            return FollowUpResponse(task_id=task_id, action="rescheduled",
                                    message="Already rescheduled (replay)")
        old_state = f"status={task.status},due_date={task.due_date}"
        old_date = task.due_date
        task.due_date = request.new_due_date
        if actor_user_id:
            task.owner_user_id = actor_user_id
        new_state = f"status={task.status},due_date={task.due_date}"
        activity = Activity(
            organization_id=self._org_id, company_id=task.company_id,
            contact_id=task.contact_id, activity_type="follow_up",
            subject=f"Rescheduled: {task.title}",
            body=f"Moved from {old_date} to {request.new_due_date}. {request.notes or ''}".strip(),
        )
        self._db.add(activity)
        self._db.flush()
        self._record_follow_up_action("task", task.id, "rescheduled", old_state, new_state,
                                       request.notes, actor_user_id,
                                       request.idempotency_key or f"reschedule_{task_id}_{uuid.uuid4().hex[:12]}")
        self._db.commit()
        return FollowUpResponse(task_id=task_id, action="rescheduled",
                                activity_id=activity.id,
                                message=f"Rescheduled to {request.new_due_date}")

    def assign_next_step(self, lead_id: int, request: FollowUpRequest, actor_user_id: str | None = None) -> FollowUpResponse:
        lead = self._db.query(Lead).filter(
            Lead.id == lead_id, Lead.organization_id == self._org_id
        ).first()
        if lead is None:
            raise ValueError("Lead not found")
        dedup_key = f"lead_next_step_{lead_id}"
        existing = self._db.query(Task).filter(
            Task.organization_id == self._org_id, Task.recovery_key == dedup_key,
            Task.is_completed.is_(False),
        ).first()
        if existing is not None:
            return FollowUpResponse(task_id=existing.id, action="assign_next_step",
                                    message="A follow up task already exists for this lead")
        idem_key = request.idempotency_key or f"assign_{lead_id}_{uuid.uuid4().hex[:12]}"
        if self._follow_up_action_exists(idem_key):
            return FollowUpResponse(task_id=0, action="assign_next_step",
                                    message="Already assigned (replay)")
        if actor_user_id and not lead.owner_user_id:
            lead.owner_user_id = actor_user_id
        task = Task(
            organization_id=self._org_id, lead_id=lead.id,
            title=request.next_step_title or f"Follow up with {lead.name or 'this lead'}",
            priority=request.next_step_priority or "medium", status="open",
            due_date=request.next_step_due_date or _TOMORROW,
            source="lead_follow_up", recovery_key=dedup_key, owner_user_id=actor_user_id,
        )
        self._db.add(task)
        self._db.flush()
        activity = Activity(
            organization_id=self._org_id, activity_type="follow_up",
            subject=f"Next step: {task.title}",
            body=request.notes or f"Follow up created for lead {lead.name}.",
        )
        self._db.add(activity)
        self._db.flush()
        self._record_follow_up_action("lead", lead.id, "assigned", "",
                                       f"task_id={task.id}", request.notes,
                                       actor_user_id,
                                       request.idempotency_key or f"assign_{lead_id}_{uuid.uuid4().hex[:12]}")
        self._db.commit()
        return FollowUpResponse(task_id=task.id, action="assign_next_step",
                                activity_id=activity.id, message="Next step assigned")

    @staticmethod
    def _format_phone(number: str) -> str:
        if not number:
            return "Unknown"
        import re
        digits = re.sub(r"\D", "", number)
        if len(digits) == 11 and digits.startswith("1"):
            return f"({digits[1:4]}) {digits[4:7]}-{digits[7:11]}"
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:10]}"
        return number

    def _get_task(self, task_id: int) -> Task | None:
        return self._db.query(Task).filter(
            Task.id == task_id, Task.organization_id == self._org_id
        ).first()

    def _record_follow_up_action(self, entity_type, entity_id, action, old_state, new_state,
                                  notes, actor_user_id, idempotency_key):
        from app.infrastructure.db.models import FollowUpAction
        existing = self._db.query(FollowUpAction).filter(
            FollowUpAction.idempotency_key == idempotency_key,
            FollowUpAction.organization_id == self._org_id,
        ).first()
        if existing is not None:
            return
        fa = FollowUpAction(
            organization_id=self._org_id, actor_user_id=actor_user_id,
            idempotency_key=idempotency_key, entity_type=entity_type,
            entity_id=entity_id, action=action, old_state=old_state or "",
            new_state=new_state or "", notes=notes or "",
        )
        self._db.add(fa)

    def _follow_up_action_exists(self, idempotency_key: str) -> bool:
        from app.infrastructure.db.models import FollowUpAction
        return self._db.query(FollowUpAction).filter(
            FollowUpAction.idempotency_key == idempotency_key,
            FollowUpAction.organization_id == self._org_id,
        ).first() is not None

    def acknowledge_reply(self, email_id: int) -> dict:
        """Mark an inbound reply as handled so it leaves the Today queue."""
        email = self._db.query(EmailMessage).filter(
            EmailMessage.id == email_id, EmailMessage.organization_id == self._org_id
        ).first()
        if email is None:
            raise ValueError("Email not found")
        email.status = "responded"
        self._db.commit()
        return {"id": email_id, "status": "responded"}

    def _lookup_company_name(self, company_id: int | None) -> str | None:
        if company_id is None:
            return None
        c = self._db.query(Company).filter(
            Company.id == company_id, Company.organization_id == self._org_id
        ).first()
        return c.name if c else None

    def _lookup_contact_name(self, contact_id: int | None) -> str | None:
        if contact_id is None:
            return None
        c = self._db.query(Contact).filter(
            Contact.id == contact_id, Contact.organization_id == self._org_id
        ).first()
        return f"{c.first_name} {c.last_name}".strip() if c else None
