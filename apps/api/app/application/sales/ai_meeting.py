"""
AI Meeting Preparation Engine.

Generates comprehensive briefing documents for sales meetings
using all available CRM context.
"""

from typing import Any

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.infrastructure.db.models import Activity, Company, Contact, Opportunity


class MeetingPrepSection(BaseModel):
    title: str
    content: str
    items: list[str]


class MeetingPrep(BaseModel):
    company_id: int
    company_name: str
    company_overview: MeetingPrepSection
    recent_timeline: MeetingPrepSection
    buying_signals: MeetingPrepSection
    technology: MeetingPrepSection
    research: MeetingPrepSection
    contacts: MeetingPrepSection
    activities: MeetingPrepSection
    open_opportunities: MeetingPrepSection
    recommended_goals: MeetingPrepSection
    suggested_questions: MeetingPrepSection
    likely_objections: MeetingPrepSection
    talking_points: MeetingPrepSection
    suggested_opening: MeetingPrepSection
    suggested_closing: MeetingPrepSection
    cross_selling: MeetingPrepSection
    upselling: MeetingPrepSection
    checklist: MeetingPrepSection


class MeetingPrepEngine:
    def __init__(self, session: Session) -> None:
        self._session = session

    def prepare(self, company: Company) -> MeetingPrep:
        contacts = self._session.execute(
            select(Contact).where(Contact.company_id == company.id, Contact.status == "active")
        ).scalars().all()

        activities = self._session.execute(
            select(Activity).where(Activity.company_id == company.id).order_by(Activity.created_at.desc()).limit(10)
        ).scalars().all()

        opps = self._session.execute(
            select(Opportunity).where(Opportunity.company_id == company.id, Opportunity.stage.notin_(["won", "lost"]))
        ).scalars().all()

        return MeetingPrep(
            company_id=company.id,
            company_name=company.name,
            company_overview=self._company_overview(company),
            recent_timeline=self._recent_timeline(activities),
            buying_signals=self._buying_signals(company),
            technology=self._technology(company),
            research=self._research(company),
            contacts=self._contacts(contacts),
            activities=self._activities(activities),
            open_opportunities=self._open_opportunities(opps),
            recommended_goals=self._recommended_goals(company, opps),
            suggested_questions=self._suggested_questions(company),
            likely_objections=self._likely_objections(company),
            talking_points=self._talking_points(company),
            suggested_opening=self._suggested_opening(company, contacts),
            suggested_closing=self._suggested_closing(company, opps),
            cross_selling=self._cross_selling(company),
            upselling=self._upselling(company, opps),
            checklist=self._checklist(company),
        )

    def _company_overview(self, c: Company) -> MeetingPrepSection:
        parts: list[str] = [c.name]
        if c.industry: parts.append(f"Industry: {c.industry}")
        if c.employees: parts.append(f"Employees: ~{c.employees}")
        if c.city: parts.append(f"Location: {c.city}{', ' + c.province if c.province else ''}")
        if c.website: parts.append(f"Website: {c.website}")
        return MeetingPrepSection(title="Company Overview", content="\n".join(parts), items=parts)

    def _recent_timeline(self, activities: list[Activity]) -> MeetingPrepSection:
        items = [f"{a.created_at.strftime('%b %d'):8s} {a.type.upper():8s} {a.subject or a.body or 'No details'}"[:120] for a in activities[:8]]
        return MeetingPrepSection(title="Recent Timeline", content="\n".join(items) if items else "No recent activity.", items=items)

    def _buying_signals(self, c: Company) -> MeetingPrepSection:
        items: list[str] = []
        if c.opportunity_score and c.opportunity_score >= 60: items.append(f"Opportunity Score: {c.opportunity_score}/100 (High)")
        elif c.opportunity_score: items.append(f"Opportunity Score: {c.opportunity_score}/100")
        if c.industry: items.append(f"Industry alignment: {c.industry}")
        if not items: items.append("No strong signals detected — focus on discovery")
        return MeetingPrepSection(title="Buying Signals", content="\n".join(items), items=items)

    def _technology(self, c: Company) -> MeetingPrepSection:
        items: list[str] = []
        # Technology stack info not available in current schema
        items.append("Technology stack unknown — ask during meeting")
        if c.website: items.append("Website present — review before meeting")
        return MeetingPrepSection(title="Technology", content="\n".join(items), items=items)

    def _research(self, c: Company) -> MeetingPrepSection:
        items: list[str] = []
        if c.description: items.append(f"Description: {c.description[:200]}")
        if c.linkedin_url: items.append(f"LinkedIn: {c.linkedin_url}")
        if c.research_status: items.append(f"Research status: {c.research_status}")
        else: items.append("Research incomplete — review company website and LinkedIn")
        return MeetingPrepSection(title="Research", content="\n".join(items), items=items)

    def _contacts(self, contacts: list[Contact]) -> MeetingPrepSection:
        if not contacts: return MeetingPrepSection(title="Contacts", content="No contacts on file. Add decision makers.", items=[])
        items = [f"{c.first_name} {c.last_name}" + (f" — {c.job_title}" if c.job_title else "") + (f" ({c.email})" if c.email else "") for c in contacts]
        return MeetingPrepSection(title="Contacts", content="\n".join(items), items=items)

    def _activities(self, activities: list[Activity]) -> MeetingPrepSection:
        items = [f"{a.activity_type.title()}: {a.subject or 'No subject'} ({a.created_at.strftime('%b %d')})" for a in activities[:5]]
        return MeetingPrepSection(title="Recent Activities", content="\n".join(items) if items else "No activities recorded.", items=items)

    def _open_opportunities(self, opps: list[Opportunity]) -> MeetingPrepSection:
        if not opps: return MeetingPrepSection(title="Open Opportunities", content="No open opportunities.", items=[])
        items = [f"{o.title or 'Untitled'} — ${o.estimated_value:,.0f} ({o.stage})" for o in opps if o.estimated_value]
        return MeetingPrepSection(title="Open Opportunities", content="\n".join(items), items=items)

    def _recommended_goals(self, c: Company, opps: list[Opportunity]) -> MeetingPrepSection:
        items = ["Understand current operational challenges", "Identify decision-making process"]
        if not opps: items.append("Introduce Pacific North Systems services")
        else: items.append(f"Advance {len(opps)} open {'opportunity' if len(opps) == 1 else 'opportunities'}")
        items.append("Discover technology stack and pain points")
        return MeetingPrepSection(title="Recommended Goals", content="\n".join(f"• {g}" for g in items), items=items)

    def _suggested_questions(self, c: Company) -> MeetingPrepSection:
        ind = (c.industry or "").lower()
        qs = [
            "What does your current workflow look like for [core process]?",
            "What are the biggest bottlenecks your team faces?",
            "How are you currently tracking projects and client communication?",
            "What would success look like 6 months after implementing a solution?",
        ]
        if "construction" in ind: qs.insert(0, "How do you currently manage field inspections?")
        if "property" in ind: qs.insert(0, "How do you handle tenant communication and maintenance requests?")
        return MeetingPrepSection(title="Suggested Questions", content="\n".join(f"• {q}" for q in qs), items=qs)

    def _likely_objections(self, c: Company) -> MeetingPrepSection:
        items = [
            ("Budget", "We don't have budget for this right now."),
            ("Timing", "We're too busy to take on a new system."),
            ("Status Quo", "We've always done it this way."),
            ("Competitor", "We're already using [Competitor X]."),
        ]
        return MeetingPrepSection(title="Likely Objections", content="\n".join(f"• {label}: {response}" for label, response in items), items=[f"{label}: {response}" for label, response in items])

    def _talking_points(self, c: Company) -> MeetingPrepSection:
        items = [
            f"Pacific North Systems has deep experience in the {c.industry or 'technology'} sector",
            "Our solutions are built specifically for companies like yours",
            "We focus on measurable ROI — typically 20-40% efficiency improvement",
            "Implementation is phased to minimize disruption",
        ]
        return MeetingPrepSection(title="Talking Points", content="\n".join(f"• {t}" for t in items), items=items)

    def _suggested_opening(self, c: Company, contacts: list[Contact]) -> MeetingPrepSection:
        contact_names = ", ".join(f"{ct.first_name}" for ct in contacts[:2]) if contacts else "team"
        content = f"Thank you for taking the time, {contact_names}. I've been learning about {c.name} and I'm excited to understand more about how you're approaching {c.industry or 'your operations'}. I think there might be some ways we could help streamline your workflow."
        return MeetingPrepSection(title="Suggested Opening", content=content, items=[content])

    def _suggested_closing(self, c: Company, opps: list[Opportunity]) -> MeetingPrepSection:
        if opps:
            content = "Based on what we discussed, I'll prepare a proposal outlining the solution and timeline. Can we schedule a follow-up for next week to review it together?"
        else:
            content = "I'd like to take what we discussed back to my team and put together a preliminary assessment. Could we schedule a follow-up call for next week?"
        return MeetingPrepSection(title="Suggested Closing", content=content, items=[content])

    def _cross_selling(self, c: Company) -> MeetingPrepSection:
        items = ["Client Portal — improves customer communication", "Document Automation — reduces manual paperwork", "Workflow Automation — streamlines repetitive tasks"]
        return MeetingPrepSection(title="Cross-Selling Ideas", content="\n".join(f"• {i}" for i in items), items=items)

    def _upselling(self, c: Company, opps: list[Opportunity]) -> MeetingPrepSection:
        if not opps: return MeetingPrepSection(title="Upselling Ideas", content="No current opportunities to upsell.", items=[])
        items = ["Extended support and maintenance package", "Advanced analytics and reporting module", "Additional user licenses for growing teams"]
        return MeetingPrepSection(title="Upselling Ideas", content="\n".join(f"• {i}" for i in items), items=items)

    def _checklist(self, c: Company) -> MeetingPrepSection:
        items = [
            "Review company website and LinkedIn profile",
            "Prepare personalized slides or demo",
            "Check recent news about the company",
            "Confirm meeting logistics (time, platform, attendees)",
            "Review open opportunities and proposals",
            "Prepare note-taking template",
        ]
        return MeetingPrepSection(title="Meeting Checklist", content="\n".join(f"☐ {i}" for i in items), items=items)
