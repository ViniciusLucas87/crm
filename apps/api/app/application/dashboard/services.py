from app.domain.dashboard.entities import DashboardSummary
from app.domain.dashboard.repositories import DashboardRepository


class DashboardService:
    def __init__(self, repository: DashboardRepository) -> None:
        self._repository = repository

    def get_summary(self, organization_id: int) -> DashboardSummary:
        return self._repository.get_summary(organization_id)
