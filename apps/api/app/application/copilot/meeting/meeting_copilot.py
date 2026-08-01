"""
Meeting Copilot — master orchestrator for meeting preparation, guidance, and follow-up.

Consumes ONLY OpportunityIntelligence. Orchestrates all meeting engines:
    Preparation → Agenda → Questions → Live Guidance → Summary → Actions → Follow-up

Architecture:
    OpportunityIntelligence → MeetingCopilot → Briefing + Guidance + Summary
"""

from app.domain.opportunity_intelligence import OpportunityIntelligence
from app.application.copilot.meeting.preparation import get_preparation_engine
from app.application.copilot.meeting.agenda import get_agenda_generator
from app.application.copilot.meeting.questions import get_question_planner
from app.application.copilot.meeting.live_guidance import get_live_guidance_engine
from app.application.copilot.meeting.summary import get_summary_engine
from app.application.copilot.meeting.actions import get_action_item_engine
from app.application.copilot.meeting.followup import get_followup_engine


class MeetingCopilot:
    def __init__(self):
        self._prep = get_preparation_engine()
        self._agenda = get_agenda_generator()
        self._questions = get_question_planner()
        self._live = get_live_guidance_engine()
        self._summary = get_summary_engine()
        self._actions = get_action_item_engine()
        self._followup = get_followup_engine()

    def prepare(self, oi: OpportunityIntelligence) -> dict:
        brief = self._prep.prepare(oi)
        agenda = self._agenda.generate(oi)
        questions = self._questions.plan(oi)

        return {
            "briefing": {
                "company_name": brief.company_name, "industry": brief.industry,
                "stakeholders": brief.stakeholders, "decision_makers": brief.decision_makers,
                "previous_meetings": brief.previous_meetings, "current_stage": brief.current_stage,
                "proposal_status": brief.proposal_status, "pain_points": brief.pain_points,
                "business_goals": brief.business_goals, "buying_signals": brief.buying_signals,
                "objections": brief.objections, "recommended_strategy": brief.recommended_strategy,
                "estimated_duration": brief.estimated_duration, "meeting_objective": brief.meeting_objective,
            },
            "agenda": {
                "title": agenda.title, "meeting_objective": agenda.meeting_objective,
                "total_duration": agenda.total_duration,
                "items": [{"topic": i.topic, "duration": i.duration, "description": i.description, "priority": i.priority} for i in agenda.items],
            },
            "questions": {
                "answered_count": questions.answered_count, "total_count": questions.total_count,
                "missing_categories": questions.missing_categories,
                "items": [{"category": q.category, "question": q.question, "priority": q.priority, "answered": q.answered, "reason": q.reason} for q in questions.questions],
            },
        }

    def live(self, oi: OpportunityIntelligence) -> dict:
        guidance = self._live.guide(oi)
        return {
            "missing_topics": guidance.missing_topics,
            "recommended_questions": guidance.recommended_questions,
            "buying_signals_detected": guidance.buying_signals_detected,
            "objections_detected": guidance.objections_detected,
            "deal_health": guidance.deal_health,
            "opportunity_score": guidance.opportunity_score,
            "discovery_progress": guidance.discovery_progress,
            "recommended_next_action": guidance.recommended_next_action,
        }

    def summarize(self, oi: OpportunityIntelligence) -> dict:
        summary = self._summary.summarize(oi)
        actions = self._actions.generate(oi)
        followup = self._followup.prepare(oi)

        return {
            "summary": {
                "executive_summary": summary.executive_summary,
                "topics_discussed": summary.topics_discussed,
                "decisions": summary.decisions,
                "risks_identified": summary.risks_identified,
                "customer_goals": summary.customer_goals,
                "pain_points_discussed": summary.pain_points_discussed,
                "open_questions": summary.open_questions,
            },
            "action_items": {
                "total": len(actions.items),
                "customer": [{"description": i.description, "deadline": i.deadline, "priority": i.priority} for i in actions.customer_items],
                "salesperson": [{"description": i.description, "deadline": i.deadline, "priority": i.priority} for i in actions.salesperson_items],
                "technical": [{"description": i.description, "deadline": i.deadline, "priority": i.priority} for i in actions.technical_items],
                "management": [{"description": i.description, "deadline": i.deadline, "priority": i.priority} for i in actions.management_items],
            },
            "follow_up": {
                "meeting_recap": followup.meeting_recap,
                "suggested_email": followup.suggested_email,
                "crm_activity": followup.crm_activity,
                "next_meeting": followup.next_meeting,
                "proposal_recommendation": followup.proposal_recommendation,
            },
        }


# Singleton
_copilot: MeetingCopilot | None = None

def get_meeting_copilot() -> MeetingCopilot:
    global _copilot
    if _copilot is None:
        _copilot = MeetingCopilot()
    return _copilot
