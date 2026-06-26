# Primal Heuristic Gap Audit

This round audits the paper-reproducible primal heuristic used by
`--algorithm-preset paper-bpc-core`.

## Current Architecture

Paper-core no longer enables arbitrary result-directory archive scanning by
default. The default UB source is the deterministic, verifier-gated
`--primal-heuristic hga-tgbc` path. The implementation now records all
candidate route plans through `--heuristic-candidates-csv` and exports complete
route JSON incumbents through `--export-incumbent`.

The current implementation contains:

- deterministic greedy route-load starts;
- randomized greedy starts with seeded station/vehicle choices;
- a clean route-set chromosome layer with route repair;
- route-inheritance and ordered-separator crossover over station sequences;
- mutation by swap, relocate, reverse, and route shuffle;
- target-greedy route truncation;
- zero-operation compaction and re-verification;
- a verifier-gated operation-portfolio bridge that reuses the existing
  operation resize/swap route-load local search as a reproducible heuristic
  candidate source.

All accepted incumbents are complete route plans and pass the independent
ExactEBRP verifier before they can update the UB.

## Differences From Original HGA-TGBC

The sibling HybridGA implementation contains a richer decoder and education
stack than the current ExactEBRP integration:

- `nGreedyLU_RA_compact_incremental` / compact TGBC decoding;
- decode cache;
- route-window guided education based on decoded operation roles;
- deeper route inheritance and ordered-separator GA population management;
- stagnation-controlled generations;
- production local search candidates using decoded operation information.

This round intentionally did not migrate debug scripts, old benchmark loops,
or obsolete experiment scaffolding. The integration remains a clean derivative
that exposes the necessary deterministic seed, runtime, candidate summary, and
verifier-gated route export controls.

## Objective Monotonicity Audit

The existing operation-level local search accepts a candidate only if
`trial.objective < best.objective - 1e-10`, and every candidate is rebuilt into
a full route plan and verified before acceptance. No acceptance bug was found
in this path. Apparent "improved" log confusion is caused by comparing labels
from different starts or from route-sequence candidates that are later rejected
or dominated by the operation-portfolio bridge.

## V12 UB Gap

On regenerated V12 M2, the improved reproducible heuristic reached
`0.745475`, improving the prior paper heuristic UB of approximately
`0.756165`, but still missing the diagnostic archive UB
`0.719065249476` and the requested minimum target `0.735000`.

On regenerated V12 M1, the improved reproducible heuristic reached `0.366800`,
which is weaker than the known archive/previous certified UB
`0.357200583208` and above the requested minimum target `0.360000`.

The best candidates in both V12 cases came from the verifier-gated
operation-portfolio bridge, not from the route-sequence GA. This indicates that
the missing strength is primarily in the TGBC decoder and guided education,
not in the certificate or verifier path.

## Implemented Improvements

- Added `--heuristic-candidates-csv` for auditable candidate-level UB output.
- Added clean HGA-style route-sequence population, crossover, mutation, repair,
  truncation, compaction, and local education.
- Fixed ordered-separator crossover so it cannot hang when truncated/repaired
  parents contain different station sets.
- Added the operation-portfolio bridge as a reproducible, verifier-gated UB
  candidate source for `hga-tgbc` and `best-of-all`.
- Expanded operation quantity polish over more randomized starts.

## Remaining Gap

The current reproducible heuristic is better than the prior paper heuristic on
V12 M2, but it is not yet a faithful HGA-TGBC migration. The next targeted work
should migrate the compact incremental TGBC decoder and decoded-operation
guided education from `Hybrid GA/Hybrid GA/HybridGA.h` without importing the
old debug and benchmark scaffolding.

## TGBC Migration Follow-Up

The next migration pass implemented the missing production pieces directly in
ExactEBRP:

- compact TGBC re-decode now carries inherited operation quantities from the
  first decoded solution;
- guided education now uses decoded route windows and operation roles to build
  same-route, zero-tail, and cross-route relocation candidates;
- the HGA-style population loop now uses a larger deterministic search budget
  instead of the previous small 16-individual/18-generation cap;
- a supply-demand quantity beam constructs complete transfer fragments, rebuilds
  route plans through the existing feasible-route decoder, and accepts only
  verifier-passed incumbents.

The objective monotonicity audit remained clean: every accepted candidate is
strictly better than the incumbent under the verifier-computed objective. The
old bridge remains available as a candidate, but on regenerated V12 M2 it is no
longer the best paper-reproducible UB.

Final 60-second seeded tests:

- V12 M1 improved from `0.366799836582` to `0.362059778868`.
- V12 M2 improved from `0.745474506024` to `0.721861135274`.

The V12 M2 target `<= 0.724500` is now met without diagnostic archive scanning.
V12 M1 is improved but still above the known diagnostic/archive value
`0.357200583208`; the next optimization target is deeper multi-transfer
education for M1 rather than certificate-guard work.
