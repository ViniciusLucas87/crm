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
from app.domain.sales.repositories import ActivityRepository, ContactRepository, OpportunityRepository, TaskRepository


class ContactService:
    def __init__(self, repository: ContactRepository) -> None:
        self._repo = repository

    def create(self, data: ContactCreate, organization_id: int) -> ContactRead:
        return self._repo.create(data, organization_id)

    def list(self, organization_id: int, company_id: int, page: int, page_size: int, search: str | None) -> ContactListResponse:
        return self._repo.list(organization_id=organization_id, company_id=company_id, page=page, page_size=page_size, search=search)

    def get(self, contact_id: int, organization_id: int) -> ContactRead:
        return self._repo.get(contact_id, organization_id)

    def update(self, contact_id: int, data: ContactUpdate, organization_id: int) -> ContactRead:
        return self._repo.update(contact_id, data, organization_id)

    def delete(self, contact_id: int, organization_id: int) -> ContactRead:
        return self._repo.delete(contact_id, organization_id)


class ActivityService:
    def __init__(self, repository: ActivityRepository) -> None:
        self._repo = repository

    def create(self, data: ActivityCreate, organization_id: int) -> ActivityRead:
        return self._repo.create(data, organization_id)

    def list(self, organization_id: int, company_id: int | None, page: int, page_size: int, activity_type: str | None) -> ActivityListResponse:
        return self._repo.list(organization_id=organization_id, company_id=company_id, page=page, page_size=page_size, activity_type=activity_type)

    def get(self, activity_id: int, organization_id: int) -> ActivityRead:
        return self._repo.get(activity_id, organization_id)

    def update(self, activity_id: int, data: ActivityUpdate, organization_id: int) -> ActivityRead:
        return self._repo.update(activity_id, data, organization_id)


class TaskService:
    def __init__(self, repository: TaskRepository) -> None:
        self._repo = repository

    def create(self, data: TaskCreate, organization_id: int) -> TaskRead:
        return self._repo.create(data, organization_id)

    def list(self, organization_id: int, company_id: int | None, page: int, page_size: int, status: str | None, priority: str | None) -> TaskListResponse:
        return self._repo.list(organization_id=organization_id, company_id=company_id, page=page, page_size=page_size, status=status, priority=priority)

    def get(self, task_id: int, organization_id: int) -> TaskRead:
        return self._repo.get(task_id, organization_id)

    def update(self, task_id: int, data: TaskUpdate, organization_id: int) -> TaskRead:
        return self._repo.update(task_id, data, organization_id)


class OpportunityService:
    def __init__(self, repository: OpportunityRepository) -> None:
        self._repo = repository

    def create(self, data: OpportunityCreate, organization_id: int) -> OpportunityRead:
        return self._repo.create(data, organization_id)

    def list(self, organization_id: int, company_id: int | None, page: int, page_size: int, stage: str | None) -> OpportunityListResponse:
        return self._repo.list(organization_id=organization_id, company_id=company_id, page=page, page_size=page_size, stage=stage)

    def get(self, opportunity_id: int, organization_id: int) -> OpportunityRead:
        return self._repo.get(opportunity_id, organization_id)

    def update(self, opportunity_id: int, data: OpportunityUpdate, organization_id: int) -> OpportunityRead:
        return self._repo.update(opportunity_id, data, organization_id)
