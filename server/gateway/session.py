"""Session lifecycle management with JSON file persistence."""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

ALL_ACCOUNT_TYPES = ("stock", "fund", "margin")
ACCOUNT_TYPE_LABELS = {"stock": "普通股票账户", "fund": "基金账户", "margin": "融资融券账户"}

DEFAULT_STORE_PATH = Path(__file__).resolve().parent.parent / "data" / "sessions.json"


@dataclass
class AccountEntry:
    account_number: str
    account_type: str

    @property
    def label(self) -> str:
        return ACCOUNT_TYPE_LABELS.get(self.account_type, self.account_type)

    def to_dict(self) -> dict:
        return {"account_number": self.account_number, "account_type": self.account_type}

    @classmethod
    def from_dict(cls, d: dict) -> AccountEntry:
        return cls(account_number=d["account_number"], account_type=d["account_type"])


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
    accounts: list[AccountEntry] = field(default_factory=list)

    # ── progress helpers ────────────────────────────────────────────────

    REQUIRED_FIELDS = ("name", "id_number", "phone")

    @property
    def missing_customer_fields(self) -> list[str]:
        return [f for f in self.REQUIRED_FIELDS if not self.customer_info.get(f)]

    @property
    def opened_types(self) -> set[str]:
        return {a.account_type for a in self.accounts}

    @property
    def available_types(self) -> list[str]:
        return [t for t in ALL_ACCOUNT_TYPES if t not in self.opened_types]

    @property
    def prerequisites_met(self) -> bool:
        return (
            not self.missing_customer_fields
            and self.identity_verified
            and self.risk_assessed
            and self.compliance_checked
        )

    @property
    def can_create_account(self) -> bool:
        return self.prerequisites_met and len(self.available_types) > 0

    def has_account(self, account_type: str) -> bool:
        return account_type in self.opened_types

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

        account_info = [
            {"account_number": a.account_number, "type": a.account_type, "label": a.label}
            for a in self.accounts
        ]

        return {
            "customer_info": {
                k: ("已填写" if self.customer_info.get(k) else "未填写")
                for k in ("name", "id_number", "phone", "email", "address")
            },
            "identity_verified": self.identity_verified,
            "risk_assessed": self.risk_assessed,
            "risk_level": self.risk_level,
            "compliance_checked": self.compliance_checked,
            "account_created": len(self.accounts) > 0,
            "accounts": account_info,
            "available_types": [
                {"type": t, "label": ACCOUNT_TYPE_LABELS[t]} for t in self.available_types
            ],
            "can_create_account": self.can_create_account,
            "missing_requirements": missing,
        }

    def to_dict(self) -> dict:
        return {
            "customer_info": self.customer_info,
            "identity_verified": self.identity_verified,
            "identity_verification_id": self.identity_verification_id,
            "risk_assessed": self.risk_assessed,
            "risk_level": self.risk_level,
            "compliance_checked": self.compliance_checked,
            "compliance_result": self.compliance_result,
            "accounts": [a.to_dict() for a in self.accounts],
        }

    @classmethod
    def from_dict(cls, d: dict) -> ApplicationState:
        accounts = [AccountEntry.from_dict(a) for a in d.get("accounts", [])]
        return cls(
            customer_info=d.get("customer_info", {}),
            identity_verified=d.get("identity_verified", False),
            identity_verification_id=d.get("identity_verification_id"),
            risk_assessed=d.get("risk_assessed", False),
            risk_level=d.get("risk_level"),
            compliance_checked=d.get("compliance_checked", False),
            compliance_result=d.get("compliance_result"),
            accounts=accounts,
        )


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

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "messages": self.messages,
            "state": self.state.to_dict(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "seq": self.seq,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Session:
        return cls(
            session_id=d["session_id"],
            messages=d.get("messages", []),
            state=ApplicationState.from_dict(d.get("state", {})),
            created_at=d.get("created_at", time.time()),
            updated_at=d.get("updated_at", time.time()),
            seq=d.get("seq", 0),
        )


class SessionManager:
    """Session store with JSON file persistence."""

    def __init__(self, store_path: Path = DEFAULT_STORE_PATH) -> None:
        self._sessions: dict[str, Session] = {}
        self._store_path = store_path
        self._load()

    # ── Public API ───────────────────────────────────────────────────────

    def get_or_create(self, session_id: str | None = None) -> Session:
        if session_id and session_id in self._sessions:
            return self._sessions[session_id]
        sid = session_id or uuid.uuid4().hex[:16]
        session = Session(session_id=sid)
        self._sessions[sid] = session
        self._save()
        return session

    def get(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def get_default(self) -> Session:
        """Single-user mode: return the most recent session, or create one."""
        if self._sessions:
            return max(self._sessions.values(), key=lambda s: s.updated_at)
        return self.get_or_create()

    def save(self) -> None:
        """Explicitly persist current state to disk."""
        self._save()

    # ── Persistence ──────────────────────────────────────────────────────

    def _save(self) -> None:
        try:
            self._store_path.parent.mkdir(parents=True, exist_ok=True)
            data = {sid: s.to_dict() for sid, s in self._sessions.items()}
            tmp = self._store_path.with_suffix(".tmp")
            tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(self._store_path)
        except Exception:
            logger.exception("failed to save sessions")

    def _load(self) -> None:
        if not self._store_path.exists():
            return
        try:
            raw = json.loads(self._store_path.read_text(encoding="utf-8"))
            for sid, d in raw.items():
                self._sessions[sid] = Session.from_dict(d)
            logger.info("loaded %d session(s) from %s", len(self._sessions), self._store_path)
        except Exception:
            logger.exception("failed to load sessions, starting fresh")
