"""
Action Item Engine — generates action items by owner.

Consumes ONLY OpportunityIntelligence. Separates items by customer,
salesperson, technical team, and management with deadlines and priority.
"""

from datetime import datetime, UTC

from app.domain.opportunity_intelligence import OpportunityIntelligence, OpportunityStage
from app.application.copilot.meeting.models import ActionItem, ActionPlan


class ActionItemEngine:
    def generate(self, oi: OpportunityIntelligence) -> ActionPlan:
        now = datetime.now(UTC).isoformat()
        stage = oi.stage

        items: list[ActionItem] = []

        # Customer items
        if not oi.business.budget.is_known():
            items.append(ActionItem("Confirm budget allocation for project", "customer", "1 week", "high"))
        if not oi.business.timeline.is_known():
            items.append(ActionItem("Clarify target implementation timeline", "customer", "1 week", "high"))
        items.append(ActionItem("Review proposal materials", "customer", "1 week", "medium"))

        # Salesperson items
        if stage in (OpportunityStage.DISCOVERY, OpportunityStage.QUALIFIED, OpportunityStage.LEAD):
            items.append(ActionItem("Document current workflow in detail", "salesperson", "3 days", "high"))
            items.append(ActionItem("Prepare solution architecture overview", "salesperson", "5 days", "medium"))
        elif stage == OpportunityStage.PROPOSAL:
            items.append(ActionItem("Address open questions from proposal review", "salesperson", "2 days", "high"))
            items.append(ActionItem("Schedule follow-up call to discuss proposal", "salesperson", "2 days", "high"))
        elif stage == OpportunityStage.NEGOTIATION:
            items.append(ActionItem("Prepare revised terms based on discussion", "salesperson", "3 days", "high"))
        items.append(ActionItem("Log meeting notes in CRM", "salesperson", "Same day", "high"))

        # Technical items
        if oi.business.constraints:
            items.append(ActionItem("Validate technical requirements and integration points", "technical", "1 week", "medium"))
        if oi.business.compliance_requirements:
            items.append(ActionItem("Review compliance requirements and identify impacts", "technical", "1 week", "medium"))

        # Management items
        if stage in (OpportunityStage.PROPOSAL, OpportunityStage.NEGOTIATION):
            items.append(ActionItem("Review and approve final proposal terms", "management", "3 days", "medium"))

        return ActionPlan(
            items=items,
            customer_items=[i for i in items if i.owner == "customer"],
            salesperson_items=[i for i in items if i.owner == "salesperson"],
            technical_items=[i for i in items if i.owner == "technical"],
            management_items=[i for i in items if i.owner == "management"],
            generated_at=now,
        )


# Singleton
_engine: ActionItemEngine | None = None

def get_action_item_engine() -> ActionItemEngine:
    global _engine
    if _engine is None:
        _engine = ActionItemEngine()
    return _engine
