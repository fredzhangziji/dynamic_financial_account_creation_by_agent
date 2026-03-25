import React from "react";
import type { ProgressState } from "../gateway/types";

interface Props {
  progress: ProgressState | null;
}

const STEPS = [
  { key: "info", label: "客户信息", check: (p: ProgressState) => {
    const required = ["name", "id_number", "phone"];
    return required.every((k) => p.customer_info[k] === "已填写");
  }},
  { key: "identity", label: "身份核验", check: (p: ProgressState) => p.identity_verified },
  { key: "risk", label: "风险评估", check: (p: ProgressState) => p.risk_assessed },
  { key: "compliance", label: "合规检查", check: (p: ProgressState) => p.compliance_checked },
  { key: "account", label: "账户创建", check: (p: ProgressState) => p.account_created },
];

export const ProgressPanel: React.FC<Props> = ({ progress }) => {
  return (
    <aside className="progress-panel">
      <h3 className="progress-panel__title">开户进度</h3>

      <div className="progress-steps">
        {STEPS.map((step) => {
          const done = progress ? step.check(progress) : false;
          return (
            <div key={step.key} className={`progress-step ${done ? "progress-step--done" : ""}`}>
              <span className="progress-step__dot">{done ? "✓" : ""}</span>
              <span className="progress-step__label">{step.label}</span>
            </div>
          );
        })}
      </div>

      {progress?.risk_level && (
        <div className="progress-detail">
          <span className="progress-detail__label">风险等级</span>
          <span className="progress-detail__value">{progress.risk_level}</span>
        </div>
      )}

      {progress?.account_number && (
        <div className="progress-detail progress-detail--success">
          <span className="progress-detail__label">账号</span>
          <span className="progress-detail__value">{progress.account_number}</span>
        </div>
      )}

      {progress && progress.missing_requirements.length > 0 && (
        <div className="progress-missing">
          <p className="progress-missing__title">待完成</p>
          <ul>
            {progress.missing_requirements.map((r) => (
              <li key={r}>{r}</li>
            ))}
          </ul>
        </div>
      )}
    </aside>
  );
};
