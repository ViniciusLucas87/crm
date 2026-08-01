"""
Email Templates — reusable templates for common sales email scenarios.

Template variables: company, contact, pain_points, products, roi, proposal_link, meeting_link.
"""

from app.application.copilot.email.models import EmailTemplate, EmailPurpose


TEMPLATES: dict[str, EmailTemplate] = {
    EmailPurpose.DISCOVERY_FOLLOWUP: EmailTemplate(
        id="discovery_followup",
        name="Discovery Follow-up",
        description="Follow up after an initial discovery conversation",
        purpose=EmailPurpose.DISCOVERY_FOLLOWUP,
        subject_template="Following up: {company} Operations Discussion",
        body_template=(
            "Hi {contact},\n\n"
            "Thank you for taking the time to discuss {company}'s operations earlier.\n\n"
            "{pain_points_section}"
            "\n\n"
            "I'd like to schedule a deeper discovery session to understand your current "
            "workflow and explore how we might help streamline operations.\n\n"
            "Would {meeting_link} work for a 30-minute conversation this week?\n\n"
            "Looking forward to continuing the discussion."
        ),
        variables=["company", "contact", "pain_points_section", "meeting_link"],
    ),
    EmailPurpose.PROPOSAL_DELIVERY: EmailTemplate(
        id="proposal_delivery",
        name="Proposal Delivery",
        description="Deliver a proposal with key highlights",
        purpose=EmailPurpose.PROPOSAL_DELIVERY,
        subject_template="Technology Solutions Proposal for {company}",
        body_template=(
            "Hi {contact},\n\n"
            "I'm pleased to share the Technology Solutions Proposal we discussed.\n\n"
            "{roi_highlights}"
            "\n\n"
            "Key highlights:\n"
            "{highlights}"
            "\n\n"
            "You can review the complete proposal here: {proposal_link}\n\n"
            "I'm available to walk through any questions. Would a call this week work?\n\n"
            "Looking forward to your thoughts."
        ),
        variables=["company", "contact", "roi_highlights", "highlights", "proposal_link"],
    ),
    EmailPurpose.PROPOSAL_REMINDER: EmailTemplate(
        id="proposal_reminder",
        name="Proposal Reminder",
        description="Gentle reminder to review a sent proposal",
        purpose=EmailPurpose.PROPOSAL_REMINDER,
        subject_template="Quick follow-up: {company} Proposal",
        body_template=(
            "Hi {contact},\n\n"
            "I wanted to check in on the proposal we sent over. I know you've been busy.\n\n"
            "If you have any questions, I'm happy to walk through it — no pressure at all.\n\n"
            "You can find it here: {proposal_link}\n\n"
            "Looking forward to hearing your thoughts when you've had a chance to review."
        ),
        variables=["company", "contact", "proposal_link"],
    ),
    EmailPurpose.MEETING_SCHEDULING: EmailTemplate(
        id="meeting_scheduling",
        name="Meeting Scheduling",
        description="Schedule a discovery or follow-up meeting",
        purpose=EmailPurpose.MEETING_SCHEDULING,
        subject_template="Let's connect: {company} Operations Review",
        body_template=(
            "Hi {contact},\n\n"
            "I'd like to set up some time to discuss how we might help {company} "
            "address {pain_point_summary}.\n\n"
            "Would any of these times work for a 30-minute call?\n"
            "{meeting_link}\n\n"
            "Looking forward to connecting."
        ),
        variables=["company", "contact", "pain_point_summary", "meeting_link"],
    ),
    EmailPurpose.MEETING_RECAP: EmailTemplate(
        id="meeting_recap",
        name="Meeting Recap",
        description="Send a recap after a meeting with action items",
        purpose=EmailPurpose.MEETING_RECAP,
        subject_template="Recap: {company} Discussion — Next Steps",
        body_template=(
            "Hi {contact},\n\n"
            "Thank you for the productive conversation earlier. Here's a quick recap:\n\n"
            "{recap_points}"
            "\n\n"
            "Next steps:\n"
            "{next_steps}"
            "\n\n"
            "I'll follow up on my action items and look forward to our next conversation."
        ),
        variables=["company", "contact", "recap_points", "next_steps"],
    ),
    EmailPurpose.OBJECTION_RESPONSE: EmailTemplate(
        id="objection_response",
        name="Objection Response",
        description="Address specific concerns or objections",
        purpose=EmailPurpose.OBJECTION_RESPONSE,
        subject_template="Re: {company} — Addressing Your Questions",
        body_template=(
            "Hi {contact},\n\n"
            "Thank you for sharing your concerns — they're completely valid and I want to address them directly.\n\n"
            "{objection_responses}"
            "\n\n"
            "I hope this helps clarify. I'm happy to discuss any of these points further.\n\n"
            "Would a quick call help?"
        ),
        variables=["company", "contact", "objection_responses"],
    ),
    EmailPurpose.IMPLEMENTATION_KICKOFF: EmailTemplate(
        id="implementation_kickoff",
        name="Implementation Kickoff",
        description="Kick off the implementation phase after closing",
        purpose=EmailPurpose.IMPLEMENTATION_KICKOFF,
        subject_template="Welcome aboard: {company} Implementation Kickoff",
        body_template=(
            "Hi {contact},\n\n"
            "We're excited to get started! Welcome to the Pacific North Systems family.\n\n"
            "Here's what happens next:\n"
            "{kickoff_steps}"
            "\n\n"
            "Your dedicated project manager will reach out within 24 hours to schedule "
            "the kickoff meeting.\n\n"
            "Looking forward to building something great together."
        ),
        variables=["company", "contact", "kickoff_steps"],
    ),
    EmailPurpose.CUSTOMER_CHECKIN: EmailTemplate(
        id="customer_checkin",
        name="Customer Check-in",
        description="Check in with an existing customer",
        purpose=EmailPurpose.CUSTOMER_CHECKIN,
        subject_template="Checking in: How are things going at {company}?",
        body_template=(
            "Hi {contact},\n\n"
            "Just wanted to check in and see how things are going. "
            "Is there anything we can help with?\n\n"
            "We're here if you need anything at all.\n\n"
            "Hope all is well."
        ),
        variables=["company", "contact"],
    ),
    EmailPurpose.REENGAGEMENT: EmailTemplate(
        id="reengagement",
        name="Re-engagement",
        description="Re-engage a dormant opportunity",
        purpose=EmailPurpose.REENGAGEMENT,
        subject_template="Thought of {company} — Checking In",
        body_template=(
            "Hi {contact},\n\n"
            "I was thinking about our earlier conversations and wanted to check in. "
            "I know priorities shift, and I wanted to see if {pain_point_summary} "
            "is still something you're thinking about.\n\n"
            "No pressure at all — just wanted to see how things are going.\n\n"
            "Would a brief catch-up call make sense?"
        ),
        variables=["company", "contact", "pain_point_summary"],
    ),
    EmailPurpose.THANK_YOU: EmailTemplate(
        id="thank_you",
        name="Thank You",
        description="Send a thank you note after a meeting or milestone",
        purpose=EmailPurpose.THANK_YOU,
        subject_template="Thank you, {contact}",
        body_template=(
            "Hi {contact},\n\n"
            "I wanted to take a moment to say thank you. "
            "I really appreciate the time and insight you've shared about {company}.\n\n"
            "We're looking forward to continuing to work together.\n\n"
            "Have a great week."
        ),
        variables=["company", "contact"],
    ),
}


def get_template(purpose: str) -> EmailTemplate | None:
    return TEMPLATES.get(purpose)


def list_templates() -> list[dict]:
    return [
        {"id": t.id, "name": t.name, "description": t.description, "purpose": t.purpose}
        for t in TEMPLATES.values()
    ]
