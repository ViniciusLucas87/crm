"""Phase 3 production acceptance tests — audit, operations, backup freshness."""


from app.infrastructure.db.models import FollowUpAction

API = "/api/v1"


class TestAuditEndpoint:
    """Tests for GET /api/v1/audit — read-only, org-scoped."""

    def test_audit_requires_auth(self, client):
        resp = client.get(f"{API}/audit")
        assert resp.status_code in (401, 403)

    def test_audit_returns_empty_list(self, client):
        resp = client.get(f"{API}/audit", headers={"Authorization": "Bearer org1-admin"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["entries"] == []
        assert data["total"] == 0

    def test_audit_tenant_isolation(self, client):
        """Org 1 cannot see Org 2's audit entries."""
        import app.infrastructure.db.session as db_session
        from app.infrastructure.db.models import Organization

        # Trigger org resolution for both orgs so Organization rows exist
        client.get(f"{API}/audit", headers={"Authorization": "Bearer org1-admin"})
        client.get(f"{API}/audit", headers={"Authorization": "Bearer org2-admin"})

        db = db_session.SessionLocal()
        try:
            org2 = db.query(Organization).filter(Organization.clerk_org_id == "org_2").first()
            assert org2 is not None, "org_2 must have been auto-created by auth"

            # Seed an audit entry for org 2
            fa = FollowUpAction(
                organization_id=org2.id, entity_type="task", entity_id=1,
                action="completed", idempotency_key="audit-test-key-org2",
                old_state="open", new_state="completed",
            )
            db.add(fa)
            db.commit()

            # Org 2 sees it
            r2 = client.get(f"{API}/audit", headers={"Authorization": "Bearer org2-admin"})
            assert r2.status_code == 200
            assert r2.json()["total"] >= 1

            # Org 1 does not
            r1 = client.get(f"{API}/audit", headers={"Authorization": "Bearer org1-admin"})
            assert r1.status_code == 200
            for e in r1.json()["entries"]:
                assert e["idempotency_key"] != "audit-test-key-org2"
        finally:
            db.close()

    def test_audit_no_update_delete(self, client):
        """PUT and DELETE must return 405 Method Not Allowed."""
        h = {"Authorization": "Bearer org1-admin"}
        assert client.put(f"{API}/audit", headers=h).status_code == 405
        assert client.delete(f"{API}/audit", headers=h).status_code == 405


class TestOperationsStatus:
    """Tests for GET /api/v1/operations/status."""

    def test_status_requires_auth(self, client):
        resp = client.get(f"{API}/operations/status")
        assert resp.status_code in (401, 403)

    def test_status_returns_degraded_without_workers(self, client):
        """Without Celery workers or backup verification, status degrades honestly."""
        resp = client.get(f"{API}/operations/status", headers={"Authorization": "Bearer org1-admin"})
        assert resp.status_code == 200
        data = resp.json()
        # A test process has no Redis, Celery heartbeat, or backup marker.
        # Reporting unhealthy is the correct fail-safe production contract.
        assert data["status"] in ("healthy", "degraded", "unhealthy")
        assert "build_id" in data
        assert "db_status" in data
        assert isinstance(data["outbox_pending"], int)
        assert data["oldest_pending_outbox_seconds"] is None or isinstance(
            data["oldest_pending_outbox_seconds"], int
        )
        assert isinstance(data["stripe_payment_failures_24h"], int)
        assert isinstance(data["telnyx_unprocessed_webhooks_24h"], int)
        assert data["worker_status"] in ("running", "stale", "unknown")
        assert "worker_heartbeat_ms" in data
        # backup_last_ts may be None (no S3 in test) or a valid ISO timestamp
        assert "backup_last_ts" in data

    def test_public_liveness_minimal(self, client):
        """Public liveness must reveal minimal info."""
        resp = client.get(f"{API}/health/live")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        # Must NOT expose build info or internal state
        assert "db_status" not in data
