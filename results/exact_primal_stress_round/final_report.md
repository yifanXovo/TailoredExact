# Exact Primal Stress Round Final Report

Branch: `codex/longrun-round17-local-results`  
Start commit: `a878a5d153da5c61d877a480cdb73c6eb7d3aeb3`  
Final commit: recorded in the final response after push.

## Code Changes

- Added `--ub-event-log` support for paper-core accepted incumbents.
- Added JSON summary fields for initial UB, final UB, after-initial UB
  improvement count/timing/source, and exact-phase primal module calls.
- Added route-pool incumbent master call/success counters.
- Added a deterministic verifier-gated local re-decode repair pass:
  `--exact-phase-local-redecode-repair true|false`.
- Added deterministic hard V20/M3 generation script:
  `scripts/generate_hard_exact_stress_instances.py`.
- Updated fallback build command in README to include native HGA-TGBC sources.

## Existing Dataset Results

| case | status | UB | LB | gap | certified | UB improved after initial |
|---|---|---:|---:|---:|---|---|
| V4 smoke | optimal | 0 | 0 | 0 | yes | no |
| V12 M2 regenerated | optimal | 0.718504070755 | 0.718504070755 | 0 | yes | no |
| V12 M1 regenerated | not closed | 0.357200583208 | 0.332675660948 | 0.0686586848205 | no | no |
| V12 M2 greedy-start | optimal | 0.718504070755 | 0.718504070755 | 0 | yes | yes |

The regenerated V12 M2 `0.718504070755` claim is backed by raw JSON and the
local audit CSV. The earlier documentation/raw mismatch concern does not apply
to this round's new result.

## V20/M3 Stress Results

Six hard generated V20/M3 instances were tested with native HGA-TGBC and 300s
paper-core runs. None certified. Initial UB did not improve during the exact
phase in the six native-HGA rows. The main plateau is relaxation lower-bound
strength/time, not pricing.

Selected gaps:

- `tight_T_seed3101`: gap `0.539352457127`.
- `tight_T_seed3102`: gap `0.117001706903`.
- `high_imbalance_seed3201`: gap `0.133872050793`.
- `high_imbalance_seed3202`: gap `0.123952619596`.
- `moderate_seed3301`: gap `0.130305288314`.
- `moderate_seed3302`: gap `0.339917396426`.

Two selected V20 rows were rerun with a larger local re-decode repair budget.
They still had no UB improvement, confirming the next target is bound strength.

## Weak UB Experiment

The V12 M2 greedy-start row deliberately began with weak UB `0.789342396801`.
The exact-phase local re-decode repair found verifier-passed UB
`0.718504070755`, and the full frontier certified that value. This confirms the
run can improve a weak initial UB through a paper-reproducible UB-only module.

## Audit Status

The requested Python audit could not run because this machine has only the
WindowsApps `python.exe` placeholder. A PowerShell field audit over result JSONs
was generated at `certificate_audit.csv`; all 20 result JSON rows passed the
local checks. The C++ `certificate-basis-test` and `option-consistency-test`
diagnostics both exited 0. No incumbent source contributes lower-bound evidence.

## Bottleneck

For V12 M1 and V20/M3, the bottleneck is valid relaxation lower-bound closure.
The recommended next step is stronger certificate-safe interval relaxations
and relaxation cache reuse, not another broad heuristic-only round.
