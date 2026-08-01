"""
Agenda Generator — creates meeting agendas from OpportunityIntelligence.

Determines topics, durations, and priorities based on opportunity stage.
"""

from datetime import datetime, UTC

from app.domain.opportunity_intelligence import OpportunityIntelligence, OpportunityStage
from app.application.copilot.meeting.models import MeetingAgenda, AgendaItem


class AgendaGenerator:
    def generate(self, oi: OpportunityIntelligence, duration_minutes: int = 30) -> MeetingAgenda:
        now = datetime.now(UTC).isoformat()
        stage = oi.stage
        company = oi.company_name or "the organization"

        items = self._build_items(oi, stage, duration_minutes)

        total = sum(self._parse_duration(i.duration) for i in items)
        return MeetingAgenda(
            title=f"{company} — {self._stage_label(stage)} Meeting Agenda",
            items=items,
            total_duration=f"{total} minutes",
            meeting_objective=self._objective_for_stage(stage, company),
            generated_at=now,
        )

    def _build_items(self, oi, stage, total_min) -> list[AgendaItem]:
        templates = {
            OpportunityStage.LEAD: [
                ("Introductions & Company Overview", "5 min", "Introduce PNS, understand {company}'s business"),
                ("Current Operations Overview", "10 min", "Walk through how {company} operates today"),
                ("Pain Points & Challenges", "10 min", "Identify key operational friction points"),
                ("Next Steps", "5 min", "Confirm follow-up actions and timeline"),
            ],
            OpportunityStage.DISCOVERY: [
                ("Introduction & Context", "5 min", "Review previous discussions and set objectives"),
                ("Current Process Deep Dive", "15 min", "Document current workflow in detail"),
                ("Requirements & Constraints", "10 min", "Capture technical, budget, and timeline requirements"),
                ("Success Criteria", "5 min", "Define what success looks like for {company}"),
                ("Next Steps & Timeline", "5 min", "Confirm next meeting and action items"),
            ],
            OpportunityStage.PROPOSAL: [
                ("Welcome & Agenda Review", "5 min", "Set expectations for the session"),
                ("Executive Summary Walkthrough", "10 min", "Present key proposal highlights and ROI"),
                ("Solution Architecture Review", "15 min", "Walk through recommended components and rationale"),
                ("Implementation Timeline", "5 min", "Review phased approach and milestones"),
                ("Q&A and Objections", "10 min", "Address questions and concerns"),
                ("Next Steps", "5 min", "Confirm decision timeline and follow-up"),
            ],
            OpportunityStage.NEGOTIATION: [
                ("Opening & Context", "5 min", "Reaffirm partnership vision"),
                ("Terms Review", "15 min", "Discuss agreement terms and timeline"),
                ("Addressing Concerns", "10 min", "Resolve outstanding questions"),
                ("Decision & Next Steps", "5 min", "Confirm path to signature"),
            ],
        }

        default = [
            ("Check-in & Context", "5 min", "Review current status and objectives"),
            ("Key Discussion Topics", "15 min", "Address priority items for {company}"),
            ("Action Items & Next Steps", "5 min", "Confirm follow-up and timeline"),
        ]

        item_templates = templates.get(stage, default)

        result = []
        priority = "high"
        for label, duration, desc in item_templates:
            result.append(AgendaItem(
                topic=label,
                duration=duration,
                description=desc.replace("{company}", oi.company_name or "the organization"),
                priority=priority,
            ))
            priority = "medium"  # First item is highest priority

        return result

    def _parse_duration(self, dur: str) -> int:
        try:
            return int(dur.split()[0])
        except (ValueError, IndexError):
            return 5

    def _stage_label(self, stage) -> str:
        labels = {
            OpportunityStage.LEAD: "Introduction",
            OpportunityStage.QUALIFIED: "Discovery",
            OpportunityStage.DISCOVERY: "Discovery",
            OpportunityStage.SOLUTION_DESIGN: "Solution Design",
            OpportunityStage.PROPOSAL: "Proposal Review",
            OpportunityStage.NEGOTIATION: "Negotiation",
        }
        return labels.get(stage, "Meeting")

    def _objective_for_stage(self, stage, company) -> str:
        objectives = {
            OpportunityStage.LEAD: f"Introduce Pacific North Systems and understand {company}'s operational needs.",
            OpportunityStage.DISCOVERY: f"Document {company}'s current workflow, pain points, and requirements.",
            OpportunityStage.PROPOSAL: f"Present the proposed solution and secure agreement to move forward.",
            OpportunityStage.NEGOTIATION: f"Finalize terms and timeline for the engagement.",
        }
        return objectives.get(stage, f"Advance the relationship with {company}.")


# Singleton
_engine: AgendaGenerator | None = None

def get_agenda_generator() -> AgendaGenerator:
    global _engine
    if _engine is None:
        _engine = AgendaGenerator()
    return _engine
