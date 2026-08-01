"""
Sprint 47.7 — Public Automation Assessment API

POST /api/public/automation-assessment
Accepts website assessment submissions. Creates CRM records transactionally.
Supports idempotency via Idempotency-Key header.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, UTC
from typing import Any

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.orm import Session

from app.application.assessment.service import submit_assessment
from app.infrastructure.db.session import get_db_session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/public", tags=["public"])


# ── Request schemas ──

class ContactSchema(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=120)
    last_name: str = Field(..., min_length=1, max_length=120)
    email: str = Field(..., min_length=3, max_length=255)
    phone: str | None = Field(None, max_length=50)
    role: str | None = Field(None, max_length=255)


class CompanySchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    website: str | None = Field(None, max_length=255)
    industry: str = Field("Other", max_length=120)
    employee_range: str | None = Field(None, max_length=50)
    location: str | None = Field(None, max_length=255)


class ConsentSchema(BaseModel):
    privacy_accepted: bool = False
    marketing_accepted: bool = False
    accepted_at: str | None = None


class AttributionSchema(BaseModel):
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    utm_term: str | None = None
    utm_content: str | None = None
    referrer: str | None = None
    landing_page: str | None = None


class AssessmentSubmission(BaseModel):
    assessment_version: str = Field(default="1.0", min_length=1, max_length=20)
    answers: dict[str, Any] = Field(default_factory=dict)
    results: dict[str, Any] = Field(default_factory=dict)
    contact: ContactSchema
    company: CompanySchema
    consent: ConsentSchema | None = None
    attribution: AttributionSchema | None = None


class AssessmentResponse(BaseModel):
    submission_id: str
    assessment_id: str
    status: str
    automation_score: int
    estimated_hours_saved: int
    estimated_annual_savings: int
    primary_pain_points: list
    recommended_solutions: list
    report_status: str
    booking_url: str


# ── Rate limiting (simple in-memory) ──
_rate_limit_store: dict[str, list[float]] = {}
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 10     # requests per window

def _check_rate_limit(client_ip: str) -> bool:
    now = datetime.now(UTC).timestamp()
    if client_ip not in _rate_limit_store:
        _rate_limit_store[client_ip] = []
    _rate_limit_store[client_ip] = [t for t in _rate_limit_store[client_ip] if now - t < RATE_LIMIT_WINDOW]
    if len(_rate_limit_store[client_ip]) >= RATE_LIMIT_MAX:
        return False
    _rate_limit_store[client_ip].append(now)
    return True


# ── Routes ──

@router.post("/automation-assessment", response_model=AssessmentResponse)
async def submit_automation_assessment(
    request: Request,
    body: AssessmentSubmission,
):
    """Public endpoint for website automation assessment submissions.
    
    Accepts assessment data from the marketing website. Creates or reuses
    Company, Contact, Lead records. Stores raw answers and calculated results.
    Returns public-safe response with no internal IDs.
    
    Supports idempotency via Idempotency-Key header.
    """
    # ── Rate limiting ──
    client_ip = request.client.host if request.client else "unknown"
    if not _check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
    
    # ── Idempotency key ──
    idempotency_key = request.headers.get("Idempotency-Key") or request.headers.get("idempotency-key")
    
    # ── Correlation ID ──
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    
    # ── Validate request size ──
    body_str = await request.body()
    if len(body_str) > 100_000:  # 100KB max
        raise HTTPException(status_code=413, detail="Request body too large")
    
    # ── Get DB session ──
    db: Session = next(get_db_session())
    
    try:
        # ── Build results dict from either new format (results) or old format (flat) ──
        answers = body.answers
        results = body.results if body.results else answers.get("results", {})
        
        # Support old marketing format: flat fields
        if not answers:
            answers = body.model_dump(exclude={"contact", "company", "consent", "attribution", "assessment_version", "results"})
        
        response = submit_assessment(
            session=db,
            assessment_version=body.assessment_version,
            answers=answers,
            contact_data=body.contact.model_dump(),
            company_data=body.company.model_dump(),
            results=results,
            consent=body.consent.model_dump() if body.consent else None,
            attribution=body.attribution.model_dump() if body.attribution else None,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        
        return AssessmentResponse(**response)
    
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.exception("Assessment submission failed: correlation_id=%s", correlation_id)
        raise HTTPException(status_code=500, detail="An error occurred processing your assessment. Please try again.")
    finally:
        db.close()
