def _auth(token: str = "org1-admin") -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_authorized_sender_status_and_queued_outreach(client, monkeypatch):
    monkeypatch.setenv("SMTP_USER", "sender@pacificnorthsystems.com")
    monkeypatch.setenv("SMTP_PASS", "app-password")
    monkeypatch.setenv("SMTP_FROM_EMAIL", "hello@pacificnorthsystems.com")

    status = client.get("/api/v1/outreach-email/sender-status", headers=_auth())
    assert status.status_code == 200
    assert status.json()["configured"] is True
    assert status.json()["daily_cap"] == 10

    queued = client.post(
        "/api/v1/outreach-email/send",
        headers=_auth(),
        json={
            "contact_email": "owner@example.ca",
            "contact_name": "Alex Owner",
            "subject": "Question about missed customer calls",
            "body_text": "Hi Alex, I saw your public note about missing calls while on site. Never Miss can send a reply after an unanswered call and keep a callback task visible. Would a short conversation be useful? If this is not relevant, reply opt out.",
            "source_platform": "reddit",
            "source_url": "https://www.reddit.com/r/example/comments/123",
            "public_evidence": "Public post says calls are missed while working on site.",
            "email_source": "Public business contact page: https://example.ca/contact",
        },
    )
    assert queued.status_code == 202
    assert queued.json()["status"] == "queued"


def test_outreach_requires_opt_out(client, monkeypatch):
    monkeypatch.setenv("SMTP_USER", "sender@pacificnorthsystems.com")
    monkeypatch.setenv("SMTP_PASS", "app-password")
    monkeypatch.setenv("SMTP_FROM_EMAIL", "hello@pacificnorthsystems.com")
    response = client.post(
        "/api/v1/outreach-email/send",
        headers=_auth(),
        json={
            "contact_email": "owner@example.ca",
            "contact_name": "Alex Owner",
            "subject": "Question about missed customer calls",
            "body_text": "Hi Alex, I saw your public note about missing calls while on site. Never Miss can send a reply after an unanswered call and keep a callback task visible. Would a short conversation be useful?",
            "source_platform": "reddit",
            "source_url": "https://www.reddit.com/r/example/comments/123",
            "public_evidence": "Public post says calls are missed while working on site.",
            "email_source": "Public business contact page: https://example.ca/contact",
        },
    )
    assert response.status_code == 422


def test_outreach_blocks_already_queued_address(client, monkeypatch):
    monkeypatch.setenv("SMTP_USER", "sender@pacificnorthsystems.com")
    monkeypatch.setenv("SMTP_PASS", "app-password")
    monkeypatch.setenv("SMTP_FROM_EMAIL", "hello@pacificnorthsystems.com")
    body = {
        "contact_email": "owner@example.ca",
        "contact_name": "Alex Owner",
        "subject": "Question about missed customer calls",
        "body_text": "Hi Alex, I saw your public note about missing calls while on site. Never Miss can send a reply after an unanswered call and keep a callback task visible. Would a short conversation be useful? If this is not relevant, reply opt out.",
        "source_platform": "reddit",
        "source_url": "https://www.reddit.com/r/example/comments/123",
        "public_evidence": "Public post says calls are missed while working on site.",
        "email_source": "Public business contact page: https://example.ca/contact",
    }
    assert client.post("/api/v1/outreach-email/send", headers=_auth(), json=body).status_code == 202
    duplicate = client.post("/api/v1/outreach-email/send", headers=_auth(), json=body)
    assert duplicate.status_code == 409


def test_outreach_cap_counts_pending_queue_items(client, monkeypatch):
    monkeypatch.setenv("SMTP_USER", "sender@pacificnorthsystems.com")
    monkeypatch.setenv("SMTP_PASS", "app-password")
    monkeypatch.setenv("SMTP_FROM_EMAIL", "hello@pacificnorthsystems.com")
    for index in range(10):
        response = client.post(
            "/api/v1/outreach-email/send",
            headers=_auth(),
            json={
                "contact_email": f"owner{index}@example.ca",
                "contact_name": f"Owner {index}",
                "subject": "Question about missed customer calls",
                "body_text": "Hi there, I saw your public note about missing calls while on site. Never Miss can send a reply after an unanswered call and keep a callback task visible. Would a short conversation be useful? If this is not relevant, reply opt out.",
                "source_platform": "reddit",
                "source_url": f"https://www.reddit.com/r/example/comments/{index}",
                "public_evidence": "Public post says calls are missed while working on site.",
                "email_source": "Public business contact page: https://example.ca/contact",
            },
        )
        assert response.status_code == 202

    capped = client.post(
        "/api/v1/outreach-email/send",
        headers=_auth(),
        json={
            "contact_email": "overflow@example.ca",
            "contact_name": "Overflow Owner",
            "subject": "Question about missed customer calls",
            "body_text": "Hi there, I saw your public note about missing calls while on site. Never Miss can send a reply after an unanswered call and keep a callback task visible. Would a short conversation be useful? If this is not relevant, reply opt out.",
            "source_platform": "reddit",
            "source_url": "https://www.reddit.com/r/example/comments/overflow",
            "public_evidence": "Public post says calls are missed while working on site.",
            "email_source": "Public business contact page: https://example.ca/contact",
        },
    )
    assert capped.status_code == 429
