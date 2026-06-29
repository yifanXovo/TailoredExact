# Sealed Paper-Run Protocol

This protocol defines the paper-candidate execution mode used in
`results/sealed_paper_pipeline_round/`.

## Command Contract

Paper-candidate rows use one command template:

```powershell
build\ExactEBRP.exe --method gcap-frontier `
  --algorithm-preset paper-exact-v20-certificate `
  --paper-run-sealed true `
  --input <instance> --lambda 0.15 --T 3600 `
  --time-limit <budget> --out <raw.json>
```

Only the input path, output path, progress/UB-event output paths, and time
budget differ between rows.

## Provenance Rules

When `--paper-run-sealed true` is active, the solver records:

- `sealed_run=true`;
- a `sealed_run_id` and start timestamp;
- `no_archive_scanning=true`;
- `no_external_known_ub=true`;
- `no_focus_only_certificate=true`;
- incumbent provenance and whether the incumbent was generated inside the run.

The sealed run guard disables arbitrary incumbent archive scanning and rejects
paper certification if the row uses external incumbent JSON, HGA incumbent
imports, focus-only certificate paths, resume/imported focus bounds, or a
manually supplied interval cutoff UB outside the interval-oracle method.

## Certificate Rules

The native HGA-TGBC incumbent is a verifier-gated upper bound only. It never
contributes lower-bound evidence. A sealed row can be reported as an
original-problem certificate only when the full frontier ledger is closed:

- `status=optimal`;
- `objective=lower_bound=upper_bound` within tolerance;
- `certified_original_problem=true`;
- `verifier_passed=true`;
- `unresolved_intervals=0`;
- `invalid_bound_intervals=0`;
- `open_nodes=0`;
- full improving-Gini frontier coverage is recorded.

Automatic interval-oracle rows close leaves only when the compact original
fixed-interval cutoff MIP proves infeasibility. Timeouts and feasible relaxed
diagnostics leave the full result noncertified.
