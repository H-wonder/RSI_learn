# 失败机制编码（M1–M6）

> 这份文档把“哪条断言失败”提升为“为什么会失败”。
> 它是报告失败分析章的编码手册，也是任务二在 rsi-flow 里做结构干预的依据。
> 每条机制都给出：可观察信号、典型任务、结构映射、预期效果。

## 为什么需要机制层

断言级分类（漏建记录、漏发消息、多做……）只回答**哪里错了**，不回答**为什么**。
同一个 `missing_record` 可能来自四种完全不同的原因：

1. 选错应用/数据源（根本没有读到数据）；
2. 规则读错（读到了，但判断错了）；
3. 长链中断（判断对了，但没走到最后一步）；
4. 收尾没校验（做了，但字段/数量错了）。

如果只按断言类型统计，就会把四种问题混成一类，结构设计也就无从下手。
机制层的作用是：**把失败映射到可干预的结构缺口**。

## 编码流程

对每个失败任务：

1. 看最终失败断言（`assertions` + 实际 `end_state`）；
2. 从第一条消息开始，找**第一次偏离正确路径**的位置；
3. 判断偏离属于哪条机制；若有多个，选**最早、最致命**的一条为主机制；
4. 记录证据：工具调用序列、错误响应、错误字段、缺失动作；
5. 给出一条“如果这里有显式结构，能否避免”的判断。

## M1 工具/数据源选择错误

**定义**：模型选错应用、端点、工作表或查询方式，且失败后不回到正确数据源。

**可观察信号**：

- 调用了任务未提供的应用（HubSpot vs Salesforce、Airtable vs Google Sheets）；
- 收到 `401 No ... account is connected`、`Spreadsheet not found` 后放弃；
- 反复 `api_search` 但不 `api_fetch`；
- 最终 0 分或只有极少数断言通过。

**典型任务**：`sales.multi_hop_lookup`、`operations.generator_load_testing_schedule`、
`support.reamaze_intercom_sync`、`hr.monday_onboarding_pipeline`。

**结构映射**：`ToolNode` 固定 app/endpoint/参数模板 + 失败重试 + fallback 查询。

**预期效果**：减少“0 步有效操作”的 0 分任务；对 P2/P3 的提升应大于 P1。

## M2 规则/资格判定错误

**定义**：读到了规则，但阈值、日期、资格条件或最新公告判断错，导致集合成员错。

**可观察信号**：

- 日期窗口算错（14 天/90 天/7 天）；
- 忽略最新公告/政策（hiring freeze、采购暂停）；
- 把未批准/未到期/非 active 的对象纳入；
- 断言集中在 `*_exists`、数量、状态字段。

**典型任务**：`operations.generator_load_testing_schedule`、
`hr.workforce_planning_forecast`、`finance.invoice_aging_followup`、
`marketing.newsletter_sponsor_invoicing`。

**结构映射**：`RuleNode`（规则抽取 + schema 校验）→ `FilterNode`（集合过滤）。
LLM 只负责从文档抽取规则，过滤由确定性代码执行。

**预期效果**：P4a 的 pass/partial 提升；错误从“集合成员错”变成“规则抽取错”，
更容易定位和修复。

## M3 路由/优先级错误

**定义**：对象选对了，但收件人、团队、tier、会议时段或路径选错。

**可观察信号**：

- 邮件发给了错误的团队/收件人；
- Salesforce case 的 owner/tier 错；
- Calendly/Zoom 的时段或区域错；
- 部分分很高（0.6–0.9），但 pass 为 0，因为路由断言是硬门槛。

**典型任务**：`sales.zoom_regional_webinar_coordinator`、
`support.zendesk_escalation_waterfall`、`finance.invoice_aging_followup`、
`hr.policy_update_distribution`。

**结构映射**：`BranchNode` + 显式路由表（tier/金额/区域 → 目的地）+
发送前断言校验。

**预期效果**：P4b 的提升应最明显；这类任务的部分分高、pass 低，
结构干预的“通过率弹性”最大。

