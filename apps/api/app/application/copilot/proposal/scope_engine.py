"""
Scope Engine — estimates project scope, complexity, and resource requirements.

Consumes ONLY OpportunityIntelligence. Produces ScopeAssessment with team size,
timeline, complexity ratings, and confidence.
"""

from __future__ import annotations

from datetime import datetime, UTC

from app.domain.opportunity_intelligence import OpportunityIntelligence
from app.application.copilot.proposal.models import ScopeAssessment


class ScopeEngine:
    """Estimates project scope from OpportunityIntelligence.

    Evaluates project size, complexity (technical, integration), risk,
    training/support effort, recommended team, and timeline.
    """

    def assess(self, oi: OpportunityIntelligence) -> ScopeAssessment:
        now = datetime.now(UTC).isoformat()

        employees = oi.company_employees or 50
        pain_count = len(oi.business.pain_points)
        has_integration = any(
            "integration" in (p.value or "").lower()
            for p in oi.business.pain_points
        )
        has_compliance = bool(oi.business.compliance_requirements)
        constraint_count = len(oi.business.constraints)

        # ── Project size ──
        if employees > 500 or pain_count >= 5:
            size = "large"
        elif employees > 100 or pain_count >= 3:
            size = "medium"
        else:
            size = "small"

        # ── Complexity ──
        if size == "large" and (has_integration or has_compliance):
            complexity = "high"
        elif size == "medium" and has_integration:
            complexity = "medium"
        else:
            complexity = "low" if size == "small" else "medium"

        # ── Technical complexity ──
        if has_compliance and constraint_count >= 2:
            tech = "high"
        elif has_integration or constraint_count >= 1:
            tech = "medium"
        else:
            tech = "low"

        # ── Integration complexity ──
        integration = "high" if has_integration and constraint_count >= 2 else (
            "medium" if has_integration else "low"
        )

        # ── Risk ──
        risk = "high" if complexity == "high" else ("medium" if complexity == "medium" else "low")

        # ── Training ──
        training = "high" if employees > 300 else ("medium" if employees > 100 else "low")

        # ── Support ──
        support = "high" if employees > 500 else ("medium" if employees > 100 else "low")

        # ── Team size ──
        if size == "large":
            team = 6
        elif size == "medium":
            team = 4
        else:
            team = 2

        # ── Timeline ──
        if size == "large":
            weeks = 20
        elif size == "medium":
            weeks = 14
        else:
            weeks = 8

        # ── Confidence ──
        confidence = min(90, 50 + pain_count * 5)

        return ScopeAssessment(
            project_size=size,
            complexity=complexity,
            technical_complexity=tech,
            integration_complexity=integration,
            implementation_risk=risk,
            training_effort=training,
            support_effort=support,
            recommended_team_size=team,
            estimated_timeline_weeks=weeks,
            confidence=confidence,
            generated_at=now,
        )


# Singleton
_engine: ScopeEngine | None = None


def get_scope_engine() -> ScopeEngine:
    global _engine
    if _engine is None:
        _engine = ScopeEngine()
    return _engine
