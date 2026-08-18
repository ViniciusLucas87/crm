from tests.conftest import auth_headers


def test_factory_portfolio_is_seeded_and_organization_scoped(client):
    response = client.get("/api/v1/app-factory/portfolio", headers=auth_headers("org1-admin"))
    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["problems_researched"] >= 20
    assert payload["summary"]["qualified_for_build"] == 0
    assert payload["guardrails"]["automatic_production_release"] is False
    never_forget = next(item for item in payload["candidates"] if item["slug"] == "never-forget")
    assert never_forget["total_score"] >= 75
    assert never_forget["evidence_count"] >= 3
    assert never_forget["eligible_for_validation"] is True
    assert never_forget["eligible_for_build"] is False

    other = client.get("/api/v1/app-factory/portfolio", headers=auth_headers("org2-admin"))
    assert other.status_code == 200
    assert other.json()["summary"]["problems_researched"] >= 20


def test_experiment_gate_rejects_unqualified_candidate(client):
    portfolio = client.get(
        "/api/v1/app-factory/portfolio", headers=auth_headers("org1-admin")
    ).json()
    candidate = next(item for item in portfolio["candidates"] if item["evidence_count"] == 0)
    response = client.post(
        "/api/v1/app-factory/experiments",
        headers=auth_headers("org1-admin"),
        json={
            "candidate_id": candidate["id"],
            "name": "Unqualified experiment",
            "hypothesis": "This must be rejected because the evidence gate is incomplete.",
            "channel": "search",
            "success_metric": "At least five qualified purchase intent actions.",
            "spend_limit_cents": 500,
        },
    )
    assert response.status_code == 409


def test_member_cannot_create_factory_experiment(client):
    portfolio = client.get(
        "/api/v1/app-factory/portfolio", headers=auth_headers("org1-admin")
    ).json()
    candidate = next(item for item in portfolio["candidates"] if item["slug"] == "never-forget")
    response = client.post(
        "/api/v1/app-factory/experiments",
        headers=auth_headers("org1-member"),
        json={
            "candidate_id": candidate["id"],
            "name": "Never Forget purchase intent",
            "hypothesis": "Contractors will request a pilot at the proposed entry price.",
            "channel": "opt in landing page",
            "success_metric": "Five qualified pilot requests from fifty targeted visits.",
            "spend_limit_cents": 1000,
        },
    )
    assert response.status_code == 403
