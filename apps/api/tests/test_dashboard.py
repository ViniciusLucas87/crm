from conftest import auth_headers
from fastapi.testclient import TestClient
from datetime import date, timedelta

from app.infrastructure.db.models import Organization, Task


def test_dashboard_summary_shape(client: TestClient) -> None:
    response = client.get(
        "/api/v1/dashboard/summary",
        headers=auth_headers("org1-admin"),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["tasks_today"] >= 0
    assert payload["pipeline_value"] >= 0


def test_dashboard_task_counter_includes_overdue_and_excludes_upcoming(client: TestClient) -> None:
    # First authenticated request provisions the test organization.
    client.get("/api/v1/dashboard/summary", headers=auth_headers("org1-admin"))
    from app.infrastructure.db import session as db_session
    db = db_session.SessionLocal()
    try:
        org = db.query(Organization).filter(Organization.clerk_org_id == "org_1").one()
        db.add_all([
            Task(organization_id=org.id, title="Overdue follow up", due_date=date.today() - timedelta(days=2), is_completed=False),
            Task(organization_id=org.id, title="Due today", due_date=date.today(), is_completed=False),
            Task(organization_id=org.id, title="Upcoming", due_date=date.today() + timedelta(days=2), is_completed=False),
            Task(organization_id=org.id, title="Completed overdue", due_date=date.today() - timedelta(days=3), is_completed=True),
        ])
        db.commit()

        response = client.get("/api/v1/dashboard/summary", headers=auth_headers("org1-admin"))
        assert response.status_code == 200
        assert response.json()["tasks_today"] == 2
    finally:
        db.close()
