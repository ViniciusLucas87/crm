"""
AI Agent API Endpoints.

Exposes the agent framework to the frontend:
- Agent discovery (list all agents)
- Single agent execution
- Multi-agent orchestration
- Streaming execution
- Execution history
"""

import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.application.agents import (
    AgentExecutor,
    AgentOrchestrator,
    ExecutionPlan,
    Planner,
    get_agent_registry,
    get_execution_log,
    register_all_agents,
)
from app.application.llm.provider import LLMConfig
from app.infrastructure.auth.clerk import AuthContext, require_permission
from app.infrastructure.db.session import get_db_session
from app.infrastructure.mcp import register_all_tools
from app.infrastructure.mcp.tool_registry import ToolRegistry

router = APIRouter(prefix="/agents", tags=["agents"])


def _setup(session: Session, org_id: int) -> AgentOrchestrator:
    """Setup tool registry and agent registry for a request."""
    tool_registry = ToolRegistry(organization_id=org_id)
    register_all_tools(lambda: Session(bind=session.get_bind()), org_id, tool_registry)
    register_all_agents()
    return AgentOrchestrator(tool_registry, get_agent_registry())


# ── Agent Discovery ──

@router.get("/")
def list_agents(
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    """List all available AI agents."""
    _setup(session, ctx.organization_id)
    registry = get_agent_registry()
    return {
        "total": len(registry.list_all()),
        "agents": [a.to_dict() for a in registry.list_all()],
        "categories": {
            cat: [a.to_dict() for a in registry.list_by_category(cat)]
            for cat in {"research", "sales", "operations", "outreach"}
        },
    }


@router.get("/{agent_name}")
def get_agent(
    agent_name: str,
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    """Get details for a specific agent."""
    _setup(session, ctx.organization_id)
    agent = get_agent_registry().get(agent_name)
    if agent is None:
        return {"error": f"Agent '{agent_name}' not found."}
    return agent.to_dict()


# ── Agent Execution ──

@router.post("/{agent_name}/execute")
async def execute_agent(
    agent_name: str,
    request: Request,
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    """Execute a single agent with a goal."""
    body = await request.json()
    goal = body.get("goal", "")
    context = body.get("context", {})
    provider_cfg = body.get("provider", {})

    orchestrator = _setup(session, ctx.organization_id)
    agent = get_agent_registry().get(agent_name)
    if agent is None:
        return {"error": f"Agent '{agent_name}' not found."}

    llm_config = LLMConfig(
        provider=provider_cfg.get("provider", "openai"),
        model=provider_cfg.get("model", "gpt-4o"),
        api_key=provider_cfg.get("api_key", ""),
        api_base=provider_cfg.get("api_base"),
        temperature=provider_cfg.get("temperature", 0.3),
    )

    executor = AgentExecutor(agent, get_registry(), llm_config)
    result = await executor.execute(goal=goal, context=context)
    return result


# ── Multi-Agent Orchestration ──

@router.post("/orchestrate")
async def orchestrate_agents(
    request: Request,
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    """Execute a multi-agent workflow from a natural language goal."""
    body = await request.json()
    goal = body.get("goal", "")
    context = body.get("context", {})
    provider_cfg = body.get("provider", {})

    orchestrator = _setup(session, ctx.organization_id)
    orchestrator._llm_config = LLMConfig(
        provider=provider_cfg.get("provider", "openai"),
        model=provider_cfg.get("model", "gpt-4o"),
        api_key=provider_cfg.get("api_key", ""),
        api_base=provider_cfg.get("api_base"),
        temperature=provider_cfg.get("temperature", 0.3),
    )

    return await orchestrator.execute_goal(goal, context)


@router.post("/orchestrate/stream")
async def orchestrate_agents_stream(
    request: Request,
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    """Stream a multi-agent workflow execution via SSE."""
    body = await request.json()
    goal = body.get("goal", "")
    context = body.get("context", {})
    provider_cfg = body.get("provider", {})

    orchestrator = _setup(session, ctx.organization_id)
    orchestrator._llm_config = LLMConfig(
        provider=provider_cfg.get("provider", "openai"),
        model=provider_cfg.get("model", "gpt-4o"),
        api_key=provider_cfg.get("api_key", ""),
        api_base=provider_cfg.get("api_base"),
        temperature=provider_cfg.get("temperature", 0.3),
    )

    async def event_stream():
        async for event in orchestrator.execute_goal_stream(goal, context):
            if await request.is_disconnected():
                break
            yield f"data: {json.dumps(event, default=str)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ── Planning ──

@router.post("/plan")
async def plan_workflow(
    request: Request,
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    """Generate an execution plan without running it."""
    _setup(session, ctx.organization_id)
    body = await request.json()
    goal = body.get("goal", "")
    context = body.get("context", {})
    plan = Planner.plan(goal, context)
    return plan.to_dict()


# ── Execution History ──

@router.get("/history")
def execution_history(
    agent_name: str | None = Query(None),
    limit: int = Query(20, le=100),
    ctx: AuthContext = Depends(require_permission("companies:read")),
):
    """Get agent execution history."""
    log = get_execution_log()
    if agent_name:
        records = log.list_by_agent(agent_name, limit)
    else:
        records = log.list_recent(limit)
    return {"total": len(records), "executions": [r.to_dict() for r in records]}


@router.get("/history/{execution_id}")
def execution_detail(
    execution_id: str,
    ctx: AuthContext = Depends(require_permission("companies:read")),
):
    """Get details for a specific execution."""
    record = get_execution_log().get(execution_id)
    if record is None:
        return {"error": f"Execution '{execution_id}' not found."}
    return record.to_dict()
