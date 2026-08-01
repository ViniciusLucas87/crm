from datetime import date, timedelta

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.infrastructure.db.models import Activity, Company, Contact, Opportunity, Task


class ActionRecommendation(BaseModel):
    id: str
    title: str
    description: str
    priority: str  # "high", "medium", "low"
    action_type: str  # "follow_up", "add_contact", "create_proposal", "review", "call"
    company_id: int | None = None
    company_name: str | None = None


class ActionResponse(BaseModel):
    recommendations: list[ActionRecommendation]


class ActionEngine:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_recommendations(self, organization_id: int, company_id: int | None = None) -> ActionResponse:
        recs: list[ActionRecommendation] = []

        # Rule: Companies with no activity in 30+ days → follow-up
        thirty_days_ago = date.today() - timedelta(days=30)
        base_q = select(Company).where(Company.organization_id == organization_id, Company.is_archived.is_(False))
        if company_id:
            base_q = base_q.where(Company.id == company_id)

        companies = self._session.execute(base_q).scalars().all()
        for company in companies:
            last_activity = self._session.execute(
                select(func.max(Activity.created_at)).where(Activity.company_id == company.id)
            ).scalar_one_or_none()

            if last_activity is None or last_activity.date() < thirty_days_ago:
                recs.append(ActionRecommendation(
                    id=f"followup-{company.id}",
                    title="No recent activity",
                    description=f"No activity logged for {company.name} in the last 30 days. Schedule a follow-up.",
                    priority="high",
                    action_type="follow_up",
                    company_id=company.id,
                    company_name=company.name,
                ))

            # Rule: No contacts → add decision maker
            contact_count = self._session.execute(
                select(func.count(Contact.id)).where(Contact.company_id == company.id)
            ).scalar_one()
            if contact_count == 0:
                recs.append(ActionRecommendation(
                    id=f"nocontact-{company.id}",
                    title="Add a contact",
                    description=f"{company.name} has no contacts. Add a decision maker to start engaging.",
                    priority="medium",
                    action_type="add_contact",
                    company_id=company.id,
                    company_name=company.name,
                ))

            # Rule: Active opportunities → check progress
            opps = self._session.execute(
                select(Opportunity).where(Opportunity.company_id == company.id, Opportunity.status == "active")
            ).scalars().all()
            for opp in opps:
                if opp.updated_at and opp.updated_at.date() < date.today() - timedelta(days=14):
                    recs.append(ActionRecommendation(
                        id=f"staleopp-{opp.id}",
                        title="Stale opportunity",
                        description=f"Opportunity '{opp.title}' hasn't been updated in 2 weeks. Review progress.",
                        priority="medium",
                        action_type="review",
                        company_id=company.id,
                        company_name=company.name,
                    ))

        return ActionResponse(recommendations=recs[:10])
