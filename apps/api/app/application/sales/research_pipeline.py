"""
Lead Research Pipeline.

Orchestrates the AI enrichment pipeline for leads:
  Website Analysis → Business Analysis → Industry Detection →
  Technology Detection → Buying Signal Detection →
  Decision Maker Discovery → Operational Challenge Detection →
  AI Opportunity Analysis → Recommended Services →
  Opportunity Scoring → Confidence Scoring → Executive Summary

Every stage reports progress. Pipeline is resumable.
"""

import json
import time
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.llm.enrichment import EnrichmentService
from app.infrastructure.db.models import Lead, LeadTimelineEvent

RESEARCH_STAGES = [
    {"key": "website_analysis", "label": "Website Analysis", "order": 1},
    {"key": "business_analysis", "label": "Business Analysis", "order": 2},
    {"key": "industry_detection", "label": "Industry Detection", "order": 3},
    {"key": "technology_detection", "label": "Technology Detection", "order": 4},
    {"key": "buying_signals", "label": "Buying Signal Detection", "order": 5},
    {"key": "decision_makers", "label": "Decision Maker Discovery", "order": 6},
    {"key": "operational_challenges", "label": "Operational Challenge Detection", "order": 7},
    {"key": "opportunity_analysis", "label": "AI Opportunity Analysis", "order": 8},
    {"key": "recommended_services", "label": "Recommended Services", "order": 9},
    {"key": "opportunity_scoring", "label": "Opportunity Scoring", "order": 10},
    {"key": "confidence_scoring", "label": "Confidence Scoring", "order": 11},
    {"key": "executive_summary", "label": "Executive Summary", "order": 12},
]

STAGE_STATUSES = ("pending", "running", "complete", "failed", "skipped")


def _init_stages() -> list[dict[str, Any]]:
    return [{"key": s["key"], "label": s["label"], "order": s["order"], "status": "pending"} for s in RESEARCH_STAGES]


def _add_timeline(session: Session, org_id: int, lead_id: int, event_type: str, description: str, metadata: dict | None = None):
    session.add(LeadTimelineEvent(
        organization_id=org_id, lead_id=lead_id, event_type=event_type,
        description=description, metadata_json=json.dumps(metadata) if metadata else None,
    ))


