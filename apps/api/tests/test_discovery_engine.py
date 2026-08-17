import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from app.application.sales.discovery_engine import DiscoveryCriteria, LLMDiscoveryProvider


def test_discovery_ignores_gateway_fallback_instead_of_creating_blank_lead():
    gateway = Mock()
    gateway.chat = AsyncMock(return_value=SimpleNamespace(
        model="budget_blocked",
        content=json.dumps({"summary": "LLM temporarily unavailable."}),
    ))
    provider = LLMDiscoveryProvider(api_key="configured")

    with patch("app.application.llm.gateway.get_llm_gateway", return_value=gateway):
        companies = asyncio.run(provider.discover(DiscoveryCriteria(count=3)))

    assert companies == []


def test_discovery_uses_cache_and_excludes_existing_names():
    gateway = Mock()
    gateway.chat = AsyncMock(return_value=SimpleNamespace(
        model="deepseek-v4-flash",
        content=json.dumps({"companies": [
            {"name": "Fresh Construction Ltd.", "industry": "Construction", "city": "Vancouver"},
            {"name": "", "industry": "Construction"},
        ]}),
    ))
    provider = LLMDiscoveryProvider(api_key="configured")
    criteria = DiscoveryCriteria(
        industry="Construction",
        city="Vancouver",
        count=3,
        organization_id=7,
        excluded_names=["Existing Builder Ltd."],
    )

    with patch("app.application.llm.gateway.get_llm_gateway", return_value=gateway):
        companies = asyncio.run(provider.discover(criteria))

    assert [company.name for company in companies] == ["Fresh Construction Ltd."]
    messages, config = gateway.chat.await_args.args
    assert config.feature == "discovery"
    assert config.organization_id == 7
    assert config.bypass_cache is False
    assert "Existing Builder Ltd." in messages[-1].content
    assert "exactly 3" in messages[-1].content
