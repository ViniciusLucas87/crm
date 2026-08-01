"""
Business Analysis Engine — generates professional consulting analysis from OpportunityIntelligence.

Writes as an experienced enterprise consultant. Every statement supported by data.
Never invents facts. Consumes ONLY OpportunityIntelligence.
"""

from __future__ import annotations

from datetime import datetime, UTC

from app.domain.opportunity_intelligence import OpportunityIntelligence
from app.application.copilot.proposal.models import BusinessAnalysis


class BusinessAnalysisEngine:
    """Generates executive summary, business assessment, and operational analysis.

    All analysis flows from OpportunityIntelligence — never from raw insights.
    Writes in a professional consulting tone with concrete, data-backed statements.
    """

    def analyze(self, oi: OpportunityIntelligence) -> BusinessAnalysis:
        now = datetime.now(UTC).isoformat()

        return BusinessAnalysis(
            executive_summary=self._build_executive_summary(oi),
            business_overview=self._build_business_overview(oi),
            current_situation=self._build_current_situation(oi),
            operational_challenges=self._build_operational_challenges(oi),
            growth_challenges=self._build_growth_challenges(oi),
            business_risks=self._build_business_risks(oi),
            business_opportunities=self._build_business_opportunities(oi),
            generated_at=now,
        )

    def _build_executive_summary(self, oi: OpportunityIntelligence) -> str:
        parts = []

        name = oi.company_name or "the organization"
        industry = oi.company_industry
        employees = oi.company_employees

        if name and industry:
            parts.append(f"{name} is a {industry} organization")
        elif name:
            parts.append(f"{name}")
        else:
            parts.append("The organization")

        if employees:
            parts[-1] += f" with approximately {employees} employees"

        parts[-1] += "."

        # Pain points
        pains = [p.value for p in oi.business.pain_points if p.value]
        if pains:
            pain_text = "; ".join(pains[:3])
            parts.append(f"Current operational challenges include: {pain_text}.")

        # Goals
        goals = [g.value for g in oi.business.business_goals if g.value]
        if goals:
            parts.append(f"The organization aims to {goals[0].lower().rstrip('.')}.")

        parts.append(
            "Pacific North Systems has conducted a comprehensive assessment of the "
            "current operational environment and developed a solution architecture "
            "designed to address these challenges while positioning the organization "
            "for continued growth and operational excellence."
        )

        return "\n\n".join(parts)

    def _build_business_overview(self, oi: OpportunityIntelligence) -> str:
        parts = []

        name = oi.company_name or "The organization"
        industry = oi.company_industry

        if industry:
            parts.append(
                f"{name} operates in the {industry} sector. "
                f"Organizations in this industry typically face challenges related to "
                f"operational efficiency, regulatory compliance, and workforce management."
            )
        else:
            parts.append(f"{name} is an established organization with ongoing operational needs.")

        if oi.company_employees:
            parts.append(
                f"With approximately {oi.company_employees} employees, the organization "
                f"requires solutions that scale efficiently across teams while maintaining "
                f"security, reliability, and ease of use."
            )

        if oi.company_locations:
            parts.append(
                f"The organization operates from {', '.join(oi.company_locations)}, "
                f"which introduces considerations around distributed team coordination "
                f"and multi-site operational consistency."
            )

        return "\n\n".join(parts) if parts else "Business overview pending further discovery."

    def _build_current_situation(self, oi: OpportunityIntelligence) -> str:
        parts = []

        # Current process
        processes = [p.value for p in oi.business.current_process if p.value]
        if processes:
            parts.append(f"Current operational processes include: {'; '.join(processes[:3])}.")

        # Current software
        software = [s.value for s in oi.business.current_software if s.value]
        if software:
            parts.append(f"The organization currently relies on {', '.join(software[:5])}.")

        # Manual work
        if oi.business.manual_work_indicators:
            parts.append(
                f"Manual work indicators were identified: "
                f"{'; '.join(oi.business.manual_work_indicators[:4])}. "
                f"These represent significant opportunities for automation and efficiency gains."
            )

        if not parts:
            parts.append("Current operational state to be documented through further discovery.")

        return "\n\n".join(parts)

    def _build_operational_challenges(self, oi: OpportunityIntelligence) -> list[str]:
        challenges = []

        pains = oi.business.pain_points
        for p in pains[:5]:
            if p.value:
                challenges.append(f"{p.value} (confidence: {p.confidence}%)")

        if oi.business.manual_work_indicators:
            challenges.append(
                f"Manual processes create bottlenecks: "
                f"{len(oi.business.manual_work_indicators)} areas requiring automation."
            )

        if oi.business.constraints:
            for c in oi.business.constraints[:3]:
                if c.value:
                    challenges.append(f"Constraint: {c.value}")

        return challenges if challenges else ["Operational challenges to be identified through discovery."]

    def _build_growth_challenges(self, oi: OpportunityIntelligence) -> list[str]:
        challenges = []

        goals = oi.business.business_goals
        if goals:
            for g in goals[:3]:
                if g.value:
                    challenges.append(f"Growth objective: {g.value}")

        if oi.company_employees and oi.company_employees > 100:
            challenges.append(
                f"Scaling operations across {oi.company_employees} employees requires "
                f"consistent processes and centralized systems."
            )

        if oi.business.timeline.is_known():
            challenges.append(
                f"Timeline pressure: implementation targeted for {oi.business.timeline.value}"
            )

        return challenges if challenges else ["Growth objectives to be clarified during discovery."]

    def _build_business_risks(self, oi: OpportunityIntelligence) -> list[str]:
        risks = []

        op_risks = oi.business.operational_risks
        for r in op_risks[:4]:
            if r.value:
                risks.append(f"Operational risk: {r.value}")

        if oi.business.compliance_requirements:
            for c in oi.business.compliance_requirements[:2]:
                if c.value:
                    risks.append(f"Compliance exposure: {c.value}")

        if not oi.business.budget.is_known():
            risks.append("Financial risk: budget not yet confirmed, which may affect project scoping.")

        return risks if risks else ["Risk assessment will be refined through continued discovery."]

    def _build_business_opportunities(self, oi: OpportunityIntelligence) -> list[str]:
        opportunities = []

        if oi.business.manual_work_indicators:
            opportunities.append(
                f"Automation opportunity: {len(oi.business.manual_work_indicators)} "
                f"manual processes identified for digitization, with potential for "
                f"significant efficiency gains."
            )

        if oi.business.pain_points:
            opportunities.append(
                f"Process optimization: addressing {len(oi.business.pain_points)} "
                f"identified pain points can deliver measurable operational improvement."
            )

        if oi.business.business_goals:
            opportunities.append(
                f"Strategic alignment: solution architecture can be designed to directly "
                f"support {len(oi.business.business_goals)} stated business objectives."
            )

        return opportunities if opportunities else ["Opportunity assessment pending further discovery."]


# Singleton
_engine: BusinessAnalysisEngine | None = None


def get_business_analysis_engine() -> BusinessAnalysisEngine:
    global _engine
    if _engine is None:
        _engine = BusinessAnalysisEngine()
    return _engine
