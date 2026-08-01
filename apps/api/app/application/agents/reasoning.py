"""
Reasoning Engine & Approval Workflow.

Reasoning Engine: Chain-of-thought reasoning with tool selection.
Approval Workflow: Classifies actions as safe/needs_approval.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ── Reasoning Engine ──

class ActionType(str, Enum):
    TOOL_CALL = "tool_call"
    RESPOND = "respond"
    ASK_USER = "ask_user"
    COMPLETE = "complete"


@dataclass
class ReasoningStep:
    """A single step in the agent's reasoning chain."""
    thought: str
    action_type: ActionType
    action: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    requires_approval: bool = False


@dataclass
class ReasoningTrace:
    """Full reasoning trace for explainability."""
    agent_name: str
    goal: str
    steps: list[ReasoningStep] = field(default_factory=list)
    final_answer: str = ""
    tools_called: list[str] = field(default_factory=list)

    def add_step(self, step: ReasoningStep) -> None:
        self.steps.append(step)
        if step.action_type == ActionType.TOOL_CALL:
            self.tools_called.append(step.action.get("tool", "unknown"))

    def to_audit_log(self) -> dict[str, Any]:
        return {
            "agent": self.agent_name,
            "goal": self.goal,
            "reasoning_steps": [
                {"thought": s.thought, "action": s.action_type.value, "confidence": s.confidence}
                for s in self.steps
            ],
            "tools_called": self.tools_called,
            "final_answer": self.final_answer[:500],
        }


class ReasoningEngine:
    """
    Chain-of-thought reasoning engine.

    Generates reasoning steps that the executor follows.
    Each step has: thought → action → observation → next thought.
    """

    @staticmethod
    def build_tool_selection_prompt(tools: list[dict[str, Any]], goal: str, context: str) -> str:
        """Build a prompt that helps the LLM select the right tools."""
        tool_descriptions = "\n".join(
            f"- {t.get('function', t).get('name', t.get('name', 'unknown'))}: {t.get('function', t).get('description', t.get('description', ''))}"
            for t in tools
        )
        return f"""You are an AI agent with access to the following tools:

{tool_descriptions}

Goal: {goal}

Context: {context}

Think step by step:
1. What information do I need?
2. Which tool provides that information?
3. What should I do with the result?

Plan your approach, then execute tools one at a time."""

    @staticmethod
    def classify_action(tool_name: str) -> ActionType:
        """Classify a tool call as safe or needing approval."""
        DESTRUCTIVE_TOOLS = {
            "update_company", "delete_company", "complete_task", "create_task",
            "send_email", "modify_crm", "delete_record", "create_project",
        }
        if tool_name in DESTRUCTIVE_TOOLS:
            return ActionType.ASK_USER
        return ActionType.TOOL_CALL


# ── Approval Workflow ──

class ApprovalStatus(str, Enum):
    AUTO_APPROVED = "auto_approved"
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"


@dataclass
class ApprovalRequest:
    """A request for human approval before executing an action."""
    request_id: str
    agent_name: str
    action: str
    description: str
    reasoning: str
    risk_level: str  # "low", "medium", "high"
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: str = ""


class ApprovalWorkflow:
    """
    Manages the approval workflow for agent actions.

    Rules:
    - Read-only tools: AUTO_APPROVED (safe)
    - Write tools (update_company, create_task): PENDING (needs approval)
    - Destructive tools (delete): PENDING (always needs approval)
    - Send communications: PENDING (needs approval)
    """

    SAFE_TOOLS: set[str] = {
        "search_companies", "get_company", "list_companies",
        "search_contacts", "get_contact",
        "list_opportunities", "get_opportunity", "recommend_opportunities",
        "company_timeline", "recent_activity",
        "company_signals", "market_signals",
        "calculate_score", "explain_score",
        "daily_brief", "next_action",
        "proposal_context", "meeting_context",
        "list_tasks", "dashboard_summary",
        "company_analysis",
        "knowledge_search", "service_catalog", "pricing_reference",
    }

    NEEDS_APPROVAL_TOOLS: set[str] = {
        "update_company", "create_task", "complete_task",
        "proposal_save", "timeline_append",
        "send_email", "modify_crm",
    }

    DESTRUCTIVE_TOOLS: set[str] = {
        "delete_company", "delete_record", "delete_task",
    }

    @classmethod
    def classify(cls, tool_name: str) -> ApprovalStatus:
        if tool_name in cls.SAFE_TOOLS:
            return ApprovalStatus.AUTO_APPROVED
        return ApprovalStatus.PENDING

    @classmethod
    def is_safe(cls, tool_name: str) -> bool:
        return tool_name in cls.SAFE_TOOLS

    @classmethod
    def risk_level(cls, tool_name: str) -> str:
        if tool_name in cls.SAFE_TOOLS:
            return "low"
        if tool_name in cls.NEEDS_APPROVAL_TOOLS:
            return "medium"
        return "high"
