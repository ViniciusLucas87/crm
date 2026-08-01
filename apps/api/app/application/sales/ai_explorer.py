"""
AI Opportunity Explorer Engine.

Natural language search across companies for opportunities.
Results explain WHY they match the query.
"""

from typing import Any

from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.infrastructure.db.models import Company, Contact


class ExplorerResult(BaseModel):
    company_id: int
    company_name: str
    industry: str | None
    employees: int | None
    opportunity_score: int | None
    match_reasons: list[str]


class ExplorerResponse(BaseModel):
    query: str
    interpreted_as: str
    results: list[ExplorerResult]
    total: int
    suggestion: str | None = None


class OpportunityExplorerEngine:
    def __init__(self, session: Session, organization_id: int) -> None:
        self._session = session
        self._org_id = organization_id

    def search(self, query: str) -> ExplorerResponse:
        query_lower = query.lower().strip()
        base = select(Company).where(Company.organization_id == self._org_id, Company.is_archived == False)

        # Interpret the query
        interpreted, filters, sort_col = self._interpret(query_lower)

        # Apply filters
        stmt = base
        for f in filters:
            stmt = stmt.where(f)
        if sort_col is not None:
            stmt = stmt.order_by(sort_col.desc().nullslast())
        stmt = stmt.limit(20)

        companies = self._session.execute(stmt).scalars().all()
        results = [self._to_result(c, query_lower) for c in companies]

        suggestion = None
        if not results:
            suggestion = "Try: 'construction companies', 'high score', 'no contacts', 'growing fast', or 'needs inspection'"

        return ExplorerResponse(
            query=query,
            interpreted_as=interpreted,
            results=results,
            total=len(results),
            suggestion=suggestion,
        )

    def _interpret(self, q: str) -> tuple[str, list[Any], Any]:
        filters: list[Any] = []
        sort_col = Company.opportunity_score

        # Industry keywords
        industries: dict[str, str] = {
            "construction": "construction", "property": "property", "engineering": "engineering",
            "manufacturing": "manufacturing", "architecture": "architecture",
        }
        matched_industry = None
        for kw, ind in industries.items():
            if kw in q:
                filters.append(Company.industry.ilike(f"%{ind}%"))
                matched_industry = ind
                break

        # Score-related
        if any(w in q for w in ["high score", "top score", "best score", "highest score"]):
            filters.append(Company.opportunity_score >= 70)
            sort_col = Company.opportunity_score
        elif any(w in q for w in ["score", "scored"]):
            sort_col = Company.opportunity_score

        # Contact-related
        if any(w in q for w in ["no contact", "no contacts", "without contact"]):
            subq = select(Contact.company_id).where(Contact.status == "active")
            filters.append(~Company.id.in_(subq))

        # Size-related
        if any(w in q for w in ["growing", "growth", "large", "big"]):
            filters.append(Company.employees >= 50)
            sort_col = Company.employees
        if any(w in q for w in ["small"]):
            filters.append(Company.employees < 20)

        # Service-related
        if any(w in q for w in ["inspection", "inspections"]):
            filters.append(Company.industry.ilike("%construction%"))
        if any(w in q for w in ["document", "automation", "documents"]):
            filters.append(or_(Company.industry.ilike("%engineering%"), Company.industry.ilike("%property%")))
        if any(w in q for w in ["portal", "client"]):
            filters.append(or_(Company.industry.ilike("%property%"), Company.industry.ilike("%architecture%")))

        # Website-related
        if any(w in q for w in ["outdated website", "no website", "website"]):
            filters.append(or_(Company.website.is_(None), Company.website == ""))

        # Research-related
        if any(w in q for w in ["research", "not researched", "unresearched"]):
            filters.append(or_(Company.research_status.is_(None), Company.research_status == "pending"))

        # Description
        interpreted_parts: list[str] = []
        if matched_industry: interpreted_parts.append(f"Industry: {matched_industry}")
        else: interpreted_parts.append("All industries")
        interpreted = " · ".join(interpreted_parts) if interpreted_parts else "General search"

        return interpreted, filters, sort_col

    def _to_result(self, c: Company, q: str) -> ExplorerResult:
        reasons: list[str] = []

        if "construction" in q and c.industry and "construction" in c.industry.lower():
            reasons.append(f"Construction industry match")
        if "property" in q and c.industry and "property" in c.industry.lower():
            reasons.append(f"Property management industry match")
        if any(w in q for w in ["high score"]) and c.opportunity_score and c.opportunity_score >= 70:
            reasons.append(f"Opportunity Score: {c.opportunity_score}/100")
        if any(w in q for w in ["no contact"]) and c.opportunity_score:
            reasons.append("No contacts on file — untapped prospect")
        if any(w in q for w in ["growing"]) and c.employees and c.employees >= 50:
            reasons.append(f"Large workforce: ~{c.employees} employees")
        if c.opportunity_score:
            reasons.append(f"Opportunity Score: {c.opportunity_score}/100")
        if c.industry:
            reasons.append(f"Industry: {c.industry}")

        return ExplorerResult(
            company_id=c.id,
            company_name=c.name,
            industry=c.industry,
            employees=c.employees,
            opportunity_score=c.opportunity_score,
            match_reasons=reasons[:5],
        )
