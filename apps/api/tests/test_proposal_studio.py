"""
Tests for Proposal Studio — professional consulting proposal platform.

All tests deterministic. No LLM. No transcript parsing.
Mock OpportunityIntelligence only.

Coverage:
    BusinessAnalysisEngine, SolutionArchitectureEngine, ROIEngine,
    ScopeEngine, RiskAssessmentEngine, ImplementationRoadmapEngine,
    ProposalReviewEngine, Versioning, Components, Export, ProposalStudio.
"""

import json

import pytest

from app.domain.opportunity_intelligence import (
    OpportunityIntelligence, OpportunityStage, OpportunityStatus,
    TypedValue, Stakeholder, StakeholderRole, BusinessContext,
    SalesContext, SolutionContext, TimelineEvent, EventType,
    CustomerType, UrgencyLevel, create_empty_intelligence,
)
from app.application.copilot.proposal.models import (
    Proposal, ProposalSection, ProposalVersion, ROIReport, ROIAssumption,
    RiskAssessment, AssessedRisk, ScopeAssessment, ImplementationRoadmap,
    ImplementationPhase, SolutionArchitecture, WorkflowStep,
    ArchitectureComponent, BusinessAnalysis, ProposalReview,
    ReviewCategory, ExportConfig,
)
from app.application.copilot.proposal.business_analysis import (
    BusinessAnalysisEngine, get_business_analysis_engine,
)
from app.application.copilot.proposal.solution_architecture import (
    SolutionArchitectureEngine,
)
from app.application.copilot.proposal.roi_engine import (
    ROIEngine, get_roi_engine,
)
from app.application.copilot.proposal.scope_engine import (
    ScopeEngine, get_scope_engine,
)
from app.application.copilot.proposal.risk_assessment import (
    RiskAssessmentEngine,
)
from app.application.copilot.proposal.implementation_roadmap import (
    ImplementationRoadmapEngine,
)
from app.application.copilot.proposal.proposal_review import (
    ProposalReviewEngine,
)
from app.application.copilot.proposal.export_engine import (
    ExportEngine, get_export_engine,
)
from app.application.copilot.proposal.component_library import ComponentLibrary
from app.application.copilot.proposal.versioning import (
    ProposalVersionManager, get_version_manager,
)
from app.application.copilot.proposal.proposal_studio import (
    ProposalStudio, get_proposal_studio,
)
from app.application.copilot.proposal.extension_points import (
    get_extension_points, get_extension_schema,
)


# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════

def sample_oi() -> OpportunityIntelligence:
    """Build a realistic OpportunityIntelligence for testing."""
    oi = create_empty_intelligence(opportunity_id=1, company_id=100, organization_id=1)
    oi.stage = OpportunityStage.DISCOVERY
    oi.company_name = "Acme Construction Ltd."
    oi.company_industry = "Construction"
    oi.company_employees = 250
    oi.company_locations = ["Vancouver, BC, Canada"]
    oi.company_website = "https://acme.example.com"

    # Stakeholders
    oi.stakeholders = [
        Stakeholder(id=1, name="Sarah Chen", title="VP Operations", role=StakeholderRole.DECISION_MAKER, is_primary=True),
        Stakeholder(id=2, name="Mike Torres", title="IT Manager", role=StakeholderRole.TECHNICAL),
    ]

    # Business
    oi.business.pain_points = [
        TypedValue(value="Manual inspections take 4 hours per site", confidence=90, source="conversation"),
        TypedValue(value="Duplicate data entry across 3 spreadsheets", confidence=85, source="conversation"),
        TypedValue(value="Lost paperwork causing compliance issues", confidence=80, source="conversation"),
    ]
    oi.business.current_process = [
        TypedValue(value="Field techs fill paper forms, office staff type them in", confidence=90, source="conversation"),
    ]
    oi.business.current_software = [
        TypedValue(value="Excel", confidence=90, source="conversation"),
        TypedValue(value="QuickBooks", confidence=85, source="conversation"),
    ]
    oi.business.business_goals = [
        TypedValue(value="Reduce inspection turnaround by 50%", confidence=85, source="conversation"),
    ]
    oi.business.manual_work_indicators = [
        "Manual inspections take 4 hours per site",
        "Duplicate data entry across 3 spreadsheets",
    ]
    oi.business.constraints = [
        TypedValue(value="Must integrate with existing accounting system", confidence=85, source="conversation"),
    ]
    oi.business.compliance_requirements = [
        TypedValue(value="Annual safety audit compliance", confidence=80, source="conversation"),
    ]
    oi.business.budget = TypedValue(value=120000, confidence=80, source="conversation")
    oi.business.timeline = TypedValue(value="90_days", confidence=70, source="conversation")

    # Sales
    oi.sales.buying_signals = [
        TypedValue(value="Looking for a solution for months", confidence=85, source="conversation"),
    ]
    oi.sales.objections = [
        TypedValue(value="Worried about training time", confidence=80, source="conversation"),
    ]
    oi.sales.urgency = TypedValue(value=UrgencyLevel.HIGH, confidence=75, source="conversation")
    oi.sales.customer_type = TypedValue(value=CustomerType.OPERATIONAL, confidence=80, source="conversation")

    return oi


