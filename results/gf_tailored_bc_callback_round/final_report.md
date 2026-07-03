# Tailored BC Callback Round Final Report

Status label: `minimal_dynamic_callback_path_available`

## Callback Boundary

The executable loads `cplex2211.dll` dynamically, registers a generic CPLEX callback, and solves the smoke fixed-interval LP/MIP in-process. The smoke interval row reports relaxation/candidate/progress callback events, paper-safe relaxation-point separator attempts for Gini interval, visit-inventory, Gini subset-envelope, and low-Gini L1 centering rows, candidate compact route/service plus objective projection checks, and CPLEX branch-order priorities applied through `CPXcopyorder`.

## Evidence Generated

- `callback_smoke.csv` records callback availability.
- `tailored_cut_ablation.csv` records paper-safe static tailored cut guards.
- `tailored_bc_vs_static.csv` separates true callback BC from static fallback.
- `callback_event_summary.csv` records callback events from the fixed-interval smoke solve when callbacks are available.
- `tailored_branch_callback_smoke.csv` records a diagnostic-only CPLEX toy MIP branch-smoke row. It applies branch priorities, records relaxation/candidate callbacks, enters CPLEX branch context, and creates one-shot Gini branches through `CPXcallbackmakebranch`.
- `gini_branching_comparison.csv` now separates toy branch-smoke evidence from the moderate low-Gini hard-leaf diagnostic. In the hard-leaf row, `--tailored-bc-gini-branching auto` selects the branch-callback path and records branch-context calls plus one-shot Gini branches when CPLEX enters branch context.
- `interval_callback_separator_diagnostic.json` disables overlapping static tailored cut families and confirms that relaxation-point callback separators are invoked without using diagnostic evidence as a paper certificate.
- Candidate callbacks now run compact projection verifiers when route/service variables and `Y_i`, `r_i`, `e_i`, targets, weights, lambda, and cutoff data are available. The route projection verifier checks station disjointness, depot flow, station flow, service linking, duration under the pickup-only handling convention, final-inventory balance, and reconstructed route load order. The objective projection verifier recomputes ratios, penalty, Gini, and the objective from final inventories. Rejections use only already-valid model rows; unsupported route-load or Gini/objective mismatches are recorded instead of adding unsafe no-good cuts.
- `moderate_seed3301_low_gini1_callback_guarded.json` is a guarded full-preset hard-leaf diagnostic. If the full preset setup and solve exceed the outer wrapper timeout, the runner writes an honest noncertificate timeout JSON instead of leaving a missing artifact.
- `moderate_seed3301_low_gini1_callback_minimal_short3.json` is a diagnostic hard-leaf callback run with overlapping static diagnostic families disabled. It is included to preserve solver-final callback evidence on the moderate low-Gini leaf when the full-preset guarded row times out before producing callback counters.
- `hard_leaf_tailored_bc.csv` and `hard_leaf_comparison.csv` now include short no-branch, callback-Gini-branch, and selector fallback diagnostics for the two known moderate low-Gini leaves, plus matched 60s low-Gini-2 callback variants. These rows are diagnostic only; they test callback branch behavior and bound direction without changing paper certificate evidence.
- `exact_vs_cplex_callback_round.csv` now compares the current 60s low-Gini-2 callback rows against prior one-thread plain fixed-interval and static compact-BC baselines from `gf_compact_bc_lowgini_round`. The callback tailored rows improve the 60s low-Gini-2 lower bound over those baselines but still do not close the leaf.
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

This package now contains a minimal CPLEX-managed callback path for fixed-interval compact models, including user-cut callback plumbing, relaxation-point separation for Gini interval, visit-inventory, Gini subset-envelope, and low-Gini L1 centering rows, candidate compact route/service and final-inventory objective projection validation, branch-order priority injection, diagnostic branch-context evidence with one-shot Gini branches in the toy branch smoke, and diagnostic hard-leaf evidence where moderate low-Gini intervals enter branch context and create Gini branches through `CPXcallbackmakebranch`. Short branch-mode ablations now compare no-branch, callback-Gini-branch, and selector fallback behavior on the two known moderate low-Gini leaves. The 60s low-Gini-2 callback-tailored rows improve the lower bound over prior one-thread plain fixed-interval and static compact-BC baselines, but they do not close the leaf and the improvement is not uniquely attributable to custom Gini branching because off/selector callback variants reach the same bound in this short run. It is not yet the full requested tailored branch-and-cut: full-preset hard-leaf callback ablations, longer matched hard-leaf comparisons, and hard-leaf closure evidence remain incomplete.

Final commit SHA: recorded in the final assistant response after commit creation.
