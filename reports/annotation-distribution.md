# 问题分类标注分布

- total tasks: 60
- labels: AI 初标 + 用户复核；P4 的 P4a/P4b 子类由人工判定

## 主类分布

| type | count | share | example tasks |
|---|---:|---:|---|
| P2 | 10 | 16.7% | sales.multi_hop_lookup, sales.create_contact_for_account, sales.champion_change_alert |
| P3 | 7 | 11.7% | sales.sheets_reconciliation, operations.vendor_compliance_audit, support.zendesk_sf_case_sync |
| P4a | 16 | 26.7% | sales.calendly_sla_monitoring, marketing.social_engagement_response, marketing.seo_brief_prioritization |
| P4b | 9 | 15.0% | sales.zoom_regional_webinar_coordinator, support.hiver_slack_digest, support.helpscout_auto_categorization |
| P5 | 3 | 5.0% | sales.overdue_followup_flag, marketing.link_building, hr.monday_onboarding_pipeline |
| P7 | 1 | 1.7% | sales.calendly_reschedule_chain |
| P8 | 12 | 20.0% | marketing.content_localization, marketing.social_benchmark, marketing.engagement_optimization |
| P9 | 2 | 3.3% | sales.partnership_contract, finance.fiscal_year_rollover |

## 域 × 主类

| domain | P1 | P2 | P3 | P4a | P4b | P5 | P6 | P7 | P8 | P9 | total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| finance |  | 2 |  | 3 | 1 |  |  |  | 3 | 1 | 10 |
| hr |  |  | 1 | 3 | 4 | 1 |  |  | 1 |  | 10 |
| marketing |  | 1 |  | 3 |  | 1 |  |  | 5 |  | 10 |
| operations |  | 3 | 1 | 4 |  |  |  |  | 2 |  | 10 |
| sales |  | 4 | 1 | 1 | 1 | 1 |  | 1 |  | 1 | 10 |
| support |  |  | 4 | 2 | 3 |  |  |  | 1 |  | 10 |

## 次类分布

| type | appears as secondary |
|---|---:|
| P1 | 31 |
| P2 | 17 |
| P3 | 1 |
| P5 | 53 |
| P7 | 5 |
| P8 | 6 |
| P9 | 4 |

## 观察

- P4 已拆成两个子类：P4a 资格筛选/规则判定（谁符合条件、是否越过阈值）
  与 P4b 分支路由/优先级（去哪里、走哪条路径、什么优先级）。
- P4a 16 题、P4b 9 题，合计仍是 25 题；拆开后能区分“集合选错”和“目的地选错”。
- P1（单工具 CRUD）和 P6（模糊匹配）在 60 题样本里没有作为主类出现：
  这两类可能更多作为**次类**，或者样本没有覆盖到。
- P9（长链编排）只有 2 题，但它的“长”是跨度而非类别；
  很多 P4a/P4b 任务其实也包含 5+ 步，需要在论文里说明分类口径。
- P5 作为次类出现 53 次，建议在论文里作为横切约束层，而不是普通主类。
