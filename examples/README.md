# Synthetic Examples

These hand-authored fictional fixtures document the executable data contracts. They are not production-derived. The runnable implementation reads them locally and writes generated output only under an ignored directory selected by the reviewer.

Suggested reading order:

1. `source_feed.csv` — intentionally messy input.
2. `product_reference.csv` — the tiny active-key reference used by validation.
3. `quality_results.csv` — an illustrative compact outcome table, including `WARN`, `FAIL`, and `ERROR`.
4. `mart_sample.csv` — expected accepted rows at the documented canonical grain.
5. `report_sample.csv` — the expected thin aggregate over accepted mart rows.

The examples use future dates, generic source names, fictional IDs, and `TST`, a fake currency code. They demonstrate the clean-room implementation only; they do not prove or reproduce the historical system.
