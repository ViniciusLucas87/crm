"""
Email Review Engine — evaluates generated emails for quality.

Scores 8 dimensions: professionalism, clarity, tone, grammar, business
accuracy, opportunity consistency, call to action, and length.
"""

from __future__ import annotations

from datetime import datetime, UTC

from app.application.copilot.email.models import EmailDraft, EmailReview


class EmailReviewEngine:
    """Reviews generated emails for quality and readiness.

    Evaluates professionalism, clarity, tone, business accuracy,
    consistency with the opportunity, and call-to-action strength.
    """

    def review(self, draft: EmailDraft) -> EmailReview:
        now = datetime.now(UTC).isoformat()

        professionalism = self._score_professionalism(draft)
        clarity = self._score_clarity(draft)
        tone_score = self._score_tone(draft)
        grammar = self._score_grammar(draft)
        business_accuracy = self._score_business_accuracy(draft)
        opportunity_consistency = self._score_consistency(draft)
        cta_score = self._score_cta(draft)
        length_score = self._score_length(draft)

        scores = [
            professionalism, clarity, tone_score, grammar,
            business_accuracy, opportunity_consistency, cta_score, length_score,
        ]
        overall = int(sum(scores) / len(scores))

        suggestions: list[str] = []
        warnings: list[str] = []

        if professionalism < 70:
            suggestions.append("Consider more formal language for business communication.")
        if clarity < 70:
            suggestions.append("Some sentences could be clearer. Try shorter paragraphs.")
        if cta_score < 60:
            suggestions.append("The call to action could be more specific with a clear next step.")
        if length_score < 60:
            if len(draft.body) > 800:
                warnings.append("Email is quite long. Consider shortening for readability.")
            elif len(draft.body) < 100:
                warnings.append("Email is very short. Consider adding more context.")

        ready = overall >= 70 and len(warnings) == 0

        return EmailReview(
            professionalism=professionalism,
            clarity=clarity,
            tone_score=tone_score,
            grammar_score=grammar,
            business_accuracy=business_accuracy,
            opportunity_consistency=opportunity_consistency,
            call_to_action_score=cta_score,
            length_score=length_score,
            overall_score=overall,
            suggestions=suggestions,
            warnings=warnings,
            ready_to_send=ready,
            generated_at=now,
        )

    def _score_professionalism(self, draft: EmailDraft) -> int:
        score = 70
        unprofessional = ["hey", "yo", "dude", "cool", "awesome", "amazing"]
        for word in unprofessional:
            if word in draft.body.lower():
                score -= 10
        # Check for proper greeting
        if draft.greeting and len(draft.greeting) > 3:
            score += 10
        # Check for signature
        if draft.signature and len(draft.signature) > 20:
            score += 10
        return min(100, max(0, score))

    def _score_clarity(self, draft: EmailDraft) -> int:
        score = 70
        body = draft.body
        sentences = [s.strip() for s in body.replace("\n", ". ").split(".") if s.strip()]
        if sentences:
            avg_len = sum(len(s.split()) for s in sentences) / len(sentences)
            if 10 <= avg_len <= 30:
                score += 15
            elif avg_len > 40:
                score -= 10
        if draft.subject and len(draft.subject) < 80:
            score += 10
        return min(100, max(0, score))

    def _score_tone(self, draft: EmailDraft) -> int:
        score = 70
        if draft.strategy:
            expected = draft.strategy.tone
            body_lower = draft.body.lower()
            if expected == "formal":
                if any(w in body_lower for w in ["thanks!", "awesome", "cool"]):
                    score -= 15
            elif expected == "warm":
                if "thank you" in body_lower or "appreciate" in body_lower:
                    score += 10
        return min(100, max(0, score))

    def _score_grammar(self, draft: EmailDraft) -> int:
        score = 85
        body = draft.body
        # Basic checks
        if "  " in body:
            score -= 5
        if body != body.strip():
            score -= 5
        # Subject should not be empty
        if not draft.subject:
            score -= 30
        if not draft.greeting:
            score -= 10
        return min(100, max(0, score))

    def _score_business_accuracy(self, draft: EmailDraft) -> int:
        score = 60
        body = draft.body
        # Check for concrete details (not just generic)
        if any(c.isdigit() for c in body):
            score += 10
        if "%" in body or "percent" in body:
            score += 10
        if "$" in body or "savings" in body.lower() or "roi" in body.lower():
            score += 10
        return min(100, max(0, score))

    def _score_consistency(self, draft: EmailDraft) -> int:
        score = 75
        if draft.strategy:
            # Check that the email aligns with its stated purpose
            body_lower = draft.body.lower()
            purpose = draft.strategy.purpose
            if "discovery" in purpose and "proposal" in body_lower:
                score -= 10  # Don't jump to proposal during discovery
        return min(100, max(0, score))

    def _score_cta(self, draft: EmailDraft) -> int:
        score = 50
        cta = draft.call_to_action
        if cta and len(cta) > 10:
            score += 20
        # Check for clear next step
        body_lower = draft.body.lower()
        cta_signals = ["would you", "let me know", "schedule", "available", "thoughts"]
        matches = sum(1 for s in cta_signals if s in body_lower)
        score += matches * 8
        return min(100, max(0, score))

    def _score_length(self, draft: EmailDraft) -> int:
        body_len = len(draft.body)
        if 200 <= body_len <= 600:
            return 90
        elif 100 <= body_len <= 800:
            return 75
        elif body_len < 50:
            return 40
        else:
            return 60


# Singleton
_engine: EmailReviewEngine | None = None


def get_email_review_engine() -> EmailReviewEngine:
    global _engine
    if _engine is None:
        _engine = EmailReviewEngine()
    return _engine
