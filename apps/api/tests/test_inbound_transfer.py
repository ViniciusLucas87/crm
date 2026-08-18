import asyncio
import base64
import json
from types import SimpleNamespace

from app.presentation.api.v1.routes import telephony


def test_inbound_never_miss_call_transfers_to_configured_mobile(monkeypatch):
    config = SimpleNamespace(
        organization_id=1,
        product_code="never_miss",
        enabled=True,
        business_phone="+16042251745",
        notification_phone="+17786786568",
    )

    class Result:
        def scalar_one_or_none(self):
            return config

    class Session:
        def execute(self, _statement):
            return Result()

    captured = {}

    class Response:
        status_code = 200

    class Client:
        def __init__(self, **_kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def post(self, url, **kwargs):
            captured["url"] = url
            captured["json"] = kwargs["json"]
            return Response()

    monkeypatch.setenv("INBOUND_CALL_TRANSFER_ENABLED", "true")
    monkeypatch.setenv("TELNYX_API_KEY", "test-key")
    monkeypatch.setenv("TELNYX_PUBLIC_URL", "https://api.pacificnorthsystems.com")
    monkeypatch.setattr(telephony.httpx, "AsyncClient", Client)

    transferred = asyncio.run(
        telephony._transfer_inbound_call(
            {
                "direction": "incoming",
                "call_control_id": "call-control-123",
                "to": "+16042251745",
                "from": "+16045550100",
            },
            Session(),
        )
    )

    assert transferred is True
    assert captured["url"].endswith("/calls/call-control-123/actions/transfer")
    assert captured["json"]["to"] == "+17786786568"
    assert captured["json"]["from"] == "+16042251745"
    assert captured["json"]["timeout_secs"] == 25
    assert captured["json"]["webhook_url"] == "https://api.pacificnorthsystems.com/api/v1/telephony/webhook"


def test_inbound_transfer_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("INBOUND_CALL_TRANSFER_ENABLED", raising=False)
    transferred = asyncio.run(
        telephony._transfer_inbound_call(
            {"direction": "incoming", "call_control_id": "call-control-123", "to": "+16042251745"},
            object(),
        )
    )
    assert transferred is False


def test_transfer_leg_state_recovers_organization_without_using_destination_number():
    state = base64.b64encode(
        json.dumps({"kind": "never_miss_transfer", "organization_id": 7}).encode()
    ).decode()
    decoded = telephony._decode_never_miss_transfer_state({"client_state": state})
    assert decoded == {"kind": "never_miss_transfer", "organization_id": 7}


def test_unrelated_or_invalid_client_state_is_ignored():
    unrelated = base64.b64encode(json.dumps({"kind": "other", "organization_id": 7}).encode()).decode()
    assert telephony._decode_never_miss_transfer_state({"client_state": unrelated}) == {}
    assert telephony._decode_never_miss_transfer_state({"client_state": "not-base64"}) == {}
