# 任务二设计方案：S0–S7 超长可验证 Agent 结构

> 状态：**设计稿，待讨论**。本文件对应任务二的 5 分“方案”部分；确认后再在
> rsi-flow `test` 分支实现（5 分“实现”部分）。
>
> 设计基于 rsi-flow 现有的顺序（routes）、条件分支（JEXL condition）、
> 嵌套 flow（`type: flow`）、async all/close（`strategies`），以及已实现的
> `LlmNode` / `ToolNode` / `FinalActionNode` / `VerifierNode`。
> 引擎细节与坑见 [rsi-flow-internals.md](rsi-flow-internals.md)。

## 1. 要解决的问题

任务一的失败机制编码给出六个可干预缺口：

| 机制 | 现象 | 结构缺口 |
|---|---|---|
| M1 工具/数据源 | 调错应用、401 后不换源 | 没有固定工具绑定与 fallback |
| M2 规则/资格 | 阈值/日期/最新公告判错 | 没有规则抽取 + 确定性过滤节点 |
| M3 路由/优先级 | 收件人/团队/tier/时段错 | 没有显式路由表 |
| M4 长链/最后动作 | 查到了但没写回/没发通知 | 没有强制收尾节点 |
| M5 集合/负约束 | 多做、把排除对象纳入 | 没有负约束 guard |
| M6 收尾校验 | 只差 1–2 条断言 | 没有最终状态校验/修复 |

任务二不是“让模型多想一会儿”，而是把这些缺口变成**显式结构**。

## 2. 总体架构：S0–S7

```text
FLOW_AGENT_ULTRA (root, sequence)
│
├─ S0 CONTRACT_PARSE            LLM：任务契约 → contract_json
│
├─ S1 EVIDENCE_GATHER           async all / close
│   ├─ EVID_GMAIL               Tool → LLM extract → ev_gmail_json
│   ├─ EVID_SHEETS              Tool → LLM extract → ev_sheets_json
│   ├─ EVID_SALESFORCE          Tool → LLM extract → ev_sf_json
│   └─ EVID_ZENDESK             Tool → LLM extract → ev_zd_json
│   └─ JOIN_EVIDENCE            幂等 join
│
├─ S2 NORMALIZE_RULES           LLM + Rule/Filter：fact_json
│
├─ S3 PLAN                      LLM：plan_json（DAG + negative constraints）
│   └─ PLAN_VALIDATE            确定性校验：工具/步骤/负约束
│
├─ S4 EXECUTE                   sequence + branch + nested
│   ├─ EXEC_UPDATE              ToolNode：更新记录
│   ├─ EXEC_ROUTE               Branch：tier / escalation / priority
│   ├─ EXEC_NOTIFY              ToolNode：发通知（分支目标）
│   └─ EXEC_WRITEBACK           ToolNode：写回表格/备注
│
├─ S5 VERIFY                    Verifier：正向 + 负向 + 计数 + 最后动作
│   └─ verify_json {passed, missing[]}
│
├─ S6 REPAIR (bounded ×2)       Branch：repair_needed / done
│   ├─ REPAIR_1                 只修 missing 的动作 → 再 verify
│   └─ REPAIR_2                 第二次有界修复 → 再 verify
│
├─ S7 FINALIZE + AUDIT          FinalAction + Audit
│   └─ audit_json（trace/tokens/cost/decisions）
│
└─ end
```

**规模**：约 25–40 个节点、4–6 个嵌套子流程、2 个并行组、3+ 个条件分支、
2 轮有界修复。它不是线性 prompt 链，而是“分层 + 并行 + 分支 + 嵌套 + 校验修复”的
超长结构。

## 3. 设计原则

### 3.1 LLM 只做判断，不做控制流

- **LLM 节点**：契约解析、证据抽取、规则歧义消解、计划生成、修复计划。
- **确定性节点**：工具绑定、过滤、路由、计数、负约束、最终动作、校验。
- 控制流（顺序/分支/并行/嵌套）全部由 flow JSON 决定，不由模型自由选择。

### 3.2 每个阶段有数据契约

阶段之间只传 JSON 字符串，字段固定；LLM 输出必须过 schema 校验，失败则走
fallback/repair，不允许“看起来像 JSON”就往下走。

### 3.3 结构对应机制

| 机制 | 结构组件 |
|---|---|
| M1 | S1 `ToolNode` 固定 app/action + retry/fallback |
| M2 | S2 `RuleNode` + `FilterNode` |
| M3 | S4 `BranchNode` + 显式路由表 |
| M4 | S4 sequence + S7 `FinalActionNode` |
| M5 | S2/S5 negative guard |
| M6 | S5 `VerifierNode` + S6 bounded repair |

### 3.4 不假装支持没有的能力