# ═══════════════════════════════════════════════════════════
# BUSINESS ANALYSIS ENGINE
# ═══════════════════════════════════════════════════════════

class TestBusinessAnalysisEngine:
    def test_generates_all_fields(self):
        engine = get_business_analysis_engine()
        result = engine.analyze(sample_oi())
        assert result.executive_summary
        assert len(result.executive_summary) > 100
        assert "Acme Construction" in result.executive_summary
        assert result.business_overview
        assert result.current_situation
        assert len(result.operational_challenges) >= 1
        assert result.generated_at

    def test_empty_oi_handled_gracefully(self):
        engine = get_business_analysis_engine()
        result = engine.analyze(create_empty_intelligence())
        assert result.executive_summary
        assert result.operational_challenges

    def test_no_invented_facts(self):
        """Executive summary should not contain unsupported claims."""
        engine = get_business_analysis_engine()
        result = engine.analyze(sample_oi())
        # Should not mention technologies not in the data
        assert "blockchain" not in result.executive_summary.lower()
        assert "AI-powered" not in result.executive_summary.lower()


# ═══════════════════════════════════════════════════════════
# SOLUTION ARCHITECTURE ENGINE
# ═══════════════════════════════════════════════════════════

class TestSolutionArchitectureEngine:
    def test_generates_workflows(self):
        engine = SolutionArchitectureEngine()
        result = engine.design(sample_oi())
        assert len(result.current_workflow) >= 2
        assert len(result.future_workflow) >= 2
        assert len(result.components) >= 1

    def test_components_have_rationale(self):
        engine = SolutionArchitectureEngine()
        result = engine.design(sample_oi())
        for c in result.components:
            assert c.name
            assert c.purpose
            assert c.business_value
            assert c.reason_selected

    def test_empty_oi(self):
        engine = SolutionArchitectureEngine()
        result = engine.design(create_empty_intelligence())
        assert len(result.current_workflow) >= 2


# ═══════════════════════════════════════════════════════════
# ROI ENGINE
# ═══════════════════════════════════════════════════════════

class TestROIEngine:
    def test_calculates_savings(self):
        engine = get_roi_engine()
        result = engine.calculate(sample_oi())
        assert result.hours_saved_per_week > 0
        assert result.estimated_annual_savings > 0
        assert result.estimated_payback_months > 0

    def test_assumptions_are_editable(self):
        engine = get_roi_engine()
        result = engine.calculate(sample_oi())
        assert len(result.assumptions) >= 3
        for a in result.assumptions:
            assert a.editable is True
            assert a.label
            assert a.value >= 0

    def test_empty_oi(self):
        engine = get_roi_engine()
        result = engine.calculate(create_empty_intelligence())
        assert result.estimated_annual_savings >= 0


