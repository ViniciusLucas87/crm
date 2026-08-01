"""
Email Generator — produces professional, natural-sounding emails.

Consumes EmailContext and EmailStrategy. Generates subject, greeting,
opening, body, call to action, and signature. Never invents information.
Never sounds AI-generated.
"""

from __future__ import annotations

from datetime import datetime, UTC

from app.application.copilot.email.models import (
    EmailContext, EmailStrategy, EmailDraft, EmailPurpose, EmailType,
)
from app.application.copilot.email.templates import get_template


class EmailGenerator:
    """Generates professional emails from context and strategy.

    Produces complete drafts with subject, preview, greeting, opening,
    body, call to action, and signature. Professional, natural, consultative.
    """

    def generate(self, context: EmailContext, strategy: EmailStrategy) -> EmailDraft:
        now = datetime.now(UTC).isoformat()

        contact = context.contact_name.split(" ")[0] if context.contact_name else "there"
        company = context.company_name or "your organization"

        # ── Subject ──
        subject = self._build_subject(context, strategy)

        # ── Greeting ──
        greeting = self._build_greeting(contact, strategy)

        # ── Opening ──
        opening = self._build_opening(context, strategy)

        # ── Body ──
        body = self._build_body(context, strategy)

        # ── Call to action ──
        cta = self._build_cta(context, strategy)

        # ── Signature ──
        signature = self._build_signature()

        # ── Preview ──
        preview = body[:120].strip() + "…" if len(body) > 120 else body

        return EmailDraft(
            subject=subject,
            preview=preview,
            greeting=greeting,
            opening=opening,
            body=body,
            call_to_action=cta,
            signature=signature,
            strategy=strategy,
            generated_at=now,
        )

    def generate_from_template(
        self, context: EmailContext, strategy: EmailStrategy, template_id: str | None = None,
    ) -> EmailDraft:
        """Generate email using a specific template."""
        template = get_template(template_id or strategy.purpose)
        if not template:
            return self.generate(context, strategy)

        now = datetime.now(UTC).isoformat()
        contact = context.contact_name.split(" ")[0] if context.contact_name else "there"
        full_contact = context.contact_name or "there"
        company = context.company_name or "your organization"

        # ── Build template variables ──
        pains = context.pain_points[:3]
        pain_summary = pains[0] if pains else "operational efficiency"
        pain_section = "\n".join(f"• {p}" for p in pains) if pains else ""

        products = context.recommended_products[:5]
        highlights = "\n".join(f"• {p}" for p in products) if products else "• Custom solution designed for your requirements"
        roi = context.budget or "measurable ROI"
        roi_highlights = f"Based on our analysis, this solution is projected to deliver {roi} in annual savings through improved operational efficiency."

        # Simple variable substitution
        vars_dict = {
            "company": company,
            "contact": full_contact,
            "pain_points_section": pain_section or "I was impressed by what you shared about your current operations.",
            "pain_point_summary": pain_summary,
            "highlights": highlights,
            "roi_highlights": roi_highlights,
            "recap_points": pain_section or "• Reviewed current operational processes\n• Identified key areas for improvement",
            "next_steps": "• Schedule technical discovery\n• Review proposal\n• Confirm timeline",
            "kickoff_steps": "• Project manager introduction\n• Kickoff meeting scheduling\n• Technical environment setup\n• Team onboarding",
            "objection_responses": "• Your concerns are valid and we've designed specific mitigations for each.",
            "proposal_link": "[Proposal Link]",
            "meeting_link": "[Schedule a Meeting]",
        }

        subject = template.subject_template
        body = template.body_template
        for var, val in vars_dict.items():
            subject = subject.replace(f"{{{var}}}", val)
            body = body.replace(f"{{{var}}}", val)

        greeting = self._build_greeting(contact, strategy)
        opening = ""
        cta = ""
        signature = self._build_signature()

        return EmailDraft(
            subject=subject,
            preview=body[:120].strip() + "…",
            greeting=greeting,
            opening=opening,
            body=body,
            call_to_action=cta,
            signature=signature,
            strategy=strategy,
            generated_at=now,
        )

    def _build_subject(self, context: EmailContext, strategy: EmailStrategy) -> str:
        company = context.company_name or "your organization"
        purpose = strategy.purpose

        subject_map = {
            EmailPurpose.DISCOVERY_FOLLOWUP: f"Following up: {company} Operations Discussion",
            EmailPurpose.PROPOSAL_DELIVERY: f"Technology Solutions Proposal for {company}",
            EmailPurpose.PROPOSAL_REMINDER: f"Quick follow-up: {company} Proposal",
            EmailPurpose.MEETING_SCHEDULING: f"Let's connect: {company} Operations Review",
            EmailPurpose.MEETING_CONFIRMATION: f"Confirmed: {company} Meeting",
            EmailPurpose.MEETING_RECAP: f"Recap: {company} Discussion — Next Steps",
            EmailPurpose.OBJECTION_RESPONSE: f"Re: {company} — Addressing Your Questions",
            EmailPurpose.BUDGET_DISCUSSION: f"{company} — Investment Overview",
            EmailPurpose.TECHNICAL_CLARIFICATION: f"{company} — Technical Follow-up",
            EmailPurpose.CONTRACT_FOLLOWUP: f"{company} — Agreement Status",
            EmailPurpose.IMPLEMENTATION_KICKOFF: f"Welcome aboard: {company} Implementation Kickoff",
            EmailPurpose.CUSTOMER_CHECKIN: f"Checking in: How are things going at {company}?",
            EmailPurpose.REENGAGEMENT: f"Thought of {company} — Checking In",
            EmailPurpose.LOST_RECOVERY: f"Checking in: {company}",
            EmailPurpose.THANK_YOU: f"Thank you, {context.contact_name or 'you'}",
            EmailPurpose.REFERRAL_REQUEST: f"Quick question for you",
        }
        return subject_map.get(purpose, f"Following up: {company}")

    def _build_greeting(self, contact: str, strategy: EmailStrategy) -> str:
        if strategy.tone == "formal":
            return f"Dear {contact},"
        if strategy.tone == "warm":
            return f"Hi {contact},"
        return f"Hi {contact},"

    def _build_opening(self, context: EmailContext, strategy: EmailStrategy) -> str:
        purpose = strategy.purpose

        openings = {
            EmailPurpose.DISCOVERY_FOLLOWUP: (
                "Thank you for taking the time to speak with me earlier. "
                "I enjoyed learning more about your operations."
            ),
            EmailPurpose.PROPOSAL_DELIVERY: (
                "I'm pleased to share the technology solutions proposal we discussed. "
                "This summarizes our recommended approach based on your operational needs."
            ),
            EmailPurpose.PROPOSAL_REMINDER: (
                "I wanted to gently follow up on the proposal I sent over. "
                "I know how busy things get."
            ),
            EmailPurpose.MEETING_RECAP: (
                "Thank you for the productive conversation. Here's a summary of "
                "what we covered and the agreed next steps."
            ),
            EmailPurpose.OBJECTION_RESPONSE: (
                "Thank you for sharing your concerns — they're completely valid, "
                "and I want to make sure we address each one thoroughly."
            ),
            EmailPurpose.CUSTOMER_CHECKIN: (
                "I hope this message finds you well. Just wanted to check in "
                "and see how things are progressing."
            ),
            EmailPurpose.IMPLEMENTATION_KICKOFF: (
                "We're thrilled to get started. Welcome to the Pacific North "
                "Systems family."
            ),
        }
        return openings.get(purpose, "I hope this message finds you well.")

    def _build_body(self, context: EmailContext, strategy: EmailStrategy) -> str:
        parts: list[str] = []

        # Pain point acknowledgment
        if context.pain_points and strategy.purpose in (
            EmailPurpose.DISCOVERY_FOLLOWUP, EmailPurpose.MEETING_RECAP,
        ):
            parts.append("Based on our conversation, I understand that:")
            for p in context.pain_points[:3]:
                parts.append(f"• {p}")
            parts.append("")

        # Solution / value
        if strategy.purpose == EmailPurpose.PROPOSAL_DELIVERY:
            if context.recommended_products:
                parts.append("The proposed solution includes:")
                for p in context.recommended_products[:5]:
                    parts.append(f"• {p}")
                parts.append("")
            if context.budget:
                parts.append(
                    f"Our analysis indicates potential annual savings of {context.budget} "
                    f"through improved operational efficiency."
                )
                parts.append("")

        # Budget discussion
        if strategy.purpose == EmailPurpose.BUDGET_DISCUSSION:
            parts.append(
                "Based on the operational improvements we've identified, "
                "I'd like to discuss the investment range that would make "
                "this initiative feasible for your team."
            )
            parts.append("")

        # Objection response
        if strategy.purpose == EmailPurpose.OBJECTION_RESPONSE and context.objections:
            parts.append("You mentioned:")
            for o in context.objections[:3]:
                parts.append(f"• {o}")
            parts.append("")
            parts.append(
                "Here's how we typically address these:\n"
                "• Training and onboarding are included in every engagement\n"
                "• We offer phased implementation to manage risk\n"
                "• Our support team is available throughout the transition"
            )
            parts.append("")

        # Timeline
        if context.timeline and strategy.purpose in (
            EmailPurpose.PROPOSAL_DELIVERY, EmailPurpose.CONTRACT_FOLLOWUP,
        ):
            parts.append(f"We're targeting {context.timeline} for implementation.")

        # CTA transition
        if strategy.purpose == EmailPurpose.DISCOVERY_FOLLOWUP:
            parts.append("I'd love to schedule a deeper discovery session to understand your current workflow and explore how we can help.")
        elif strategy.purpose == EmailPurpose.PROPOSAL_DELIVERY:
            parts.append("I'm available to walk through this with you and answer any questions at your convenience.")
        elif strategy.purpose == EmailPurpose.PROPOSAL_REMINDER:
            parts.append("If you have any questions, I'm happy to jump on a quick call — no pressure at all.")

        return "\n\n".join(parts) if parts else "I wanted to follow up and see how things are progressing on your end."

    def _build_cta(self, context: EmailContext, strategy: EmailStrategy) -> str:
        ctas = {
            EmailPurpose.DISCOVERY_FOLLOWUP: "Would you be available for a 30-minute call this week?",
            EmailPurpose.PROPOSAL_DELIVERY: "Would it be helpful to schedule a call to walk through the proposal together?",
            EmailPurpose.PROPOSAL_REMINDER: "Let me know if you have any questions — I'm here to help.",
            EmailPurpose.MEETING_SCHEDULING: "What time works best for you?",
            EmailPurpose.MEETING_RECAP: "I'll follow up on the action items we discussed. When would be a good time for our next conversation?",
            EmailPurpose.OBJECTION_RESPONSE: "Would a quick call help clarify any of these points?",
            EmailPurpose.BUDGET_DISCUSSION: "When would be a good time to discuss the investment details?",
            EmailPurpose.CUSTOMER_CHECKIN: "Is there anything we can help with right now?",
            EmailPurpose.IMPLEMENTATION_KICKOFF: "Your project manager will reach out within 24 hours to schedule the kickoff.",
            EmailPurpose.REENGAGEMENT: "Would a brief catch-up call make sense? No pressure at all.",
        }
        return ctas.get(strategy.purpose, "I look forward to hearing from you.")

    def _build_signature(self) -> str:
        return (
            "Best regards,\n"
            "Pacific North Systems\n"
            "Technology Solutions for Modern Operations\n"
            "pacificnorthsystems.com"
        )


# Singleton
_generator: EmailGenerator | None = None


def get_email_generator() -> EmailGenerator:
    global _generator
    if _generator is None:
        _generator = EmailGenerator()
    return _generator
