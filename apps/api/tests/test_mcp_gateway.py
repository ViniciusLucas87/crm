import json

from fastapi.testclient import TestClient

from tests.conftest import auth_headers


def rpc(method: str, params: dict | None = None, request_id: int = 1) -> dict:
    return {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params or {}}


def test_mcp_initializes_with_tools_resources_prompts_and_instructions(client: TestClient) -> None:
    response = client.post(
        "/api/v1/mcp",
        headers=auth_headers("org1-admin"),
        json=rpc("initialize", {"protocolVersion": "2024-11-05"}),
    )
    assert response.status_code == 200
    result = response.json()["result"]
    assert result["serverInfo"]["name"] == "Pacific North Systems MCP Server"
    assert set(result["capabilities"]) == {"tools", "resources", "prompts"}
    assert "business_context" in result["instructions"]


def test_mcp_registry_is_repeatable_and_marks_write_tools(client: TestClient) -> None:
    first = client.post("/api/v1/mcp", headers=auth_headers("org1-admin"), json=rpc("tools/list"))
    second = client.post("/api/v1/mcp", headers=auth_headers("org1-admin"), json=rpc("tools/list", request_id=2))
    assert first.status_code == 200
    assert second.status_code == 200
    tools = first.json()["result"]["tools"]
    assert len(tools) == len(second.json()["result"]["tools"])
    by_name = {tool["name"]: tool for tool in tools}
    assert by_name["business_context"]["annotations"]["readOnlyHint"] is True
    assert by_name["create_task"]["annotations"]["readOnlyHint"] is False


def test_mcp_context_resource_and_controlled_write(client: TestClient) -> None:
    create = client.post(
        "/api/v1/mcp",
        headers=auth_headers("org1-admin"),
        json=rpc("tools/call", {"name": "create_company", "arguments": {"name": "MCP Test Company"}}),
    )
    assert create.status_code == 200
    assert create.json()["error"] is None, create.json()
    payload = json.loads(create.json()["result"]["content"][0]["text"])
    assert payload["result"]["name"] == "MCP Test Company"

    context = client.post(
        "/api/v1/mcp",
        headers=auth_headers("org1-admin"),
        json=rpc("resources/read", {"uri": "pns://crm/context"}, request_id=2),
    )
    assert context.status_code == 200
    resource = json.loads(context.json()["result"]["contents"][0]["text"])
    assert resource["result"]["summary"]["companies"] == 1


def test_private_service_token_authenticates_without_clerk_token(client: TestClient, monkeypatch) -> None:
    client.post("/api/v1/mcp", headers=auth_headers("org1-admin"), json=rpc("initialize"))
    monkeypatch.setenv("PNS_CRM_MCP_TOKEN", "private-test-token")
    response = client.post(
        "/api/v1/mcp",
        headers={"Authorization": "Bearer private-test-token"},
        json=rpc("ping"),
    )
    assert response.status_code == 200
    assert response.json()["result"] == {"pong": True}


def test_mcp_rejects_missing_authentication(client: TestClient) -> None:
    response = client.post("/api/v1/mcp", json=rpc("tools/list"))
    assert response.status_code == 401
