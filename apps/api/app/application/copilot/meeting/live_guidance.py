"""
Live Guidance Engine — real-time meeting guidance.

Consumes OpportunityIntelligence. Recommends questions, surfaces
missing topics, detects signals and objections. Never analyzes transcript.
"""

from datetime import datetime, UTC

from app.domain.opportunity_intelligence import OpportunityIntelligence
from app.application.copilot.meeting.models import LiveGuidance


class LiveGuidanceEngine:
    def guide(self, oi: OpportunityIntelligence) -> LiveGuidance:
        now = datetime.now(UTC).isoformat()

        missing = self._missing_topics(oi)
        questions = self._recommend_questions(missing)
        signals = [b.value or "" for b in oi.sales.buying_signals if b.value]
        objections = [o.value or "" for o in oi.sales.objections if o.value]
        health = str(oi.deal_health.value) if oi.deal_health.is_known() else "unknown"
        score = oi.opportunity_score.value if oi.opportunity_score.is_known() else 0
        discovery = oi.discovery_score.value if oi.discovery_score.is_known() else 0

        return LiveGuidance(
            missing_topics=missing,
            recommended_questions=questions[:5],
            buying_signals_detected=signals,
            objections_detected=objections,
            deal_health=health,
            opportunity_score=score,
            discovery_progress=discovery,
            recommended_next_action=oi.sales.next_best_action or "Continue discovery",
            generated_at=now,
        )

    def _missing_topics(self, oi: OpportunityIntelligence) -> list[str]:
        missing = []
        if not oi.business.budget.is_known():
            missing.append("Budget")
        if not oi.business.timeline.is_known():
            missing.append("Timeline")
        if not any("decision_maker" in str(s.role.value if hasattr(s.role, "value") else s.role) for s in oi.stakeholders):
            missing.append("Decision Maker")
        if not oi.business.pain_points:
            missing.append("Pain Points")
        if not oi.business.business_goals:
            missing.append("Business Goals")
        if not oi.business.current_process:
            missing.append("Current Process")
        if not oi.business.current_software:
            missing.append("Current Software")
        if not oi.business.constraints:
            missing.append("Technical Constraints")
        if not oi.sales.buying_signals:
            missing.append("Buying Signals")
        return missing

    def _recommend_questions(self, missing: list[str]) -> list[str]:
        q_map = {
            "Budget": "Do you have a budget allocated for this type of initiative?",
            "Timeline": "When would you ideally want to have something in place?",
            "Decision Maker": "Who besides yourself would be involved in this decision?",
            "Pain Points": "What's costing your team the most time right now?",
            "Business Goals": "What would success look like after implementation?",
            "Current Process": "Walk me through how this works today.",
            "Current Software": "What tools are you currently using for this?",
            "Technical Constraints": "Are there any technical requirements we should know about?",
            "Buying Signals": "How does this initiative rank in your current priorities?",
        }
        return [q_map[m] for m in missing if m in q_map]


# Singleton
_engine: LiveGuidanceEngine | None = None

def get_live_guidance_engine() -> LiveGuidanceEngine:
    global _engine
    if _engine is None:
        _engine = LiveGuidanceEngine()
    return _engine
