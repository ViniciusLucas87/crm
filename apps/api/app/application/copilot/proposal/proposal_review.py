"""
Proposal Review Engine — evaluates proposal quality across 8 categories.

Produces overall score, strengths, weaknesses, recommendations, and
ready-to-send determination.
"""

from __future__ import annotations

from datetime import datetime, UTC

from app.application.copilot.proposal.models import (
    Proposal, ProposalReview, ReviewCategory,
    BusinessAnalysis, SolutionArchitecture, ROIReport,
    ScopeAssessment, RiskAssessment, ImplementationRoadmap,
)


REVIEW_CATEGORIES = [
    "business_understanding",
    "solution_fit",
    "roi_quality",
    "implementation_plan",
    "scope_accuracy",
    "risk_coverage",
    "completeness",
    "professional_quality",
]


class ProposalReviewEngine:
    """Evaluates proposal quality and readiness.

    Scores eight categories. Provides actionable recommendations.
    Determines if proposal is ready to send.
    """

    def review(
        self,
        proposal: Proposal,
        business: BusinessAnalysis | None = None,
        architecture: SolutionArchitecture | None = None,
        roi: ROIReport | None = None,
        scope: ScopeAssessment | None = None,
        risks: RiskAssessment | None = None,
        roadmap: ImplementationRoadmap | None = None,
    ) -> ProposalReview:
        categories: list[ReviewCategory] = []

        # ── Business Understanding ──
        bu_score = self._score_business_understanding(business)
        categories.append(ReviewCategory(
            name="Business Understanding",
            score=bu_score,
            comment="Well-articulated business context and challenges" if bu_score >= 70
            else "Business context could be strengthened with more specific operational details",
        ))

        # ── Solution Fit ──
        sf_score = self._score_solution_fit(architecture)
        categories.append(ReviewCategory(
            name="Solution Fit",
            score=sf_score,
            comment="Solution components directly address identified challenges" if sf_score >= 70
            else "Solution alignment with business needs could be stronger",
        ))

        # ── ROI Quality ──
        roi_score = self._score_roi(roi)
        categories.append(ReviewCategory(
            name="ROI Quality",
            score=roi_score,
            comment="ROI calculations are transparent with clear assumptions" if roi_score >= 70
            else "ROI could benefit from more detailed assumptions and calculations",
        ))

        # ── Implementation Plan ──
        impl_score = self._score_implementation(roadmap)
        categories.append(ReviewCategory(
            name="Implementation Plan",
            score=impl_score,
            comment="Phased approach with clear deliverables and dependencies" if impl_score >= 70
            else "Implementation plan needs more detail on phases and dependencies",
        ))

        # ── Scope Accuracy ──
        sc_score = self._score_scope(scope)
        categories.append(ReviewCategory(
            name="Scope Accuracy",
            score=sc_score,
            comment="Scope assessment aligns with organizational complexity" if sc_score >= 70
            else "Scope may need recalibration based on organizational factors",
        ))

        # ── Risk Coverage ──
        rk_score = self._score_risks(risks)
        categories.append(ReviewCategory(
            name="Risk Coverage",
            score=rk_score,
            comment="Comprehensive risk assessment with clear mitigations" if rk_score >= 70
            else "Risk assessment could cover additional categories",
        ))

        # ── Completeness ──
        comp_score = self._score_completeness(proposal, business, architecture, roi, scope, risks, roadmap)
        categories.append(ReviewCategory(
            name="Completeness",
            score=comp_score,
            comment="All proposal sections present and populated" if comp_score >= 70
            else "Some proposal sections are missing or incomplete",
        ))

        # ── Professional Quality ──
        pq_score = self._score_professional_quality(proposal)
        categories.append(ReviewCategory(
            name="Professional Quality",
            score=pq_score,
            comment="Proposal meets professional consulting standards" if pq_score >= 70
            else "Proposal quality could be improved for client presentation",
        ))

        # ── Aggregate ──
        scores = [c.score for c in categories]
        overall = int(sum(scores) / len(scores)) if scores else 0

        strengths = [c.name for c in categories if c.score >= 70]
        weaknesses = [c.name for c in categories if c.score < 50]
        recommendations = [
            f"Strengthen {w.lower()}" for w in weaknesses
        ]
        missing = proposal.missing_information if proposal.missing_information else []
        ready = overall >= 70 and len(weaknesses) <= 1

        return ProposalReview(
            categories=categories,
            overall_score=overall,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations if recommendations else ["Proposal meets quality standards."],
            missing_information=missing,
            ready_to_send=ready,
        )

    def _score_business_understanding(self, ba: BusinessAnalysis | None) -> int:
        if not ba:
            return 0
        score = 30
        if ba.executive_summary and len(ba.executive_summary) > 100:
            score += 20
        if ba.operational_challenges:
            score += 20
        if ba.business_risks:
            score += 15
        if ba.business_opportunities:
            score += 15
        return min(100, score)

    def _score_solution_fit(self, arch: SolutionArchitecture | None) -> int:
        if not arch:
            return 0
        score = 20
        if arch.current_workflow:
            score += 20
        if arch.future_workflow:
            score += 25
        if arch.components:
            score += min(35, len(arch.components) * 15)
        return min(100, score)

    def _score_roi(self, roi: ROIReport | None) -> int:
        if not roi:
            return 0
        score = 30
        if roi.estimated_annual_savings > 0:
            score += 20
        if roi.assumptions and len(roi.assumptions) >= 3:
            score += 25
        if roi.estimated_payback_months > 0:
            score += 15
        if roi.hours_saved_per_week > 0:
            score += 10
        return min(100, score)

    def _score_implementation(self, roadmap: ImplementationRoadmap | None) -> int:
        if not roadmap:
            return 0
        score = 20
        if len(roadmap.phases) >= 5:
            score += 30
        if roadmap.total_duration:
            score += 20
        if all(p.deliverables for p in roadmap.phases):
            score += 30
        return min(100, score)

    def _score_scope(self, scope: ScopeAssessment | None) -> int:
        if not scope:
            return 0
        return scope.confidence

    def _score_risks(self, risks: RiskAssessment | None) -> int:
        if not risks:
            return 0
        score = 30
        if len(risks.risks) >= 3:
            score += 30
        if all(r.mitigation for r in risks.risks):
            score += 40
        return min(100, score)

    def _score_completeness(
        self, proposal, business, architecture, roi, scope, risks, roadmap,
    ) -> int:
        parts = [business, architecture, roi, scope, risks, roadmap]
        present = sum(1 for p in parts if p is not None)
        return int((present / len(parts)) * 100)

    def _score_professional_quality(self, proposal: Proposal) -> int:
        score = 30
        if proposal.title:
            score += 10
        if proposal.company_name:
            score += 10
        if proposal.sections and len(proposal.sections) >= 5:
            score += 25
        if proposal.generated_at:
            score += 10
        if proposal.quality_score >= 60:
            score += 15
        return min(100, score)


# Singleton
_engine: ProposalReviewEngine | None = None


def get_proposal_review_engine() -> ProposalReviewEngine:
    global _engine
    if _engine is None:
        _engine = ProposalReviewEngine()
    return _engine
