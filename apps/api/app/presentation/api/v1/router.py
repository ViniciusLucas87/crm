from fastapi import APIRouter

from app.presentation.api.v1.routes import (
    actions,
    agents,
    ai,
    app_factory,
    assessment_public,
    assessments,
    audit,
    auth,
    companies,
    contacts,
    conversations,
    copilot,
    dashboard,
    decision_maker,
    demand,
    documents,
    enrich,
    health,
    health_llm,
    intelligence,
    knowledge,
    leads,
    linkedin_leads,
    mcp,
    never_forget,
    operations,
    outreach_email,
    products,
    reddit_leads,
    reports,
    sales,
    sales_coach,
    scoring,
    search,
    subscriptions,
    telemetry,
    tiktok_leads,
    telephony,
    timeline,
    transcription,
    workers,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(health_llm.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
api_router.include_router(contacts.router, tags=["contacts"])
api_router.include_router(sales.router, tags=["sales"])
api_router.include_router(timeline.router, tags=["timeline"])
api_router.include_router(actions.router, tags=["actions"])
api_router.include_router(search.router, tags=["search"])
api_router.include_router(intelligence.router, tags=["intelligence"])
api_router.include_router(scoring.router, tags=["scoring"])
api_router.include_router(ai.router, tags=["ai"])
api_router.include_router(app_factory.router, tags=["app-factory"])
api_router.include_router(mcp.router, tags=["mcp"])
api_router.include_router(never_forget.router, tags=["never-forget"])
api_router.include_router(agents.router, tags=["agents"])
api_router.include_router(enrich.router, tags=["enrich"])
api_router.include_router(reports.router, tags=["reports"])
api_router.include_router(telephony.router, tags=["telephony"])
api_router.include_router(products.router, tags=["products"])
api_router.include_router(subscriptions.router, tags=["subscriptions"])
api_router.include_router(telemetry.router, tags=["telemetry"])
api_router.include_router(operations.router, prefix="/operations", tags=["operations"])
api_router.include_router(outreach_email.router, tags=["outreach-email"])
api_router.include_router(decision_maker.router, tags=["decision-maker"])
api_router.include_router(documents.router, tags=["documents"])
api_router.include_router(leads.router, tags=["leads"])
api_router.include_router(reddit_leads.router, tags=["reddit-leads"])
api_router.include_router(linkedin_leads.router, tags=["linkedin-leads"])
api_router.include_router(tiktok_leads.router, tags=["tiktok-leads"])
api_router.include_router(conversations.router, tags=["conversations"])
api_router.include_router(copilot.router, tags=["copilot"])
api_router.include_router(transcription.router, prefix="/transcription", tags=["transcription"])
api_router.include_router(audit.router, tags=["audit"])
api_router.include_router(sales_coach.router, prefix="/sales-coach", tags=["sales-coach"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["knowledge"])
api_router.include_router(demand.router, prefix="/demand", tags=["demand"])
api_router.include_router(workers.router, prefix="/workers", tags=["workers"])
api_router.include_router(assessment_public.router, tags=["public"])
api_router.include_router(assessments.router, tags=["assessments"])
