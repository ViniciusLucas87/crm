"""
Sprint 47.5 — Rapport Intelligence Engine

Generates rapport-building suggestions from:
- Company location, industry, news
- Contact role, previous conversations
- Local context (weather, business events — when available)
- Never fabricates facts. Every suggestion includes source and freshness.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC, timedelta
from typing import Any


@dataclass
class RapportSuggestion:
    """A rapport-building opener with source traceability."""
    topic: str                                # e.g., "local_weather", "industry_trend", "company_milestone"
    suggested_opener: str                     # Exact wording
    transition: str                           # How to transition to business
    source: str                               # Where this came from
    fetched_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    expires_at: str = ""                      
    confidence: int = 70
    is_fresh: bool = True
    
    def to_dict(self) -> dict:
        return {
            "topic": self.topic,
            "suggested_opener": self.suggested_opener,
            "transition": self.transition,
            "source": self.source,
            "fetched_at": self.fetched_at,
            "expires_at": self.expires_at,
            "confidence": self.confidence,
            "is_fresh": self.is_fresh,
        }


class RapportIntelligenceEngine:
    """Generates rapport opportunities from available context.
    
    Safety rules:
    - Never invent sports results, weather, or company announcements
    - Never surface personal/sensitive information
    - Prefer professional context (company, role, industry, location)
    - Only use live context when fresh and verifiable
    """
    
    # ── Industry-specific rapport angles ──
    INDUSTRY_ANGLES = {
        "construction": {
            "topics": [
                "field-to-office communication",
                "inspection and compliance workflow",
                "subcontractor coordination",
                "weather impact on scheduling",
                "project documentation handoff",
                "safety reporting requirements",
            ],
            "openers": {
                "field_communication": "How do your field teams currently communicate job status back to the office?",
                "compliance": "What do your compliance and inspection processes look like on a typical project?",
                "weather": "Has the recent weather affected any of your active projects?",
                "scheduling": "How do you handle scheduling when site conditions change unexpectedly?",
            },
        },
        "property_management": {
            "topics": [
                "tenant communication workflow",
                "maintenance request handling",
                "inspection scheduling",
                "vendor management",
                "lease renewal tracking",
            ],
            "openers": {
                "maintenance": "How do you currently handle maintenance requests from tenants?",
                "inspections": "What does your inspection and reporting process look like?",
                "vendors": "How do you coordinate with external vendors and contractors?",
            },
        },
        "tourism": {
            "topics": [
                "booking management",
                "seasonal staffing",
                "guest communication",
                "activity scheduling",
            ],
            "openers": {
                "booking": "How do you manage bookings across different channels?",
                "seasonal": "How does your operation change between peak and off-peak seasons?",
            },
        },
        "field_services": {
            "topics": [
                "dispatch and routing",
                "job documentation",
                "customer communication",
                "inventory and parts management",
            ],
            "openers": {
                "dispatch": "How do you currently schedule and dispatch your field teams?",
                "documentation": "What does your field technician's paperwork look like after a job?",
            },
        },
        "logistics": {
            "topics": [
                "shipment tracking",
                "driver communication",
                "delivery confirmation",
                "route optimization",
            ],
            "openers": {
                "tracking": "How do you currently track shipments from dispatch to delivery?",
                "communication": "How do drivers and dispatchers stay in sync during the day?",
            },
        },
        "manufacturing": {
            "topics": [
                "production scheduling",
                "quality control workflow",
                "inventory management",
                "supplier coordination",
            ],
            "openers": {
                "production": "How do you currently manage production scheduling and changeovers?",
                "quality": "What does your quality control and reporting process look like?",
            },
        },
    }
    
    # ── Role-specific rapport angles ──
    ROLE_ANGLES = {
        "operations": {
            "focus": ["workflow efficiency", "team coordination", "process bottlenecks"],
            "opener": "What's been the biggest operational challenge for your team recently?",
        },
        "owner": {
            "focus": ["business growth", "cost control", "strategic priorities"],
            "opener": "What's top of mind for the business right now?",
        },
        "manager": {
            "focus": ["team performance", "reporting needs", "daily workflow"],
            "opener": "How does your team currently handle [process] on a typical day?",
        },
        "director": {
            "focus": ["department goals", "resource allocation", "process improvement"],
            "opener": "What initiatives is your department focused on this quarter?",
        },
        "vp": {
            "focus": ["strategic alignment", "cross-department coordination", "ROI"],
            "opener": "How does this fit into your broader strategic priorities?",
        },
        "c-level": {
            "focus": ["business outcomes", "competitive position", "organizational impact"],
            "opener": "What's driving the priority to address this now?",
        },
    }
    
    # ── Location context (static, for known locations) ──
    LOCATION_CONTEXT = {
        "vancouver": {
            "note": "Vancouver, BC — construction, tech, film, tourism industries. Rainy climate affects outdoor work.",
            "themes": ["rain impact on field work", "real estate density", "port and logistics", "tech talent market"],
        },
        "surrey": {
            "note": "Surrey, BC — rapid growth, construction, industrial, diverse business base.",
            "themes": ["construction growth", "industrial development", "transportation infrastructure"],
        },
        "burnaby": {
            "note": "Burnaby, BC — tech hub, Metrotown commercial centre, industrial parks.",
            "themes": ["tech corridor", "industrial operations", "commercial growth"],
        },
        "richmond": {
            "note": "Richmond, BC — logistics hub, YVR airport, manufacturing, Asian business community.",
            "themes": ["logistics and freight", "manufacturing", "import/export"],
        },
        "kelowna": {
            "note": "Kelowna, BC — tourism, agriculture, construction, tech growth.",
            "themes": ["seasonal business", "agriculture tech", "construction boom"],
        },
        "victoria": {
            "note": "Victoria, BC — government, tech, tourism, marine industries.",
            "themes": ["government procurement", "marine industry", "tech sector growth"],
        },
    }
    
    def __init__(self):
        self._company_context: dict = {}
        self._contact_context: dict = {}
        self._live_providers: dict = {}  # Plug-in live context providers
        self._previous_suggestions: list[str] = []
    
    def set_company_context(self, ctx: dict):
        """Set company context for industry/location-specific rapport."""
        self._company_context = ctx
    
    def set_contact_context(self, ctx: dict):
        """Set contact context for role-specific rapport."""
        self._contact_context = ctx
    
    def register_live_provider(self, name: str, provider):
        """Register a live context provider (weather, sports, events, etc.)."""
        self._live_providers[name] = provider
    
    def generate_opener(self, skip_small_talk: bool = False) -> RapportSuggestion | None:
        """Generate the best rapport opener for the current context."""
        
        if skip_small_talk:
            return RapportSuggestion(
                topic="skip_rapport",
                suggested_opener="I know your time is limited, so I'll keep this focused.",
                transition="Let me share what I'd like to cover today.",
                source="time_sensitivity",
                confidence=90,
            )
        
        # 1. Try live context first (weather, events, news)
        live = self._try_live_context()
        if live:
            return live
        
        # 2. Try industry-specific opener
        industry = self._company_context.get("industry", "").lower()
        if industry in self.INDUSTRY_ANGLES:
            return self._industry_opener(industry)
        
        # 3. Try location-based context
        location = self._company_context.get("location", self._company_context.get("city", "")).lower()
        if location in self.LOCATION_CONTEXT:
            return self._location_opener(location)
        
        # 4. Try role-based
        role = self._contact_context.get("role", "").lower()
        for role_key, angle in self.ROLE_ANGLES.items():
            if role_key in role:
                return RapportSuggestion(
                    topic=f"role_{role_key}",
                    suggested_opener=angle["opener"],
                    transition="That helps me understand where to focus today.",
                    source=f"contact_role: {role}",
                    confidence=70,
                )
        
        # 5. Generic professional opener
        return RapportSuggestion(
            topic="professional_opening",
            suggested_opener="Thanks for taking the time today. I've been looking forward to understanding your operation better.",
            transition="Could you tell me a bit about your role and what prompted today's conversation?",
            source="professional_default",
            confidence=65,
        )
    
    def generate_transition(self, from_stage: str, to_stage: str) -> str:
        """Generate a natural transition between conversation stages."""
        transitions = {
            ("opening", "rapport"): "Before we get into the details, I'd love to understand a bit about how business has been for your team.",
            ("rapport", "discovery"): "That gives me useful context. Could you walk me through how that process works today?",
            ("discovery", "pain_points"): "That's helpful. Where does that process create the most delay or frustration?",
            ("pain_points", "current_process"): "Let me make sure I understand the full workflow. What happens after that step?",
            ("current_process", "budget"): "Now that I understand the process, have you thought about what solving this would be worth?",
            ("budget", "timeline"): "And in terms of timing — what's driving the urgency on your end?",
            ("timeline", "decision_maker"): "One more thing — besides yourself, who else would need to be involved?",
            ("decision_maker", "solution"): "Based on everything you've shared, I think there's a real opportunity here.",
            ("solution", "closing"): "The next useful step would be to map this workflow and show you a practical example.",
        }
        key = (from_stage, to_stage)
        if key in transitions:
            return transitions[key]
        return f"That's helpful context. Let me ask about the next piece."
    
    def _try_live_context(self) -> RapportSuggestion | None:
        """Try live context providers. Returns None if none available/fresh."""
        for name, provider in self._live_providers.items():
            try:
                suggestion = provider.get_suggestion(self._company_context, self._contact_context)
                if suggestion and self._is_fresh(suggestion):
                    return suggestion
            except Exception:
                continue
        return None
    
    def _is_fresh(self, suggestion: RapportSuggestion) -> bool:
        """Check if a live suggestion is still fresh."""
        if not suggestion.expires_at:
            return True
        try:
            expires = datetime.fromisoformat(suggestion.expires_at)
            return datetime.now(UTC) < expires
        except (ValueError, TypeError):
            return True
    
    def _industry_opener(self, industry: str) -> RapportSuggestion | None:
        """Generate an industry-specific opener."""
        angles = self.INDUSTRY_ANGLES.get(industry)
        if not angles:
            return None
        
        # Pick the most relevant topic for the contact role
        openers = angles.get("openers", {})
        # Default to first available
        for key, opener in openers.items():
            return RapportSuggestion(
                topic=f"industry_{industry}_{key}",
                suggested_opener=opener,
                transition="That helps me understand where to focus today.",
                source=f"industry: {industry}",
                confidence=75,
            )
        return None
    
    def _location_opener(self, location: str) -> RapportSuggestion | None:
        """Generate a location-based opener."""
        ctx = self.LOCATION_CONTEXT.get(location)
        if not ctx:
            return None
        
        industry = self._company_context.get("industry", "").lower()
        # Tailor to industry if possible
        if industry == "construction" and "rain" in str(ctx.get("themes", [])):
            return RapportSuggestion(
                topic="local_weather_construction",
                suggested_opener="I know the weather in the Lower Mainland can be unpredictable for field work. Has it affected your scheduling recently?",
                transition="That's helpful context for understanding your operational rhythm.",
                source=f"location: {location}",
                confidence=72,
            )
        
        return RapportSuggestion(
            topic=f"location_{location}",
            suggested_opener=f"I know the {location.title()} area has been growing rapidly. How has that affected your business?",
            transition="That's interesting context. Let me share what I'd like to cover today.",
            source=f"location: {location}",
            confidence=68,
        )
