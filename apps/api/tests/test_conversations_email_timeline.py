from datetime import UTC, datetime
from uuid import uuid4

from conftest import auth_headers
from fastapi.testclient import TestClient

from app.infrastructure.db import session as db_session
from app.infrastructure.db.models import Activity, Company, EmailMessage


def _create_company(client: TestClient, name: str) -> int:
    authenticated = client.get(
        "/api/v1/auth/me", headers=auth_headers("org1-admin")
    )
    assert authenticated.status_code == 200
    with db_session.SessionLocal() as session:
        company = Company(organization_id=1, name=name)
        session.add(company)
        session.commit()
        session.refresh(company)
        return company.id


def test_company_email_appears_in_conversation_timeline_and_stats(client: TestClient) -> None:
    company_id = _create_company(client, "Timeline Email Co")

    created_conversation = client.post(
        "/api/v1/conversations",
        params={"company_id": company_id},
        headers=auth_headers("org1-admin"),
    )
    assert created_conversation.status_code == 200
    conversation_id = created_conversation.json()["id"]

    sent_at = datetime.now(UTC)
    with db_session.SessionLocal() as session:
        session.add(EmailMessage(
            public_uuid=str(uuid4()),
            organization_id=1,
            company_id=company_id,
            direction="outbound",
            status="sent",
            delivery_status="accepted",
            from_address="vinidias@pacificnorthsystems.com",
            to_address="hello@example.com",
            subject="A human follow-up",
            provider="zoho",
            sent_at=sent_at,
        ))
        session.commit()

    timeline = client.get(
        f"/api/v1/conversations/{conversation_id}/timeline",
        headers=auth_headers("org1-admin"),
    )
    assert timeline.status_code == 200
    email_event = next(event for event in timeline.json()["events"] if event["type"] == "email")
    assert email_event["data"]["subject"] == "A human follow-up"
    assert email_event["data"]["direction"] == "outbound"
    assert email_event["data"]["to_address"] == "hello@example.com"

    stats = client.get(
        f"/api/v1/conversations/{conversation_id}/stats",
        headers=auth_headers("org1-admin"),
    )
    assert stats.status_code == 200
    assert stats.json()["email_count"] == 1
    assert stats.json()["total_events"] == 1


def test_company_email_timeline_is_tenant_scoped(client: TestClient) -> None:
    company_id = _create_company(client, "Scoped Email Co")
    conversation = client.post(
        "/api/v1/conversations",
        params={"company_id": company_id},
        headers=auth_headers("org1-admin"),
    ).json()

    response = client.get(
        f"/api/v1/conversations/{conversation['id']}/timeline",
        headers=auth_headers("org2-admin"),
    )
    assert response.status_code == 200
    assert response.json() == {"error": "Conversation not found"}


def test_created_activity_is_linked_to_the_active_conversation(client: TestClient) -> None:
    company_id = _create_company(client, "Linked Activity Co")
    conversation = client.post(
        "/api/v1/conversations",
        params={"company_id": company_id},
        headers=auth_headers("org1-admin"),
    ).json()

    created = client.post(
        "/api/v1/activities",
        json={
            "company_id": company_id,
            "activity_type": "email",
            "subject": "Manual email log",
            "body": "A useful note from the interaction.",
        },
        headers=auth_headers("org1-admin"),
    )
    assert created.status_code == 200

    with db_session.SessionLocal() as session:
        activity = session.get(Activity, created.json()["id"])
        assert activity is not None
        assert activity.conversation_id == conversation["id"]

    timeline = client.get(
        f"/api/v1/conversations/{conversation['id']}/timeline",
        headers=auth_headers("org1-admin"),
    ).json()
    activity_event = next(
        event for event in timeline["events"] if event["type"] == "activity"
    )
    assert activity_event["data"]["subject"] == "Manual email log"