# ═══════════════════════════════════════════════════════════
# SCOPE ENGINE
# ═══════════════════════════════════════════════════════════

class TestScopeEngine:
    def test_assesses_complexity(self):
        engine = get_scope_engine()
        result = engine.assess(sample_oi())
        assert result.project_size in ("small", "medium", "large", "enterprise")
        assert result.recommended_team_size >= 1
        assert result.estimated_timeline_weeks >= 4

    def test_small_company(self):
        engine = get_scope_engine()
        oi = create_empty_intelligence()
        oi.company_employees = 10
        result = engine.assess(oi)
        assert result.project_size == "small"

    def test_large_company(self):
        engine = get_scope_engine()
        oi = create_empty_intelligence()
        oi.company_employees = 600
        oi.business.pain_points = [
            TypedValue(value="p1", confidence=80), TypedValue(value="p2", confidence=80),
            TypedValue(value="p3", confidence=80), TypedValue(value="p4", confidence=80),
            TypedValue(value="p5", confidence=80),
        ]
        result = engine.assess(oi)
        assert result.project_size == "large"


# ═══════════════════════════════════════════════════════════
# RISK ASSESSMENT ENGINE
# ═══════════════════════════════════════════════════════════

class TestRiskAssessmentEngine:
    def test_identifies_risks(self):
        engine = RiskAssessmentEngine()
        result = engine.assess(sample_oi())
        assert len(result.risks) >= 3
        assert result.overall_risk_level in ("low", "medium", "high")

    def test_each_risk_has_mitigation(self):
        engine = RiskAssessmentEngine()
        result = engine.assess(sample_oi())
        for r in result.risks:
            assert r.risk
            assert r.severity in ("critical", "high", "medium", "low")
            assert r.likelihood in ("high", "medium", "low")
            assert r.mitigation
            assert len(r.mitigation) > 10

    def test_no_budget_creates_risk(self):
        engine = RiskAssessmentEngine()
        oi = sample_oi()
        oi.business.budget = TypedValue.empty()
        result = engine.assess(oi)
        assert any("budget" in r.risk.lower() for r in result.risks)

    def test_covers_all_categories(self):
        engine = RiskAssessmentEngine()
        result = engine.assess(sample_oi())
        categories = {r.category for r in result.risks}
        # At least operational + adoption should always be present
        assert "operational" in categories
        assert "adoption" in categories
        assert len(categories) >= 2, f"Expected multiple categories, got: {categories}"


# ═══════════════════════════════════════════════════════════
# IMPLEMENTATION ROADMAP
# ═══════════════════════════════════════════════════════════

class TestImplementationRoadmap:
    def test_generates_phases(self):
        engine = ImplementationRoadmapEngine()
        result = engine.generate(sample_oi())
        assert len(result.phases) >= 6
        assert result.total_duration

    def test_phases_have_deliverables(self):
        engine = ImplementationRoadmapEngine()
        result = engine.generate(sample_oi())
        for p in result.phases:
            assert p.name
            assert p.estimated_duration
            assert len(p.deliverables) >= 1

    def test_phases_have_dependencies(self):
        engine = ImplementationRoadmapEngine()
        result = engine.generate(sample_oi())
        # First phase should have no dependencies
        assert result.phases[0].dependencies == []
        # Second phase should depend on first
        assert len(result.phases[1].dependencies) >= 1


# ═══════════════════════════════════════════════════════════
# PROPOSAL REVIEW ENGINE
# ═══════════════════════════════════════════════════════════

class TestProposalReviewEngine:
    def test_reviews_all_categories(self):
        engine = ProposalReviewEngine()
        result = engine.review(Proposal(id="test"))
        assert len(result.categories) == 8
        assert 0 <= result.overall_score <= 100

    def test_empty_proposal_scores_low(self):
        engine = ProposalReviewEngine()
        result = engine.review(Proposal(id="test"))
        assert result.overall_score <= 50
        assert not result.ready_to_send

    def test_has_strengths_and_weaknesses(self):
        engine = ProposalReviewEngine()
        result = engine.review(Proposal(id="test"))
        assert isinstance(result.strengths, list)
        assert isinstance(result.weaknesses, list)
        assert isinstance(result.recommendations, list)


