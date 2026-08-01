"""
Proposal Studio — master orchestrator for professional proposal generation.

Consumes ONLY OpportunityIntelligence. Orchestrates all proposal engines:
    BusinessAnalysis → SolutionArchitecture → ROI → Scope → Risks
    → Implementation Roadmap → Review → Export

This is the flagship demonstration feature of Project TITAN.

Architecture:
    OpportunityIntelligence → ProposalStudio → Professional Proposal → Export
"""

from __future__ import annotations

from datetime import datetime, UTC
from typing import Any

from app.domain.opportunity_intelligence import OpportunityIntelligence
from app.application.copilot.proposal.models import (
    Proposal, ProposalSection, ProposalVersion, ExportConfig, ExtensionPoints,
)
from app.application.copilot.proposal.business_analysis import (
    BusinessAnalysisEngine, get_business_analysis_engine,
)
from app.application.copilot.proposal.solution_architecture import (
    SolutionArchitectureEngine, get_solution_architecture_engine,
)
from app.application.copilot.proposal.roi_engine import (
    ROIEngine, get_roi_engine,
)
from app.application.copilot.proposal.scope_engine import (
    ScopeEngine, get_scope_engine,
)
from app.application.copilot.proposal.risk_assessment import (
    RiskAssessmentEngine, get_risk_assessment_engine,
)
from app.application.copilot.proposal.implementation_roadmap import (
    ImplementationRoadmapEngine, get_implementation_roadmap_engine,
)
from app.application.copilot.proposal.proposal_review import (
    ProposalReviewEngine, get_proposal_review_engine,
)
from app.application.copilot.proposal.export_engine import (
    ExportEngine, get_export_engine,
)
from app.application.copilot.proposal.component_library import ComponentLibrary
from app.application.copilot.proposal.versioning import (
    ProposalVersionManager, get_version_manager,
)
from app.application.copilot.proposal.extension_points import get_extension_points


