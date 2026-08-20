# Validation Scenarios

The scenarios below are executable in `tests/test_pipeline.py`. All were run successfully on 2026-08-20 using Python 3.12.9; see `VALIDATION_RESULTS.md` for the bounded result.

| ID | Scenario | Expected result | Test |
|---|---|---|---|
| `VAL-01` | mixed supported date formats | normalized to the same date type | `test_val_01_mixed_supported_dates_normalize` |
| `VAL-02` | invalid date in one record | record retained as an explicit parse failure | `test_val_02_invalid_date_remains_an_exception` |
| `VAL-03` | malformed numeric field | safe conversion fails visibly and yields a non-pass result | `test_val_03_malformed_numeric_is_visible_and_non_pass` |
| `VAL-04` | duplicate canonical grain | affected records are quarantined under the stated rule | `test_val_04_duplicate_canonical_grain_is_quarantined` |
| `VAL-05` | orphan product key | row remains visible in exception output | `test_val_05_orphan_product_key_is_retained` |
| `VAL-06` | stale input | downstream warehouse write is refused | `test_val_06_stale_input_refuses_downstream_write` |
| `VAL-07` | partial input | completeness guard prevents downstream write | `test_val_07_partial_input_refuses_downstream_write` |
| `VAL-08` | check execution throws | verdict is `ERROR`, never `PASS` | `test_val_08_check_exception_is_error_never_pass` |
| `VAL-09` | repeat same bounded period | exports remain identical and mart rows do not duplicate | `test_val_09_repeated_period_is_idempotent` |
| `VAL-10` | source-to-mart reconciliation | accepted synthetic totals equal mart totals | `test_val_10_source_to_mart_totals_reconcile` |
| `VAL-11` | mart-to-report reconciliation | report aggregates equal the accepted mart slice | `test_val_11_mart_to_report_totals_reconcile` |
| `VAL-12` | positional schema shift with the same column count | contract fails and names changed positions | `test_val_12_same_width_positional_schema_shift_fails` |

## Evidence rule

These passing results apply only to the exact clean-room implementation and tiny invented fixtures. They do not establish production performance, availability, accuracy, reliability, scale, savings, or coverage.
