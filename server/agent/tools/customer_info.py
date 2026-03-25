"""Tool: save / update customer personal information."""

from __future__ import annotations

import re
from typing import Any, Optional

from pydantic import BaseModel

from agent.tools.registry import BaseTool, ToolResult
from gateway.session import SessionManager


class SaveCustomerInfoParams(BaseModel):
    name: Optional[str] = None
    id_type: Optional[str] = None
    id_number: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    occupation: Optional[str] = None
    annual_income: Optional[str] = None


class SaveCustomerInfoTool(BaseTool):
    name = "save_customer_info"
    description = (
        "保存或更新客户个人信息。所有字段均为可选，可以分多次调用逐步补充。"
        "支持的字段：name(姓名)、id_type(证件类型，默认身份证)、id_number(证件号码)、"
        "phone(手机号)、email(邮箱)、address(地址)、occupation(职业)、annual_income(年收入)。"
    )
    parameters = SaveCustomerInfoParams

    def __init__(self, sessions: SessionManager) -> None:
        self._sessions = sessions

    async def execute(self, session_id: str, **kwargs: Any) -> ToolResult:
        session = self._sessions.get(session_id)
        if not session:
            return ToolResult(success=False, message="会话不存在")

        errors: list[str] = []
        updated: list[str] = []

        for key, value in kwargs.items():
            if value is None:
                continue
            value = str(value).strip()
            if not value:
                continue

            if key == "id_number" and not self._validate_id(value):
                errors.append("身份证号格式不正确（应为18位）")
                continue
            if key == "phone" and not re.match(r"^1[3-9]\d{9}$", value):
                errors.append("手机号格式不正确（应为11位）")
                continue
            if key == "email" and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value):
                errors.append("邮箱格式不正确")
                continue

            session.state.customer_info[key] = value
            updated.append(key)

        filled = list(session.state.customer_info.keys())
        missing = session.state.missing_customer_fields

        msg_parts: list[str] = []
        if updated:
            msg_parts.append(f"已更新: {', '.join(updated)}")
        if errors:
            msg_parts.append(f"校验失败: {'; '.join(errors)}")
        if missing:
            msg_parts.append(f"必填项仍缺: {', '.join(missing)}")
        else:
            msg_parts.append("必填信息已齐全")

        return ToolResult(
            success=not errors,
            message="；".join(msg_parts),
            data={"filled_fields": filled, "missing_required": missing},
        )

    @staticmethod
    def _validate_id(id_number: str) -> bool:
        return bool(re.match(r"^\d{17}[\dXx]$", id_number))