class ProposalStudio:
    """Master orchestrator for professional consulting proposals.

    Generates complete proposals from OpportunityIntelligence in under
    5 minutes (target). Every section is editable, lockable, and versioned.
    """

    def __init__(self):
        self._business_analysis = get_business_analysis_engine()
        self._solution_architecture = get_solution_architecture_engine()
        self._roi = get_roi_engine()
        self._scope = get_scope_engine()
        self._risk = get_risk_assessment_engine()
        self._roadmap = get_implementation_roadmap_engine()
        self._review = get_proposal_review_engine()
        self._export = get_export_engine()
        self._version_manager = get_version_manager()
        self._components = ComponentLibrary()

    def generate(self, oi: OpportunityIntelligence, opportunity_id: int | None = None) -> Proposal:
        """Generate a complete, consulting-quality proposal from OpportunityIntelligence.

        This is the main entry point. Runs all engines, assembles sections,
        reviews quality, and returns a ready-to-edit proposal.

        Args:
            oi: OpportunityIntelligence — the single source of truth
            opportunity_id: Optional CRM opportunity ID
        """
        now = datetime.now(UTC).isoformat()
        comp = self._components

        company_name = oi.company_name or "the organization"

        # ═══ Run all engines ═══
        business = self._business_analysis.analyze(oi)
        architecture = self._solution_architecture.design(oi)
        roi = self._roi.calculate(oi)
        scope = self._scope.assess(oi)
        risks = self._risk.assess(oi)
        roadmap = self._roadmap.generate(oi)

        # ═══ Assemble sections ═══
        sections: list[ProposalSection] = []

        # 1. Executive Summary
        sections.append(comp.executive_summary(business.executive_summary, now))

        # 2. Business Assessment
        ba_content = business.business_overview
        if business.current_situation:
            ba_content += f"\n\n## Current Situation\n\n{business.current_situation}"
        sections.append(comp.business_assessment(ba_content, now))

        # 3. Current State
        cs_lines = []
        if business.operational_challenges:
            cs_lines.append("### Operational Challenges")
            for c in business.operational_challenges:
                cs_lines.append(f"• {c}")
        if business.growth_challenges:
            cs_lines.append("\n### Growth Challenges")
            for c in business.growth_challenges:
                cs_lines.append(f"• {c}")
        sections.append(comp.current_state("\n".join(cs_lines), now))

        # 4. Current Workflow
        cw_steps = [f"{s.label}: {s.description}" for s in architecture.current_workflow]
        sections.append(comp.current_workflow(cw_steps, now))

        # 5. Future Architecture
        arch_components = [
            {
                "name": c.name,
                "purpose": c.purpose,
                "business_value": c.business_value,
                "reason_selected": c.reason_selected,
            }
            for c in architecture.components
        ]
        sections.append(comp.future_architecture(arch_components, now))

        # 6. Business Benefits
        benefits = business.business_opportunities
        sections.append(comp.business_benefits(benefits, now))

        # 7. ROI
        roi_assumptions = [
            {"label": a.label, "value": a.value, "unit": a.unit, "description": a.description}
            for a in roi.assumptions
        ]
        sections.append(comp.roi_block(
            roi.hours_saved_per_week, roi.estimated_annual_savings,
            roi.estimated_payback_months, roi_assumptions, now,
        ))

        # 8. Implementation Roadmap
        phases = [
            {
                "phase": p.phase, "name": p.name,
                "estimated_duration": p.estimated_duration,
                "description": p.description,
                "deliverables": p.deliverables,
            }
            for p in roadmap.phases
        ]
        sections.append(comp.implementation_roadmap(phases, roadmap.total_duration, now))

        # 9. Deliverables
        all_deliverables: list[str] = []
        for p in roadmap.phases:
            all_deliverables.extend(p.deliverables)
        sections.append(comp.deliverables(all_deliverables, now))

        # 10. Timeline
        timeline_content = f"Total estimated implementation duration: **{roadmap.total_duration}**"
        sections.append(comp.timeline(timeline_content, now))

        # 11. Investment
        investment_items = [
            {"item": "Discovery & Planning", "estimate": "$8,000 – $12,000"},
            {"item": "Design & Development", "estimate": "$45,000 – $75,000"},
            {"item": "Testing & Deployment", "estimate": "$10,000 – $15,000"},
            {"item": "Training & Documentation", "estimate": "$5,000 – $8,000"},
            {"item": "First-Year Support", "estimate": "$12,000"},
            {"item": "Total Estimated Investment", "estimate": "$80,000 – $122,000"},
        ]
        sections.append(comp.investment(investment_items, now))

        # 12. Risk Assessment
        risk_items = [
            {
                "risk": r.risk, "severity": r.severity,
                "likelihood": r.likelihood, "mitigation": r.mitigation,
            }
            for r in risks.risks
        ]
        sections.append(comp.risks(risk_items, risks.overall_risk_level, now))

        # 13. Assumptions
        sections.append(comp.assumptions(roi_assumptions, now))

        # 14. Next Steps
        next_steps = [
            "Review proposal with key stakeholders",
            "Schedule technical discovery workshop",
            "Finalize scope and timeline",
            "Contract review and kickoff",
        ]
        sections.append(comp.next_steps(next_steps, now))

        # ═══ Create proposal ═══
        proposal_id = f"prop-{oi.company_id or 'unknown'}-{now[:10]}"
        proposal = Proposal(
            id=proposal_id,
            title=f"Technology Solutions Proposal for {company_name}",
            company_name=company_name,
            opportunity_id=opportunity_id,
            generated_at=now,
            sections=sections,
            source_intelligence_version=oi.last_updated,
        )

        # ═══ Review ═══
        review = self._review.review(
            proposal, business, architecture, roi, scope, risks, roadmap,
        )
        proposal.quality_score = review.overall_score
        proposal.ready_to_send = review.ready_to_send
        proposal.missing_information = review.missing_information

        # ═══ Version ═══
        self._version_manager.create_version(proposal, reason="Initial generation")

        return proposal

    def regenerate_section(
        self, proposal: Proposal, section_id: str, oi: OpportunityIntelligence,
    ) -> ProposalSection | None:
        """Regenerate a single section without reprocessing the entire proposal."""
        now = datetime.now(UTC).isoformat()
        engine_map = {
            "executive_summary": lambda: self._components.executive_summary(
                self._business_analysis.analyze(oi).executive_summary, now,
            ),
        }

        regenerator = engine_map.get(section_id)
        if not regenerator:
            return None

        new_section = regenerator()
        for i, s in enumerate(proposal.sections):
            if s.id == section_id:
                proposal.sections[i] = new_section
                return new_section
        return None

    def export(
        self, proposal: Proposal, format: str = "markdown", config: ExportConfig | None = None,
    ) -> Any:
        """Export proposal to the specified format."""
        config = config or ExportConfig(format=format)

        if format == "markdown":
            return self._export.export_markdown(proposal, config)
        elif format == "html":
            return self._export.export_html(proposal, config)
        else:
            return self._export.export(proposal, config)

    def get_extension_points(self) -> ExtensionPoints:
        """Return available extension points for future features."""
        return get_extension_points()


# Singleton
_studio: ProposalStudio | None = None


def get_proposal_studio() -> ProposalStudio:
    global _studio
    if _studio is None:
        _studio = ProposalStudio()
    return _studio
