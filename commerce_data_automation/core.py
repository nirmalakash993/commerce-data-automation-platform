"""Deterministic, credential-free data quality and warehouse demo.

The module reads only explicitly supplied local CSV fixtures. It has no connector,
network, environment-variable, or production-data input path.
"""

from __future__ import annotations

import csv
import hashlib
import json
import random
import sqlite3
from collections import Counter, defaultdict
from contextlib import closing
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Iterable, Sequence


SOURCE_SCHEMA = (
    "record_id",
    "source_name",
    "event_date_raw",
    "sku_code",
    "units_raw",
    "gross_value_minor",
    "currency_code",
)
REFERENCE_SCHEMA = ("sku_code", "product_state")
OUTPUT_FILES = (
    "landing.csv",
    "exceptions.csv",
    "mart.csv",
    "report.csv",
    "quality_results.csv",
    "run_summary.json",
)


class SchemaContractError(ValueError):
    """Raised when a CSV header differs from its positional contract."""


class InputRefused(ValueError):
    """Raised when freshness or completeness prevents a downstream write."""


class VerificationError(AssertionError):
    """Raised when generated outputs do not reconcile with expected fixtures."""


@dataclass(frozen=True)
class PipelineResult:
    run_scope: str
    input_rows: int
    accepted_rows: int
    exception_count: int
    mart_rows: int
    report_rows: int
    verdict_counts: dict[str, int]
    output_dir: Path

    def as_dict(self) -> dict[str, object]:
        return {
            "run_scope": self.run_scope,
            "input_rows": self.input_rows,
            "accepted_rows": self.accepted_rows,
            "exception_count": self.exception_count,
            "mart_rows": self.mart_rows,
            "report_rows": self.report_rows,
            "verdict_counts": dict(sorted(self.verdict_counts.items())),
            "output_dir": str(self.output_dir),
        }


def parse_event_date(value: str) -> date | None:
    """Parse the two deliberately supported fixture formats safely."""

    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _safe_int(value: str) -> int | None:
    try:
        return int(value.strip())
    except (TypeError, ValueError):
        return None


def _validate_header(actual: Sequence[str], expected: Sequence[str], path: Path) -> None:
    if tuple(actual) == tuple(expected):
        return
    missing = [name for name in expected if name not in actual]
    extra = [name for name in actual if name not in expected]
    shifted = [
        f"position {index + 1}: expected {wanted!r}, found {found!r}"
        for index, (wanted, found) in enumerate(zip(expected, actual))
        if wanted != found
    ]
    details = []
    if missing:
        details.append(f"missing={missing}")
    if extra:
        details.append(f"extra={extra}")
    if shifted:
        details.append("shifted=" + "; ".join(shifted))
    raise SchemaContractError(f"schema contract failed for {path.name}: " + ", ".join(details))


