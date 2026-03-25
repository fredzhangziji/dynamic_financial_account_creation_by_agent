# 智能开户 Agent 系统

基于 **"网关 + Agent"** 架构的 AI 驱动金融开户系统。参考 [OpenClaw](https://github.com/anthropics/openclaw) 的核心设计思想，采用 ReAct 范式实现无固定流程的对话式开户体验。

## 业务背景

传统证券开户系统采用**固定步骤的向导式流程**——用户必须按照"填写信息 → 上传证件 → 风险评估 → 签署协议 → 开户"的顺序逐步操作，无法跳过或调整顺序。

本系统将开户流程交由 AI Agent 动态编排：

- **目标固定，路径自由**：开户需要完成信息采集、身份核验、风险评估、合规检查等事项，但 Agent 根据对话上下文灵活决定执行顺序
- **自然对话交互**：用户通过聊天完成开户，无需填写表单
- **智能信息处理**：用户一次提供多项信息时批量处理，不重复询问已知内容
- **即时反馈**：工具执行状态实时推送，进度面板同步更新

## 架构设计

```
┌───────────────────────┐
│   前端 (React+Vite)    │
│  ChatWindow  Progress │
│    GatewayClient      │
└─────────┬─────────────┘
          │ WebSocket (JSON 帧)
┌─────────┴─────────────┐
│   网关层 (FastAPI)     │
│  方法分发 · 会话管理     │
└─────────┬─────────────┘
          │
┌─────────┴─────────────┐
│   Agent 运行时         │
│  ReAct 循环 (LLM+Tool) │
└─────────┬─────────────┘
          │
┌─────────┴─────────────┐
│   业务工具              │
│  信息采集 · 身份核验     │
│  风险评估 · 合规检查     │
│  账户创建 · 进度查询     │
└───────────────────────┘
```

### 消息流转

1. 用户通过前端发送消息 → WebSocket `req` 帧到达网关
2. 网关按 `method` 字符串分发到对应 handler
3. `chat.send` handler 启动异步 Agent 任务，立即返回 `res` 确认
4. Agent 运行时进入 ReAct 循环：调用 LLM → 执行工具 → 回填结果 → 再调 LLM → ... → 生成最终回复
5. 每个阶段通过 WebSocket `event` 帧实时推送到前端

### 业务工具

| 工具 | 功能 | 模拟策略 |
|------|------|---------|
| `save_customer_info` | 保存客户信息（增量更新） | 格式校验（身份证18位、手机11位等） |
| `verify_identity` | 身份核验 | 模拟1秒延迟，格式正确即通过 |
| `assess_risk_tolerance` | 风险评估 | 评分矩阵计算风险等级 |
| `check_compliance` | 合规检查（反洗钱） | 内置测试黑名单筛查 |
| `create_account` | 创建账户 | 检查前置条件，生成模拟账号 |
| `get_application_progress` | 查询进度 | 返回各步骤完成状态 |

## 与 OpenClaw 的架构对标

本系统参考了 OpenClaw 的架构分层和设计决策：

| 设计要素 | OpenClaw | 本系统 |
|---------|----------|--------|
| 通信协议 | WebSocket + `req/res/event` JSON 帧 | 完全对齐 |
| 请求路由 | `coreGatewayHandlers` 方法字符串分发 | `handlers.py` 方法分发表 |
| Agent 执行 | `runEmbeddedPiAgent` + Pi 工具循环 | `AgentRuntime.run()` ReAct 循环 |
| 工具接口 | `AgentTool { name, description, parameters, execute }` | `BaseTool` 抽象类（Pydantic Schema） |
| 工具注册 | `createOpenClawTools` + `tool-catalog.ts` | `ToolRegistry` + 各业务工具 |
| 事件推送 | `emitAgentEvent` 事件总线 | WebSocket `event` 帧异步推送 |
| 会话管理 | `SessionManager` + freshness 策略 | `SessionManager` JSON 文件持久化 |
| 异步派发 | `dispatchAgentRunFromGateway` fire-and-forget | `asyncio.create_task` 异步执行 |
| 前端客户端 | `GatewayBrowserClient` (Lit) | `GatewayClient` (React) |
| 工具卡片 | `tool-cards.ts` 可折叠状态卡片 | `ToolCard.tsx` 状态卡片 |
| Schema 校验 | TypeBox → JSON Schema | Pydantic → JSON Schema |

## 技术栈

- **后端**: Python 3.11+ / FastAPI / WebSocket / OpenAI SDK / Pydantic
- **前端**: React 18 / TypeScript / Vite / react-markdown
- **LLM**: OpenAI 兼容 API（支持通义千问、DeepSeek、Ollama 等）

## 环境配置

### 前置条件

- Python 3.11+
- Node.js 18+
- 一个 OpenAI 兼容 API 的密钥（通义千问、DeepSeek 等）

### 1. 配置 LLM API

```bash
cd server
cp .env.example .env
```

编辑 `server/.env`，填入实际的 API 配置：

```env
# 通义千问示例
OPENAI_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_API_KEY=sk-your-api-key
OPENAI_MODEL=qwen3-max

# DeepSeek 示例
# OPENAI_API_BASE=https://api.deepseek.com/v1
# OPENAI_API_KEY=sk-your-api-key
# OPENAI_MODEL=deepseek-chat

# 本地 Ollama 示例
# OPENAI_API_BASE=http://localhost:11434/v1
# OPENAI_API_KEY=ollama
# OPENAI_MODEL=qwen2.5:latest
```

### 2. 安装依赖

```bash
# 后端
cd server
pip install -r requirements.txt

# 前端
cd web
npm install
```

## 启动运行

需要两个终端，分别启动后端和前端：

```bash
# 终端 1：启动后端网关（默认 8000 端口）
cd server
python3 main.py

# 终端 2：启动前端开发服务器（默认 5173 端口）
cd web
npm run dev
```

打开浏览器访问 `http://localhost:5173`，即可开始对话式开户。

## 数据持久化

系统会将会话记录、客户信息和账户数据持久化到本地 JSON 文件：

```
server/data/sessions.json
```

- 后端首次运行时自动创建 `data/` 目录和文件
- 每次对话完成后自动保存，重启后端或刷新页面后历史记录和开户进度会自动恢复
- 当前为单用户模式，每次连接自动加载最近一次会话

**清空所有数据**（重新开始）：

```bash
rm -rf server/data
```

删除后重启后端即可以全新状态开始。

## 目录结构

```
├── server/                          # 后端
│   ├── main.py                      # 启动入口
│   ├── config.py                    # 环境变量配置
│   ├── .env.example                 # 配置模板
│   ├── requirements.txt             # Python 依赖
│   ├── gateway/
│   │   ├── server.py                # FastAPI + WebSocket 端点
│   │   ├── protocol.py              # req/res/event 帧协议
│   │   ├── session.py               # 会话管理 + 开户进度 + JSON 持久化
│   │   └── handlers.py              # 方法分发表
│   ├── agent/
│   │   ├── runtime.py               # ReAct 循环（LLM + Tool loop）
│   │   ├── prompts.py               # 系统提示词
│   │   └── tools/
│   │       ├── registry.py          # 工具基类 + 注册表
│   │       ├── customer_info.py     # 客户信息采集
│   │       ├── identity.py          # 身份核验（模拟）
│   │       ├── risk_assessment.py   # 风险评估（评分矩阵）
│   │       ├── compliance.py        # 合规检查（模拟）
│   │       └── account.py           # 账户创建 + 进度查询
│   ├── data/
│   │   └── sessions.json           # 持久化数据（自动生成，已 gitignore）
│   └── models/
│       ├── customer.py              # 客户数据模型
│       └── account.py               # 账户数据模型
├── web/                             # 前端
│   ├── vite.config.ts               # Vite 配置（含 WS 代理）
│   └── src/
│       ├── App.tsx                  # 主布局
│       ├── gateway/
│       │   ├── client.ts            # WebSocket 客户端
│       │   └── types.ts             # 协议类型
│       ├── components/
│       │   ├── ChatWindow.tsx       # 聊天容器
│       │   ├── MessageBubble.tsx    # 消息气泡（Markdown）
│       │   ├── ToolCard.tsx         # 工具状态卡片
│       │   ├── InputBar.tsx         # 输入栏
│       │   └── ProgressPanel.tsx    # 开户进度面板
│       └── hooks/
│           └── useGateway.ts        # 网关连接 Hook
```
