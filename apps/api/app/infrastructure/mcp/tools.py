"""
MCP Tools — Complete Tool Suite.

Every tool the LLM can call. Tools are pure business-logic wrappers
that call application services — never repositories, never SQL.

Registered at import time into the global ToolRegistry.
"""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select, or_
from sqlalchemy.orm import Session

from app.application.sales.ai_analysis import CompanyAnalysisEngine
from app.application.sales.ai_brief import DailyBriefEngine
from app.application.sales.ai_meeting import MeetingPrepEngine
from app.application.sales.ai_proposal import ProposalBuilderEngine
from app.application.sales.scoring import ScoringEngine
from app.infrastructure.db.models import Activity, Call, Company, Contact, Lead, Opportunity, Task
from app.infrastructure.mcp.context_builders import CompanyContext
from app.infrastructure.mcp.tool_registry import ToolDefinition, ToolParameter, ToolRegistry, get_registry


# ── Helper ──

def _company_query(session: Session, org_id: int, company_id: int | None = None):
    base = select(Company).where(Company.organization_id == org_id, Company.is_archived == False)
    if company_id is not None:
        base = base.where(Company.id == company_id)
    return base


def _build_company_context(session: Session, c: Company) -> CompanyContext:
    contacts = session.execute(select(Contact).where(Contact.company_id == c.id, Contact.status == "active")).scalars().all()
    activities = session.execute(select(Activity).where(Activity.company_id == c.id).order_by(Activity.created_at.desc()).limit(10)).scalars().all()
    opps = session.execute(select(Opportunity).where(Opportunity.company_id == c.id, Opportunity.stage.notin_(["won", "lost"]))).scalars().all()
    tasks = session.execute(select(Task).where(Task.company_id == c.id, Task.status != "completed")).scalars().all()
    return CompanyContext.from_company(c, contacts, activities, opps, tasks)


# ── Tool Handler Factory ──
# Each handler receives a session+org_id via closure

def make_search_companies(session_factory, org_id: int):
    async def handler(query: str = "", industry: str = "", min_score: int = 0, limit: int = 10):
        session = session_factory()
        try:
            stmt = _company_query(session, org_id)
            if query:
                stmt = stmt.where(Company.name.ilike(f"%{query}%"))
            if industry:
                stmt = stmt.where(Company.industry.ilike(f"%{industry}%"))
            if min_score > 0:
                stmt = stmt.where(Company.opportunity_score >= min_score)
            companies = session.execute(stmt.order_by(Company.opportunity_score.desc().nullslast()).limit(limit)).scalars().all()
            return {
                "total": len(companies),
                "companies": [
                    {"id": c.id, "name": c.name, "industry": c.industry, "opportunity_score": c.opportunity_score, "employees": c.employees, "city": c.city}
                    for c in companies
                ],
            }
        finally:
            session.close()
    return handler


def make_get_company(session_factory, org_id: int):
    async def handler(company_id: int):
        session = session_factory()
        try:
            c = session.execute(_company_query(session, org_id, company_id)).scalar_one_or_none()
            if c is None:
                return {"error": f"Company {company_id} not found."}
            ctx = _build_company_context(session, c)
            return ctx.model_dump()
        finally:
            session.close()
    return handler


def make_list_companies(session_factory, org_id: int):
    async def handler(status: str = "active", limit: int = 20, offset: int = 0):
        session = session_factory()
        try:
            stmt = _company_query(session, org_id)
            if status != "all":
                stmt = stmt.where(Company.status == status)
            companies = session.execute(stmt.order_by(Company.name).offset(offset).limit(limit)).scalars().all()
            total = session.execute(select(func.count(Company.id)).where(Company.organization_id == org_id, Company.is_archived == False)).scalar_one()
            return {
                "total": total,
                "offset": offset,
                "limit": limit,
                "companies": [{"id": c.id, "name": c.name, "industry": c.industry, "status": c.status, "opportunity_score": c.opportunity_score} for c in companies],
            }
        finally:
            session.close()
    return handler


