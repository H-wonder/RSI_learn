# 结构验证方案（任务一 → 任务二）

> 任务一最后一句是“下一步需要在其中验证结构”。这份文档就是那一步的具体方案。
> 目标不是马上实现完整引擎，而是先定义**怎么证明结构有用**。

## 1. 要验证什么

**假设**：对多跳检索、规则推理、跨应用同步类任务，把任务拆成显式 flow（顺序/分支/并行/嵌套）比 direct agent 更可靠。

**对比**：

- Baseline：官方 `auto-bench` 的 direct agent（模型自己决定每一步）；
- Structured：同样模型，但按 flow JSON 规定的节点/顺序/分支执行。

**指标**：pass rate、partial credit、平均步数、token、成本；按任务类型分开报。

## 2. 选哪几个任务

先做 3 个，覆盖三种结构，不贪多：

| 任务 | 问题类 | 为什么选它 | 需要的结构 |
|---|---|---|---|
| `sales.multi_hop_lookup` | P2 | 信息跨 Gmail/Sheets/Salesforce，且要按 tier 条件路由 | 顺序 + 并行 + 条件 |
| `operations.generator_load_testing_schedule` | P4a | 多条频率/跳过规则，再建日历 | 条件 + 时间节点 |
| `support.zendesk_sf_case_sync` | P3 | 读 3 个配置表、过滤、同步到 Salesforce | 并行读取 + 汇聚 |

### 2.1 可证伪假设

| 编号 | 假设 | 主要观测 | 如果成立 |
|---|---|---|---|
| H1 | 显式 FinalAction/Verifier 节点能减少“最后一步缺失” | P9/P3 的最后动作断言失败数 | structured 的 pass 提升集中在长链任务 |
| H2 | 显式路由表能减少 P4b 的收件人/tier 错误 | P4b 的路由断言失败数 | P4b 提升，P4a 不应同等提升（区分效度） |
| H3 | 规则抽取 + 确定性过滤能减少 P4a 的集合成员错误 | P4a 的集合/数量断言 | P4a 提升，错误类型从“集合错”转为“规则抽取错” |
| H4 | 结构化的收益不是“多跑几步” | 步数/token/成本对照 | 控制步数后仍提升，才归因于结构 |

如果四条假设都不成立，或者所有类型同等提升，优先怀疑：
模型只是多跑了步数/多调了工具，而不是结构本身起作用。这时需要做
“步数匹配”的对照（给 direct agent 同样的步数预算）或节点消融。

## 3. 结构设计

### 3.1 `sales.multi_hop_lookup`

```
start
 → read_policy（Gmail：最新 routing policy）
 → read_account（Sheets：Account Hierarchy）
 → parallel:
     read_fx（Sheets：FX Rates）
     read_cases（Salesforce：open support cases）
 → merge
 → decide_recipients（condition：tier + escalation）
 → send_emails（Gmail）
 → update_opportunity（Salesforce：stage=Closed Won）
 → end
```

关键点：

- `read_*` 是工具节点，参数写死（app、query、字段），模型只负责抽取/判断；
- `decide_recipients` 是 LLM 节点，但输入被限制为“tier + 是否有 escalation”，输出收件人列表；
- 失败重试：`read_*` 失败时重试 1 次，再走 fallback 查询。

### 3.2 `operations.generator_load_testing_schedule`

```
start
 → read_generators（Sheets）
 → read_engineers（Sheets）
 → filter_due（规则节点：Monthly/Quarterly + 14 天窗口）
 → filter_skip（规则节点：Under Repair / Event / Emergency run）
 → compute_date（时间节点：下一个工作日 06:00）
 → create_events（Calendar，逐条）
 → email_engineers（按 building 分组）
 → end
```

### 3.3 `support.zendesk_sf_case_sync`

```
start
 → parallel:
     read_blocklist
     read_sla
     read_config
 → merge
 → read_tickets（Zendesk）
 → filter_and_priority（规则节点）
 → match_contacts（Salesforce）
 → create_cases（逐条）
 → add_comments（Zendesk）
 → slack_summary
 → end
```

## 4. rsi-flow 里需要补什么

当前 rsi-flow 已有：顺序、条件分支、嵌套、async any/all/void/close。

还缺：

| 缺口 | 最小实现 |
|---|---|
| LLM 节点 | 新 `LlmNode`：输入 prompt + 变量，调 OpenAI-compatible API，输出 JSON |
| 工具节点 | 新 `ToolNode`：包一个 AutomationBench 工具（先 mock/HTTP） |
| 动态列表 | 先不做；把 3 个任务写成固定节点数 |
| 重试/降级 | 先做单节点重试 1 次 |
| 状态映射 | `initial_state` → flow 变量；`end_state` → 评分 |
| 预算控制 | 每节点记录 token/步数 |

**先做最小闭环**：只实现 `LlmNode` + `ToolNode` + 单节点重试，够跑 3.1 即可。

## 5. 实现步骤

1. **在 rsi-flow 加两个节点**（`test` 分支）
   - `LlmNode`：`prompt`、`model`、`responseFormat` 参数；输出注册到 flow scope。
   - `ToolNode`：`app`、`action`、`params` 参数；先支持 3 个工具（Gmail send、Salesforce update、Sheets read）。
