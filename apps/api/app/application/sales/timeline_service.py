from app.domain.sales.timeline import TimelineResponse
from app.infrastructure.repositories.timeline_repository import SqlTimelineRepository


class TimelineService:
    def __init__(self, repository: SqlTimelineRepository) -> None:
        self._repo = repository

    def get_timeline(self, organization_id: int, company_id: int | None = None, page: int = 1, page_size: int = 30) -> TimelineResponse:
        return self._repo.get_timeline(organization_id=organization_id, company_id=company_id, page=page, page_size=page_size)
