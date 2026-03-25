"""Tool: identity verification (simulated for demo)."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any, Optional

from pydantic import BaseModel

from agent.tools.registry import BaseTool, ToolResult
from gateway.session import SessionManager

MISMATCHED_IDS = {"110101199901011234"}


class VerifyIdentityParams(BaseModel):
    id_type: Optional[str] = "身份证"
    id_number: str
    name: str


class VerifyIdentityTool(BaseTool):
    name = "verify_identity"
    description = (
        "对客户进行身份核验（模拟）。需要提供证件类型、证件号码和姓名。"
        "前置条件：客户信息中已有姓名和证件号。"
    )
    parameters = VerifyIdentityParams

    def __init__(self, sessions: SessionManager) -> None:
        self._sessions = sessions

    async def execute(self, session_id: str, **kwargs: Any) -> ToolResult:
        session = self._sessions.get(session_id)
        if not session:
            return ToolResult(success=False, message="会话不存在")

        id_number = kwargs.get("id_number", "")
        name = kwargs.get("name", "")

        if not id_number or not name:
            return ToolResult(success=False, message="缺少必要参数: id_number 和 name")

        info = session.state.customer_info
        if not info.get("name") or not info.get("id_number"):
            return ToolResult(
                success=False,
                message="请先通过 save_customer_info 保存客户的姓名和证件号",
            )

        await asyncio.sleep(1)

        if id_number in MISMATCHED_IDS:
            return ToolResult(success=False, message="核验失败：姓名与证件号不匹配")

        verification_id = f"VER-{uuid.uuid4().hex[:8].upper()}"
        session.state.identity_verified = True
        session.state.identity_verification_id = verification_id

        return ToolResult(
            success=True,
            message=f"身份核验通过，核验流水号: {verification_id}",
            data={"verification_id": verification_id},
        )
