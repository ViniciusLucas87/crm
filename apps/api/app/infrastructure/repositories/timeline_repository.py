from datetime import datetime

from sqlalchemy import func, literal, select, text, union_all
from sqlalchemy.orm import Session

from app.domain.sales.timeline import TimelineEvent, TimelineResponse
from app.infrastructure.db.models import Activity, Company, Contact, Opportunity, Task


class SqlTimelineRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_timeline(self, *, organization_id: int, company_id: int | None = None, page: int = 1, page_size: int = 30) -> TimelineResponse:
        # Base columns each subquery must return: id, event_type, entity_type, entity_id, title, description, company_id, company_name, occurred_at

        company_events = (
            select(
                Company.id.label("id"),
                literal("company_created").label("event_type"),
                literal("company").label("entity_type"),
                Company.id.label("entity_id"),
                func.concat("Created company").label("title"),
                Company.name.label("description"),
                Company.id.label("company_id"),
                Company.name.label("company_name"),
                Company.created_at.label("occurred_at"),
            )
            .where(Company.organization_id == organization_id)
        )

        contact_events = (
            select(
                Contact.id.label("id"),
                literal("contact_added").label("event_type"),
                literal("contact").label("entity_type"),
                Contact.id.label("entity_id"),
                func.concat("Added contact").label("title"),
                func.concat(Contact.first_name, " ", Contact.last_name).label("description"),
                Contact.company_id.label("company_id"),
                literal(None).label("company_name"),
                Contact.created_at.label("occurred_at"),
            )
            .where(Contact.organization_id == organization_id)
        )

        activity_events = (
            select(
                Activity.id.label("id"),
                func.concat("activity_", Activity.activity_type).label("event_type"),
                literal("activity").label("entity_type"),
                Activity.id.label("entity_id"),
                func.concat(
                    text("CASE activity_type WHEN 'call' THEN 'Phone call' WHEN 'email' THEN 'Email sent' WHEN 'meeting' THEN 'Meeting' WHEN 'note' THEN 'Note added' ELSE 'Activity' END")
                ).label("title"),
                Activity.subject.label("description"),
                Activity.company_id.label("company_id"),
                literal(None).label("company_name"),
                Activity.created_at.label("occurred_at"),
            )
            .where(Activity.organization_id == organization_id)
        )

        task_events = (
            select(
                Task.id.label("id"),
                literal("task_created").label("event_type"),
                literal("task").label("entity_type"),
                Task.id.label("entity_id"),
                func.concat("Task: ", Task.title).label("title"),
                literal(None).label("description"),
                Task.company_id.label("company_id"),
                literal(None).label("company_name"),
                Task.created_at.label("occurred_at"),
            )
            .where(Task.organization_id == organization_id)
        )

        opportunity_events = (
            select(
                Opportunity.id.label("id"),
                literal("opportunity_created").label("event_type"),
                literal("opportunity").label("entity_type"),
                Opportunity.id.label("entity_id"),
                func.concat("Opportunity: ", Opportunity.title).label("title"),
                literal(None).label("description"),
                Opportunity.company_id.label("company_id"),
                literal(None).label("company_name"),
                Opportunity.created_at.label("occurred_at"),
            )
            .where(Opportunity.organization_id == organization_id)
        )

        all_events = union_all(company_events, contact_events, activity_events, task_events, opportunity_events).alias("events")

        q = select(all_events)
        if company_id is not None:
            q = q.where(all_events.c.company_id == company_id)

        total = self._session.execute(select(func.count()).select_from(q.subquery())).scalar_one()

        rows = self._session.execute(
            select(all_events).order_by(all_events.c.occurred_at.desc()).offset((page - 1) * page_size).limit(page_size)
        ).all()

        items = [
            TimelineEvent(
                id=row.id,
                event_type=row.event_type,
                entity_type=row.entity_type,
                entity_id=row.entity_id,
                title=row.title,
                description=row.description,
                company_id=row.company_id,
                company_name=row.company_name,
                occurred_at=row.occurred_at,
            )
            for row in rows
        ]

        return TimelineResponse(items=items, total=total, page=page, page_size=page_size)
