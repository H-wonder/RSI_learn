# 问题分类标注分布

- total tasks: 60
- labels: AI 初标，待人工复核

## 主类分布

| type | count | share | example tasks |
|---|---:|---:|---|
| P2 | 10 | 16.7% | sales.multi_hop_lookup, sales.create_contact_for_account, sales.champion_change_alert |
| P3 | 7 | 11.7% | sales.sheets_reconciliation, operations.vendor_compliance_audit, support.zendesk_sf_case_sync |
| P4 | 25 | 41.7% | sales.calendly_sla_monitoring, sales.zoom_regional_webinar_coordinator, marketing.social_engagement_response |
| P5 | 3 | 5.0% | sales.overdue_followup_flag, marketing.link_building, hr.monday_onboarding_pipeline |
| P7 | 1 | 1.7% | sales.calendly_reschedule_chain |
| P8 | 12 | 20.0% | marketing.content_localization, marketing.social_benchmark, marketing.engagement_optimization |
| P9 | 2 | 3.3% | sales.partnership_contract, finance.fiscal_year_rollover |

## 域 × 主类

| domain | P1 | P2 | P3 | P4 | P5 | P6 | P7 | P8 | P9 | total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| finance |  | 2 |  | 4 |  |  |  | 3 | 1 | 10 |
| hr |  |  | 1 | 7 | 1 |  |  | 1 |  | 10 |
| marketing |  | 1 |  | 3 | 1 |  |  | 5 |  | 10 |
| operations |  | 3 | 1 | 4 |  |  |  | 2 |  | 10 |
| sales |  | 4 | 1 | 2 | 1 |  | 1 |  | 1 | 10 |
| support |  |  | 4 | 5 |  |  |  | 1 |  | 10 |

## 次类分布

| type | appears as secondary |
|---|---:|
| P1 | 31 |
| P2 | 17 |
| P3 | 1 |
| P4 | 28 |
| P5 | 53 |
| P7 | 5 |
| P8 | 6 |
| P9 | 4 |

## 观察

- P4（条件路由/规则推理）占比较高，说明“读规则再决定做什么”是主要能力。
- P1（单工具 CRUD）和 P6（模糊匹配）在 60 题样本里没有作为主类出现：
  这两类可能更多作为**次类**，或者样本没有覆盖到。
- P9（长链编排）只有 2 题，但它的“长”是跨度而非类别；
  很多 P4 任务其实也包含 5+ 步，需要在论文里说明分类口径。
- 下一步：人工复核 P4 的 25 题，看看能否拆成
  “资格筛选（eligibility）”和“分支路由（routing）”两类。