rsi-flow 没有循环、动态扇出、重试、checkpoint。设计上用：

- **有界修复分支**（REPAIR_1/REPAIR_2）代替 while；
- **固定任务模板**（3 个任务的步骤数写死）代替动态 fan-out；
- **节点内 retry/fallback** 代替引擎级重试；
- **preflight 校验脚本** 代替被注释掉的 CheckEntrance。

这些限制会写进“风险与限制”，不把权宜之计说成通用能力。

## 4. 阶段与数据契约

### S0 CONTRACT_PARSE

- 节点：`LLM_CALL`（prompt = 任务原文 + 输出 schema）；
- 输出 `contract_json`：

```json
{
  "goal": "mark deal won and notify the right team",
  "entities": {"account": "Meridian Corp", "opportunity": "Platform Deal"},
  "required_actions": ["update_opportunity", "send_notification"],
  "constraints": ["use latest routing policy", "currency conversion required"],
  "sources": ["gmail", "sheets", "salesforce", "zendesk"],
  "success_criteria": ["stage=Closed Won", "correct recipient", "amount=$156,000"]
}
```

- 校验：字段齐全、`required_actions` 非空；失败走 `CONTRACT_FALLBACK`（规则模板）。

### S1 EVIDENCE_GATHER

- 4 个嵌套子流程并行（async all/close）；
- 每个子流程：`ToolNode`（固定 app/action）→ `LLM_CALL`（抽取字段）→
  `VERIFY_CONTAINS`（关键字段）；
- 输出 `ev_*_json`，并汇总 `evidence_json`：

```json
{
  "sources": [
    {"name": "gmail", "status": "ok", "records": [...], "errors": []},
    {"name": "sheets", "status": "degraded", "records": [...], "errors": ["FX sheet missing"]}
  ],
  "missing_sources": ["zendesk"]
}
```

- 失败处理：每个 ToolNode 内部 retry 1 次；仍失败则记 `degraded`，不直接终止；
  S5 会把“缺证据”当成 missing 处理。

### S2 NORMALIZE_RULES

- 确定性节点：
  - 日期/币种/ID 归一化；
  - 最新公告/政策选择（按时间戳）；
  - 阈值/资格过滤（`FilterNode`）；
  - 冲突记录。
- LLM 只在规则文本有歧义时做抽取，输出必须带 `source_quote`。
- 输出 `fact_json`：

```json
{
  "entities": {...},
  "policy": {"id": "...", "effective_at": "...", "source": "gmail"},
  "thresholds": {"sla_hours": 24, "window_days": 14},
  "eligible": ["..."],
  "excluded": ["..."],
  "conflicts": []
}
```

### S3 PLAN

- LLM 生成 `plan_json`，步骤带依赖、前置/后置条件、负约束；
- `PLAN_VALIDATE` 确定性校验：
  - 工具必须在注册表中；
  - 必做动作不能缺；
  - 负约束必须进入 plan 的 guard；
  - 步骤依赖不能成环。
- 输出：

```json
{
  "steps": [
    {"id": "s1", "action": "update_opportunity", "tool": "salesforce.update",
     "args": {...}, "depends_on": [], "postconditions": ["stage=Closed Won"]},
    {"id": "s2", "action": "notify_exec", "tool": "gmail.send",
     "args": {...}, "depends_on": ["s1"], "postconditions": ["to=executive-team"]}
  ],
  "negative_constraints": ["do_not_email_ops_if_no_escalation"]
}
```

### S4 EXECUTE

- 按 `depends_on` 顺序执行；独立步骤可用 async all，但只允许写唯一 key；
- `EXEC_ROUTE` 用 JEXL 条件：
  - `tier == 'Enterprise' && hasEscalation == true` → 双通知；
  - `tier != 'Enterprise' || hasEscalation == false` → 单通知；
  - `default` 兜底；
- 每个动作：pre-check → ToolNode → post-check → `execution_log_json`。

### S5 VERIFY

- `VerifierNode` 检查：
  - 正向：记录存在、字段相等、消息发给正确收件人；
  - 负向：不该存在的记录/消息不存在；
  - 计数：集合大小等于 N；
  - 最后动作：写回/通知已完成。
- 输出 `verify_json`：

```json
{"passed": false, "missing": [
  {"type": "missing_message", "target": "support-escalation", "expected": "$156,000"}
]}
```

### S6 REPAIR（有界 2 轮）

- `BranchNode`：`verify.passed == true` → S7；否则 → REPAIR_1；
- REPAIR_1：只针对 `missing[]` 生成修复计划（LLM + 确定性映射），执行后重新 verify；
- 仍失败 → REPAIR_2；再失败 → 记录 `unrepaired`，进入 S7 但标记失败；
- 不使用 while，避免引擎不支持循环。

