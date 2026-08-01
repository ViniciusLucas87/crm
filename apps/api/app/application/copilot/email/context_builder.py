"""
Email Context Builder — aggregates opportunity data for email generation.

Consumes ONLY OpportunityIntelligence. Collects company, contact, stage,
signals, objections, activities, and previous communications.
"""

from __future__ import annotations

from datetime import datetime, UTC

from app.domain.opportunity_intelligence import OpportunityIntelligence
from app.application.copilot.email.models import EmailContext


class EmailContextBuilder:
    """Builds EmailContext from OpportunityIntelligence.

    Collects all relevant data for email generation: company,
    contact, stage, signals, pain points, activities, and timeline.
    """

    def build(self, oi: OpportunityIntelligence) -> EmailContext:
        now = datetime.now(UTC).isoformat()

        # Primary contact
        primary = next((s for s in oi.stakeholders if s.is_primary), None) or (
            oi.stakeholders[0] if oi.stakeholders else None
        )

        contact_name = primary.name if primary else ""
        contact_title = primary.title if primary else ""
        contact_email = primary.email if primary else ""

        # Decision makers
        dms = [s.name for s in oi.stakeholders if s.role.value == "decision_maker"]

        # Pain points
        pains = [p.value or "" for p in oi.business.pain_points if p.value]

        # Goals
        goals = [g.value or "" for g in oi.business.business_goals if g.value]

        # Buying signals
        signals = [b.value or "" for b in oi.sales.buying_signals if b.value]

        # Objections
        objections = [o.value or "" for o in oi.sales.objections if o.value]

        # Recommended products
        products = [p.get("product", "") if isinstance(p, dict) else str(p)
                     for p in oi.solutions.recommended_products]

        # Budget
        budget_str = f"${oi.business.budget.value:,}" if oi.business.budget.is_known() else ""

        # Timeline
        timeline_str = oi.business.timeline.value if oi.business.timeline.is_known() else ""

        # Activities from timeline
        prev_activities = [
            e.description for e in oi.timeline
            if e.event_type.value in ("call", "email", "meeting", "activity")
        ][:5]

        return EmailContext(
            company_name=oi.company_name,
            contact_name=contact_name,
            contact_title=contact_title,
            contact_email=contact_email,
            opportunity_stage=oi.stage.value if hasattr(oi.stage, "value") else str(oi.stage),
            deal_health=str(oi.deal_health.value) if oi.deal_health.is_known() else "unknown",
            proposal_status=oi.solutions.proposal_status,
            last_activity=prev_activities[0] if prev_activities else "",
            last_meeting_date="",
            next_action=oi.sales.next_best_action,
            buying_signals=signals,
            objections=objections,
            pain_points=pains,
            business_goals=goals,
            recommended_products=products,
            timeline=timeline_str,
            budget=budget_str,
            decision_makers=dms,
            previous_activities=prev_activities,
            previous_emails=[],
            generated_at=now,
        )


# Singleton
_builder: EmailContextBuilder | None = None


def get_email_context_builder() -> EmailContextBuilder:
    global _builder
    if _builder is None:
        _builder = EmailContextBuilder()
    return _builder
