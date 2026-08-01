"""
Email Copilot — master orchestrator for professional email generation.

Consumes ONLY OpportunityIntelligence. Orchestrates context building,
strategy determination, generation, and review.

Architecture:
    OpportunityIntelligence → EmailCopilot → Professional Email
"""

from __future__ import annotations

from app.domain.opportunity_intelligence import OpportunityIntelligence
from app.application.copilot.email.models import (
    EmailContext, EmailStrategy, EmailDraft, EmailReview,
)
from app.application.copilot.email.context_builder import (
    EmailContextBuilder, get_email_context_builder,
)
from app.application.copilot.email.strategy_engine import (
    EmailStrategyEngine, get_email_strategy_engine,
)
from app.application.copilot.email.generator import (
    EmailGenerator, get_email_generator,
)
from app.application.copilot.email.review_engine import (
    EmailReviewEngine, get_email_review_engine,
)
from app.application.copilot.email.templates import list_templates


class EmailCopilot:
    """Professional email generation for enterprise software sales.

    Generates the RIGHT email based on the current opportunity state.
    All intelligence flows from OpportunityIntelligence.
    """

    def __init__(self):
        self._context_builder = get_email_context_builder()
        self._strategy = get_email_strategy_engine()
        self._generator = get_email_generator()
        self._review = get_email_review_engine()

    def generate(
        self, oi: OpportunityIntelligence, template_id: str | None = None,
    ) -> dict:
        """Generate a complete email from OpportunityIntelligence.

        Args:
            oi: OpportunityIntelligence — the single source of truth
            template_id: Optional specific template to use
        """
        context = self._context_builder.build(oi)
        strategy = self._strategy.determine(oi)

        if template_id:
            draft = self._generator.generate_from_template(context, strategy, template_id)
        else:
            draft = self._generator.generate(context, strategy)

        review = self._review.review(draft)

        return {
            "context": {
                "company_name": context.company_name,
                "contact_name": context.contact_name,
                "contact_title": context.contact_title,
                "opportunity_stage": context.opportunity_stage,
                "deal_health": context.deal_health,
            },
            "strategy": {
                "purpose": strategy.purpose,
                "email_type": strategy.email_type,
                "tone": strategy.tone,
                "focus_points": strategy.focus_points,
                "avoid_topics": strategy.avoid_topics,
            },
            "draft": {
                "subject": draft.subject,
                "preview": draft.preview,
                "greeting": draft.greeting,
                "opening": draft.opening,
                "body": draft.body,
                "call_to_action": draft.call_to_action,
                "signature": draft.signature,
                "generated_at": draft.generated_at,
            },
            "review": {
                "overall_score": review.overall_score,
                "professionalism": review.professionalism,
                "clarity": review.clarity,
                "tone_score": review.tone_score,
                "business_accuracy": review.business_accuracy,
                "call_to_action_score": review.call_to_action_score,
                "length_score": review.length_score,
                "suggestions": review.suggestions,
                "warnings": review.warnings,
                "ready_to_send": review.ready_to_send,
            },
        }

    def get_templates(self) -> list[dict]:
        return list_templates()

    def review_draft(self, draft_dict: dict) -> dict:
        """Review a manually provided email draft."""
        draft = EmailDraft(
            subject=draft_dict.get("subject", ""),
            body=draft_dict.get("body", ""),
            greeting=draft_dict.get("greeting", ""),
            call_to_action=draft_dict.get("call_to_action", ""),
            signature=draft_dict.get("signature", ""),
        )
        review = self._review.review(draft)
        return {
            "overall_score": review.overall_score,
            "professionalism": review.professionalism,
            "clarity": review.clarity,
            "tone_score": review.tone_score,
            "business_accuracy": review.business_accuracy,
            "call_to_action_score": review.call_to_action_score,
            "length_score": review.length_score,
            "suggestions": review.suggestions,
            "warnings": review.warnings,
            "ready_to_send": review.ready_to_send,
        }


# Singleton
_copilot: EmailCopilot | None = None


def get_email_copilot() -> EmailCopilot:
    global _copilot
    if _copilot is None:
        _copilot = EmailCopilot()
    return _copilot
