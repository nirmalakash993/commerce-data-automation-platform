# Local Runbook

## Environment

- Python 3.11 or newer.
- No package installation.
- No cloud account, credential, network access, environment variable, or service configuration.

Run all commands from the repository root.

## Test

```text
python -m unittest discover -s tests -v
```

The suite maps directly to the twelve scenarios in `VALIDATION_SCENARIOS.md` and adds a duplicate-input-key refusal test.

## Full demo

```text
python -m commerce_data_automation demo --output-dir build/demo
```

The command:

1. reads only `examples/source_feed.csv` and `examples/product_reference.csv`;
2. runs the bounded `2030-01` period with a declared `2030-01-05` as-of date;
3. writes a local SQLite warehouse and reviewable CSV/JSON exports;
4. repeats the period;
5. compares hashes of deterministic exports to verify repeatability;
6. independently compares mart/report rows and totals with expected fixtures.

`build/` is excluded from Git.

## Generate fresh invented fixtures

```text
python -m commerce_data_automation generate --output-dir build/generated --seed 20300102
```

The generator accepts only an output directory and integer seed. It has no option for a production source, connector, credential, or configuration file.

## Run and verify separately

```text
python -m commerce_data_automation run --input examples/source_feed.csv --reference examples/product_reference.csv --output-dir build/run --as-of 2030-01-05 --simulate-check-error SOURCE_B
python -m commerce_data_automation verify --output-dir build/run --expected-mart examples/mart_sample.csv --expected-report examples/report_sample.csv
```

## Expected refusal behavior

The command exits nonzero and does not create the warehouse when:

- the positional schema differs;
- the input has fewer than the configured minimum records;
- no valid event date exists;
- the newest valid event is outside the declared freshness window.

Record-level date, numeric, currency, duplicate-grain, and reference failures remain visible in landing and exception output instead of aborting the entire accepted slice.
