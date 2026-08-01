from typing import Protocol

from app.domain.dashboard.entities import DashboardSummary


class DashboardRepository(Protocol):
    def get_summary(self, organization_id: int) -> DashboardSummary: ...
