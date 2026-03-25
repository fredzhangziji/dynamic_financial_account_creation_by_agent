"""WebSocket JSON frame protocol, aligned with OpenClaw's req/res/event model."""

from __future__ import annotations

import uuid
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class FrameType(str, Enum):
    REQ = "req"
    RES = "res"
    EVENT = "event"


# ── Inbound (client → gateway) ──────────────────────────────────────────────

class RequestFrame(BaseModel):
    type: FrameType = FrameType.REQ
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    method: str
    params: dict[str, Any] = Field(default_factory=dict)


# ── Outbound (gateway → client) ─────────────────────────────────────────────

class ResponseFrame(BaseModel):
    type: FrameType = FrameType.RES
    id: str
    ok: bool
    payload: dict[str, Any] | None = None
    error: dict[str, str] | None = None


class EventFrame(BaseModel):
    type: FrameType = FrameType.EVENT
    event: str
    payload: dict[str, Any] = Field(default_factory=dict)
    seq: int = 0


# ── Helpers ──────────────────────────────────────────────────────────────────

def ok_response(req_id: str, payload: dict[str, Any] | None = None) -> dict:
    return ResponseFrame(id=req_id, ok=True, payload=payload).model_dump()


def error_response(req_id: str, code: str, message: str) -> dict:
    return ResponseFrame(
        id=req_id, ok=False, error={"code": code, "message": message}
    ).model_dump()


def event_frame(event: str, payload: dict[str, Any], seq: int = 0) -> dict:
    return EventFrame(event=event, payload=payload, seq=seq).model_dump()
