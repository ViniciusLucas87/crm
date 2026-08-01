"""
Question Planner — recommends discovery questions by category.

Consumes ONLY OpportunityIntelligence. Identifies missing information
and recommends questions to maximize discovery. Tracks answered status.
"""

from datetime import datetime, UTC

from app.domain.opportunity_intelligence import OpportunityIntelligence, OpportunityStage
from app.application.copilot.meeting.models import DiscoveryQuestion, QuestionPlan


# ── Question bank organized by category ──

QUESTION_BANK: dict[str, list[dict]] = {
    "discovery": [
        {"q": "Walk me through how this process works today — from start to finish.", "triggers": "current_process"},
        {"q": "How many people are involved in this workflow on a daily basis?", "triggers": "employees"},
        {"q": "What does your current technology stack look like for managing operations?", "triggers": "current_software"},
    ],
    "business": [
        {"q": "What would success look like six months after implementing a solution?", "triggers": "goals"},
        {"q": "What's driving the decision to explore a solution now?", "triggers": "urgency"},
        {"q": "How does this initiative align with your broader business goals?", "triggers": "goals"},
    ],
    "technical": [
        {"q": "What systems would a new solution need to integrate with?", "triggers": "constraint"},
        {"q": "Are there any security or compliance requirements we should be aware of?", "triggers": "compliance"},
        {"q": "How do you currently handle data between your different systems?", "triggers": "integration"},
    ],
    "operational": [
        {"q": "What's the most time-consuming part of this process for your team?", "triggers": "pain_point"},
        {"q": "How do you currently handle exceptions or edge cases?", "triggers": "current_process"},
        {"q": "How much time does this process consume across the team each week?", "triggers": "pain_point"},
    ],
    "financial": [
        {"q": "Do you have a budget allocated for this initiative?", "triggers": "budget"},
        {"q": "How do you typically evaluate the ROI of technology investments?", "triggers": "budget"},
        {"q": "What's the cost of the current process in terms of time and resources?", "triggers": "pain_point"},
    ],
    "decision_making": [
        {"q": "Who besides yourself would be involved in a decision like this?", "triggers": "decision_maker"},
        {"q": "What does your approval process typically look like?", "triggers": "decision_maker"},
        {"q": "Have you evaluated similar solutions before? What was that process like?", "triggers": "competitor"},
    ],
    "implementation": [
        {"q": "What timeframe are you working toward for implementation?", "triggers": "timeline"},
        {"q": "How do you typically handle change management and training?", "triggers": "implementation"},
        {"q": "What would a successful rollout look like from your perspective?", "triggers": "implementation"},
    ],
    "risk": [
        {"q": "What are the biggest risks you see in this project?", "triggers": "risk"},
        {"q": "What happens if nothing changes in the next 6-12 months?", "triggers": "urgency"},
        {"q": "Are there any organizational changes on the horizon that might affect this?", "triggers": "risk"},
    ],
}


class QuestionPlanner:
    def plan(self, oi: OpportunityIntelligence) -> QuestionPlan:
        now = datetime.now(UTC).isoformat()
        questions: list[DiscoveryQuestion] = []

        # Determine what's known
        known = self._known_fields(oi)
        all_known = set(known)

        for category, qdefs in QUESTION_BANK.items():
            for qdef in qdefs:
                trigger = qdef["triggers"]
                answered = trigger in all_known
                priority = 8 if not answered else 3
                questions.append(DiscoveryQuestion(
                    category=category,
                    question=qdef["q"],
                    priority=priority,
                    answered=answered,
                    reason=f"Information about {trigger} {'already captured' if answered else 'still needed'}",
                ))

        # Sort: unanswered first, then by priority
        questions.sort(key=lambda q: (q.answered, -q.priority))

        answered_count = sum(1 for q in questions if q.answered)
        missing_categories = [
            cat for cat in QUESTION_BANK
            if not any(q.answered for q in questions if q.category == cat)
        ]

        return QuestionPlan(
            questions=questions,
            answered_count=answered_count,
            total_count=len(questions),
            missing_categories=missing_categories,
            generated_at=now,
        )

    def _known_fields(self, oi: OpportunityIntelligence) -> list[str]:
        known = []
        if oi.business.current_process and any(p.value for p in oi.business.current_process):
            known.append("current_process")
        if oi.business.current_software and any(s.value for s in oi.business.current_software):
            known.append("current_software")
        if oi.company_employees:
            known.append("employees")
        if oi.business.business_goals and any(g.value for g in oi.business.business_goals):
            known.append("goals")
        if oi.sales.urgency.is_known():
            known.append("urgency")
        if oi.business.constraints and any(c.value for c in oi.business.constraints):
            known.append("constraint")
        if oi.business.compliance_requirements and any(c.value for c in oi.business.compliance_requirements):
            known.append("compliance")
        if oi.business.pain_points and any(p.value for p in oi.business.pain_points):
            known.append("pain_point")
        if oi.business.budget.is_known():
            known.append("budget")
        if any("decision_maker" in str(s.role.value if hasattr(s.role, "value") else s.role) for s in oi.stakeholders):
            known.append("decision_maker")
        if oi.business.timeline.is_known():
            known.append("timeline")
        if any(r.value for r in oi.business.operational_risks if r.value):
            known.append("risk")
        return known


# Singleton
_engine: QuestionPlanner | None = None

def get_question_planner() -> QuestionPlanner:
    global _engine
    if _engine is None:
        _engine = QuestionPlanner()
    return _engine