## M4 长链中断/最后动作缺失

**定义**：前面的读取和判断基本正确，但在最后一步（写回、发通知、建记录）停止。

**可观察信号**：

- 轨迹在“已查到数据/已决定动作”后结束；
- 失败断言集中在最后的 `*_exists` / `*_sent`；
- 部分分中等偏高（0.4–0.8），但最后一步全丢；
- 步数没有到上限，模型主动结束。

**典型任务**：`sales.partnership_contract`、`support.reamaze_intercom_sync`、
`hr.offboarding_automation`、`finance.qb_invoice_from_orders`。

**结构映射**：`Sequence` + checkpoint + 显式 `FinalActionNode`；
流程未走完不允许结束。

**预期效果**：P9/P3 的 pass 提升；减少“差最后一步”的失败。

## M5 集合/负约束违反

**定义**：做了不该做的动作，或把不该纳入的对象纳入集合。

**可观察信号**：

- 失败断言类型含 `not`（负断言）；
- 邮件/消息里多带了排除对象；
- 给不该处理的记录打了标签/建了任务；
- 计数断言不等于 N。

**典型任务**：`sales.overdue_followup_flag`、`hr.mandatory_meeting_scheduling`、
`operations.mailchimp_subscriber_sync`、`marketing.social_engagement_response`。

**结构映射**：`FilterNode`（显式排除集）+ 负断言 guard（发送前检查）。

**预期效果**：P5 和负断言失败率下降；对 P4a 也有溢出收益。

## M6 收尾校验缺失

**定义**：主体动作基本完成，但字段、金额、数量、格式没有做最终核对。

**可观察信号**：

- 部分分在 0.8–1.0；
- 只差 1–2 条断言；
- 常见于金额换算、日期格式、计数字段、邮件正文中的一个数字；
- 没有任何“发送前自检”的工具调用。

**典型任务**：`marketing.social_benchmark`（0.949）、
`marketing.seo_brief_prioritization`（0.923）、
`sales.overdue_followup_flag`（0.889，默认 effort）、
`marketing.win_loss_analysis`（0.938，默认 effort）。

**结构映射**：`VerifierNode`（读取最终状态 → 对照断言/规则 → 修正或补做）。

**预期效果**：把“接近满分”转成“通过”；对 pass rate 的提升可能比新增能力更大。

## 机制 × 结构 × 指标

| 机制 | rsi-flow 最小实现 | 主要影响 | 观测指标 |
|---|---|---|---|
| M1 工具/数据源 | ToolNode + retry/fallback | P2/P3 的 0 分任务 | 有效工具调用数、0 分率 |
| M2 规则/资格 | RuleNode + FilterNode | P4a | pass、集合成员错误数 |
| M3 路由/优先级 | BranchNode + 路由表 | P4b | pass、收件人/tier 错误数 |
| M4 长链/最后动作 | Sequence + FinalActionNode | P3/P9 | 最后动作缺失数、pass |
| M5 集合/负约束 | FilterNode + negative guard | P5 | 负断言失败数、extra 比例 |
| M6 收尾校验 | VerifierNode | 0.8–1.0 near miss | 近满分转通过数 |

## 与任务二的关系

任务二不需要一次性实现六种节点。建议按**证据强度**排序：

1. 先做 M4（最后动作）+ M6（收尾校验）：实现成本低，直接针对 near miss；
2. 再做 M2/M3（规则 + 路由）：对应 P4a/P4b，是样本最大的能力族；
3. 最后做 M1/M5（工具绑定 + 集合约束）：需要更多工具层改造。

每个机制都应有一个**可证伪的假设**：

- 加入 FinalActionNode 后，P9 的“最后动作缺失”断言失败数应下降；
- 加入 VerifierNode 后，0.8–1.0 区间的任务应有更高比例转为通过；
- 加入路由表后，P4b 的 pass 应提升，而 P4a 不应显著变化（区分效度）；
- 如果所有类型都同等提升，说明收益可能来自“多跑了几步”，而不是结构本身，需要做步数/ token 对照。
