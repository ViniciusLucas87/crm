from conftest import auth_headers
from fastapi.testclient import TestClient


def test_companies_crud_lifecycle(client: TestClient) -> None:
    create_payload = {
        "name": "Acme Construction",
        "industry": "Construction",
        "website": "https://acme.test",
        "owner": "vinidias@pacificnorthsystems.com",
    }

    created = client.post(
        "/api/v1/companies", json=create_payload, headers=auth_headers("org1-admin")
    )
    assert created.status_code == 200
    company_id = created.json()["id"]

    listed = client.get("/api/v1/companies", headers=auth_headers("org1-admin"))
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    updated = client.patch(
        f"/api/v1/companies/{company_id}",
        json={"employees": 42},
        headers=auth_headers("org1-admin"),
    )
    assert updated.status_code == 200
    assert updated.json()["employees"] == 42

    archived = client.delete(
        f"/api/v1/companies/{company_id}", headers=auth_headers("org1-admin")
    )
    assert archived.status_code == 200
    assert archived.json()["is_archived"] is True

    restored = client.post(
        f"/api/v1/companies/{company_id}/restore", headers=auth_headers("org1-admin")
    )
    assert restored.status_code == 200
    assert restored.json()["is_archived"] is False

    duplicated = client.post(
        f"/api/v1/companies/{company_id}/duplicate", headers=auth_headers("org1-admin")
    )
    assert duplicated.status_code == 200
    assert duplicated.json()["name"].endswith("(Copy)")

    filtered = client.get(
        "/api/v1/companies",
        params={"search": "Acme", "page": 1, "page_size": 10},
        headers=auth_headers("org1-admin"),
    )
    assert filtered.status_code == 200
    assert filtered.json()["total"] >= 2


def test_companies_forbid_member_write_access(client: TestClient) -> None:
    response = client.post(
        "/api/v1/companies",
        json={"name": "Blocked Company"},
        headers=auth_headers("org1-member"),
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"


def test_companies_are_isolated_by_organization(client: TestClient) -> None:
    created = client.post(
        "/api/v1/companies",
        json={"name": "Org One Company"},
        headers=auth_headers("org1-admin"),
    )
    assert created.status_code == 200
    company_id = created.json()["id"]

    foreign_list = client.get("/api/v1/companies", headers=auth_headers("org2-admin"))
    assert foreign_list.status_code == 200
    assert foreign_list.json()["total"] == 0

    foreign_get = client.get(
        f"/api/v1/companies/{company_id}", headers=auth_headers("org2-admin")
    )
    assert foreign_get.status_code == 404
