"""Tool: compliance check — AML / sanctions screening (simulated)."""

from __future__ import annotations

import asyncio
from typing import Any

from pydantic import BaseModel

from agent.tools.registry import BaseTool, ToolResult
from gateway.session import SessionManager

BLACKLIST_NAMES = {"张违规", "李黑名单"}


class CheckComplianceParams(BaseModel):
    pass


class CheckComplianceTool(BaseTool):
    name = "check_compliance"
    description = (
        "对客户进行合规检查（反洗钱/制裁名单筛查）。无需额外参数，"
        "将基于已保存的客户信息自动执行检查。前置条件：客户信息中至少已有姓名。"
    )
    parameters = CheckComplianceParams

    def __init__(self, sessions: SessionManager) -> None:
        self._sessions = sessions

    async def execute(self, session_id: str, **kwargs: Any) -> ToolResult:
        session = self._sessions.get(session_id)
        if not session:
            return ToolResult(success=False, message="会话不存在")

        name = session.state.customer_info.get("name")
        if not name:
            return ToolResult(
                success=False,
                message="请先保存客户姓名后再进行合规检查",
            )

        await asyncio.sleep(0.8)

        if name in BLACKLIST_NAMES:
            session.state.compliance_checked = True
            session.state.compliance_result = "需人工审核"
            return ToolResult(
                success=False,
                message=f"合规检查未通过：客户 {name} 命中风险名单，需转人工审核",
                data={"result": "manual_review", "reason": "命中风险名单"},
            )

        session.state.compliance_checked = True
        session.state.compliance_result = "通过"
        return ToolResult(
            success=True,
            message="合规检查通过：反洗钱筛查及制裁名单筛查均无异常",
            data={"result": "passed"},
        )
