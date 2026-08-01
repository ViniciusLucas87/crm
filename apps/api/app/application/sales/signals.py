from datetime import date, datetime, timedelta

from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.infrastructure.db.models import Activity, Company, Contact, Opportunity


class Signal(BaseModel):
    signal: str
    reason: str
    confidence: int  # 0-100
    suggested_opportunity: str | None = None
    suggested_solution: str | None = None


class CompanySignals(BaseModel):
    company_id: int
    company_name: str
    opportunity_score: int
    signals: list[Signal]


class SignalResponse(BaseModel):
    companies: list[CompanySignals]
    total_with_signals: int


class BuyingSignalEngine:
    def __init__(self, session: Session) -> None:
        self._session = session

    def detect(self, organization_id: int, min_score: int = 50) -> SignalResponse:
        companies = self._session.execute(
            select(Company).where(Company.organization_id == organization_id, Company.is_archived.is_(False))
        ).scalars().all()

        results: list[CompanySignals] = []

        for company in companies:
            signals: list[Signal] = []
            score = 50  # Base score

            # Signal: Has website but no description → needs research
            if company.website and not company.description:
                signals.append(Signal(
                    signal="Incomplete profile",
                    reason="Company has a website but no business description.",
                    confidence=70,
                    suggested_opportunity="Website analysis opportunity",
                    suggested_solution="Research company website for services and pain points",
                ))
                score += 5

            # Signal: Has no contacts → needs outreach
            contact_count = self._session.execute(
                select(func.count(Contact.id)).where(Contact.company_id == company.id)
            ).scalar_one()
            if contact_count == 0:
                signals.append(Signal(
                    signal="No contacts",
                    reason="No decision makers identified. Cannot begin outreach.",
                    confidence=85,
                    suggested_opportunity="Add decision maker",
                    suggested_solution="Research LinkedIn for key contacts",
                ))
                score -= 10

            # Signal: Has employees but no description → growth indicator
            if company.employees and company.employees > 50 and not company.description:
                signals.append(Signal(
                    signal="Growing company",
                    reason=f"Company has {company.employees} employees — potential for automation needs.",
                    confidence=65,
                    suggested_opportunity="Automation assessment",
                    suggested_solution="Pitch workflow automation",
                ))
                score += 10

            # Signal: Has website, no tech stack → discovery opportunity
            if company.website and not company.tech_stack:
                signals.append(Signal(
                    signal="Technology unknown",
                    reason="Website present but technology stack not analyzed.",
                    confidence=60,
                    suggested_opportunity="Tech stack discovery",
                    suggested_solution="Analyze website for technology indicators",
                ))
                score += 5

            # Signal: Recent activity → engaged prospect
            recent = self._session.execute(
                select(func.max(Activity.created_at)).where(Activity.company_id == company.id)
            ).scalar_one_or_none()
            if recent and recent > datetime.now(UTC) - timedelta(days=7):
                signals.append(Signal(
                    signal="Recently active",
                    reason="Activity logged within the last 7 days — engaged prospect.",
                    confidence=80,
                ))
                score += 15

            # Signal: Active opportunity → high-value
            active_opps = self._session.execute(
                select(func.count(Opportunity.id)).where(Opportunity.company_id == company.id, Opportunity.status == "active")
            ).scalar_one()
            if active_opps > 0:
                signals.append(Signal(
                    signal="Active pipeline",
                    reason=f"{active_opps} active opportunity(s) — prioritize relationship.",
                    confidence=90,
                ))
                score += 10

            # Clamp score
            score = max(0, min(100, score))

            if score >= min_score or len(signals) > 0:
                company.opportunity_score = score
                company.buying_signals = ", ".join([s.signal for s in signals])
                self._session.add(company)
                results.append(CompanySignals(
                    company_id=company.id,
                    company_name=company.name,
                    opportunity_score=score,
                    signals=signals,
                ))

        self._session.commit()
        return SignalResponse(companies=results, total_with_signals=len(results))
