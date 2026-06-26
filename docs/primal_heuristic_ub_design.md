# Primal Heuristic UB Design

## Scope

`paper-bpc-core` obtains its default initial upper bound from a reproducible,
verifier-gated primal heuristic. The primal phase can shrink the frontier
cutoff, but it never supplies lower-bound evidence.

## Why Archive Scanning Is Not Paper-Core

Scanning `results/` is useful for diagnostics, but it is not a reproducible
paper algorithm because the incumbent depends on local history, stale files,
and which route-bearing JSON files happen to be present. Archive rows remain
available only when explicitly requested with `--incumbent-archive-auto true`.
Such rows are labeled diagnostic and have
`incumbent_source_contributes_lower_bound=false`.

## Native HGA-TGBC Module

The production default is:

```powershell
--primal-heuristic hga-tgbc
--primal-heuristic-seed <seed>
--primal-heuristic-runs <runs>
--primal-heuristic-seconds <seconds>
```

The `hga-tgbc` implementation is now a native migration of the paper
HGA-TGBC core from the sibling `Hybrid GA` project. It preserves the production
algorithmic components used by `HybridGA_HGS`: route-set initialization, route
repair, TGBC compact decoding, route-inheritance crossover, ordered-separator
crossover, mutation, guided education, decode caching, and generation
stagnation control. Default crossover, mutation, population, elite, and
education rates are taken from the native implementation.

The ExactEBRP-specific adapter only maps instance data into the native HGA data
structures, invokes the native solver, converts the decoded operations back to
ExactEBRP `RoutePlan` objects, and verifier-gates the result.

## Excluded Artifacts

The migration does not import standalone HybridGA benchmark drivers, old debug
print controls, local experiment scripts, IDE files, or unrelated tuning loops.
A generation trace block is suppressed in the copied header so ExactEBRP runs
stay quiet; this does not alter the HGA state update or acceptance logic.

## Supported Modes

- `none`: no heuristic upper bound beyond the empty route fallback.
- `greedy`: deterministic BPC-owned greedy/local route plan.
- `hga-tgbc`: native HGA-TGBC only.
- `best-of-all`: native HGA-TGBC plus other verifier-gated ExactEBRP primal
  candidates, keeping the best verified route plan.

## Verifier Gating

Every candidate route plan is checked by the independent verifier before it can
update `upper_bound`. Verified exports include route order, pickup/drop
operations, depot unload convention through operations, final inventories,
objective components, instance hash, and heuristic settings.

Result JSON records:

- `incumbent_source_category=primal_heuristic`;
- `incumbent_source_is_paper_reproducible=true`;
- `incumbent_source_contributes_lower_bound=false`.

The output guard and Python audit reject any original-problem certificate that
marks a heuristic incumbent as lower-bound evidence.

## Reproducibility Example

```powershell
build\ExactEBRP.exe --method primal-heuristic `
  --algorithm-preset paper-bpc-core `
  --input reference\regen_candidate_V12_M2_average.txt `
  --lambda 0.15 --T 3600 `
  --primal-heuristic hga-tgbc `
  --primal-heuristic-seed 20260626 `
  --primal-heuristic-runs 24 `
  --primal-heuristic-seconds 60 `
  --export-incumbent results\incumbents\v12_m2_hga_tgbc.json `
  --out results\primal_heuristic_round\v12_m2_hga_tgbc.json
```

The exported incumbent can be reused explicitly with `--incumbent-json`; this
is paper-reproducible because the file is an input artifact rather than a scan
of an arbitrary local result archive.

## Native Migration Validation

The native migration round produced verifier-passed incumbents:

- V4 smoke: `0.000000000000`;
- regenerated V12 M1: `0.357200583208`;
- regenerated V12 M2: `0.718504070755`.

The V12 M2 paper-core 600-second observation run closed in about 60.35 seconds
with `objective=lower_bound=upper_bound=0.718504070755` and audit pass. The
certificate came from full-frontier relaxation bounds; the HGA-TGBC route plan
remained UB-only.
