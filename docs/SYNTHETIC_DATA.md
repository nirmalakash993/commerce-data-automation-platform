# Synthetic Data

## Principle

Fixtures are invented from structural requirements, not transformed from production records. No source row may be masked, shuffled, hashed, perturbed, or otherwise converted into a public example.

## Current fixtures

The `examples/` directory uses:

- fictional identifiers such as `EVT-0001` and `SKU-0001`;
- generic sources such as `SOURCE_A`;
- future dates in 2030;
- `TST`, a fake currency code;
- small, reviewable values chosen only to expose validation behavior.

## Deliberate edge cases

- mixed date formats;
- an invalid date;
- a malformed numeric value;
- a source with a warning state;
- a check execution represented as `ERROR`;
- an excluded record that prevents one report slice from being accepted.

## Generator controls

- fixed seed stated in the command and documentation;
- no environment variable or path that can point to production data;
- schemas declared in `DATA_DICTIONARY.md`;
- generated files small enough to review line by line;
- fixed fictional identifier prefixes in the generated rows;
- secret and identifier scanning of generated output.
