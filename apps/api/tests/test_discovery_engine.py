import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.application.sales.discovery_engine import (
    DiscoveredCompany,
    DiscoveryCriteria,
    DiscoveryEngine,
    DiscoveryUnavailableError,
    GooglePlacesDiscoveryProvider,
    LLMDiscoveryProvider,
)


def test_discovery_reports_gateway_failure_instead_of_creating_blank_lead():
    gateway = Mock()
    gateway.chat = AsyncMock(
        return_value=SimpleNamespace(
            model="budget_blocked",
            content=json.dumps({"summary": "LLM temporarily unavailable."}),
        )
    )
    provider = LLMDiscoveryProvider(api_key="configured")

    with patch("app.application.llm.gateway.get_llm_gateway", return_value=gateway):
        with pytest.raises(DiscoveryUnavailableError):
            asyncio.run(provider.discover(DiscoveryCriteria(count=3)))


def test_discovery_uses_cache_and_excludes_existing_names():
    gateway = Mock()
    gateway.chat = AsyncMock(
        return_value=SimpleNamespace(
            model="deepseek-v4-flash",
            content=json.dumps(
                {
                    "companies": [
                        {
                            "name": "Fresh Construction Ltd.",
                            "industry": "Construction",
                            "city": "Vancouver",
                        },
                        {"name": "", "industry": "Construction"},
                    ]
                }
            ),
        )
    )
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


def test_discovery_collects_attributable_public_business_contact():
    company = DiscoveredCompany(
        name="Example Heating",
        website="https://example.com",
    )
    evidence = {
        "source_url": "https://example.com/",
        "phones": ["+16045550123"],
        "emails": ["service@example.com"],
    }
    engine = DiscoveryEngine.__new__(DiscoveryEngine)

    with patch(
        "app.application.intelligence.web_fetch.collect_website_evidence",
        new=AsyncMock(return_value=evidence),
    ):
        asyncio.run(engine._attach_public_contact_evidence([company]))

    assert company.public_phone == "+16045550123"
    assert company.public_email == "service@example.com"
    assert company.contact_source_url == "https://example.com/"
    assert company.website_evidence == {"official_website": evidence}


def test_google_places_discovers_verified_company_and_phone():
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "places": [
            {
                "id": "place-123",
                "displayName": {"text": "Example Heating Ltd."},
                "formattedAddress": "123 Main St, Vancouver, BC, Canada",
                "addressComponents": [
                    {"longText": "Vancouver", "types": ["locality"]},
                    {"shortText": "BC", "types": ["administrative_area_level_1"]},
                    {"longText": "Canada", "types": ["country"]},
                ],
                "internationalPhoneNumber": "+1 604-555-0123",
                "websiteUri": "https://example-heating.test",
                "googleMapsUri": "https://maps.google.com/example",
                "primaryTypeDisplayName": {"text": "HVAC contractor"},
                "businessStatus": "OPERATIONAL",
            }
        ]
    }

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def post(self, *_args, **_kwargs):
            return response

    provider = GooglePlacesDiscoveryProvider(api_key="configured")
    with patch(
        "app.application.sales.discovery_engine.httpx.AsyncClient",
        return_value=FakeClient(),
    ):
        companies = asyncio.run(
            provider.discover(DiscoveryCriteria(industry="HVAC", city="Vancouver", count=10))
        )

    assert len(companies) == 1
    assert companies[0].name == "Example Heating Ltd."
    assert companies[0].public_phone == "+1 604-555-0123"
    assert companies[0].city == "Vancouver"
    assert companies[0].website_evidence["provider"] == "google_places"