def _read_csv(path: Path, schema: Sequence[str]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        _validate_header(reader.fieldnames or (), schema, path)
        return [dict(row) for row in reader]


def _write_csv(path: Path, fieldnames: Sequence[str], rows: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def generate_fixtures(output_dir: Path | str, seed: int = 20300102) -> dict[str, Path]:
    """Create invented fixtures from a fixed seed with no external input path."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    units_a = rng.randint(1, 4)
    units_b = rng.randint(2, 5)
    source_rows = [
        {
            "record_id": "EVT-0001",
            "source_name": "SOURCE_A",
            "event_date_raw": "2030-01-02",
            "sku_code": "SKU-0001",
            "units_raw": str(units_a),
            "gross_value_minor": str(units_a * 600),
            "currency_code": "TST",
        },
        {
            "record_id": "EVT-0002",
            "source_name": "SOURCE_A",
            "event_date_raw": "02/01/2030",
            "sku_code": "SKU-0002",
            "units_raw": "1",
            "gross_value_minor": "not_available",
            "currency_code": "TST",
        },
        {
            "record_id": "EVT-0003",
            "source_name": "SOURCE_B",
            "event_date_raw": "2030-01-03",
            "sku_code": "SKU-0001",
            "units_raw": str(units_b),
            "gross_value_minor": str(units_b * 600),
            "currency_code": "TST",
        },
        {
            "record_id": "EVT-0004",
            "source_name": "SOURCE_C",
            "event_date_raw": "invalid-date",
            "sku_code": "SKU-9999",
            "units_raw": "1",
            "gross_value_minor": "900",
            "currency_code": "TST",
        },
    ]
    references = [
        {"sku_code": "SKU-0001", "product_state": "active"},
        {"sku_code": "SKU-0002", "product_state": "active"},
    ]
    source_path = output / "source_feed.csv"
    reference_path = output / "product_reference.csv"
    _write_csv(source_path, SOURCE_SCHEMA, source_rows)
    _write_csv(reference_path, REFERENCE_SCHEMA, references)
    return {"source": source_path, "reference": reference_path}


def _quality_row(
    run_id: str,
    check_id: str,
    scope: str,
    verdict: str,
    observed: str,
    expected: str,
) -> dict[str, str]:
    return {
        "run_id": run_id,
        "check_id": check_id,
        "scope": scope,
        "verdict": verdict,
        "observed": observed,
        "expected": expected,
    }


def _initialize_database(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        PRAGMA foreign_keys = ON;
        CREATE TABLE IF NOT EXISTS landing (
            run_scope TEXT NOT NULL,
            record_id TEXT NOT NULL,
            source_name TEXT NOT NULL,
            event_date_raw TEXT NOT NULL,
            sku_code TEXT NOT NULL,
            units_raw TEXT NOT NULL,
            gross_value_minor TEXT NOT NULL,
            currency_code TEXT NOT NULL,
            accepted INTEGER NOT NULL,
            issues_json TEXT NOT NULL,
            PRIMARY KEY (run_scope, record_id)
        );
        CREATE TABLE IF NOT EXISTS exceptions (
            run_scope TEXT NOT NULL,
            record_id TEXT NOT NULL,
            source_name TEXT NOT NULL,
            issue_code TEXT NOT NULL,
            detail TEXT NOT NULL,
            PRIMARY KEY (run_scope, record_id, issue_code)
        );
        CREATE TABLE IF NOT EXISTS mart (
            run_scope TEXT NOT NULL,
            business_date TEXT NOT NULL,
            source_name TEXT NOT NULL,
            sku_code TEXT NOT NULL,
            units INTEGER NOT NULL,
            gross_value_minor INTEGER NOT NULL,
            currency_code TEXT NOT NULL,
            PRIMARY KEY (run_scope, business_date, source_name, sku_code)
        );
        CREATE TABLE IF NOT EXISTS report (
            run_scope TEXT NOT NULL,
            period TEXT NOT NULL,
            source_name TEXT NOT NULL,
            units INTEGER NOT NULL,
            gross_value_minor INTEGER NOT NULL,
            quality_state TEXT NOT NULL,
            PRIMARY KEY (run_scope, period, source_name)
        );
        CREATE TABLE IF NOT EXISTS quality_results (
            run_scope TEXT NOT NULL,
            run_id TEXT NOT NULL,
            check_id TEXT NOT NULL,
            scope TEXT NOT NULL,
            verdict TEXT NOT NULL,
            observed TEXT NOT NULL,
            expected TEXT NOT NULL,
            PRIMARY KEY (run_scope, run_id, check_id, scope)
        );
        """
    )


def run_pipeline(
    input_path: Path | str,
    reference_path: Path | str,
    output_dir: Path | str,
    *,
    as_of: date,
    max_age_days: int = 2,
    minimum_records: int = 4,
    simulate_check_error_sources: Iterable[str] = (),
) -> PipelineResult:
    """Run the bounded local pipeline and export deterministic review artifacts."""

    source_path = Path(input_path)
    product_path = Path(reference_path)
    output = Path(output_dir)
    source_rows = _read_csv(source_path, SOURCE_SCHEMA)
    references = _read_csv(product_path, REFERENCE_SCHEMA)

    if len(source_rows) < minimum_records:
        raise InputRefused(
            f"partial input refused: observed {len(source_rows)} records; expected at least {minimum_records}"
        )

    duplicate_record_ids = sorted(
        record_id for record_id, count in Counter(row["record_id"] for row in source_rows).items() if count > 1
    )
    if duplicate_record_ids:
        raise InputRefused(f"duplicate record_id refused before write: {duplicate_record_ids}")

    valid_dates = [parsed for row in source_rows if (parsed := parse_event_date(row["event_date_raw"]))]
    if not valid_dates:
        raise InputRefused("stale input refused: no valid event date is available")
    age_days = (as_of - max(valid_dates)).days
    if age_days < 0 or age_days > max_age_days:
        raise InputRefused(
            f"stale input refused: newest valid event is {age_days} days from the declared as-of date; "
            f"allowed range is 0..{max_age_days}"
        )

    active_skus = {row["sku_code"] for row in references if row["product_state"] == "active"}
    parsed_rows: list[dict[str, object]] = []
    issues_by_record: dict[str, list[tuple[str, str]]] = defaultdict(list)
    source_issue_verdicts: dict[str, set[str]] = defaultdict(set)

    for row in source_rows:
        record_id = row["record_id"]
        source_name = row["source_name"]
        event_date = parse_event_date(row["event_date_raw"])
        units = _safe_int(row["units_raw"])
        gross = _safe_int(row["gross_value_minor"])

        if event_date is None:
            issues_by_record[record_id].append(("INVALID-DATE", "event_date_raw cannot be parsed"))
            source_issue_verdicts[source_name].add("FAIL")
        if units is None or units < 0:
            issues_by_record[record_id].append(("INVALID-UNITS", "units_raw must be a non-negative integer"))
            source_issue_verdicts[source_name].add("WARN")
        if gross is None or gross < 0:
            issues_by_record[record_id].append(
                ("INVALID-GROSS-VALUE", "gross_value_minor must be a non-negative integer")
            )
            source_issue_verdicts[source_name].add("WARN")
        if row["currency_code"] != "TST":
            issues_by_record[record_id].append(("INVALID-CURRENCY", "only the fictional TST code is accepted"))
            source_issue_verdicts[source_name].add("FAIL")
        if row["sku_code"] not in active_skus:
            issues_by_record[record_id].append(("ORPHAN-SKU", "sku_code is absent from the active reference"))
            source_issue_verdicts[source_name].add("FAIL")

        parsed_rows.append(
            {
                **row,
                "event_date": event_date,
                "units": units,
                "gross": gross,
            }
        )

    candidate_rows = [row for row in parsed_rows if not issues_by_record[row["record_id"]]]
    grain_counts = Counter(
        (row["event_date"], row["source_name"], row["sku_code"]) for row in candidate_rows
    )
    for row in candidate_rows:
        grain = (row["event_date"], row["source_name"], row["sku_code"])
        if grain_counts[grain] > 1:
            issues_by_record[row["record_id"]].append(
                ("DUPLICATE-CANONICAL-GRAIN", "business_date + source_name + sku_code is not unique")
            )
            source_issue_verdicts[row["source_name"]].add("FAIL")

    accepted = [row for row in parsed_rows if not issues_by_record[row["record_id"]]]
    run_scope = max(row["event_date"] for row in accepted).strftime("%Y-%m") if accepted else max(valid_dates).strftime("%Y-%m")
    run_id = f"RUN-{run_scope.replace('-', '')}"

    quality: list[dict[str, str]] = [
        _quality_row(run_id, "CHECK-SCHEMA", "SOURCE_FEED", "PASS", "exact-positional-match", "exact-positional-match"),
        _quality_row(run_id, "CHECK-COMPLETENESS", "SOURCE_FEED", "PASS", str(len(source_rows)), f">={minimum_records}"),
        _quality_row(run_id, "CHECK-FRESHNESS", "SOURCE_FEED", "PASS", f"{age_days}-days", f"0..{max_age_days}-days"),
    ]

    issue_groups: dict[tuple[str, str], int] = Counter()
    for row in parsed_rows:
        for issue_code, _ in issues_by_record[row["record_id"]]:
            issue_groups[(row["source_name"], issue_code)] += 1
    for (scope, issue_code), count in sorted(issue_groups.items()):
        verdict = "WARN" if issue_code in {"INVALID-UNITS", "INVALID-GROSS-VALUE"} else "FAIL"
        quality.append(
            _quality_row(run_id, f"CHECK-{issue_code}", scope, verdict, f"{count}-record(s)", "0-records")
        )

    simulated_errors = set(simulate_check_error_sources)
    for source_name in sorted({row["source_name"] for row in source_rows}):
        if source_name in simulated_errors:
            try:
                raise RuntimeError("synthetic check exception")
            except RuntimeError:
                quality.append(
                    _quality_row(
                        run_id,
                        "CHECK-EXECUTION",
                        source_name,
                        "ERROR",
                        "simulated-check-error",
                        "successful-check-execution",
                    )
                )
                source_issue_verdicts[source_name].add("ERROR")
        else:
            quality.append(
                _quality_row(
                    run_id,
                    "CHECK-EXECUTION",
                    source_name,
                    "PASS",
                    "completed",
                    "successful-check-execution",
                )
            )

    mart_groups: dict[tuple[date, str, str, str], dict[str, int]] = defaultdict(
        lambda: {"units": 0, "gross_value_minor": 0}
    )
    for row in accepted:
        key = (row["event_date"], row["source_name"], row["sku_code"], row["currency_code"])
        mart_groups[key]["units"] += int(row["units"])
        mart_groups[key]["gross_value_minor"] += int(row["gross"])

    mart_rows = [
        {
            "business_date": key[0].isoformat(),
            "source_name": key[1],
            "sku_code": key[2],
            "units": values["units"],
            "gross_value_minor": values["gross_value_minor"],
            "currency_code": key[3],
        }
        for key, values in sorted(mart_groups.items())
    ]
    accepted_units = sum(int(row["units"]) for row in accepted)
    accepted_gross = sum(int(row["gross"]) for row in accepted)
    mart_units = sum(int(row["units"]) for row in mart_rows)
    mart_gross = sum(int(row["gross_value_minor"]) for row in mart_rows)
    source_mart_pass = (accepted_units, accepted_gross) == (mart_units, mart_gross)
    quality.append(
        _quality_row(
            run_id,
            "CHECK-SOURCE-MART",
            run_scope,
            "PASS" if source_mart_pass else "FAIL",
            f"units={mart_units};gross={mart_gross}",
            f"units={accepted_units};gross={accepted_gross}",
        )
    )

    report_groups: dict[str, dict[str, int]] = defaultdict(lambda: {"units": 0, "gross_value_minor": 0})
    for row in mart_rows:
        report_groups[row["source_name"]]["units"] += int(row["units"])
        report_groups[row["source_name"]]["gross_value_minor"] += int(row["gross_value_minor"])
    report_rows = []
    for source_name, totals in sorted(report_groups.items()):
        verdicts = source_issue_verdicts.get(source_name, set())
        if "ERROR" in verdicts:
            quality_state = "blocked-by-check-error"
        elif verdicts & {"WARN", "FAIL"}:
            quality_state = "review-required"
        else:
            quality_state = "ready-for-review"
        report_rows.append(
            {
                "period": run_scope,
                "source_name": source_name,
                "units": totals["units"],
                "gross_value_minor": totals["gross_value_minor"],
                "quality_state": quality_state,
            }
        )

    report_units = sum(int(row["units"]) for row in report_rows)
    report_gross = sum(int(row["gross_value_minor"]) for row in report_rows)
    mart_report_pass = (mart_units, mart_gross) == (report_units, report_gross)
    quality.append(
        _quality_row(
            run_id,
            "CHECK-MART-REPORT",
            run_scope,
            "PASS" if mart_report_pass else "FAIL",
            f"units={report_units};gross={report_gross}",
            f"units={mart_units};gross={mart_gross}",
        )
    )

    exception_rows = [
        {
            "record_id": row["record_id"],
            "source_name": row["source_name"],
            "issue_code": issue_code,
            "detail": detail,
        }
        for row in parsed_rows
        for issue_code, detail in issues_by_record[row["record_id"]]
    ]
    landing_rows = [
        {
            **{name: row[name] for name in SOURCE_SCHEMA},
            "accepted": "true" if not issues_by_record[row["record_id"]] else "false",
            "issues": "|".join(code for code, _ in issues_by_record[row["record_id"]]),
        }
        for row in parsed_rows
    ]

    output.mkdir(parents=True, exist_ok=True)
    database_path = output / "warehouse.db"
    with closing(sqlite3.connect(database_path)) as connection:
        _initialize_database(connection)
        with connection:
            for table in ("landing", "exceptions", "mart", "report", "quality_results"):
                connection.execute(f"DELETE FROM {table} WHERE run_scope = ?", (run_scope,))
            connection.executemany(
                """
                INSERT INTO landing VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        run_scope,
                        row["record_id"],
                        row["source_name"],
                        row["event_date_raw"],
                        row["sku_code"],
                        row["units_raw"],
                        row["gross_value_minor"],
                        row["currency_code"],
                        1 if row["accepted"] == "true" else 0,
                        json.dumps(row["issues"].split("|") if row["issues"] else [], separators=(",", ":")),
                    )
                    for row in landing_rows
                ],
            )
            connection.executemany(
                "INSERT INTO exceptions VALUES (?, ?, ?, ?, ?)",
                [
                    (run_scope, row["record_id"], row["source_name"], row["issue_code"], row["detail"])
                    for row in exception_rows
                ],
            )
            connection.executemany(
                "INSERT INTO mart VALUES (?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        run_scope,
                        row["business_date"],
                        row["source_name"],
                        row["sku_code"],
                        row["units"],
                        row["gross_value_minor"],
                        row["currency_code"],
                    )
                    for row in mart_rows
                ],
            )
            connection.executemany(
                "INSERT INTO report VALUES (?, ?, ?, ?, ?, ?)",
                [
                    (
                        run_scope,
                        row["period"],
                        row["source_name"],
                        row["units"],
                        row["gross_value_minor"],
                        row["quality_state"],
                    )
                    for row in report_rows
                ],
            )
            connection.executemany(
                "INSERT INTO quality_results VALUES (?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        run_scope,
                        row["run_id"],
                        row["check_id"],
                        row["scope"],
                        row["verdict"],
                        row["observed"],
                        row["expected"],
                    )
                    for row in quality
                ],
            )

    _write_csv(output / "landing.csv", (*SOURCE_SCHEMA, "accepted", "issues"), landing_rows)
    _write_csv(output / "exceptions.csv", ("record_id", "source_name", "issue_code", "detail"), exception_rows)
    _write_csv(
        output / "mart.csv",
        ("business_date", "source_name", "sku_code", "units", "gross_value_minor", "currency_code"),
        mart_rows,
    )
    _write_csv(
        output / "report.csv",
        ("period", "source_name", "units", "gross_value_minor", "quality_state"),
        report_rows,
    )
    _write_csv(
        output / "quality_results.csv",
        ("run_id", "check_id", "scope", "verdict", "observed", "expected"),
        quality,
    )
    verdict_counts = Counter(row["verdict"] for row in quality)
    result = PipelineResult(
        run_scope=run_scope,
        input_rows=len(source_rows),
        accepted_rows=len(accepted),
        exception_count=len(exception_rows),
        mart_rows=len(mart_rows),
        report_rows=len(report_rows),
        verdict_counts=dict(verdict_counts),
        output_dir=output,
    )
    (output / "run_summary.json").write_text(
        json.dumps(result.as_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def verify_outputs(
    output_dir: Path | str,
    expected_mart_path: Path | str,
    expected_report_path: Path | str,
) -> dict[str, object]:
    """Compare exact generated mart/report rows and independently reconcile totals."""

    output = Path(output_dir)
    actual_mart = _read_csv(
        output / "mart.csv",
        ("business_date", "source_name", "sku_code", "units", "gross_value_minor", "currency_code"),
    )
    expected_mart = _read_csv(
        Path(expected_mart_path),
        ("business_date", "source_name", "sku_code", "units", "gross_value_minor", "currency_code"),
    )
    actual_report = _read_csv(
        output / "report.csv",
        ("period", "source_name", "units", "gross_value_minor", "quality_state"),
    )
    expected_report = _read_csv(
        Path(expected_report_path),
        ("period", "source_name", "units", "gross_value_minor", "quality_state"),
    )
    if actual_mart != expected_mart:
        raise VerificationError(f"mart mismatch: actual={actual_mart!r}; expected={expected_mart!r}")
    if actual_report != expected_report:
        raise VerificationError(f"report mismatch: actual={actual_report!r}; expected={expected_report!r}")

    mart_totals = (
        sum(int(row["units"]) for row in actual_mart),
        sum(int(row["gross_value_minor"]) for row in actual_mart),
    )
    report_totals = (
        sum(int(row["units"]) for row in actual_report),
        sum(int(row["gross_value_minor"]) for row in actual_report),
    )
    if mart_totals != report_totals:
        raise VerificationError(f"mart/report totals differ: {mart_totals!r} != {report_totals!r}")
    return {
        "mart_matches": True,
        "report_matches": True,
        "reconciled_units": mart_totals[0],
        "reconciled_gross_value_minor": mart_totals[1],
    }


def output_hashes(output_dir: Path | str) -> dict[str, str]:
    """Hash deterministic exports, excluding the mutable SQLite file."""

    output = Path(output_dir)
    return {
        name: hashlib.sha256((output / name).read_bytes()).hexdigest()
        for name in OUTPUT_FILES
    }
