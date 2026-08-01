"""
Demand Intelligence Engine — Provider Framework

Abstract interface for signal providers. Every data source implements this.
Pluggable architecture — add new providers without changing engine code.

Providers:
    Reddit, LinkedIn, Google, Company websites, Indeed, Glassdoor,
    GitHub, News, Industry forums, Government tenders, etc.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import StrEnum
from typing import Any


class SignalSource(StrEnum):
    REDDIT = "reddit"
    LINKEDIN = "linkedin"
    GOOGLE = "google"
    COMPANY_WEBSITE = "company_website"
    GOOGLE_BUSINESS = "google_business"
    INDEED = "indeed"
    GLASSDOOR = "glassdoor"
    COMPANY_CAREERS = "company_careers"
    GITHUB = "github"
    STACK_OVERFLOW = "stackoverflow"
    FACEBOOK = "facebook"
    X = "x"
    NEWS = "news"
    BLOG = "blog"
    FORUM = "forum"
    INDUSTRY_COMMUNITY = "industry_community"
    GOVERNMENT_TENDER = "government_tender"
    PROCUREMENT_PORTAL = "procurement_portal"
    CONSTRUCTION_FORUM = "construction_forum"
    PROPERTY_MANAGEMENT = "property_management"
    HVAC_FORUM = "hvac_forum"
    ELECTRICAL_FORUM = "electrical_forum"
    MUNICIPAL_PROCUREMENT = "municipal_procurement"
    OTHER = "other"


class PainType(StrEnum):
    SOFTWARE_NEED = "software_need"
    CRM_NEED = "crm_need"
    AUTOMATION_NEED = "automation_need"
    INSPECTION_SOFTWARE = "inspection_software"
    DISPATCH_SOFTWARE = "dispatch_software"
    REPORTING_NEED = "reporting_need"
    SPREADSHEET_PAIN = "spreadsheet_pain"
    MANUAL_PROCESS = "manual_process"
    REPLACING_SOFTWARE = "replacing_software"
    EVALUATING_VENDORS = "evaluating_vendors"
    OPERATIONAL_BOTTLENECK = "operational_bottleneck"
    HIRING_OPS = "hiring_ops"
    HIRING_PROCESS_IMPROVEMENT = "hiring_process_improvement"
    DIGITAL_TRANSFORMATION = "digital_transformation"
    FIELD_SERVICE = "field_service"
    SCHEDULING = "scheduling"
    INVENTORY = "inventory"
    COMPLIANCE = "compliance"
    PAPER_INSPECTIONS = "paper_inspections"
    AI_LOOKING = "ai_looking"
    ERP_REPLACEMENT = "erp_replacement"


class Urgency(StrEnum):
    CRITICAL = "critical"  # Immediate need
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MONITOR = "monitor"  # Long-term trend


class RecommendedAction(StrEnum):
    COLD_EMAIL = "cold_email"
    LINKEDIN_MESSAGE = "linkedin_message"
    PHONE_CALL = "phone_call"
    WAIT = "wait"
    MONITOR = "monitor"
    NOT_QUALIFIED = "not_qualified"
    CREATE_PROPOSAL = "create_proposal"
    REQUEST_DEMO = "request_demo"


@dataclass
class RawSignal:
    """Raw signal detected from a provider before processing."""
    source: SignalSource
    source_url: str
    title: str
    content: str
    author: str | None = None
    author_title: str | None = None
    company_name: str | None = None
    published_at: str | None = None
    location: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ClassifiedSignal:
    """Signal after AI classification and enrichment."""
    # ── From RawSignal ──
    source: SignalSource
    source_url: str
    title: str
    content: str
    author: str | None = None
    author_title: str | None = None
    company_name: str | None = None
    published_at: str | None = None
    location: str | None = None

    # ── Classification ──
    pain_type: PainType | None = None
    industry: str | None = None
    business_size: str | None = None  # small | medium | enterprise
    urgency: Urgency = Urgency.MEDIUM
    buying_intent: int = 0  # 0-100
    estimated_budget: str | None = None
    technology_maturity: str | None = None  # low | medium | high
    operational_complexity: str | None = None
    potential_fit: str | None = None  # low | medium | high | perfect
    recommended_solution: str | None = None
    confidence: float = 0.5

    # ── Lead scoring ──
    lead_score: int = 0  # 0-100
    recommended_action: RecommendedAction = RecommendedAction.MONITOR

    # ── Extracted entities ──
    technologies_mentioned: list[str] = field(default_factory=list)
    competitors_mentioned: list[str] = field(default_factory=list)
    software_mentioned: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)

    # ── Metadata ──
    processed_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════
# PROVIDER INTERFACE
# ═══════════════════════════════════════════════════════════

class SignalProvider(ABC):
    """Abstract interface for all signal providers.

    Usage:
        class RedditProvider(SignalProvider):
            @property
            def provider_name(self) -> str: return "reddit"

            async def search(self, query, filters) -> list[RawSignal]: ...
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique identifier matching SignalSource enum."""

    @abstractmethod
    async def search(self, query: str, filters: dict[str, Any] | None = None) -> list[RawSignal]:
        """Execute a search and return raw signals."""

    @abstractmethod
    async def normalize(self, raw: RawSignal) -> ClassifiedSignal:
        """Convert raw signal to classified signal."""

    async def health_check(self) -> bool:
        """Verify provider availability."""
        return True

    async def get_limits(self) -> dict[str, Any]:
        """Return provider rate limits."""
        return {"requests_per_minute": 10, "requests_per_day": 100}


class MockSignalProvider(SignalProvider):
    """Simulated signal provider for development/testing."""

    @property
    def provider_name(self) -> str:
        return "mock"

    async def search(self, query: str, filters: dict[str, Any] | None = None) -> list[RawSignal]:
        return []

    async def normalize(self, raw: RawSignal) -> ClassifiedSignal:
        return ClassifiedSignal(
            source=raw.source, source_url=raw.source_url,
            title=raw.title, content=raw.content,
            pain_type=PainType.SOFTWARE_NEED,
            lead_score=50, confidence=0.5,
        )


# ═══════════════════════════════════════════════════════════
# BUYING SIGNAL LIBRARY
# ═══════════════════════════════════════════════════════════

BUYING_SIGNAL_PATTERNS: dict[PainType, list[str]] = {
    PainType.SOFTWARE_NEED: [
        "need software", "looking for software", "software recommendation",
        "recommend software", "best software for", "software solution",
        "need a system", "looking for a platform",
    ],
    PainType.CRM_NEED: [
        "need crm", "looking for crm", "crm recommendation",
        "customer management", "manage customers", "client tracking",
        "need to track", "sales pipeline",
    ],
    PainType.AUTOMATION_NEED: [
        "need automation", "looking for automation", "automate",
        "manual process", "streamline", "workflow automation",
        "need to automate", "automating",
    ],
    PainType.INSPECTION_SOFTWARE: [
        "inspection software", "inspection app", "inspection platform",
        "need inspection", "digital inspection", "paperless inspection",
        "inspection report", "field inspection",
    ],
    PainType.DISPATCH_SOFTWARE: [
        "dispatch software", "dispatch system", "scheduling software",
        "route optimization", "field service management", "fsm",
        "dispatch app", "need dispatch",
    ],
    PainType.REPORTING_NEED: [
        "need reporting", "reporting tool", "dashboard",
        "need reports", "analytics", "business intelligence",
        "data visualization", "report builder",
    ],
    PainType.SPREADSHEET_PAIN: [
        "using excel", "using spreadsheets", "spreadsheet",
        "google sheets", "still on paper", "manual entry",
        "paper based", "whiteboard",
    ],
    PainType.MANUAL_PROCESS: [
        "manual process", "manual processes", "too manual",
        "time consuming", "double entry", "data entry",
        "paperwork", "admin overhead",
    ],
    PainType.REPLACING_SOFTWARE: [
        "replace", "replacing", "current system", "current software",
        "switching from", "migrating from", "leaving",
        "not happy with", "frustrated with",
    ],
    PainType.EVALUATING_VENDORS: [
        "evaluating", "comparing", "vs", "versus",
        "alternatives to", "competitors", "looking at",
        "considering", "reviewing options",
    ],
    PainType.HIRING_OPS: [
        "hiring operations", "operations manager", "ops manager",
        "director of operations", "vp operations",
        "hiring ops", "operations hire",
    ],
    PainType.HIRING_PROCESS_IMPROVEMENT: [
        "process improvement", "continuous improvement",
        "six sigma", "lean", "efficiency manager",
        "business process", "process analyst",
    ],
    PainType.DIGITAL_TRANSFORMATION: [
        "digital transformation", "digital strategy",
        "technology roadmap", "modernization",
        "going digital", "digitize",
    ],
    PainType.AI_LOOKING: [
        "need ai", "looking for ai", "ai solution",
        "artificial intelligence", "machine learning",
        "need ml", "ai tool", "ai platform",
    ],
    PainType.ERP_REPLACEMENT: [
        "replacing erp", "new erp", "erp system",
        "enterprise resource", "erp implementation",
        "migrate erp", "erp migration",
    ],
}

SIGNAL_PRIORITY_SCORES: dict[PainType, int] = {
    PainType.REPLACING_SOFTWARE: 90,  # Actively looking to switch
    PainType.EVALUATING_VENDORS: 85,
    PainType.ERP_REPLACEMENT: 85,
    PainType.SOFTWARE_NEED: 75,
    PainType.AI_LOOKING: 70,
    PainType.INSPECTION_SOFTWARE: 80,
    PainType.DISPATCH_SOFTWARE: 80,
    PainType.AUTOMATION_NEED: 75,
    PainType.CRM_NEED: 70,
    PainType.DIGITAL_TRANSFORMATION: 70,
    PainType.HIRING_OPS: 65,
    PainType.HIRING_PROCESS_IMPROVEMENT: 60,
    PainType.MANUAL_PROCESS: 55,
    PainType.SPREADSHEET_PAIN: 55,
    PainType.REPORTING_NEED: 50,
    PainType.SCHEDULING: 45,
    PainType.FIELD_SERVICE: 45,
    PainType.INVENTORY: 40,
    PainType.COMPLIANCE: 40,
    PainType.PAPER_INSPECTIONS: 50,
    PainType.OPERATIONAL_BOTTLENECK: 45,
}

ACTION_BY_SCORE: list[tuple[int, RecommendedAction]] = [
    (85, RecommendedAction.PHONE_CALL),
    (70, RecommendedAction.CREATE_PROPOSAL),
    (60, RecommendedAction.LINKEDIN_MESSAGE),
    (45, RecommendedAction.COLD_EMAIL),
    (30, RecommendedAction.MONITOR),
    (0, RecommendedAction.NOT_QUALIFIED),
]


def classify_signal(raw: RawSignal) -> ClassifiedSignal:
    """AI classifier — runs keyword + pattern matching for instant classification.

    In production, this would use LLM for deeper analysis.
    """
    content_lower = (raw.title + " " + raw.content).lower()

    pain_type = None
    max_matches = 0
    for pt, patterns in BUYING_SIGNAL_PATTERNS.items():
        matches = sum(1 for p in patterns if p in content_lower)
        if matches > max_matches:
            max_matches = matches
            pain_type = pt

    if not pain_type:
        pain_type = PainType.SOFTWARE_NEED

    base_score = SIGNAL_PRIORITY_SCORES.get(pain_type, 40)
    confidence = min(0.95, 0.3 + (max_matches * 0.15))

    # Determine action
    action = RecommendedAction.MONITOR
    for threshold, act in ACTION_BY_SCORE:
        if base_score >= threshold:
            action = act
            break

    return ClassifiedSignal(
        source=raw.source, source_url=raw.source_url,
        title=raw.title, content=raw.content,
        author=raw.author, author_title=raw.author_title,
        company_name=raw.company_name, published_at=raw.published_at,
        location=raw.location,
        pain_type=pain_type, urgency=Urgency.HIGH if base_score >= 70 else Urgency.MEDIUM,
        buying_intent=base_score, lead_score=base_score,
        recommended_action=action, confidence=confidence,
        keywords=[p for p in BUYING_SIGNAL_PATTERNS.get(pain_type, []) if p in content_lower],
        metadata=raw.metadata,
    )
