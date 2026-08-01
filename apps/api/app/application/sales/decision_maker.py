"""
Decision Maker Intelligence Engine.

Analyzes contacts and organizational structure to recommend
the best people to approach for software purchasing decisions.

Never simply lists contacts — scores, ranks, and explains WHY
each person is recommended, what they care about, and how to
approach them.
"""

from typing import Any

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.db.models import Activity, Company, Contact


# ── Role Scoring Tables ──

EXECUTIVE_TITLES: dict[str, int] = {
    "owner": 100, "founder": 100, "ceo": 100, "president": 98,
    "managing director": 96, "general manager": 90, "coo": 95,
    "director": 85, "vp": 88, "vice president": 88, "chief": 95,
    "partner": 90, "principal": 85,
}

OPERATIONAL_TITLES: dict[str, int] = {
    "operations manager": 92, "operations director": 94,
    "office manager": 75, "facilities manager": 72,
    "project manager": 78, "program manager": 78,
    "construction manager": 80, "maintenance manager": 76,
    "field service manager": 82, "site manager": 78,
    "production manager": 80, "plant manager": 82,
    "logistics manager": 72, "supply chain": 75,
}

TECHNICAL_TITLES: dict[str, int] = {
    "it manager": 88, "technology director": 92, "cto": 100,
    "engineering manager": 85, "technical director": 90,
    "digital transformation": 95, "innovation": 88,
    "systems manager": 82, "infrastructure manager": 80,
    "software manager": 85, "development manager": 82,
    "head of technology": 92, "head of it": 90,
    "head of engineering": 88, "head of digital": 90,
}

FINANCE_TITLES: dict[str, int] = {
    "cfo": 95, "finance director": 90, "finance manager": 78,
    "controller": 72, "vp finance": 92,
}

SALES_TITLES: dict[str, int] = {
    "business development": 82, "sales director": 80,
    "sales manager": 75, "account manager": 65,
    "vp sales": 85, "head of sales": 85,
}


# ── Output Models ──

class ContactScore(BaseModel):
    contact_id: int
    full_name: str
    job_title: str | None
    email: str | None
    phone: str | None
    role_fit_score: int
    influence_score: int
    accessibility_score: int
    executive_authority: int
    technical_authority: int
    operational_impact: int
    overall_priority: int
    role_category: str  # "executive", "operational", "technical", "finance", "sales", "other"
    reasoning: list[str]


class DecisionMakerReport(BaseModel):
    company_id: int
    company_name: str
    contacts_scored: list[ContactScore]
    primary_contact: ContactScore | None
    secondary_contact: ContactScore | None
    technical_contact: ContactScore | None
    operational_contact: ContactScore | None
    executive_sponsor: ContactScore | None
    engagement_strategy: list[str]
    outreach_plan: dict[str, Any]


# ── Engine ──

