"""
Risk Assessment Engine — identifies and scores business, technical, operational,
adoption, and integration risks from OpportunityIntelligence.

Every risk includes severity, likelihood, and mitigation strategy.
"""

from __future__ import annotations

from datetime import datetime, UTC

from app.domain.opportunity_intelligence import OpportunityIntelligence
from app.application.copilot.proposal.models import RiskAssessment, AssessedRisk


class RiskAssessmentEngine:
    """Identifies and scores project risks from OpportunityIntelligence.

    Evaluates five risk categories: business, technical, operational,
    adoption, and integration. Each risk includes severity, likelihood,
    and a concrete mitigation strategy.
    """

    def assess(self, oi: OpportunityIntelligence) -> RiskAssessment:
        now = datetime.now(UTC).isoformat()
        risks: list[AssessedRisk] = []

        has_budget = oi.business.budget.is_known()
        has_timeline = oi.business.timeline.is_known()
        has_dm = any(s.role.value == "decision_maker" for s in oi.stakeholders)
        pain_count = len(oi.business.pain_points)
        has_compliance = bool(oi.business.compliance_requirements)
        constraint_count = len(oi.business.constraints)
        objection_count = len(oi.sales.objections)

        # ── Business Risks ──
        if not has_budget:
            risks.append(AssessedRisk(
                category="business",
                risk="Unconfirmed budget may affect project scope and timeline",
                severity="high",
                likelihood="medium",
                mitigation="Confirm budget allocation before proceeding to solution design. Present phased investment options.",
            ))

        if not has_timeline:
            risks.append(AssessedRisk(
                category="business",
                risk="Undefined implementation timeline creates resource planning uncertainty",
                severity="medium",
                likelihood="high",
                mitigation="Establish target go-live date and work backward to define milestones.",
            ))

        if not has_dm:
            risks.append(AssessedRisk(
                category="business",
                risk="Decision maker not clearly identified",
                severity="high",
                likelihood="medium",
                mitigation="Identify economic buyer and ensure inclusion in solution design discussions.",
            ))

        # ── Technical Risks ──
        if constraint_count >= 1:
            risks.append(AssessedRisk(
                category="technical",
                risk=f"Technical constraints ({constraint_count} identified) may limit solution options",
                severity="medium",
                likelihood="medium",
                mitigation="Conduct technical discovery workshop to validate constraints and identify compatible solutions.",
            ))

        if has_compliance:
            risks.append(AssessedRisk(
                category="technical",
                risk="Compliance requirements add complexity to solution design and testing",
                severity="medium",
                likelihood="high",
                mitigation="Engage compliance specialist early in design phase. Include compliance testing in QA plan.",
            ))

        # ── Operational Risks ──
        if pain_count <= 1:
            risks.append(AssessedRisk(
                category="operational",
                risk="Limited operational discovery may result in incomplete solution requirements",
                severity="medium",
                likelihood="medium",
                mitigation="Conduct additional discovery sessions with operational stakeholders.",
            ))

        risks.append(AssessedRisk(
            category="operational",
            risk="Process changes may temporarily reduce productivity during transition",
            severity="low",
            likelihood="high",
            mitigation="Implement phased rollout with parallel run period. Provide adequate training and support.",
        ))

        # ── Adoption Risks ──
        if oi.company_employees and oi.company_employees > 100:
            risks.append(AssessedRisk(
                category="adoption",
                risk=f"Large user base ({oi.company_employees} employees) requires structured change management",
                severity="medium",
                likelihood="high",
                mitigation="Develop comprehensive training program. Identify champions within each department. Phase rollout by team.",
            ))

        risks.append(AssessedRisk(
            category="adoption",
            risk="Staff resistance to new technology may slow adoption",
            severity="medium",
            likelihood="medium",
            mitigation="Involve end users in design and testing. Demonstrate efficiency gains early. Provide ongoing support.",
        ))

        # ── Integration Risks ──
        current_sw = [s.value for s in oi.business.current_software if s.value]
        if len(current_sw) >= 2:
            risks.append(AssessedRisk(
                category="integration",
                risk=f"Integration with {len(current_sw)} existing systems requires careful planning",
                severity="medium",
                likelihood="high",
                mitigation="Perform integration audit during discovery. Design API-first integration layer. Test integrations early.",
            ))

        # ── Overall ──
        critical = sum(1 for r in risks if r.severity == "critical")
        high = sum(1 for r in risks if r.severity == "high")
        if critical >= 1 or high >= 3:
            overall = "high"
        elif high >= 1 or len(risks) >= 5:
            overall = "medium"
        else:
            overall = "low"

        return RiskAssessment(risks=risks, overall_risk_level=overall, generated_at=now)


# Singleton
_engine: RiskAssessmentEngine | None = None


def get_risk_assessment_engine() -> RiskAssessmentEngine:
    global _engine
    if _engine is None:
        _engine = RiskAssessmentEngine()
    return _engine
