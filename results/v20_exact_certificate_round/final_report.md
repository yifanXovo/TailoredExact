# V20 Exact Certificate Round Final Report

Branch: `codex/longrun-round17-local-results`
Starting remote head: `e41ba513de0acae653c44299c718c0c1bf8e2fce`
Synchronized implementation commit SHA: pending final commit; see final response for branch head.

## Code Changes

- Added `--method interval-cutoff-oracle` with `--interval-exact-cutoff-oracle compact-mip`.
- Added fixed-Gini-interval compact cutoff constraints to the original compact MIP writer.
- Added oracle JSON fields for gamma range, cutoff, solver status, basis, LP/solution/log paths, timeout, infeasibility, and improving-solution status.
- Added conservative audit checks for interval oracle rows.
- Added `scripts/run_interval_cutoff_oracles.py` for per-leaf oracle runs.
- Added `scripts/merge_interval_oracle_results.py` for exact full-ledger leaf merge auditing.
- Added `scripts/summarize_v20_exact_certificate_round.py` for round summaries.

## Priority Target Outcome

`reference/hard_stress/V20_M3/high_imbalance_seed3202.txt` certified in the reproduced full-frontier run.

| row | status | objective | LB | UB | gap | runtime |
|---|---|---:|---:|---:|---:|---:|
| high_imbalance_seed3202_reproduced_baseline | optimal | 1.74931345205 | 1.74931345205 | 1.74931345205 | 0 | 409.831s |

Certificate basis:

- relaxation-only full-frontier ledger;
- `unresolved_intervals=0`;
- `invalid_bound_intervals=0`;
- `open_nodes=0`;
- `frontier_covers_all_improving_gini_values=true`;
- `frontier_range_certificate_scope=original_full_improving_range`;
- all final leaves are bound-fathomed by `inventory_route_gini_relaxation_fathomed`;
- no BPC tree interval was used, so exact pricing closure was not required;
- route-mask all-subset enumeration was not certifying.

Raw certificate:

- `results/v20_exact_certificate_round/raw/high_imbalance_seed3202_reproduced_baseline.json`
- `results/v20_exact_certificate_round/raw/high_imbalance_seed3202_reproduced_baseline.intervals.csv`
- copied certificate: `results/v20_exact_certificate_round/high_imbalance_seed3202_full_certificate.json`

## Interval Oracle Result

The new compact cutoff oracle was tested on old unresolved leaves from the previous noncertified ledger: `13,18,19,20`.

All four short diagnostic oracle runs timed out. They were not merged and do not contribute certificate evidence.

Files:

- `results/v20_exact_certificate_round/high_imbalance_seed3202_interval_oracle_results.csv`
- `results/v20_exact_certificate_round/ledger_merge_audit.csv`
- `results/v20_exact_certificate_round/high_imbalance_seed3202_merged_ledger.csv`

Merge audit conclusion for the old ledger: `certificate_incomplete`, `final_open_leaf_count=4`.

## V12 Stability

| row | status | objective | LB | UB | gap | runtime |
|---|---|---:|---:|---:|---:|---:|
| V4 smoke 30s | optimal | 0 | 0 | 0 | 0 | 0.931s |
| V12 M2 canonical 300s | optimal | 0.718504070755 | 0.718504070755 | 0.718504070755 | 0 | 207.544s |
| V12 M1 diagnostic 300s | not closed | 0.357200583208 | 0.332675660948 | 0.357200583208 | 0.0686586848205 | 300.366s |
| V12 M1 600s | optimal | 0.357200583208 | 0.357200583208 | 0.357200583208 | 0 | 473.494s |

## BPC Fallback

BPC interval fallback was not run in this round because the priority V20 instance certified before fallback was needed. It remains diagnostic unless exact pricing closes for every certificate node.

## Audit

Commands:

```powershell
D:\\msys64\\ucrt64\\bin\\python.exe scripts\audit_bpc_certificate.py --self-test
D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py results\v20_exact_certificate_round\raw --csv-out results\v20_exact_certificate_round\certificate_audit.csv --fail-on-error
build\ExactEBRP.exe --method certificate-basis-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --out results\v20_exact_certificate_round\raw\certificate_basis_test.json
build\ExactEBRP.exe --method option-consistency-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --out results\v20_exact_certificate_round\raw\option_consistency_test.json
```

Audit result: `audited_rows=12 failures=0`.

## Paper-Candidate Status

A V20 paper-candidate exact portfolio can now include the interval oracle as an optional certificate module, but the actual `high_imbalance_seed3202` certificate in this round did not require it. The canonical paper-core command remains unchanged. The next step should be a controlled V20/M3 mini-matrix to check whether the same relaxation-only full-frontier closure repeats on other hard stress rows before launching a broad benchmark table.

## Key Files

- `docs/exact_interval_cutoff_mip_oracle.md`
- `docs/focused_interval_ledger_merge.md`
- `docs/high_imbalance_seed3202_full_certificate_report.md`
- `results/v20_exact_certificate_round/high_imbalance_seed3202_certificate_attempt.csv`
- `results/v20_exact_certificate_round/high_imbalance_seed3202_interval_oracle_results.csv`
- `results/v20_exact_certificate_round/high_imbalance_seed3202_merged_ledger.csv`
- `results/v20_exact_certificate_round/interval_bpc_fallback_results.csv`
- `results/v20_exact_certificate_round/v12_stability_summary.csv`
- `results/v20_exact_certificate_round/certificate_audit.csv`
