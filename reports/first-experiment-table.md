# 第一张实验表（small，18 题）

## 配置

| 项 | 值 |
|---|---|
| 模型 | `gpt-5.6-sol` |
| base_url | `https://intlapi.thingo.com.cn/v1` |
| toolset | `api` |
| max_steps | 50 |
| 数据 | AutomationBench public，6 域 × 3 题 = 18 |
| 运行日期 | 2026-11-17 |
| 结果文件 | `results/small/*.json` |
| 成本 | $21.12 |

## 表 1：分域

| 域 | n | 通过率 | 部分分 | 平均步数 |
|---|---:|---:|---:|---:|
| sales | 3 | 33.3% | 0.630 | 9.7 |
| marketing | 3 | 0% | 0.432 | 12.3 |
| operations | 3 | 0% | 0.450 | 13.3 |
| support | 3 | 0% | 0.582 | 14.7 |
| finance | 3 | 33.3% | 0.657 | 20.0 |
| hr | 3 | 33.3% | 0.619 | 21.7 |
| **总体** | **18** | **16.7%** | **0.562** | **15.3** |

## 表 2：问题类型（12/18 有标签）

| 问题类 | n | 通过率 | 部分分 | 平均步数 | 例子 |
|---|---:|---:|---:|---:|---|
| P2 多跳检索 | 3 | 0% | 0.333 | 21.3 | finance.invoice_email_extract |
| P3 跨应用同步 | 2 | 0% | 0.423 | 13.0 | support.zendesk_sf_case_sync |
| P4 条件路由/规则 | 4 | 25.0% | 0.464 | 15.0 | hr.quarterly_termination_queue |
| P5 排除/冲突 | 1 | 0% | 0.889 | 14.0 | sales.overdue_followup_flag |
| P8 聚合/计算 | 1 | 0% | 0.938 | 13.0 | marketing.win_loss_analysis |
| P9 长链编排 | 1 | 0% | 0.571 | 14.0 | finance.fiscal_year_rollover |
| 未标注 | 6 | 33.3% | 0.668 | 14.0 | finance.credit_card_reconciliation |

> 未标注原因：这次 small 是独立均匀抽样，6 题（每域 index=50）不在 60 题标注样本里。
> 下一轮用 `data/tasks/small_from_annotation.csv`，18 题全部有标签。

## 表 3：失败类型

| 类别 | 失败断言数 | 占比 | 涉及任务 |
|---|---:|---:|---:|
| 漏建记录 | 31 | 45.6% | 7 |
| 漏发消息/通知 | 24 | 35.3% | 9 |
| 多做（负断言） | 8 | 11.8% | 5 |
| 其他 | 4 | 5.9% | 3 |
| 值写错 | 1 | 1.5% | 1 |

## 关键观察

1. **通过率 16.7%，但部分分 0.562**：很多任务不是完全不会，而是差几条断言。
2. **4 题只差一点**：`marketing.win_loss_analysis` 0.938、`support.intercom_feature_request` 0.900、
   `sales.overdue_followup_flag` 0.889、`hr.offboarding_automation` 0.857。
3. **失败集中在“漏做”**：漏建记录 + 漏发消息 = 80.9% 的失败断言。
4. **P4 的通过来自“pause”任务**：`hr.quarterly_termination_queue` 正确做法是读到暂停公告后什么都不做。
5. **成本**：18 题 $21.12；按此估算全量 600 题约 $700，放量前需要预算决策。

## 下一步

- 修采样：用 `small_from_annotation.csv` 重跑或直接给 6 题补标签；
- 逐题看 4 个 0 分任务（`sales.multi_hop_lookup`、`marketing.social_engagement_response`、
  `operations.generator_load_testing_schedule`、`hr.workforce_planning_forecast`）；
- 决定 medium（60 题）还是直接用更便宜的模型跑 full。
