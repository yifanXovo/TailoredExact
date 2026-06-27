# Primal Heuristic Gap Audit

This round replaces the earlier HGA-inspired derivative with a native
HGA-TGBC migration from the sibling `Hybrid GA` implementation.

## Current Architecture

`paper-bpc-core` still disables arbitrary result-directory archive scanning by
default. The default paper UB source is the deterministic, verifier-gated
`--primal-heuristic hga-tgbc` path.

The `hga-tgbc` mode now runs the migrated native HGA-TGBC stack through
`runHgaTgbcNative`:

- route-set population initialization and route repair;
- TGBC compact full and incremental route-load decoders;
- decode cache;
- route-inheritance crossover;
- ordered-separator crossover;
- mutation;
- guided education using decoded route information;
- stagnation-controlled generations;
- zero-operation compaction through the native compact decoder.

The adapter converts ExactEBRP instances into the native HGA data structures,
runs the native algorithm with the default production rates from HybridGA, then
converts the decoded operations back into ExactEBRP route plans. A candidate can
update the UB only after the independent ExactEBRP verifier accepts the complete
route plan.

## Migration Scope

Migrated production-relevant files:

- `HybridGA.h`;
- `newGreedy.cpp`;
- `GreedyMethods.h`;
- `GreedyExtensions.h`;
- `AVLCalculator.h`;
- `Solvers.h`;
- `InstanceData.h`.

The migration intentionally excludes standalone benchmark loops, old debug
drivers, local IDE files, and obsolete experiment scaffolding. One native
generation-trace print block is suppressed in the copied header; this changes
only console output, not algorithm state transitions.

## Objective And Legality Audit

The native HGA candidate is rejected unless `verifySolution` passes. The V4,
V12 M1, and V12 M2 migrated-HGA incumbents produced in this round all pass the
verifier and are exported as complete route plans.

The earlier objective-log concern is not present in the native path used by
`hga-tgbc`: the ExactEBRP bridge records only verifier-passed complete decoded
solutions, and the best candidate is selected by true objective after
verification. Diagnostic intermediate native population events are not used as
accepted ExactEBRP incumbents.

## UB Results

Using seed `20260626`, `--primal-heuristic-runs 24`, and a 60-second heuristic
budget:

| Instance | Native HGA-TGBC UB | Verifier | Notes |
| --- | ---: | --- | --- |
| V4 smoke | 0.000000000000 | passed | exact zero smoke incumbent |
| regenerated V12 M1 | 0.357200583208 | passed | matches the known good UB |
| regenerated V12 M2 | 0.718504070755 | passed | improves the prior diagnostic archive UB 0.719065249476 |

## BPC Observation

The V12 M2 paper-core observation run used the native HGA-TGBC incumbent and a
600-second limit. It terminated in about 60.35 seconds with:

- `certified_original_problem=true`;
- `objective=lower_bound=upper_bound=0.718504070755`;
- `unresolved_intervals=0`;
- `invalid_bound_intervals=0`;
- `open_nodes=0`;
- `pricing_time_seconds=0`.

The UB did not need BPC-tree improvement in this run because the migrated HGA
candidate was already strong enough for the vehicle-indexed relaxation
portfolio to close the full improving Gini frontier. This is a relaxation-only
frontier certificate, not heuristic lower-bound evidence.

## Remaining Check

The next broad benchmark should keep the native HGA path fixed and test whether
larger regenerated variants retain verifier-passed incumbents and certificate
closure. If a future instance does not close, the progress logs should separate
UB weakness from relaxation-bound weakness before changing BPC logic.
