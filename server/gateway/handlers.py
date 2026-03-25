"""Method dispatch – aligned with OpenClaw's coreGatewayHandlers pattern."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Callable, Awaitable

from gateway.protocol import ok_response, error_response, event_frame
from gateway.session import SessionManager

if TYPE_CHECKING:
    from fastapi import WebSocket
    from agent.runtime import AgentRuntime

logger = logging.getLogger(__name__)

# ── Types ────────────────────────────────────────────────────────────────────

HandlerFn = Callable[
    [dict[str, Any], "RequestContext"],
    Awaitable[dict | None],
]


class RequestContext:
    """Per-request context passed to every handler."""

    def __init__(
        self,
        ws: "WebSocket",
        sessions: SessionManager,
        agent: "AgentRuntime",
        req_id: str,
    ) -> None:
        self.ws = ws
        self.sessions = sessions
        self.agent = agent
        self.req_id = req_id

    async def send(self, data: dict) -> None:
        await self.ws.send_json(data)


# ── Handlers ─────────────────────────────────────────────────────────────────

async def handle_connect(params: dict[str, Any], ctx: RequestContext) -> dict:
    session = ctx.sessions.get_default()
    has_history = len(session.messages) > 0
    return ok_response(ctx.req_id, {
        "session_id": session.session_id,
        "has_history": has_history,
    })


async def handle_chat_send(params: dict[str, Any], ctx: RequestContext) -> dict:
    session_id = params.get("session_id")
    message = params.get("message", "")
    if not message:
        return error_response(ctx.req_id, "INVALID_PARAMS", "message is required")

    session = ctx.sessions.get_or_create(session_id)
    session.add_message("user", message)

    await ctx.send(ok_response(ctx.req_id, {"status": "started", "session_id": session.session_id}))

    async def _run() -> None:
        try:
            async for evt in ctx.agent.run(session, message):
                seq = session.next_seq()
                await ctx.send(event_frame(evt.stream, {**evt.data, "session_id": session.session_id}, seq))
        except Exception:
            logger.exception("agent run failed")
            await ctx.send(event_frame("error", {"message": "Agent 运行出错，请重试"}, session.next_seq()))
        finally:
            ctx.sessions.save()

    asyncio.create_task(_run())
    return None


async def handle_chat_history(params: dict[str, Any], ctx: RequestContext) -> dict:
    session = ctx.sessions.get(params.get("session_id", ""))
    if not session:
        return ok_response(ctx.req_id, {"messages": []})
    visible = [m for m in session.messages if m["role"] in ("user", "assistant")]
    return ok_response(ctx.req_id, {"messages": visible})


async def handle_session_status(params: dict[str, Any], ctx: RequestContext) -> dict:
    session = ctx.sessions.get(params.get("session_id", ""))
    if not session:
        return error_response(ctx.req_id, "NOT_FOUND", "session not found")
    return ok_response(ctx.req_id, {"progress": session.state.to_progress()})


# ── Dispatch table ───────────────────────────────────────────────────────────

HANDLERS: dict[str, HandlerFn] = {
    "connect": handle_connect,
    "chat.send": handle_chat_send,
    "chat.history": handle_chat_history,
    "session.status": handle_session_status,
}


async def dispatch(method: str, params: dict[str, Any], ctx: RequestContext) -> dict | None:
    handler = HANDLERS.get(method)
    if not handler:
        return error_response(ctx.req_id, "UNKNOWN_METHOD", f"unknown method: {method}")
    return await handler(params, ctx)
