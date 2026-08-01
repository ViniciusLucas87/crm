"""
AI Email Assistant Engine.

Generates context-aware email drafts using CRM data.
Every email is editable before sending.
"""

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.db.models import Company, Contact


class EmailDraft(BaseModel):
    type: str  # cold, followup, proposal, meeting, reengagement, thank_you, reminder, discovery
    subject: str
    body: str
    company_id: int | None = None
    contact_name: str | None = None


class EmailAssistantEngine:
    def __init__(self, session: Session) -> None:
        self._session = session

    def generate(self, company: Company, email_type: str, contact_id: int | None = None) -> EmailDraft:
        contact = None
        if contact_id:
            contact = self._session.execute(
                select(Contact).where(Contact.id == contact_id, Contact.company_id == company.id)
            ).scalar_one_or_none()

        contact_name = f"{contact.first_name} {contact.last_name}" if contact else "there"
        first_name = contact.first_name if contact else "there"
        company_name = company.name
        industry = company.industry or "your industry"

        generators = {
            "cold": self._cold_email,
            "followup": self._followup_email,
            "proposal": self._proposal_email,
            "meeting": self._meeting_email,
            "reengagement": self._reengagement_email,
            "thank_you": self._thank_you_email,
            "reminder": self._reminder_email,
            "discovery": self._discovery_email,
        }

        gen = generators.get(email_type, self._cold_email)
        subject, body = gen(first_name, company_name, industry, company)
        return EmailDraft(type=email_type, subject=subject, body=body, company_id=company.id, contact_name=contact_name)

    def _cold_email(self, first_name: str, company_name: str, industry: str, c: Company) -> tuple[str, str]:
        subject = f"Streamlining operations at {company_name}"
        body = f"""Hi {first_name},

I've been following {company_name}'s work in the {industry} space and wanted to reach out.

At Pacific North Systems, we specialize in helping {industry} companies streamline their operations through custom software solutions. We've helped similar organizations reduce administrative overhead by 20-40% while improving team productivity.

Would you be open to a brief conversation about your current operational challenges? I'd love to learn more about your priorities and share how we might help.

Best regards,
[Your Name]
Pacific North Systems"""
        return subject, body

    def _followup_email(self, first_name: str, company_name: str, industry: str, c: Company) -> tuple[str, str]:
        subject = f"Following up — {company_name}"
        body = f"""Hi {first_name},

I wanted to follow up on our previous conversation about {company_name}'s operations.

Since we last spoke, I've been thinking about some specific ways we could help streamline your workflows, particularly around [specific area discussed].

Do you have time for a quick call this week to discuss next steps?

Best regards,
[Your Name]
Pacific North Systems"""
        return subject, body

    def _proposal_email(self, first_name: str, company_name: str, industry: str, c: Company) -> tuple[str, str]:
        subject = f"Proposal for {company_name}"
        body = f"""Hi {first_name},

Thank you for the opportunity to present our proposal for {company_name}. Please find the attached proposal document outlining our recommended solution, timeline, and investment.

Key highlights:
• Tailored solution for your {industry} operations
• Phased implementation to minimize disruption
• Measurable ROI within 6-12 months

I'd be happy to walk through the proposal together. Would [Day] at [Time] work for a brief call?

Looking forward to your feedback.

Best regards,
[Your Name]
Pacific North Systems"""
        return subject, body

    def _meeting_email(self, first_name: str, company_name: str, industry: str, c: Company) -> tuple[str, str]:
        subject = f"Confirming our meeting — {company_name}"
        body = f"""Hi {first_name},

I'm writing to confirm our upcoming meeting to discuss {company_name}'s {industry} operations and how Pacific North Systems might help.

Meeting Details:
• Date: [Date]
• Time: [Time]
• Platform: [Video call link]

I've prepared a brief overview based on what I've learned about {company_name}. Looking forward to a productive conversation.

Best regards,
[Your Name]
Pacific North Systems"""
        return subject, body

    def _reengagement_email(self, first_name: str, company_name: str, industry: str, c: Company) -> tuple[str, str]:
        subject = f"Checking in — {company_name}"
        body = f"""Hi {first_name},

It's been a while since we connected about {company_name}'s operations. I wanted to check in and see how things are going.

We've recently helped several {industry} companies implement solutions that significantly improved their workflows. If your priorities have evolved, I'd love to explore how we might support you.

Are you available for a quick catch-up call next week?

Best regards,
[Your Name]
Pacific North Systems"""
        return subject, body

    def _thank_you_email(self, first_name: str, company_name: str, industry: str, c: Company) -> tuple[str, str]:
        subject = f"Thank you — great conversation"
        body = f"""Hi {first_name},

Thank you for taking the time to speak with me today. I really enjoyed learning more about {company_name} and your goals for the coming year.

Based on our conversation, I'll be putting together [deliverable] and will share it by [date].

In the meantime, please don't hesitate to reach out if anything comes to mind.

Best regards,
[Your Name]
Pacific North Systems"""
        return subject, body

    def _reminder_email(self, first_name: str, company_name: str, industry: str, c: Company) -> tuple[str, str]:
        subject = f"Reminder: Upcoming meeting — {company_name}"
        body = f"""Hi {first_name},

Just a quick reminder about our meeting scheduled for [Date] at [Time].

I'm looking forward to discussing how Pacific North Systems can support {company_name}'s {industry} operations.

Please let me know if you need to reschedule.

Best regards,
[Your Name]
Pacific North Systems"""
        return subject, body

    def _discovery_email(self, first_name: str, company_name: str, industry: str, c: Company) -> tuple[str, str]:
        subject = f"Learning more about {company_name}"
        body = f"""Hi {first_name},

I'd love to schedule a brief discovery call to learn more about {company_name}'s operations and challenges in the {industry} space.

Our goal would be to understand:
• Your current workflows and tools
• Key operational challenges
• What an ideal solution would look like
• Timeline and priorities

No commitment required — just an exploratory conversation to see if there's a fit.

Would [Day] or [Day] work for a 20-minute call?

Best regards,
[Your Name]
Pacific North Systems"""
        return subject, body
