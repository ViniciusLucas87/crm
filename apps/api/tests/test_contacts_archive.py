from conftest import auth_headers


def test_archived_contacts_are_hidden_by_default(client):
    headers = auth_headers("org1-admin")
    company = client.post("/api/v1/companies", json={"name": "Contact Test Co"}, headers=headers)
    assert company.status_code == 200
    company_id = company.json()["id"]

    contact = client.post(
        "/api/v1/contacts",
        json={"company_id": company_id, "first_name": "Test", "last_name": "Contact"},
        headers=headers,
    )
    assert contact.status_code == 200
    contact_id = contact.json()["id"]

    archived = client.delete(f"/api/v1/contacts/{contact_id}", headers=headers)
    assert archived.status_code == 200

    active = client.get("/api/v1/contacts", params={"company_id": company_id}, headers=headers)
    assert active.status_code == 200
    assert active.json()["items"] == []

    all_contacts = client.get(
        "/api/v1/contacts",
        params={"company_id": company_id, "include_archived": True},
        headers=headers,
    )
    assert all_contacts.status_code == 200
    assert all_contacts.json()["items"][0]["status"] == "archived"
