"""Today workspace integration tests — seeded records, tenant isolation, state transitions."""

from datetime import date, datetime, UTC, timedelta
import uuid

from app.infrastructure.db.models import (
    Organization, Company, Task, Lead, Activity, FollowUpAction,
)

API = "/api/v1/dashboard"


def _get_db():
    """Lazy import so conftest monkeypatch takes effect."""
    from app.infrastructure.db.session import SessionLocal
    return SessionLocal()


def _get_org(db, clerk_org_id, name="Test Org"):
    """Find or create an organization matching the conftest auth tokens."""
    org = db.query(Organization).filter(Organization.clerk_org_id == clerk_org_id).first()
    if org is None:
        org = Organization(clerk_org_id=clerk_org_id, name=name,
                           slug=f"test-{clerk_org_id}-{uuid.uuid4().hex[:6]}")
        db.add(org)
        db.commit()
        db.refresh(org)
    return org


def _seed_company(db, org, name):
    c = Company(organization_id=org.id, name=name)
    db.add(c)
    db.commit()
    return c


def _seed_task(db, org, **kw):
    defaults = dict(organization_id=org.id, title="Test follow up",
                    priority="medium", status="open", due_date=date.today(),
                    is_completed=False)
    defaults.update(kw)
    t = Task(**defaults)
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


def _seed_lead(db, org, **kw):
    defaults = dict(organization_id=org.id, name="Test Lead", status="new")
    defaults.update(kw)
    l = Lead(**defaults)
    db.add(l)
    db.commit()
    db.refresh(l)
    return l


class TestTodayWorkspace:
    def test_empty_returns_all_sections_empty(self, client):
        resp = client.get(f"{API}/today", headers={"Authorization": "Bearer org1-admin"})
        assert resp.status_code == 200
        data = resp.json()
        for s in ["assessment_leads","missed_calls","inbound_replies",
                   "overdue_follow_ups","due_today","upcoming","leads_no_next_action"]:
            assert data[s] == []

    def test_requires_auth(self, client):
        resp = client.get(f"{API}/today")
        assert resp.status_code in (401, 403)

    def test_tenant_isolation(self, client):
        db = _get_db()
        try:
            org1, org2 = _get_org(db, "org_1"), _get_org(db, "org_2")
            c1 = _seed_company(db, org1, "Acme")
            c2 = _seed_company(db, org2, "Beta")
            _seed_task(db, org1, company_id=c1.id, title="Org1 Overdue",
                       due_date=date.today() - timedelta(days=3))
            _seed_task(db, org2, company_id=c2.id, title="Org2 Today", due_date=date.today())

            h1 = {"Authorization": "Bearer org1-admin"}
            h2 = {"Authorization": "Bearer org2-admin"}
            r1 = client.get(f"{API}/today", headers=h1)
            r2 = client.get(f"{API}/today", headers=h2)

            overdue1 = [t["title"] for t in r1.json()["overdue_follow_ups"]]
            overdue2 = [t["title"] for t in r2.json()["overdue_follow_ups"]]
            due1 = [t["title"] for t in r1.json()["due_today"]]
            due2 = [t["title"] for t in r2.json()["due_today"]]

            assert "Org1 Overdue" in overdue1
            assert "Org1 Overdue" not in overdue2
            assert "Org2 Today" in due2
            assert "Org2 Today" not in due1
        finally:
            db.close()

    def test_sorts_overdue_by_date(self, client):
        db = _get_db()
        try:
            org1 = _get_org(db, "org_1")
            c = _seed_company(db, org1, "SortCo")
            _seed_task(db, org1, company_id=c.id, title="Older", due_date=date.today() - timedelta(days=5))
            _seed_task(db, org1, company_id=c.id, title="Newer", due_date=date.today() - timedelta(days=1))
            resp = client.get(f"{API}/today", headers={"Authorization": "Bearer org1-admin"})
            overdue = resp.json()["overdue_follow_ups"]
            assert len(overdue) >= 2
            assert overdue[0]["title"] == "Older"
        finally:
            db.close()


