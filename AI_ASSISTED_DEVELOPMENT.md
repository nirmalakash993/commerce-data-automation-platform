# AI-Assisted Development

## Classification

AI assists development; it is not part of the proposed runtime. The reference design is deterministic: parsing, schema checks, SQL transformations, comparisons, and approval gates.

## Division of responsibility

| Responsibility | Human | AI assistance |
|---|---|---|
| problem and scope | defines the operating problem, boundaries, and what must remain manual | helps structure alternatives and questions |
| business meaning | defines grains, mappings, thresholds, exception semantics, and acceptance criteria | drafts logic from supplied rules |
| implementation | reviews design and authorizes changes | accelerates code, SQL, fixtures, and documentation drafts |
| investigation | decides which evidence is authoritative | helps enumerate artifacts, compare definitions, and trace failures |
| validation | selects independent checks and accepts or rejects results | drafts harnesses and summarizes discrepancies |
| production change | retains approval responsibility | may prepare a plan; does not approve itself |

## Working method

1. Encode schemas, rules, prohibitions, and known hazards in persistent project context.
2. Inspect read-only evidence before proposing a change.
3. State assumptions and a bounded plan in plain language.
4. Require explicit human approval before any state-changing action.
5. Run deterministic checks through a path independent of the generated logic where practical.
6. Record contradictions and unknowns instead of resolving them by plausibility.
7. Feed confirmed failures back into fixtures, tests, and written constraints.

## How generated logic is validated

The clean-room implementation is challenged with:

- a malformed row that should remain visible rather than aborting the entire landing step;
- duplicate and orphan keys at the declared grain;
- stale, empty, and partial input;
- a check-query exception that must become `ERROR`;
- a repeated date-bounded run that must not duplicate output;
- a source-to-mart-to-report reconciliation using synthetic values;
- a positional schema comparison, not only a column-count comparison.

All twelve mapped scenarios are executable in `tests/test_pipeline.py`, alongside an additional duplicate-input-key refusal test. The verification recorded on 2026-08-20 ran 13 tests successfully using Python 3.12.9; see `docs/VALIDATION_RESULTS.md`. This is a result for the small synthetic reference only, not the historical system.

## Known AI failure patterns represented by the design

- plausible documentation describing a control that code does not implement;
- validation code treating missing results as success;
- a summary restating a computed fact incorrectly;
- a change with a wider state impact than its prose description;
- a shallow schema check missing a shifted field.

The control is not “AI reviews AI.” The control is traceable evidence, independent execution, bounded scope, and human judgment about business meaning.

## Public claim boundary

It is accurate to say that AI coding agents accelerated investigation, implementation, debugging, review, and documentation under human direction. It is not accurate to call this an AI platform, autonomous pipeline, or machine-learning system.
