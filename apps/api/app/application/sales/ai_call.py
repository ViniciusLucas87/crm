"""
AI Call Assistant Engine.

Pre-call: generates objectives, questions, objection responses.
Post-call: processes transcript into summary, tasks, timeline events.
"""

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.db.models import Company, Contact


class CallObjective(BaseModel):
    goal: str
    success_criteria: str


class PreCallBrief(BaseModel):
    company_id: int
    company_name: str
    objectives: list[CallObjective]
    company_summary: str
    buying_signals: str
    suggested_questions: list[str]
    likely_objections: list[dict[str, str]]
    talking_points: list[str]
    cross_selling: list[str]
    upselling: list[str]
    success_criteria: list[str]


class PostCallResult(BaseModel):
    summary: str
    tasks: list[dict[str, str]]
    timeline_events: list[dict[str, str]]
    opportunity_updates: list[str]
    follow_up_recommendations: list[str]


class CallAssistantEngine:
    def __init__(self, session: Session) -> None:
        self._session = session

    def pre_call(self, company: Company) -> PreCallBrief:
        ind = (company.industry or "").lower()

        objectives = [
            CallObjective(goal="Understand current operational workflow", success_criteria="Clear picture of daily processes and bottlenecks"),
            CallObjective(goal="Identify key decision makers", success_criteria="Names and roles of all stakeholders in purchasing"),
            CallObjective(goal="Uncover pain points and priorities", success_criteria="Ranked list of top 3 operational challenges"),
            CallObjective(goal="Establish timeline and budget", success_criteria="Rough timeline and budget range confirmed"),
        ]

        industry_qs: dict[str, list[str]] = {
            "construction": ["How do you currently manage field inspections?", "What's your process for client communication during projects?"],
            "property": ["How do tenants submit maintenance requests?", "What's your biggest challenge in managing multiple properties?"],
            "engineering": ["How do you manage document versions across teams?", "What tools do you use for project collaboration?"],
            "manufacturing": ["How do you track inventory and maintenance schedules?", "What's your current quality control process?"],
            "architecture": ["How do you share designs with clients for feedback?", "What's your project collaboration workflow?"],
        }

        qs = industry_qs.get(ind, ["What software tools are you currently using?", "What's your biggest operational frustration right now?"])
        qs += ["Who else would be involved in a technology decision?", "What would success look like 6 months after implementation?", "Have you evaluated solutions like this before?"]

        objections = [
            {"objection": "Budget", "response": "I understand. Many clients find the ROI justifies the investment within 6-12 months through efficiency gains."},
            {"objection": "Timing", "response": "We can phase implementation to work around your schedule. Even a discovery phase can start small."},
            {"objection": "Status Quo", "response": "That's totally fair. I'd love to show you how similar companies improved without disrupting what already works."},
            {"objection": "Competitor", "response": "Great — it means you see the value. Let me share what makes our approach different."},
        ]

        return PreCallBrief(
            company_id=company.id,
            company_name=company.name,
            objectives=objectives,
            company_summary=f"{company.name} — {company.industry or 'Unknown industry'} — ~{company.employees or 'N/A'} employees — {company.city or 'Unknown location'}",
            buying_signals=f"Opportunity Score: {company.opportunity_score or 'N/A'}/100. {company.industry or 'Unknown'} industry — aligned with our expertise." if company.opportunity_score else "Complete company research to improve signal detection.",
            suggested_questions=qs,
            likely_objections=objections,
            talking_points=[
                f"Pacific North Systems has proven experience in the {company.industry or 'technology'} sector",
                "We focus on measurable outcomes — not just software features",
                "Our phased approach means you see value quickly without disrupting operations",
                "We become a long-term technology partner, not just a vendor",
            ],
            cross_selling=["Client Portal", "Document Automation", "Workflow Automation"],
            upselling=["Advanced Analytics", "Extended Support", "Additional User Licenses"],
            success_criteria=["Scheduling a follow-up meeting", "Agreement to receive a proposal", "Introduction to additional stakeholders"],
        )

    def post_call(self, company: Company, transcript: str | None = None) -> PostCallResult:
        summary = f"Call with {company.name} completed. "
        if transcript:
            summary += f"Transcript captured ({len(transcript)} characters). Key points to be extracted."
        else:
            summary += "Review notes and update CRM with key discussion points, decisions, and action items."

        tasks = [
            {"title": f"Send follow-up email to {company.name}", "priority": "high", "due": "within 24 hours"},
            {"title": "Update company notes with call summary", "priority": "medium", "due": "today"},
            {"title": "Schedule next touchpoint", "priority": "medium", "due": "this week"},
        ]
        if not company.tech_stack:
            tasks.append({"title": "Document technology stack discussed", "priority": "medium", "due": "today"})

        timeline_events = [
            {"type": "call", "subject": f"Call with {company.name}", "body": "Sales call completed. See notes for details."},
        ]

        return PostCallResult(
            summary=summary,
            tasks=tasks,
            timeline_events=timeline_events,
            opportunity_updates=["Update opportunity stage based on call outcome", "Adjust probability based on conversation signals"],
            follow_up_recommendations=["Send personalized follow-up within 24 hours", "Add any promised materials or links", "Schedule next meeting before ending the call", "Update CRM immediately after the call"],
        )