2. **写 `flow-multi-hop.json`**
   - 用现有 `routes` + `condition` + `strategies: all/close` 表达 3.1。
3. **写一个最小 runner**
   - 读 AutomationBench 的一个任务：`prompt`、`initial_state`、`assertions`；
   - 把 `initial_state` 注入 flow 变量；
   - 跑 flow，拿 `end_state`；
   - 用 `rubric` 的 assertions 评分。
4. **对比实验**
   - direct agent：用 `results/medium-max/` 的同配置结果作为基准；
   - structured：同一任务、同一模型/工具集/max_steps；
   - 先每任务每条件 3 次；方差大再补到 5 次；
   - 报 pass/partial/steps/token/cost，逐任务报，不只报均值。

## 6. 对比协议（公平性）

- 同模型（`gpt-5.6-sol`）、同 toolset（`api`）、同 max_steps（50）、同 reasoning effort（`max`）、同 API 路径（`chat_completions`）；
- 同任务、同初始状态、同 prompt；
- 先每任务每条件 **3 次**；方差大再补到 5 次；报均值与范围（n 小，不做强显著性）；
- structured 的 token/成本要单独报，不能只报通过率；
- 如果 structured 通过率高但成本翻倍，要写清“性价比”；
- 额外做**节点消融**：去掉 Verifier / FinalAction / Router 各跑一次，看收益是否来自预期节点；
- 额外做**步数对照**：给 direct agent 相同的步数上限，排除“只是多跑了几步”。

**判定标准**：

- 强证据：3 个任务中至少 2 个 pass 提升，且对应机制的断言失败数下降；
- 中等证据：partial 提升但 pass 不变；
- 负结果：structured 更差或成本 >2× 且无 pass 提升——也要如实报告。

## 7. 预期与风险

**预期**：

- P2/P3 任务：structured 的 pass rate 明显上升，因为不会漏掉“发邮件/写回”步骤；
- P4a/P4b 任务：structured 在规则复杂时更稳，但规则抽取/路由表节点仍可能错；
- 成本：structured 的 token 可能更高（多节点调用），但步数更少。

**风险**：

- rsi-flow 缺循环/动态扇出，3 个任务只能写死节点数；
- 工具节点需要把 AutomationBench 的 world state 映射进来，工作量不小；
- 评测口径必须和 direct agent 完全一致，否则结论不成立。

## 8. 时间安排

| 阶段 | 内容 | 产出 |
|---|---|---|
| 第 1 步 | 加 `LlmNode` + `ToolNode` | 能跑一个“读 → 判断 → 写”的 3 节点 flow |
| 第 2 步 | 写 `flow-multi-hop.json` | 能跑 `sales.multi_hop_lookup` |
| 第 3 步 | 最小 runner + 评分 | 一次 structured 结果 |
| 第 4 步 | 3 次对比（每任务每条件） | 表 3：direct vs structured |
| 第 5 步 | 节点消融 + 步数对照 | 收益归因：结构 vs 步数 |

**成本粗估**：3 任务 × 2 条件 × 3 次 = 18 次运行；按 max effort 每题 $1–3 估算，
约 **$18–54**。先跑 1 个任务验证 runner，再扩到 3 个，避免一次性烧预算。

> 这是任务二“设计复杂超长 Agent 结构”的起点；先做最小闭环，再扩展循环/动态扇出/重试。

## 9. 实现进度（2026-11-18）

已在 rsi-flow **`test` 分支**落地最小节点（未动 `dev_rsi`）：

| 组件 | 文件 | 状态 |
|---|---|---|
| `LlmNode` | `flow-core/.../agent/LlmNode.java` | 已实现；OpenAI-compatible Chat Completions，支持 env / system property 配置 |
| `ToolNode` + registry | `agent/ToolNode.java`、`ToolRegistry.java` | 已实现；工具由调用方注册，app/action 固定 |
| `FinalActionNode` + registry | `agent/FinalActionNode.java`、`FinalActionRegistry.java` | 已实现；未注册动作会失败，防止流程提前结束 |
| `VerifierNode` | `agent/VerifierNode.java` | 已实现；检查 expected fragments 并返回 `{passed, missing}` |
| 测试 | `FLOW_AGENT/FlowAgentTest.java` | 3 个测试：tool flow、LLM mock、final+verifier |
| 构建 | `../scripts/mvn-rsi.sh -pl flow-test -am test` | **20/20 通过**（原 17 + 新增 3） |

**还没做**：

- AutomationBench `WorldState` 与 ToolRegistry 的桥接（需要把 47 个模拟 SaaS 工具映射成 handler）；
- 3 个任务的 flow JSON（`flow-multi-hop.json` 等）；
- direct vs structured 的 3 次对比、节点消融与步数对照；
- 循环/动态扇出/checkpoint 仍是缺口（当前 3 个任务先写死节点数）。

下一步先写 `sales.multi_hop_lookup` 的 flow JSON，把一个 AutomationBench 任务
端到端跑通，再扩到另外两个任务。
