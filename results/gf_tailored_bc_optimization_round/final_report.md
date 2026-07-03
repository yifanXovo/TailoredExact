# GF Tailored BC Optimization Round Final Report

Status: `partial_optimization_with_hard_leaf_finalization_blocker`

## Baseline Fair Benchmark

- baseline_smoke_v4_m1_tailored_60s: paper_gf_tailored_bc status=optimal certified=true LB=0 UB=0 gap=0 wall=1.371s
- baseline_smoke_v4_m1_plain_cplex_60s: plain_cplex_benchmark status=optimal benchmark_optimal=true LB=0 UB=0 gap=0 wall=0.121s
- baseline_v12_m1_avg_tailored_300s: paper_gf_tailored_bc status=gcap_frontier_not_closed certified=false LB=0.34856314104 UB=0.357200583208 gap=0.0241809296353 wall=420.029s
- baseline_v12_m1_avg_plain_cplex_300s: plain_cplex_benchmark status=optimal benchmark_optimal=true LB=0.357200583208 UB=0.357200583208 gap=0 wall=185.712s
- baseline_v12_m2_avg_tailored_300s: paper_gf_tailored_bc status=optimal certified=true LB=0.718504070755 UB=0.718504070755 gap=0 wall=292.374s
- baseline_v12_m2_avg_plain_cplex_300s: plain_cplex_benchmark status=not_certified certified=false LB=0.62337314027 UB=0.719065249476 gap=0.133078478311 wall=300.139s
- baseline_diag_v12_m1_low_gini_tailored_300s: paper_gf_tailored_bc status=native_exit_noncertified certified=false LB=0.0 UB=0.0 gap=1.0 wall=41.235s
- baseline_diag_v12_m1_low_gini_plain_cplex_300s: plain_cplex_benchmark status=optimal benchmark_optimal=true LB=0.0280241198263 UB=0.0280241198263 gap=0 wall=22.831s

Plain CPLEX rows are benchmark-only in the raw evidence package. They retain their benchmark optimality metadata, but `certified_original_problem=false` so they cannot be imported as paper-core Tailored-BC certificates.

## Code Changes

- Added option-aware, deviation-ranked Gini subset-envelope callback separation. The separator now uses `--tailored-bc-gini-subset-max-size` and `--tailored-bc-gini-subset-max-cuts`, prioritizes high LP ratio deviations, and records max envelope violation from callback rows.
- Preserved the same paper-safe subset-envelope inequalities; only separation order and throttling changed.

## Paper-Safe vs Diagnostic

- Paper-safe: fixed Gini interval cap, visit/final-inventory linking, Gini subset-envelope cuts, low-Gini L1 centering, variable-S centering, basic transfer cutset, lifted support-duration covers, S*P estimator already proved in prior docs.
- Diagnostic-only: Benders-like transfer-network inventory cuts, compatibility-filtered transfer network cuts, S-bucket refinement without exact full S coverage, generated hard probes, forced hard fixed-interval leaves.

## Hard Low-Gini and Hard-Leaf Results

All 60s hard fixed-interval rows in this round wrote honest noncertified wrapper/native-exit artifacts. This means the immediate blocker is fixed-interval hard-leaf finalization/time-limit behavior under these configurations, not a demonstrated bound improvement.
- generated_diag_v12_m2_tight_cutoff / callback_auto_gini_branch: status=native_exit_noncertified LB=0.0 UB=1.65777317757 gap=1.0
- generated_diag_v12_m2_tight_cutoff / callback_no_gini_branch: status=wrapper_timeout_noncertified LB=0.0 UB=1.65777317757 gap=1.0
- generated_diag_v12_m2_tight_cutoff / callback_selector_gini_branch: status=native_exit_noncertified LB=0.0 UB=1.65777317757 gap=1.0
- generated_diag_v12_m2_tight_cutoff / plain_fixed_interval_mip: status=wrapper_timeout_noncertified LB=0.0 UB=1.65777317757 gap=1.0
- generated_diag_v12_m2_tight_cutoff / static_tailored_safe: status=wrapper_timeout_noncertified LB=0.0 UB=1.65777317757 gap=1.0
- high_imbalance_seed3201_hard / callback_auto_gini_branch: status=wrapper_timeout_noncertified LB=0.0 UB=2.44340319194 gap=1.0
- high_imbalance_seed3201_hard / callback_no_gini_branch: status=wrapper_timeout_noncertified LB=0.0 UB=2.44340319194 gap=1.0
- high_imbalance_seed3201_hard / callback_selector_gini_branch: status=wrapper_timeout_noncertified LB=0.0 UB=2.44340319194 gap=1.0
- high_imbalance_seed3201_hard / plain_fixed_interval_mip: status=wrapper_timeout_noncertified LB=0.0 UB=2.44340319194 gap=1.0
- high_imbalance_seed3201_hard / static_tailored_safe: status=wrapper_timeout_noncertified LB=0.0 UB=2.44340319194 gap=1.0

