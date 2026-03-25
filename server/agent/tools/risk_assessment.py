"""Tool: risk tolerance assessment (simulated scoring matrix)."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel

from agent.tools.registry import BaseTool, ToolResult
from gateway.session import SessionManager

SCORE_MAP: dict[str, dict[str, int]] = {
    "investment_experience": {
        "无": 1, "1年以下": 2, "1-3年": 3, "3-5年": 4, "5年以上": 5,
    },
    "risk_preference": {
        "保守型": 1, "稳健型": 2, "平衡型": 3, "积极型": 4, "激进型": 5,
    },
    "income_level": {
        "10万以下": 1, "10-30万": 2, "30-50万": 3, "50-100万": 4, "100万以上": 5,
    },
    "investment_goal": {
        "资产保值": 1, "稳健增值": 2, "资产增值": 3, "追求高收益": 4,
    },
    "loss_tolerance": {
        "不能接受亏损": 1, "10%以内": 2, "10%-30%": 3, "30%-50%": 4, "50%以上": 5,
    },
}

LEVEL_THRESHOLDS = [
    (8, "保守型"), (13, "稳健型"), (18, "积极型"),
]


class AssessRiskParams(BaseModel):
    investment_experience: Optional[str] = None
    risk_preference: Optional[str] = None
    income_level: Optional[str] = None
    investment_goal: Optional[str] = None
    loss_tolerance: Optional[str] = None


class AssessRiskToleranceTool(BaseTool):
    name = "assess_risk_tolerance"
    description = (
        "根据客户的投资经验、风险偏好、收入水平、投资目标和亏损承受能力进行风险评估。"
        "各参数可选值——"
        "investment_experience: 无/1年以下/1-3年/3-5年/5年以上；"
        "risk_preference: 保守型/稳健型/平衡型/积极型/激进型；"
        "income_level: 10万以下/10-30万/30-50万/50-100万/100万以上；"
        "investment_goal: 资产保值/稳健增值/资产增值/追求高收益；"
        "loss_tolerance: 不能接受亏损/10%以内/10%-30%/30%-50%/50%以上。"
    )
    parameters = AssessRiskParams

    def __init__(self, sessions: SessionManager) -> None:
        self._sessions = sessions

    async def execute(self, session_id: str, **kwargs: Any) -> ToolResult:
        session = self._sessions.get(session_id)
        if not session:
            return ToolResult(success=False, message="会话不存在")

        provided = {k: v for k, v in kwargs.items() if v is not None}
        if len(provided) < 3:
            return ToolResult(
                success=False,
                message="至少需要3项评估指标才能完成风险评估",
                data={"provided": list(provided.keys()), "available": list(SCORE_MAP.keys())},
            )

        total = 0
        details: dict[str, int] = {}
        for key, value in provided.items():
            mapping = SCORE_MAP.get(key, {})
            score = mapping.get(str(value), 3)
            details[key] = score
            total += score

        risk_level = "激进型"
        for threshold, level in LEVEL_THRESHOLDS:
            if total <= threshold:
                risk_level = level
                break

        session.state.risk_assessed = True
        session.state.risk_level = risk_level

        return ToolResult(
            success=True,
            message=f"风险评估完成，您的风险等级为: {risk_level}（总分 {total}）",
            data={"risk_level": risk_level, "total_score": total, "detail_scores": details},
        )