def make_search_contacts(session_factory, org_id: int):
    async def handler(query: str = "", company_id: int | None = None, limit: int = 20):
        session = session_factory()
        try:
            stmt = select(Contact).join(Company).where(Company.organization_id == org_id, Contact.status == "active")
            if query:
                stmt = stmt.where(or_(Contact.first_name.ilike(f"%{query}%"), Contact.last_name.ilike(f"%{query}%"), Contact.email.ilike(f"%{query}%")))
            if company_id:
                stmt = stmt.where(Contact.company_id == company_id)
            contacts = session.execute(stmt.limit(limit)).scalars().all()
            return {
                "total": len(contacts),
                "contacts": [{"id": ct.id, "first_name": ct.first_name, "last_name": ct.last_name, "title": ct.job_title, "email": ct.email, "phone": ct.phone, "company_id": ct.company_id} for ct in contacts],
            }
        finally:
            session.close()
    return handler


def make_list_opportunities(session_factory, org_id: int):
    async def handler(stage: str = "", limit: int = 20):
        session = session_factory()
        try:
            stmt = select(Opportunity, Company).join(Company).where(Opportunity.organization_id == org_id)
            if stage:
                stmt = stmt.where(Opportunity.stage == stage)
            else:
                stmt = stmt.where(Opportunity.stage.notin_(["won", "lost"]))
            rows = session.execute(stmt.order_by(Opportunity.estimated_value.desc().nullslast()).limit(limit)).all()
            return {
                "total": len(rows),
                "opportunities": [
                    {"id": o.id, "title": o.title, "stage": o.stage, "estimated_value": float(o.estimated_value) if o.estimated_value else None, "probability": float(o.probability) if o.probability else None, "company_name": c.name, "company_id": c.id}
                    for o, c in rows
                ],
            }
        finally:
            session.close()
    return handler


def make_recommend_opportunities(session_factory, org_id: int):
    async def handler(min_score: int = 50, limit: int = 10):
        session = session_factory()
        try:
            companies = session.execute(
                select(Company).where(Company.organization_id == org_id, Company.is_archived == False, Company.opportunity_score >= min_score)
                .order_by(Company.opportunity_score.desc().nullslast()).limit(limit)
            ).scalars().all()
            return {
                "recommendation": "Top opportunities ranked by opportunity score",
                "companies": [
                    {"id": c.id, "name": c.name, "industry": c.industry, "opportunity_score": c.opportunity_score, "confidence_score": c.confidence_score, "reason": f"Opportunity Score: {c.opportunity_score}/100. {c.industry or 'Unknown'} industry — aligned with our services."}
                    for c in companies
                ],
            }
        finally:
            session.close()
    return handler


def make_company_timeline(session_factory, org_id: int):
    async def handler(company_id: int, limit: int = 20):
        session = session_factory()
        try:
            c = session.execute(_company_query(session, org_id, company_id)).scalar_one_or_none()
            if c is None:
                return {"error": f"Company {company_id} not found."}
            activities = session.execute(select(Activity).where(Activity.company_id == company_id).order_by(Activity.created_at.desc()).limit(limit)).scalars().all()
            return {
                "company_name": c.name,
                "events": [{"type": a.activity_type, "subject": a.subject, "body": a.body, "date": str(a.created_at)} for a in activities],
                "total": len(activities),
            }
        finally:
            session.close()
    return handler


def make_recent_activity(session_factory, org_id: int):
    async def handler(limit: int = 20):
        session = session_factory()
        try:
            activities = session.execute(
                select(Activity, Company).join(Company).where(Activity.organization_id == org_id).order_by(Activity.created_at.desc()).limit(limit)
            ).all()
            return {
                "activities": [
                    {"type": a.activity_type, "subject": a.subject, "date": str(a.created_at), "company_name": c.name, "company_id": c.id}
                    for a, c in activities
                ],
            }
        finally:
            session.close()
    return handler


def make_company_signals(session_factory, org_id: int):
    async def handler(company_id: int):
        session = session_factory()
        try:
            c = session.execute(_company_query(session, org_id, company_id)).scalar_one_or_none()
            if c is None:
                return {"error": f"Company {company_id} not found."}
            score_result = ScoringEngine(session).score_company(c)
            return {
                "company_name": c.name,
                "opportunity_score": score_result.opportunity_score,
                "confidence_score": score_result.confidence_score,
                "confidence_level": score_result.confidence_level,
                "signals": [b.model_dump() for b in score_result.score_breakdown],
                "recommended_services": score_result.recommended_services,
                "next_action": score_result.next_action,
                "estimated_value": score_result.estimated_value,
            }
        finally:
            session.close()
    return handler


