"""
Solution Architecture Engine — generates current → future workflow visualizations.

Consumes ONLY OpportunityIntelligence. Produces workflow diagrams with purpose,
business value, and selection rationale for each component.
"""

from __future__ import annotations

from datetime import datetime, UTC

from app.domain.opportunity_intelligence import OpportunityIntelligence
from app.application.copilot.proposal.models import (
    SolutionArchitecture, WorkflowStep, ArchitectureComponent,
)


# ── Component definitions with business rationale ──

COMPONENT_LIBRARY: dict[str, dict] = {
    "Inspection Platform": {
        "purpose": "Mobile-first inspection management with offline capability",
        "business_value": "Eliminates paper forms, reduces inspection time by 40-60%, enables real-time quality monitoring",
        "triggers": ["inspection", "audit", "field", "site"],
    },
    "Operations Dashboard": {
        "purpose": "Real-time operational visibility across all business functions",
        "business_value": "Consolidates spreadsheet-based tracking into a single source of truth, enabling data-driven decisions",
        "triggers": ["spreadsheet", "excel", "dashboard", "reporting", "visibility"],
    },
    "Document AI": {
        "purpose": "Automated document processing and intelligent data extraction",
        "business_value": "Reduces manual data entry by 60-80%, eliminates transcription errors, accelerates processing",
        "triggers": ["paper", "paperwork", "document", "data entry", "scan", "compliance"],
    },
    "Workflow Automation": {
        "purpose": "Intelligent process automation engine for repetitive tasks",
        "business_value": "Eliminates duplicate data entry, standardizes processes, reduces administrative overhead by 30-50%",
        "triggers": ["workflow", "automation", "manual", "duplicate", "double entry"],
    },
    "Custom Integration": {
        "purpose": "Seamless connection between existing software investments",
        "business_value": "Eliminates data silos, ensures single source of truth, preserves existing technology investments",
        "triggers": ["integration", "disconnected", "multiple system", "silo"],
    },
    "Field Service Management": {
        "purpose": "Optimized dispatch, scheduling, and field team coordination",
        "business_value": "Reduces travel time, improves first-time fix rate, increases daily throughput per technician",
        "triggers": ["dispatch", "scheduling", "field", "technician", "mobile", "route"],
    },
    "Client Portal": {
        "purpose": "Self-service platform for client communication and document sharing",
        "business_value": "Reduces administrative follow-up, improves client satisfaction, provides transparent project visibility",
        "triggers": ["client", "customer portal", "communication", "follow-up"],
    },
    "Analytics Platform": {
        "purpose": "Comprehensive business intelligence and reporting engine",
        "business_value": "Transforms raw operational data into actionable insights, enabling proactive management",
        "triggers": ["analytics", "reporting", "metrics", "kpi"],
    },
}


