"""
AI Agent Executor.

Runs a single agent with a ReAct-style reasoning loop:
1. Think — agent reasons about what to do
2. Act — agent calls an MCP tool
3. Observe — agent processes the result
4. Repeat until complete

Every execution is logged for auditability.
"""

import json
import time
from dataclasses import field
from typing import Any

from app.application.agents.execution_log import ExecutionRecord, get_execution_log
from app.application.agents.reasoning import ActionType, ApprovalStatus, ApprovalWorkflow, ReasoningStep, ReasoningTrace
from app.application.agents.registry import AgentDefinition
from app.application.llm.provider import LLMConfig, LLMMessage
from app.infrastructure.mcp.tool_registry import ToolRegistry


class AgentExecutor:
    """
    Executes a single agent with reasoning loop.

    The agent:
    1. Receives a goal and context
    2. Reasons about which tools to call
    3. Calls tools via MCP
    4. Processes results
    5. Returns a final answer with full reasoning trace
    """

    def __init__(
        self,
        agent: AgentDefinition,
        registry: ToolRegistry,
        llm_config: LLMConfig | None = None,
    ) -> None:
        self._agent = agent
        self._registry = registry
        self._llm_config = llm_config or LLMConfig()
        self._trace: ReasoningTrace | None = None

    async def execute(
        self,
        goal: str,
        context: dict[str, Any] | None = None,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Execute the agent to achieve the given goal."""
        ctx = context or {}
        execution_log = get_execution_log()
        record = execution_log.start(self._agent.name, goal)
        self._trace = ReasoningTrace(agent_name=self._agent.name, goal=goal)

        # Filter tools to only authorized ones
        all_tools = self._registry.list_openai_functions()
        authorized_tools = [
            t for t in all_tools
            if not self._agent.authorized_tools or t.get("function", {}).get("name") in self._agent.authorized_tools
        ]
        if not authorized_tools and all_tools:
            authorized_tools = all_tools  # If no filter specified, allow all

        # Build system prompt
        system_prompt = self._build_system_prompt(ctx)

        # Build messages
        messages: list[LLMMessage] = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=f"Goal: {goal}\n\nContext: {json.dumps(ctx, default=str)}\n\nExecute the plan step by step. Call tools as needed."),
        ]

        # Reasoning loop
        try:
            result = await self._reasoning_loop(messages, authorized_tools, record)
            record.complete(result, self._trace.final_answer, 0.9)
            return {
                "agent": self._agent.name,
                "goal": goal,
                "result": result,
                "reasoning_trace": self._trace.to_audit_log(),
                "tools_called": self._trace.tools_called,
                "execution_id": record.execution_id,
                "execution_time_ms": record.execution_time_ms,
            }
        except Exception as e:
            record.fail(str(e))
            return {
                "agent": self._agent.name,
                "goal": goal,
                "error": str(e),
                "reasoning_trace": self._trace.to_audit_log() if self._trace else {},
                "execution_id": record.execution_id,
            }

    async def _reasoning_loop(
        self,
        messages: list[LLMMessage],
        tools: list[dict[str, Any]],
        record: ExecutionRecord,
    ) -> dict[str, Any]:
        """ReAct reasoning loop: Think → Act → Observe → Repeat."""
        from app.application.llm.gateway import get_llm_gateway, GatewayConfig
        gateway = get_llm_gateway()
        iteration = 0
        pending_approvals: list[dict[str, Any]] = []

        while iteration < self._agent.max_iterations:
            iteration += 1

            # Step 1: Think — get LLM response
            gcfg = GatewayConfig(feature="mcp", organization_id=1, temperature=0.3,
                                 tools=tools if tools else None, max_tokens=4096)
            gresp = await gateway.chat(messages, gcfg)

            if not gresp.tool_calls:
                # Agent is done — return final answer
                self._trace.final_answer = gresp.content
                return {"answer": gresp.content, "iterations": iteration}

            # Step 2: Act — execute tool calls
            for tc in gresp.tool_calls:
                # Check approval
                approval = ApprovalWorkflow.classify(tc.name)

                if approval != ApprovalStatus.AUTO_APPROVED:
                    pending_approvals.append({
                        "tool": tc.name,
                        "arguments": tc.arguments,
                        "reasoning": f"Agent '{self._agent.name}' wants to call '{tc.name}'",
                        "risk": ApprovalWorkflow.risk_level(tc.name),
                    })
                    # Add tool response indicating approval is needed
                    messages.append(LLMMessage(role="assistant", content=gresp.content or ""))
                    messages.append(LLMMessage(
                        role="tool",
                        content=f"Action '{tc.name}' requires human approval. It has been queued for review.",
                        tool_call_id=tc.id,
                    ))
                    continue

                # Execute tool
                self._trace.add_step(ReasoningStep(
                    thought=f"Calling tool: {tc.name}",
                    action_type=ActionType.TOOL_CALL,
                    action={"tool": tc.name, "arguments": tc.arguments},
                ))

                tool_result = await self._registry.execute(tc.name, **tc.arguments)
                record.tools_called.append(tc.name)

                # Add to conversation
                messages.append(LLMMessage(role="assistant", content=gresp.content or ""))
                messages.append(LLMMessage(
                    role="tool",
                    content=json.dumps(tool_result, default=str)[:4000],
                    tool_call_id=tc.id,
                    name=tc.name,
                ))

        # Max iterations reached
        self._trace.final_answer = "Max iterations reached without completion."
        return {"answer": "Max iterations reached.", "iterations": iteration, "pending_approvals": pending_approvals}

    def _build_system_prompt(self, context: dict[str, Any]) -> str:
        """Build the agent's system prompt with tool instructions."""
        base = self._agent.system_prompt

        # Add tool usage instructions
        tool_instructions = """
HOW TO WORK:
1. Analyze the goal and context.
2. Select the most appropriate tool to gather information.
3. Call ONE tool at a time.
4. Process the result before calling the next tool.
5. When you have enough information, provide your final answer.
6. Always explain your reasoning.

RULES:
- Never invent information. Only use data from tool results.
- If a tool returns an error, try an alternative approach.
- Be concise but thorough in your final answer.
- Cite specific data points from tool results.
- If you cannot complete the goal, explain why clearly."""
        return base + tool_instructions
