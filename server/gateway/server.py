"""FastAPI application with WebSocket gateway endpoint."""

from __future__ import annotations

import json
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from gateway.protocol import error_response
from gateway.session import SessionManager
from gateway.handlers import dispatch, RequestContext
from agent.runtime import create_runtime

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Account-Opening Agent Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions = SessionManager()
agent_runtime = create_runtime(sessions)


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    await ws.accept()
    logger.info("client connected")
    try:
        while True:
            raw = await ws.receive_text()
            try:
                frame = json.loads(raw)
            except json.JSONDecodeError:
                await ws.send_json(error_response("?", "PARSE_ERROR", "invalid JSON"))
                continue

            frame_type = frame.get("type")
            if frame_type != "req":
                await ws.send_json(error_response("?", "INVALID_FRAME", "expected type=req"))
                continue

            req_id = frame.get("id", "?")
            method = frame.get("method", "")
            params = frame.get("params", {})

            ctx = RequestContext(ws=ws, sessions=sessions, agent=agent_runtime, req_id=req_id)
            response = await dispatch(method, params, ctx)
            if response is not None:
                await ws.send_json(response)

    except WebSocketDisconnect:
        logger.info("client disconnected")
    except Exception:
        logger.exception("ws error")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
