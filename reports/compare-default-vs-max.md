# 同一批 60 题：默认 effort vs max effort

- A：medium 实验（默认 effort）
- B：medium-max 实验（max effort）
- n：60（逐题配对）

## 1. 总体

| 指标 | A | B | 变化 |
|---|---:|---:|---:|
| 通过率 | 11.7% | 33.3% | +21.7 pp |
| 通过数 | 7/60 | 20/60 | +13 |
| 平均部分分 | 0.509 | 0.715 | +0.206（95% bootstrap CI [+0.112, +0.303]） |
| 平均步数 | 15.2 | 15.2 | +0.1 |
| 平均输出 token | 2,982 | 9,714 | +6,732 |
| 总成本 | $71.78 | $120.41 | $+48.62 |
| refusal-stopped | 0 | 1 | — |

## 2. 逐题变化

| 类别 | 任务数 |
|---|---:|
| A 通过、B 通过 | 6 |
| A 失败、B 通过（提升） | 14 |
| A 通过、B 失败（退化） | 1 |
| A 失败、B 失败 | 39 |

McNemar 精确检验（通过/不通过）：p = 0.0009766（不一致对 14 vs 1）

部分分逐题变化：提升 35 题，不变 18 题，下降 7 题。

## 3. 分域

| 域 | n | 通过 A | 通过 B | 部分分 A | 部分分 B | 部分分变化 |
|---|---:|---:|---:|---:|---:|---:|
| sales | 10 | 0.0% | 10.0% | 0.396 | 0.507 | +0.112 |
| marketing | 10 | 10.0% | 50.0% | 0.614 | 0.891 | +0.277 |
| operations | 10 | 10.0% | 30.0% | 0.458 | 0.680 | +0.222 |
| support | 10 | 0.0% | 30.0% | 0.506 | 0.865 | +0.359 |
| finance | 10 | 30.0% | 40.0% | 0.586 | 0.670 | +0.084 |
| hr | 10 | 20.0% | 40.0% | 0.495 | 0.677 | +0.183 |

## 4. 问题类型

| 类型 | n | 通过 A | 通过 B | 部分分 A | 部分分 B | 部分分变化 |
|---|---:|---:|---:|---:|---:|---:|
| P2 多跳检索 | 10 | 10.0% | 10.0% | 0.415 | 0.472 | +0.057 |
| P3 跨应用同步 | 7 | 0.0% | 14.3% | 0.436 | 0.754 | +0.318 |
| P4a 资格筛选/规则判定 | 16 | 18.8% | 56.2% | 0.444 | 0.781 | +0.337 |
| P4b 分支路由/优先级 | 9 | 0.0% | 33.3% | 0.615 | 0.797 | +0.182 |
| P5 排除/冲突 | 3 | 33.3% | 33.3% | 0.630 | 0.481 | -0.148 |
| P7 时间/日程 | 1 | 0.0% | 0.0% | 0.667 | 0.833 | +0.167 |
| P8 聚合/计算 | 12 | 16.7% | 41.7% | 0.632 | 0.842 | +0.210 |
| P9 长链编排 | 2 | 0.0% | 0.0% | 0.286 | 0.429 | +0.143 |

## 5. 从失败变为通过的任务

| 任务 | 类型 | A 分数 | B 分数 |
|---|---|---:|---:|
| `finance.annual_budget_prep` | P8 | 0.70 | 1.00 |
| `finance.invoice_aging_followup` | P4b | 0.33 | 1.00 |
| `hr.i9_verification_tracking` | P4b | 0.38 | 1.00 |
| `hr.recruitment_channel_roi` | P8 | 0.00 | 1.00 |
| `marketing.content_localization` | P8 | 0.83 | 1.00 |
| `marketing.newsletter_sponsor_invoicing` | P4a | 0.84 | 1.00 |
| `marketing.social_engagement_response` | P4a | 0.00 | 1.00 |
| `marketing.win_loss_analysis` | P8 | 0.94 | 1.00 |
| `operations.mailchimp_subscriber_sync` | P4a | 0.17 | 1.00 |
| `operations.perishable_inventory_expiry` | P4a | 0.00 | 1.00 |
| `sales.sheets_reconciliation` | P3 | 0.25 | 1.00 |
| `support.freshdesk_contract_renewal` | P4a | 0.29 | 1.00 |
| `support.intercom_freshdesk_escalation` | P4a | 0.34 | 1.00 |
| `support.zendesk_escalation_waterfall` | P4b | 0.88 | 1.00 |

## 6. 从通过变为失败的任务

| 任务 | 类型 | A 分数 | B 分数 |
|---|---|---:|---:|
| `finance.revenue_recognition` | P8 | 1.00 | 0.75 |

