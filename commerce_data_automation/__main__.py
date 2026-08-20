"""Command-line entry point for the clean-room demo."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from .core import (
    InputRefused,
    SchemaContractError,
    VerificationError,
    generate_fixtures,
    output_hashes,
    run_pipeline,
    verify_outputs,
)


def _date(value: str) -> date:
    return date.fromisoformat(value)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the credential-free commerce data reference.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate", help="create deterministic synthetic fixtures")
    generate.add_argument("--output-dir", type=Path, required=True)
    generate.add_argument("--seed", type=int, default=20300102)

    run = subparsers.add_parser("run", help="run the local pipeline over explicit CSV fixtures")
    run.add_argument("--input", type=Path, required=True)
    run.add_argument("--reference", type=Path, required=True)
    run.add_argument("--output-dir", type=Path, required=True)
    run.add_argument("--as-of", type=_date, required=True)
    run.add_argument("--max-age-days", type=int, default=2)
    run.add_argument("--minimum-records", type=int, default=4)
    run.add_argument("--simulate-check-error", action="append", default=[])

    verify = subparsers.add_parser("verify", help="compare generated outputs with expected fixtures")
    verify.add_argument("--output-dir", type=Path, required=True)
    verify.add_argument("--expected-mart", type=Path, required=True)
    verify.add_argument("--expected-report", type=Path, required=True)

    demo = subparsers.add_parser("demo", help="run, repeat, and verify the repository demo")
    demo.add_argument("--output-dir", type=Path, default=Path("build/demo"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "generate":
            paths = generate_fixtures(args.output_dir, args.seed)
            print(json.dumps({key: str(value) for key, value in paths.items()}, indent=2, sort_keys=True))
            return 0
        if args.command == "run":
            result = run_pipeline(
                args.input,
                args.reference,
                args.output_dir,
                as_of=args.as_of,
                max_age_days=args.max_age_days,
                minimum_records=args.minimum_records,
                simulate_check_error_sources=args.simulate_check_error,
            )
            print(json.dumps(result.as_dict(), indent=2, sort_keys=True))
            return 0
        if args.command == "verify":
            result = verify_outputs(args.output_dir, args.expected_mart, args.expected_report)
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0

        first = run_pipeline(
            "examples/source_feed.csv",
            "examples/product_reference.csv",
            args.output_dir,
            as_of=date(2030, 1, 5),
            simulate_check_error_sources=("SOURCE_B",),
        )
        first_hashes = output_hashes(args.output_dir)
        second = run_pipeline(
            "examples/source_feed.csv",
            "examples/product_reference.csv",
            args.output_dir,
            as_of=date(2030, 1, 5),
            simulate_check_error_sources=("SOURCE_B",),
        )
        second_hashes = output_hashes(args.output_dir)
        if first_hashes != second_hashes:
            raise VerificationError("repeat run changed deterministic exports")
        verification = verify_outputs(
            args.output_dir,
            "examples/mart_sample.csv",
            "examples/report_sample.csv",
        )
        print(
            json.dumps(
                {
                    "first_run": first.as_dict(),
                    "second_run": second.as_dict(),
                    "idempotent_exports": True,
                    "verification": verification,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    except (InputRefused, SchemaContractError, VerificationError, OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
