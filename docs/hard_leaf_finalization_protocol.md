# Hard Leaf Finalization Protocol

This protocol applies to `paper-gf-tailored-bc` fixed-interval hard-leaf runs where CPLEX is managed through the tailored callback API.

## Required Artifacts

Every hard-leaf run must produce a final JSON, even if the native solver process exceeds the requested time limit or exits before the CPLEX best-bound API can be queried. The wrapper may write a noncertified JSON only when it clearly labels the source as wrapper finalization.

The final JSON and summary CSVs must record:

- `progress_log_path`;
- `progress_checkpoints_written`;
- `gap_trajectory_available`;
- `compact_bc_best_bound_available`;
- `compact_bc_best_bound_fail_reason`;
- `compact_bc_native_time_limit_param_id`;
- `compact_bc_native_time_limit_seconds`;
- `compact_bc_native_time_limit_set_rc`;
- `compact_bc_callback_abort_requests`;
- `plateau_detected`;
- `last_bound_improvement_time`;
- `finalization_source`;
- `wrapper_timeout_noncertified` status when the wrapper, rather than CPLEX, terminates the row.

## Checkpoint Semantics

Callback-managed tailored BC rows must write heartbeat checkpoints at the configured progress interval. These checkpoint rows are diagnostic until CPLEX exposes a valid best bound for the fixed-interval model.

Plain fixed-interval MIP rows and static tailored rows are not callback-managed rows. They are not required to write callback checkpoint rows, but they still must write final JSON.

## Bound Validity

A hard-leaf lower bound may enter paper evidence only when it has an explicit valid scope:

- CPLEX final best bound for the original fixed-interval model;
- fixed-interval infeasibility certificate;
- valid relaxation/frontier bound;
- audited full-frontier ledger aggregation.

Wrapper checkpoints without a valid CPLEX best bound are progress diagnostics only. They must not be merged as paper-core lower-bound evidence.

## Timeout Handling

This round tested CPLEX callback wall-clock abort. The generic callback abort request did not reliably stop the moderate low-Gini hard leaf in this build. Therefore wrapper-managed timeout finalization remains mandatory for callback hard-leaf diagnostics.

When a wrapper timeout occurs, the row must be noncertified unless a valid earlier checkpoint or solver-final certificate exists. If no valid best bound was exposed, summaries use `no_valid_bound_emitted`.

The finalization round confirmed that `CPX_PARAM_TILIM` is set before `CPXmipopt` and that callback-side deadline checks can request `CPXcallbackabort`. These safeguards are recorded for audit, but they are not themselves certificate evidence. If CPLEX does not return a final status and best bound, the parent wrapper may preserve progress traces and produce final JSON only under a noncertified status.

## Valid Checkpoint Trajectory

The bound-trajectory round distinguishes two checkpoint classes:

- heartbeat-only rows, which show callback activity but no solver-native bound;
- CPLEX-native bound rows, where `best_bound_available=true` and `progress_source=cplex_native_callback_info`.

A CPLEX-native bound checkpoint is a valid diagnostic lower bound for the original fixed-interval compact model at that point in the solve. If the worker is externally killed before `CPXmipopt` returns, the wrapper may preserve the best checkpoint in final JSON with:

- `status=wrapper_timeout_valid_checkpoint_bound`;
- `finalization_source=wrapper_best_cplex_native_checkpoint`;
- `compact_bc_best_bound_available=true`;
- `compact_bc_bound_valid=true`;
- `interval_oracle_can_merge_bound=false`.

That row remains noncertified and diagnostic-only unless a future parent-frontier implementation explicitly audits checkpoint-bound evidence before merging it.

The long-run convergence runner preserves this distinction for every row: solver-final rows can be certified or noncertified according to the fixed-interval model status, while wrapper checkpoint rows are diagnostic-only even when the checkpoint bound is valid.
