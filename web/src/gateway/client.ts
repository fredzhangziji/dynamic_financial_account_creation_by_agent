/**
 * WebSocket gateway client – aligned with OpenClaw's GatewayBrowserClient.
 * Handles req/res pairing and event streaming.
 */

import type { RequestFrame, ResponseFrame, EventFrame, InboundFrame } from "./types";

type PendingEntry = {
  resolve: (payload: Record<string, unknown>) => void;
  reject: (err: Error) => void;
};

type EventHandler = (event: EventFrame) => void;

let idCounter = 0;
function nextId(): string {
  return `r${++idCounter}-${Date.now().toString(36)}`;
}

export class GatewayClient {
  private ws: WebSocket | null = null;
  private pending = new Map<string, PendingEntry>();
  private eventHandlers: EventHandler[] = [];
  private _connected = false;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private url: string;

  constructor(url: string) {
    this.url = url;
  }

  get connected(): boolean {
    return this._connected;
  }

  connect(): void {
    if (this.ws) return;
    this.ws = new WebSocket(this.url);

    this.ws.addEventListener("open", () => {
      this._connected = true;
    });

    this.ws.addEventListener("message", (ev) => {
      this.handleMessage(String(ev.data));
    });

    this.ws.addEventListener("close", () => {
      this._connected = false;
      this.ws = null;
      this.rejectAllPending("connection closed");
      this.scheduleReconnect();
    });

    this.ws.addEventListener("error", () => {
      this.ws?.close();
    });
  }

  disconnect(): void {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.ws?.close();
    this.ws = null;
    this._connected = false;
  }

  async request(method: string, params: Record<string, unknown> = {}): Promise<Record<string, unknown>> {
    return new Promise((resolve, reject) => {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
        reject(new Error("not connected"));
        return;
      }
      const id = nextId();
      this.pending.set(id, { resolve, reject });
      const frame: RequestFrame = { type: "req", id, method, params };
      this.ws.send(JSON.stringify(frame));
    });
  }

  onEvent(handler: EventHandler): () => void {
    this.eventHandlers.push(handler);
    return () => {
      this.eventHandlers = this.eventHandlers.filter((h) => h !== handler);
    };
  }

  // ── Internal ──────────────────────────────────────────────────────

  private handleMessage(raw: string): void {
    let frame: InboundFrame;
    try {
      frame = JSON.parse(raw);
    } catch {
      return;
    }

    if (frame.type === "res") {
      const res = frame as ResponseFrame;
      const entry = this.pending.get(res.id);
      if (entry) {
        this.pending.delete(res.id);
        if (res.ok) {
          entry.resolve(res.payload ?? {});
        } else {
          entry.reject(new Error(res.error?.message ?? "request failed"));
        }
      }
    } else if (frame.type === "event") {
      const evt = frame as EventFrame;
      for (const h of this.eventHandlers) {
        try {
          h(evt);
        } catch { /* handler error */ }
      }
    }
  }

  private rejectAllPending(reason: string): void {
    for (const [, entry] of this.pending) {
      entry.reject(new Error(reason));
    }
    this.pending.clear();
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer) return;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, 2000);
  }
}
