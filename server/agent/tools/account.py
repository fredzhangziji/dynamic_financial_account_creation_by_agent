"""Tool: create account & query progress."""

from __future__ import annotations

import time
from typing import Any, Optional

from pydantic import BaseModel

from agent.tools.registry import BaseTool, ToolResult
from gateway.session import SessionManager


class CreateAccountParams(BaseModel):
    account_type: Optional[str] = "stock"


class CreateAccountTool(BaseTool):
    name = "create_account"
    description = (
        "为客户创建证券账户。可选的 account_type: stock(普通股票账户)、"
        "fund(基金账户)、margin(融资融券账户)。"
        "前置条件：必填信息已齐全、身份核验通过、风险评估完成、合规检查通过。"
    )
    parameters = CreateAccountParams

    _counter: int = 0

    def __init__(self, sessions: SessionManager) -> None:
        self._sessions = sessions

    async def execute(self, session_id: str, **kwargs: Any) -> ToolResult:
        session = self._sessions.get(session_id)
        if not session:
            return ToolResult(success=False, message="会话不存在")

        state = session.state
        if not state.can_create_account:
            missing = state.to_progress()["missing_requirements"]
            return ToolResult(
                success=False,
                message=f"开户条件尚未满足，还需完成: {', '.join(missing)}",
                data={"missing": missing},
            )

        if state.account_created:
            return ToolResult(
                success=True,
                message=f"账户已存在，账号: {state.account_number}",
                data={"account_number": state.account_number},
            )

        CreateAccountTool._counter += 1
        date_str = time.strftime("%Y%m%d")
        account_number = f"HT-{date_str}-{CreateAccountTool._counter:04d}"

        account_type = kwargs.get("account_type", "stock")
        type_labels = {"stock": "普通股票账户", "fund": "基金账户", "margin": "融资融券账户"}
        type_label = type_labels.get(account_type, "普通股票账户")

        state.account_created = True
        state.account_number = account_number
        state.account_type = account_type

        return ToolResult(
            success=True,
            message=f"开户成功！账户类型: {type_label}，账号: {account_number}",
            data={
                "account_number": account_number,
                "account_type": account_type,
                "account_type_label": type_label,
                "customer_name": state.customer_info.get("name", ""),
            },
        )


class GetApplicationProgressParams(BaseModel):
    pass


class GetApplicationProgressTool(BaseTool):
    name = "get_application_progress"
    description = "查询当前开户申请的进度状态，了解哪些步骤已完成、哪些还需要补充。无需额外参数。"
    parameters = GetApplicationProgressParams

    def __init__(self, sessions: SessionManager) -> None:
        self._sessions = sessions

    async def execute(self, session_id: str, **kwargs: Any) -> ToolResult:
        session = self._sessions.get(session_id)
        if not session:
            return ToolResult(success=False, message="会话不存在")

        progress = session.state.to_progress()
        return ToolResult(success=True, message="当前开户进度", data=progress)