def make_market_signals(session_factory, org_id: int):
    async def handler(limit: int = 10):
        session = session_factory()
        try:
            companies = session.execute(
                select(Company).where(Company.organization_id == org_id, Company.is_archived == False, Company.opportunity_score >= 50)
                .order_by(Company.opportunity_score.desc().nullslast()).limit(limit)
            ).scalars().all()
            return {
                "total_with_signals": len(companies),
                "companies": [
                    {"id": c.id, "name": c.name, "industry": c.industry, "opportunity_score": c.opportunity_score, "employees": c.employees}
                    for c in companies
                ],
            }
        finally:
            session.close()
    return handler


def make_calculate_score(session_factory, org_id: int):
    async def handler(company_id: int):
        session = session_factory()
        try:
            c = session.execute(_company_query(session, org_id, company_id)).scalar_one_or_none()
            if c is None:
                return {"error": f"Company {company_id} not found."}
            result = ScoringEngine(session).score_company(c)
            return result.model_dump()
        finally:
            session.close()
    return handler


def make_explain_score(session_factory, org_id: int):
    async def handler(company_id: int):
        session = session_factory()
        try:
            c = session.execute(_company_query(session, org_id, company_id)).scalar_one_or_none()
            if c is None:
                return {"error": f"Company {company_id} not found."}
            result = ScoringEngine(session).score_company(c)
            return {
                "company_name": c.name,
                "score": result.opportunity_score,
                "confidence": f"{result.confidence_level} ({result.confidence_score}%)",
                "breakdown": [b.model_dump() for b in result.score_breakdown],
                "explanation": f"The score of {result.opportunity_score}/100 is based on {len(result.score_breakdown)} detected signals from CRM data.",
            }
        finally:
            session.close()
    return handler


def make_next_action(session_factory, org_id: int):
    async def handler(company_id: int):
        session = session_factory()
        try:
            c = session.execute(_company_query(session, org_id, company_id)).scalar_one_or_none()
            if c is None:
                return {"error": f"Company {company_id} not found."}
            result = ScoringEngine(session).score_company(c)
            return {
                "company_name": c.name,
                "next_action": result.next_action,
                "reasoning": f"Based on opportunity score ({result.opportunity_score}/100), confidence ({result.confidence_level}), and detected signals.",
                "supporting_data": {
                    "score": result.opportunity_score,
                    "confidence_level": result.confidence_level,
                    "recommended_services": result.recommended_services,
                },
            }
        finally:
            session.close()
    return handler


def make_daily_brief(session_factory, org_id: int):
    async def handler():
        session = session_factory()
        try:
            engine = DailyBriefEngine(session, org_id)
            brief = engine.generate()
            return brief.model_dump()
        finally:
            session.close()
    return handler


def make_proposal_context(session_factory, org_id: int):
    async def handler(company_id: int):
        session = session_factory()
        try:
            c = session.execute(_company_query(session, org_id, company_id)).scalar_one_or_none()
            if c is None:
                return {"error": f"Company {company_id} not found."}
            proposal = ProposalBuilderEngine(session).build(c)
            return proposal.model_dump()
        finally:
            session.close()
    return handler


def make_meeting_context(session_factory, org_id: int):
    async def handler(company_id: int):
        session = session_factory()
        try:
            c = session.execute(_company_query(session, org_id, company_id)).scalar_one_or_none()
            if c is None:
                return {"error": f"Company {company_id} not found."}
            prep = MeetingPrepEngine(session).prepare(c)
            return prep.model_dump()
        finally:
            session.close()
    return handler


def make_list_tasks(session_factory, org_id: int):
    async def handler(status: str = "", limit: int = 20):
        session = session_factory()
        try:
            stmt = select(Task, Company).join(Company).where(Task.organization_id == org_id)
            if status:
                stmt = stmt.where(Task.status == status)
            rows = session.execute(stmt.order_by(Task.due_date.asc().nullslast()).limit(limit)).all()
            return {
                "total": len(rows),
                "tasks": [
                    {"id": t.id, "title": t.title, "priority": t.priority, "status": t.status, "due_date": str(t.due_date) if t.due_date else None, "company_name": c.name, "company_id": c.id}
                    for t, c in rows
                ],
            }
        finally:
            session.close()
    return handler


