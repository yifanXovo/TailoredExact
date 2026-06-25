# Primal UB Improvement Round Final Report

Branch: `codex/longrun-round17-local-results`

Final pushed commit SHA: recorded in the assistant final response after commit.

## Build And Audit

Build command:

```powershell
D:\msys64\ucrt64\bin\g++.exe -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src\Parser.cpp src\Evaluator.cpp src\Result.cpp src\Bounds.cpp src\ColumnPool.cpp src\TailoredExact.cpp src\Pricing.cpp src\Cuts.cpp src\Branching.cpp src\Master.cpp src\ColumnGeneration.cpp src\CplexBaseline.cpp src\Logger.cpp src\main.cpp -o build\ExactEBRP.exe
```

Audit command:

```powershell
D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py --self-test
D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py results\primal_ub_improvement_round\raw --csv-out results\primal_ub_improvement_round\certificate_audit.csv --fail-on-error
```

The Windows `python.exe` in `WindowsApps` is an execution alias, so the MSYS2
Python path above was used. The audit passed with 15 rows and 0 failures.

## Code Changes

- Added `--heuristic-candidates-csv` to `SolveOptions` and CLI parsing.
- Added HGA-style route-sequence repair, truncation, crossover, mutation,
  compaction, and candidate logging.
- Fixed ordered-separator crossover so truncated/repaired parents cannot cause
  an infinite fill loop.
- Added a verifier-gated operation-portfolio bridge inside the seeded
  `hga-tgbc`/`best-of-all` paper heuristic candidate pool.
- Expanded operation quantity polish over randomized starts.

All heuristic and imported incumbents remain UB-only and record
`incumbent_source_contributes_lower_bound=false`.

## Heuristic UB Results

Regenerated V12 M2:

- previous paper heuristic UB: approximately `0.756165366387`;
- improved reproducible heuristic UB: `0.745474506024`;
- diagnostic archive UB: `0.719065249476`;
- target status: improved but did not reach the requested minimum target
  `0.735000`.

Regenerated V12 M1:

- improved reproducible heuristic UB: `0.366799836582`;
- known good/archive UB: `0.357200583208`;
- target status: did not reach the requested minimum target `0.360000`.

The strongest V12 candidates came from the verifier-gated operation-portfolio
bridge. Route-sequence GA candidates were useful diagnostics but not the best
source.

## Focused Certificate Results

V4 smoke paper-core 30s:

- status: `optimal`;
- objective/LB/UB: `0`;
- certified original problem: `true`.

V12 M2 paper-core, improved heuristic, 300s:

- status: `gcap_frontier_not_closed`;
- UB: `0.745474506024`;
- LB: `0.689651961258`;
- gap: `0.0748818964495`;
- unresolved intervals/open nodes: `3` / `3`;
- certified original problem: `false`.

V12 M2 explicit exported heuristic incumbent JSON, 300s:

- status: `gcap_frontier_not_closed`;
- UB/LB/gap match the in-run heuristic row.

V12 M2 diagnostic archive, 300s:

- status: `optimal`;
- objective/LB/UB: `0.719065249476`;
- certified original problem: `true`;
- use: diagnostic UB-quality threshold only, not paper-core default.

V12 M1 paper-core, improved heuristic, 300s:

- status: `gcap_frontier_not_closed`;
- UB: `0.366799836582`;
- LB: `0.344555798130`;
- gap: `0.060643534247`;
- unresolved intervals/open nodes: `3` / `3`;
- certified original problem: `false`.

V12 M1 explicit exported heuristic incumbent JSON, 300s:

- status: `gcap_frontier_not_closed`;
- same UB and lower-bound plateau scope as the in-run heuristic row.

## Generated Variants

The requested generated-variant rerun was attempted for ten existing
engineering variants. The batch was stopped after the first row exceeded the
expected 120s wall-clock behavior without producing a raw JSON or log output.
No generated-variant improvement is claimed this round. The stopped batch is
recorded in:

- `results/generated_variant_round2/run_status.csv`;
- `results/generated_variant_round2/summary.csv`.

## Relaxation-Bound Findings

The V12 M2 diagnostic archive row still certifies through the same
relaxation-only paper-core certificate path. Under the improved reproducible
heuristic UB, V12 M1/M2 remain noncertified. This indicates that UB quality is
currently the dominant limitation; broad frontier or relaxation scheduling is
secondary for these regenerated rows.

## Remaining Bottlenecks

- The integrated heuristic is still a clean derivative, not a faithful full
  HGA-TGBC migration.
- The missing pieces are the compact incremental TGBC decoder and
  decoded-operation guided education from HybridGA.
- Generated variant reruns need a more robust wall-clock wrapper or a solver
  time-limit fix before large local campaigns.

## Next Recommended Action

Run one more targeted heuristic round focused only on migrating the compact
TGBC decoder and guided education, then rerun V12 M1/M2 and the generated
variant subset. Do not start a comprehensive paper benchmark until V12 M2
paper-reproducible UB is near `0.724500` or the failure reason is proven
structural.