## Gini Split / Branching Policies

Compared diagnostic policies: static/no-callback, callback with Gini branching off, callback auto branch callback, selector branch mode, and existing outer-controller ledger design. No hard fixed-interval policy produced final bound evidence in this round because the rows did not finalize under the wrapper caps. The existing outer-controller remains the only certificate-capable split design when full child coverage is audited.

## Transfer-Network / Benders-Like Cut Status

No Benders-like transfer-network cut was promoted. Basic transfer cutset validity test passed, but the stronger network cut remains diagnostic-only until the full proof and no-false-rejection audit are complete.

## Control Reproduction

- control_v12_m2_tailored_300s_rerun: status=optimal certified=true LB=0.718504070755 UB=0.718504070755 gap=0
- control_tight_T_seed3101_tailored_300s: status=optimal certified=True LB=0.107252734134 UB=0.107252734134 gap=0
- control_high_imbalance_seed3202_tailored_1200s: status=optimal certified=True LB=1.74931345205 UB=1.74931345205 gap=0

## Fair Post-Optimization Benchmark

Small-instance post-change comparison is represented by the final runtime comparison CSV, combining Phase 0 baseline and post-change control reruns. `tight_T_seed3101`, `high_imbalance_seed3202`, and rerun V12 M2 certify under one-thread settings. V12 M1 remains documented as noncertified at 300s in this round, with prior package post-merge evidence preserved outside this round.

## Regressions / Limitations

- One V12 M2 post-change attempt native-exited, but an immediate rerun certified at the same 300s one-thread setting.
- Hard fixed-interval diagnostics repeatedly failed to produce solver-final JSON under short caps; wrapper JSONs prevent false certificates but do not provide useful LB trajectory.
- The ranked Gini subset separator is implemented and tested, but hard-leaf rows did not finalize enough to demonstrate bound movement.

## Remaining Bottlenecks

1. Make fixed-interval hard-leaf solves respect internal time caps and emit partial valid bounds.
2. Add in-process progress/best-bound checkpointing for interval callback solves.
3. Re-run hard-leaf split policies once finalization is reliable.
4. Keep Benders-like transfer-network cuts diagnostic until proof and no-false-rejection tests are complete.

## Audit Status

- Build command completed successfully with existing warnings only.
- `audit_bpc_certificate.py --self-test`: passed.
- `audit_bpc_certificate.py results/gf_tailored_bc_optimization_round/raw --fail-on-error`: passed, 47 rows audited.
- `certificate-basis-test` and `option-consistency-test`: passed with the smoke input required by this build.
- `audit_tailored_bc_callback_round.py`: passed, 47 rows audited.
- `audit_gf_compact_bc_summary.py`: passed, 47 rows audited.
- `audit_thread_fairness.py`: passed, 47 rows audited.
- `audit_objective_convention.py`: passed, 47 rows audited.
- `audit_timeprofile_finalization.py`: passed, 12 frontier/benchmark rows audited.
- `audit_no_instance_special_cases.py`: passed.
- `audit_certificate_sources.py`: completed with zero recognized rows for this tailored-BC result layout; source classification for this round is therefore reported through `final_source_classification.csv` and the tailored callback audit.

Exact commit SHA: recorded in the final Codex response after push.
