# Sealed Run Finalization Protocol

This protocol closes the gap exposed by the sealed mini-suite: a paper run is
not complete unless it emits an auditable final artifact, even when it does not
certify.

## Contract

Every sealed run must end with:

- a final JSON under the run's `raw/` directory;
- an interval ledger CSV, real or checkpoint-derived;
- progress and UB event logs when the solver reached those phases;
- explicit provenance fields:
  - `sealed_run=true`;
  - `no_archive_scanning=true`;
  - `no_external_known_ub=true`;
  - `no_focus_only_certificate=true`;
  - `finalization_source`.

Allowed `finalization_source` values are:

- `solver_final_json`: the solver wrote its own final result;
- `wrapper_checkpoint`: the wrapper synthesized a noncertified artifact from a
  completed progress checkpoint;
- `interrupted_checkpoint`: the wrapper synthesized a noncertified artifact
  after a wall-clock interruption or missing solver JSON;
- `error_json`: the wrapper recorded a solver or launch error.

Only `solver_final_json` can certify a row. Checkpoint and error artifacts are
paper-auditable evidence of failure, not certificates.

## Noncertified Fields

For noncertified sealed rows the JSON must include:

- `certified_original_problem=false`;
- `lower_bound`, `upper_bound`, and `gap`;
- `unresolved_intervals`, `open_nodes`, and `invalid_bound_intervals`;
- `frontier_covers_all_improving_gini_values=false` unless the solver proved
  full coverage;
- `stop_reason`;
- `last_progress_event`;
- `plateau_reason`.

Missing final JSON is treated as an audit failure when progress logs exist.

## Wrapper Behavior

`scripts/run_sealed_pipeline_completion.py` implements this contract. Its
`run-row` command launches the sealed solver command and writes a checkpoint
JSON if the solver exits without final JSON. Its `summarize` command includes
both certified and noncertified rows. Its `self-test` command simulates a
missing final JSON and checks that a noncertified artifact is emitted.

Current self-test output:

```text
results/sealed_pipeline_completion_round/finalization_tests/finalization_test_summary.csv
```
