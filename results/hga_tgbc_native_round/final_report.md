# Native HGA-TGBC Migration Final Report

## Scope

This round replaces the earlier simplified HGA-style path with a native
HGA-TGBC migration. The `--primal-heuristic hga-tgbc` mode now runs only the
migrated native HGA-TGBC stack and accepts only verifier-passed complete route
plans as upper bounds.

## Code Changes

- Added isolated native HGA-TGBC headers under `include/hga_tgbc/`.
- Added native greedy/TGBC decoder implementation under `src/hga_tgbc/`.
- Added `HgaTgbcRunner` as the ExactEBRP adapter and verifier gate.
- Wired native HGA-TGBC into `runPaperPrimalHeuristic`.
- Kept arbitrary result-directory archive scanning disabled by default for
  `paper-bpc-core`.
- Removed the previous `results/tgbc_migration_round` intermediate artifacts
  from the tracked branch because they came from the non-faithful derivative
  path and are superseded by this native migration round.

The adapter does not use heuristic evidence as a lower bound. It only produces
verified upper-bound route plans.

## Build

`cmake` was not available on this local machine. The fallback C++17 command in
`commands.md` compiled successfully with warnings only in the copied native HGA
code.

## Validation

Certificate audit self-test passed. The audit over
`results/hga_tgbc_native_round/raw` reported four rows and zero failures.

| Instance / run | Result |
| --- | --- |
| V4 native HGA-TGBC | UB 0.000000000000, verifier passed |
| V12 M1 native HGA-TGBC | UB 0.357200583208, verifier passed |
| V12 M2 native HGA-TGBC | UB 0.718504070755, verifier passed |
| V12 M2 paper-core 600s | certified optimum 0.718504070755 in about 60.35s |

The V12 M2 paper-core observation did not require BPC-tree UB improvement:
native HGA-TGBC already produced a UB strong enough for the relaxation portfolio
to close the full improving Gini frontier. Pricing time was zero and the final
certificate was relaxation-only with `unresolved_intervals=0`,
`invalid_bound_intervals=0`, and `open_nodes=0`.

## Legality Checks

Every accepted native HGA route plan passed the independent ExactEBRP verifier.
No non-verified HGA candidate is allowed to update UB. HGA/TGBC incumbents
remain UB-only and are marked with
`incumbent_source_contributes_lower_bound=false`.

## Remaining Work

The native HGA-TGBC path should now be kept fixed while running broader
generated-variant benchmarks. If a future instance remains noncertified, the
next diagnosis should first determine whether the blocker is UB quality or
relaxation-bound strength before changing BPC search logic.
