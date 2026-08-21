from fastapi.testclient import TestClient

from app.infrastructure.db import session as db_session
from app.infrastructure.db.models import Call, Company, Contact
from tests.conftest import auth_headers


def test_browser_call_is_saved_and_appears_in_history(client: TestClient) -> None:
    created = client.post(
        "/api/v1/telephony/calls/browser",
        headers=auth_headers("org1-admin"),
        json={"phone_number": "+16045550123"},
    )
    assert created.status_code == 200
    call_id = created.json()["id"]

    updated = client.patch(
        f"/api/v1/telephony/calls/browser/{call_id}",
        headers=auth_headers("org1-admin"),
        json={"status": "ended", "duration_seconds": 42},
    )
    assert updated.status_code == 200

    history = client.get("/api/v1/telephony/history", headers=auth_headers("org1-admin"))
    assert history.status_code == 200
    item = history.json()["items"][0]
    assert item["kind"] == "call"
    assert item["direction"] == "outbound"
    assert item["phone_number"] == "+16045550123"
    assert item["duration_seconds"] == 42


def test_call_center_history_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/telephony/history")
    assert response.status_code == 401


def test_browser_call_history_is_tenant_scoped(client: TestClient) -> None:
    client.post(
        "/api/v1/telephony/calls/browser",
        headers=auth_headers("org1-admin"),
        json={"phone_number": "+16045550124"},
    )

    other_org = client.get("/api/v1/telephony/history", headers=auth_headers("org2-admin"))
    assert other_org.status_code == 200
    assert other_org.json()["items"] == []


def test_browser_call_auto_links_a_unique_contact_phone_to_conversation(client: TestClient) -> None:
    with db_session.SessionLocal() as session:
        company = Company(organization_id=1, name="Call Centre Plumbing")
        session.add(company)
        session.flush()
        contact = Contact(
            organization_id=1,
            company_id=company.id,
            first_name="Casey",
            last_name="Contact",
            phone="604-722-1848",
        )
        session.add(contact)
        session.commit()
        company_id, contact_id = company.id, contact.id

    created = client.post(
        "/api/v1/telephony/calls/browser",
        headers=auth_headers("org1-admin"),
        json={"phone_number": "+16047221848"},
    )
    assert created.status_code == 200
    body = created.json()
    assert body["company_id"] == company_id
    assert body["contact_id"] == contact_id
    assert body["conversation_id"] is not None

    connected = client.patch(
        f"/api/v1/telephony/calls/browser/{body['id']}",
        headers=auth_headers("org1-admin"),
        json={"status": "connected", "duration_seconds": 0},
    )
    assert connected.status_code == 200

    timeline = client.get(
        f"/api/v1/conversations/{body['conversation_id']}/timeline",
        headers=auth_headers("org1-admin"),
    )
    assert timeline.status_code == 200
    assert any(event["type"] == "call" and event["id"] == body["id"] for event in timeline.json()["events"])


def test_creating_company_conversation_backfills_matching_legacy_browser_call(client: TestClient) -> None:
    with db_session.SessionLocal() as session:
        company = Company(organization_id=1, name="Legacy Call Plumbing")
        session.add(company)
        session.flush()
        contact = Contact(
            organization_id=1,
            company_id=company.id,
            first_name="Unknown",
            last_name="Contact",
            phone="6047221848",
        )
        session.add(contact)
        legacy_call = Call(
            public_uuid="f7243c04-bd16-4c96-92ec-2e168cfca93e",
            organization_id=1,
            provider="telnyx_webrtc",
            direction="outbound",
            status="ended",
            phone_number="+16047221848",
        )
        session.add(legacy_call)
        session.commit()
        company_id, contact_id, call_id = company.id, contact.id, legacy_call.id

    conversation = client.post(
        "/api/v1/conversations",
        params={"company_id": company_id},
        headers=auth_headers("org1-admin"),
    )
    assert conversation.status_code == 200

    with db_session.SessionLocal() as session:
        linked_call = session.get(Call, call_id)
        assert linked_call is not None
        assert linked_call.company_id == company_id
        assert linked_call.contact_id == contact_id
        assert linked_call.conversation_id == conversation.json()["id"]
