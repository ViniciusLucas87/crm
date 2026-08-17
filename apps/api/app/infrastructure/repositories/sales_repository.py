from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.domain.sales.entities import (
    ActivityCreate,
    ActivityListResponse,
    ActivityRead,
    ActivityUpdate,
    ContactCreate,
    ContactListResponse,
    ContactRead,
    ContactUpdate,
    OpportunityCreate,
    OpportunityListResponse,
    OpportunityRead,
    OpportunityUpdate,
    TaskCreate,
    TaskListResponse,
    TaskRead,
    TaskUpdate,
)
from app.infrastructure.db.models import Activity, Contact, Opportunity, Task


class SqlContactRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, data: ContactCreate, organization_id: int) -> ContactRead:
        contact = Contact(organization_id=organization_id, **data.model_dump())
        self._session.add(contact)
        self._session.commit()
        self._session.refresh(contact)
        return ContactRead.model_validate(contact)

    def list(self, *, organization_id: int, company_id: int, page: int, page_size: int, search: str | None) -> ContactListResponse:
        q = select(Contact).where(Contact.organization_id == organization_id, Contact.company_id == company_id)
        if search:
            pattern = f"%{search}%"
            q = q.where(or_(Contact.first_name.ilike(pattern), Contact.last_name.ilike(pattern), Contact.email.ilike(pattern)))
        total = self._session.execute(select(func.count()).select_from(q.subquery())).scalar_one()
        rows = self._session.execute(q.order_by(Contact.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).scalars().all()
        return ContactListResponse(items=[ContactRead.model_validate(r) for r in rows], total=total, page=page, page_size=page_size)

    def get(self, contact_id: int, organization_id: int) -> ContactRead:
        row = self._session.execute(select(Contact).where(Contact.id == contact_id, Contact.organization_id == organization_id)).scalar_one()
        return ContactRead.model_validate(row)

    def update(self, contact_id: int, data: ContactUpdate, organization_id: int) -> ContactRead:
        row = self._session.execute(select(Contact).where(Contact.id == contact_id, Contact.organization_id == organization_id)).scalar_one()
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(row, k, v)
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        return ContactRead.model_validate(row)

    def delete(self, contact_id: int, organization_id: int) -> ContactRead:
        row = self._session.execute(select(Contact).where(Contact.id == contact_id, Contact.organization_id == organization_id)).scalar_one()
        row.status = "archived"
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        return ContactRead.model_validate(row)


class SqlActivityRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, data: ActivityCreate, organization_id: int) -> ActivityRead:
        from app.infrastructure.db.models import Conversation

        act = Activity(organization_id=organization_id, **data.model_dump())
        conversation = self._session.execute(
            select(Conversation).where(
                Conversation.organization_id == organization_id,
                Conversation.company_id == data.company_id,
                Conversation.status == "active",
            ).order_by(Conversation.updated_at.desc())
        ).scalars().first()
        if conversation:
            act.conversation_id = conversation.id
            conversation.last_activity_at = datetime.now(UTC)
            if (
                conversation.relationship_stage == "new"
                and data.activity_type in {"call", "email", "meeting"}
            ):
                conversation.relationship_stage = "contacted"
        self._session.add(act)
        self._session.commit()
        self._session.refresh(act)
        return ActivityRead.model_validate(act)

    def list(self, *, organization_id: int, company_id: int | None, page: int, page_size: int, activity_type: str | None) -> ActivityListResponse:
        q = select(Activity).where(Activity.organization_id == organization_id)
        if company_id is not None:
            q = q.where(Activity.company_id == company_id)
        if activity_type:
            q = q.where(Activity.activity_type == activity_type)
        total = self._session.execute(select(func.count()).select_from(q.subquery())).scalar_one()
        rows = self._session.execute(q.order_by(Activity.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).scalars().all()
        return ActivityListResponse(items=[ActivityRead.model_validate(r) for r in rows], total=total, page=page, page_size=page_size)

    def get(self, activity_id: int, organization_id: int) -> ActivityRead:
        row = self._session.execute(select(Activity).where(Activity.id == activity_id, Activity.organization_id == organization_id)).scalar_one()
        return ActivityRead.model_validate(row)

    def update(self, activity_id: int, data: ActivityUpdate, organization_id: int) -> ActivityRead:
        row = self._session.execute(select(Activity).where(Activity.id == activity_id, Activity.organization_id == organization_id)).scalar_one()
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(row, k, v)
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        return ActivityRead.model_validate(row)


class SqlTaskRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, data: TaskCreate, organization_id: int) -> TaskRead:
        task = Task(organization_id=organization_id, **data.model_dump())
        self._session.add(task)
        self._session.commit()
        self._session.refresh(task)
        return TaskRead.model_validate(task)

    def list(self, *, organization_id: int, company_id: int | None, page: int, page_size: int, status: str | None, priority: str | None) -> TaskListResponse:
        q = select(Task).where(Task.organization_id == organization_id)
        if company_id is not None:
            q = q.where(Task.company_id == company_id)
        if status:
            q = q.where(Task.status == status)
        if priority:
            q = q.where(Task.priority == priority)
        total = self._session.execute(select(func.count()).select_from(q.subquery())).scalar_one()
        rows = self._session.execute(q.order_by(Task.due_date.asc()).offset((page - 1) * page_size).limit(page_size)).scalars().all()
        return TaskListResponse(items=[TaskRead.model_validate(r) for r in rows], total=total, page=page, page_size=page_size)

    def get(self, task_id: int, organization_id: int) -> TaskRead:
        row = self._session.execute(select(Task).where(Task.id == task_id, Task.organization_id == organization_id)).scalar_one()
        return TaskRead.model_validate(row)

    def update(self, task_id: int, data: TaskUpdate, organization_id: int) -> TaskRead:
        row = self._session.execute(select(Task).where(Task.id == task_id, Task.organization_id == organization_id)).scalar_one()
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(row, k, v)
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        return TaskRead.model_validate(row)


class SqlOpportunityRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, data: OpportunityCreate, organization_id: int) -> OpportunityRead:
        opp = Opportunity(organization_id=organization_id, **data.model_dump())
        self._session.add(opp)
        self._session.commit()
        self._session.refresh(opp)
        return OpportunityRead.model_validate(opp)

    def list(self, *, organization_id: int, company_id: int | None, page: int, page_size: int, stage: str | None) -> OpportunityListResponse:
        q = select(Opportunity).where(Opportunity.organization_id == organization_id)
        if company_id is not None:
            q = q.where(Opportunity.company_id == company_id)
        if stage:
            q = q.where(Opportunity.stage == stage)
        total = self._session.execute(select(func.count()).select_from(q.subquery())).scalar_one()
        rows = self._session.execute(q.order_by(Opportunity.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).scalars().all()
        return OpportunityListResponse(items=[OpportunityRead.model_validate(r) for r in rows], total=total, page=page, page_size=page_size)

    def get(self, opportunity_id: int, organization_id: int) -> OpportunityRead:
        row = self._session.execute(select(Opportunity).where(Opportunity.id == opportunity_id, Opportunity.organization_id == organization_id)).scalar_one()
        return OpportunityRead.model_validate(row)

    def update(self, opportunity_id: int, data: OpportunityUpdate, organization_id: int) -> OpportunityRead:
        row = self._session.execute(select(Opportunity).where(Opportunity.id == opportunity_id, Opportunity.organization_id == organization_id)).scalar_one()
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(row, k, v)
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        return OpportunityRead.model_validate(row)
