"""
Opportunity Intelligence Builder — aggregates and normalizes data from all sources.

Inputs:
    - ConversationInsights (from Decision Engine)
    - Company (from CRM)
    - Contacts (from CRM)
    - Activities (from CRM)
    - Opportunities (from CRM)
    - Proposals (from Proposal Studio)

Output:
    - OpportunityIntelligence (canonical business object)

Rules:
    - Latest verified information wins
    - History preserved in timeline
    - No duplication
    - Every field carries confidence + source
"""

from __future__ import annotations

import logging
from datetime import datetime, UTC
from typing import Any

from app.domain.opportunity_intelligence import (
    OpportunityIntelligence, OpportunityStage, OpportunityStatus,
    TypedValue, Stakeholder, StakeholderRole, BusinessContext, SalesContext,
    SolutionContext, TimelineEvent, EventType, CustomerType, UrgencyLevel,
    STAGE_TRANSITIONS, create_empty_intelligence,
)
from app.application.transcription.intelligence import ConversationInsight, InsightCategory
from app.application.opportunity_intelligence.normalizer import (
    normalize_budget, normalize_timeline, detect_customer_type,
    detect_urgency, classify_stakeholder_role,
)

logger = logging.getLogger(__name__)


class OpportunityIntelligenceBuilder:
    """Builds canonical OpportunityIntelligence from all data sources.

    Merges ConversationInsights with CRM data. Never duplicates.
    Latest verified information wins. Historical information preserved.
    """

    def build(
        self,
        insights: list[ConversationInsight] | None = None,
        company: dict[str, Any] | None = None,
        contacts: list[dict[str, Any]] | None = None,
        activities: list[dict[str, Any]] | None = None,
        opportunity: dict[str, Any] | None = None,
        proposals: list[dict[str, Any]] | None = None,
        previous_intelligence: OpportunityIntelligence | None = None,
    ) -> OpportunityIntelligence:
        """Build complete OpportunityIntelligence from all sources.

        Args:
            insights: ConversationInsights from Decision Engine
            company: Company dict from CRM
            contacts: Contact dicts from CRM
            activities: Activity dicts from CRM
            opportunity: Opportunity dict from CRM
            proposals: Proposal dicts from Proposal Studio
            previous_intelligence: Previous build for history preservation
        """
        insights = insights or []
        company = company or {}
        contacts = contacts or []
        activities = activities or []
        opportunity = opportunity or {}
        proposals = proposals or []
        now = datetime.now(UTC).isoformat()

        # ── Initialize ──
        oi = create_empty_intelligence(
            opportunity_id=opportunity.get("id"),
            company_id=company.get("id"),
            organization_id=company.get("organization_id"),
        )
        oi.updated_at = now
        oi.last_updated = now

        # ── Categorize insights ──
        by_category: dict[InsightCategory, list[ConversationInsight]] = {}
        for ins in insights:
            by_category.setdefault(ins.category, []).append(ins)

        all_insight_text = [i.value for i in insights]

        # ── Stage ──
        oi.stage = self._determine_stage(opportunity, by_category)

        # ── Status ──
        oi.status = self._determine_status(opportunity)

        # ── Scores ──
        oi.opportunity_score = self._extract_score(opportunity, "opportunity_score")
        oi.deal_health = self._extract_score(opportunity, "health_score")

        # ── Company ──
        oi.company_name = company.get("name", "")
        oi.company_industry = company.get("industry", "")
        oi.company_employees = company.get("employees")
        oi.company_website = company.get("website", "")
        if company.get("revenue"):
            try:
                oi.company_revenue = float(company["revenue"])
            except (TypeError, ValueError):
                pass

        # Parse locations from company
        loc_parts = []
        for f in ["city", "province", "country"]:
            v = company.get(f)
            if v:
                loc_parts.append(str(v))
        if loc_parts:
            oi.company_locations = [", ".join(loc_parts)]

        # ── Stakeholders ──
        oi.stakeholders = self._build_stakeholders(contacts, by_category)

        # ── Business Context ──
        oi.business = self._build_business_context(by_category, company)

        # ── Sales Context ──
        oi.sales = self._build_sales_context(by_category, all_insight_text)

        # ── Solutions ──
        oi.solutions = self._build_solution_context(proposals)

        # ── Timeline ──
        oi.timeline = self._build_timeline(insights, activities, proposals, previous_intelligence)

        # ── Metadata ──
        oi.insight_count = len(insights)
        oi.activity_count = len(activities)
        oi.proposal_count = len(proposals)
        oi.source_count = (1 if company else 0) + len(contacts) + len(activities) + len(proposals)
        oi.confidence = self._compute_confidence(oi)

        # ── Discovery score ──
        oi.discovery_score = self._compute_discovery_score(oi)

        # ── Proposal readiness ──
        oi.proposal_readiness = self._compute_proposal_readiness(oi)

        # ── Merge with previous ──
        if previous_intelligence:
            oi = self._merge_history(oi, previous_intelligence)

        return oi

    # ═══════════════════════════════════════════════════════
    # STAGE & STATUS
    # ═══════════════════════════════════════════════════════

    def _determine_stage(self, opportunity, by_category) -> OpportunityStage:
        """Determine current stage from opportunity + insights."""
        stage_str = opportunity.get("stage", "")

        # If stage is explicitly set to something other than "lead", use it
        if stage_str and stage_str != "lead":
            try:
                return OpportunityStage(stage_str)
            except ValueError:
                pass

        # Infer from insights (fallback for "lead" or empty stage)
        has_budget = InsightCategory.BUDGET in by_category
        has_dm = InsightCategory.DECISION_MAKER in by_category
        has_pain = InsightCategory.PAIN_POINT in by_category
        has_goals = InsightCategory.GOAL in by_category

        if not has_pain and not has_goals:
            return OpportunityStage.LEAD
        if has_pain and not has_dm:
            return OpportunityStage.QUALIFIED if has_pain else OpportunityStage.LEAD
        if has_dm and has_budget:
            return OpportunityStage.PROPOSAL if has_goals else OpportunityStage.SOLUTION_DESIGN
        if has_pain and has_dm:
            return OpportunityStage.DISCOVERY
        return OpportunityStage.LEAD

    def _determine_status(self, opportunity) -> OpportunityStatus:
        status_str = opportunity.get("status", "active")
        try:
            return OpportunityStatus(status_str)
        except ValueError:
            return OpportunityStatus.ACTIVE

    # ═══════════════════════════════════════════════════════
    # SCORES
    # ═══════════════════════════════════════════════════════

    def _extract_score(self, data, key) -> TypedValue[int]:
        val = data.get(key)
        if val is not None:
            try:
                return TypedValue(value=int(val), confidence=90, source="crm", updated_at=datetime.now(UTC).isoformat())
            except (ValueError, TypeError):
                pass
        return TypedValue.empty()

    # ═══════════════════════════════════════════════════════
    # STAKEHOLDERS
    # ═══════════════════════════════════════════════════════

    def _build_stakeholders(self, contacts, by_category) -> list[Stakeholder]:
        stakeholders: list[Stakeholder] = []

        for c in contacts:
            role = classify_stakeholder_role(
                c.get("job_title", ""),
                is_decision_maker=bool(c.get("is_decision_maker", False)),
            )
            stakeholders.append(Stakeholder(
                id=c.get("id"),
                name=f"{c.get('first_name', '')} {c.get('last_name', '')}".strip(),
                title=c.get("job_title", ""),
                email=c.get("email", ""),
                phone=c.get("phone") or c.get("mobile", ""),
                role=role,
                is_primary=bool(c.get("is_primary", False)),
                confidence=90,
                source="crm",
            ))

        # Add decision makers discovered in conversation
        dm_insights = by_category.get(InsightCategory.DECISION_MAKER, [])
        existing_names = {s.name.lower() for s in stakeholders}
        for ins in dm_insights:
            if ins.value.lower() not in existing_names:
                stakeholders.append(Stakeholder(
                    name=ins.value,
                    role=StakeholderRole.DECISION_MAKER,
                    confidence=ins.confidence,
                    source="conversation",
                ))

        return stakeholders

    # ═══════════════════════════════════════════════════════
    # BUSINESS CONTEXT
    # ═══════════════════════════════════════════════════════

    def _build_business_context(self, by_category, company) -> BusinessContext:
        ctx = BusinessContext()

        # Current process
        ctx.current_process = [
            TypedValue(value=i.value, confidence=i.confidence, source="conversation", updated_at=datetime.now(UTC).isoformat())
            for i in by_category.get(InsightCategory.CURRENT_PROCESS, [])
        ]

        # Current software
        ctx.current_software = [
            TypedValue(value=i.value, confidence=i.confidence, source="conversation", updated_at=datetime.now(UTC).isoformat())
            for i in by_category.get(InsightCategory.CURRENT_SOFTWARE, [])
        ]

        # Goals
        ctx.business_goals = [
            TypedValue(value=i.value, confidence=i.confidence, source="conversation", updated_at=datetime.now(UTC).isoformat())
            for i in by_category.get(InsightCategory.GOAL, [])
        ]

        # Pain points
        ctx.pain_points = [
            TypedValue(value=i.value, confidence=i.confidence, source="conversation", updated_at=datetime.now(UTC).isoformat())
            for i in by_category.get(InsightCategory.PAIN_POINT, [])
        ]

        # Manual work indicators
        manual_keywords = ["manual", "paper", "spreadsheet", "double entry", "duplicate", "handwritten"]
        ctx.manual_work_indicators = [
            i.value for i in by_category.get(InsightCategory.PAIN_POINT, [])
            if any(kw in i.value.lower() for kw in manual_keywords)
        ]

        # Risks
        ctx.operational_risks = [
            TypedValue(value=i.value, confidence=i.confidence, source="conversation", updated_at=datetime.now(UTC).isoformat())
            for i in by_category.get(InsightCategory.RISK, [])
        ]

        # Constraints
        ctx.constraints = [
            TypedValue(value=i.value, confidence=i.confidence, source="conversation", updated_at=datetime.now(UTC).isoformat())
            for i in by_category.get(InsightCategory.CONSTRAINT, [])
        ]

        # Compliance
        ctx.compliance_requirements = [
            TypedValue(value=i.value, confidence=i.confidence, source="conversation", updated_at=datetime.now(UTC).isoformat())
            for i in by_category.get(InsightCategory.COMPLIANCE, [])
        ]

        # Budget
        budget_ins = by_category.get(InsightCategory.BUDGET, [])
        if budget_ins:
            ctx.budget_raw = budget_ins[0].value
            ctx.budget = normalize_budget(budget_ins[0].value)

        # Timeline
        timeline_ins = by_category.get(InsightCategory.TIMELINE, [])
        if timeline_ins:
            ctx.timeline = normalize_timeline(timeline_ins[0].value)

        return ctx

    # ═══════════════════════════════════════════════════════
    # SALES CONTEXT
    # ═══════════════════════════════════════════════════════

    def _build_sales_context(self, by_category, all_text) -> SalesContext:
        ctx = SalesContext()

        ctx.buying_signals = [
            TypedValue(value=i.value, confidence=i.confidence, source="conversation", updated_at=datetime.now(UTC).isoformat())
            for i in by_category.get(InsightCategory.BUYING_SIGNAL, [])
        ]

        ctx.objections = [
            TypedValue(value=i.value, confidence=i.confidence, source="conversation", updated_at=datetime.now(UTC).isoformat())
            for i in by_category.get(InsightCategory.OBJECTION, [])
        ]

        ctx.urgency = detect_urgency(all_text)
        ctx.customer_type = detect_customer_type(all_text)

        return ctx

    # ═══════════════════════════════════════════════════════
    # SOLUTIONS
    # ═══════════════════════════════════════════════════════

    def _build_solution_context(self, proposals) -> SolutionContext:
        ctx = SolutionContext()

        if proposals:
            latest = proposals[-1]
            ctx.proposal_status = "generated"
            ctx.proposal_quality = latest.get("quality_score", 0)
            ctx.recommended_products = latest.get("solution_components", [])
            ctx.estimated_roi = latest.get("roi_analysis", "")
            ctx.estimated_complexity = "medium"

        return ctx

    # ═══════════════════════════════════════════════════════
    # TIMELINE
    # ═══════════════════════════════════════════════════════

    def _build_timeline(
        self,
        insights,
        activities,
        proposals,
        previous,
    ) -> list[TimelineEvent]:
        events: list[TimelineEvent] = []

        # Carry forward existing timeline
        if previous and previous.timeline:
            events.extend(previous.timeline)

        # Add insight-derived events
        for ins in insights:
            if ins.category == InsightCategory.PAIN_POINT:
                events.append(TimelineEvent(
                    event_type=EventType.PAIN_POINT_DISCOVERED,
                    description=f"Pain point: {ins.value}",
                    timestamp=ins.timestamp or datetime.now(UTC).isoformat(),
                    source="conversation",
                ))
            elif ins.category == InsightCategory.BUDGET:
                events.append(TimelineEvent(
                    event_type=EventType.BUDGET_IDENTIFIED,
                    description=f"Budget identified: {ins.value}",
                    timestamp=ins.timestamp or datetime.now(UTC).isoformat(),
                    source="conversation",
                ))
            elif ins.category == InsightCategory.DECISION_MAKER:
                events.append(TimelineEvent(
                    event_type=EventType.DECISION_MAKER_IDENTIFIED,
                    description=f"Decision maker: {ins.value}",
                    timestamp=ins.timestamp or datetime.now(UTC).isoformat(),
                    source="conversation",
                ))

        # Activities
        for act in activities:
            act_type = act.get("activity_type", "").lower()
            event_type = EventType.CALL if "call" in act_type else (
                EventType.EMAIL if "email" in act_type else (
                    EventType.MEETING if "meeting" in act_type else EventType.ACTIVITY
                )
            )
            events.append(TimelineEvent(
                event_type=event_type,
                description=act.get("subject", act.get("body", ""))[:200],
                timestamp=act.get("created_at", datetime.now(UTC).isoformat()),
                source="crm",
            ))

        # Proposals
        for prop in proposals:
            events.append(TimelineEvent(
                event_type=EventType.PROPOSAL_GENERATED,
                description=f"Proposal: {prop.get('title', '')}",
                timestamp=prop.get("generated_at", datetime.now(UTC).isoformat()),
                source="proposal_studio",
            ))

        # Sort and deduplicate
        events.sort(key=lambda e: e.timestamp, reverse=True)
        seen = set()
        unique: list[TimelineEvent] = []
        for e in events:
            key = (e.event_type.value, e.description[:80], e.timestamp[:19])
            if key not in seen:
                seen.add(key)
                unique.append(e)

        return unique

    # ═══════════════════════════════════════════════════════
    # SCORES
    # ═══════════════════════════════════════════════════════

    def _compute_confidence(self, oi: OpportunityIntelligence) -> int:
        """Overall confidence based on data completeness."""
        score = 0
        if oi.company_name:
            score += 15
        if oi.company_industry:
            score += 10
        if oi.stakeholders:
            score += 15
        if oi.business.pain_points:
            score += 15
        if oi.business.budget.is_known():
            score += 10
        if oi.business.timeline.is_known():
            score += 10
        if oi.sales.buying_signals:
            score += 10
        if oi.solutions.proposal_status != "none":
            score += 10
        if oi.timeline:
            score += 5
        return min(100, score)

    def _compute_discovery_score(self, oi: OpportunityIntelligence) -> TypedValue[int]:
        """Discovery completeness score."""
        fields = [
            bool(oi.company_name),
            bool(oi.company_industry),
            bool(oi.company_employees),
            bool(oi.business.current_process),
            bool(oi.business.current_software),
            bool(oi.business.pain_points),
            bool(oi.business.business_goals),
            bool(oi.stakeholders),
            oi.business.budget.is_known(),
            oi.business.timeline.is_known(),
        ]
        pct = int((sum(1 for f in fields if f) / len(fields)) * 100)
        return TypedValue(value=pct, confidence=80, source="builder", updated_at=datetime.now(UTC).isoformat())

    def _compute_proposal_readiness(self, oi: OpportunityIntelligence) -> TypedValue[int]:
        """Proposal readiness score."""
        score = 0
        if oi.business.pain_points:
            score += 30
        if oi.business.budget.is_known():
            score += 20
        if oi.business.timeline.is_known():
            score += 15
        if oi.stakeholders:
            score += 15
        if oi.business.business_goals:
            score += 10
        if oi.business.current_software:
            score += 10
        return TypedValue(value=min(100, score), confidence=80, source="builder", updated_at=datetime.now(UTC).isoformat())

    def _merge_history(
        self,
        new: OpportunityIntelligence,
        old: OpportunityIntelligence,
    ) -> OpportunityIntelligence:
        """Merge with previous: latest verified wins, history preserved."""
        # Preserve older values if new is empty
        if not new.company_name and old.company_name:
            new.company_name = old.company_name
        if not new.company_industry and old.company_industry:
            new.company_industry = old.company_industry

        # Merge stakeholders: new ones + existing not overwritten
        existing_ids = {s.id for s in new.stakeholders if s.id}
        for s in old.stakeholders:
            if s.id and s.id not in existing_ids:
                new.stakeholders.append(s)
                existing_ids.add(s.id)

        # Carry forward timeline
        old_keys = {(e.event_type.value, e.description[:80], e.timestamp[:19]) for e in new.timeline}
        for e in old.timeline:
            key = (e.event_type.value, e.description[:80], e.timestamp[:19])
            if key not in old_keys:
                new.timeline.append(e)

        new.timeline.sort(key=lambda e: e.timestamp, reverse=True)

        return new


# Singleton
_builder: OpportunityIntelligenceBuilder | None = None


def get_opportunity_intelligence_builder() -> OpportunityIntelligenceBuilder:
    global _builder
    if _builder is None:
        _builder = OpportunityIntelligenceBuilder()
    return _builder
