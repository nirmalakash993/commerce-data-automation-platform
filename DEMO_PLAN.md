# Demo Plan

## Current state

The repository contains a runnable, credential-free Python and SQLite reference, thirteen standard-library tests, deterministic fixture generation, and expected synthetic mart/report outputs.

## Demo objective

Let a reviewer trace one messy input through refusal gates, text-preserving landing, row exceptions, a canonical mart, quality history, and a thin report without a live account or production data.

## Reproducible sequence

1. Inspect `examples/source_feed.csv` and `examples/product_reference.csv`.
2. Run `python -m unittest discover -s tests -v`.
3. Run `python -m commerce_data_automation demo --output-dir build/demo`.
4. Inspect `build/demo/landing.csv` and verify every source record remains visible.
5. Inspect `build/demo/exceptions.csv` and the distinct `WARN`, `FAIL`, and `ERROR` results.
6. Compare `build/demo/mart.csv` and `build/demo/report.csv` with their expected examples.
7. Review the command output confirming that a repeated period produced byte-identical deterministic exports.

## Demonstrated artifacts

- deterministic fixture generator with a documented seed;
- exact positional schema checks and pre-write freshness/completeness refusal;
- safe transformations authored in the clean-room tree;
- local SQLite landing, mart, report, exception, and quality tables;
- twelve tests mapped to `docs/VALIDATION_SCENARIOS.md` plus a duplicate-input-key refusal test;
- source-to-mart and mart-to-report reconciliation;
- a deliberate synthetic check exception that becomes `ERROR`.

## Acceptance result

The sequence was executed on 2026-08-20 with Python 3.12.9. Thirteen tests passed, repeat exports were byte-identical, and the expected mart/report matched. See `docs/VALIDATION_RESULTS.md` for the bounded evidence.

## Out of scope

No production connector, hosted service, real mailbox, cloud project, employer schema, performance benchmark, historical metric replay, or production-system simulation.