def make_dashboard_summary(session_factory, org_id: int):
    async def handler():
        session = session_factory()
        try:
            total_companies = session.execute(select(func.count(Company.id)).where(Company.organization_id == org_id, Company.is_archived == False)).scalar_one()
            total_opps = session.execute(select(func.count(Opportunity.id)).where(Opportunity.organization_id == org_id, Opportunity.stage.notin_(["won", "lost"]))).scalar_one()
            pipeline = session.execute(select(func.sum(Opportunity.estimated_value)).where(Opportunity.organization_id == org_id, Opportunity.stage.notin_(["won", "lost"]))).scalar_one() or 0
            won = session.execute(select(func.sum(Opportunity.estimated_value)).where(Opportunity.organization_id == org_id, Opportunity.stage == "won")).scalar_one() or 0
            overdue = session.execute(select(func.count(Task.id)).where(Task.organization_id == org_id, Task.status != "completed", Task.due_date < func.now())).scalar_one()
            return {
                "total_companies": total_companies,
                "total_opportunities": total_opps,
                "pipeline_value": float(pipeline),
                "won_value": float(won),
                "overdue_tasks": overdue,
            }
        finally:
            session.close()
    return handler


def make_company_analysis(session_factory, org_id: int):
    async def handler(company_id: int):
        session = session_factory()
        try:
            c = session.execute(_company_query(session, org_id, company_id)).scalar_one_or_none()
            if c is None:
                return {"error": f"Company {company_id} not found."}
            analysis = CompanyAnalysisEngine(session).analyze(c)
            return analysis.model_dump()
        finally:
            session.close()
    return handler


# ── Compact operational context ──

def make_business_context(session_factory, org_id: int):
    async def handler(task_limit: int = 8, lead_limit: int = 8):
        session = session_factory()
        try:
            now = datetime.now(UTC)
            today = now.date()
            companies = session.execute(
                select(func.count(Company.id)).where(Company.organization_id == org_id, Company.is_archived == False)
            ).scalar_one()
            open_opportunities = session.execute(
                select(func.count(Opportunity.id)).where(
                    Opportunity.organization_id == org_id,
                    Opportunity.stage.notin_(["won", "lost"]),
                )
            ).scalar_one()
            pipeline = session.execute(
                select(func.sum(Opportunity.estimated_value)).where(
                    Opportunity.organization_id == org_id,
                    Opportunity.stage.notin_(["won", "lost"]),
                )
            ).scalar_one() or 0
            tasks = session.execute(
                select(Task)
                .where(Task.organization_id == org_id, Task.is_completed == False)
                .order_by(Task.due_date.asc())
                .limit(max(1, min(task_limit, 25)))
            ).scalars().all()
            leads = session.execute(
                select(Lead)
                .where(Lead.organization_id == org_id, Lead.status.notin_(["archived", "rejected", "converted"]))
                .order_by(Lead.opportunity_score.desc().nullslast())
                .limit(max(1, min(lead_limit, 25)))
            ).scalars().all()
            missed_calls = session.execute(
                select(Call)
                .where(
                    Call.organization_id == org_id,
                    Call.direction == "inbound",
                    Call.status.in_(["missed", "no_answer"]),
                    Call.created_at >= now - timedelta(days=7),
                )
                .order_by(Call.created_at.desc())
                .limit(10)
            ).scalars().all()
            return {
                "generated_at": now.isoformat(),
                "summary": {
                    "companies": companies,
                    "open_opportunities": open_opportunities,
                    "pipeline_value": float(pipeline),
                    "open_tasks": len(tasks),
                    "missed_calls_last_7_days": len(missed_calls),
                },
                "priority_tasks": [
                    {
                        "id": item.id,
                        "title": item.title,
                        "due_date": item.due_date.isoformat(),
                        "overdue": item.due_date < today,
                        "priority": item.priority,
                        "company_id": item.company_id,
                    }
                    for item in tasks
                ],
                "priority_leads": [
                    {
                        "id": item.id,
                        "name": item.name,
                        "industry": item.industry,
                        "city": item.city,
                        "province": item.province,
                        "opportunity_score": item.opportunity_score,
                        "status": item.status,
                    }
                    for item in leads
                ],
                "missed_calls": [
                    {
                        "id": item.id,
                        "phone_number": item.phone_number,
                        "time": (item.started_at or item.created_at).isoformat(),
                        "sms_status": item.sms_status,
                    }
                    for item in missed_calls
                ],
                "usage_note": "Use detail tools only for records needed for the current task.",
            }
        finally:
            session.close()
    return handler


# ── Controlled CRM actions ──

def _company_for_org(session: Session, org_id: int, company_id: int) -> Company | None:
    return session.execute(
        select(Company).where(Company.id == company_id, Company.organization_id == org_id)
    ).scalar_one_or_none()


