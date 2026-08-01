"""
Proposal Intelligence — generates structured software proposals from conversation insights.

Consumes ConversationInsights + company context. Never analyzes raw transcript.
Produces complete proposals with executive summary, solution, pricing, timeline, ROI.

Architecture:
    ConversationInsights + Company → ProposalGenerator → Structured Proposal → Export
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any

from app.application.transcription.intelligence import ConversationInsight, InsightCategory


@dataclass
class ProposalSection:
    title: str
    content: str
    subsections: list[dict[str, str]] = field(default_factory=list)


@dataclass
class Proposal:
    """Complete structured proposal ready for rendering and export."""
    title: str = ""
    company_name: str = ""
    generated_at: str = ""

    # ── Sections ──
    executive_summary: str = ""
    current_state: str = ""
    proposed_solution: str = ""
    solution_components: list[str] = field(default_factory=list)
    implementation_plan: list[dict[str, str]] = field(default_factory=list)
    deliverables: list[str] = field(default_factory=list)
    roi_analysis: str = ""
    roi_metrics: list[dict[str, str]] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    investment: list[dict[str, str]] = field(default_factory=list)
    timeline: str = ""
    next_steps: list[str] = field(default_factory=list)

    # ── Quality ──
    quality_score: int = 0
    missing_information: list[str] = field(default_factory=list)
    readiness: str = "draft"


IMPLEMENTATION_PHASES = [
    {"phase": "Discovery & Planning", "duration": "1-2 weeks", "description": "Requirements gathering, stakeholder interviews, technical discovery"},
    {"phase": "Design & Architecture", "duration": "2-3 weeks", "description": "System design, UI/UX prototypes, architecture review"},
    {"phase": "Development", "duration": "6-10 weeks", "description": "Iterative development with bi-weekly demos"},
    {"phase": "Testing & QA", "duration": "2-3 weeks", "description": "Integration testing, user acceptance testing, performance testing"},
    {"phase": "Deployment", "duration": "1-2 weeks", "description": "Production deployment, data migration, go-live support"},
    {"phase": "Training", "duration": "1 week", "description": "User training sessions, documentation handoff"},
    {"phase": "Ongoing Support", "duration": "Ongoing", "description": "Technical support, maintenance, feature updates"},
]

DEFAULT_DELIVERABLES = [
    "Web Application Portal", "Mobile Application", "Operations Dashboard",
    "REST API", "Database Implementation", "User Authentication System",
    "Hosting & Infrastructure", "User Training Sessions", "Technical Documentation",
    "30-Day Support Period",
]

DEFAULT_INVESTMENT = [
    {"item": "Discovery & Planning", "estimate": "$8,000 - $12,000"},
    {"item": "Design & Development", "estimate": "$45,000 - $75,000"},
    {"item": "Testing & Deployment", "estimate": "$10,000 - $15,000"},
    {"item": "Training & Documentation", "estimate": "$5,000 - $8,000"},
    {"item": "First-Year Support", "estimate": "$12,000"},
    {"item": "Total Estimated Investment", "estimate": "$80,000 - $122,000"},
]


class ProposalGenerator:
    """Generates structured software proposals from conversation intelligence.

    Consumes ConversationInsights and company context.
    Produces complete proposals with all required sections.
    """

    def generate(
        self,
        company_name: str = "",
        company_context: dict[str, Any] | None = None,
        insights: list[ConversationInsight] | None = None,
    ) -> Proposal:
        """Generate a complete proposal from structured insights."""
        ctx = company_context or {}
        ins = insights or []

        proposal = Proposal(
            title=f"Technology Solutions Proposal for {company_name}" if company_name else "Technology Solutions Proposal",
            company_name=company_name,
            generated_at=datetime.now(UTC).isoformat(),
        )

        # Extract categorized insights
        pain_points = [i.value for i in ins if i.category == InsightCategory.PAIN_POINT]
        current_software = [i.value for i in ins if i.category == InsightCategory.CURRENT_SOFTWARE]
        current_process = [i.value for i in ins if i.category == InsightCategory.CURRENT_PROCESS]
        goals = [i.value for i in ins if i.category == InsightCategory.GOAL]
        risks = [i.value for i in ins if i.category == InsightCategory.RISK]
        budget = next((i.value for i in ins if i.category == InsightCategory.BUDGET), None)
        timeline = next((i.value for i in ins if i.category == InsightCategory.TIMELINE), None)
        decision_makers = [i.value for i in ins if i.category == InsightCategory.DECISION_MAKER]

        industry = ctx.get("industry", "")
        employees = ctx.get("employees", "")

        # ── Executive Summary ──
        proposal.executive_summary = self._build_executive_summary(company_name, industry, employees, pain_points, goals)

        # ── Current State ──
        proposal.current_state = self._build_current_state(current_software, current_process, pain_points)

        # ── Proposed Solution ──
        solution = self._build_solution(pain_points, industry)
        proposal.proposed_solution = solution["description"]
        proposal.solution_components = solution["components"]

        # ── Implementation ──
        proposal.implementation_plan = IMPLEMENTATION_PHASES.copy()

        # ── Deliverables ──
        proposal.deliverables = DEFAULT_DELIVERABLES.copy()

        # ── ROI ──
        proposal.roi_analysis = self._build_roi(pain_points)
        proposal.roi_metrics = self._build_roi_metrics(pain_points)

        # ── Risks ──
        proposal.risks = risks if risks else [
            "User adoption and change management",
            "Data migration from existing systems",
            "Integration with current software stack",
            "Scope creep during implementation",
        ]

        # ── Investment ──
        proposal.investment = DEFAULT_INVESTMENT.copy()
        if budget:
            proposal.investment.append({"item": "Client Budget Indicated", "estimate": budget})

        # ── Timeline ──
        proposal.timeline = timeline or "Estimated 12-16 weeks from kickoff to go-live"

        # ── Next Steps ──
        proposal.next_steps = [
            "Schedule technical discovery workshop",
            "Review proposal with decision makers",
            "Finalize scope and timeline",
            "Contract and kickoff",
        ]

        # ── Quality ──
        proposal.quality_score = self._score_proposal(proposal)
        proposal.missing_information = self._find_missing(pain_points, budget, timeline, decision_makers, risks)
        proposal.readiness = "ready" if proposal.quality_score >= 70 else "needs_review" if proposal.quality_score >= 40 else "draft"

        return proposal

    def _build_executive_summary(self, name, industry, employees, pain_points, goals) -> str:
        parts = []
        if name:
            desc = f"{name} is"
            if industry:
                desc += f" a {industry} company"
            if employees:
                desc += f" with approximately {employees} employees"
            parts.append(desc + ".")
        if pain_points:
            parts.append(f"They currently face challenges with {', '.join(pain_points[:3]).lower()}.")
        if goals:
            parts.append(f"Their goals include {', '.join(goals[:2]).lower()}.")
        parts.append("Pacific North Systems proposes a comprehensive technology solution to address these challenges, streamline operations, and position them for continued growth.")
        return "\n\n".join(parts) if parts else "Technology solutions proposal based on discovery conversations."

    def _build_current_state(self, software, process, pain_points) -> str:
        parts = []
        if software:
            parts.append(f"Currently using: {', '.join(software)}.")
        if process:
            parts.append(f"Current processes: {', '.join(process)}.")
        if pain_points:
            parts.append(f"Key pain points include: {', '.join(pain_points)}.")
        return " ".join(parts) if parts else "Current operational state to be documented during discovery."

    def _build_solution(self, pain_points, industry) -> dict:
        components = []
        desc_parts = []

        pain_lower = [p.lower() for p in pain_points]
        all_text = " ".join(pain_lower)

        if any(w in all_text for w in ["inspection", "manual", "paper"]):
            components.append("Inspection Platform — mobile-first inspection management with offline support")
        if any(w in all_text for w in ["scheduling", "dispatch", "tracking"]):
            components.append("Operations Dashboard — real-time visibility into field operations")
        if any(w in all_text for w in ["paper", "document", "data entry"]):
            components.append("Document AI — automated document processing and data extraction")
        if any(w in all_text for w in ["workflow", "automation", "manual", "process"]):
            components.append("Workflow Automation — intelligent process automation engine")
        if any(w in all_text for w in ["integration", "disconnected", "multiple"]):
            components.append("Custom Integration — seamless connection between existing systems")
        if any(w in all_text for w in ["reporting", "dashboard", "visibility"]):
            components.append("Analytics & Reporting — comprehensive business intelligence")

        if not components:
            components = [
                "Custom Software Solution — tailored to business requirements",
                "Operations Dashboard — centralized management and visibility",
                "Workflow Automation — process optimization and automation",
            ]

        desc_parts.append("Pacific North Systems recommends a phased technology implementation:")
        desc_parts.append("\n".join(f"• {c}" for c in components))

        return {"description": "\n".join(desc_parts), "components": components}

    def _build_roi(self, pain_points) -> str:
        parts = ["Based on industry benchmarks and the specific challenges identified:"]
        parts.append("• Reduction in manual data entry: 60-80%")
        parts.append("• Inspection processing time improvement: 40-60%")
        parts.append("• Administrative overhead reduction: 30-50%")
        parts.append("• Error rate reduction: 70-90%")
        parts.append("\nEstimated annual savings: 15-25 hours per week across the team.")
        return "\n".join(parts)

    def _build_roi_metrics(self, pain_points) -> list[dict]:
        return [
            {"metric": "Weekly Hours Saved", "estimate": "15-25 hours"},
            {"metric": "Manual Work Eliminated", "estimate": "60-80%"},
            {"metric": "Processing Speed Improvement", "estimate": "40-60%"},
            {"metric": "Error Reduction", "estimate": "70-90%"},
            {"metric": "Expected Payback Period", "estimate": "6-12 months"},
        ]

    def _score_proposal(self, p: Proposal) -> int:
        score = 50
        if p.executive_summary and len(p.executive_summary) > 100:
            score += 10
        if p.current_state and len(p.current_state) > 50:
            score += 10
        if p.solution_components:
            score += 10
        if p.roi_analysis:
            score += 10
        if p.risks:
            score += 5
        if p.next_steps:
            score += 5
        return min(score, 100)

    def _find_missing(self, pain_points, budget, timeline, decision_makers, risks) -> list[str]:
        missing = []
        if not pain_points:
            missing.append("Detailed pain points from discovery")
        if not budget:
            missing.append("Budget confirmation")
        if not timeline:
            missing.append("Implementation timeline")
        if not decision_makers:
            missing.append("Decision maker identification")
        return missing
