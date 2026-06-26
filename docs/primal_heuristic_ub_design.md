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

## Primal UB Improvement Round

This round added `--heuristic-candidates-csv`, which records every
verifier-checked candidate with objective components, route counts, operation
totals, route durations, runtime, and whether it became the best incumbent.
The seeded `hga-tgbc` path now includes a clean operation-portfolio bridge that
reuses verifier-gated operation resize/swap route-load local search as a
reproducible UB candidate source.

On regenerated V12 M2, the improved heuristic reached UB `0.745475`, improving
the previous paper heuristic UB of approximately `0.756165`, but still missing
the diagnostic archive UB `0.719065249476`. On regenerated V12 M1, the
improved UB is `0.366800`, above the known good UB `0.357200583208`. The next
heuristic step is a fuller migration of HybridGA's compact TGBC decoder and
decoded-operation guided education.

## TGBC Migration Round

The follow-up TGBC migration round completed the production-relevant decoder
and education migration without importing HybridGA debug outputs, obsolete
benchmark drivers, or tuning scaffolding. The `hga-tgbc` path now includes:

- compact TGBC re-decode with inherited operation quantities from the first
  decoded route plan;
- decoded-operation guided education using route windows, supply/demand role
  classification, same-route relocate, zero-operation tail compaction, and
  cross-route relocation candidates;
- larger deterministic HGA-style population budgets controlled by
  `--primal-heuristic-runs` and `--primal-heuristic-seconds`;
- deterministic supply-demand pair route-set construction;
- deterministic supply-demand quantity-beam construction over complete
  pickup/drop transfer fragments, followed by existing route reconstruction
  and independent verifier checks.

The quantity-beam component is still an upper-bound heuristic only. It creates
candidate route-load plans, rebuilds feasible routes, and accepts a plan only
after the independent verifier confirms route flow, station capacity, truck
capacity, route duration, final inventory, and objective consistency.

Final smoke tests under seed `20260626` produced:

- V4 smoke UB `0`;
- regenerated V12 M1 UB `0.362059778868`, improved from `0.366799836582`;
- regenerated V12 M2 UB `0.721861135274`, improved from `0.745474506024`
  and meeting the strong UB target `<= 0.724500`.

All rows remain `certificate_scope=primal_heuristic_ub_only`; the incumbent
source contributes no lower-bound evidence.