def make_create_company(session_factory, org_id: int):
    async def handler(name: str, industry: str = "", website: str = "", phone: str = "", email: str = ""):
        session = session_factory()
        try:
            clean_name = name.strip()
            if not clean_name:
                return {"error": "Company name is required."}
            existing = session.execute(
                select(Company).where(Company.organization_id == org_id, func.lower(Company.name) == clean_name.lower())
            ).scalar_one_or_none()
            if existing:
                return {"error": "A company with this name already exists.", "company_id": existing.id}
            company = Company(
                organization_id=org_id,
                name=clean_name,
                industry=industry.strip() or None,
                website=website.strip() or None,
                phone=phone.strip() or None,
                email=email.strip() or None,
                status="active",
            )
            session.add(company)
            session.commit()
            session.refresh(company)
            return {"id": company.id, "name": company.name, "status": company.status}
        finally:
            session.close()
    return handler


def make_create_contact(session_factory, org_id: int):
    async def handler(company_id: int, first_name: str, last_name: str, email: str = "", phone: str = "", title: str = ""):
        session = session_factory()
        try:
            company = _company_for_org(session, org_id, company_id)
            if not company:
                return {"error": "Company not found."}
            contact = Contact(
                organization_id=org_id,
                company_id=company.id,
                first_name=first_name.strip(),
                last_name=last_name.strip(),
                email=email.strip() or None,
                phone=phone.strip() or None,
                job_title=title.strip() or None,
                status="active",
                discovery_source="mcp",
            )
            if not contact.first_name or not contact.last_name:
                return {"error": "First and last name are required."}
            session.add(contact)
            session.commit()
            session.refresh(contact)
            return {"id": contact.id, "company_id": company.id, "name": f"{contact.first_name} {contact.last_name}"}
        finally:
            session.close()
    return handler


def make_add_note(session_factory, org_id: int):
    async def handler(company_id: int, note: str, subject: str = "CRM note"):
        session = session_factory()
        try:
            company = _company_for_org(session, org_id, company_id)
            if not company:
                return {"error": "Company not found."}
            activity = Activity(
                organization_id=org_id,
                company_id=company.id,
                activity_type="note",
                subject=subject.strip()[:255] or "CRM note",
                body=note.strip(),
            )
            if not activity.body:
                return {"error": "Note text is required."}
            session.add(activity)
            session.commit()
            session.refresh(activity)
            return {"id": activity.id, "company_id": company.id, "status": "saved"}
        finally:
            session.close()
    return handler


def make_create_task(session_factory, org_id: int):
    async def handler(title: str, due_date: str, company_id: int | None = None, description: str = "", priority: str = "medium"):
        session = session_factory()
        try:
            if company_id is not None and not _company_for_org(session, org_id, company_id):
                return {"error": "Company not found."}
            try:
                parsed_due_date = date.fromisoformat(due_date)
            except ValueError:
                return {"error": "Due date must use YYYY-MM-DD format."}
            if priority not in {"low", "medium", "high", "urgent"}:
                return {"error": "Priority must be low, medium, high or urgent."}
            task = Task(
                organization_id=org_id,
                company_id=company_id,
                title=title.strip(),
                description=description.strip() or None,
                priority=priority,
                status="open",
                due_date=parsed_due_date,
                is_completed=False,
                source="mcp",
            )
            if not task.title:
                return {"error": "Task title is required."}
            session.add(task)
            session.commit()
            session.refresh(task)
            return {"id": task.id, "title": task.title, "due_date": task.due_date.isoformat(), "status": task.status}
        finally:
            session.close()
    return handler


def make_complete_task(session_factory, org_id: int):
    async def handler(task_id: int):
        session = session_factory()
        try:
            task = session.execute(
                select(Task).where(Task.id == task_id, Task.organization_id == org_id)
            ).scalar_one_or_none()
            if not task:
                return {"error": "Task not found."}
            task.status = "completed"
            task.is_completed = True
            session.commit()
            return {"id": task.id, "status": "completed"}
        finally:
            session.close()
    return handler


