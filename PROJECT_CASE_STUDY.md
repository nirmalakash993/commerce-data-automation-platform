# Project Case Study

## Summary

This reference combines three related patterns into one portfolio item: defensive operational ingestion, a governed warehouse, and migration from spreadsheet-owned logic to a thin reporting layer. The combination avoids presenting overlapping parts of one data flow as separate systems.

## Situation

File-based operational sources can be valid enough to open while still being wrong for downstream use. A changed header, stale export, partial attachment, duplicate key, malformed date, or missing product reference can all produce believable output. Reporting workbooks then accumulate duplicate formulas and source dumps because they are compensating for weak upstream contracts.

## Design response

The architecture separates five responsibilities:

1. select and validate the intended input;
2. preserve the received record in a text-tolerant landing layer;
3. normalize meaning in reviewable views;
4. build idempotent tables at explicit business grains;
5. reconcile a bounded presentation layer back to its warehouse source.

Quality results are data, not only alerts. A query or check error is recorded as `ERROR`; silence cannot become a pass.

## Contribution boundary

In the historical employer-context work, I defined data grains, rules, exception behavior, approval boundaries, and acceptance criteria; shaped and operated the architecture; directed and contributed to AI-assisted implementation; and investigated evidence when outputs contradicted expectations. Platform services, source-system behavior, team inputs, and any employer-owned implementation remain separate contributions.

This repository is a new explanatory reconstruction and clean-room implementation. It does not contain or claim to reproduce the original source, configuration, metrics, business rules, or production topology.

## AI-assisted method

AI agents accelerated environment inspection, draft SQL and scripts, debugging, review, and documentation. The method depended on persistent constraints, read-only investigation, explicit approval before state changes, and evidence-backed claims. Human review caught failure modes such as a check failing open, a schema comparison that was too shallow, and prose that overstated what code actually did.

## Validation

Historical acceptance used bounded reconciliation, dry-run inspection, direct source comparisons, and named failure cases. The public reference validates the generic pattern independently with thirteen standard-library tests and a reproducible local demo over invented fixtures. The suite covers refusal, quarantine, error-state preservation, idempotence, schema position, and two reconciliation boundaries. The exact bounded result is recorded in `docs/VALIDATION_RESULTS.md`.

## Outcome represented here

The public-safe outcome is a coherent, inspectable design for moving messy operational inputs toward governed reporting while preserving failures and uncertainty. It is not evidence of a public production deployment or a benchmark.

## Limitations

- No production artifact is included.
- Historical quantitative outcomes are intentionally omitted pending separate disclosure approval.
- SQLite demonstrates data contracts and controls locally; no live BigQuery connector or scale equivalence is claimed.
- The written clearance covers public clean-room code and documentation, but no license grant was approved; the repository therefore has no `LICENSE` file.
