"""Protected App Factory portfolio and validation APIs."""

import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.application.app_factory_catalog import CANDIDATES, EVIDENCE
from app.infrastructure.auth.clerk import AuthContext, require_permission
from app.infrastructure.db.app_factory import (
    AppFactoryCandidate,
    AppFactoryEvidence,
    AppFactoryExperiment,
)
from app.infrastructure.db.session import get_db_session

router = APIRouter(prefix="/app-factory", tags=["app-factory"])


class ExperimentInput(BaseModel):
    candidate_id: int
    name: str = Field(min_length=3, max_length=255)
    hypothesis: str = Field(min_length=10, max_length=2000)
    channel: str = Field(min_length=2, max_length=80)
    success_metric: str = Field(min_length=10, max_length=1000)
    spend_limit_cents: int = Field(default=0, ge=0, le=25_000)


def _seed(session: Session, organization_id: int) -> None:
    existing = set(
        session.scalars(
            select(AppFactoryCandidate.slug).where(
                AppFactoryCandidate.organization_id == organization_id
            )
        )
    )
    for item in CANDIDATES:
        if item["slug"] in existing:
            continue
        candidate = AppFactoryCandidate(
            organization_id=organization_id,
            slug=item["slug"],
            name=item["name"],
            audience=item["audience"],
            problem=item["problem"],
            proposed_format=item["proposed_format"],
            proposed_price=item["proposed_price"],
            distribution_thesis=item["distribution_thesis"],
            current_workaround=item["current_workaround"],
            decision=item["decision"],
            decision_reason=item["decision_reason"],
            score_json=json.dumps(item["score"]),
            total_score=item["total_score"],
            estimated_monthly_cost_cents=item["estimated_monthly_cost_cents"],
            risk_level=item["risk_level"],
            evidence_count=len(EVIDENCE.get(item["slug"], [])),
        )
        session.add(candidate)
        session.flush()
        for source_type, title, url, observed_at, signal, evidence_kind in EVIDENCE.get(
            item["slug"], []
        ):
            session.add(
                AppFactoryEvidence(
                    organization_id=organization_id,
                    candidate_id=candidate.id,
                    source_type=source_type,
                    source_title=title,
                    source_url=url,
                    observed_at=observed_at,
                    signal=signal,
                    evidence_kind=evidence_kind,
                )
            )
    session.commit()


def _candidate_payload(candidate: AppFactoryCandidate, evidence: list[AppFactoryEvidence]) -> dict:
    evidence_complete = len(evidence) >= 3
    score_passes = candidate.total_score >= 75
    return {
        "id": candidate.id,
        "slug": candidate.slug,
        "name": candidate.name,
        "audience": candidate.audience,
        "problem": candidate.problem,
        "proposed_format": candidate.proposed_format,
        "proposed_price": candidate.proposed_price,
        "distribution_thesis": candidate.distribution_thesis,
        "current_workaround": candidate.current_workaround,
        "decision": candidate.decision,
        "decision_reason": candidate.decision_reason,
        "scores": json.loads(candidate.score_json),
        "total_score": candidate.total_score,
        "estimated_monthly_cost_cents": candidate.estimated_monthly_cost_cents,
        "risk_level": candidate.risk_level,
        "evidence_count": len(evidence),
        "evidence_complete": evidence_complete,
        "eligible_for_validation": score_passes
        and evidence_complete
        and candidate.risk_level != "high",
        "eligible_for_build": False,
        "evidence": [
            {
                "source_type": item.source_type,
                "source_title": item.source_title,
                "source_url": item.source_url,
                "observed_at": item.observed_at,
                "signal": item.signal,
                "evidence_kind": item.evidence_kind,
            }
            for item in evidence
        ],
    }


@router.get("/portfolio")
def portfolio(
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    _seed(session, ctx.organization_id)
    candidates = session.scalars(
        select(AppFactoryCandidate)
        .where(AppFactoryCandidate.organization_id == ctx.organization_id)
        .order_by(AppFactoryCandidate.total_score.desc(), AppFactoryCandidate.name)
    ).all()
    evidence = session.scalars(
        select(AppFactoryEvidence).where(AppFactoryEvidence.organization_id == ctx.organization_id)
    ).all()
    evidence_by_candidate: dict[int, list[AppFactoryEvidence]] = {}
    for item in evidence:
        evidence_by_candidate.setdefault(item.candidate_id, []).append(item)
    experiments = session.scalars(
        select(AppFactoryExperiment)
        .where(AppFactoryExperiment.organization_id == ctx.organization_id)
        .order_by(AppFactoryExperiment.created_at.desc())
    ).all()
    candidate_payload = [
        _candidate_payload(item, evidence_by_candidate.get(item.id, [])) for item in candidates
    ]
    return {
        "summary": {
            "problems_researched": len(candidates),
            "qualified_for_validation": sum(
                1 for item in candidate_payload if item["eligible_for_validation"]
            ),
            "qualified_for_build": 0,
            "active_experiments": sum(1 for item in experiments if item.status == "active"),
            "monthly_experiment_cost_limit_cents": sum(
                item.spend_limit_cents
                for item in experiments
                if item.status in {"proposed", "active"}
            ),
            "human_actions": [
                "Review evidence for the highest scoring candidates",
                "Approve a small Never Forget purchase intent experiment",
                "Do not start product development until validation results pass the release gates",
            ],
        },
        "candidates": candidate_payload,
        "experiments": [
            {
                "id": item.id,
                "candidate_id": item.candidate_id,
                "name": item.name,
                "hypothesis": item.hypothesis,
                "channel": item.channel,
                "success_metric": item.success_metric,
                "status": item.status,
                "spend_limit_cents": item.spend_limit_cents,
                "actual_spend_cents": item.actual_spend_cents,
                "visitors": item.visitors,
                "intent_actions": item.intent_actions,
                "paid_conversions": item.paid_conversions,
            }
            for item in experiments
        ],
        "guardrails": {
            "minimum_score": 75,
            "minimum_independent_sources": 3,
            "automatic_production_release": False,
            "automatic_private_messages": False,
            "production_credentials_available_to_experiments": False,
        },
    }


@router.post("/experiments", status_code=201)
def create_experiment(
    payload: ExperimentInput,
    ctx: AuthContext = Depends(require_permission("companies:write")),
    session: Session = Depends(get_db_session),
):
    candidate = session.scalar(
        select(AppFactoryCandidate).where(
            AppFactoryCandidate.id == payload.candidate_id,
            AppFactoryCandidate.organization_id == ctx.organization_id,
        )
    )
    if candidate is None:
        raise HTTPException(404, "Candidate not found")
    evidence_count = (
        session.scalar(
            select(func.count(AppFactoryEvidence.id)).where(
                AppFactoryEvidence.candidate_id == candidate.id,
                AppFactoryEvidence.organization_id == ctx.organization_id,
            )
        )
        or 0
    )
    if candidate.total_score < 75 or evidence_count < 3 or candidate.risk_level == "high":
        raise HTTPException(409, "This candidate has not passed the validation entry gate")
    experiment = AppFactoryExperiment(
        organization_id=ctx.organization_id,
        **payload.model_dump(),
    )
    session.add(experiment)
    session.commit()
    session.refresh(experiment)
    return {
        "id": experiment.id,
        "status": experiment.status,
        "message": "Experiment proposed for human review",
    }
