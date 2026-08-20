from __future__ import annotations

import csv
import sqlite3
import tempfile
import unittest
from contextlib import closing
from datetime import date
from pathlib import Path

from commerce_data_automation import InputRefused, SchemaContractError, parse_event_date, run_pipeline


SOURCE_FIELDS = [
    "record_id",
    "source_name",
    "event_date_raw",
    "sku_code",
    "units_raw",
    "gross_value_minor",
    "currency_code",
]
BASE_ROWS = [
    ["EVT-0001", "SOURCE_A", "2030-01-02", "SKU-0001", "2", "1200", "TST"],
    ["EVT-0002", "SOURCE_A", "02/01/2030", "SKU-0002", "1", "not_available", "TST"],
    ["EVT-0003", "SOURCE_B", "2030-01-03", "SKU-0001", "3", "1800", "TST"],
    ["EVT-0004", "SOURCE_C", "invalid-date", "SKU-9999", "1", "900", "TST"],
]


class PipelineValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.source = self.root / "source.csv"
        self.reference = self.root / "reference.csv"
        self.output = self.root / "output"
        self._write_source(BASE_ROWS)
        self._write_csv(
            self.reference,
            ["sku_code", "product_state"],
            [["SKU-0001", "active"], ["SKU-0002", "active"]],
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @staticmethod
    def _write_csv(path: Path, fields: list[str], rows: list[list[str]]) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerow(fields)
            writer.writerows(rows)

    def _write_source(self, rows: list[list[str]], fields: list[str] | None = None) -> None:
        self._write_csv(self.source, fields or SOURCE_FIELDS, rows)

    def _run(self, **overrides):
        arguments = {
            "as_of": date(2030, 1, 5),
            "simulate_check_error_sources": ("SOURCE_B",),
        }
        arguments.update(overrides)
        return run_pipeline(self.source, self.reference, self.output, **arguments)

    @staticmethod
    def _csv_rows(path: Path) -> list[dict[str, str]]:
        with path.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def test_val_01_mixed_supported_dates_normalize(self) -> None:
        self.assertEqual(parse_event_date("2030-01-02"), date(2030, 1, 2))
        self.assertEqual(parse_event_date("02/01/2030"), date(2030, 1, 2))

    def test_val_02_invalid_date_remains_an_exception(self) -> None:
        self._run()
        exceptions = self._csv_rows(self.output / "exceptions.csv")
        self.assertIn(("EVT-0004", "INVALID-DATE"), {(row["record_id"], row["issue_code"]) for row in exceptions})
        landing = self._csv_rows(self.output / "landing.csv")
        self.assertEqual(len(landing), 4)

    def test_val_03_malformed_numeric_is_visible_and_non_pass(self) -> None:
        self._run()
        exceptions = self._csv_rows(self.output / "exceptions.csv")
        self.assertIn(
            ("EVT-0002", "INVALID-GROSS-VALUE"),
            {(row["record_id"], row["issue_code"]) for row in exceptions},
        )
        quality = self._csv_rows(self.output / "quality_results.csv")
        self.assertTrue(any(row["verdict"] == "WARN" for row in quality))

    def test_val_04_duplicate_canonical_grain_is_quarantined(self) -> None:
        rows = BASE_ROWS + [["EVT-0005", "SOURCE_A", "2030-01-02", "SKU-0001", "1", "600", "TST"]]
        self._write_source(rows)
        self._run(minimum_records=4)
        exceptions = self._csv_rows(self.output / "exceptions.csv")
        duplicate_ids = {
            row["record_id"] for row in exceptions if row["issue_code"] == "DUPLICATE-CANONICAL-GRAIN"
        }
        self.assertEqual(duplicate_ids, {"EVT-0001", "EVT-0005"})

    def test_val_05_orphan_product_key_is_retained(self) -> None:
        self._run()
        exceptions = self._csv_rows(self.output / "exceptions.csv")
        self.assertIn(("EVT-0004", "ORPHAN-SKU"), {(row["record_id"], row["issue_code"]) for row in exceptions})

    def test_val_06_stale_input_refuses_downstream_write(self) -> None:
        with self.assertRaises(InputRefused):
            self._run(as_of=date(2030, 2, 1))
        self.assertFalse((self.output / "warehouse.db").exists())

    def test_val_07_partial_input_refuses_downstream_write(self) -> None:
        with self.assertRaises(InputRefused):
            self._run(minimum_records=5)
        self.assertFalse((self.output / "warehouse.db").exists())

    def test_val_08_check_exception_is_error_never_pass(self) -> None:
        self._run()
        quality = self._csv_rows(self.output / "quality_results.csv")
        execution = [
            row for row in quality if row["check_id"] == "CHECK-EXECUTION" and row["scope"] == "SOURCE_B"
        ]
        self.assertEqual([row["verdict"] for row in execution], ["ERROR"])

    def test_val_09_repeated_period_is_idempotent(self) -> None:
        first = self._run()
        first_mart = (self.output / "mart.csv").read_bytes()
        second = self._run()
        self.assertEqual(first_mart, (self.output / "mart.csv").read_bytes())
        self.assertEqual(first.as_dict(), second.as_dict())
        with closing(sqlite3.connect(self.output / "warehouse.db")) as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM mart").fetchone()[0], 2)

    def test_val_10_source_to_mart_totals_reconcile(self) -> None:
        self._run()
        mart = self._csv_rows(self.output / "mart.csv")
        self.assertEqual(sum(int(row["units"]) for row in mart), 5)
        self.assertEqual(sum(int(row["gross_value_minor"]) for row in mart), 3000)
        quality = self._csv_rows(self.output / "quality_results.csv")
        self.assertEqual(
            [row["verdict"] for row in quality if row["check_id"] == "CHECK-SOURCE-MART"],
            ["PASS"],
        )

    def test_val_11_mart_to_report_totals_reconcile(self) -> None:
        self._run()
        mart = self._csv_rows(self.output / "mart.csv")
        report = self._csv_rows(self.output / "report.csv")
        self.assertEqual(
            sum(int(row["gross_value_minor"]) for row in mart),
            sum(int(row["gross_value_minor"]) for row in report),
        )
        quality = self._csv_rows(self.output / "quality_results.csv")
        self.assertEqual(
            [row["verdict"] for row in quality if row["check_id"] == "CHECK-MART-REPORT"],
            ["PASS"],
        )

    def test_val_12_same_width_positional_schema_shift_fails(self) -> None:
        shifted = SOURCE_FIELDS.copy()
        shifted[3], shifted[4] = shifted[4], shifted[3]
        self._write_source(BASE_ROWS, fields=shifted)
        with self.assertRaisesRegex(SchemaContractError, "position 4"):
            self._run()

    def test_duplicate_record_id_refuses_before_write(self) -> None:
        rows = BASE_ROWS + [["EVT-0001", "SOURCE_B", "2030-01-03", "SKU-0002", "1", "600", "TST"]]
        self._write_source(rows)
        with self.assertRaisesRegex(InputRefused, "duplicate record_id"):
            self._run()
        self.assertFalse((self.output / "warehouse.db").exists())


if __name__ == "__main__":
    unittest.main()
