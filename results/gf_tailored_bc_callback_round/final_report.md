# Tailored BC Callback Round Final Report

Status label: `minimal_dynamic_callback_path_available`

## Callback Boundary

The executable loads `cplex2211.dll` dynamically, registers a generic CPLEX callback, and solves the smoke fixed-interval LP/MIP in-process. The smoke interval row reports relaxation/candidate/progress callback events, paper-safe relaxation-point separator attempts for Gini interval, visit-inventory, Gini subset-envelope, low-Gini L1 centering, basic transfer-cutset, and pair/triple support-duration cover rows, candidate compact route/service plus objective projection checks, and CPLEX branch-order priorities applied through `CPXcopyorder`.

## Evidence Generated

- `callback_smoke.csv` records callback availability.
- `tailored_cut_ablation.csv` records paper-safe static tailored cut guards.
- `tailored_bc_vs_static.csv` separates true callback BC from static fallback.
- `callback_event_summary.csv` records callback events from the fixed-interval smoke solve when callbacks are available.
- `callback_activity_summary.csv` now reports basic transfer-cutset and support-duration callback candidates, violations, and cuts. In this package the transfer and support-duration separators were exercised on callback rows; support-duration candidates mean evaluated high-support pair/triple subsets, while violations/cuts require a route-duration-infeasible cover that is violated by the relaxation point.
- `tailored_branch_callback_smoke.csv` records a diagnostic-only CPLEX toy MIP branch-smoke row. It applies branch priorities, records relaxation/candidate callbacks, enters CPLEX branch context, and creates one-shot Gini branches through `CPXcallbackmakebranch`.
- `gini_branching_comparison.csv` now separates toy branch-smoke evidence from the moderate low-Gini hard-leaf diagnostic. In the hard-leaf row, `--tailored-bc-gini-branching auto` selects the branch-callback path and records branch-context calls plus one-shot Gini branches when CPLEX enters branch context.
- `interval_callback_separator_diagnostic.json` disables overlapping static tailored cut families and confirms that relaxation-point callback separators are invoked without using diagnostic evidence as a paper certificate.
- Candidate callbacks now run compact projection verifiers when route/service variables and `Y_i`, `r_i`, `e_i`, targets, weights, lambda, and cutoff data are available. The route projection verifier checks station disjointness, depot flow, station flow, service linking, duration under the pickup-only handling convention, final-inventory balance, and reconstructed route load order. The objective projection verifier recomputes ratios, penalty, Gini, and the objective from final inventories. Rejections use only already-valid model rows; unsupported route-load or Gini/objective mismatches are recorded instead of adding unsafe no-good cuts.
- `moderate_seed3301_low_gini1_callback_guarded.json` is a guarded full-preset hard-leaf diagnostic. If the full preset setup and solve exceed the outer wrapper timeout, the runner writes an honest noncertificate timeout JSON instead of leaving a missing artifact.
- `moderate_seed3301_low_gini1_callback_minimal_short3.json` is a diagnostic hard-leaf callback run with overlapping static diagnostic families disabled. It is included to preserve solver-final callback evidence on the moderate low-Gini leaf when the full-preset guarded row times out before producing callback counters.
- `hard_leaf_tailored_bc.csv` and `hard_leaf_comparison.csv` now include short no-branch, callback-Gini-branch, and selector fallback diagnostics for the two known moderate low-Gini leaves, plus longer 60s/300s/1200s callback variants. These rows are diagnostic only; they test callback branch behavior and bound direction without changing paper certificate evidence.
- `exact_vs_cplex_callback_round.csv` now compares the current 60s/300s/1200s moderate low-Gini callback rows against prior one-thread plain fixed-interval and static compact-BC baselines from `gf_compact_bc_lowgini_round`. The callback tailored rows improve low-Gini hard-leaf lower bounds over those baselines in several matched settings; the low-Gini-2 300s callback-Gini diagnostic closes that fixed interval by integer infeasibility.
- `full_row_confirmation_summary.csv` records one-thread `paper-gf-tailored-bc` preservation rows for V12 M1, V12 M2, `tight_T_seed3101`, and `high_imbalance_seed3202`, in addition to the smoke full-row. In this package V12 M2, `tight_T_seed3101`, and `high_imbalance_seed3202` certify. V12 M1 now has both 300s and 1200s noncertified parent frontier JSONs before optional post-solve interval closure; the 1200s row improves LB/gap to `0.353171916148` / `0.0112784447991` and is not a wrapper-synthesized zero-bound artifact.
- `generated_hard_diagnostic_summary.csv`, `generated_hard_leaf_callback_summary.csv`, and `generated_hard_instance_effectiveness.csv` now record guarded one-thread callback probes for the deterministic generated hard-diagnostic instances under `reference/hard_compact_bc_diagnostics/`. Parent full-row summaries aggregate child `auto_oracle/interval_*.json` callback evidence so generated hard-instance effectiveness is not undercounted. These rows are diagnostic only; wrapper timeouts are preserved as noncertificate JSON rather than being treated as failures to emit artifacts.
- `source_classification.csv` preserves tailored source classes per JSON row.