def make_create_opportunity(session_factory, org_id: int):
    async def handler(company_id: int, title: str, estimated_value: float = 0, probability: int = 50, stage: str = "lead"):
        session = session_factory()
        try:
            company = _company_for_org(session, org_id, company_id)
            if not company:
                return {"error": "Company not found."}
            if probability < 0 or probability > 100:
                return {"error": "Probability must be between 0 and 100."}
            if stage not in {"lead", "qualified", "proposal", "negotiation", "won", "lost"}:
                return {"error": "Unsupported opportunity stage."}
            opportunity = Opportunity(
                organization_id=org_id,
                company_id=company.id,
                title=title.strip(),
                estimated_value=Decimal(str(max(0, estimated_value))),
                probability=probability,
                stage=stage,
                status="active",
            )
            if not opportunity.title:
                return {"error": "Opportunity title is required."}
            session.add(opportunity)
            session.commit()
            session.refresh(opportunity)
            return {"id": opportunity.id, "company_id": company.id, "title": opportunity.title, "stage": opportunity.stage}
        finally:
            session.close()
    return handler


# ── Service Catalog & Knowledge ──

SERVICE_CATALOG = {
    "custom_crm": {"name": "Custom CRM", "description": "Tailored CRM solution for your business processes", "typical_timeline": "2-4 months", "tier": "Professional"},
    "client_portal": {"name": "Client Portal", "description": "Secure client communication and document sharing", "typical_timeline": "1-2 months", "tier": "Essentials"},
    "inspection_platform": {"name": "Inspection Platform", "description": "Mobile field inspection and reporting system", "typical_timeline": "3-5 months", "tier": "Enterprise"},
    "document_automation": {"name": "Document Automation", "description": "Automated document generation and workflow", "typical_timeline": "1-3 months", "tier": "Professional"},
    "workflow_automation": {"name": "Workflow Automation", "description": "Custom business process automation", "typical_timeline": "2-4 months", "tier": "Professional"},
    "operations_dashboard": {"name": "Operations Dashboard", "description": "Real-time KPI and operations monitoring", "typical_timeline": "1-2 months", "tier": "Essentials"},
    "reporting_system": {"name": "Reporting System", "description": "Advanced analytics and reporting platform", "typical_timeline": "2-3 months", "tier": "Professional"},
    "mobile_workforce": {"name": "Mobile Workforce App", "description": "Field team management and communication app", "typical_timeline": "3-4 months", "tier": "Enterprise"},
    "business_intelligence": {"name": "Business Intelligence", "description": "AI-powered insights and forecasting", "typical_timeline": "2-3 months", "tier": "Enterprise"},
}

PRICING_TIERS = {
    "Essentials": {"setup_range": "$5,000–$10,000", "monthly_range": "$400–$800", "ideal_for": "Small teams (1-20 employees)"},
    "Professional": {"setup_range": "$10,000–$25,000", "monthly_range": "$800–$2,000", "ideal_for": "Mid-size companies (20-100 employees)"},
    "Enterprise": {"setup_range": "$25,000–$50,000", "monthly_range": "$2,000–$5,000", "ideal_for": "Large organizations (100+ employees)"},
}


def make_service_catalog():
    async def handler(category: str = ""):
        if category and category in SERVICE_CATALOG:
            return {"service": SERVICE_CATALOG[category]}
        return {"services": [{"id": k, **v} for k, v in SERVICE_CATALOG.items()]}
    return handler


def make_pricing_reference():
    async def handler(tier: str = ""):
        if tier and tier in PRICING_TIERS:
            return {"tier": tier, **PRICING_TIERS[tier]}
        return {"pricing_tiers": [{"tier": k, **v} for k, v in PRICING_TIERS.items()]}
    return handler


def make_knowledge_search():
    async def handler(query: str = ""):
        q = query.lower()
        results: list[dict[str, Any]] = []
        for k, v in SERVICE_CATALOG.items():
            if q in v["name"].lower() or q in v["description"].lower():
                results.append({"type": "service", "id": k, **v})
        for k, v in PRICING_TIERS.items():
            if q in k.lower() or q in v["ideal_for"].lower():
                results.append({"type": "pricing", "tier": k, **v})
        from app.application.sales.ai_knowledge import KnowledgeBaseArchitecture
        for item in KnowledgeBaseArchitecture.PLAYBOOK:
            searchable = f'{item["category"]} {item["title"]} {item["summary"]} {item["content"]}'.lower()
            if not q or q in searchable:
                results.append({"type": "playbook", **item})
        return {"query": query, "results": results, "total": len(results)}
    return handler


# ── Register All Tools ──

