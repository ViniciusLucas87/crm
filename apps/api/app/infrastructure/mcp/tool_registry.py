"""
MCP Tool Registry.

Central registry for all MCP tools. Each tool has:
- name: unique identifier
- description: what the tool does (for LLM consumption)
- parameters: JSON Schema for input
- handler: async callable that executes the tool
- category: logical grouping

The LLM only sees tool names, descriptions, and parameter schemas.
It never sees implementation details, SQL, or repository internals.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolParameter:
    name: str
    type: str  # "string", "integer", "number", "boolean", "array", "object"
    description: str
    required: bool = False
    default: Any = None
    enum: list[str] | None = None


@dataclass
class ToolDefinition:
    name: str
    description: str
    category: str
    parameters: list[ToolParameter] = field(default_factory=list)
    handler: Callable[..., Any] | None = None
    read_only: bool = True
    destructive: bool = False
    external_side_effect: bool = False

    def to_mcp_schema(self) -> dict[str, Any]:
        """Convert to MCP-compatible JSON Schema for tool listing."""
        properties: dict[str, dict[str, Any]] = {}
        required: list[str] = []

        for p in self.parameters:
            prop: dict[str, Any] = {"type": p.type, "description": p.description}
            if p.enum:
                prop["enum"] = p.enum
            if p.default is not None:
                prop["default"] = p.default
            properties[p.name] = prop
            if p.required:
                required.append(p.name)

        input_schema: dict[str, Any] = {"type": "object", "properties": properties}
        if required:
            input_schema["required"] = required

        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": input_schema,
            "annotations": {
                "readOnlyHint": self.read_only,
                "destructiveHint": self.destructive,
                "openWorldHint": self.external_side_effect,
            },
        }

    def to_openai_function(self) -> dict[str, Any]:
        """Convert to OpenAI function-calling format."""
        properties: dict[str, dict[str, Any]] = {}
        required: list[str] = []

        for p in self.parameters:
            prop: dict[str, Any] = {"type": p.type, "description": p.description}
            if p.enum:
                prop["enum"] = p.enum
            properties[p.name] = prop
            if p.required:
                required.append(p.name)

        params: dict[str, Any] = {"type": "object", "properties": properties}
        if required:
            params["required"] = required

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": params,
            },
        }


class ToolRegistry:
    """Central registry for all MCP tools."""

    def __init__(self, *, organization_id: int | None = None) -> None:
        self._tools: dict[str, ToolDefinition] = {}
        self.organization_id = organization_id

    def register(self, tool: ToolDefinition) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered.")
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def list_all(self) -> list[ToolDefinition]:
        return list(self._tools.values())

    def list_by_category(self, category: str) -> list[ToolDefinition]:
        return [t for t in self._tools.values() if t.category == category]

    def list_mcp_schemas(self) -> list[dict[str, Any]]:
        return [t.to_mcp_schema() for t in self._tools.values()]

    def list_openai_functions(self) -> list[dict[str, Any]]:
        return [t.to_openai_function() for t in self._tools.values()]

    async def execute(self, tool_name: str, **kwargs: Any) -> dict[str, Any]:
        tool = self._tools.get(tool_name)
        if tool is None:
            return {"error": f"Unknown tool: {tool_name}"}
        if tool.handler is None:
            return {"error": f"Tool '{tool_name}' has no handler."}

        try:
            result = tool.handler(**kwargs)
            # Support both sync and async handlers
            import inspect
            if inspect.iscoroutine(result):
                result = await result
            return {"result": result, "tool": tool_name}
        except Exception as e:
            return {"error": str(e), "tool": tool_name}


# ── Global registry instance ──

_registry: ToolRegistry | None = None


def get_registry() -> ToolRegistry:
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry


def reset_registry() -> None:
    global _registry
    _registry = ToolRegistry()
