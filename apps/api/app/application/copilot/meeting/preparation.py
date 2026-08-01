"""
Meeting Preparation Engine — generates complete pre-meeting briefings.

Consumes ONLY OpportunityIntelligence. Produces briefing with company context,
stakeholders, stage, signals, objectives, and strategy.
"""

from datetime import datetime, UTC

from app.domain.opportunity_intelligence import OpportunityIntelligence, OpportunityStage
from app.application.copilot.meeting.models import MeetingBrief


class MeetingPreparationEngine:
    def prepare(self, oi: OpportunityIntelligence) -> MeetingBrief:
        now = datetime.now(UTC).isoformat()
        stage = str(oi.stage.value) if hasattr(oi.stage, "value") else str(oi.stage)

        stakeholders = [
            {"name": s.name, "title": s.title, "role": str(s.role.value) if hasattr(s.role, "value") else str(s.role)}
            for s in oi.stakeholders
        ]
        dms = [s.name for s in oi.stakeholders if "decision_maker" in str(s.role.value if hasattr(s.role, "value") else s.role)]

        prev_meetings = [
            e.description for e in oi.timeline
            if e.event_type.value in ("meeting", "call")
        ][:5]

        pains = [p.value or "" for p in oi.business.pain_points if p.value]
        goals = [g.value or "" for g in oi.business.business_goals if g.value]
        signals = [b.value or "" for b in oi.sales.buying_signals if b.value]
        objections = [o.value or "" for o in oi.sales.objections if o.value]

        objective = self._determine_objective(oi, stage)

        return MeetingBrief(
            company_name=oi.company_name,
            industry=oi.company_industry,
            stakeholders=stakeholders,
            decision_makers=dms,
            previous_meetings=prev_meetings,
            current_stage=stage,
            proposal_status=oi.solutions.proposal_status,
            pain_points=pains,
            business_goals=goals,
            buying_signals=signals,
            objections=objections,
            recommended_strategy=oi.sales.sales_strategy or "Continue discovery",
            estimated_duration="45 minutes" if oi.stage in (OpportunityStage.PROPOSAL, OpportunityStage.NEGOTIATION) else "30 minutes",
            meeting_objective=objective,
            generated_at=now,
        )

    def _determine_objective(self, oi: OpportunityIntelligence, stage: str) -> str:
        objectives = {
            "lead": "Introduce Pacific North Systems and understand {company}'s operational landscape.",
            "qualified": "Explore current workflow and identify operational improvement opportunities.",
            "discovery": "Document current processes, pain points, and requirements for {company}.",
            "solution_design": "Present recommended solution architecture and validate technical requirements.",
            "proposal": "Walk through the proposal, address questions, and confirm next steps.",
            "negotiation": "Finalize terms, timeline, and agreement details.",
            "won": "Kick off implementation and introduce the project team.",
            "implementation": "Review project progress and address any blockers.",
            "support": "Ensure {company} is receiving maximum value from the platform.",
        }
        obj = objectives.get(stage, "Continue building the relationship with {company}.")
        return obj.replace("{company}", oi.company_name or "the organization")


# Singleton
_engine: MeetingPreparationEngine | None = None

def get_preparation_engine() -> MeetingPreparationEngine:
    global _engine
    if _engine is None:
        _engine = MeetingPreparationEngine()
    return _engine
