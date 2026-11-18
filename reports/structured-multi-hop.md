# 结构化 Agent v0：`sales.multi_hop_lookup`

> 任务二实现记录（第一版）。目标不是一次性做完三个任务，而是先把
> S0–S7 结构在一个真实 AutomationBench 任务上端到端跑通。
>
> **最终结果与另外两个任务见 [structured-three-tasks.md](structured-three-tasks.md)。**

## 结构

`FLOW_AGENT_ULTRA`（36 个节点、44 条路由、1 个 async all/close 并行组）：

```text
S0 contract parse (LLM, max)
S1 parallel evidence: Gmail / Hierarchy / FX / Opportunity / Cases
S2 facts (LLM, max) + rule check
S3 plan (LLM, high) + JSON field extraction
S4 update opportunity → build base64 raw email → send executive
   → conditional support branch → send support
S5 score via world bridge + rule check
S6 repair 1/2 (bounded; resend + rescore)
S7 final action + audit
```

关键设计：LLM 只输出**语义字段**（stage、recipient、email body），
真正的 tool 参数（URL、method、Gmail raw base64）由确定性节点构造。
这避免了 LLM 生成相对 URL、错误 Gmail payload 等问题。

## 结果

| 运行 | 分数 | 断言 | 说明 |
|---|---:|---:|---|
| direct agent（max，60 题中的该题） | 0.333 | 1/3 | 只更新了 stage，两封邮件都没发 |
| structured v0 run 1 | **1.000** | **3/3** | 端到端通过 |
| structured v0 run 2 | **1.000** | **3/3** | 重置 WorldState 后重复，稳定通过 |
| structured v0 run 3 | **1.000** | **3/3** | 第三次重复；n=3 全通过 |
| 消融：去掉 S6 repair | **1.000** | **3/3** | 首次执行即通过，repair 贡献为 0 |

## 成本/时间

- 每次 structured run 约 2 分钟（3 次 LLM 调用，其中 S0/S2 用 max、S3 用 high）；
- LLM 调用：S0（max）、S2（max）、S3（high）各 1 次；
- 消融与三次重复见 [structured-three-tasks.md](structured-three-tasks.md)。

## 复现

```bash
# 1) 启动 WorldState bridge（重置状态）
cd automationbench-baseline
uv run --project ../datasets/AutomationBench python scripts/world_bridge.py \
  --domain sales --task sales.multi_hop_lookup --port 8765

# 2) 运行 rsi-flow structured agent
cd ../rsi-flow
CP="flow-test/target/test-classes:flow-test/target/classes:flow-core/target/classes:..."
java -cp "$CP" -Dbridge.url=http://127.0.0.1:8765 \
  -Dtask.name=sales.multi_hop_lookup \
  -Dresult.path=/tmp/ultra-result.json \
  cc.eamon.open.flow.FLOW_AGENT.UltraAgentRunner
```

## 观察

1. 直接让 LLM 生成完整 `api_fetch` args 会出错：相对 URL、Gmail `body` 而不是 `raw`；
2. 把 LLM 限制在语义层、由确定性节点构造 tool args 后，一次通过；
3. Gmail 必须用 `base64_encode` + `raw`，这是 rsi-flow ToolNode 需要显式建模的
   协议细节；
4. S6 的两轮 repair 在失败时会重复发邮件，后续应加“只修 missing”的精确修复，
   而不是简单重发。