# ═══════════════════════════════════════════════════════════
# VERSIONING
# ═══════════════════════════════════════════════════════════

class TestVersioning:
    def test_creates_version(self):
        vm = get_version_manager()
        proposal = Proposal(id="test")
        proposal.sections = [
            ProposalSection(id="s1", title="Section 1", content="Hello"),
        ]
        v1 = vm.create_version(proposal)
        assert v1.version == 1
        assert proposal.current_version == 1
        assert len(proposal.versions) == 1

    def test_compare_versions(self):
        vm = get_version_manager()
        proposal = Proposal(id="test")
        proposal.sections = [ProposalSection(id="s1", title="S1", content="v1")]
        vm.create_version(proposal)

        proposal.sections = [ProposalSection(id="s1", title="S1", content="v2")]
        vm.create_version(proposal)

        diff = vm.compare(proposal.versions[0], proposal.versions[1])
        assert "s1" in diff
        assert diff["s1"]["type"] == "modified"

    def test_rollback(self):
        vm = get_version_manager()
        proposal = Proposal(id="test")
        proposal.sections = [ProposalSection(id="s1", title="S1", content="original")]
        vm.create_version(proposal)

        proposal.sections = [ProposalSection(id="s1", title="S1", content="modified")]
        vm.create_version(proposal)

        vm.rollback(proposal, 1)
        assert proposal.sections[0].content == "original"
        assert proposal.current_version == 1


# ═══════════════════════════════════════════════════════════
# COMPONENT LIBRARY
# ═══════════════════════════════════════════════════════════

class TestComponentLibrary:
    def test_all_components_created(self):
        comp = ComponentLibrary()
        now = "2026-07-23"

        es = comp.executive_summary("summary", now)
        assert es.id == "executive_summary"
        assert es.content == "summary"

        roi = comp.roi_block(10, 50000, 6, [], now)
        assert roi.id == "roi"
        assert "50,000" in roi.content

        roadmap = comp.implementation_roadmap([
            {"phase": 1, "name": "Test", "estimated_duration": "2 weeks", "description": "desc", "deliverables": ["d1"]},
        ], "2 weeks", now)
        assert roadmap.id == "implementation_roadmap"

        risks = comp.risks([
            {"risk": "Test risk", "severity": "high", "likelihood": "medium", "mitigation": "Fix it"},
        ], "medium", now)
        assert "Test risk" in risks.content

        steps = comp.next_steps(["Step 1", "Step 2"], now)
        assert "Step 1" in steps.content

    def test_section_has_status(self):
        comp = ComponentLibrary()
        section = comp.executive_summary("content")
        assert section.status == "generated"


# ═══════════════════════════════════════════════════════════
# EXPORT ENGINE
# ═══════════════════════════════════════════════════════════

class TestExportEngine:
    def test_markdown_export(self):
        engine = get_export_engine()
        proposal = Proposal(
            id="test", title="Test Proposal", company_name="Acme",
            generated_at="2026-07-23T00:00:00Z",
            sections=[
                ProposalSection(id="s1", title="Executive Summary", content="Test summary."),
                ProposalSection(id="s2", title="ROI", content="ROI content."),
            ],
        )
        md = engine.export_markdown(proposal)
        assert "# Test Proposal" in md
        assert "Acme" in md
        assert "Executive Summary" in md
        assert "ROI" in md

    def test_html_export(self):
        engine = get_export_engine()
        proposal = Proposal(
            id="test", title="Test", company_name="Acme",
            sections=[ProposalSection(id="s1", title="Section", content="Content.")],
        )
        html = engine.export_html(proposal)
        assert "<html>" in html
        assert "Test" in html

    def test_export_config(self):
        engine = get_export_engine()
        config = ExportConfig(
            format="pdf", include_toc=True, include_page_numbers=True,
            company_name="PNS", primary_color="#000000",
        )
        result = engine.export(Proposal(id="test"), config)
        assert result["format"] == "pdf"
        assert result["config"]["company_name"] == "PNS"


