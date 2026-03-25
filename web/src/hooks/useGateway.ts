import { useCallback, useEffect, useRef, useState } from "react";
import { GatewayClient } from "../gateway/client";
import type { EventFrame, ChatMessage, ToolEvent, ProgressState } from "../gateway/types";

const WS_URL = `${location.protocol === "https:" ? "wss:" : "ws:"}//${location.host}/ws`;

export function useGateway() {
  const clientRef = useRef<GatewayClient | null>(null);
  const [connected, setConnected] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [toolEvents, setToolEvents] = useState<ToolEvent[]>([]);
  const [progress, setProgress] = useState<ProgressState | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const client = new GatewayClient(WS_URL);
    clientRef.current = client;

    const unsub = client.onEvent((evt: EventFrame) => {
      if (evt.event === "assistant" || evt.event === "chat") {
        const content = evt.payload.content as string;
        if (content) {
          setMessages((prev) => [...prev, { role: "assistant", content }]);
          setLoading(false);
        }
      } else if (evt.event === "tool") {
        const te: ToolEvent = {
          phase: evt.payload.phase as "start" | "end",
          name: evt.payload.name as string,
          success: evt.payload.success as boolean | undefined,
          message: evt.payload.message as string | undefined,
          arguments: evt.payload.arguments as string | undefined,
        };
        setToolEvents((prev) => [...prev, te]);
      } else if (evt.event === "error") {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: `⚠️ ${evt.payload.message ?? "发生错误"}` },
        ]);
        setLoading(false);
      }
    });

    client.connect();

    const poll = setInterval(() => {
      setConnected(client.connected);
    }, 500);

    return () => {
      unsub();
      clearInterval(poll);
      client.disconnect();
    };
  }, []);

  const initialize = useCallback(async () => {
    const client = clientRef.current;
    if (!client) return;
    try {
      const res = await client.request("connect", {});
      const sid = res.session_id as string;
      setSessionId(sid);
    } catch { /* retry on next connect */ }
  }, []);

  useEffect(() => {
    if (connected && !sessionId) {
      initialize();
    }
  }, [connected, sessionId, initialize]);

  const sendMessage = useCallback(
    async (message: string) => {
      const client = clientRef.current;
      if (!client || !sessionId) return;
      setMessages((prev) => [...prev, { role: "user", content: message }]);
      setToolEvents([]);
      setLoading(true);
      try {
        await client.request("chat.send", { session_id: sessionId, message });
      } catch {
        setLoading(false);
      }
    },
    [sessionId]
  );

  const refreshProgress = useCallback(async () => {
    const client = clientRef.current;
    if (!client || !sessionId) return;
    try {
      const res = await client.request("session.status", { session_id: sessionId });
      setProgress(res.progress as ProgressState);
    } catch { /* ignore */ }
  }, [sessionId]);

  useEffect(() => {
    if (!loading && sessionId) {
      refreshProgress();
    }
  }, [loading, sessionId, refreshProgress]);

  return { connected, sessionId, messages, toolEvents, progress, loading, sendMessage };
}
