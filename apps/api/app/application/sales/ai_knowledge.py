"""
AI Knowledge Base Architecture.

Prepares the internal knowledge system for future AI consumption.
Currently defines the data model and API contracts.
Vector search will be added in a future sprint.
"""

from pydantic import BaseModel


class KnowledgeCategory(BaseModel):
    id: str
    name: str
    description: str
    item_count: int
    status: str  # "populated", "ready", "planned"


class KnowledgeBaseOverview(BaseModel):
    categories: list[KnowledgeCategory]
    total_items: int
    ready_for_ai: bool
    message: str


class KnowledgeBaseArchitecture:
    """
    Knowledge Base Architecture — prepared for future AI consumption.

    Categories:
    1. Services — Pacific North Systems service offerings
    2. Pricing — Pricing models and tiers
    3. Projects — Past project case studies
    4. Case Studies — Industry-specific success stories
    5. Proposal Templates — Reusable proposal structures
    6. Implementation Guides — Technical documentation
    7. FAQs — Common questions and answers
    8. Sales Methodology — Best practices and frameworks
    """

    CATEGORIES: list[dict[str, str]] = [
        {"id": "services", "name": "Services", "description": "Service offerings, descriptions, and capabilities", "status": "planned"},
        {"id": "pricing", "name": "Pricing", "description": "Pricing models, tiers, and typical ranges", "status": "planned"},
        {"id": "projects", "name": "Projects", "description": "Past project summaries and outcomes", "status": "planned"},
        {"id": "case_studies", "name": "Case Studies", "description": "Industry-specific success stories with metrics", "status": "planned"},
        {"id": "templates", "name": "Proposal Templates", "description": "Reusable proposal and SOW templates", "status": "planned"},
        {"id": "guides", "name": "Implementation Guides", "description": "Technical documentation and implementation playbooks", "status": "planned"},
        {"id": "faqs", "name": "FAQs", "description": "Common prospect questions and approved answers", "status": "planned"},
        {"id": "methodology", "name": "Sales Methodology", "description": "Sales frameworks, qualification criteria, and best practices", "status": "planned"},
    ]

    def get_overview(self) -> KnowledgeBaseOverview:
        categories = [
            KnowledgeCategory(
                id=c["id"], name=c["name"], description=c["description"],
                item_count=0, status=c["status"],
            )
            for c in self.CATEGORIES
        ]
        return KnowledgeBaseOverview(
            categories=categories,
            total_items=0,
            ready_for_ai=False,
            message="Knowledge Base architecture is defined. Content population is planned for a future sprint. Once populated, this will serve as the AI's business knowledge foundation — enabling context-aware recommendations grounded in Pacific North Systems' actual services, pricing, and methodology.",
        )

    def get_mcp_context_schema(self) -> dict:
        """Returns the MCP context schema for future AI agent integration."""
        return {
            "version": "1.0",
            "contexts": {
                "company_context": {"source": "CRM", "fields": ["name", "industry", "employees", "opportunity_score", "contacts", "activities"]},
                "proposal_context": {"source": "AI Proposal Builder", "fields": ["company", "recommended_services", "estimated_value", "timeline"]},
                "meeting_context": {"source": "AI Meeting Prep", "fields": ["company", "timeline", "contacts", "opportunities", "talking_points"]},
                "opportunity_context": {"source": "CRM + Scoring Engine", "fields": ["score", "confidence", "breakdown", "signals", "services"]},
                "timeline_context": {"source": "CRM Timeline", "fields": ["activities", "calls", "emails", "meetings", "tasks"]},
                "knowledge_context": {"source": "Knowledge Base", "fields": ["services", "pricing", "case_studies", "methodology"], "status": "planned"},
            },
        }
