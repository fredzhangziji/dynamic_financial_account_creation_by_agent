import React from "react";
import ReactMarkdown from "react-markdown";
import type { ChatMessage } from "../gateway/types";

interface Props {
  message: ChatMessage;
}

export const MessageBubble: React.FC<Props> = ({ message }) => {
  const isUser = message.role === "user";
  return (
    <div className={`msg-row ${isUser ? "msg-row--user" : "msg-row--assistant"}`}>
      <div className={`msg-avatar ${isUser ? "msg-avatar--user" : "msg-avatar--assistant"}`}>
        {isUser ? "你" : "AI"}
      </div>
      <div className={`msg-bubble ${isUser ? "msg-bubble--user" : "msg-bubble--assistant"}`}>
        {isUser ? (
          <p>{message.content}</p>
        ) : (
          <ReactMarkdown>{message.content}</ReactMarkdown>
        )}
      </div>
    </div>
  );
};
