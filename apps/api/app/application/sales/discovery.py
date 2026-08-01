from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.infrastructure.db.models import Company


class ProspectDiscovery:
    def __init__(self, session: Session) -> None:
        self._session = session

    def search(self, organization_id: int, *, industry: str | None = None, city: str | None = None, province: str | None = None, country: str | None = None, min_employees: int | None = None, max_employees: int | None = None, business_type: str | None = None, keyword: str | None = None, research_status: str | None = None, min_score: int | None = None, page: int = 1, page_size: int = 20):
        q = select(Company).where(Company.organization_id == organization_id, Company.is_archived.is_(False))

        if industry:
            q = q.where(Company.industry.ilike(f"%{industry}%"))
        if city:
            q = q.where(Company.city.ilike(f"%{city}%"))
        if province:
            q = q.where(Company.province.ilike(f"%{province}%"))
        if country:
            q = q.where(Company.country.ilike(f"%{country}%"))
        if min_employees is not None:
            q = q.where(Company.employees >= min_employees)
        if max_employees is not None:
            q = q.where(Company.employees <= max_employees)
        if business_type:
            q = q.where(Company.business_type.ilike(f"%{business_type}%"))
        if keyword:
            pattern = f"%{keyword}%"
            q = q.where(or_(Company.name.ilike(pattern), Company.description.ilike(pattern), Company.business_categories.ilike(pattern)))
        if research_status:
            q = q.where(Company.research_status == research_status)
        if min_score is not None:
            q = q.where(Company.opportunity_score >= min_score)

        total = self._session.execute(select(func.count()).select_from(q.subquery())).scalar_one()
        rows = self._session.execute(q.order_by(Company.opportunity_score.desc().nullslast()).offset((page - 1) * page_size).limit(page_size)).scalars().all()

        return {
            "items": [
                {
                    "id": c.id, "name": c.name, "industry": c.industry, "city": c.city, "province": c.province,
                    "employees": c.employees, "website": c.website, "opportunity_score": c.opportunity_score,
                    "research_status": c.research_status, "business_type": c.business_type,
                }
                for c in rows
            ],
            "total": total, "page": page, "page_size": page_size,
        }


class ResearchQueueService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_queue(self, organization_id: int):
        q = select(Company).where(
            Company.organization_id == organization_id,
            Company.is_archived.is_(False),
            Company.research_status.in_(["pending", "in_progress"]),
        ).order_by(Company.research_status == "in_progress", Company.opportunity_score.desc().nullslast())

        rows = self._session.execute(q.limit(20)).scalars().all()
        return {
            "items": [
                {"id": c.id, "name": c.name, "industry": c.industry, "research_status": c.research_status,
                 "opportunity_score": c.opportunity_score, "website": c.website,
                 "missing": [f for f in ["description", "employees", "industry", "contacts"] if not getattr(c, f, None)]}
                for c in rows
            ],
            "total": len(rows),
        }

    def mark_researched(self, company_id: int, organization_id: int):
        from datetime import UTC, datetime
        c = self._session.execute(select(Company).where(Company.id == company_id, Company.organization_id == organization_id)).scalar_one()
        c.research_status = "researched"
        c.research_date = datetime.now(UTC)
        c.confidence_score = 80
        self._session.add(c)
        self._session.commit()
        return {"status": "ok"}
