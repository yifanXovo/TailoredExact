# Sealed Pipeline Completion Round Final Report

Branch: `codex/longrun-round17-local-results`
Commit SHA: recorded in the final response after push. The self-referential
final commit SHA cannot be embedded in this file without changing the commit
hash.

## Code Changes

- Added sealed-run finalization fields to `SolveResult` JSON:
  `finalization_source`, `last_progress_event`, `plateau_reason`, and
  `auto_interval_oracle_status_by_leaf`.
- Added CLI parsing for automatic interval BPC fallback budgets:
  `--auto-interval-bpc-time-limit` and `--auto-interval-bpc-max-leaves`.
- Extended automatic interval oracle bookkeeping, including `min-lb` ordering
  and per-leaf status strings.
- Added `scripts/run_sealed_pipeline_completion.py` to run sealed rows,
  synthesize noncertified checkpoint JSONs when solver JSON is missing, run
  checkpoint oracle diagnostics, and summarize the sealed mini-suite.
- Tightened `scripts/audit_bpc_certificate.py` so sealed rows require final
  provenance fields and progress logs require final JSONs.

## Unified Sealed Command

All sealed mini-suite rows used the same algorithm template:

```powershell
build\ExactEBRP.exe --method gcap-frontier `
  --algorithm-preset paper-exact-v20-certificate `
  --paper-run-sealed true `
  --auto-interval-oracle true `
  --auto-interval-oracle-order low-gini `
  --auto-interval-bpc-fallback true `
  --input <instance> --lambda 0.15 --T 3600 `
  --time-limit <budget> --out <raw.json>
```

Only input path, output path, and time budget differed. No row used archive
scanning, external known UB, external incumbent JSON, manual focus intervals, or
instance-specific gamma ranges.

## Certification Summary

See `sealed_minisuite_summary.csv`.

Certified rows:

| row | objective | basis |
| --- | ---: | --- |
| `v4_smoke` | `0` | solver final full-frontier certificate |
| `v12_m2_300s` | `0.718504070755` | relaxation-only full-frontier certificate |
| `v12_m1_600s` | `0.357200583208` | relaxation-only full-frontier certificate |
| `high_imbalance_seed3202` | `1.74931345205` | relaxation-only full-frontier certificate |
| `tight_T_seed3101` | `0.107252734134` | relaxation-only full-frontier certificate |

Noncertified V20 rows:

| row | UB | LB | gap | unresolved | finalization | plateau |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| `high_imbalance_seed3201` | `2.44340319194` | `1.50460803` | `0.384216229658` | `3` | `interrupted_checkpoint` | `checkpoint_oracle_timeout` |
| `tight_T_seed3102` | `0.600704436685` | `0.450176109171` | `0.250586342169` | `1` | `wrapper_checkpoint` | `checkpoint_oracle_timeout` |
| `moderate_seed3301` | `0.0491525526647` | `0.00921610362464` | `0.8125` | `10` | `interrupted_checkpoint` | `checkpoint_oracle_diagnostic_unresolved` |
| `moderate_seed3302` | `0.195636206549` | `0.0252187297505` | `0.87109375` | `6` | `interrupted_checkpoint` | `checkpoint_oracle_timeout` |

Every row now has final JSON. Missing final JSON is no longer an accepted
outcome.

## Oracle and BPC

Checkpoint exact interval cutoff oracle diagnostics were run for the four
noncertified V20 rows:

- `moderate_seed3301`: one checkpoint leaf was proven infeasible;
- `high_imbalance_seed3201`, `tight_T_seed3102`, and `moderate_seed3302`:
  checkpoint leaf oracle timed out.

These oracle rows are diagnostic only because they do not cover the full final
frontier ledger. Automatic BPC fallback did not close any row and remains
diagnostic.

## Audit

Commands run:

```powershell
D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py --self-test
D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py `
  results\sealed_pipeline_completion_round\raw `
  --csv-out results\sealed_pipeline_completion_round\certificate_audit.csv `
  --fail-on-error `
  --require-progress-finals results\sealed_pipeline_completion_round\raw
build\ExactEBRP.exe --method certificate-basis-test ...
build\ExactEBRP.exe --method option-consistency-test ...
D:\msys64\ucrt64\bin\python.exe scripts\audit_no_instance_special_cases.py `
  --out results\sealed_pipeline_completion_round\no_instance_special_case_audit.txt
```

Audit result: `audited_rows=15 failures=0`.

## Paper-Readiness Decision

The sealed pipeline is now complete in the auditable sense: every row produces a
final JSON, noncertified rows are included in audit, and no row depends on
archive scanning, known UB injection, or instance-specific logic.

It is not yet ready for broad paper benchmark testing. The V20 certified count
remains `2/6`, below the requested `3/6` threshold. The next round should focus
on full in-solver automatic interval oracle processing over all unresolved
leaves, safe ledger merge, and leaf partitioning for oracle timeouts.
