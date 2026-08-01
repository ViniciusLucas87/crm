"""
AI Agent Registry.

Central registry for all AI agents. Each agent is a named,
configured workflow with:
- System prompt defining its role
- Authorized MCP tools it can call
- Safety classification
- Execution constraints
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AgentSafety(str, Enum):
    SAFE = "safe"                # Can run autonomously
    NEEDS_APPROVAL = "approval"   # Some actions need human approval
    RESTRICTED = "restricted"     # Always needs approval


@dataclass
class AgentDefinition:
    """Defines an AI agent — its identity, mission, tools, and constraints."""
    name: str
    version: str
    description: str
    mission: str
    system_prompt: str
    category: str  # "research", "sales", "operations", "outreach"
    safety: AgentSafety = AgentSafety.SAFE
    authorized_tools: list[str] = field(default_factory=list)
    max_iterations: int = 10
    temperature: float = 0.3
    requires_context: list[str] = field(default_factory=list)  # e.g. ["company", "contacts"]
    output_schema: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name, "version": self.version,
            "description": self.description, "mission": self.mission,
            "category": self.category, "safety": self.safety.value,
            "authorized_tools": self.authorized_tools,
            "max_iterations": self.max_iterations,
        }


class AgentRegistry:
    """Central registry for all AI agents."""

    def __init__(self) -> None:
        self._agents: dict[str, AgentDefinition] = {}

    def register(self, agent: AgentDefinition) -> None:
        if agent.name in self._agents:
            raise ValueError(f"Agent '{agent.name}' already registered.")
        self._agents[agent.name] = agent

    def get(self, name: str) -> AgentDefinition | None:
        return self._agents.get(name)

    def list_all(self) -> list[AgentDefinition]:
        return list(self._agents.values())

    def list_by_category(self, category: str) -> list[AgentDefinition]:
        return [a for a in self._agents.values() if a.category == category]

    def list_safe(self) -> list[AgentDefinition]:
        return [a for a in self._agents.values() if a.safety == AgentSafety.SAFE]


# ── Global registry ──

_agent_registry: AgentRegistry | None = None


def get_agent_registry() -> AgentRegistry:
    global _agent_registry
    if _agent_registry is None:
        _agent_registry = AgentRegistry()
    return _agent_registry


def reset_agent_registry() -> None:
    global _agent_registry
    _agent_registry = AgentRegistry()
