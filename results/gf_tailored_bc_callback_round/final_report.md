# Tailored BC Callback Round Final Report

Status label: `minimal_dynamic_callback_path_available`

## Callback Boundary

The executable loads `cplex2211.dll` dynamically, registers a generic CPLEX callback, and solves the smoke fixed-interval LP/MIP in-process. The smoke interval row reports relaxation/candidate/progress callback events, one redundant paper-safe user cut, candidate interval-consistency checks, and CPLEX branch-order priorities applied through `CPXcopyorder`.

## Evidence Generated

- `callback_smoke.csv` records callback availability.
- `tailored_cut_ablation.csv` records paper-safe static tailored cut guards.
- `tailored_bc_vs_static.csv` separates true callback BC from static fallback.
- `callback_event_summary.csv` records callback events from the fixed-interval smoke solve when callbacks are available.
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

The user-specified remote head was `b65fb2e1cece2c70980eeb91aadfee07ac2591b8`, but `origin/codex/longrun-round17-local-results` resolved to `cb11b9f5f477b707511388b0196f0864c75d1fbb` at fetch time; the requested SHA was not present in the fetched branch.

## Paper Claim

This package now contains a minimal CPLEX-managed callback path for fixed-interval compact models, including user-cut callback plumbing, candidate interval-consistency validation, and branch-order priority injection. It is not yet the full requested tailored branch-and-cut: verifier-backed lazy incumbent rejection, custom Gini branch creation on hard leaves, hard-leaf callback ablations, and performance-positive hard-leaf evidence remain incomplete.

Final commit SHA: recorded in the final assistant response after commit creation.
