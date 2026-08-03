"""
MCP Tools — Complete Tool Suite.

Every tool the LLM can call. Tools are pure business-logic wrappers
that call application services — never repositories, never SQL.

Registered at import time into the global ToolRegistry.
"""

from sqlalchemy import func, select, or_
from sqlalchemy.orm import Session

from app.application.sales.ai_analysis import CompanyAnalysisEngine
from app.application.sales.ai_brief import DailyBriefEngine
from app.application.sales.ai_meeting import MeetingPrepEngine
from app.application.sales.ai_proposal import ProposalBuilderEngine
from app.application.sales.scoring import ScoringEngine
from app.infrastructure.db.models import Activity, Company, Contact, Opportunity, Task
from app.infrastructure.mcp.context_builders import CompanyContext
from app.infrastructure.mcp.tool_registry import ToolDefinition, ToolParameter, get_registry


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
                "events": [{"type": a.type, "subject": a.subject, "body": a.body, "date": str(a.created_at)} for a in activities],
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
                    {"type": a.type, "subject": a.subject, "date": str(a.created_at), "company_name": c.name, "company_id": c.id}
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

def register_all_tools(session_factory, org_id: int) -> None:
    """Register all MCP tools with the global registry."""
    registry = get_registry()

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
    ]

    for tool in tools:
        registry.register(tool)
