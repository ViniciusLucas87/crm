"""
Implementation Roadmap — generates professional phased implementation timeline.

Consumes ONLY OpportunityIntelligence. Produces 7-phase roadmap with
deliverables, estimated duration, and dependencies.
"""

from __future__ import annotations

from datetime import datetime, UTC

from app.domain.opportunity_intelligence import OpportunityIntelligence
from app.application.copilot.proposal.models import (
    ImplementationRoadmap, ImplementationPhase,
)
from app.application.copilot.proposal.scope_engine import ScopeEngine


DEFAULT_PHASES = [
    {
        "name": "Discovery & Planning",
        "description": "Requirements gathering, stakeholder interviews, technical discovery, and project planning.",
        "deliverables": [
            "Requirements Document",
            "Technical Architecture Blueprint",
            "Project Plan with Milestones",
            "Risk Register",
        ],
        "dependencies": [],
    },
    {
        "name": "Solution Design",
        "description": "System architecture design, UI/UX prototypes, integration specifications, and data model design.",
        "deliverables": [
            "System Architecture Document",
            "UI/UX Prototypes",
            "Integration Specifications",
            "Data Model and Schema Design",
        ],
        "dependencies": ["Discovery & Planning"],
    },
    {
        "name": "Development",
        "description": "Iterative development with bi-weekly sprint reviews and continuous stakeholder feedback.",
        "deliverables": [
            "Working Software (incremental)",
            "API Documentation",
            "Integration Implementations",
            "Sprint Review Reports",
        ],
        "dependencies": ["Solution Design"],
    },
    {
        "name": "Quality Assurance",
        "description": "Integration testing, user acceptance testing, performance testing, and security audit.",
        "deliverables": [
            "Test Results Report",
            "UAT Sign-off",
            "Performance Test Results",
            "Security Audit Report",
        ],
        "dependencies": ["Development"],
    },
    {
        "name": "Deployment",
        "description": "Production deployment, data migration, go-live support, and operational handoff.",
        "deliverables": [
            "Production Environment",
            "Data Migration Completion Report",
            "Deployment Runbook",
            "Go-Live Support Plan",
        ],
        "dependencies": ["Quality Assurance"],
    },
    {
        "name": "Training",
        "description": "End-user training sessions, administrator training, documentation handoff.",
        "deliverables": [
            "Training Materials",
            "User Manuals",
            "Administrator Guide",
            "Training Completion Records",
        ],
        "dependencies": ["Deployment"],
    },
    {
        "name": "Ongoing Support",
        "description": "Technical support, maintenance updates, feature enhancements, and performance monitoring.",
        "deliverables": [
            "Support SLA",
            "Maintenance Schedule",
            "Performance Dashboard",
            "Quarterly Review Reports",
        ],
        "dependencies": ["Training"],
    },
]


class ImplementationRoadmapEngine:
    """Generates phased implementation timeline from OpportunityIntelligence.

    Produces professional roadmap with durations scaled to project scope.
    """

    def generate(self, oi: OpportunityIntelligence) -> ImplementationRoadmap:
        now = datetime.now(UTC).isoformat()
        scope = ScopeEngine().assess(oi)

        # Scale durations based on project size
        duration_map = {
            "small": [1, 2, 4, 2, 1, 1, 999],   # weeks per phase (999 = ongoing)
            "medium": [2, 3, 8, 3, 2, 1, 999],
            "large": [3, 4, 12, 4, 3, 2, 999],
            "enterprise": [4, 6, 16, 6, 4, 2, 999],
        }

        durations = duration_map.get(scope.project_size, duration_map["medium"])

        phases: list[ImplementationPhase] = []
        for i, phase_def in enumerate(DEFAULT_PHASES):
            dur = durations[i]
            dur_str = f"{dur} weeks" if dur < 999 else "Ongoing"

            phases.append(ImplementationPhase(
                phase=i + 1,
                name=phase_def["name"],
                description=phase_def["description"],
                deliverables=phase_def["deliverables"],
                estimated_duration=dur_str,
                dependencies=phase_def["dependencies"],
            ))

        # Total duration
        total_weeks = sum(d for d in durations if d < 999)
        total = f"{total_weeks} weeks ({total_weeks // 4} months)"

        return ImplementationRoadmap(phases=phases, total_duration=total, generated_at=now)


# Singleton
_engine: ImplementationRoadmapEngine | None = None


def get_implementation_roadmap_engine() -> ImplementationRoadmapEngine:
    global _engine
    if _engine is None:
        _engine = ImplementationRoadmapEngine()
    return _engine