### S7 FINALIZE + AUDIT

- `FinalActionNode`：确保最终写回/通知真的执行；未注册或失败则抛异常；
- `AuditNode`：记录每阶段输入/输出摘要、重试次数、token/成本、失败原因；
- 输出 `audit_json`，供评测和报告使用。

## 5. 节点清单

| 阶段 | 节点 | 类型 | 说明 |
|---|---|---|---|
| S0 | `CONTRACT_PARSE` | LLM | 任务契约 |
| S0 | `CONTRACT_FALLBACK` | 确定性 | 模板兜底 |
| S1 | `EVID_*` | nested flow | 每个数据源一个子流程 |
| S1 | `EVID_*_READ` | Tool | 固定 app/action |
| S1 | `EVID_*_EXTRACT` | LLM | 字段抽取 |
| S1 | `JOIN_EVIDENCE` | 确定性 | 幂等 join |
| S2 | `NORMALIZE` | 确定性 | 日期/币种/ID |
| S2 | `POLICY_SELECT` | 确定性/LLM | 最新政策 |
| S2 | `FILTER_ELIGIBLE` | 确定性 | 资格过滤 |
| S3 | `PLAN` | LLM | DAG |
| S3 | `PLAN_VALIDATE` | 确定性 | 工具/依赖/负约束 |
| S4 | `EXEC_*` | Tool/Branch | 执行/路由 |
| S5 | `VERIFY` | Verifier | 正向/负向/计数 |
| S6 | `REPAIR_1/2` | Branch+nested | 有界修复 |
| S7 | `FINALIZE` | FinalAction | 强制收尾 |
| S7 | `AUDIT` | 确定性 | trace/cost |

## 6. 三个任务的实例化

### 6.1 `sales.multi_hop_lookup`（P2，首选）

- S1：Gmail routing policy、Sheets Account Hierarchy/FX、Salesforce opportunity、
  Zendesk open cases；
- S2：最新 policy、tier、币种换算、escalation 条件；
- S3：更新 opportunity、发 executive/support 邮件；
- S4：`tier == Enterprise && hasEscalation` → 双通知；否则单通知；
- S5：stage=Closed Won、金额 $156,000、收件人正确、无错误收件人；
- S6：缺邮件/字段时修复。

### 6.2 `operations.generator_load_testing_schedule`（P4a）

- S1：generators、engineers、calendar；
- S2：频率规则、14 天窗口、skip 状态（Under Repair/Event/Emergency）；
- S3：生成测试列表 + 日历事件；
- S4：建事件、按 building 发邮件（固定 N，写死节点）；
- S5：事件存在、日期正确、skip 单元未建；
- S6：修复漏建/日期错。

### 6.3 `support.zendesk_sf_case_sync`（P3）

- S1：blocklist/SLA/config 并行 + Zendesk tickets；
- S2：过滤 + 优先级；
- S3：创建 Salesforce cases、Zendesk comments、Slack summary；
- S4：顺序创建 + 唯一 key 写回；
- S5：case 数量、字段、Slack 计数；
- S6：修复漏建/计数错。

## 7. 评估协议

- **Direct**：官方 `auto-bench` 的 direct agent（已有 `results/medium-max` 的同配置结果）；
- **Structured**：同一任务、同一模型/工具集/max_steps/max effort/API 路径；
- 每个任务每个条件 **3 次**；方差大再补到 5 次；
- 指标：pass、partial、steps、token、cost、wall time、修复轮次、机制级断言失败数；
- **节点消融**：去掉 Verifier、FinalAction、Router 各跑一次；
- **步数对照**：给 direct agent 相同步数上限，排除“只是多跑了几步”；
- **公平性**：同 prompt、同 initial_state、同工具、同评分 rubric。

### 成功/失败判据

- 强证据：3 个任务中至少 2 个 pass 提升，且对应机制断言失败数下降；
- 中等证据：partial 提升但 pass 不变；
- 负结果：structured 更差或成本 >2× 且无 pass 提升——如实报告。

### 假设

- H1：FinalAction/Verifier 减少 M4/M6，提升 P9/P3；
- H2：路由表减少 P4b 的收件人/tier 错误；
- H3：规则抽取 + 确定性过滤减少 P4a 的集合成员错误；
- H4：收益不是“多跑几步”——步数/token 对照 + 消融。

## 8. 风险与限制

1. **async 上下文是浅拷贝**：并行分支共享 `HashMap`，并发写不安全。
   设计上只并行只读取证，每个分支写唯一变量名；必要时把
   `FlowScopeContext.variableMap` 改成 `ConcurrentHashMap`（需单独评审）。
