import asyncio
import logging

import httpx

from app.application.telephony.telnyx import TelnyxProvider, _safe_response_text


class _FakeTelnyxClient:
    async def post(self, endpoint, json):
        request = httpx.Request("POST", f"https://api.telnyx.com/v2{endpoint}")
        return httpx.Response(
            201,
            request=request,
            json={
                "data": {
                    "id": "credential-id",
                    "sip_username": "secret-user",
                    "sip_password": "secret-password",
                    "token": "secret-token",
                }
            },
        )


def test_safe_response_text_redacts_nested_credentials():
    response = httpx.Response(
        400,
        request=httpx.Request("POST", "https://api.telnyx.com/v2/telephony_credentials"),
        json={"error": {"sip_password": "secret", "token": "also-secret", "detail": "invalid"}},
    )

    safe = _safe_response_text(response)

    assert "secret" not in safe
    assert "also-secret" not in safe
    assert safe.count("[REDACTED]") == 2


def test_successful_token_generation_does_not_log_credentials(caplog):
    provider = TelnyxProvider({"connection_id": "connection-id"})
    provider._initialized = True
    provider._http = _FakeTelnyxClient()

    with caplog.at_level(logging.INFO):
        result = asyncio.run(provider.generate_token("user-1"))

    assert result["sip_username"] == "secret-user"
    assert result["sip_password"] == "secret-password"
    assert "secret-user" not in caplog.text
    assert "secret-password" not in caplog.text
    assert "secret-token" not in caplog.text
