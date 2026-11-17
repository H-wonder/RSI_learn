# max 60 题失败机制编码

- 失败任务：40（含 1 个 refusal）

| 机制 | 任务数 | 占比（失败任务） |
|---|---:|---:|
| M1 工具/数据源 | 4 | 10.0% |
| M2 规则/资格 | 3 | 7.5% |
| M3 路由/优先级 | 4 | 10.0% |
| M4 长链/最后动作 | 16 | 40.0% |
| M5 集合/负约束 | 4 | 10.0% |
| M6 收尾校验 | 8 | 20.0% |
| R refusal（不计入 M1–M6） | 1 | 2.5% |

## 逐题编码

| 任务 | 类型 | 分数 | 主机制 | 证据 |
|---|---|---:|---|---|
| `finance.qb_invoice_from_orders` | P4a | 0.000 | M1 | Salesforce 401; orders source never resolved |
| `hr.monday_onboarding_pipeline` | P5 | 0.000 | M1 | no connected HRIS source; Monday items missing |
| `hr.policy_update_distribution` | P4b | 0.250 | M1 | employee directory unavailable; individual emails missing |
| `operations.vendor_compliance_audit` | P3 | 0.231 | M1 | Salesforce fields empty; wrong compliance set; negative assertions |
| `hr.mandatory_meeting_scheduling` | P4a | 0.167 | M2 | exemption/eligibility and recipients wrong |
| `sales.calendly_sla_monitoring` | P4a | 0.000 | M2 | breach detection/notification rules |
| `sales.multi_hop_lookup` | P2 | 0.333 | M2 | tier/currency/notification rule misapplied |
| `hr.zoom_orientation_sessions` | P4b | 0.667 | M3 | wrong session/email body for two hires |
| `sales.calendly_multi_stakeholder_scheduling` | P2 | 0.600 | M3 | invitee set wrong |
| `support.helpscout_auto_categorization` | P4b | 0.778 | M3 | wrong tag/note/channel |
| `support.hiver_slack_digest` | P4b | 0.818 | M3 | drafts/emails/channel routing wrong |
| `finance.payment_terms_tracking` | P2 | 0.000 | M4 | terms verified but no emails sent |
| `finance.vendor_insurance_verification` | P4a | 0.833 | M4 | notification missing |
| `hr.offboarding_automation` | P4b | 0.857 | M4 | sheet write-back missing |
| `marketing.seasonal_campaign` | P2 | 0.667 | M4 | Buffer post missing |
| `operations.asana_fire_drill` | P2 | 0.800 | M4 | Asana action missing |
| `operations.docusign_contractor_offboard` | P8 | 0.600 | M4 | Trello card/Notion page missing |
| `operations.generator_load_testing_schedule` | P4a | 0.857 | M4 | email notification missing |
| `operations.mailchimp_ecommerce_sync` | P4a | 0.714 | M4 | Slack summary missing |
| `sales.calendly_reschedule_chain` | P7 | 0.833 | M4 | Salesforce note missing |
| `sales.champion_change_alert` | P2 | 0.250 | M4 | found contacts but no task/Slack alert |
| `sales.overdue_followup_flag` | P5 | 0.444 | M4 | tasks/email missing for three accounts |
| `sales.partnership_contract` | P9 | 0.143 | M4 | DocuSign/Calendly/stage missing |
| `sales.zoom_regional_webinar_coordinator` | P4b | 0.800 | M4 | Slack summary missing |
| `support.reamaze_intercom_sync` | P3 | 0.952 | M4 | Slack summary missing |
| `support.zendesk_sf_case_sync` | P3 | 0.750 | M4 | one case + Slack counts missing |
| `support.zoho_multitenant_isolation` | P3 | 0.750 | M4 | ticket comments missing |
| `finance.revenue_recognition` | P8 | 0.750 | M5 | row CTR-003 should not exist (regression) |
| `hr.benefits_enrollment_audit` | P3 | 0.833 | M5 | posted Slack message that should not exist |
| `marketing.engagement_optimization` | P8 | 0.455 | M5 | rows that should not exist; Slack missing |
| `support.gorgias_fraud_detection` | P3 | 0.765 | M5 | extra sheet row/message/channel |
| `finance.fiscal_year_rollover` | P9 | 0.714 | M6 | email body amount/restatement wrong |
| `finance.invoice_email_extract` | P2 | 0.400 | M6 | invoice rows/amounts wrong |
| `marketing.analyst_mention_tracking` | P8 | 0.917 | M6 | email body missing content |
| `marketing.seo_brief_prioritization` | P4a | 0.923 | M6 | email body missing a keyword/number |
| `marketing.social_benchmark` | P8 | 0.949 | M6 | email body missing content |
| `operations.space_utilization_analysis` | P8 | 0.600 | M6 | email body missing room/count |
| `sales.create_contact_for_account` | P2 | 0.667 | M6 | contact fields do not match |
| `support.hiver_csat_analysis` | P8 | 0.840 | M6 | sheet rows/email body wrong |
| `operations.drive_slack_dock_schedule` | P2 | 0.000 | R | provider safety refusal |
