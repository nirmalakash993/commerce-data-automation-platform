"""Clean-room commerce data automation reference implementation."""

from .core import (
    InputRefused,
    PipelineResult,
    SchemaContractError,
    VerificationError,
    generate_fixtures,
    parse_event_date,
    run_pipeline,
    verify_outputs,
)

__all__ = [
    "InputRefused",
    "PipelineResult",
    "SchemaContractError",
    "VerificationError",
    "generate_fixtures",
    "parse_event_date",
    "run_pipeline",
    "verify_outputs",
]
