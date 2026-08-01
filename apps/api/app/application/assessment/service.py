"""
Sprint 47.7 — Submit Automation Assessment Service

Transactional pipeline: validate → resolve entities → create/update CRM records →
store assessment → create activity + task → write outbox events → commit.

Never creates partial CRM records. All-or-nothing transaction.
"""
from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import datetime, UTC
from typing import Any

from sqlalchemy.orm import Session

from app.infrastructure.db.models import (
    Company, Contact, Lead, AutomationAssessment, OutboxEvent, Activity, Task,
)

logger = logging.getLogger(__name__)

# Default organization for public submissions
DEFAULT_ORG_ID = 1


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _map_results(results: dict) -> dict:
    """Normalize results from either camelCase (marketing) or snake_case."""
    return {
        "opportunityScore": results.get("opportunityScore", results.get("opportunity_score", 0)),
        "estimatedWeeklyHours": results.get("estimatedWeeklyHours", results.get("estimated_weekly_hours", 0)),
        "estimatedAnnualHours": results.get("estimatedAnnualHours", results.get("estimated_annual_hours", 0)),
        "estimatedAnnualLabourCost": results.get("estimatedAnnualLabourCost", results.get("estimated_annual_labour_cost", 0)),
        "estimatedAnnualSavings": results.get("estimatedAnnualSavings", results.get("estimated_annual_savings", 0)),
        "scoreInterpretation": results.get("scoreInterpretation", results.get("score_interpretation", "")),
        "recommended_solutions": results.get("recommended_solutions", results.get("recommendedSolutions", [])),
    }


def _normalize_company_name(name: str) -> str:
    return " ".join(name.strip().lower().split())


def _derive_domain(email: str | None, website: str | None) -> str | None:
    """Derive a normalized domain for company matching."""
    if email and "@" in email:
        domain = email.split("@")[1].lower()
        if domain not in ("gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com", "protonmail.com"):
            return domain
    if website:
        from urllib.parse import urlparse
        parsed = urlparse(website if "://" in website else f"https://{website}")
        domain = parsed.netloc or parsed.path
        domain = domain.lower().replace("www.", "").split("/")[0]
        if domain:
            return domain
    return None


def _compute_fingerprint(email: str, company_name: str, version: str, answers: dict) -> str:
    """Compute a deterministic assessment fingerprint."""
    raw = f"{_normalize_email(email)}|{_normalize_company_name(company_name)}|{version}|{json.dumps(answers, sort_keys=True)}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _resolve_company(session: Session, company_data: dict, email: str | None) -> Company | None:
    """Find or create a company. Returns existing match or None if creation needed."""
    name = company_data.get("name", "")
    website = company_data.get("website", "")
    domain = _derive_domain(email, website)
    
    # 1. Try website domain match
    if domain:
        existing = session.query(Company).filter(
            Company.organization_id == DEFAULT_ORG_ID,
            Company.website.ilike(f"%{domain}%"),
            Company.is_archived == False,
        ).first()
        if existing:
            return existing
    
    # 2. Try email domain match
    if email and "@" in email:
        email_domain = email.split("@")[1]
        existing = session.query(Company).filter(
            Company.organization_id == DEFAULT_ORG_ID,
            Company.website.ilike(f"%{email_domain}%"),
            Company.is_archived == False,
        ).first()
        if existing:
            return existing
    
    # 3. Try normalized name match
    if name:
        normalized = _normalize_company_name(name)
        existing = session.query(Company).filter(
            Company.organization_id == DEFAULT_ORG_ID,
            Company.is_archived == False,
        ).filter(Company.name.ilike(normalized)).first()
        if existing:
            return existing
    
    return None


def _resolve_contact(session: Session, contact_data: dict, company_id: int | None) -> Contact | None:
    """Find existing contact by email or phone."""
    email = contact_data.get("email", "")
    phone = contact_data.get("phone", "")
    
    if email:
        existing = session.query(Contact).filter(
            Contact.organization_id == DEFAULT_ORG_ID,
            Contact.email == _normalize_email(email),
            Contact.status == "active",
        ).first()
        if existing:
            return existing
    
    if phone and company_id:
        existing = session.query(Contact).filter(
            Contact.organization_id == DEFAULT_ORG_ID,
            Contact.company_id == company_id,
            Contact.phone == phone,
            Contact.status == "active",
        ).first()
        if existing:
            return existing
    
    return None


def _resolve_lead(session: Session, contact_id: int | None, company_id: int | None) -> Lead | None:
    """Find active lead for this contact + company."""
    if contact_id and company_id:
        existing = session.query(Lead).filter(
            Lead.organization_id == DEFAULT_ORG_ID,
            Lead.imported_company_id == company_id,
            Lead.status.in_(["new", "qualified", "contacted"]),
        ).first()
        if existing:
            return existing
    return None


