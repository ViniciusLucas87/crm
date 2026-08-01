"""
Sprint 47.7 — Next Commitment Engine & Meeting-Close Assistant

Determines the best next commitment and provides exact closing language.
Never recommends "send information" when a stronger step is appropriate.
"""

from dataclasses import dataclass, field
from app.application.transcription.deal_narrative import DealNarrative


@dataclass
class CommitmentRecommendation:
    """A recommended next commitment with exact closing language."""
    commitment_type: str          # continue_discovery | workflow_mapping | technical_discovery | stakeholder_include | proposal | paid_discovery
    title: str
    suggested_wording: str        # Exact two-option close when applicable
    reason: str
    fallback: str = ""
    alternatives: list[str] = field(default_factory=list)
    confidence: int = 75


CLOSE_TEMPLATES = {
    "workflow_mapping": CommitmentRecommendation(
        commitment_type="workflow_mapping",
        title="Schedule workflow-mapping session",
        suggested_wording="Based on what you've described, the best next step would be to map this workflow with the person who owns it operationally. We could identify where the manual work occurs and show you what a practical solution could look like. Would next Tuesday or Thursday work better?",
        reason="Enough discovery to show value. A collaborative workflow session advances the deal without pressure.",
        fallback="Could I send you a short outline and reconnect next week with the operations owner?",
        alternatives=[
            "The next useful step would be to walk through your current process together. Would next week work?",
            "I'd like to prepare a brief workflow map based on what you've shared. Could we review it together?",
        ],
        confidence=82,
    ),
    "technical_discovery": CommitmentRecommendation(
        commitment_type="technical_discovery",
        title="Schedule technical discovery",
        suggested_wording="I think there's enough here to justify a focused technical discussion. Could we schedule 30 minutes with the people responsible for operations and your current systems?",
        reason="Pain and impact are clear. Technical requirements need validation before a proposal.",
        fallback="Could I prepare a short technical questionnaire and we'll review it next week?",
        alternatives=[
            "The next step should be understanding your technical environment. Would your IT team be available for a brief call?",
            "Let's schedule a focused session to review your current systems and integration needs.",
        ],
        confidence=80,
    ),
    "stakeholder_include": CommitmentRecommendation(
        commitment_type="stakeholder_include",
        title="Include the decision maker",
        suggested_wording="Who else should be involved in the next discussion so we can understand the operational and technical requirements together? Would it make sense to schedule that session now while we're both here?",
        reason="Current contact is not the final decision maker. Engaging stakeholders early prevents later delays.",
        fallback="Could you introduce me to the right person when the time is right?",
        alternatives=[
            "What would they need to see to feel confident? I can prepare something specifically for them.",
            "Should we set up a brief introduction call with them next week?",
        ],
        confidence=85,
    ),
    "proposal": CommitmentRecommendation(
        commitment_type="proposal",
        title="Move toward proposal",
        suggested_wording="I have enough information to prepare a focused proposal around this workflow. Could we schedule a review meeting next week so we can walk through it together rather than just emailing a document?",
        reason="Discovery is thorough, pain is quantified, solution fit is clear. A proposal review meeting advances toward a decision.",
        fallback="I'll prepare a brief scope document and we can discuss it when you're ready.",
        alternatives=[
            "The next step should be a scoped proposal based on what we've discussed. Does next week work to review it?",
            "I'd like to prepare a proposal with specific recommendations. Let's schedule time to walk through it.",
        ],
        confidence=85,
    ),
    "paid_discovery": CommitmentRecommendation(
        commitment_type="paid_discovery",
        title="Propose paid discovery engagement",
        suggested_wording="The most responsible next step would be a short paid discovery engagement where we document the process, define requirements, and produce an implementation plan. This gives you a concrete roadmap before committing to a larger project.",
        reason="Complex workflow requires deeper analysis. Paid discovery protects both parties and produces actionable deliverables.",
        fallback="We could start with a brief scoping session at no cost and then discuss a formal discovery if it makes sense.",
        alternatives=[
            "A focused discovery engagement would give us both clarity on scope and approach. Would that be worth exploring?",
        ],
        confidence=75,
    ),
    "continue_discovery": CommitmentRecommendation(
        commitment_type="continue_discovery",
        title="Continue discovery",
        suggested_wording="",
        reason="Not enough information yet to recommend a specific close. Continue qualifying.",
        confidence=50,
    ),
}

# Progression priority: which close to recommend based on narrative state
CLOSE_PROGRESSION = [
    "continue_discovery",
    "stakeholder_include",
    "workflow_mapping",
    "technical_discovery",
    "proposal",
    "paid_discovery",
]


class NextCommitmentEngine:
    """Determines the best realistic next commitment.
    
    Never recommends "send information" when a stronger qualified step is appropriate.
    Prefers two-option scheduling closes.
    """
    
    def __init__(self):
        pass
    
    def determine(self, narrative: DealNarrative) -> CommitmentRecommendation:
        """Determine the best next commitment based on the deal narrative."""
        
        # ── Strong case with decision maker unknown → stakeholder include first ──
        if (narrative.quantified_cost and 
            narrative.urgency in ("medium", "high") and
            narrative.decision_process == "unknown" and
            narrative.solution_hypothesis):
            return CLOSE_TEMPLATES["stakeholder_include"]
        
        # ── Quantified pain + urgency + solution → proposal ──
        if (narrative.quantified_cost and
            narrative.urgency in ("medium", "high") and
            narrative.solution_hypothesis and
            narrative.decision_process != "unknown" and
            len(narrative.micro_commitments) >= 3):
            return CLOSE_TEMPLATES["proposal"]
        
        # ── Good discovery + solution fit → technical discovery ──
        if (narrative.operational_problem and
            narrative.business_impact and
            narrative.solution_hypothesis and
            narrative.urgency != "unknown"):
            return CLOSE_TEMPLATES["technical_discovery"]
        
        # ── Pain identified + impact understood → workflow mapping ──
        if (narrative.operational_problem and
            narrative.business_impact and
            len(narrative.micro_commitments) >= 1):
            return CLOSE_TEMPLATES["workflow_mapping"]
        
        # ── Need more discovery ──
        return CLOSE_TEMPLATES["continue_discovery"]
    
    def get_objection_to_commitment(self, objection: str) -> CommitmentRecommendation:
        """After handling an objection, recommend the path back to commitment."""
        if "think about" in objection.lower() or "need to" in objection.lower():
            return CommitmentRecommendation(
                commitment_type="workflow_mapping",
                title="Address hesitation with value",
                suggested_wording="Of course. What specifically would you need to understand before deciding whether to move forward? Would a workflow map and preliminary ROI estimate help you evaluate it?",
                reason="Acknowledge the hesitation, then offer a low-risk next step that provides concrete value.",
                fallback="Let me prepare a brief outline of what we discussed and you can review it at your convenience.",
                alternatives=[
                    "I understand. The next useful step would be to quantify the potential improvement so you have clear numbers to work with.",
                ],
                confidence=82,
            )
        
        if "expensive" in objection.lower() or "cost" in objection.lower() or "budget" in objection.lower():
            return CommitmentRecommendation(
                commitment_type="workflow_mapping",
                title="Reframe cost as investment",
                suggested_wording="I understand budget is a concern. The best way to evaluate the investment would be to map the current cost against the expected improvement. Would a focused workflow session help us build that comparison?",
                reason="Don't defend price — offer a collaborative way to evaluate value.",
                fallback="Let me prepare a brief ROI estimate based on what you've shared.",
                confidence=80,
            )
        
        return CLOSE_TEMPLATES["continue_discovery"]
