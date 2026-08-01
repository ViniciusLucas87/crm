"""
Pacific North Systems ICP (Ideal Customer Profile) Scoring Engine.

Evaluates leads against PNS's specific business profile to determine
fit probability — NOT just opportunity size.

Key factors:
  - Company size (10-150 ideal)
  - Decision accessibility (owner/founder)
  - Industry match
  - Technology maturity (low = better)
  - Manual processes
  - Procurement complexity
  - Geographic proximity to Vancouver
  - Estimated sales cycle
"""

from dataclasses import dataclass, field


# ── ICP Configuration ──

IDEAL_EMPLOYEES = (10, 150)
ACCEPTABLE_EMPLOYEES = (150, 300)
LOWER_PRIORITY_EMPLOYEES = (300, 500)

HIGH_PRIORITY_INDUSTRIES = [
    "construction", "property management", "restoration", "hvac",
    "electrical", "plumbing", "engineering", "manufacturing",
    "marine", "facilities management", "field service",
    "inspection", "marine services",
]
MEDIUM_PRIORITY_INDUSTRIES = [
    "architecture", "logistics", "professional services",
]

DECISION_MAKER_TITLES = [
    "owner", "president", "managing director", "operations manager",
    "general manager", "managing partner", "facilities manager",
    "property manager", "construction manager",
]

PNS_SERVICES = [
    "custom software development", "ai automation",
    "workflow automation", "internal business systems",
    "inspection software", "dashboards", "custom crm",
    "reporting systems", "document ai", "integrations",
    "it consulting", "it support",
]

TARGET_GEOGRAPHY = [
    "vancouver", "burnaby", "richmond", "north vancouver",
    "west vancouver", "surrey", "coquitlam", "langley",
    "delta", "maple ridge", "british columbia", "bc",
    "metro vancouver", "lower mainland",
]


@dataclass
class ICPScore:
    """PNS Ideal Customer Profile fit score."""

    pns_fit_score: int = 50  # 0-100
    factors: list[dict] = field(default_factory=list)
    sales_difficulty: str = "moderate"  # very_easy, easy, moderate, difficult, enterprise
    estimated_sales_cycle: str = "3 months"
    recommended_first_project: str = ""
    outreach_strategy: dict = field(default_factory=dict)
    why_pns: list[str] = field(default_factory=list)
    risk_factors: list[str] = field(default_factory=list)


