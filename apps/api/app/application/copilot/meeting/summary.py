"""
Meeting Summary Engine — generates post-meeting summaries.

Consumes ONLY OpportunityIntelligence. Produces executive summary,
topics discussed, decisions, risks, goals, pain points, open questions.
"""

from datetime import datetime, UTC

from app.domain.opportunity_intelligence import OpportunityIntelligence
from app.application.copilot.meeting.models import MeetingSummary


class MeetingSummaryEngine:
    def summarize(self, oi: OpportunityIntelligence) -> MeetingSummary:
        now = datetime.now(UTC).isoformat()
        company = oi.company_name or "the organization"

        exec_summary = (
            f"Meeting with {company} to discuss operational improvements. "
            f"Current stage: {oi.stage.value if hasattr(oi.stage, 'value') else oi.stage}. "
        )

        if oi.business.pain_points:
            exec_summary += (
                f"Key pain points identified include {oi.business.pain_points[0].value.lower()}. "
            )

        if oi.sales.buying_signals:
            exec_summary += "Buying signals were positive. "

        if oi.sales.next_best_action:
            exec_summary += f"Next step: {oi.sales.next_best_action}."

        topics = []
        if oi.business.pain_points:
            topics.append("Current operational challenges and pain points")
        if oi.business.current_process:
            topics.append("Current workflow and process documentation")
        if oi.business.current_software:
            topics.append("Existing technology stack and integrations")
        if oi.business.business_goals:
            topics.append("Business goals and success criteria")
        if oi.business.budget.is_known():
            topics.append("Budget and investment discussion")
        if oi.business.timeline.is_known():
            topics.append("Implementation timeline and phasing")

        decisions = []
        if oi.sales.next_best_action:
            decisions.append(f"Next step agreed: {oi.sales.next_best_action}")
        if oi.stage.value in ("proposal", "negotiation"):
            decisions.append("Proceeding to proposal stage")

        risks = [r.value for r in oi.business.operational_risks if r.value]
        if oi.sales.objections:
            risks.extend(o.value for o in oi.sales.objections if o.value)

        goals = [g.value for g in oi.business.business_goals if g.value]
        pains = [p.value for p in oi.business.pain_points if p.value]

        open_qs = []
        if not oi.business.budget.is_known():
            open_qs.append("Confirm budget allocation")
        if not oi.business.timeline.is_known():
            open_qs.append("Clarify implementation timeline")
        if not any("decision_maker" in str(s.role.value if hasattr(s.role, "value") else s.role) for s in oi.stakeholders):
            open_qs.append("Identify decision maker")

        return MeetingSummary(
            executive_summary=exec_summary,
            topics_discussed=topics,
            decisions=decisions,
            risks_identified=risks,
            customer_goals=goals,
            pain_points_discussed=pains,
            open_questions=open_qs,
            generated_at=now,
        )


# Singleton
_engine: MeetingSummaryEngine | None = None

def get_summary_engine() -> MeetingSummaryEngine:
    global _engine
    if _engine is None:
        _engine = MeetingSummaryEngine()
    return _engine
