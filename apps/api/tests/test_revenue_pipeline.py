import json

from app.application.sales.outreach import OutreachGenerator
from app.application.sales.research_pipeline import ResearchPipeline
from app.infrastructure.db.models import Lead


def _lead() -> Lead:
    return Lead(
        organization_id=1,
        name="Evidence Builders",
        industry="Construction",
        website="https://example.com",
        status="researching",
    )


def test_research_results_persist_for_agent_and_outreach() -> None:
    lead = _lead()
    pipeline = ResearchPipeline(session=None)  # persistence helper does not use the session
    result = {
        "summary": json.dumps({"decision_makers": [{"name": "Sam Lee", "role": "Owner"}]}),
        "confidence": "high",
    }

    pipeline._apply_stage_result(lead, "decision_makers", result)

    assert "Sam Lee" in (lead.decision_makers_data or "")
    assert "decision_makers" in json.loads(lead.research_data or "{}")


def test_outreach_context_contains_research_evidence() -> None:
    lead = _lead()
    lead.website_data = json.dumps({"evidence": {"source_url": "https://example.com"}})
    lead.research_data = json.dumps({"buying_signals": {"content": "Hiring operations staff"}})
    lead.decision_makers_data = json.dumps({"decision_makers": [{"role": "Owner"}]})

    context = OutreachGenerator()._lead_context(lead)

    assert "source_url" in context["website_research"]
    assert "Hiring operations staff" in context["research"]
    assert "Owner" in context["decision_makers"]


def test_fallback_outreach_does_not_invent_performance_claims() -> None:
    email = OutreachGenerator()._fallback_outreach(_lead())["cold_email"]

    assert "30-40%" not in email
    assert "reduce operational overhead" not in email
