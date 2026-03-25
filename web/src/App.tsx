import React from "react";
import { useGateway } from "./hooks/useGateway";
import { ChatWindow } from "./components/ChatWindow";
import { ProgressPanel } from "./components/ProgressPanel";

const App: React.FC = () => {
  const { connected, messages, toolEvents, progress, loading, sendMessage } = useGateway();

  return (
    <div className="app">
      <header className="app-header">
        <h1 className="app-header__title">智能开户助手</h1>
        <span className={`app-header__status ${connected ? "app-header__status--on" : ""}`}>
          {connected ? "已连接" : "连接中..."}
        </span>
      </header>
      <main className="app-main">
        <ChatWindow
          messages={messages}
          toolEvents={toolEvents}
          loading={loading}
          onSend={sendMessage}
        />
        <ProgressPanel progress={progress} />
      </main>
    </div>
  );
};

export default App;
