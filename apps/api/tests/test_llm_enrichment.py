from types import SimpleNamespace

import pytest

from app.application.llm.enrichment import EnrichmentService


def test_enrichment_service_initializes_when_configured() -> None:
    service = EnrichmentService(api_key="test-key")

    assert service.available is True


@pytest.mark.asyncio
async def test_enrichment_uses_gateway_output_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeGateway:
        async def chat(self, messages, config):
            assert config.feature == "enrichment"
            assert config.max_tokens > 0
            return SimpleNamespace(model="test-model", content="Prioritize follow-up")

    monkeypatch.setattr(
        "app.application.llm.gateway.get_llm_gateway",
        lambda: FakeGateway(),
    )
    service = EnrichmentService(api_key="test-key")

    result = await service.enrich("daily_brief", {"tasks": 1})

    assert result.enriched is True
    assert result.content == "Prioritize follow-up"
