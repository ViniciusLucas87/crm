"""
Follow-Up Engine — prepares post-meeting follow-up materials.

Consumes ONLY OpportunityIntelligence. Generates meeting recap,
suggested email, CRM activity, next meeting recommendation,
and proposal recommendation.
"""

from datetime import datetime, UTC

from app.domain.opportunity_intelligence import OpportunityIntelligence, OpportunityStage
from app.application.copilot.meeting.models import FollowUpPlan


class FollowUpEngine:
    def prepare(self, oi: OpportunityIntelligence) -> FollowUpPlan:
        now = datetime.now(UTC).isoformat()
        company = oi.company_name or "the organization"
        stage = str(oi.stage.value) if hasattr(oi.stage, "value") else str(oi.stage)

        # Recap
        pains = [p.value for p in oi.business.pain_points[:3] if p.value]
        recap = f"Meeting with {company} to discuss operational improvements. "
        if pains:
            recap += f"Key pain points: {'; '.join(pains)}. "
        if oi.sales.next_best_action:
            recap += f"Next step: {oi.sales.next_best_action}."

        # Suggested email
        contact = oi.stakeholders[0].name.split(" ")[0] if oi.stakeholders else "there"
        email = (
            f"Subject: Following up — {company} Discussion\n\n"
            f"Hi {contact},\n\n"
            f"Thank you for the productive conversation today. "
            f"I've captured the key points and action items.\n\n"
        )
        if pains:
            email += "We discussed:\n" + "\n".join(f"• {p}" for p in pains[:3]) + "\n\n"
        email += (
            f"I'll follow up on the next steps we discussed and look forward "
            f"to continuing the conversation.\n\n"
            f"Best regards,\nPacific North Systems"
        )

        # CRM activity
        crm = f"Meeting held — Stage: {stage}. "
        if pains:
            crm += f"Pain points: {'; '.join(pains[:2])}. "

        # Next meeting
        next_stage_map = {
            "lead": "Discovery call",
            "qualified": "Technical discovery",
            "discovery": "Solution design review",
            "solution_design": "Proposal walkthrough",
            "proposal": "Proposal Q&A",
            "negotiation": "Contract finalization",
        }
        next_meeting = next_stage_map.get(stage, "Follow-up call")

        # Proposal recommendation
        proposal_rec = ""
        if oi.stage in (OpportunityStage.DISCOVERY, OpportunityStage.SOLUTION_DESIGN):
            proposal_rec = "Prepare proposal after completing technical discovery."
        elif oi.stage == OpportunityStage.PROPOSAL:
            proposal_rec = "Proposal is ready — follow up within 3 days."
        elif oi.stage == OpportunityStage.NEGOTIATION:
            proposal_rec = "Proposal under negotiation — prepare for close."

        return FollowUpPlan(
            meeting_recap=recap,
            suggested_email=email,
            crm_activity=crm,
            next_meeting=next_meeting,
            proposal_recommendation=proposal_rec,
            generated_at=now,
        )


# Singleton
_engine: FollowUpEngine | None = None

def get_followup_engine() -> FollowUpEngine:
    global _engine
    if _engine is None:
        _engine = FollowUpEngine()
    return _engine