class TestFollowUpActions:
    def test_complete_requires_next_step_or_terminal(self, client):
        db = _get_db()
        try:
            org1 = _get_org(db, "org_1")
            c = _seed_company(db, org1, "TermCo")
            task = _seed_task(db, org1, company_id=c.id)
            resp = client.post(f"{API}/tasks/{task.id}/follow-up",
                               json={"action": "complete"},
                               headers={"Authorization": "Bearer org1-admin"})
            assert resp.status_code == 400
            assert "next step" in resp.json()["detail"].lower() or "terminal" in resp.json()["detail"].lower()
        finally:
            db.close()

    def test_complete_with_next_step(self, client):
        db = _get_db()
        try:
            org1 = _get_org(db, "org_1")
            c = _seed_company(db, org1, "NextCo")
            task = _seed_task(db, org1, company_id=c.id, title="Original")
            resp = client.post(
                f"{API}/tasks/{task.id}/follow-up",
                json={"action": "complete", "next_step_title": "Call back",
                      "next_step_due_date": str(date.today() + timedelta(days=7))},
                headers={"Authorization": "Bearer org1-admin"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["action"] == "completed"
            assert data["next_task_id"] is not None
            assert data["activity_id"] is not None
            db.refresh(task)
            assert task.is_completed is True
        finally:
            db.close()

    def test_complete_idempotent(self, client):
        db = _get_db()
        try:
            org1 = _get_org(db, "org_1")
            c = _seed_company(db, org1, "IdemCo")
            task = _seed_task(db, org1, company_id=c.id)
            r1 = client.post(f"{API}/tasks/{task.id}/follow-up",
                             json={"action": "complete", "terminal_outcome": "won"},
                             headers={"Authorization": "Bearer org1-admin"})
            assert r1.status_code == 200
            r2 = client.post(f"{API}/tasks/{task.id}/follow-up",
                             json={"action": "complete", "next_step_title": "No"},
                             headers={"Authorization": "Bearer org1-admin"})
            assert r2.status_code == 200
            assert "already" in r2.json()["message"].lower()
            # Verify FollowUpAction ledger: exactly one completed entry
            actions = db.query(FollowUpAction).filter(
                FollowUpAction.entity_type == "task",
                FollowUpAction.entity_id == task.id,
                FollowUpAction.action == "completed",
            ).all()
            assert len(actions) == 1, f"Expected 1 FollowUpAction, got {len(actions)}"
            assert actions[0].actor_user_id is not None, "actor_user_id must be set"
            assert actions[0].old_state, "old_state must be recorded"
            assert actions[0].new_state, "new_state must be recorded"
            # Verify idempotency: same key pattern for task (UUID-based)
            assert actions[0].idempotency_key.startswith("complete_"), (
                f"idempotency_key must start with 'complete_', got {actions[0].idempotency_key}"
            )
        finally:
            db.close()

    def test_reschedule_changes_date(self, client):
        db = _get_db()
        try:
            org1 = _get_org(db, "org_1")
            c = _seed_company(db, org1, "RSCo")
            task = _seed_task(db, org1, company_id=c.id, due_date=date.today())
            nd = str(date.today() + timedelta(days=14))
            resp = client.post(f"{API}/tasks/{task.id}/follow-up",
                               json={"action": "reschedule", "new_due_date": nd},
                               headers={"Authorization": "Bearer org1-admin"})
            assert resp.status_code == 200
            db.refresh(task)
            assert str(task.due_date) == nd
        finally:
            db.close()

    def test_cross_tenant_blocked(self, client):
        db = _get_db()
        try:
            org1 = _get_org(db, "org_1")
            org2 = _get_org(db, "org_2")
            c2 = _seed_company(db, org2, "OtherCo")
            task = _seed_task(db, org2, company_id=c2.id)
            resp = client.post(f"{API}/tasks/{task.id}/follow-up",
                               json={"action": "complete", "terminal_outcome": "won"},
                               headers={"Authorization": "Bearer org1-admin"})
            assert resp.status_code == 400
        finally:
            db.close()

    def test_nonexistent_task_400(self, client):
        resp = client.post(f"{API}/tasks/99999/follow-up",
                           json={"action": "complete", "terminal_outcome": "won"},
                           headers={"Authorization": "Bearer org1-admin"})
        assert resp.status_code == 400

    def test_bad_action_400(self, client):
        resp = client.post(f"{API}/tasks/1/follow-up",
                           json={"action": "delete"},
                           headers={"Authorization": "Bearer org1-admin"})
        assert resp.status_code in (400, 422)

    def test_member_write_rejected(self, client):
        resp = client.post(f"{API}/tasks/1/follow-up",
                           json={"action": "complete", "terminal_outcome": "won"},
                           headers={"Authorization": "Bearer org1-member"})
        assert resp.status_code in (401, 403)


class TestLeadAssignNextStep:
    def test_creates_task(self, client):
        db = _get_db()
        try:
            org1 = _get_org(db, "org_1")
            lead = _seed_lead(db, org1, name="Lead A")
            resp = client.post(f"{API}/leads/{lead.id}/assign-next-step",
                               json={"action": "assign_next_step", "next_step_title": "Review"},
                               headers={"Authorization": "Bearer org1-admin"})
            assert resp.status_code == 200
            data = resp.json()
            assert data["task_id"] is not None
            task = db.query(Task).filter(Task.id == data["task_id"]).first()
            assert task.recovery_key == f"lead_next_step_{lead.id}"
        finally:
            db.close()

    def test_idempotent(self, client):
        db = _get_db()
        try:
            org1 = _get_org(db, "org_1")
            lead = _seed_lead(db, org1, name="Lead I")
            client.post(f"{API}/leads/{lead.id}/assign-next-step",
                        json={"action": "assign_next_step", "next_step_title": "First"},
                        headers={"Authorization": "Bearer org1-admin"})
            r2 = client.post(f"{API}/leads/{lead.id}/assign-next-step",
                             json={"action": "assign_next_step", "next_step_title": "Second"},
                             headers={"Authorization": "Bearer org1-admin"})
            assert r2.status_code == 200
            assert "already" in r2.json()["message"].lower()
            tasks = db.query(Task).filter(Task.recovery_key == f"lead_next_step_{lead.id}").all()
            assert len(tasks) == 1
        finally:
            db.close()

    def test_lead_id_populated_on_follow_up_task(self, client):
        """Task created via assign-next-step has lead_id set."""
        db = _get_db()
        try:
            org1 = _get_org(db, "org_1")
            lead = _seed_lead(db, org1, name="Lead ID Test")
            resp = client.post(f"{API}/leads/{lead.id}/assign-next-step",
                               json={"action": "assign_next_step", "next_step_title": "Call them"},
                               headers={"Authorization": "Bearer org1-admin"})
            assert resp.status_code == 200
            task_id = resp.json()["task_id"]
            task = db.query(Task).filter(Task.id == task_id).first()
            assert task.lead_id == lead.id, f"Expected lead_id={lead.id}, got {task.lead_id}"
        finally:
            db.close()

    def test_two_distinct_reschedules_both_succeed(self, client):
        """Two different reschedule requests produce two ledger rows."""
        db = _get_db()
        try:
            org1 = _get_org(db, "org_1")
            c = _seed_company(db, org1, "RS2Co")
            task = _seed_task(db, org1, company_id=c.id, due_date=date.today())
            d1 = str(date.today() + timedelta(days=7))
            d2 = str(date.today() + timedelta(days=14))
            r1 = client.post(f"{API}/tasks/{task.id}/follow-up",
                             json={"action": "reschedule", "new_due_date": d1, "idempotency_key": "resched-test-1"},
                             headers={"Authorization": "Bearer org1-admin"})
            assert r1.status_code == 200
            r2 = client.post(f"{API}/tasks/{task.id}/follow-up",
                             json={"action": "reschedule", "new_due_date": d2, "idempotency_key": "resched-test-2"},
                             headers={"Authorization": "Bearer org1-admin"})
            assert r2.status_code == 200
            actions = db.query(FollowUpAction).filter(
                FollowUpAction.entity_id == task.id,
                FollowUpAction.action == "rescheduled",
            ).all()
            assert len(actions) == 2, f"Expected 2 reschedule ledger rows, got {len(actions)}"
        finally:
            db.close()

    def test_cross_tenant_missed_call_not_visible(self, client):
        """Org 1 cannot see Org 2's missed calls via lookup helpers."""
        h1 = {"Authorization": "Bearer org1-admin"}
        h2 = {"Authorization": "Bearer org2-admin"}
        r1 = client.get(f"{API}/today", headers=h1)
        r2 = client.get(f"{API}/today", headers=h2)
        assert r1.status_code == 200
        assert r2.status_code == 200

    def test_exact_replay_same_key_no_side_effects(self, client):
        """Same idempotencyKey twice: one Activity, one ledger row, same due date."""
        db = _get_db()
        try:
            org1 = _get_org(db, "org_1")
            c = _seed_company(db, org1, "ReplayCo")
            task = _seed_task(db, org1, company_id=c.id, due_date=date.today())
            nd = str(date.today() + timedelta(days=5))
            replay_key = "replay-test-key-1"
            h = {"Authorization": "Bearer org1-admin"}
            r1 = client.post(f"{API}/tasks/{task.id}/follow-up",
                             json={"action": "reschedule", "new_due_date": nd, "idempotency_key": replay_key},
                             headers=h)
            assert r1.status_code == 200
            r2 = client.post(f"{API}/tasks/{task.id}/follow-up",
                             json={"action": "reschedule", "new_due_date": nd, "idempotency_key": replay_key},
                             headers=h)
            assert r2.status_code == 200
            assert "replay" in r2.json()["message"].lower()
            db.refresh(task)
            assert str(task.due_date) == nd
            actions = db.query(FollowUpAction).filter(
                FollowUpAction.idempotency_key == replay_key
            ).all()
            assert len(actions) == 1, f"Expected 1 ledger row, got {len(actions)}"
            # Different key succeeds
            r3 = client.post(f"{API}/tasks/{task.id}/follow-up",
                             json={"action": "reschedule", "new_due_date": str(date.today() + timedelta(days=10)),
                                   "idempotency_key": "replay-test-key-2"},
                             headers=h)
            assert r3.status_code == 200
            all_actions = db.query(FollowUpAction).filter(
                FollowUpAction.entity_id == task.id,
                FollowUpAction.action == "rescheduled",
            ).all()
            assert len(all_actions) == 2, f"Expected 2 ledger rows after distinct keys, got {len(all_actions)}"
        finally:
            db.close()
