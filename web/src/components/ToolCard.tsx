import React from "react";
import type { ToolEvent } from "../gateway/types";

const TOOL_LABELS: Record<string, string> = {
  save_customer_info: "保存客户信息",
  verify_identity: "身份核验",
  assess_risk_tolerance: "风险评估",
  check_compliance: "合规检查",
  create_account: "创建账户",
  get_application_progress: "查询进度",
};

interface Props {
  events: ToolEvent[];
}

export const ToolCard: React.FC<Props> = ({ events }) => {
  if (events.length === 0) return null;

  const grouped = new Map<string, ToolEvent[]>();
  for (const e of events) {
    const key = e.name;
    if (!grouped.has(key)) grouped.set(key, []);
    grouped.get(key)!.push(e);
  }

  return (
    <div className="tool-cards">
      {[...grouped.entries()].map(([name, evts]) => {
        const last = evts[evts.length - 1];
        const isDone = last.phase === "end";
        const isOk = last.success !== false;
        const label = TOOL_LABELS[name] ?? name;
        return (
          <div
            key={name}
            className={`tool-card ${isDone ? (isOk ? "tool-card--ok" : "tool-card--fail") : "tool-card--running"}`}
          >
            <span className="tool-card__icon">
              {isDone ? (isOk ? "✓" : "✗") : "⟳"}
            </span>
            <span className="tool-card__label">{label}</span>
            {isDone && last.message && (
              <span className="tool-card__msg">{last.message}</span>
            )}
          </div>
        );
      })}
    </div>
  );
};
