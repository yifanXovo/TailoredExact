# LP Pattern and Long-Run Plain Benchmark Final Report

Status label: `dominant_bucket_open_tailored_bc_beats_plain_new_cuts_not_selected`.

## Dominant Bucket Results

Target: `moderate_seed3301`, G interval `[0.0122881381662, 0.0245762763324]`, dominant S bucket `[16.59546103547, 23.272821182835]`, cutoff `0.0491525526647`.

| row | budget | LB | gap to cutoff | nodes | role |
|---|---:|---:|---:|---:|---|
| plain fixed-interval MIP | 10800 | 0.048310474908 | 0.0008420777566999979 | 459291 | benchmark-only |
| plain telemetry-only | 10800 | 0.0484679856754 | 0.0006845669893000006 | 571329 | benchmark diagnostic only |
| static tailored compact BC | 10800 | 0.049002141816 | 0.00015041084869999582 | 607618 | paper-safe fixed interval subproblem |
| current best tailored | 10800 | 0.0488918805666 | 0.00026067209809999686 | 477661 | paper-safe fixed interval subproblem |
| all new paper-safe cuts | 10800 | 0.0487820084447 | 0.0003705442199999978 | 242085 | paper-safe fixed interval subproblem |

## Required Answers

1. Did plain CPLEX catch up to or surpass Tailored-BC at 10800s? No. Pure plain reached LB `0.048310474908`; best tailored reached `0.049002141816`.
2. Did plain CPLEX show late-stage acceleration? No decisive acceleration. Pure plain improved from `0.048035857993` at 1200s/3600s to `0.048310474908` at 10800s, still far below tailored 3600s.
3. Did telemetry-only callback distort plain CPLEX behavior? Yes. Telemetry-only LB was `0.0484679856754`, delta `0.0001575107673999973` over pure plain, so it remains benchmark diagnostic only.
4. Were LP/fractional snapshots exported? Diagnostic checkpoint snapshots were exported under `lp_snapshots/`. Exact best-bound-node relaxation vectors were not available through the current callback path; missing S/P/H/G and fractional variable values are explicitly labelled `not_exposed_by_current_cplex_callback`, not zero-filled.
5. What does nearest-relaxation pattern show? Bound and node trajectories are available, but S/P/H/G and estimator slacks cannot yet be reconstructed at best-bound nodes. The next API target is real relaxation-point extraction tied to the best-bound checkpoint.
6. Did bucket integer inventory domain tightening help? It is paper-safe and audited, but on the dominant bucket it reduced nodes while weakening or tying the bound: 3600s LB `0.0487233640003` vs static `0.0487638722254`; 10800s all-new LB `0.0487820084447`.
7. Did required movement / required visit cuts help? They are paper-safe and audited. They tied the best 1200s/3600s bounds and slightly reduced nodes in the combined 3600s row, but did not close the bucket.
8. Did the S-P-H coupled estimator help? It is implemented as paper-safe with bucket-local McCormick rows and audited. It tied the best 1200s/3600s bounds, but did not improve the 10800s dominant result beyond static tailored.
9. Which mechanism improved the dominant bucket most? Existing static tailored compact BC remains strongest at 10800s. Among new mechanisms, required movement/visit is neutral-to-slightly helpful in node count; integer-domain alone is not beneficial on this dominant bucket.
10. Did exact H semantics remain valid? Yes. The paper-safe H cap is retained; H lower/spread-cap semantics remain diagnostic. See `exact_H_semantics_audit.csv`.
11. Did the dominant bucket close? No. Best LB `0.049002141816` leaves gap `0.00015041084869999582`.
12. Did the adaptive child close or improve? It did not close, but improved materially: all-new adaptive child reached `0.0487233640003` at 1200s/3600s versus plain `0.048147514854` at 3600s.
13. Did secondary hard leaves regress? Mixed. `high_imbalance_seed3201_hard` and `tight_T_seed3102_hard` improved strongly; `low_gini_2` improved slightly; `moderate_seed3302_hard` regressed versus plain at 300s.
- `high_imbalance_seed3201_hard`: improved; plain LB `2.1614881406`, best tailored LB `2.27668699832` via `all_new_paper_safe_cuts`.
- `low_gini_2`: improved; plain LB `0.048894652654`, best tailored LB `0.0489209015481` via `current_best_new_combined_paper_safe`.
- `moderate_seed3302_hard`: regressed; plain LB `0.14433282147`, best tailored LB `0.142568520966` via `current_best_new_combined_paper_safe`.
- `tight_T_seed3102_hard`: improved; plain LB `0.31243853008`, best tailored LB `0.517898731718` via `all_new_paper_safe_cuts`.
14. Was a full convergence benchmark triggered? No. The dominant bucket is open, gap is not below `1e-5`, the new all-safe 10800s LB did not improve over the prior best, and the best result came from the static baseline rather than the new mechanism.
15. If yes, how did certified runtime compare? Not applicable; no full convergence benchmark was triggered and no full-ledger certificate was claimed.
16. Are there paper-core contamination risks? No detected contamination. Plain and telemetry rows are marked benchmark/diagnostic only; BPC, archive, known-UB, focus-only, route-mask, and external-incumbent evidence are excluded by the paper-strict and certificate audits.
17. Recommended next step: preserve static tailored as the selected dominant-bucket configuration, keep bucket-required movement as safe but optional, and target a new low-Gini denominator/root-bound mechanism plus true relaxation-vector extraction before another full convergence attempt.

## Trigger Decision

`full_convergence_comparison.csv` records `triggered=False`. Static tailored improved late and is close, but the new paper-safe combined row was weaker (`0.0487820084447`), so projection to full convergence under 21600s is not reliable enough to launch the full benchmark matrix.

## Audit Summary

- `certificate_audit.csv`: 65 rows, 0 failures
- `paper_strict_algorithm_audit.csv`: 169 rows, 0 failures
- `bucket_integer_inventory_domain_audit.csv`: 65 rows, 0 failures
- `bucket_required_movement_audit.csv`: 65 rows, 0 failures
- `lp_snapshot_integrity_audit.csv`: 116 rows, 0 failures
- `summary_cleanup_audit.csv`: 65 rows, 0 failures
- `thread_fairness_audit.csv`: 65 rows, 0 failures
- `objective_convention_audit.csv`: 65 rows, 0 failures
- `timeprofile_finalization_audit.csv`: 54 rows, 0 failures
- `s_bucket_coverage_audit.csv`: 40 rows, 0 failures
- `s_bucket_ledger_merge_audit.csv`: 40 rows, 0 failures
- `low_gini_cut_validity_audit.csv`: 39 rows, 0 failures
- `transfer_cut_validity_audit.csv`: 1 rows, 0 failures
- `bucket_ratio_domain_tightening_audit.csv`: 65 rows, 0 failures
- `model_identity_audit.csv`: 52 rows, 0 failures
- `plateau_bound_trace_audit.csv`: 3013 rows, 0 failures

## Output Package

Primary outputs are in `results/gf_tailored_bc_lp_pattern_strengthening_round/`: raw JSON, logs, progress traces, LP exports, snapshot CSVs, longrun summaries, secondary regressions, and audit CSVs.
