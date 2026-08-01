"""
AI Proposal Builder Engine.

Generates structured proposal drafts from CRM context.
Proposals are always editable — this is a starting point, not a final document.
"""

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.db.models import Activity, Company, Contact, Opportunity


class ProposalSection(BaseModel):
    heading: str
    body: str
    editable: bool = True


class ProposalDraft(BaseModel):
    company_id: int
    company_name: str
    title: str
    sections: list[ProposalSection]


class ProposalBuilderEngine:
    def __init__(self, session: Session) -> None:
        self._session = session

    def build(self, company: Company) -> ProposalDraft:
        contacts = self._session.execute(
            select(Contact).where(Contact.company_id == company.id, Contact.status == "active")
        ).scalars().all()

        opps = self._session.execute(
            select(Opportunity).where(Opportunity.company_id == company.id, Opportunity.stage.notin_(["won", "lost"]))
        ).scalars().all()

        contact_names = ", ".join(f"{c.first_name} {c.last_name}" for c in contacts[:3]) if contacts else "[Contact Name]"
        industry = company.industry or "your industry"
        company_name = company.name
        emp = company.employees or "N/A"

        sections: list[ProposalSection] = [
            ProposalSection(
                heading="Executive Summary",
                body=f"This proposal outlines a recommended solution for {company_name}, a {industry} company with approximately {emp} employees. Based on our assessment, we believe Pacific North Systems can deliver significant operational improvements through tailored software solutions.",
            ),
            ProposalSection(
                heading="Current Situation",
                body=f"{company_name} currently operates in the {industry} sector. Our analysis suggests opportunities to improve operational efficiency, streamline communication, and digitize key business processes. {'Multiple locations were identified, indicating potential challenges in centralized operations management.' if company.locations else 'The company would benefit from a centralized platform to manage its growing operations.'}",
            ),
            ProposalSection(
                heading="Identified Challenges",
                body=self._build_challenges(company),
            ),
            ProposalSection(
                heading="Business Impact",
                body="Without addressing these challenges, the organization may continue to experience: reduced operational efficiency, fragmented communication, manual process overhead, and missed growth opportunities. By implementing a modern software solution, these issues can be systematically resolved.",
            ),
            ProposalSection(
                heading="Recommended Solution",
                body=self._build_solution(company),
            ),
            ProposalSection(
                heading="Deliverables",
                body=self._build_deliverables(company),
            ),
            ProposalSection(
                heading="Estimated Timeline",
                body=f"Based on company size (~{emp} employees), we estimate a phased implementation over {'4-6 months' if emp and emp > 100 else '2-4 months' if emp and emp > 20 else '1-2 months'}. Each phase includes discovery, configuration, testing, training, and go-live support.",
            ),
            ProposalSection(
                heading="Estimated Investment",
                body=self._build_investment(company),
            ),
            ProposalSection(
                heading="Expected ROI",
                body="Based on industry benchmarks, organizations implementing similar solutions typically achieve:\n• 20-40% reduction in administrative overhead\n• 30% improvement in response times\n• 25% increase in team productivity\n• Return on investment within 6-12 months",
            ),
            ProposalSection(
                heading="Next Steps",
                body=f"1. Review and discuss this proposal with {contact_names}\n2. Schedule a technical discovery session\n3. Refine scope and timeline based on feedback\n4. Finalize agreement and begin Phase 1\n\nWe look forward to partnering with {company_name}.",
            ),
        ]

        return ProposalDraft(
            company_id=company.id,
            company_name=company.name,
            title=f"Proposal for {company.name}",
            sections=sections,
        )

    def _build_challenges(self, c: Company) -> str:
        ind = (c.industry or "").lower()
        items: list[str] = []
        if "construction" in ind:
            items = ["Field inspection coordination", "Project documentation management", "Client communication gaps"]
        elif "property" in ind:
            items = ["Tenant communication inefficiency", "Maintenance request tracking", "Document and lease management"]
        elif "engineering" in ind:
            items = ["Document version control", "Project specification management", "Cross-team collaboration"]
        elif "manufacturing" in ind:
            items = ["Inventory visibility", "Preventive maintenance scheduling", "Quality control documentation"]
        else:
            items = ["Operational process inefficiencies", "Communication fragmentation", "Manual data entry and reporting"]
        return "\n".join(f"• {i}" for i in items)

    def _build_solution(self, c: Company) -> str:
        ind = (c.industry or "").lower()
        if "construction" in ind:
            return "Pacific North Systems recommends implementing an integrated Inspection Platform with Field Service capabilities, combined with an Operations Dashboard for real-time visibility. This solution includes mobile field access, automated reporting, and client communication tools."
        if "property" in ind:
            return "We recommend a comprehensive Client Portal with integrated Scheduling and Document Automation. This solution centralizes tenant communication, automates maintenance workflows, and provides owners with real-time visibility."
        return "Pacific North Systems recommends a custom CRM solution with Client Portal, Workflow Automation, and Reporting capabilities. The solution will be tailored to your specific operational requirements."

    def _build_deliverables(self, c: Company) -> str:
        items = [
            "Fully configured software platform",
            "Mobile-responsive interface for field/remote access",
            "Custom workflow automation",
            "Real-time reporting dashboard",
            "Team training and onboarding",
            "30-day post-launch support",
            "Documentation and user guides",
        ]
        return "\n".join(f"• {i}" for i in items)

    def _build_investment(self, c: Company) -> str:
        emp = c.employees or 0
        if emp > 100: tier, setup, monthly = "Enterprise", "$25,000–$50,000", "$2,000–$5,000/month"
        elif emp > 20: tier, setup, monthly = "Professional", "$10,000–$25,000", "$800–$2,000/month"
        else: tier, setup, monthly = "Essentials", "$5,000–$10,000", "$400–$800/month"
        return f"Based on a {tier} deployment for ~{emp} users:\n• One-time setup: {setup}\n• Recurring: {monthly}\n\nExact pricing will be confirmed after technical discovery."
