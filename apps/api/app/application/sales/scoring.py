"""
Explainable Opportunity Scoring Engine.

Every company receives a score (0-100), confidence level,
score breakdown, recommended services, estimated value,
and suggested next action. The user always understands WHY.

Architecture:
    ScoringEngine → RuleEvaluator → OpportunityCalculator
                 → ConfidenceCalculator → RecommendationEngine
                 → ValueEstimator
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.infrastructure.db.models import Activity, Company, Contact, Opportunity


# ── Rule Definition ──

class ScoringRule(BaseModel):
    id: str
    category: str  # "industry", "size", "technology", "growth", "digital_presence", "signals"
    description: str
    points: int  # positive or negative
    condition_field: str  # e.g. "industry", "employees", "website"
    condition_op: str  # "eq", "gt", "lt", "contains", "missing", "present", "one_of"
    condition_value: Any = None


# ── Configurable Rule Set ──

POSITIVE_RULES: list[ScoringRule] = [
    # Industry signals
    ScoringRule(id="ind_construction", category="industry", description="Construction Industry", points=15, condition_field="industry", condition_op="contains", condition_value="construction"),
    ScoringRule(id="ind_property", category="industry", description="Property Management", points=15, condition_field="industry", condition_op="contains", condition_value="property"),
    ScoringRule(id="ind_engineering", category="industry", description="Engineering Firm", points=14, condition_field="industry", condition_op="contains", condition_value="engineering"),
    ScoringRule(id="ind_manufacturing", category="industry", description="Manufacturing", points=13, condition_field="industry", condition_op="contains", condition_value="manufacturing"),
    ScoringRule(id="ind_architecture", category="industry", description="Architecture", points=12, condition_field="industry", condition_op="contains", condition_value="architecture"),
    # Size signals
    ScoringRule(id="size_20_100", category="size", description="20-100 Employees", points=12, condition_field="employees", condition_op="between", condition_value=[20, 100]),
    ScoringRule(id="size_100_500", category="size", description="100-500 Employees", points=8, condition_field="employees", condition_op="between", condition_value=[100, 500]),
    ScoringRule(id="size_large", category="size", description="Large Workforce", points=5, condition_field="employees", condition_op="gt", condition_value=500),
    # Website/tech signals
    ScoringRule(id="web_outdated", category="technology", description="Website Present", points=3, condition_field="website", condition_op="present"),
    # Growth signals
    ScoringRule(id="growth_multiloc", category="growth", description="Multiple Locations", points=10, condition_field="locations", condition_op="present"),
    # Digital presence
    ScoringRule(id="digi_linkedin", category="digital_presence", description="LinkedIn Profile", points=5, condition_field="linkedin_url", condition_op="present"),
    ScoringRule(id="digi_active", category="digital_presence", description="Digital Presence", points=3, condition_field="website", condition_op="present"),
    # Contact signals
    ScoringRule(id="contact_present", category="signals", description="Has Contacts", points=5, condition_field="_has_contacts", condition_op="eq", condition_value=True),
    # Recent activity
    ScoringRule(id="act_recent", category="signals", description="Recent Activity (7d)", points=10, condition_field="_has_recent_activity", condition_op="eq", condition_value=True),
]

NEGATIVE_RULES: list[ScoringRule] = [
    ScoringRule(id="neg_small", category="size", description="Very Small Company (<3)", points=-10, condition_field="employees", condition_op="lt", condition_value=3),
    ScoringRule(id="neg_no_web", category="technology", description="No Website", points=-3, condition_field="website", condition_op="missing"),
]


# ── Confidence Calculator ──

class ConfidenceCalculator:
    FIELDS = ["description", "industry", "employees", "website", "tech_stack", "linkedin_url", "city"]

    @staticmethod
    def calculate(company: Company) -> tuple[int, str, list[str]]:
        present = [f for f in ConfidenceCalculator.FIELDS if getattr(company, f, None)]
        ratio = len(present) / len(ConfidenceCalculator.FIELDS)
        score = int(ratio * 100)

        if score >= 80:
            level = "High"
            detail = "Company data is well-researched."
        elif score >= 50:
            level = "Medium"
            detail = "Some information is missing."
        else:
            level = "Low"
            detail = "Limited public information available."

        missing = [f for f in ConfidenceCalculator.FIELDS if not getattr(company, f, None)]
        reasons = [f"✓ {f}" for f in present] + [f"✗ {f}" for f in missing]
        return score, level, [detail] + reasons[:6]


# ── Rule Evaluator ──

class RuleEvaluator:
    @staticmethod
    def evaluate_rule(rule: ScoringRule, company: Company, extras: dict[str, Any]) -> bool:
        if rule.condition_field.startswith("_"):
            return extras.get(rule.condition_field) == rule.condition_value
        val = getattr(company, rule.condition_field, None)
        if rule.condition_op == "present":
            return val is not None and val != ""
        if rule.condition_op == "missing":
            return val is None or val == ""
        if rule.condition_op == "contains":
            return val is not None and rule.condition_value.lower() in str(val).lower()
        if rule.condition_op == "eq":
            return val == rule.condition_value
        if rule.condition_op == "gt":
            return val is not None and val > rule.condition_value
        if rule.condition_op == "lt":
            return val is not None and val < rule.condition_value
        if rule.condition_op == "between":
            low, high = rule.condition_value
            return val is not None and low <= val <= high
        return False


# ── Value Estimator ──

class ValueEstimator:
    @staticmethod
    def estimate(opportunity_score: int, employees: int | None) -> dict[str, Any]:
        if opportunity_score >= 75:
            tier, range_str = "Enterprise", "CAD $60,000–$150,000+"
        elif opportunity_score >= 55:
            tier, range_str = "Large", "CAD $20,000–$60,000"
        elif opportunity_score >= 40:
            tier, range_str = "Medium", "CAD $8,000–$20,000"
        else:
            tier, range_str = "Small", "CAD $3,000–$8,000"
        return {"tier": tier, "range": range_str, "confidence": "estimated"}


# ── Service Recommender ──

SERVICE_CATALOG = {
    "construction": ["Inspection Platform", "Field Service Software", "Operations Dashboard"],
    "property": ["Client Portal", "Scheduling Platform", "Document Automation"],
    "engineering": ["Custom CRM", "AI Document Processing", "Workflow Automation"],
    "manufacturing": ["Inventory Management", "Maintenance Management", "Operations Dashboard"],
    "architecture": ["Client Portal", "Document Automation", "Mobile Workforce App"],
    "default": ["Custom CRM", "Client Portal", "Workflow Automation", "Reporting System"],
}


class RecommendationEngine:
    @staticmethod
    def recommend(company: Company, score: int, signals: list[str]) -> dict[str, Any]:
        industry_lower = (company.industry or "").lower()
        services: list[str] = []
        for kw, svcs in SERVICE_CATALOG.items():
            if kw in industry_lower:
                services = svcs
                break
        if not services:
            services = SERVICE_CATALOG["default"]

        # Add based on signals
        if "No Client Portal" in str(signals) or company.employees and company.employees > 50:
            if "Client Portal" not in services:
                services.append("Client Portal")
        if company.employees and company.employees > 100:
            if "Business Intelligence" not in services:
                services.append("Business Intelligence")

        return {"services": services[:5], "reason": f"Based on {company.industry or 'company'} profile and {len(signals)} detected signals"}


# ── Next Action Engine ──

class NextActionEngine:
    @staticmethod
    def suggest(score: int, has_contacts: bool, has_recent_activity: bool, signals: list[str]) -> str:
        if not has_contacts:
            return "Add a decision maker contact."
        if not has_recent_activity:
            return "Schedule a discovery call."
        if score >= 70:
            return "Prepare a proposal."
        if score >= 50:
            return "Send a relevant case study."
        return "Research this company further."


# ── Main Scoring Engine ──

class ScoreBreakdown(BaseModel):
    rule_id: str
    category: str
    description: str
    points: int


class OpportunityScoreResult(BaseModel):
    company_id: int
    company_name: str
    opportunity_score: int
    confidence_score: int
    confidence_level: str
    confidence_detail: list[str]
    score_breakdown: list[ScoreBreakdown]
    recommended_services: list[str]
    service_reason: str
    estimated_value: dict[str, Any]
    next_action: str


class ScoringEngine:
    def __init__(self, session: Session) -> None:
        self._session = session

    def score_company(self, company: Company) -> OpportunityScoreResult:
        # Compute extras
        contact_count = self._session.execute(
            select(func.count(Contact.id)).where(Contact.company_id == company.id)
        ).scalar_one()
        recent = self._session.execute(
            select(func.max(Activity.created_at)).where(Activity.company_id == company.id)
        ).scalar_one_or_none()
        recent_7d = recent is not None and recent > datetime.now(timezone.utc) - timedelta(days=7)
        extras = {"_has_contacts": contact_count > 0, "_has_recent_activity": recent_7d}

        # Evaluate all rules
        breakdown: list[ScoreBreakdown] = []
        total = 0

        for rule in POSITIVE_RULES:
            if RuleEvaluator.evaluate_rule(rule, company, extras):
                breakdown.append(ScoreBreakdown(rule_id=rule.id, category=rule.category, description=f"+{rule.points} {rule.description}", points=rule.points))
                total += rule.points
        for rule in NEGATIVE_RULES:
            if RuleEvaluator.evaluate_rule(rule, company, extras):
                breakdown.append(ScoreBreakdown(rule_id=rule.id, category=rule.category, description=f"{rule.points} {rule.description}", points=rule.points))
                total += rule.points

        total = max(0, min(100, total + 50))  # Base 50 + rules

        # Confidence
        conf_score, conf_level, conf_detail = ConfidenceCalculator.calculate(company)

        # Services
        svc = RecommendationEngine.recommend(company, total, [b.description for b in breakdown])

        # Value
        value = ValueEstimator.estimate(total, company.employees)

        # Next action
        action = NextActionEngine.suggest(total, contact_count > 0, recent_7d, [b.description for b in breakdown])

        # Persist
        company.opportunity_score = total
        company.confidence_score = conf_score
        self._session.add(company)
        self._session.commit()

        return OpportunityScoreResult(
            company_id=company.id,
            company_name=company.name,
            opportunity_score=total,
            confidence_score=conf_score,
            confidence_level=conf_level,
            confidence_detail=conf_detail,
            score_breakdown=breakdown,
            recommended_services=svc["services"],
            service_reason=svc["reason"],
            estimated_value=value,
            next_action=action,
        )
