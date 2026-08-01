"""
AI Agent Orchestrator.

Coordinates multiple agents to execute complex multi-step workflows.
Agents can call one another through the orchestrator.

Example workflow:
  User: "Prepare a proposal for Atlas Construction"
  → Research Agent (gathers intelligence)
  → Proposal Agent (generates draft)
  → Creates follow-up task
  → Updates timeline
  → Returns complete proposal
"""

import asyncio
import time
from typing import Any

from app.application.agents.execution_log import ExecutionRecord, get_execution_log
from app.application.agents.planner import ExecutionPlan, Planner
from app.application.agents.registry import AgentDefinition, AgentRegistry, get_agent_registry
from app.application.agents.executor import AgentExecutor
from app.application.llm.provider import LLMConfig
from app.infrastructure.mcp.tool_registry import ToolRegistry


class AgentOrchestrator:
    """
    Coordinates multiple agents through a planned workflow.

    Features:
    - Sequential agent execution with dependency tracking
    - Context passing between agents
    - Parallel execution of independent agents
    - Full audit trail across all agents
    - Approval gating for destructive actions
    """

    def __init__(
        self,
        registry: ToolRegistry,
        agent_registry: AgentRegistry | None = None,
        llm_config: LLMConfig | None = None,
    ) -> None:
        self._tool_registry = registry
        self._agent_registry = agent_registry or get_agent_registry()
        self._llm_config = llm_config or LLMConfig()

    async def execute_plan(self, plan: ExecutionPlan, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute a complete multi-agent plan."""
        ctx = context or {}
        results: dict[int, dict[str, Any]] = {}
        execution_log = get_execution_log()
        master_record = execution_log.start("orchestrator", plan.goal)
        all_tools_called: list[str] = []
        pending_approvals: list[dict[str, Any]] = []

        # Execute steps in order, respecting dependencies
        for i, step in enumerate(plan.steps):
            # Wait for dependencies
            for dep_idx in step.depends_on:
                while dep_idx not in results:
                    await asyncio.sleep(0.1)

            # Gather context from dependencies
            step_context = {**ctx, **step.input_context}
            for dep_idx in step.depends_on:
                if dep_idx in results:
                    step_context[f"step_{dep_idx}_result"] = results[dep_idx]

            # Get agent
            agent = self._agent_registry.get(step.agent_name)
            if agent is None:
                results[i] = {"error": f"Agent '{step.agent_name}' not found."}
                continue

            # Execute agent
            executor = AgentExecutor(agent, self._tool_registry, self._llm_config)
            result = await executor.execute(
                goal=step.description,
                context=step_context,
            )

            results[i] = result
            all_tools_called.extend(result.get("tools_called", []))

            if "pending_approvals" in result:
                pending_approvals.extend(result["pending_approvals"])

        # Build final response
        final_result = {
            "goal": plan.goal,
            "plan_reasoning": plan.reasoning,
            "agents_executed": len(plan.steps),
            "total_tools_called": len(all_tools_called),
            "tools_called": all_tools_called,
            "results": [results[i] for i in sorted(results.keys())],
            "pending_approvals": pending_approvals,
            "execution_id": master_record.execution_id,
        }

        master_record.complete(final_result, plan.reasoning, 0.9)
        return final_result

    async def execute_goal(self, goal: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Plan and execute a goal in one call."""
        plan = Planner.plan(goal, context)
        return await self.execute_plan(plan, context)

    async def execute_goal_stream(self, goal: str, context: dict[str, Any] | None = None):
        """Execute a goal with streaming progress updates."""
        ctx = context or {}

        # Step 1: Plan
        yield {"type": "planning", "goal": goal}
        plan = Planner.plan(goal, ctx)
        yield {"type": "plan_ready", "plan": plan.to_dict()}

        # Step 2: Execute each step
        results: dict[int, dict[str, Any]] = {}
        for i, step in enumerate(plan.steps):
            yield {"type": "step_start", "step": i + 1, "total": len(plan.steps), "agent": step.agent_name, "description": step.description}

            # Wait for dependencies
            for dep_idx in step.depends_on:
                while dep_idx not in results:
                    await asyncio.sleep(0.05)

            step_context = {**ctx, **step.input_context}
            for dep_idx in step.depends_on:
                if dep_idx in results:
                    step_context[f"step_{dep_idx}_result"] = results[dep_idx]

            agent = self._agent_registry.get(step.agent_name)
            if agent is None:
                yield {"type": "step_error", "step": i + 1, "error": f"Agent '{step.agent_name}' not found"}
                continue

            # Stream agent execution
            executor = AgentExecutor(agent, self._tool_registry, self._llm_config)

            # For simplicity, execute and yield result
            result = await executor.execute(goal=step.description, context=step_context)
            results[i] = result

            yield {
                "type": "step_complete",
                "step": i + 1,
                "agent": step.agent_name,
                "tools_called": result.get("tools_called", []),
                "result_summary": str(result.get("result", {}))[:300],
            }

        yield {"type": "complete", "goal": goal, "steps_completed": len(plan.steps)}
