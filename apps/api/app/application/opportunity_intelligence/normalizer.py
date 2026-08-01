"""
Normalization — standardize values from disparate sources into canonical forms.

Handles budget (string→int), timeline (fuzzy→enum), customer type detection,
stakeholder role classification. Every normalized value carries source + confidence.

Architecture:
    Raw values → Normalizer → TypedValue[T]
"""

from __future__ import annotations

import re
from datetime import datetime, UTC
from decimal import Decimal
from typing import Any

from app.domain.opportunity_intelligence import (
    TypedValue, CustomerType, UrgencyLevel, StakeholderRole,
)


# ═══════════════════════════════════════════════════════════
# BUDGET NORMALIZATION
# ═══════════════════════════════════════════════════════════

def normalize_budget(raw: str | None, source: str = "conversation") -> TypedValue[int]:
    """Normalize budget strings to integer dollar amounts.

    Examples:
        "$40k"     → 40000
        "$40,000"  → 40000
        "40000"    → 40000
        "$1.2M"    → 1200000
        "None"     → TypedValue.empty()
    """
    if not raw or not raw.strip():
        return TypedValue.empty()

    raw = raw.strip()

    # Already clean integer
    if raw.isdigit():
        return TypedValue(value=int(raw), confidence=90, source=source, updated_at=datetime.now(UTC).isoformat())

    # Remove $ and commas
    cleaned = raw.replace("$", "").replace(",", "").replace(" ", "").lower()

    # Clean integer after stripping formatting
    if cleaned.isdigit():
        return TypedValue(value=int(cleaned), confidence=90, source=source, updated_at=datetime.now(UTC).isoformat())

    # Handle "none", "unknown", "not discussed"
    if cleaned in ("none", "unknown", "notdiscussed", "n/a", "na", "tbd", ""):
        return TypedValue.empty()

    # Handle "40k", "40K"
    match = re.match(r"^(\d+\.?\d*)\s*k$", cleaned)
    if match:
        value = int(float(match.group(1)) * 1_000)
        return TypedValue(value=value, confidence=85, source=source, updated_at=datetime.now(UTC).isoformat())

    # Handle "1.2m", "1.2M"
    match = re.match(r"^(\d+\.?\d*)\s*m$", cleaned)
    if match:
        value = int(float(match.group(1)) * 1_000_000)
        return TypedValue(value=value, confidence=85, source=source, updated_at=datetime.now(UTC).isoformat())

    # Handle "1.2mil", "1.2 million"
    match = re.match(r"^(\d+\.?\d*)\s*mil", cleaned)
    if match:
        value = int(float(match.group(1)) * 1_000_000)
        return TypedValue(value=value, confidence=80, source=source, updated_at=datetime.now(UTC).isoformat())

    # Try parsing as float
    try:
        value = int(float(cleaned))
        return TypedValue(value=value, confidence=70, source=source, updated_at=datetime.now(UTC).isoformat())
    except (ValueError, TypeError):
        pass

    # Range: "40-50k"
    match = re.match(r"^(\d+)-(\d+)\s*k$", cleaned)
    if match:
        low = int(match.group(1)) * 1_000
        high = int(match.group(2)) * 1_000
        return TypedValue(value=(low + high) // 2, confidence=70, source=source, updated_at=datetime.now(UTC).isoformat())

    return TypedValue.empty()


# ═══════════════════════════════════════════════════════════
# TIMELINE NORMALIZATION
# ═══════════════════════════════════════════════════════════

TIMELINE_PATTERNS: dict[str, list[str]] = {
    "immediate": ["immediate", "asap", "urgent", "right away", "now", "yesterday"],
    "30_days": ["30 days", "month", "next month", "4 weeks", "within a month"],
    "60_days": ["60 days", "two months", "2 months", "8 weeks"],
    "90_days": ["90 days", "quarter", "next quarter", "3 months", "q", "12 weeks"],
    "180_days": ["6 months", "half year", "six months", "180 days"],
    "this_year": ["this year", "by end of year", "eoy", "within the year"],
    "next_year": ["next year", "next fiscal", "2027", "2028"],
}


def normalize_timeline(raw: str | None, source: str = "conversation") -> TypedValue[str]:
    """Normalize timeline strings to standard categories."""
    if not raw or not raw.strip():
        return TypedValue.empty()

    raw_lower = raw.strip().lower()

    for category, patterns in TIMELINE_PATTERNS.items():
        if any(p in raw_lower for p in patterns):
            return TypedValue(value=category, confidence=80, source=source, updated_at=datetime.now(UTC).isoformat())

    return TypedValue(value=raw_lower, confidence=60, source=source, updated_at=datetime.now(UTC).isoformat())


# ═══════════════════════════════════════════════════════════
# CUSTOMER TYPE DETECTION
# ═══════════════════════════════════════════════════════════

CUSTOMER_TYPE_SIGNALS: dict[CustomerType, list[str]] = {
    CustomerType.OPERATIONAL: [
        "process", "workflow", "manual", "day-to-day", "operation", "efficiency",
        "team", "staff", "field", "dispatch", "inspection", "paperwork",
    ],
    CustomerType.STRATEGIC: [
        "growth", "strategy", "market", "competitive", "scale", "vision",
        "expansion", "direction", "roadmap", "future",
    ],
    CustomerType.FINANCIAL: [
        "budget", "cost", "saving", "investment", "payback", "roi",
        "reduce cost", "expense", "margin", "profit",
    ],
    CustomerType.TECHNICAL: [
        "integration", "api", "system", "architecture", "security",
        "cloud", "database", "infrastructure", "compliance", "data",
    ],
}


def detect_customer_type(texts: list[str]) -> TypedValue[CustomerType]:
    """Detect customer type from conversation text signals."""
    if not texts:
        return TypedValue(value=CustomerType.UNKNOWN, confidence=0, source="", updated_at=datetime.now(UTC).isoformat())

    all_text = " ".join(texts).lower()
    scores: dict[CustomerType, int] = {}

    for ctype, signals in CUSTOMER_TYPE_SIGNALS.items():
        scores[ctype] = sum(1 for s in signals if s in all_text)

    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return TypedValue(value=CustomerType.UNKNOWN, confidence=0, source="", updated_at=datetime.now(UTC).isoformat())

    confidence = min(90, scores[best] * 15)
    return TypedValue(value=best, confidence=confidence, source="conversation", updated_at=datetime.now(UTC).isoformat())


# ═══════════════════════════════════════════════════════════
# URGENCY DETECTION
# ═══════════════════════════════════════════════════════════

URGENCY_SIGNALS: dict[UrgencyLevel, list[str]] = {
    UrgencyLevel.CRITICAL: ["critical", "emergency", "breaking", "losing money", "audit", "deadline"],
    UrgencyLevel.HIGH: ["urgent", "asap", "immediate", "quick", "fast", "soon", "priority"],
    UrgencyLevel.MEDIUM: ["months", "quarter", "planning", "evaluating", "looking"],
    UrgencyLevel.LOW: ["someday", "eventually", "exploring", "just browsing", "no rush"],
}


def detect_urgency(texts: list[str]) -> TypedValue[UrgencyLevel]:
    """Detect urgency level from conversation text signals."""
    if not texts:
        return TypedValue(value=UrgencyLevel.UNKNOWN, confidence=0, source="", updated_at=datetime.now(UTC).isoformat())

    all_text = " ".join(texts).lower()

    for level in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH, UrgencyLevel.MEDIUM, UrgencyLevel.LOW]:
        for signal in URGENCY_SIGNALS[level]:
            if signal in all_text:
                return TypedValue(value=level, confidence=75, source="conversation", updated_at=datetime.now(UTC).isoformat())

    return TypedValue(value=UrgencyLevel.UNKNOWN, confidence=0, source="", updated_at=datetime.now(UTC).isoformat())


# ═══════════════════════════════════════════════════════════
# STAKEHOLDER ROLE CLASSIFICATION
# ═══════════════════════════════════════════════════════════

ROLE_KEYWORDS: dict[StakeholderRole, list[str]] = {
    StakeholderRole.DECISION_MAKER: ["vp", "director", "owner", "president", "ceo", "cfo", "cto", "coo", "chief", "head of"],
    StakeholderRole.CHAMPION: ["manager", "lead", "senior", "advocate"],
    StakeholderRole.TECHNICAL: ["engineer", "developer", "architect", "it", "technical", "systems", "admin"],
    StakeholderRole.FINANCE: ["finance", "accounting", "controller", "cfo", "treasurer", "budget"],
    StakeholderRole.END_USER: ["user", "operator", "technician", "staff", "field", "agent"],
}


def classify_stakeholder_role(title: str, is_decision_maker: bool = False) -> StakeholderRole:
    """Classify stakeholder role from title and DM flag."""
    if is_decision_maker:
        return StakeholderRole.DECISION_MAKER

    title_lower = title.lower() if title else ""

    for role, keywords in ROLE_KEYWORDS.items():
        for kw in keywords:
            if kw in title_lower:
                return role

    return StakeholderRole.OTHER