class ICPEngine:
    """Scores leads against Pacific North Systems' ICP."""

    def score(self, lead: dict) -> ICPScore:
        """Score a lead against PNS ICP. `lead` is a dict with company fields."""
        score = ICPScore()
        factors: list[dict] = []

        industry = str(lead.get("industry", "")).lower()
        city = str(lead.get("city", "")).lower()
        province = str(lead.get("province", "")).lower()
        employees = lead.get("employees")
        tech_maturity = str(lead.get("technology_maturity", "")).lower()
        description = str(lead.get("description", "")).lower()
        buying_signals = str(lead.get("buying_signals", "")).lower()
        exec_summary = str(lead.get("executive_summary", "")).lower()
        combined_text = f"{description} {buying_signals} {exec_summary}"

        # 1. Company Size (max 25 pts)
        if employees and IDEAL_EMPLOYEES[0] <= employees <= IDEAL_EMPLOYEES[1]:
            factors.append({"factor": "Ideal company size", "points": 25, "detail": f"{employees} employees — fast decisions, founder access likely"})
        elif employees and ACCEPTABLE_EMPLOYEES[0] <= employees <= ACCEPTABLE_EMPLOYEES[1]:
            factors.append({"factor": "Acceptable company size", "points": 18, "detail": f"{employees} employees — reasonable procurement timeline"})
        elif employees and LOWER_PRIORITY_EMPLOYEES[0] <= employees <= LOWER_PRIORITY_EMPLOYEES[1]:
            factors.append({"factor": "Larger organization", "points": 8, "detail": f"{employees} employees — slower decisions, more stakeholders"})
        elif employees and employees > 500:
            factors.append({"factor": "Enterprise scale", "points": 2, "detail": f"{employees} employees — procurement complexity, long sales cycles"})
        else:
            factors.append({"factor": "Unknown size", "points": 10, "detail": "Employee count unknown — moderate fit"})

        # 2. Industry Match (max 20 pts)
        if any(ind in industry for ind in HIGH_PRIORITY_INDUSTRIES):
            factors.append({"factor": "High-priority industry", "points": 20, "detail": f"{lead.get('industry', '')} is a core PNS target industry"})
        elif any(ind in industry for ind in MEDIUM_PRIORITY_INDUSTRIES):
            factors.append({"factor": "Medium-priority industry", "points": 12, "detail": f"{lead.get('industry', '')} is a secondary PNS target"})
        else:
            factors.append({"factor": "Non-core industry", "points": 4, "detail": f"{lead.get('industry', '')} is not a primary PNS focus"})

        # 3. Geographic Proximity (max 15 pts)
        location_text = f"{city} {province}"
        if any(geo in location_text for geo in TARGET_GEOGRAPHY):
            factors.append({"factor": "Local to Vancouver metro", "points": 15, "detail": f"Located in {city or province} — PNS's primary service area"})
        elif "british columbia" in province or "bc" in province:
            factors.append({"factor": "British Columbia", "points": 10, "detail": "In BC — accessible but may require travel"})
        else:
            factors.append({"factor": "Outside BC", "points": 3, "detail": f"Located in {city or province} — remote engagement only"})

        # 4. Technology Gap / Manual Processes (max 15 pts)
        manual_keywords = ["excel", "spreadsheet", "paper", "manual", "email workflow", "whatsapp", "shared folder", "basic", "legacy", "outdated", "no software", "google sheets"]
        manual_matches = [k for k in manual_keywords if k in combined_text]
        if manual_matches:
            factors.append({"factor": "Manual/outdated processes detected", "points": 15, "detail": f"Keywords: {', '.join(manual_matches[:4])} — high automation opportunity"})
        elif "medium" in tech_maturity or "low" in tech_maturity:
            factors.append({"factor": "Technology gap present", "points": 10, "detail": "Technology maturity indicated as medium/low"})
        else:
            factors.append({"factor": "Technology maturity unclear", "points": 5, "detail": "May have existing technology solutions"})

        # 5. Decision Accessibility (max 15 pts)
        owner_keywords = ["owner", "founder", "president", "managing director", "small team", "family", "independent"]
        owner_matches = [k for k in owner_keywords if k in combined_text]
        if employees and employees <= 150:
            factors.append({"factor": "Likely owner/founder accessible", "points": 15, "detail": "Small organization — decisions made quickly by leadership"})
        elif owner_matches:
            factors.append({"factor": "Decision maker accessible", "points": 12, "detail": "Owner/founder involvement indicated in company description"})
        elif employees and employees <= 300:
            factors.append({"factor": "Reasonable access", "points": 8, "detail": "Mid-size — may have dedicated management but still accessible"})
        else:
            factors.append({"factor": "Complex procurement likely", "points": 3, "detail": "Large organization — multi-stakeholder purchasing"})

        # 6. Project Size Fit (max 10 pts)
        deal_low = lead.get("estimated_deal_low")
        if deal_low and 3000 <= deal_low <= 20000:
            factors.append({"factor": "Ideal first engagement size", "points": 10, "detail": f"${deal_low:,} — perfect entry project for PNS"})
        elif deal_low and 20000 <= deal_low <= 100000:
            factors.append({"factor": "Good expansion opportunity", "points": 7, "detail": f"${deal_low:,} — manageable project with growth potential"})
        elif deal_low and deal_low > 100000:
            factors.append({"factor": "Large project — higher risk", "points": 3, "detail": f"${deal_low:,} — may exceed PNS's typical first engagement"})
        else:
            factors.append({"factor": "Project size unclear", "points": 5, "detail": "Deal size not estimated"})

        # Compute total
        total = sum(f["points"] for f in factors)
        score.pns_fit_score = min(100, total)
        score.factors = factors

        # Derive sales difficulty
        if score.pns_fit_score >= 80:
            score.sales_difficulty = "very_easy"
            score.estimated_sales_cycle = "2 weeks"
        elif score.pns_fit_score >= 65:
            score.sales_difficulty = "easy"
            score.estimated_sales_cycle = "1 month"
        elif score.pns_fit_score >= 45:
            score.sales_difficulty = "moderate"
            score.estimated_sales_cycle = "3 months"
        elif score.pns_fit_score >= 25:
            score.sales_difficulty = "difficult"
            score.estimated_sales_cycle = "6 months"
        else:
            score.sales_difficulty = "enterprise"
            score.estimated_sales_cycle = "12+ months"

        # Why PNS
        why: list[str] = []
        for f in factors:
            if f["points"] >= 15:
                why.append(f"✓ {f['detail']}")
        if not why:
            why = ["Requires further research to identify specific fit factors."]
        score.why_pns = why

        # Risk factors
        risks: list[str] = []
        for f in factors:
            if f["points"] <= 3:
                risks.append(f"⚠ {f['detail']}")
        if not risks:
            risks = ["No significant risk factors identified."]
        score.risk_factors = risks

        return score


def score_lead_icp(lead_data: dict) -> dict:
    """Convenience function: score a lead and return dict."""
    engine = ICPEngine()
    result = engine.score(lead_data)
    return {
        "pns_fit_score": result.pns_fit_score,
        "factors": result.factors,
        "sales_difficulty": result.sales_difficulty,
        "estimated_sales_cycle": result.estimated_sales_cycle,
        "why_pns": result.why_pns,
        "risk_factors": result.risk_factors,
    }
