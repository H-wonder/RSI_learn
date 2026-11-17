# exp-002 小批量问题记录

## 总览

| 项 | 值 |
|---|---|
| 模型 | gpt-5.6-sol（中转站） |
| n | 18（6 域 × 3） |
| 通过率 | 16.7%（3/18） |
| 平均部分分 | 0.562 |
| 平均步数 | 15.3 |
| 成本 | $21.12 |

失败类型（自动归类，待人工复核）：

| 类别 | 失败断言数 | 占比 | 涉及任务 |
|---|---:|---:|---:|
| missing_record | 31 | 45.6% | 7 |
| missing_message_or_note | 24 | 35.3% | 9 |
| extra_or_unwanted_action | 8 | 11.8% | 5 |
| other | 4 | 5.9% | 3 |
| wrong_value_or_state | 1 | 1.5% | 1 |

最高频断言：

| 断言类型 | 次数 |
|---|---:|
| `gmail_message_sent_to_with_body_contains` | 19 |
| `google_sheets_row_exists` | 13 |
| `slack_message_exists` | 5 |
| `reamaze_conversation_exists` | 4 |

## 逐题记录（待人工补“实际做了什么/根因”）

| # | 域 | 任务 | 分数 | 失败断言数 | 最高频失败类型 | 自动类别 | 实际做了什么 | 根因 |
|---:|---|---|---:|---:|---|---|---|---|
| 1 | support | support.reamaze_intercom_sync | 0.095 | 19 | gmail_message_sent_to_with_body_contains | missing_message |  |  |
| 2 | marketing | marketing.tam_analysis | 0.357 | 9 | google_sheets_row_exists | missing_record |  |  |
| 3 | marketing | marketing.social_engagement_response | 0.000 | 7 | slack_message_exists | missing_message |  |  |
| 4 | operations | operations.generator_load_testing_schedule | 0.000 | 7 | google_calendar_event_exists | missing_record |  |  |
| 5 | hr | hr.workforce_planning_forecast | 0.000 | 4 | google_sheets_row_exists | missing_record |  |  |

## 接近满分但没过的任务

| 任务 | 分数 | 差在哪 |
|---|---:|---|
| marketing.win_loss_analysis | 0.938 | 只差 1 条断言 |
| support.intercom_feature_request | 0.900 | 只差 1–2 条 |
| sales.overdue_followup_flag | 0.889 | 只差 1 条 |
| hr.offboarding_automation | 0.857 | 只差 1–2 条 |

## 系统性问题

| 问题 | 证据 | 影响 | 处理 |
|---|---|---|---|
| 采样与标注不对齐 | 6 题（每域 index=50）不在 60 题标注里 | 类型表只有 12/18 | 下一轮用 `data/tasks/small_from_annotation.csv` |
| 漏发通知/漏建记录为主 | 80.9% 的失败断言是这两类 | 基线通过率低 | 结构实验重点验证“通知/写回”节点 |
| support 单题极慢 | support 3 题 10 分 22 秒 | 放量成本高 | medium 先跑 2 个域，或降低 max_steps |

## 结论

- 18 题里 3 题通过，4 题只差一点；问题主要是“漏做”，不是“做错”。
- 先补 6 题的标签或重跑对齐的 small，再决定 medium/full。
- 全量 600 题按当前成本约 $700，需要预算决策或换更便宜的模型。
