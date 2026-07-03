# Tailored BC Callback Round Final Report

Status label: `minimal_dynamic_callback_path_available`

## Callback Boundary

The executable loads `cplex2211.dll` dynamically, registers a generic CPLEX callback, and solves the smoke fixed-interval LP/MIP in-process. The smoke interval row reports relaxation/candidate/progress callback events, paper-safe relaxation-point separator attempts for Gini interval, visit-inventory, Gini subset-envelope, and low-Gini L1 centering rows, candidate interval-consistency checks, and CPLEX branch-order priorities applied through `CPXcopyorder`.

## Evidence Generated

- `callback_smoke.csv` records callback availability.
- `tailored_cut_ablation.csv` records paper-safe static tailored cut guards.
- `tailored_bc_vs_static.csv` separates true callback BC from static fallback.
- `callback_event_summary.csv` records callback events from the fixed-interval smoke solve when callbacks are available.
- `interval_callback_separator_diagnostic.json` disables overlapping static tailored cut families and confirms that relaxation-point callback separators are invoked without using diagnostic evidence as a paper certificate.
- `moderate_seed3301_low_gini1_callback_guarded.json` is a guarded hard-leaf diagnostic. If the in-process CPLEX callback path exceeds the outer wrapper timeout, the runner writes an honest noncertificate timeout JSON instead of leaving a missing artifact.
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

This package now contains a minimal CPLEX-managed callback path for fixed-interval compact models, including user-cut callback plumbing, relaxation-point separation for Gini interval, visit-inventory, Gini subset-envelope, and low-Gini L1 centering rows, candidate interval-consistency validation, and branch-order priority injection. It is not yet the full requested tailored branch-and-cut: verifier-backed lazy incumbent rejection, custom Gini branch creation on hard leaves, hard-leaf callback ablations, and performance-positive hard-leaf evidence remain incomplete.

Final commit SHA: recorded in the final assistant response after commit creation.
