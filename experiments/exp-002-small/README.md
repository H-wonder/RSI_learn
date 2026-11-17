# exp-002 小批量（每域 3 题，共 18 题）

## 目的

**暴露问题**，不是拿分数。跑完必须逐题记录失败原因，填 [issues.md](issues.md)。

## 命令

```bash
# 从 60 题标注样本里选 18 题，保证“问题类型 × 通过率”能算全
python scripts/run_batch.py --name small --tasks-file data/tasks/small_from_annotation.csv

python scripts/analyze_results.py --dir results/small \
  --out-md reports/small.md --out-issues reports/small.issues.csv \
  --out-tasks reports/small.tasks.csv

python scripts/analyze_by_type.py --dir results/small \
  --annotation data/annotation/tasks_to_label.csv \
  --out-md reports/small.by_type.md --out-csv reports/small.by_type.csv
```

## 结果

| 指标 | 值 |
|---|---:|
| n | 18 |
| 通过率 | 16.7%（3/18） |
| 平均部分分 | 0.562 |
| 平均步数 | 15.3 |
| token in/out | 3,797,606 / 71,167 |
| 成本 | $21.12 |

分域：

| 域 | n | 通过率 | 部分分 | 平均步数 |
|---|---:|---:|---:|---:|
| sales | 3 | 33.3% | 0.630 | 9.7 |
| marketing | 3 | 0% | 0.432 | 12.3 |
| operations | 3 | 0% | 0.450 | 13.3 |
| support | 3 | 0% | 0.582 | 14.7 |
| finance | 3 | 33.3% | 0.657 | 20.0 |
| hr | 3 | 33.3% | 0.619 | 21.7 |

完整报告：[reports/small.md](../../reports/small.md)

## 逐题结果

| 任务 | 分数 | 步数 |
|---|---:|---:|
| finance.credit_card_reconciliation | **1.000** | 15 |
| hr.quarterly_termination_queue | **1.000** | 12 |
| sales.linkedin_sales_prospecting | **1.000** | 5 |
| marketing.win_loss_analysis | 0.938 | 13 |
| support.intercom_feature_request | 0.900 | 18 |
| sales.overdue_followup_flag | 0.889 | 14 |
| hr.offboarding_automation | 0.857 | 30 |
| operations.hubspot_personalized_outreach | 0.750 | 10 |
| support.zendesk_sf_case_sync | 0.750 | 14 |
| operations.asana_fire_drill | 0.600 | 23 |
| finance.fiscal_year_rollover | 0.571 | 14 |
| finance.invoice_email_extract | 0.400 | 31 |
| marketing.tam_analysis | 0.357 | 13 |
| support.reamaze_intercom_sync | 0.095 | 12 |
| sales.multi_hop_lookup | 0.000 | 10 |
| marketing.social_engagement_response | 0.000 | 11 |
| operations.generator_load_testing_schedule | 0.000 | 7 |
| hr.workforce_planning_forecast | 0.000 | 23 |

## 结论

- 失败类型：漏建记录 45.6%、漏发消息 35.3%、多做 11.8%。
- 4 题“只差一两条断言”（0.857–0.938），说明结构优化空间大。
- 4 题完全 0 分，需要逐题看对话。
- **采样问题**：这次 small 用的是独立均匀抽样，6 题不在 60 题标注里，导致类型表只有 12/18。
  下一轮改用 `data/tasks/small_from_annotation.csv`，保证 18/18 都有标签。
- 是否可以放量：先修采样 + 复核 4 个 0 分任务，再跑 medium。
