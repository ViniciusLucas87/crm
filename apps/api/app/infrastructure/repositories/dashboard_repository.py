from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.dashboard.entities import DashboardSummary
from app.infrastructure.db.models import (
    Activity,
    Company,
    Opportunity,
    Task,
)


class SqlDashboardRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_summary(self, organization_id: int) -> DashboardSummary:
        today = date.today()

        tasks_today = self._session.execute(
            select(func.count(Task.id)).where(
                Task.organization_id == organization_id,
                Task.due_date <= today,
                Task.is_completed.is_(False),
            )
        ).scalar_one()
        companies = self._session.execute(
            select(func.count(Company.id)).where(
                Company.organization_id == organization_id,
                Company.is_archived.is_(False),
            )
        ).scalar_one()
        active_opportunities = self._session.execute(
            select(func.count(Opportunity.id)).where(
                Opportunity.organization_id == organization_id,
                Opportunity.status == "active",
            )
        ).scalar_one()
        meetings = self._session.execute(
            select(func.count(Activity.id)).where(
                Activity.organization_id == organization_id,
                Activity.activity_type == "meeting",
                Activity.due_date == today,
            )
        ).scalar_one()
        pipeline_value = self._session.execute(
            select(func.coalesce(func.sum(Opportunity.estimated_value), 0)).where(
                Opportunity.organization_id == organization_id,
                Opportunity.status == "active"
            )
        ).scalar_one()
        won_deals = self._session.execute(
            select(func.count(Opportunity.id)).where(
                Opportunity.organization_id == organization_id,
                Opportunity.stage == "won",
            )
        ).scalar_one()
        revenue_forecast = self._session.execute(
            select(func.coalesce(func.sum(Opportunity.estimated_value), 0)).where(
                Opportunity.organization_id == organization_id,
                Opportunity.status == "active"
            )
        ).scalar_one()
        activities_due_today = self._session.execute(
            select(func.count(Activity.id)).where(
                Activity.organization_id == organization_id,
                Activity.due_date == today,
            )
        ).scalar_one()

        return DashboardSummary(
            tasks_today=int(tasks_today),
            companies=int(companies),
            active_opportunities=int(active_opportunities),
            meetings=int(meetings),
            pipeline_value=int(pipeline_value),
            won_deals=int(won_deals),
            revenue_forecast=int(revenue_forecast),
            activities_due_today=int(activities_due_today),
        )
