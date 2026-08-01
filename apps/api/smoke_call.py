"""Explicit, opt-in telephony smoke test for local development only."""

import os


def main() -> None:
    target_number = os.getenv("PNS_SMOKE_CALL_NUMBER", "").strip()
    if not target_number:
        raise SystemExit("Set PNS_SMOKE_CALL_NUMBER to run the opt-in call smoke test.")

    os.environ.setdefault("CLERK_ISSUER", "https://clerk.test")
    os.environ.setdefault("CLERK_JWKS_URL", "https://clerk.test/.well-known/jwks.json")

    from fastapi.testclient import TestClient

    from app.infrastructure.auth import clerk as clerk_auth
    from app.main import app

    token_claims = {
        "test-token": {
            "sub": "u1",
            "email": "admin@pacificnorthsystems.com",
            "name": "Test Admin",
            "org_id": "org_1",
            "org_slug": "pacific-north-systems",
            "org_name": "Pacific North Systems",
            "org_role": "admin",
        }
    }
    clerk_auth._decode_clerk_token = lambda token: token_claims.get(token, {})
    client = TestClient(app)
    headers = {"Authorization": "Bearer test-token"}

    response = client.post(
        f"/api/v1/telephony/call?company_id=1&phone_number={target_number}",
        headers=headers,
    )
    print(f"Status: {response.status_code}")
    print(f"Body: {response.text[:500]}")


if __name__ == "__main__":
    main()
