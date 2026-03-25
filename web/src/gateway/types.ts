/* WebSocket protocol types – aligned with server/gateway/protocol.py */

export interface RequestFrame {
  type: "req";
  id: string;
  method: string;
  params: Record<string, unknown>;
}

export interface ResponseFrame {
  type: "res";
  id: string;
  ok: boolean;
  payload?: Record<string, unknown>;
  error?: { code: string; message: string };
}

export interface EventFrame {
  type: "event";
  event: string;
  payload: Record<string, unknown>;
  seq: number;
}

export type InboundFrame = ResponseFrame | EventFrame;

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ToolEvent {
  phase: "start" | "end";
  name: string;
  success?: boolean;
  message?: string;
  arguments?: string;
}

export interface AccountInfo {
  account_number: string;
  type: string;
  label: string;
}

export interface ProgressState {
  customer_info: Record<string, string>;
  identity_verified: boolean;
  risk_assessed: boolean;
  risk_level: string | null;
  compliance_checked: boolean;
  account_created: boolean;
  accounts: AccountInfo[];
  available_types: { type: string; label: string }[];
  can_create_account: boolean;
  missing_requirements: string[];
}
