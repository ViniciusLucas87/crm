"""
Sprint 47.9 — Assessment Detail API

GET /api/v1/assessments/{public_uuid}
Returns full assessment with intelligence for CRM display.
"""
from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

from app.infrastructure.db.models import AutomationAssessment
from app.infrastructure.db.session import get_db_session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/assessments", tags=["assessments"])


@router.get("/{public_uuid}")
def get_assessment(public_uuid: str):
    """Get full assessment detail including intelligence (Sprint 47.9)."""
    db: Session = get_db_session()
    try:
        assessment = db.query(AutomationAssessment).filter(
            AutomationAssessment.public_id == public_uuid,
        ).first()

        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")

        intelligence = assessment.intelligence_json or {}

        return {
            "id": assessment.public_id,
            "status": "completed",
            "created_at": assessment.created_at.isoformat() if assessment.created_at else None,

            # Company & Contact
            "company_id": assessment.company_id,
            "contact_id": assessment.contact_id,
            "lead_id": assessment.lead_id,

            # Scores
            "automation_score": assessment.automation_score,
            "score_interpretation": intelligence.get("score_interpretation", ""),

            # Raw answers
            "raw_answers": assessment.raw_answers or {},
            "industry": assessment.industry,
            "employee_range": assessment.employee_range,

            # Calculated outputs
            "estimated_weekly_hours": assessment.estimated_weekly_hours,
            "estimated_annual_hours": assessment.estimated_annual_hours,
            "estimated_annual_savings": assessment.estimated_annual_savings,
            "estimated_people_count": assessment.estimated_people_count,
            "calculated_output": assessment.calculated_output or {},

            # Intelligence (Sprint 47.9)
            "primary_pain_point": assessment.primary_pain_point,
            "secondary_pain_points": assessment.secondary_pain_points or [],
            "current_process_summary": assessment.current_process_summary,
            "root_cause": assessment.root_cause,
            "business_impact": assessment.business_impact,
            "recommended_solution_categories": assessment.recommended_solution_categories or [],
            "recommendation_reasons": assessment.recommendation_reasons or [],
            "urgency": assessment.urgency,
            "buying_signals": assessment.buying_signals or [],
            "likely_decision_maker": assessment.likely_decision_maker,
            "project_size_band": assessment.project_size_band,
            "next_best_action": assessment.next_best_action,
            "discovery_questions": assessment.discovery_questions or [],
            "intelligence_version": assessment.intelligence_version,
            "intelligence_confidence": float(assessment.intelligence_confidence) if assessment.intelligence_confidence else None,

            # PDF & Email
            "pdf_status": assessment.pdf_status,
            "email_status": "delivered",

            # Metadata
            "assessment_version": assessment.assessment_version,
            "scoring_model_version": assessment.scoring_model_version,
            "correlation_id": assessment.correlation_id,
        }
    finally:
        db.close()


@router.get("/by-lead/{lead_id}")
def get_assessment_by_lead(lead_id: int):
    """Get the most recent assessment for a lead (for the Lead page intelligence card)."""
    db: Session = get_db_session()
    try:
        assessment = db.query(AutomationAssessment).filter(
            AutomationAssessment.lead_id == lead_id,
        ).order_by(AutomationAssessment.created_at.desc()).first()

        if not assessment:
            raise HTTPException(status_code=404, detail="No assessment found for this lead")

        return {
            "id": assessment.public_id,
            "automation_score": assessment.automation_score,
            "primary_pain_point": assessment.primary_pain_point,
            "estimated_annual_savings": assessment.estimated_annual_savings,
            "estimated_weekly_hours": assessment.estimated_weekly_hours,
            "recommended_solution_categories": assessment.recommended_solution_categories or [],
            "urgency": assessment.urgency,
            "next_best_action": assessment.next_best_action,
            "current_process_summary": assessment.current_process_summary,
            "discovery_questions": assessment.discovery_questions or [],
            "likely_decision_maker": assessment.likely_decision_maker,
            "project_size_band": assessment.project_size_band,
        }
    finally:
        db.close()
