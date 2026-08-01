"""
Email Strategy Engine — determines email purpose, type, and tone.

Consumes ONLY OpportunityIntelligence. Determines what kind of email
to send based on the current opportunity state.
"""

from __future__ import annotations

from datetime import datetime, UTC

from app.domain.opportunity_intelligence import OpportunityIntelligence, OpportunityStage
from app.application.copilot.email.models import EmailStrategy, EmailPurpose, EmailType


class EmailStrategyEngine:
    """Determines email purpose and strategy from OpportunityIntelligence.

    Evaluates opportunity stage, deal health, proposal status, objections,
    and buying signals to recommend the most effective email approach.
    """

    def determine(self, oi: OpportunityIntelligence) -> EmailStrategy:
        now = datetime.now(UTC).isoformat()
        stage = oi.stage

        purpose, etype, focus, avoid = self._evaluate(oi)

        return EmailStrategy(
            purpose=purpose,
            email_type=etype,
            tone=self._determine_tone(oi),
            focus_points=focus,
            avoid_topics=avoid,
            generated_at=now,
        )

    def _evaluate(self, oi: OpportunityIntelligence) -> tuple[str, str, list[str], list[str]]:
        stage = oi.stage
        has_proposal = oi.solutions.proposal_status != "none"
        has_objections = len(oi.sales.objections) > 0
        has_signals = len(oi.sales.buying_signals) > 0
        has_budget = oi.business.budget.is_known()
        has_timeline = oi.business.timeline.is_known()

        # ── Stage-based strategy ──

        if stage in (OpportunityStage.LEAD,):
            return (
                EmailPurpose.DISCOVERY_FOLLOWUP, EmailType.STANDARD,
                ["Introduction", "Value proposition overview", "Discovery meeting invitation"],
                ["Pricing details", "Technical specifications"],
            )

        if stage == OpportunityStage.QUALIFIED:
            return (
                EmailPurpose.DISCOVERY_FOLLOWUP, EmailType.STANDARD,
                ["Pain point acknowledgment", "Process exploration", "Next meeting scheduling"],
                ["Pricing", "Contract terms"],
            )

        if stage == OpportunityStage.DISCOVERY:
            if has_signals and not has_budget:
                return (
                    EmailPurpose.BUDGET_DISCUSSION, EmailType.STANDARD,
                    ["Value demonstration", "ROI preview", "Budget exploration"],
                    ["Final pricing", "Contract language"],
                )
            return (
                EmailPurpose.DISCOVERY_FOLLOWUP, EmailType.STANDARD,
                ["Pain point validation", "Operational impact", "Success criteria"],
                ["Pricing until pain is quantified"],
            )

        if stage == OpportunityStage.SOLUTION_DESIGN:
            return (
                EmailPurpose.TECHNICAL_CLARIFICATION, EmailType.TECHNICAL,
                ["Solution architecture overview", "Integration approach", "Technical validation"],
                ["Final pricing", "Contract"],
            )

        if stage == OpportunityStage.PROPOSAL:
            if has_proposal:
                if has_objections:
                    return (
                        EmailPurpose.OBJECTION_RESPONSE, EmailType.STANDARD,
                        ["Objection acknowledgment", "Clarification", "Value reinforcement"],
                        ["Defensiveness", "Discounting without justification"],
                    )
                return (
                    EmailPurpose.PROPOSAL_DELIVERY, EmailType.EXECUTIVE_SUMMARY,
                    ["Proposal highlights", "ROI summary", "Next steps"],
                    ["New technical details", "Additional requirements"],
                )
            return (
                EmailPurpose.PROPOSAL_DELIVERY, EmailType.STANDARD,
                ["Solution summary", "Timeline overview", "Decision timeline"],
                ["Competitor comparisons"],
            )

        if stage == OpportunityStage.NEGOTIATION:
            return (
                EmailPurpose.CONTRACT_FOLLOWUP, EmailType.FORMAL,
                ["Terms clarification", "Timeline confirmation", "Decision support"],
                ["New technical discussions", "Scope expansion"],
            )

        if stage == OpportunityStage.WON:
            return (
                EmailPurpose.IMPLEMENTATION_KICKOFF, EmailType.STANDARD,
                ["Celebration", "Next steps", "Team introductions"],
                ["Upselling", "Additional costs"],
            )

        if stage == OpportunityStage.IMPLEMENTATION:
            return (
                EmailPurpose.CUSTOMER_CHECKIN, EmailType.FRIENDLY,
                ["Progress update", "Support availability", "Feedback request"],
                ["New sales pitches"],
            )

        if stage == OpportunityStage.LOST:
            return (
                EmailPurpose.LOST_RECOVERY, EmailType.STANDARD,
                ["Relationship maintenance", "Value reinforcement", "Future check-in"],
                ["Aggressive re-selling", "Pressure tactics"],
            )

        # Default
        return (
            EmailPurpose.CUSTOMER_CHECKIN, EmailType.STANDARD,
            ["Relationship building", "Value check-in"],
            ["Pricing", "Technical details"],
        )

    def _determine_tone(self, oi: OpportunityIntelligence) -> str:
        urgency = oi.sales.urgency.value
        if hasattr(urgency, "value"):
            urgency_val = urgency.value if hasattr(urgency, "value") else str(urgency)
        else:
            urgency_val = str(urgency)

        if urgency_val in ("critical", "high"):
            return "direct"
        if oi.stage in (OpportunityStage.WON, OpportunityStage.IMPLEMENTATION):
            return "warm"
        if oi.stage == OpportunityStage.NEGOTIATION:
            return "formal"
        if len(oi.sales.buying_signals) >= 2:
            return "confident"
        return "professional"


# Singleton
_engine: EmailStrategyEngine | None = None


def get_email_strategy_engine() -> EmailStrategyEngine:
    global _engine
    if _engine is None:
        _engine = EmailStrategyEngine()
    return _engine
