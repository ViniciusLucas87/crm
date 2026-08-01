"""
Proposal Studio — professional consulting proposal platform.

All engines consume OpportunityIntelligence exclusively.
Never ConversationInsights. Never raw transcript.

Architecture:
    OpportunityIntelligence → ProposalStudio → Professional Proposal → Export
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any

from app.domain.opportunity_intelligence import (
    OpportunityIntelligence, TypedValue, Stakeholder, OpportunityStage,
    BusinessContext, SalesContext, SolutionContext, TimelineEvent, EventType,
)


# ═══════════════════════════════════════════════════════════
# BASE TYPES
# ═══════════════════════════════════════════════════════════

@dataclass
class ProposalSection:
    """A collapsible, editable, lockable proposal section."""
    id: str
    title: str
    content: str = ""
    status: str = "generated"  # generated, edited, locked
    generated_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProposalVersion:
    version: int
    created_at: str
    generated_by: str
    reason: str
    sections: list[ProposalSection] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Proposal:
    """Complete consulting-quality software proposal."""
    id: str = ""
    title: str = ""
    company_name: str = ""
    opportunity_id: int | None = None
    generated_at: str = ""

    # ── Sections ──
    sections: list[ProposalSection] = field(default_factory=list)

    # ── Versioning ──
    current_version: int = 1
    versions: list[ProposalVersion] = field(default_factory=list)

    # ── Quality ──
    quality_score: int = 0
    ready_to_send: bool = False
    missing_information: list[str] = field(default_factory=list)

    # ── Metadata ──
    source_intelligence_version: str = ""


# ═══════════════════════════════════════════════════════════
# ROI MODEL
# ═══════════════════════════════════════════════════════════

@dataclass
class ROIAssumption:
    label: str
    value: float
    unit: str
    editable: bool = True
    description: str = ""


@dataclass
class ROIReport:
    hours_saved_per_week: float = 0
    admin_savings_annual: float = 0
    inspection_efficiency_gain: float = 0  # percentage
    paperwork_reduction: float = 0  # percentage
    error_reduction: float = 0  # percentage
    operational_visibility_gain: float = 0  # percentage
    estimated_annual_savings: float = 0
    estimated_payback_months: int = 0
    assumptions: list[ROIAssumption] = field(default_factory=list)
    generated_at: str = ""


# ═══════════════════════════════════════════════════════════
# RISK MODEL
# ═══════════════════════════════════════════════════════════

@dataclass
class AssessedRisk:
    category: str  # business, technical, operational, adoption, integration
    risk: str
    severity: str  # critical, high, medium, low
    likelihood: str  # high, medium, low
    mitigation: str


@dataclass
class RiskAssessment:
    risks: list[AssessedRisk] = field(default_factory=list)
    overall_risk_level: str = "medium"
    generated_at: str = ""


# ═══════════════════════════════════════════════════════════
# SCOPE MODEL
# ═══════════════════════════════════════════════════════════

@dataclass
class ScopeAssessment:
    project_size: str = "medium"  # small, medium, large, enterprise
    complexity: str = "medium"
    technical_complexity: str = "medium"
    integration_complexity: str = "medium"
    implementation_risk: str = "medium"
    training_effort: str = "medium"
    support_effort: str = "medium"
    recommended_team_size: int = 3
    estimated_timeline_weeks: int = 12
    confidence: int = 0
    generated_at: str = ""


# ═══════════════════════════════════════════════════════════
# IMPLEMENTATION PHASE
# ═══════════════════════════════════════════════════════════

@dataclass
class ImplementationPhase:
    phase: int
    name: str
    description: str = ""
    deliverables: list[str] = field(default_factory=list)
    estimated_duration: str = ""
    dependencies: list[str] = field(default_factory=list)


@dataclass
class ImplementationRoadmap:
    phases: list[ImplementationPhase] = field(default_factory=list)
    total_duration: str = ""
    generated_at: str = ""


# ═══════════════════════════════════════════════════════════
# SOLUTION ARCHITECTURE
# ═══════════════════════════════════════════════════════════

@dataclass
class WorkflowStep:
    label: str
    description: str = ""
    role: str = ""


@dataclass
class ArchitectureComponent:
    name: str
    purpose: str = ""
    business_value: str = ""
    reason_selected: str = ""


@dataclass
class SolutionArchitecture:
    current_workflow: list[WorkflowStep] = field(default_factory=list)
    future_workflow: list[WorkflowStep] = field(default_factory=list)
    components: list[ArchitectureComponent] = field(default_factory=list)
    generated_at: str = ""


# ═══════════════════════════════════════════════════════════
# BUSINESS ANALYSIS
# ═══════════════════════════════════════════════════════════

@dataclass
class BusinessAnalysis:
    executive_summary: str = ""
    business_overview: str = ""
    current_situation: str = ""
    operational_challenges: list[str] = field(default_factory=list)
    growth_challenges: list[str] = field(default_factory=list)
    business_risks: list[str] = field(default_factory=list)
    business_opportunities: list[str] = field(default_factory=list)
    generated_at: str = ""


# ═══════════════════════════════════════════════════════════
# PROPOSAL REVIEW
# ═══════════════════════════════════════════════════════════

@dataclass
class ReviewCategory:
    name: str
    score: int  # 0-100
    comment: str = ""


@dataclass
class ProposalReview:
    categories: list[ReviewCategory] = field(default_factory=list)
    overall_score: int = 0
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    missing_information: list[str] = field(default_factory=list)
    ready_to_send: bool = False


# ═══════════════════════════════════════════════════════════
# EXPORT
# ═══════════════════════════════════════════════════════════

@dataclass
class ExportConfig:
    format: str = "pdf"  # pdf, docx, markdown, html
    include_toc: bool = True
    include_page_numbers: bool = True
    company_name: str = "Pacific North Systems"
    company_logo_url: str = ""
    primary_color: str = "#1a365d"
    font_family: str = "Helvetica"
    include_section_numbers: bool = True
    include_timestamps: bool = True


# ═══════════════════════════════════════════════════════════
# EXTENSION POINTS (placeholders)
# ═══════════════════════════════════════════════════════════

@dataclass
class ExtensionPoints:
    """Future extension points — architecture only, not implemented."""
    case_studies_enabled: bool = False
    reference_projects_enabled: bool = False
    testimonials_enabled: bool = False
    pricing_templates_enabled: bool = False
    industry_templates_enabled: bool = False
    images_enabled: bool = False
    diagrams_enabled: bool = False
    videos_enabled: bool = False