class DecisionMakerEngine:
    """Scores and ranks contacts for purchasing decision influence."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def analyze(self, company: Company) -> DecisionMakerReport:
        contacts = self._session.execute(
            select(Contact).where(Contact.company_id == company.id, Contact.status == "active")
        ).scalars().all()

        activities = self._session.execute(
            select(Activity).where(Activity.company_id == company.id).order_by(Activity.created_at.desc()).limit(20)
        ).scalars().all()

        # Score every contact
        scored = [self._score_contact(c, company, contacts, activities) for c in contacts]
        scored.sort(key=lambda s: s.overall_priority, reverse=True)

        # If no contacts, generate suggested roles to find
        if not scored:
            scored = self._suggest_roles(company)

        primary = scored[0] if scored else None
        secondary = scored[1] if len(scored) > 1 else None
        technical = next((s for s in scored if s.role_category == "technical"), None)
        operational = next((s for s in scored if s.role_category == "operational"), primary)
        executive = next((s for s in scored if s.role_category == "executive"), primary)

        return DecisionMakerReport(
            company_id=company.id,
            company_name=company.name,
            contacts_scored=scored,
            primary_contact=primary,
            secondary_contact=secondary,
            technical_contact=technical,
            operational_contact=operational,
            executive_sponsor=executive,
            engagement_strategy=self._build_strategy(company, scored),
            outreach_plan=self._build_outreach(company, primary) if primary else {},
        )

    def _score_contact(self, c: Contact, company: Company, all_contacts: list[Contact], activities: list[Activity]) -> ContactScore:
        title = (c.job_title or "").lower().strip()

        # Role fit — match against title tables
        role_fit = 0
        role_category = "other"
        for titles, category in [
            (EXECUTIVE_TITLES, "executive"), (OPERATIONAL_TITLES, "operational"),
            (TECHNICAL_TITLES, "technical"), (FINANCE_TITLES, "finance"),
            (SALES_TITLES, "sales"),
        ]:
            for kw, score in titles.items():
                if kw in title:
                    if score > role_fit:
                        role_fit = score
                        role_category = category

        if role_fit == 0 and title:
            role_fit = 40  # Unknown title — neutral
            role_category = "other"

        # Executive authority — based on title level
        exec_auth = role_fit if role_category == "executive" else role_fit // 2 if role_category in ("finance", "technical") else role_fit // 3

        # Technical authority
        tech_auth = role_fit if role_category == "technical" else role_fit // 3

        # Operational impact — higher for operational roles in their industry
        op_impact = role_fit if role_category == "operational" else role_fit // 2

        # Accessibility — email + phone + LinkedIn + CRM activity
        accessibility = 30
        if c.email: accessibility += 25
        if c.phone or c.mobile: accessibility += 20
        if c.linkedin: accessibility += 15
        contact_activities = [a for a in activities if a.contact_id == c.id]
        if contact_activities: accessibility += 10

        # Influence — position in org + CRM history
        influence = role_fit // 2 + min(len(contact_activities) * 5, 30)

        # Overall priority (0-100)
        overall = min(100, (
            role_fit * 0.30 +
            min(accessibility, 100) * 0.20 +
            exec_auth * 0.20 +
            tech_auth * 0.10 +
            op_impact * 0.10 +
            influence * 0.10
        ))  # fmt: skip

        # Reasoning
        reasoning: list[str] = []
        if role_category == "executive": reasoning.append(f"Executive-level role — high purchasing authority")
        if role_category == "operational": reasoning.append(f"Operational role — directly impacted by workflow improvements")
        if role_category == "technical": reasoning.append(f"Technical role — likely evaluates solutions")
        if c.email: reasoning.append("Email available — high accessibility")
        if c.phone: reasoning.append("Phone available — direct outreach possible")
        if contact_activities: reasoning.append(f"{len(contact_activities)} previous CRM interactions — existing relationship")
        if c.is_decision_maker: reasoning.append("Marked as decision maker in CRM")
        if not reasoning: reasoning.append("Limited data — recommend enrichment")

        return ContactScore(
            contact_id=c.id, full_name=f"{c.first_name} {c.last_name}",
            job_title=c.job_title, email=c.email, phone=c.phone,
            role_fit_score=role_fit, influence_score=min(influence, 100),
            accessibility_score=min(accessibility, 100),
            executive_authority=exec_auth, technical_authority=tech_auth,
            operational_impact=op_impact, overall_priority=int(overall),
            role_category=role_category, reasoning=reasoning,
        )

    def _suggest_roles(self, company: Company) -> list[ContactScore]:
        """Generate suggested roles when no contacts exist."""
        ind = (company.industry or "").lower()
        suggestions: list[ContactScore] = []

        if "construction" in ind or "engineering" in ind:
            suggestions.append(self._role_template("Operations Manager", "operational", 92, company))
            suggestions.append(self._role_template("Project Manager", "operational", 78, company))
            suggestions.append(self._role_template("Owner/CEO", "executive", 100, company))
        elif "property" in ind:
            suggestions.append(self._role_template("Property Manager", "operational", 88, company))
            suggestions.append(self._role_template("Owner/CEO", "executive", 100, company))
        elif "manufacturing" in ind:
            suggestions.append(self._role_template("Plant Manager", "operational", 85, company))
            suggestions.append(self._role_template("Operations Director", "operational", 94, company))
            suggestions.append(self._role_template("IT Manager", "technical", 88, company))
        else:
            suggestions.append(self._role_template("Owner/CEO", "executive", 100, company))
            suggestions.append(self._role_template("Operations Manager", "operational", 85, company))
            suggestions.append(self._role_template("IT Manager", "technical", 82, company))

        return suggestions

    def _role_template(self, title: str, category: str, score: int, company: Company) -> ContactScore:
        return ContactScore(
            contact_id=0, full_name=f"[Suggested: {title}]", job_title=title,
            email=None, phone=None,
            role_fit_score=score, influence_score=score // 2,
            accessibility_score=20, executive_authority=score if category == "executive" else score // 3,
            technical_authority=score if category == "technical" else score // 3,
            operational_impact=score if category == "operational" else score // 2,
            overall_priority=score - 10, role_category=category,
            reasoning=[
                f"Suggested role for {company.industry or 'this'} industry",
                f"No contacts on file — add this role to begin outreach",
                f"Based on company size (~{company.employees or 'N/A'} employees)",
            ],
        )

    def _build_strategy(self, company: Company, scored: list[ContactScore]) -> list[str]:
        """Generate a multi-step engagement strategy."""
        ind = (company.industry or "").lower()
        steps: list[str] = []

        has_ops = any(s.role_category == "operational" for s in scored)
        has_exec = any(s.role_category == "executive" for s in scored)
        has_tech = any(s.role_category == "technical" for s in scored)

        if has_ops:
            steps.append(f"1. Contact {next(s.full_name for s in scored if s.role_category == 'operational')} first — introduce workflow automation benefits for {ind} operations")
        elif scored:
            steps.append(f"1. Contact {scored[0].full_name} — introduce Pacific North Systems and assess needs")

        if has_exec:
            steps.append(f"2. After initial interest, schedule meeting with executive sponsor to discuss ROI and business impact")

        if has_tech and len(steps) >= 2:
            steps.append("3. Arrange technical workshop to demonstrate platform capabilities")
        elif company.employees and company.employees > 50:
            steps.append("3. Prepare a tailored demo addressing their specific operational challenges")

        steps.append("4. Present proposal with pricing tier aligned to company size and needs")
        steps.append("5. Close with a phased implementation plan to minimize risk")

        if not company.website:
            steps.append("⚠ Research company website and digital presence before outreach")

        return steps

    def _build_outreach(self, company: Company, primary: ContactScore | None) -> dict[str, Any]:
        if not primary:
            return {"error": "No primary contact to prepare outreach for"}

        ind = (company.industry or "their industry")
        name = primary.full_name

        return {
            "primary_contact": name,
            "cold_email_subject": f"Streamlining operations at {company.name}",
            "cold_email_body": f"Hi {primary.full_name.split()[0]},\n\nI've been following {company.name}'s work in {ind} and wanted to reach out. At Pacific North Systems, we specialize in helping {ind} companies streamline operations through custom software solutions.\n\nWould you be open to a brief conversation about your current operational challenges?\n\nBest regards,\n[Your Name]",
            "linkedin_message": f"Hi {primary.full_name.split()[0]}, I've been impressed by {company.name}'s presence in {ind}. I'd love to connect and share how we're helping similar companies improve operational efficiency. No pressure — just a conversation.",
            "call_script": [
                f"Opening: 'Hi {primary.full_name.split()[0]}, this is [Name] from Pacific North Systems. I'm reaching out because we've helped several {ind} companies improve their operations...'",
                "Discovery: 'What are your biggest operational challenges right now?'",
                "Value: 'We typically help companies reduce admin overhead by 20-40%.'",
                "Close: 'Could we schedule a 20-minute call to explore if there's a fit?'",
            ],
            "discovery_questions": [
                "What software tools are you currently using for operations?",
                "What's the biggest bottleneck your team faces daily?",
                "How do you currently track projects and client communication?",
                "Who else would be involved in a technology decision?",
            ],
            "likely_objections": [
                {"objection": "We don't have budget", "response": "Many clients find the ROI justifies investment within 6-12 months."},
                {"objection": "We're too busy", "response": "Implementation is phased to minimize disruption. We work around your schedule."},
            ],
            "recommended_follow_up": "Send case study via email after 3 days if no response. Follow up with a call after 7 days.",
        }
