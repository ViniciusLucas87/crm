"""
MCP API Endpoints.

Exposes the MCP server to external consumers:
- JSON-RPC endpoint for tool calls
- SSE streaming for real-time responses
- Tool listing for discovery

The LLM communicates ONLY through these endpoints.
"""

import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.application.llm import LLMConfig, LLMMessage, create_provider, get_memory_store, get_prompt
from app.application.llm.prompt_components import CHAT_SYSTEM_PROMPT
from app.infrastructure.auth.clerk import AuthContext, require_permission
from app.infrastructure.db.session import get_db_session
from app.infrastructure.mcp import MCPServer, get_registry, register_all_tools

router = APIRouter(prefix="/mcp", tags=["mcp"])


def _get_server(session: Session, org_id: int) -> MCPServer:
    registry = get_registry()
    # Re-register tools for this org (session factory pattern)
    register_all_tools(lambda: session, org_id)
    return MCPServer(registry)


# ── JSON-RPC Endpoint ──

@router.post("/message")
async def mcp_message(
    request: Request,
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    """Handle a JSON-RPC 2.0 message. Returns tool list, executes tools."""
    body = await request.json()
    server = _get_server(session, ctx.organization_id)
    response = await server.handle_message(body)
    return response


# ── SSE Streaming Endpoint ──

@router.get("/sse")
async def mcp_sse(
    request: Request,
    message: str = Query(..., description="JSON-encoded JSON-RPC message"),
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    """Stream MCP responses via Server-Sent Events."""
    server = _get_server(session, ctx.organization_id)

    try:
        body = json.loads(message)
    except json.JSONDecodeError:
        async def error_stream():
            yield f"data: {json.dumps({'error': 'Invalid JSON'})}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(error_stream(), media_type="text/event-stream")

    async def event_stream():
        async for event in server.stream_response(body):
            if await request.is_disconnected():
                break
            yield event

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ── Tool Discovery ──

@router.get("/tools")
def list_tools(
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    """List all available MCP tools with their schemas."""
    server = _get_server(session, ctx.organization_id)
    registry = get_registry()
    return {
        "server": MCPServer.SERVER_INFO,
        "tools": registry.list_mcp_schemas(),
        "openai_functions": registry.list_openai_functions(),
        "total": len(registry.list_all()),
    }


from app.application.llm.prompt_components import CHAT_SYSTEM_PROMPT

# ── AI Chat Endpoint (Multi-Tool Reasoning) ──
async def mcp_chat(
    request: Request,
    ctx: AuthContext = Depends(require_permission("companies:read")),
    session: Session = Depends(get_db_session),
):
    """
    AI Chat endpoint with automatic multi-tool reasoning.

    The AI:
    1. Understands intent from natural language
    2. Plans which MCP tools to call
    3. Automatically chains multiple tool calls
    4. Combines results into coherent business insights
    5. Explains reasoning with supporting data
    6. Suggests next actions
    """
    body = await request.json()
    user_message = body.get("message", "")
    session_id = body.get("session_id", str(uuid.uuid4()))
    provider_cfg = body.get("provider", {})
    stream = body.get("stream", False)

    # Setup
    server = _get_server(session, ctx.organization_id)
    registry = get_registry()
    memory = get_memory_store().get_or_create(session_id)
    tools = registry.list_openai_functions()

    # Configure LLM — default to DeepSeek
    llm_config = LLMConfig(
        provider=provider_cfg.get("provider", "deepseek"),
        model=provider_cfg.get("model", "deepseek-chat"),
        api_key=provider_cfg.get("api_key", "") or "sk-4baa89a56bc14ef6aa4de2587e525d8e",
        api_base=provider_cfg.get("api_base", "https://api.deepseek.com/v1"),
        temperature=provider_cfg.get("temperature", 0.3),
        max_tokens=provider_cfg.get("max_tokens", 4096),
    )

    # Build context
    enriched_context = _build_chat_context(session, ctx.organization_id, user_message)

    # Add user message to memory
    memory.add_message("user", user_message)
    memory.add_message("system", enriched_context.get("summary", ""))

    try:
        llm = create_provider(llm_config)

        # Build messages with context
        llm_messages = [
            LLMMessage(role="system", content=CHAT_SYSTEM_PROMPT),
            LLMMessage(role="system", content=f"CURRENT CRM CONTEXT:\n{enriched_context.get('summary', 'No context available.')}"),
            LLMMessage(role="user", content=user_message),
        ]

        if stream:
            return await _handle_stream(request, llm, llm_messages, tools, memory, session_id, registry)
        else:
            return await _handle_chat(llm, llm_messages, tools, memory, session_id, registry, user_message)

    except Exception as e:
        return {"error": str(e), "session_id": session_id, "fallback": "I encountered an error processing your request. Please try again or check that the LLM API key is configured correctly."}


async def _handle_chat(llm, llm_messages, tools, memory, session_id, registry, user_message):
    """Handle non-streaming chat with multi-tool reasoning loop."""
    max_iterations = 6
    iteration = 0
    all_tool_results: list[dict[str, Any]] = []
    all_tools_called: list[str] = []

    while iteration < max_iterations:
        iteration += 1
        response = await llm.chat(llm_messages, tools if tools else None)

        if not response.tool_calls:
            # No more tools needed — return final answer
            memory.add_message("assistant", response.content)
            return {
                "session_id": session_id,
                "content": response.content,
                "tools_called": all_tools_called,
                "tool_results": all_tool_results,
                "iterations": iteration,
                "usage": response.usage,
                "memory_context": memory.get_context_summary(),
            }

        # Execute each tool call
        for tc in response.tool_calls:
            tool_result = await registry.execute(tc.name, **tc.arguments)
            all_tools_called.append(tc.name)
            all_tool_results.append({"tool": tc.name, "arguments": tc.arguments, "result_summary": str(tool_result)[:500]})
            memory.add_tool_execution(tc.name, tc.arguments, tool_result)

            # Add to conversation
            llm_messages.append(LLMMessage(role="assistant", content=response.content or f"Calling {tc.name}..."))
            llm_messages.append(LLMMessage(role="tool", content=str(tool_result)[:4000], tool_call_id=tc.id, name=tc.name))

    # Max iterations reached
    final = f"I've gathered {len(all_tools_called)} data points but need more direction to give you a complete answer. What specific aspect would you like me to focus on?"
    memory.add_message("assistant", final)
    return {"session_id": session_id, "content": final, "tools_called": all_tools_called, "iterations": iteration}


async def _handle_stream(request, llm, llm_messages, tools, memory, session_id, registry):
    """Handle streaming chat."""
    async def event_stream():
        yield f"data: {json.dumps({'type': 'start', 'session_id': session_id})}\n\n"
        full_response = ""

        async for chunk in llm.chat_stream(llm_messages, tools):
            if await request.is_disconnected():
                break
            full_response += chunk
            yield f"data: {json.dumps({'type': 'content', 'text': chunk})}\n\n"

        memory.add_message("assistant", full_response)
        yield f"data: {json.dumps({'type': 'done', 'session_id': session_id})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def _build_chat_context(session: Session, org_id: int, user_message: str) -> dict[str, Any]:
    """Build enriched context for the AI chat from live CRM data."""
    from sqlalchemy import func, select
    from app.infrastructure.db.models import Company, Opportunity, Task

    total_companies = session.execute(select(func.count(Company.id)).where(Company.organization_id == org_id, Company.archived_at.is_(None))).scalar_one()
    total_opps = session.execute(select(func.count(Opportunity.id)).where(Opportunity.organization_id == org_id, Opportunity.stage.notin_(["won", "lost"]))).scalar_one()
    total_tasks = session.execute(select(func.count(Task.id)).where(Task.organization_id == org_id, Task.status != "completed")).scalar_one()
    pipeline = session.execute(select(func.sum(Opportunity.estimated_value)).where(Opportunity.organization_id == org_id, Opportunity.stage.notin_(["won", "lost"]))).scalar_one() or 0

    # Find matching companies if user mentions names
    mentioned_companies: list[dict[str, Any]] = []
    companies = session.execute(select(Company).where(Company.organization_id == org_id, Company.archived_at.is_(None)).limit(50)).scalars().all()
    for c in companies:
        if c.name.lower() in user_message.lower():
            mentioned_companies.append({
                "id": c.id, "name": c.name, "industry": c.industry,
                "opportunity_score": c.opportunity_score, "employees": c.employees,
            })

    summary = f"CRM Overview: {total_companies} companies, {total_opps} open opportunities, ${float(pipeline):,.0f} pipeline, {total_tasks} pending tasks."
    if mentioned_companies:
        summary += f" Mentioned companies: {json.dumps(mentioned_companies)}"

    return {"summary": summary, "mentioned_companies": mentioned_companies, "total_companies": total_companies}


# ── Prompt Discovery ──

@router.get("/prompts")
def list_prompts_endpoint(
    ctx: AuthContext = Depends(require_permission("companies:read")),
):
    """List all available prompt templates."""
    from app.application.llm.prompts import list_prompts
    prompts = list_prompts()
    return {
        "total": len(prompts),
        "prompts": [
            {"name": p.name, "version": p.version, "description": p.description, "category": p.category, "variables": p.variables}
            for p in prompts
        ],
    }


# ── Memory Management ──

@router.get("/memory/{session_id}")
def get_memory(session_id: str):
    """Get conversation memory for a session."""
    memory = get_memory_store().get(session_id)
    if memory is None:
        return {"error": "Session not found", "session_id": session_id}
    return memory.get_context_summary()


@router.delete("/memory/{session_id}")
def delete_memory(session_id: str):
    """Clear conversation memory for a session."""
    get_memory_store().delete(session_id)
    return {"status": "deleted", "session_id": session_id}
