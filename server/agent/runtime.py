"""Agent runtime – ReAct loop via OpenAI-compatible function calling."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator

from openai import AsyncOpenAI

from config import settings
from agent.prompts import SYSTEM_PROMPT
from agent.tools.registry import ToolRegistry, ToolResult, BaseTool
from agent.tools.customer_info import SaveCustomerInfoTool
from agent.tools.identity import VerifyIdentityTool
from agent.tools.risk_assessment import AssessRiskToleranceTool
from agent.tools.compliance import CheckComplianceTool
from agent.tools.account import CreateAccountTool, GetApplicationProgressTool
from gateway.session import Session, SessionManager

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 10


@dataclass
class AgentEvent:
    stream: str  # "assistant" | "tool" | "error"
    data: dict[str, Any] = field(default_factory=dict)


class AgentRuntime:
    """Drives the LLM ↔ Tool loop, aligned with OpenClaw's embedded Pi runner."""

    def __init__(self, registry: ToolRegistry, sessions: SessionManager) -> None:
        self._registry = registry
        self._sessions = sessions
        self._client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_api_base,
        )
        self._model = settings.openai_model

    async def run(self, session: Session, user_message: str) -> AsyncGenerator[AgentEvent, None]:
        messages = session.build_messages(SYSTEM_PROMPT)
        tool_schemas = self._registry.get_schemas()
        rounds = 0

        while rounds < MAX_TOOL_ROUNDS:
            rounds += 1
            try:
                response = await self._client.chat.completions.create(
                    model=self._model,
                    messages=messages,
                    tools=tool_schemas or None,
                )
            except Exception as e:
                logger.exception("LLM call failed")
                yield AgentEvent(stream="error", data={"message": f"模型调用失败: {e}"})
                return

            choice = response.choices[0]
            msg = choice.message

            if msg.tool_calls:
                messages.append(msg.model_dump())
                for tc in msg.tool_calls:
                    fn = tc.function
                    yield AgentEvent(
                        stream="tool",
                        data={"phase": "start", "name": fn.name, "arguments": fn.arguments},
                    )

                    result = await self._registry.execute(fn.name, fn.arguments, session.session_id)

                    yield AgentEvent(
                        stream="tool",
                        data={
                            "phase": "end",
                            "name": fn.name,
                            "success": result.success,
                            "message": result.message,
                        },
                    )

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result.to_text(),
                    })
                continue

            content = msg.content or ""
            session.add_message("assistant", content)
            yield AgentEvent(stream="assistant", data={"content": content})
            return

        yield AgentEvent(stream="error", data={"message": "工具调用轮次超限，请重试"})


def create_runtime(sessions: SessionManager) -> AgentRuntime:
    registry = ToolRegistry()
    tools: list[BaseTool] = [
        SaveCustomerInfoTool(sessions),
        VerifyIdentityTool(sessions),
        AssessRiskToleranceTool(sessions),
        CheckComplianceTool(sessions),
        CreateAccountTool(sessions),
        GetApplicationProgressTool(sessions),
    ]
    for t in tools:
        registry.register(t)
    return AgentRuntime(registry, sessions)