def _calculate_lead_score(assessment_data: dict, results: dict) -> dict:
    """Calculate lead priority and score."""
    score = 0
    reasons = []
    
    savings = results.get("estimated_annual_savings", 0)
    if savings > 50000:
        score += 25
        reasons.append("Estimated savings above $50,000")
    elif savings > 20000:
        score += 15
        reasons.append("Estimated savings above $20,000")
    elif savings > 0:
        score += 8
        reasons.append("Positive savings estimate")
    
    score_val = results.get("opportunityScore", results.get("automation_score", 0))
    if score_val >= 80:
        score += 20
        reasons.append("High automation opportunity")
    elif score_val >= 60:
        score += 12
        reasons.append("Moderate automation opportunity")
    elif score_val >= 40:
        score += 6
        reasons.append("Some automation opportunity")
    
    people = assessment_data.get("peopleInvolved", "")
    if people in ("16-50", "50+"):
        score += 12
        reasons.append("High number of people affected")
    elif people in ("6-15",):
        score += 8
        reasons.append("Multiple people affected")
    
    weekly_time = assessment_data.get("weeklyTimeSpent", "")
    if weekly_time in ("More than 40 hours", "20–40 hours"):
        score += 10
        reasons.append("Significant weekly time investment")
    elif weekly_time in ("10–20 hours",):
        score += 6
        reasons.append("Moderate weekly time investment")
    
    industry = assessment_data.get("businessType", "")
    target_industries = ["Construction / Trades", "Property Management", "Manufacturing", "Tourism / Transportation"]
    if industry in target_industries:
        score += 10
        reasons.append("Target industry")
    
    priority = "high" if score >= 70 else "medium" if score >= 40 else "low"
    
    return {
        "priority": priority,
        "score": min(score, 100),
        "reasons": reasons,
        "score_version": "1.0",
    }


