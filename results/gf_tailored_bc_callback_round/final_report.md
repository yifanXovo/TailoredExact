# Tailored BC Callback Round Final Report

Status label: `callback_unavailable_static_fallback_only`

## Callback Boundary

FAILED GOAL: remained static CPLEX-backed compact MIP; not a true tailored branch-and-cut callback implementation.

Callback blocker: callback_unavailable: current ExactEBRP CPLEX integration writes LP files and invokes cplex.exe command files; the executable is built with the repository MinGW/g++ path and is not linked against the CPLEX Concert/C API. headers_found=true, c_api_headers_found=true, msvc_env_available=false. Rows using paper-gf-tailored-bc are therefore labelled static_fallback unless a future MSVC/CPLEX-linked callback target is added.

## Evidence Generated

- `callback_smoke.csv` records callback availability.
- `tailored_cut_ablation.csv` records paper-safe static tailored cut guards.
- `tailored_bc_vs_static.csv` separates true callback BC from static fallback.
- `callback_event_summary.csv` has zero callback events when callbacks are unavailable.
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
D:\msys64\ucrt64\bin\g++.exe -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src\main.cpp src\Parser.cpp src\Evaluator.cpp src\Result.cpp src\Bounds.cpp src\ColumnPool.cpp src\TailoredExact.cpp src\Pricing.cpp src\Cuts.cpp src\Branching.cpp src\Master.cpp src\ColumnGeneration.cpp src\CplexBaseline.cpp src\TailoredBC.cpp src\TailoredBCCuts.cpp src\TailoredBCCallbacks.cpp src\GiniBranching.cpp src\hga_tgbc\HgaTgbcGreedy.cpp src\HgaTgbcRunner.cpp src\Logger.cpp -o build\ExactEBRP.exe
```

The user-specified remote head was `b65fb2e1cece2c70980eeb91aadfee07ac2591b8`, but `origin/codex/longrun-round17-local-results` resolved to `cb11b9f5f477b707511388b0196f0864c75d1fbb` at fetch time; the requested SHA was not present in the fetched branch.

## Paper Claim

This package does not support a new paper claim of CPLEX-managed tailored branch-and-cut callbacks. The implemented static cut rows may remain diagnostic or compact-BC strengthening, but they are not callback evidence.

Final commit SHA: recorded in the final assistant response after commit creation.
