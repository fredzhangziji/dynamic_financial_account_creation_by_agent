"""Session lifecycle management, aligned with OpenClaw's SessionManager."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ApplicationState:
    """Tracks account-opening progress within a session."""

    customer_info: dict[str, Any] = field(default_factory=dict)
    identity_verified: bool = False
    identity_verification_id: str | None = None
    risk_assessed: bool = False
    risk_level: str | None = None
    compliance_checked: bool = False
    compliance_result: str | None = None
    account_created: bool = False
    account_number: str | None = None
    account_type: str | None = None

    # ── progress helpers ────────────────────────────────────────────────

    REQUIRED_FIELDS = ("name", "id_number", "phone")

    @property
    def missing_customer_fields(self) -> list[str]:
        return [f for f in self.REQUIRED_FIELDS if not self.customer_info.get(f)]

    @property
    def can_create_account(self) -> bool:
        return (
            not self.missing_customer_fields
            and self.identity_verified
            and self.risk_assessed
            and self.compliance_checked
            and not self.account_created
        )

    def to_progress(self) -> dict[str, Any]:
        missing: list[str] = []
        if self.missing_customer_fields:
            missing.extend(self.missing_customer_fields)
        if not self.identity_verified:
            missing.append("身份核验")
        if not self.risk_assessed:
            missing.append("风险评估")
        if not self.compliance_checked:
            missing.append("合规检查")
        return {
            "customer_info": {
                k: ("已填写" if self.customer_info.get(k) else "未填写")
                for k in ("name", "id_number", "phone", "email", "address")
            },
            "identity_verified": self.identity_verified,
            "risk_assessed": self.risk_assessed,
            "risk_level": self.risk_level,
            "compliance_checked": self.compliance_checked,
            "account_created": self.account_created,
            "account_number": self.account_number,
            "can_create_account": self.can_create_account,
            "missing_requirements": missing,
        }


@dataclass
class Session:
    session_id: str
    messages: list[dict[str, Any]] = field(default_factory=list)
    state: ApplicationState = field(default_factory=ApplicationState)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    seq: int = 0

    def next_seq(self) -> int:
        self.seq += 1
        self.updated_at = time.time()
        return self.seq

    def add_message(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})
        self.updated_at = time.time()

    def build_messages(self, system_prompt: str) -> list[dict[str, Any]]:
        return [{"role": "system", "content": system_prompt}] + list(self.messages)


class SessionManager:
    """In-memory session store."""

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def get_or_create(self, session_id: str | None = None) -> Session:
        if session_id and session_id in self._sessions:
            return self._sessions[session_id]
        sid = session_id or uuid.uuid4().hex[:16]
        session = Session(session_id=sid)
        self._sessions[sid] = session
        return session

    def get(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)
