import React, { useEffect, useRef } from "react";
import type { ChatMessage, ToolEvent } from "../gateway/types";
import { MessageBubble } from "./MessageBubble";
import { ToolCard } from "./ToolCard";
import { InputBar } from "./InputBar";

interface Props {
  messages: ChatMessage[];
  toolEvents: ToolEvent[];
  loading: boolean;
  onSend: (message: string) => void;
}

export const ChatWindow: React.FC<Props> = ({ messages, toolEvents, loading, onSend }) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, toolEvents, loading]);

  return (
    <section className="chat-window">
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-welcome">
            <h2>欢迎使用智能开户助手</h2>
            <p>我将协助您完成证券账户开通，随时可以开始对话。</p>
          </div>
        )}
        {messages.map((msg, i) => (
          <MessageBubble key={i} message={msg} />
        ))}
        <ToolCard events={toolEvents} />
        {loading && (
          <div className="msg-row msg-row--assistant">
            <div className="msg-avatar msg-avatar--assistant">AI</div>
            <div className="msg-bubble msg-bubble--assistant msg-bubble--typing">
              <span className="typing-dot" />
              <span className="typing-dot" />
              <span className="typing-dot" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <InputBar onSend={onSend} disabled={loading} />
    </section>
  );
};