# ═══════════════════════════════════════════════════════════
# PROPOSAL STUDIO (MASTER ORCHESTRATOR)
# ═══════════════════════════════════════════════════════════

class TestProposalStudio:
    def test_generates_complete_proposal(self):
        studio = get_proposal_studio()
        proposal = studio.generate(sample_oi(), opportunity_id=1)

        assert proposal.id
        assert "Acme Construction" in proposal.title
        assert proposal.company_name == "Acme Construction Ltd."
        assert proposal.current_version == 1
        assert proposal.quality_score >= 0
        assert len(proposal.sections) >= 10, f"Expected >=10 sections, got {len(proposal.sections)}"
        assert len(proposal.versions) == 1

    def test_all_sections_have_content(self):
        studio = get_proposal_studio()
        proposal = studio.generate(sample_oi())
        for s in proposal.sections:
            assert s.id
            assert s.title
            assert s.content, f"Section {s.id} has no content"
            assert s.status == "generated"

    def test_export_markdown(self):
        studio = get_proposal_studio()
        proposal = studio.generate(sample_oi())
        md = studio.export(proposal, format="markdown")
        assert "# Technology Solutions Proposal" in md
        assert "Acme Construction" in md

    def test_export_html(self):
        studio = get_proposal_studio()
        proposal = studio.generate(sample_oi())
        html = studio.export(proposal, format="html")
        assert "<html>" in html

    def test_ready_to_send(self):
        studio = get_proposal_studio()
        proposal = studio.generate(sample_oi())
        assert isinstance(proposal.ready_to_send, bool)

    def test_has_version_history(self):
        studio = get_proposal_studio()
        proposal = studio.generate(sample_oi())
        assert len(proposal.versions) == 1
        assert proposal.versions[0].reason == "Initial generation"

    def test_empty_oi_does_not_crash(self):
        studio = get_proposal_studio()
        proposal = studio.generate(create_empty_intelligence())
        assert proposal.title
        assert len(proposal.sections) >= 5


# ═══════════════════════════════════════════════════════════
# EXTENSION POINTS
# ═══════════════════════════════════════════════════════════

class TestExtensionPoints:
    def test_all_disabled_by_default(self):
        pts = get_extension_points()
        assert pts.case_studies_enabled is False
        assert pts.reference_projects_enabled is False
        assert pts.testimonials_enabled is False
        assert pts.pricing_templates_enabled is False
        assert pts.industry_templates_enabled is False
        assert pts.images_enabled is False
        assert pts.diagrams_enabled is False
        assert pts.videos_enabled is False

    def test_schemas_exist(self):
        for feature in ["case_studies", "testimonials", "images", "videos"]:
            schema = get_extension_schema(feature)
            assert schema is not None
            assert "enabled" in schema
            assert schema["enabled"] is False


# ═══════════════════════════════════════════════════════════
# DETERMINISTIC
# ═══════════════════════════════════════════════════════════

class TestDeterministic:
    def test_same_input_produces_same_proposal(self):
        studio = get_proposal_studio()
        oi = sample_oi()
        p1 = studio.generate(oi)
        p2 = studio.generate(oi)
        assert p1.title == p2.title
        assert p1.quality_score == p2.quality_score
        assert len(p1.sections) == len(p2.sections)

    def test_business_analysis_deterministic(self):
        engine = get_business_analysis_engine()
        oi = sample_oi()
        r1 = engine.analyze(oi)
        r2 = engine.analyze(oi)
        assert r1.executive_summary == r2.executive_summary

    def test_roi_deterministic(self):
        engine = get_roi_engine()
        oi = sample_oi()
        r1 = engine.calculate(oi)
        r2 = engine.calculate(oi)
        assert r1.hours_saved_per_week == r2.hours_saved_per_week
        assert r1.estimated_annual_savings == r2.estimated_annual_savings