def register_all_tools(session_factory, org_id: int, registry: ToolRegistry | None = None) -> ToolRegistry:
    """Register organization-scoped MCP tools into an isolated registry."""
    registry = registry or get_registry()

    tools: list[ToolDefinition] = [
        # Company
        ToolDefinition("search_companies", "Search for companies by name, industry, or minimum opportunity score.", "company", [
            ToolParameter("query", "string", "Search term for company name (partial match)"), ToolParameter("industry", "string", "Filter by industry"), ToolParameter("min_score", "integer", "Minimum opportunity score (0-100)"), ToolParameter("limit", "integer", "Max results", False, 10),
        ], make_search_companies(session_factory, org_id)),
        ToolDefinition("get_company", "Get detailed company information including contacts, activities, opportunities, and tasks.", "company", [
            ToolParameter("company_id", "integer", "Company ID", True),
        ], make_get_company(session_factory, org_id)),
        ToolDefinition("list_companies", "List companies with pagination.", "company", [
            ToolParameter("status", "string", "Filter by status", False, "active"), ToolParameter("limit", "integer", "Max results", False, 20), ToolParameter("offset", "integer", "Pagination offset", False, 0),
        ], make_list_companies(session_factory, org_id)),

        # Contacts
        ToolDefinition("search_contacts", "Search contacts by name, email, or company.", "contact", [
            ToolParameter("query", "string", "Search term"), ToolParameter("company_id", "integer", "Filter by company"), ToolParameter("limit", "integer", "Max results", False, 20),
        ], make_search_contacts(session_factory, org_id)),

        # Opportunities
        ToolDefinition("list_opportunities", "List open opportunities with company info.", "opportunity", [
            ToolParameter("stage", "string", "Filter by stage"), ToolParameter("limit", "integer", "Max results", False, 20),
        ], make_list_opportunities(session_factory, org_id)),
        ToolDefinition("recommend_opportunities", "Recommend top opportunities based on opportunity scores.", "opportunity", [
            ToolParameter("min_score", "integer", "Minimum score", False, 50), ToolParameter("limit", "integer", "Max results", False, 10),
        ], make_recommend_opportunities(session_factory, org_id)),

        # Timeline
        ToolDefinition("company_timeline", "Get company activity timeline.", "timeline", [
            ToolParameter("company_id", "integer", "Company ID", True), ToolParameter("limit", "integer", "Max events", False, 20),
        ], make_company_timeline(session_factory, org_id)),
        ToolDefinition("recent_activity", "Get recent activity across all companies.", "timeline", [
            ToolParameter("limit", "integer", "Max results", False, 20),
        ], make_recent_activity(session_factory, org_id)),

        # Signals & Scoring
        ToolDefinition("company_signals", "Get buying signals and opportunity score for a company.", "signals", [
            ToolParameter("company_id", "integer", "Company ID", True),
        ], make_company_signals(session_factory, org_id)),
        ToolDefinition("market_signals", "Get companies with active buying signals across the market.", "signals", [
            ToolParameter("limit", "integer", "Max results", False, 10),
        ], make_market_signals(session_factory, org_id)),
        ToolDefinition("calculate_score", "Calculate the opportunity score for a company with full breakdown.", "scoring", [
            ToolParameter("company_id", "integer", "Company ID", True),
        ], make_calculate_score(session_factory, org_id)),
        ToolDefinition("explain_score", "Explain why a company received its opportunity score.", "scoring", [
            ToolParameter("company_id", "integer", "Company ID", True),
        ], make_explain_score(session_factory, org_id)),

        # Actions
        ToolDefinition("next_action", "Get the recommended next action for a company.", "actions", [
            ToolParameter("company_id", "integer", "Company ID", True),
        ], make_next_action(session_factory, org_id)),
        ToolDefinition("daily_brief", "Generate today's AI-powered daily briefing with priorities, signals, and actions.", "actions", [], make_daily_brief(session_factory, org_id)),

        # Proposal & Meeting
        ToolDefinition("proposal_context", "Generate a proposal draft for a company using CRM context.", "proposal", [
            ToolParameter("company_id", "integer", "Company ID", True),
        ], make_proposal_context(session_factory, org_id)),
        ToolDefinition("meeting_context", "Generate meeting preparation materials for a company.", "meeting", [
            ToolParameter("company_id", "integer", "Company ID", True),
        ], make_meeting_context(session_factory, org_id)),

        # Tasks
        ToolDefinition("list_tasks", "List tasks with optional status filter.", "tasks", [
            ToolParameter("status", "string", "Filter by status"), ToolParameter("limit", "integer", "Max results", False, 20),
        ], make_list_tasks(session_factory, org_id)),

        # Dashboard
        ToolDefinition("dashboard_summary", "Get high-level dashboard KPIs.", "dashboard", [], make_dashboard_summary(session_factory, org_id)),
        ToolDefinition("business_context", "Get a compact current CRM briefing with priorities, pipeline, leads, tasks and missed calls. Start here for most CRM work.", "context", [
            ToolParameter("task_limit", "integer", "Maximum priority tasks", False, 8),
            ToolParameter("lead_limit", "integer", "Maximum priority leads", False, 8),
        ], make_business_context(session_factory, org_id)),

        # Analysis
        ToolDefinition("company_analysis", "Generate a comprehensive AI analysis of a company.", "analysis", [
            ToolParameter("company_id", "integer", "Company ID", True),
        ], make_company_analysis(session_factory, org_id)),

        # Knowledge
        ToolDefinition("knowledge_search", "Search the PNS service catalog, pricing guidance, sales scripts, discovery playbook, objection handling, and system guidance.", "knowledge", [
            ToolParameter("query", "string", "Search term"),
        ], make_knowledge_search()),
        ToolDefinition("service_catalog", "List all services offered by Pacific North Systems.", "knowledge", [
            ToolParameter("category", "string", "Specific service category"),
        ], make_service_catalog()),
        ToolDefinition("pricing_reference", "Get pricing tiers and ranges.", "knowledge", [
            ToolParameter("tier", "string", "Specific pricing tier"),
        ], make_pricing_reference()),

        # Controlled writes. MCP annotations tell clients these tools change CRM data.
        ToolDefinition("create_company", "Create a new CRM company after checking for an existing company with the same name.", "write", [
            ToolParameter("name", "string", "Company name", True),
            ToolParameter("industry", "string", "Industry"),
            ToolParameter("website", "string", "Company website"),
            ToolParameter("phone", "string", "Company phone"),
            ToolParameter("email", "string", "Company email"),
        ], make_create_company(session_factory, org_id), read_only=False),
        ToolDefinition("create_contact", "Create a contact linked to an existing company.", "write", [
            ToolParameter("company_id", "integer", "Company ID", True),
            ToolParameter("first_name", "string", "First name", True),
            ToolParameter("last_name", "string", "Last name", True),
            ToolParameter("email", "string", "Email"),
            ToolParameter("phone", "string", "Phone"),
            ToolParameter("title", "string", "Job title"),
        ], make_create_contact(session_factory, org_id), read_only=False),
        ToolDefinition("add_company_note", "Add an internal note to a company timeline.", "write", [
            ToolParameter("company_id", "integer", "Company ID", True),
            ToolParameter("note", "string", "Note text", True),
            ToolParameter("subject", "string", "Short note subject", False, "CRM note"),
        ], make_add_note(session_factory, org_id), read_only=False),
        ToolDefinition("create_task", "Create a CRM follow up task. Due date must use YYYY-MM-DD.", "write", [
            ToolParameter("title", "string", "Task title", True),
            ToolParameter("due_date", "string", "Due date in YYYY-MM-DD format", True),
            ToolParameter("company_id", "integer", "Optional company ID"),
            ToolParameter("description", "string", "Task details"),
            ToolParameter("priority", "string", "low, medium, high or urgent", False, "medium", ["low", "medium", "high", "urgent"]),
        ], make_create_task(session_factory, org_id), read_only=False),
        ToolDefinition("complete_task", "Mark an existing CRM task completed.", "write", [
            ToolParameter("task_id", "integer", "Task ID", True),
        ], make_complete_task(session_factory, org_id), read_only=False),
        ToolDefinition("create_opportunity", "Create a sales opportunity for an existing company.", "write", [
            ToolParameter("company_id", "integer", "Company ID", True),
            ToolParameter("title", "string", "Opportunity title", True),
            ToolParameter("estimated_value", "number", "Estimated value", False, 0),
            ToolParameter("probability", "integer", "Probability from 0 to 100", False, 50),
            ToolParameter("stage", "string", "Sales stage", False, "lead", ["lead", "qualified", "proposal", "negotiation", "won", "lost"]),
        ], make_create_opportunity(session_factory, org_id), read_only=False),
    ]

    for tool in tools:
        registry.register(tool)
    return registry
