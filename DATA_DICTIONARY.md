# Data Dictionary

All records described here are synthetic and use fictional identifiers. `TST` is a fake currency code used only to exercise numeric reconciliation without resembling a real commercial dataset.

## `source_feed.csv`

| Field | Type | Meaning |
|---|---|---|
| `record_id` | string | fictional input-row identifier |
| `source_name` | string | generic source label such as `SOURCE_A` |
| `event_date_raw` | string | intentionally mixed-format input date |
| `sku_code` | string | fictional product key |
| `units_raw` | string | source-shaped quantity before validation |
| `gross_value_minor` | string | invented unit value in minor `TST` units; may be malformed on purpose |
| `currency_code` | string | always `TST` in examples |

## `product_reference.csv`

| Field | Type | Meaning |
|---|---|---|
| `sku_code` | string | fictional product key |
| `product_state` | enum | `active` for a key accepted by the reference check |

## Generated `landing.csv`

Contains every source field plus `accepted` and pipe-delimited `issues`. All source-shaped fields remain text.

## Generated `exceptions.csv`

| Field | Type | Meaning |
|---|---|---|
| `record_id` | string | fictional input identifier |
| `source_name` | string | generic source label |
| `issue_code` | string | stable validation or reference failure code |
| `detail` | string | generic explanation without source data or configuration |

## `quality_results.csv`

| Field | Type | Meaning |
|---|---|---|
| `run_id` | string | fictional quality-run identifier |
| `check_id` | string | stable generic check name |
| `scope` | string | source or layer being evaluated |
| `verdict` | enum | `PASS`, `WARN`, `FAIL`, or `ERROR` |
| `observed` | string | synthetic observation |
| `expected` | string | stated acceptance condition |

## `mart_sample.csv`

| Field | Type | Meaning |
|---|---|---|
| `business_date` | date | normalized fictional business date |
| `source_name` | string | canonical source label |
| `sku_code` | string | fictional product key |
| `units` | integer | accepted aggregated units |
| `gross_value_minor` | integer | invented aggregated value in minor `TST` units |
| `currency_code` | string | fake currency code |

## `report_sample.csv`

| Field | Type | Meaning |
|---|---|---|
| `period` | string | synthetic reporting period |
| `source_name` | string | report grouping |
| `units` | integer | sum of accepted mart units |
| `gross_value_minor` | integer | sum of invented mart values |
| `quality_state` | string | whether the report slice is acceptable for review |

## Grain and key rules

- Landing grain: one row per `record_id` as received.
- Mart grain: one row per `business_date + source_name + sku_code`.
- Report grain: one row per `period + source_name`.
- A duplicate at mart grain must be surfaced; it must not be silently discarded without an explicit deterministic rule.
- SQLite tables are bounded by `run_scope`; rerunning the same period replaces that scope and leaves no duplicate output.
