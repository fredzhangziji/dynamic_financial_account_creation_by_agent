import React, { useState, useRef, useCallback, useEffect } from "react";

const MAX_ROWS = 6;
const LINE_HEIGHT = 22;
const PADDING = 20;

interface Props {
  onSend: (message: string) => void;
  disabled: boolean;
}

export const InputBar: React.FC<Props> = ({ onSend, disabled }) => {
  const [text, setText] = useState("");
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const autoResize = useCallback(() => {
    const el = inputRef.current;
    if (!el) return;
    el.style.height = "auto";
    const maxHeight = LINE_HEIGHT * MAX_ROWS + PADDING;
    el.style.height = `${Math.min(el.scrollHeight, maxHeight)}px`;
  }, []);

  useEffect(() => {
    autoResize();
  }, [text, autoResize]);

  const handleSend = () => {
    const msg = text.trim();
    if (!msg || disabled) return;
    onSend(msg);
    setText("");
    requestAnimationFrame(() => {
      if (inputRef.current) {
        inputRef.current.style.height = "auto";
        inputRef.current.focus();
      }
    });
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
        placeholder={disabled ? "AI 正在思考..." : "输入消息，按 Enter 发送，Shift+Enter 换行"}
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
