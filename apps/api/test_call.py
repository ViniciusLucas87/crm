"""Quick telephony smoke test — call 7786786568."""
import os

os.environ["CLERK_ISSUER"] = "https://clerk.test"
os.environ["CLERK_JWKS_URL"] = "https://clerk.test/.well-known/jwks.json"

from app.infrastructure.auth import clerk as clerk_auth
from app.main import app
from fastapi.testclient import TestClient

TOKEN_CLAIMS = {
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

clerk_auth._decode_clerk_token = lambda t: TOKEN_CLAIMS.get(t, {})
client = TestClient(app)

# Step 1: Check telephony status
print("=== TELEPHONY STATUS ===")
r = client.get("/api/v1/telephony/status")
print(f"Status: {r.status_code}")
print(f"Body: {r.text}")

# Step 2: Register browser
print("\n=== REGISTER BROWSER ===")
r = client.post("/api/v1/telephony/register", headers={"Authorization": "Bearer test-token"})
print(f"Status: {r.status_code}")
print(f"Body: {r.text[:300]}")

# Step 3: Make the call
print("\n=== MAKE CALL to 7786786568 ===")
r = client.post(
    "/api/v1/telephony/call?company_id=1&phone_number=7786786568",
    headers={"Authorization": "Bearer test-token"},
)
print(f"Status: {r.status_code}")
print(f"Body: {r.text[:500]}")

# Step 4: List calls
print("\n=== LIST CALLS ===")
r = client.get("/api/v1/telephony/calls", headers={"Authorization": "Bearer test-token"})
print(f"Status: {r.status_code}")
print(f"Body: {r.text[:500]}")

# Step 5: Conversation check
print("\n=== CONVERSATIONS ===")
r = client.get("/api/v1/conversations?company_id=1", headers={"Authorization": "Bearer test-token"})
print(f"Status: {r.status_code}")
print(f"Body: {r.text[:300]}")
