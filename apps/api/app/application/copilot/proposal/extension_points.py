"""
Extension Points — architecture-only placeholders for future features.

Not implemented. These define the integration contracts for:
    Case Studies, Reference Projects, Testimonials, Pricing Templates,
    Industry Templates, Images, Diagrams, Videos.
"""

from __future__ import annotations

from app.application.copilot.proposal.models import ExtensionPoints


EXTENSION_SCHEMA = {
    "case_studies": {
        "enabled": False,
        "schema": {"title": "str", "client": "str", "challenge": "str", "solution": "str", "results": "str", "tags": "list[str]"},
        "integration": "CaseStudyProvider → ProposalComponent",
    },
    "reference_projects": {
        "enabled": False,
        "schema": {"title": "str", "industry": "str", "description": "str", "outcome": "str"},
        "integration": "ReferenceProvider → ProposalComponent",
    },
    "testimonials": {
        "enabled": False,
        "schema": {"client_name": "str", "title": "str", "quote": "str", "avatar_url": "str"},
        "integration": "TestimonialProvider → ProposalComponent",
    },
    "pricing_templates": {
        "enabled": False,
        "schema": {"template_id": "str", "items": "list[PricingLine]", "total": "Decimal"},
        "integration": "PricingTemplateProvider → InvestmentBlock",
    },
    "industry_templates": {
        "enabled": False,
        "schema": {"industry": "str", "prebuilt_sections": "list[ProposalSection]", "boilerplate": "str"},
        "integration": "IndustryTemplateProvider → ProposalStudio",
    },
    "images": {
        "enabled": False,
        "schema": {"url": "str", "alt": "str", "caption": "str", "section_id": "str"},
        "integration": "MediaProvider → ProposalSection.render()",
    },
    "diagrams": {
        "enabled": False,
        "schema": {"type": "str", "source": "str", "rendered_url": "str"},
        "integration": "DiagramProvider → ArchitectureBlock",
    },
    "videos": {
        "enabled": False,
        "schema": {"url": "str", "thumbnail": "str", "duration": "int", "transcript": "str"},
        "integration": "VideoProvider → ProposalSection",
    },
}


def get_extension_points() -> ExtensionPoints:
    """Return the current state of all extension points."""
    return ExtensionPoints()


def get_extension_schema(feature: str) -> dict | None:
    """Get the schema for a specific extension point."""
    return EXTENSION_SCHEMA.get(feature)
