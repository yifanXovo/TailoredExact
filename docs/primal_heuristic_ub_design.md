# Primal Heuristic UB Design

## Scope

`paper-bpc-core` now obtains its default initial upper bound from a
deterministic, verifier-gated primal heuristic rather than by scanning prior
result directories. The heuristic is a primal phase only: it can shrink the
frontier cutoff, but it never supplies lower-bound evidence.

## Why Archive Scanning Is Not Paper-Core

Scanning `results/` is useful for diagnostics, but it is not a reproducible
paper algorithm because the answer depends on local history, stale files, and
which route-bearing JSON files happen to be present. Archive rows remain
available only when explicitly requested with `--incumbent-archive-auto true`.
Such rows are labeled with `incumbent_source_category=diagnostic_archive` and
`incumbent_source_is_paper_reproducible=false`.

## Heuristic Module

The production default is selected with:

```powershell
--primal-heuristic hga-tgbc
--primal-heuristic-seed <seed>
--primal-heuristic-runs <runs>
--primal-heuristic-seconds <seconds>
```

The current implementation is a clean tailored derivative of the HGA-TGBC
primal idea: seeded randomized greedy route construction, TGBC-style route-load
decoding, and local improvement over complete route plans. It intentionally
does not migrate HybridGA debug printouts, benchmark loops, stale scripts, or
standalone experiment scaffolding.

Supported modes:

- `none`: no heuristic upper bound beyond the empty route fallback.
- `greedy`: deterministic BPC-owned greedy/local route plan.
- `hga-tgbc`: seeded randomized construction plus local improvement.
- `best-of-all`: deterministic greedy and seeded HGA-style candidates, keeping
  the best verifier-passed route plan.

## Verifier Gating

Every candidate route plan is checked by the independent verifier before it can
update `upper_bound`. Verified exports include route order, pickup/drop
operations, depot unload convention through the route operations, final
inventories, objective components, instance hash, and heuristic settings.

The result JSON records:

- `incumbent_source_category=primal_heuristic`;
- `incumbent_source_is_paper_reproducible=true`;
- `incumbent_source_contributes_lower_bound=false`.

The output guard and Python audit reject any original-problem certificate that
marks an incumbent source as lower-bound evidence.

## Reproducibility

Example:

```powershell
build\ExactEBRP.exe --method primal-heuristic \
  --algorithm-preset paper-bpc-core \
  --input reference\regen_candidate_V12_M2_average.txt \
  --lambda 0.15 --T 3600 \
  --primal-heuristic hga-tgbc \
  --primal-heuristic-seed 20260626 \
  --primal-heuristic-runs 8 \
  --export-incumbent results\incumbents\v12_m2_hga_tgbc.json \
  --out results\primal_heuristic_round\v12_m2_hga_tgbc.json
```

The exported incumbent can be reused explicitly with `--incumbent-json`; this
is paper-reproducible because the file is an input artifact rather than a scan
of an arbitrary local result archive.
