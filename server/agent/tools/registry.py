"""Tool base class and registry – aligned with OpenClaw's AgentTool + tool-catalog."""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger(__name__)


@dataclass
class ToolResult:
    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    message: str = ""

    def to_text(self) -> str:
        return json.dumps(
            {"success": self.success, "message": self.message, **self.data},
            ensure_ascii=False,
            indent=2,
        )


class BaseTool(ABC):
    """Every business tool implements this interface."""

    name: str
    description: str
    parameters: type[BaseModel]

    @abstractmethod
    async def execute(self, session_id: str, **kwargs: Any) -> ToolResult:
        ...

    def to_openai_schema(self) -> dict:
        schema = self.parameters.model_json_schema()
        schema.pop("title", None)
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": schema,
            },
        }


class ToolRegistry:
    """Central registry for all agent tools."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def get_schemas(self) -> list[dict]:
        return [t.to_openai_schema() for t in self._tools.values()]

    async def execute(self, name: str, arguments: str, session_id: str) -> ToolResult:
        tool = self._tools.get(name)
        if not tool:
            return ToolResult(success=False, message=f"unknown tool: {name}")
        try:
            kwargs = json.loads(arguments) if arguments else {}
            return await tool.execute(session_id=session_id, **kwargs)
        except Exception as e:
            logger.exception("tool %s execution failed", name)
            return ToolResult(success=False, message=f"工具执行异常: {e}")
