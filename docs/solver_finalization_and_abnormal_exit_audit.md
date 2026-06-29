# Solver Finalization And Abnormal Exit Audit

The sealed pipeline now requires every row to produce an auditable final JSON,
including noncertified rows. Wrapper-synthesized JSON remains a fallback only;
the preferred outcome is solver-side finalization.

## Finalization Contract

Every final JSON includes:

- `finalization_source`;
- `solver_finalization_reached`;
- `wrapper_synthesized_final_json`;
- `process_return_code`;
- `abnormal_exit_detected`;
- `abnormal_exit_reason`;
- `stop_reason`;
- `last_progress_event`;
- `plateau_reason`.

For normal solver exits, `finalization_source=solver_final_json`,
`solver_finalization_reached=true`, `process_return_code=0`, and
`abnormal_exit_detected=false`.

For wrapper fallback, the artifact must remain noncertified and must preserve
the latest safe checkpoint lower bound, upper bound, unresolved interval count,
and stop reason. The wrapper is not allowed to synthesize optimality.

## Abnormal Exit Retest

The previous `tight_T_seed3102` sealed run had an abnormal Windows return code
`3221225477`. In `results/sealed_closure_round/`, the rerun exits normally:

- `process_return_code=0`;
- `abnormal_exit_detected=false`;
- `solver_finalization_reached=true`;
- `finalization_source=solver_final_json`.

The row remains noncertified because all oracle child attempts timed out, not
because the process crashed or omitted a final artifact.

## Audit Coverage

`scripts/audit_bpc_certificate.py` was run with
`--require-progress-finals results/sealed_closure_round/raw`. The audit covers
every final JSON in the raw directory and passes noncertified rows only when
they explicitly report `certified_original_problem=false`.