class SolutionArchitectureEngine:
    """Generates solution architecture from OpportunityIntelligence.

    Produces current workflow → future workflow mappings with component
    rationale, purpose, and business value.
    """

    def design(self, oi: OpportunityIntelligence) -> SolutionArchitecture:
        now = datetime.now(UTC).isoformat()

        current_workflow = self._infer_current_workflow(oi)
        future_workflow = self._design_future_workflow(oi, current_workflow)
        components = self._select_components(oi)

        return SolutionArchitecture(
            current_workflow=current_workflow,
            future_workflow=future_workflow,
            components=components,
            generated_at=now,
        )

    def _infer_current_workflow(self, oi: OpportunityIntelligence) -> list[WorkflowStep]:
        steps: list[WorkflowStep] = []

        # Infer from current process descriptions
        processes = [p.value for p in oi.business.current_process if p.value]
        process_text = " ".join(processes).lower() if processes else ""

        has_field = any(w in process_text for w in ["field", "technician", "site", "inspection"])
        has_paper = any(w in process_text for w in ["paper", "form", "handwritten", "print"])
        has_spreadsheet = any(w in process_text for w in ["spreadsheet", "excel", "sheet"])
        has_manager = any(w in process_text for w in ["manager", "supervisor", "review", "approve"])
        has_accounting = any(w in process_text for w in ["accounting", "quickbooks", "invoice", "finance"])

        software = [s.value for s in oi.business.current_software if s.value]

        if has_field:
            steps.append(WorkflowStep(
                label="Field Technician",
                description="Performs work at client sites, documents findings manually",
                role="Operations",
            ))

        if has_paper or not steps:
            steps.append(WorkflowStep(
                label="Paper Forms" if has_paper else "Manual Documentation",
                description="Data captured on paper forms or spreadsheets at point of work",
                role="Operations",
            ))

        if has_spreadsheet or software:
            sw_name = software[0] if software else "Spreadsheets"
            steps.append(WorkflowStep(
                label=sw_name,
                description="Data transcribed into digital format, often with duplication across systems",
                role="Administration",
            ))

        if has_manager:
            steps.append(WorkflowStep(
                label="Manager Review",
                description="Manual review and approval of documentation",
                role="Management",
            ))

        if has_accounting or (software and any("quickbooks" in s.lower() for s in software)):
            steps.append(WorkflowStep(
                label="Accounting System",
                description="Financial data entry separate from operational records",
                role="Finance",
            ))

        # Ensure minimum workflow
        if len(steps) < 2:
            steps = [
                WorkflowStep(label="Data Capture", description="Information collected manually", role="Operations"),
                WorkflowStep(label="Manual Processing", description="Data processed through spreadsheets", role="Administration"),
                WorkflowStep(label="Reporting", description="Reports generated manually for review", role="Management"),
            ]

        return steps

    def _design_future_workflow(self, oi: OpportunityIntelligence, current: list[WorkflowStep]) -> list[WorkflowStep]:
        steps: list[WorkflowStep] = []

        pain_text = " ".join([p.value or "" for p in oi.business.pain_points]).lower()
        software_text = " ".join([s.value or "" for s in oi.business.current_software]).lower()
        all_text = pain_text + " " + software_text

        # Inspection → Inspection Platform
        if any(w in all_text for w in ["inspection", "field", "technician", "site"]):
            steps.append(WorkflowStep(
                label="Inspection Platform",
                description="Mobile app captures all field data digitally with photos, GPS, and timestamps",
                role="Field Operations",
            ))

        # Paper/Document → Document AI
        if any(w in all_text for w in ["paper", "document", "data entry", "form"]):
            steps.append(WorkflowStep(
                label="Document AI",
                description="Automated document processing extracts data from forms, eliminating manual transcription",
                role="Automation",
            ))

        # Dashboard
        if any(w in all_text for w in ["spreadsheet", "excel", "dashboard", "reporting", "visibility", "tracking"]):
            steps.append(WorkflowStep(
                label="Operations Dashboard",
                description="Real-time visibility into all operations with automated reporting and alerts",
                role="Management",
            ))

        # Integration
        if any(w in all_text for w in ["integration", "disconnected", "accounting", "quickbooks"]):
            steps.append(WorkflowStep(
                label="Accounting Integration",
                description="Seamless data flow between operational and financial systems",
                role="Integration",
            ))

        # Workflow automation
        if any(w in all_text for w in ["workflow", "automation", "manual", "duplicate"]):
            steps.append(WorkflowStep(
                label="Workflow Automation",
                description="Automated routing, approvals, and notifications eliminate manual handoffs",
                role="Automation",
            ))

        # Ensure minimum
        if len(steps) < 3:
            steps = [
                WorkflowStep(label="Mobile Data Capture", description="Digital capture at point of work", role="Operations"),
                WorkflowStep(label="Cloud Platform", description="Centralized data with role-based access", role="Platform"),
                WorkflowStep(label="Automated Reporting", description="Real-time dashboards and scheduled reports", role="Management"),
            ]

        return steps

    def _select_components(self, oi: OpportunityIntelligence) -> list[ArchitectureComponent]:
        components: list[ArchitectureComponent] = []
        selected_names: set[str] = set()

        pain_text = " ".join([p.value or "" for p in oi.business.pain_points]).lower()
        software_text = " ".join([s.value or "" for s in oi.business.current_software]).lower()
        all_text = pain_text + " " + software_text

        for name, defn in COMPONENT_LIBRARY.items():
            if name in selected_names:
                continue
            if any(t in all_text for t in defn["triggers"]):
                components.append(ArchitectureComponent(
                    name=name,
                    purpose=defn["purpose"],
                    business_value=defn["business_value"],
                    reason_selected=f"Selected based on operational analysis: {defn['triggers'][0]} detected in current environment.",
                ))
                selected_names.add(name)

        return components


# Singleton
_engine: SolutionArchitectureEngine | None = None


def get_solution_architecture_engine() -> SolutionArchitectureEngine:
    global _engine
    if _engine is None:
        _engine = SolutionArchitectureEngine()
    return _engine