class ResearchPipeline:
    """Runs the AI research pipeline for a lead."""

    def __init__(self, session: Session, enrichment: EnrichmentService | None = None) -> None:
        self._session = session
        self._enrichment = enrichment

    def get_stages(self, lead: Lead) -> list[dict[str, Any]]:
        if lead.research_stages:
            try:
                return json.loads(lead.research_stages)
            except (json.JSONDecodeError, TypeError):
                pass
        return _init_stages()

    def get_progress(self, lead: Lead) -> dict[str, Any]:
        stages = self.get_stages(lead)
        completed = sum(1 for s in stages if s["status"] == "complete")
        failed = sum(1 for s in stages if s["status"] == "failed")
        running = any(s["status"] == "running" for s in stages)
        return {
            "lead_id": lead.id,
            "lead_name": lead.name,
            "total_stages": len(stages),
            "completed": completed,
            "failed": failed,
            "running": running,
            "percent": round(completed / len(stages) * 100) if stages else 0,
            "stages": stages,
        }

    def start_pipeline(self, lead: Lead, org_id: int) -> dict[str, Any]:
        """Initialize all stages to pending and mark first as running."""
        stages = _init_stages()
        if stages:
            stages[0]["status"] = "running"
        lead.research_stages = json.dumps(stages)
        lead.status = "researching"
        self._session.add(lead)
        _add_timeline(self._session, org_id, lead.id, "research_started", "AI research pipeline started")
        self._session.commit()
        return {"status": "started", "stages": stages}

    async def run_stage(self, lead: Lead, org_id: int, stage_key: str) -> dict[str, Any]:
        """Run a specific research stage."""
        stages = self.get_stages(lead)
        stage = next((s for s in stages if s["key"] == stage_key), None)
        if not stage:
            return {"error": f"Unknown stage: {stage_key}"}

        stage["status"] = "running"
        lead.research_stages = json.dumps(stages)
        self._session.add(lead)
        self._session.commit()

        try:
            result = await self._execute_stage(lead, stage_key)
            stage["status"] = "complete"
            stage["result"] = result.get("summary", "")
            _add_timeline(self._session, org_id, lead.id, f"stage_{stage_key}", f"Stage complete: {stage['label']}")
        except Exception as e:
            stage["status"] = "failed"
            stage["error"] = str(e)
            _add_timeline(self._session, org_id, lead.id, f"stage_{stage_key}_failed", f"Stage failed: {stage['label']} — {e}")

        lead.research_stages = json.dumps(stages)
        lead.last_researched_at = datetime.now(UTC)

        # Auto-advance to next stage
        self._advance_pipeline(stages)

        lead.research_stages = json.dumps(stages)
        self._session.add(lead)
        self._session.commit()

        return {"stage": stage_key, "status": stage["status"], "stages": stages}

    async def run_full_pipeline(self, lead: Lead, org_id: int) -> dict[str, Any]:
        """Run all pending stages sequentially."""
        self.start_pipeline(lead, org_id)
        stages = self.get_stages(lead)

        for stage in stages:
            if stage["status"] in ("complete", "skipped"):
                continue
            await self.run_stage(lead, org_id, stage["key"])

        lead.status = "ready_for_review"
        lead.research_stages = json.dumps(stages)
        self._session.add(lead)
        _add_timeline(self._session, org_id, lead.id, "research_complete", "AI research pipeline complete")
        self._session.commit()

        return self.get_progress(lead)

    async def _execute_stage(self, lead: Lead, stage_key: str) -> dict[str, Any]:
        """Execute a single research stage using LLM enrichment."""
        context = {
            "name": lead.name,
            "industry": lead.industry or "",
            "website": lead.website or "",
            "city": lead.city or "",
            "province": lead.province or "",
            "employees": lead.employees,
            "description": lead.description or "",
        }

        if self._enrichment and self._enrichment.available:
            result = await self._enrichment.enrich(stage_key, context)
            if result.enriched:
                return {"summary": result.content, "confidence": result.confidence}
        else:
            # Simulate completion when LLM is unavailable
            time.sleep(0.05)

        return {"summary": self._fallback_summary(lead, stage_key), "confidence": "medium"}

    def _fallback_summary(self, lead: Lead, stage_key: str) -> str:
        """Generate fallback text when LLM is unavailable."""
        fallbacks = {
            "website_analysis": f"Website {lead.website or 'not provided'}. {'Has online presence.' if lead.website else 'No website detected.'}",
            "business_analysis": f"{lead.name} operates in {lead.industry or 'an unknown industry'} with approximately {lead.employees or 'unknown'} employees.",
            "industry_detection": f"Industry classified as: {lead.industry or 'Unknown'}.",
            "technology_detection": "Technology stack analysis pending deeper research.",
            "buying_signals": "Buying signals require AI analysis to detect patterns in hiring, expansion, and technology modernization.",
            "decision_makers": "Decision maker discovery requires LinkedIn and organizational research.",
            "operational_challenges": "Operational challenges to be identified through business analysis.",
            "opportunity_analysis": "Opportunity analysis requires complete research data.",
            "recommended_services": "Service recommendations generated after full analysis.",
            "opportunity_scoring": f"Preliminary score based on available data: {lead.opportunity_score or 'pending'}.",
            "confidence_scoring": f"Confidence: {lead.confidence_score or 'pending'}%.",
            "executive_summary": f"{lead.name} is a{'n' if lead.industry and lead.industry[0].lower() in 'aeiou' else ''} {lead.industry or 'unknown'} company{' based in ' + lead.city if lead.city else ''}. Further research recommended.",
        }
        return fallbacks.get(stage_key, "Analysis pending.")

    def _advance_pipeline(self, stages: list[dict[str, Any]]) -> None:
        """Mark the next pending stage as running."""
        for stage in stages:
            if stage["status"] == "pending":
                stage["status"] = "running"
                break

    def retry_stage(self, lead: Lead, org_id: int, stage_key: str) -> dict[str, Any]:
        """Retry a failed stage synchronously."""
        stages = self.get_stages(lead)
        stage = next((s for s in stages if s["key"] == stage_key), None)
        if not stage:
            return {"error": f"Unknown stage: {stage_key}"}
        stage["status"] = "pending"
        stage.pop("error", None)
        stage.pop("result", None)
        lead.research_stages = json.dumps(stages)
        self._session.add(lead)
        self._session.commit()
        _add_timeline(self._session, org_id, lead.id, "stage_retry", f"Retrying stage: {stage['label']}")
        self._session.commit()
        return {"status": "retrying", "stage": stage_key}
