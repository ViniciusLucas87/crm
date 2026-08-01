"""
Component Library — reusable proposal section blocks.

Each component encapsulates a proposal section that can be used across
multiple proposals and future modules. Components are self-contained
with rendering logic and metadata.
"""

from __future__ import annotations

from app.application.copilot.proposal.models import ProposalSection


class ComponentLibrary:
    """Registry of reusable proposal section components."""

    @staticmethod
    def executive_summary(content: str, generated_at: str = "") -> ProposalSection:
        return ProposalSection(
            id="executive_summary",
            title="Executive Summary",
            content=content,
            generated_at=generated_at,
        )

    @staticmethod
    def business_assessment(content: str, generated_at: str = "") -> ProposalSection:
        return ProposalSection(
            id="business_assessment",
            title="Business Assessment",
            content=content,
            generated_at=generated_at,
        )

    @staticmethod
    def current_state(content: str, generated_at: str = "") -> ProposalSection:
        return ProposalSection(
            id="current_state",
            title="Current State Analysis",
            content=content,
            generated_at=generated_at,
        )

    @staticmethod
    def current_workflow(steps: list[str], generated_at: str = "") -> ProposalSection:
        flow = "\n".join(f"• **{s}**" for s in steps)
        return ProposalSection(
            id="current_workflow",
            title="Current Workflow",
            content=f"The current operational workflow follows this path:\n\n{flow}",
            generated_at=generated_at,
        )

    @staticmethod
    def future_architecture(components: list[dict], generated_at: str = "") -> ProposalSection:
        lines = ["The recommended solution architecture comprises the following components:"]
        for c in components:
            lines.append(f"\n### {c.get('name', 'Component')}")
            if c.get("purpose"):
                lines.append(f"**Purpose:** {c['purpose']}")
            if c.get("business_value"):
                lines.append(f"**Business Value:** {c['business_value']}")
            if c.get("reason_selected"):
                lines.append(f"**Why Selected:** {c['reason_selected']}")
        return ProposalSection(
            id="future_architecture",
            title="Solution Architecture",
            content="\n".join(lines),
            generated_at=generated_at,
        )

    @staticmethod
    def business_benefits(benefits: list[str], generated_at: str = "") -> ProposalSection:
        content = "\n".join(f"• {b}" for b in benefits) if benefits else "Benefits will be detailed during solution design."
        return ProposalSection(
            id="business_benefits",
            title="Business Benefits",
            content=content,
            generated_at=generated_at,
        )

    @staticmethod
    def roi_block(
        hours_saved: float, annual_savings: float, payback_months: int,
        assumptions: list[dict], generated_at: str = "",
    ) -> ProposalSection:
        lines = [
            "## Return on Investment",
            "",
            f"**Hours Saved per Week:** {hours_saved:.1f}",
            f"**Estimated Annual Savings:** ${annual_savings:,.0f}",
            f"**Estimated Payback Period:** {payback_months} months",
            "",
            "### Assumptions",
        ]
        for a in assumptions:
            lines.append(f"• **{a.get('label', 'Assumption')}:** {a.get('value', '')} {a.get('unit', '')} — {a.get('description', '')}")

        return ProposalSection(
            id="roi",
            title="Return on Investment",
            content="\n".join(lines),
            generated_at=generated_at,
        )

    @staticmethod
    def implementation_roadmap(phases: list[dict], total_duration: str, generated_at: str = "") -> ProposalSection:
        lines = [f"**Total Duration:** {total_duration}"]
        for p in phases:
            lines.append(f"\n### Phase {p.get('phase', '?')}: {p.get('name', 'Phase')}")
            lines.append(f"**Duration:** {p.get('estimated_duration', 'TBD')}")
            lines.append(f"**Description:** {p.get('description', '')}")
            if p.get("deliverables"):
                lines.append("**Deliverables:**")
                for d in p["deliverables"]:
                    lines.append(f"  • {d}")
        return ProposalSection(
            id="implementation_roadmap",
            title="Implementation Roadmap",
            content="\n".join(lines),
            generated_at=generated_at,
        )

    @staticmethod
    def deliverables(items: list[str], generated_at: str = "") -> ProposalSection:
        content = "\n".join(f"• {item}" for item in items)
        return ProposalSection(
            id="deliverables",
            title="Deliverables",
            content=content,
            generated_at=generated_at,
        )

    @staticmethod
    def timeline(content: str, generated_at: str = "") -> ProposalSection:
        return ProposalSection(
            id="timeline",
            title="Timeline",
            content=content,
            generated_at=generated_at,
        )

    @staticmethod
    def investment(items: list[dict], generated_at: str = "") -> ProposalSection:
        lines = ["| Item | Estimate |", "|------|----------|"]
        for item in items:
            lines.append(f"| {item.get('item', 'Item')} | {item.get('estimate', 'TBD')} |")
        return ProposalSection(
            id="investment",
            title="Investment",
            content="\n".join(lines),
            generated_at=generated_at,
        )

    @staticmethod
    def risks(risks: list[dict], overall: str, generated_at: str = "") -> ProposalSection:
        lines = [f"**Overall Risk Level:** {overall}", ""]
        for r in risks:
            lines.append(f"### {r.get('risk', 'Risk')}")
            lines.append(f"• **Severity:** {r.get('severity', 'N/A')}")
            lines.append(f"• **Likelihood:** {r.get('likelihood', 'N/A')}")
            lines.append(f"• **Mitigation:** {r.get('mitigation', 'N/A')}")
            lines.append("")
        return ProposalSection(
            id="risks",
            title="Risk Assessment",
            content="\n".join(lines),
            generated_at=generated_at,
        )

    @staticmethod
    def assumptions(items: list[dict], generated_at: str = "") -> ProposalSection:
        content = "\n".join(
            f"• **{a.get('label', 'Assumption')}:** {a.get('value', '')} {a.get('unit', '')}"
            for a in items
        )
        return ProposalSection(
            id="assumptions",
            title="Assumptions",
            content=content,
            generated_at=generated_at,
        )

    @staticmethod
    def next_steps(steps: list[str], generated_at: str = "") -> ProposalSection:
        content = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(steps))
        return ProposalSection(
            id="next_steps",
            title="Next Steps",
            content=content,
            generated_at=generated_at,
        )