## Audit

`audit_tailored_bc_callback_round.py` return code: 0.

Additional audits run after package generation:

- `audit_bpc_certificate.py --self-test`: passed.
- `audit_bpc_certificate.py results\gf_tailored_bc_callback_round\raw --fail-on-error`: passed.
- `audit_tailored_bc_callback_round.py`: passed.
- `audit_gf_compact_bc_summary.py`: passed.
- `audit_thread_fairness.py`: passed.
- `audit_certificate_sources.py`: passed.
- `audit_timeprofile_finalization.py`: passed.
- `audit_objective_convention.py`: passed.
- `audit_no_instance_special_cases.py`: passed.

Build command used:

```powershell
D:\msys64\ucrt64\bin\g++.exe -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src\main.cpp src\Parser.cpp src\Evaluator.cpp src\Result.cpp src\Bounds.cpp src\ColumnPool.cpp src\TailoredExact.cpp src\Pricing.cpp src\Cuts.cpp src\Branching.cpp src\Master.cpp src\ColumnGeneration.cpp src\CplexBaseline.cpp src\TailoredBC.cpp src\TailoredBCCuts.cpp src\TailoredBCCallbacks.cpp src\TailoredBCCplexApi.cpp src\GiniBranching.cpp src\hga_tgbc\HgaTgbcGreedy.cpp src\HgaTgbcRunner.cpp src\Logger.cpp -o build\ExactEBRP.exe
```

## Paper Claim

This package now contains a minimal CPLEX-managed callback path for fixed-interval compact models, including user-cut callback plumbing, relaxation-point separation for Gini interval, visit-inventory, Gini subset-envelope, low-Gini L1 centering, basic transfer-cutset, and pair/triple support-duration cover rows, candidate compact route/service and final-inventory objective projection validation, branch-order priority injection, diagnostic branch-context evidence with one-shot Gini branches in the toy branch smoke, and diagnostic hard-leaf evidence where moderate low-Gini intervals enter branch context and create Gini branches through `CPXcallbackmakebranch`. Branch-mode ablations now compare no-branch, callback-Gini-branch, and selector fallback behavior on the two known moderate low-Gini leaves, including longer 60s/300s/1200s diagnostic rows. The generated hard-diagnostic package now aggregates callback evidence from child fixed-interval `auto_oracle` solves. The low-Gini-2 callback-Gini row closes the fixed interval at 300s by integer infeasibility, and the low-Gini-1 callback-Gini rows now provide 60s/300s/1200s bound trajectory evidence against one-thread plain fixed-interval and static compact-BC baselines. The V20 control rows `tight_T_seed3101` and `high_imbalance_seed3202` certify under one-thread `paper-gf-tailored-bc`; V12 M2 also certifies. V12 M1 remains noncertified, but the added 1200s row preserves a solver-written pre-auto-oracle parent ledger with LB `0.353171916148`, gap `0.0112784447991`, and four unresolved intervals, improving over the 300s tailored row instead of falling back to a wrapper failure. This is hard-leaf callback evidence, but it is diagnostic-only and not a paper-core certificate. It is not yet the full requested tailored branch-and-cut: V12 M1 closure, full-preset hard-leaf callback ablations, longer matched hard-leaf comparisons beyond this focused low-Gini increment, and broader hard-leaf closure evidence remain incomplete.

Final commit SHA: recorded in the final assistant response after the report commit is pushed.