def submit_assessment(
    session: Session,
    assessment_version: str,
    answers: dict,
    contact_data: dict,
    company_data: dict,
    results: dict,
    consent: dict | None = None,
    attribution: dict | None = None,
    idempotency_key: str | None = None,
    correlation_id: str | None = None,
) -> dict:
    """Main transaction: validate, resolve, persist, emit outbox events.
    
    All-or-nothing. Rolls back on any failure.
    Returns public-safe response dict.
    """
    correlation_id = correlation_id or str(uuid.uuid4())
    
    # ── Normalize results ──
    results = _map_results(results)
    fingerprint = _compute_fingerprint(
        contact_data.get("email", ""),
        company_data.get("name", ""),
        assessment_version,
        answers,
    )
    
    if idempotency_key:
        existing = session.query(AutomationAssessment).filter(
            AutomationAssessment.idempotency_key == idempotency_key,
        ).first()
        if existing:
            # Policy A: same key, different hash → 409 conflict
            if existing.assessment_fingerprint != fingerprint:
                logger.warning("Idempotency key conflict: key=%s existing_fingerprint=%s new_fingerprint=%s",
                               idempotency_key, existing.assessment_fingerprint, fingerprint)
                from fastapi import HTTPException
                raise HTTPException(status_code=409, detail="Idempotency key conflict: different payload submitted with same key.")
            logger.info("Idempotent replay: key=%s fingerprint match", idempotency_key)
            return _build_public_response(existing, status="ok")
    
    # Check fingerprint for duplicate
    existing = session.query(AutomationAssessment).filter(
        AutomationAssessment.assessment_fingerprint == fingerprint,
    ).order_by(AutomationAssessment.created_at.desc()).first()
    if existing:
        logger.info("Duplicate assessment detected via fingerprint")
        return _build_public_response(existing)
    
    # ── Resolve/ create Company ──
    company = _resolve_company(session, company_data, contact_data.get("email"))
    company_created = False
    if not company:
        company = Company(
            organization_id=DEFAULT_ORG_ID,
            name=company_data.get("name", "Unknown Company"),
            website=company_data.get("website"),
            industry=company_data.get("industry"),
            business_type=answers.get("businessType"),
            city=company_data.get("location"),
            status="active",
        )
        session.add(company)
        session.flush()
        company_created = True
        logger.info("Created company: id=%s name=%s", company.id, company.name)
    else:
        # Update existing company if new info available
        if company_data.get("industry") and not company.industry:
            company.industry = company_data["industry"]
        if company_data.get("website") and not company.website:
            company.website = company_data["website"]
    
    # ── Resolve/ create Contact ──
    contact = _resolve_contact(session, contact_data, company.id)
    contact_created = False
    if not contact:
        contact = Contact(
            organization_id=DEFAULT_ORG_ID,
            company_id=company.id,
            first_name=contact_data.get("first_name", ""),
            last_name=contact_data.get("last_name", ""),
            email=_normalize_email(contact_data.get("email", "")),
            phone=contact_data.get("phone"),
            job_title=contact_data.get("role"),
            discovery_source="website_assessment",
            status="active",
        )
        session.add(contact)
        session.flush()
        contact_created = True
        logger.info("Created contact: id=%s email=%s", contact.id, contact.email)
    
    # ── Resolve/ create Lead ──
    lead = _resolve_lead(session, contact.id, company.id)
    lead_created = False
    lead_updated = False
    
    if not lead:
        lead_score = _calculate_lead_score(answers, results)
        lead = Lead(
            organization_id=DEFAULT_ORG_ID,
            name=company.name,
            industry=company_data.get("industry"),
            website=company_data.get("website"),
            city=company_data.get("location"),
            opportunity_score=results.get("opportunityScore", 0),
            status=lead_score["priority"],
            source="website_assessment",
            imported_company_id=company.id,
            estimated_value=str(results.get("estimated_annual_savings", 0)),
            notes=f"Website automation assessment. Score: {results.get('opportunityScore', 0)}. Savings: ${results.get('estimated_annual_savings', 0):,}/yr.",
        )
        session.add(lead)
        session.flush()
        lead_created = True
        logger.info("Created lead: id=%s priority=%s score=%s", lead.id, lead_score["priority"], lead_score["score"])
    else:
        # Update existing lead
        lead_score = _calculate_lead_score(answers, results)
        lead.opportunity_score = max(lead.opportunity_score or 0, results.get("opportunityScore", 0))
        lead.status = lead_score["priority"] if lead_score["priority"] == "high" and lead.status != "high" else lead.status
        lead.notes = (lead.notes or "") + f"\nUpdated assessment: {datetime.now(UTC).isoformat()}. Score: {results.get('opportunityScore', 0)}."
        session.flush()
        lead_updated = True
        logger.info("Updated existing lead: id=%s", lead.id)
    
    # ── Generate Assessment Intelligence (Sprint 47.9) ──
    from app.application.assessment.intelligence import generate_intelligence
    intelligence = generate_intelligence(answers, results, company_data, contact_data)
    
    # ── Create Assessment ──
    assessment = AutomationAssessment(
        public_id=str(uuid.uuid4()),
        organization_id=DEFAULT_ORG_ID,
        company_id=company.id,
        contact_id=contact.id,
        lead_id=lead.id,
        assessment_version=assessment_version,
        scoring_model_version="1.0",
        recommendation_model_version="1.0",
        raw_answers=answers,
        calculated_output=results,
        industry=company_data.get("industry"),
        employee_range=answers.get("peopleInvolved"),
        automation_score=results.get("opportunityScore", results.get("automation_score", 0)),
        estimated_annual_savings=results.get("estimated_annual_savings", 0),
        estimated_weekly_hours=results.get("estimatedWeeklyHours", 0),
        estimated_annual_hours=results.get("estimatedAnnualHours", 0),
        estimated_people_count=results.get("estimatedPeopleCount", 0),
        primary_pain_points=answers.get("mainProblems", []),
        privacy_accepted=consent.get("privacy_accepted", False) if consent else False,
        marketing_accepted=consent.get("marketing_accepted", False) if consent else False,
        consent_accepted_at=consent.get("accepted_at") if consent else None,
        utm_source=attribution.get("utm_source") if attribution else None,
        utm_medium=attribution.get("utm_medium") if attribution else None,
        utm_campaign=attribution.get("utm_campaign") if attribution else None,
        referrer=attribution.get("referrer") if attribution else None,
        landing_page=attribution.get("landing_page") if attribution else None,
        idempotency_key=idempotency_key,
        assessment_fingerprint=fingerprint,
        correlation_id=correlation_id,
        # ── Sprint 47.9 intelligence ──
        primary_pain_point=intelligence["primary_pain_point"],
        secondary_pain_points=intelligence["secondary_pain_points"],
        current_process_summary=intelligence["current_process_summary"],
        root_cause=intelligence["root_cause"],
        business_impact=intelligence["business_impact"],
        recommended_solution_categories=intelligence["recommended_solution_categories"],
        recommendation_reasons=intelligence["recommendation_reasons"],
        urgency=intelligence["urgency"],
        buying_signals=intelligence["buying_signals"],
        likely_decision_maker=intelligence["likely_decision_maker"],
        project_size_band=intelligence["project_size_band"],
        next_best_action=intelligence["next_best_action"],
        discovery_questions=intelligence["discovery_questions"],
        intelligence_json=intelligence,
        intelligence_version=intelligence["intelligence_version"],
        intelligence_generated_at=datetime.now(UTC),
        intelligence_confidence=intelligence["confidence"],
    )
    session.add(assessment)
    session.flush()
    
    # ── Create Activity ──
    activity = Activity(
        organization_id=DEFAULT_ORG_ID,
        company_id=company.id,
        contact_id=contact.id,
        activity_type="assessment",
        subject=f"Website Assessment — {company.name}",
        body=f"Automation assessment completed. Score: {results.get('opportunityScore', 0)}/100. "
             f"Estimated savings: ${results.get('estimated_annual_savings', 0):,}/yr. "
             f"Priority: {lead_score['priority']}.",
    )
    session.add(activity)
    session.flush()
    
    # ── Create Follow-up Task (Sprint 47.9 — Rich Context) ──
    priority = lead_score["priority"]
    due_hours = 4 if priority == "high" else 24 if priority == "medium" else 72
    solutions_text = ", ".join(intelligence["recommended_solution_categories"][:2])
    best_question = intelligence["discovery_questions"][0] if intelligence["discovery_questions"] else ""
    task = Task(
        organization_id=DEFAULT_ORG_ID,
        company_id=company.id,
        contact_id=contact.id,
        title=f"Review Assessment — {company.name}",
        description=(
            f"Primary pain: {intelligence['primary_pain_point']}\n"
            f"Score: {intelligence['automation_score']}/100\n"
            f"Estimated savings: ${intelligence['estimated_annual_savings']:,}/yr\n"
            f"Recommended solution: {solutions_text}\n"
            f"Suggested first question: {best_question}\n"
            f"Suggested objective: {intelligence['next_best_action']}"
        ),
        priority=priority,
        status="open",
        due_date=datetime.now(UTC),
    )
    session.add(task)
    session.flush()
    
    # ── Write Outbox Events (Sprint 47.9 — Rich Payloads) ──
    internal_payload = {
        "assessment_id": assessment.public_id,
        "company_name": company.name,
        "contact_email": contact.email,
        "contact_name": f"{contact.first_name} {contact.last_name}",
        "contact_phone": contact.phone or "",
        "industry": company_data.get("industry", ""),
        "employee_range": answers.get("peopleInvolved", ""),
        "lead_priority": lead_score["priority"],
        "lead_score": lead_score["score"],
        "lead_reasons": lead_score["reasons"],
        "answers": answers,
        "results": results,
        "intelligence": intelligence,
    }
    visitor_payload = {
        "assessment_id": assessment.public_id,
        "contact_email": contact.email,
        "contact_name": f"{contact.first_name} {contact.last_name}",
        "company_name": company.name,
        "automation_score": intelligence["automation_score"],
        "score_interpretation": intelligence["score_interpretation"],
        "estimated_annual_savings": intelligence["estimated_annual_savings"],
        "estimated_weekly_hours": intelligence["estimated_weekly_hours"],
        "primary_pain_point": intelligence["primary_pain_point"],
        "recommended_solutions": intelligence["recommended_solution_categories"],
    }
    
    outbox_events = [
        ("assessment.completed", {"assessment_id": assessment.public_id, "company_id": company.id, "lead_id": lead.id}),
        ("assessment.report.requested", {"assessment_id": assessment.public_id}),
        ("assessment.internal_notification.requested", internal_payload),
        ("assessment.visitor_email.requested", visitor_payload),
        ("lead.followup.requested", {"lead_id": lead.id, "task_id": task.id, "priority": priority}),
        ("knowledge.assessment_ingestion.requested", {"assessment_id": assessment.public_id, "company_id": company.id, "intelligence": intelligence}),
    ]
    
    for event_type, payload in outbox_events:
        evt = OutboxEvent(
            event_type=event_type,
            payload_json=payload,
            correlation_id=correlation_id,
        )
        session.add(evt)
    
    # ── Commit transaction ──
    session.commit()
    
    logger.info(
        "Assessment submitted: id=%s company=%s contact=%s lead=%s company_new=%s contact_new=%s lead_new=%s",
        assessment.public_id, company.id, contact.id, lead.id,
        company_created, contact_created, lead_created,
    )
    
    return _build_public_response(assessment)


def _build_public_response(assessment: AutomationAssessment, status: str = "completed") -> dict:
    """Build a public-safe response — no internal IDs."""
    output = assessment.calculated_output or {}
    return {
        "submission_id": assessment.public_id,
        "assessment_id": assessment.public_id,
        "status": status,
        "automation_score": output.get("opportunityScore", output.get("automation_score", 0)),
        "estimated_hours_saved": output.get("estimatedWeeklyHours", 0),
        "estimated_annual_savings": output.get("estimated_annual_savings", 0),
        "primary_pain_points": assessment.primary_pain_points or [],
        "recommended_solutions": output.get("recommended_solutions", []),
        "report_status": assessment.pdf_status or "queued",
        "booking_url": "https://calendly.com/vinidias-pacificnorthsystems-operations-audit/30min",
    }
