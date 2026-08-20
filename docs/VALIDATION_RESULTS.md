# Validation Results

Verification date: 2026-08-20

Environment: Windows, Python 3.12.9

Scope: exact clean-room working tree before first commit

## Automated tests

Command:

```text
python -m unittest discover -s tests -v
```

Result: **PASS — 13 tests executed, 13 passed**.

The suite verifies mixed date parsing, invalid-date retention, malformed-number visibility, duplicate canonical-grain quarantine, duplicate input-key refusal, orphan-key retention, stale and partial input refusal, exception-to-`ERROR` behavior, repeat-run idempotence, two independent reconciliation boundaries, and positional schema drift with unchanged column count.

No coverage percentage is claimed because no coverage tool is included.

## Reproducible demo

Command:

```text
python -m commerce_data_automation demo --output-dir build/demo
```

Result: **PASS**.

| Check | Observed result |
|---|---|
| input rows retained | 4 |
| accepted rows | 2 |
| exception entries | 3 |
| mart rows | 2 |
| report rows | 2 |
| verdict counts | 7 `PASS`, 1 `WARN`, 2 `FAIL`, 1 `ERROR` |
| repeat exports | byte-identical |
| expected mart | exact row match |
| expected report | exact row match |
| reconciled totals | 5 units; 3,000 invented minor `TST` units |

These are results of tiny invented fixtures. They do not describe production scale, performance, reliability, accuracy, availability, or business outcomes.
