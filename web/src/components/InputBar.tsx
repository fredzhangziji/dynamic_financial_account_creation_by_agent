import React, { useState, useRef } from "react";

interface Props {
  onSend: (message: string) => void;
  disabled: boolean;
}

export const InputBar: React.FC<Props> = ({ onSend, disabled }) => {
  const [text, setText] = useState("");
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    const msg = text.trim();
    if (!msg || disabled) return;
    onSend(msg);
    setText("");
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="input-bar">
      <textarea
        ref={inputRef}
        className="input-bar__textarea"
        placeholder={disabled ? "AI 正在思考..." : "输入消息，按 Enter 发送..."}
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        rows={1}
      />
      <button
        className="input-bar__btn"
        onClick={handleSend}
        disabled={disabled || !text.trim()}
      >
        发送
      </button>
    </div>
  );
};
