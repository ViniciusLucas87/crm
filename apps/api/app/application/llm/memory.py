"""
Conversation Memory System.

Session-scoped memory that references CRM entities.
Never persists hallucinated information — only references
to verified CRM records (company IDs, opportunity IDs, etc.).
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class MemoryEntry:
    role: Literal["user", "assistant", "tool", "system"]
    content: str
    timestamp: float = field(default_factory=time.time)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    references: dict[str, list[int]] = field(default_factory=dict)  # e.g., {"company": [1, 3], "opportunity": [5]}


@dataclass
class ConversationMemory:
    """
    Conversation-scoped memory.

    Tracks:
    - Message history (user, assistant, tool, system)
    - Referenced CRM entities (for context retrieval)
    - Active context (current company, opportunity, meeting)
    - Tool execution history
    """

    session_id: str
    messages: list[MemoryEntry] = field(default_factory=list)
    active_company_id: int | None = None
    active_opportunity_id: int | None = None
    referenced_companies: set[int] = field(default_factory=set)
    referenced_opportunities: set[int] = field(default_factory=set)
    tool_executions: list[dict[str, Any]] = field(default_factory=list)
    max_messages: int = 50
    created_at: float = field(default_factory=time.time)

    def add_message(
        self,
        role: Literal["user", "assistant", "tool", "system"],
        content: str,
        tool_calls: list[dict[str, Any]] | None = None,
        references: dict[str, list[int]] | None = None,
    ) -> None:
        entry = MemoryEntry(
            role=role,
            content=content,
            tool_calls=tool_calls or [],
            references=references or {},
        )
        self.messages.append(entry)

        # Track references
        if references:
            if "company" in references:
                self.referenced_companies.update(references["company"])
            if "opportunity" in references:
                self.referenced_opportunities.update(references["opportunity"])

        # Trim old messages
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]

    def add_tool_execution(self, tool_name: str, arguments: dict[str, Any], result: Any) -> None:
        self.tool_executions.append({
            "tool": tool_name,
            "arguments": arguments,
            "result_summary": str(result)[:500],
            "timestamp": time.time(),
        })

    def set_active_company(self, company_id: int) -> None:
        self.active_company_id = company_id
        self.referenced_companies.add(company_id)

    def set_active_opportunity(self, opportunity_id: int) -> None:
        self.active_opportunity_id = opportunity_id
        self.referenced_opportunities.add(opportunity_id)

    def get_context_summary(self) -> dict[str, Any]:
        """Get a summary of the current conversation context for the LLM."""
        return {
            "session_id": self.session_id,
            "message_count": len(self.messages),
            "active_company_id": self.active_company_id,
            "active_opportunity_id": self.active_opportunity_id,
            "referenced_companies": list(self.referenced_companies),
            "referenced_opportunities": list(self.referenced_opportunities),
            "recent_tools_used": [t["tool"] for t in self.tool_executions[-5:]],
        }

    def to_llm_messages(self, system_prompt: str = "") -> list[dict[str, Any]]:
        """Convert memory to LLM-compatible message format."""
        messages: list[dict[str, Any]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        for entry in self.messages:
            msg: dict[str, Any] = {"role": entry.role, "content": entry.content}
            if entry.tool_calls:
                msg["tool_calls"] = entry.tool_calls
            messages.append(msg)

        return messages

    def clear(self) -> None:
        self.messages.clear()
        self.tool_executions.clear()
        self.referenced_companies.clear()
        self.referenced_opportunities.clear()
        self.active_company_id = None
        self.active_opportunity_id = None


# ── Session Store ──

class MemoryStore:
    """In-memory session store for conversation memories."""

    def __init__(self, ttl_seconds: int = 3600) -> None:
        self._sessions: dict[str, ConversationMemory] = {}
        self._ttl = ttl_seconds

    def get_or_create(self, session_id: str) -> ConversationMemory:
        if session_id not in self._sessions:
            self._sessions[session_id] = ConversationMemory(session_id=session_id)
        return self._sessions[session_id]

    def get(self, session_id: str) -> ConversationMemory | None:
        return self._sessions.get(session_id)

    def delete(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def cleanup_expired(self) -> int:
        now = time.time()
        expired = [sid for sid, mem in self._sessions.items() if now - mem.created_at > self._ttl]
        for sid in expired:
            del self._sessions[sid]
        return len(expired)


# ── Global instance ──

_memory_store: MemoryStore | None = None


def get_memory_store() -> MemoryStore:
    global _memory_store
    if _memory_store is None:
        _memory_store = MemoryStore()
    return _memory_store