2. **async 异常被吞**：分支失败只打印；靠下游 `notnull` 和 S5 校验暴露。
3. **close 可能重复入队**：JOIN 必须幂等。
4. **没有循环/动态扇出**：修复用有界分支；3 个任务写死步骤数。
5. **没有静态校验**：实现前先写 preflight 脚本检查 node id、route target、
   params/results 数量、嵌套 flow、变量冲突。
6. **WorldState 桥接工作量大**：先把 `sales.multi_hop_lookup` 的 4 个数据源
   接进来，再扩另外两个任务。
7. **成本**：3 任务 × 2 条件 × 3 次 ≈ $18–54（max effort）；先跑 1 个任务约 $6–18。

## 9. 实现顺序（设计确认后）

1. preflight 校验脚本 + AutomationBench WorldState 的 ToolRegistry bridge；
2. `FLOW_AGENT_ULTRA` 根流程 + S0/S1/S5/S7 最小闭环；
3. 加 S2/S3/S4 和 `sales.multi_hop_lookup` 的 flow JSON；
4. 跑 direct vs structured（3 次）+ 消融；
5. 扩到另外两个任务；
6. 写回报告的任务二章节。

## 10. 需要讨论/确认的点

1. 是否先只实现 `sales.multi_hop_lookup`，还是三个任务一起设计、分步实现？
2. S6 用 2 轮有界修复，还是先 1 轮？
3. 是否允许修改 `FlowScopeContext.variableMap` 为 `ConcurrentHashMap`（修复 async 并发）？
4. ToolRegistry 是先接真实 WorldState，还是先用 mock 工具验证结构？
5. 3 任务 × 2 条件 × 3 次的预算是否按 $18–54 执行？

## 11. v0 实现结果（2026-11-18）

已在 `test` 分支落地 S0–S7 的第一版：

- `FLOW_AGENT_ULTRA`：36 个节点、44 条路由、1 个 async all/close 并行组；
- 新增 `RuleNode`、`FilterNode`、`AuditNode`、`ContextSnapshotNode`、
  `JsonFieldNode`、`Template`、`BridgeToolHandler`、`BridgeScoreHandler`；
- `AutomationBench WorldState` 通过 `scripts/world_bridge.py` 以本地 HTTP 暴露，
  Java `ToolNode` 通过 registry 调用；
- `FlowScopeContext` 改为 `ConcurrentHashMap`，`Executor` 队列按整队去重，
  修复 async 并行/close 的基础问题；
- 测试：`mvn-rsi.sh -pl flow-test -am test` **21/21**。

结果（同一题 `sales.multi_hop_lookup`）：

| 条件 | 分数 | 断言 |
|---|---:|---:|
| direct agent（max，60 题中的该题） | 0.333 | 1/3 |
| structured v0 run 1 | **1.000** | **3/3** |
| structured v0 run 2 | **1.000** | **3/3** |

关键发现：让 LLM 生成完整 `api_fetch` args 会失败（相对 URL、Gmail `body` 而非
`raw`）；把 LLM 限制在语义层、由确定性节点构造 tool args 后，两次都通过。

**当前限制**：只有 1 个任务、2 次重复；没有节点消融、步数对照、3 次重复；
S3 因中转站 524 用了 `high` 而不是 `max`；修复轮次是简单重发，不是“只修 missing”。
这些是下一步，不把 v0 说成完整实验。

## 12. 三个任务全部落地（2026-11-18）

在 v0 基础上补齐另外两个任务，并完成重复与消融：

| flow | 任务 | 节点/路由 | LLM 调用 | 结构重点 |
|---|---|---:|---:|---|
| `FLOW_AGENT_ULTRA` | sales.multi_hop_lookup | 36 / 44 | 3 | 并行证据、受限 LLM、条件分支、repair |
| `FLOW_AGENT_OPS` | operations.generator_load_testing_schedule | 37 / 41 | 0 | `RowsNode` + `WhereNode` 规则过滤、逐条确定性执行 |
| `FLOW_AGENT_SUPPORT` | support.zendesk_sf_case_sync | 60 / 70 | 1 | 8 路并行读取、单次 LLM 归一化、确定性写入 |

新增通用节点 `RowsNode`（Sheets `values` → 行对象）与
`WhereNode`（行级 JEXL 过滤，支持模板变量），
让“读表 → 按规则过滤 → 行动”可以完整落在 flow 里，而不是把结论写死。

结果与消融见 [../reports/structured-three-tasks.md](../reports/structured-three-tasks.md)：

- direct 三题分别 0.333 / 0.857 / 0.750，structured 全部 1.000；
- sales 三次重复全通过；去掉 S6 repair 仍 1.000；
- operations 串行读取仍 1.000；support 去掉“已存在 Case 去重”降到 0.9375。

仍然存在的限制：flow 按任务手工编译、节点数写死；rsi-flow 没有循环/动态扇出；
样本小；bridge 不是官方运行时。
