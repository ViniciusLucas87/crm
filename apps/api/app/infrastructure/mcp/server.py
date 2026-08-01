"""
MCP Server — Model Context Protocol Server.

Exposes application tools to LLM consumers via JSON-RPC over HTTP/SSE.
The LLM communicates only through this server — never touches the database.

Endpoints:
- POST /mcp/message    — JSON-RPC message handling
- GET  /mcp/sse        — SSE streaming endpoint
- GET  /mcp/tools      — List all available tools
"""

import asyncio
import json
import time
from collections.abc import AsyncGenerator
from typing import Any

from pydantic import BaseModel

from app.infrastructure.mcp.tool_registry import ToolRegistry


class JSONRPCRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: str | int | None = None
    method: str
    params: dict[str, Any] | None = None


class JSONRPCResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: str | int | None = None
    result: Any | None = None
    error: dict[str, Any] | None = None


class MCPServer:
    """
    MCP Server implementation.

    Supports:
    - JSON-RPC 2.0 request/response
    - Server-Sent Events (SSE) for streaming
    - tools/list, tools/call, initialize methods
    """

    SERVER_INFO = {
        "name": "Pacific North Systems MCP Server",
        "version": "1.0.0",
        "protocolVersion": "2024-11-05",
    }

    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry

    async def handle_message(self, message: dict[str, Any]) -> dict[str, Any]:
        """Handle a JSON-RPC message."""
        try:
            req = JSONRPCRequest(**message)
        except Exception as e:
            return JSONRPCResponse(id=None, error={"code": -32700, "message": f"Parse error: {e}"}).model_dump()

        method_handlers = {
            "initialize": self._handle_initialize,
            "tools/list": self._handle_list_tools,
            "tools/call": self._handle_call_tool,
            "ping": self._handle_ping,
        }

        handler = method_handlers.get(req.method)
        if handler is None:
            return JSONRPCResponse(id=req.id, error={"code": -32601, "message": f"Method not found: {req.method}"}).model_dump()

        try:
            result = await handler(req.params or {})
            return JSONRPCResponse(id=req.id, result=result).model_dump()
        except Exception as e:
            return JSONRPCResponse(id=req.id, error={"code": -32603, "message": str(e)}).model_dump()

    async def _handle_initialize(self, params: dict[str, Any]) -> dict[str, Any]:
        return {
            "protocolVersion": self.SERVER_INFO["protocolVersion"],
            "serverInfo": self.SERVER_INFO,
            "capabilities": {"tools": {}},
        }

    async def _handle_list_tools(self, params: dict[str, Any]) -> dict[str, Any]:
        return {"tools": self._registry.list_mcp_schemas()}

    async def _handle_call_tool(self, params: dict[str, Any]) -> dict[str, Any]:
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        result = await self._registry.execute(tool_name, **arguments)
        return {"content": [{"type": "text", "text": json.dumps(result, default=str)}]}

    async def _handle_ping(self, params: dict[str, Any]) -> dict[str, Any]:
        return {"pong": True}

    async def stream_response(self, message: dict[str, Any]) -> AsyncGenerator[str, None]:
        """Generate SSE stream for a JSON-RPC message."""
        response = await self.handle_message(message)
        yield f"data: {json.dumps(response, default=str)}\n\n"
        yield "data: [DONE]\n\n"

    async def stream_tool_call(self, tool_name: str, arguments: dict[str, Any]) -> AsyncGenerator[str, None]:
        """Stream a tool call execution as SSE events."""
        yield f"event: tool_start\ndata: {json.dumps({'tool': tool_name, 'arguments': arguments})}\n\n"
        await asyncio.sleep(0.01)

        try:
            result = await self._registry.execute(tool_name, **arguments)
            yield f"event: tool_result\ndata: {json.dumps(result, default=str)}\n\n"
        except Exception as e:
            yield f"event: tool_error\ndata: {json.dumps({'error': str(e)})}\n\n"

        yield f"event: tool_end\ndata: {json.dumps({'tool': tool_name, 'status': 'complete'})}\n\n"
        yield "data: [DONE]\n\n"
