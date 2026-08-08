# HGA-TGBC current algorithm

## Current implementation

HGA-TGBC is the incumbent provider called before C6 exact search. Its contract
is heuristic: it proposes a route plan; `verifySolution` independently decides
whether that plan is a valid original-problem upper bound. C6 exactness does
not assume that HGA is optimal, reproducible beyond its fixed seed, or capable
of proving a lower bound.

The production bridge is `runHgaTgbcNative` in `src/HgaTgbcRunner.cpp`. The
population algorithm is `HybridGA_HGS` in `include/hga_tgbc/HybridGA.h`; its
TGBC decoders are declared under `include/hga_tgbc` and implemented by the
HGA/TGBC sources including `src/hga_tgbc/HgaTgbcGreedy.cpp`.

### Frozen C6-HGA-FULL parameters

| Parameter | Active value |
|---|---:|
| seed | 20260626 |
| population size | 24 |
| crossover probability | 0.85 |
| route-inheritance crossover mixture | 0.65 |
| mutation probability | 0.30 |
| TGBC decode iterations | 10 |
| selection style | fitness selection (`HGAFitness`) |
| decode compaction | full compact mode 1 |
| decode-cache maximum | 200,000 entries |
| education probability | 0.10 |
| education trials | 5 |
| tournament size | 3 |
| stopping mode | generation stagnation |
| generations with no strict global-best improvement | 2,000 |
| local exact-phase re-decode | disabled |

`primal_heuristic_runs` is 12 in the command pack, but the bridge applies
`max(24,runs)`, so the production population is 24. Time is not the normal HGA
stop variable; the overall process deadline remains an emergency correctness
boundary.

### Representation

An individual owns \(M\) ordered station sequences. The equivalent chromosome
is a permutation of station IDs with zero separators between routes. Every
station occurs once in the sanitized full representation, although the TGBC
decoder may execute only a feasible prefix and may assign zero operation to a
visited sequence position. The decoded operation vector gives net pickup
(positive) or drop (negative) by station.

### Initialization

The active constructive mode is zero. Therefore `initialize_population`
creates 24 random separator chromosomes using the fixed Mersenne-Twister seed;
the optional legacy-priority and objective-aware constructive initializers are
present in source but inactive in the current C6 profile. Each individual is
decoded before generation zero, and the best decoded fitness becomes the
initial global best.

### Decoder and fitness

`decode_routes` uses `nGreedyLU_RA_compact_full` in compaction mode 1. The
decoder assigns feasible pickup/drop quantities to the route sequences under
vehicle capacity, station inventory/capacity, travel, handling, and duration
limits. Phenotype-keyed results are cached.

Fitness is maximized and is the negative original objective:

\[
  \phi=-\left(G+\lambda\sum_i w_i|r_i-1|\right),
  \qquad r_i=Y_i/\widehat Y_i.
\]

`objective_from_ops_offset` computes this expression explicitly for guided
move estimates. Final population fitness comes from the TGBC decoder's
`objective_value` under the same sign convention. Greater fitness means a
smaller EBRP objective.

### One generation

For each of 24 offspring:

1. select two parents by a size-three fitness tournament;
2. with probability 0.85, use route-inheritance crossover with conditional
   probability 0.65, otherwise ordered separator crossover;
3. without crossover, copy the fitter parent;
4. mutate with probability 0.30 using the implemented reversal, relocation,
   or exchange family (occasionally two mutation operations);
5. sanitize duplicate/out-of-range stations and insert missing stations at
   the least tail-detour route;
6. decode the child with the compact TGBC decoder; and
7. with probability 0.10, run guided education, accepting only strict decoded
   fitness improvements.

The old population and offspring are pooled. Exact duplicate chromosomes keep
only their fitter representative. Because the active selection style is
`HGAFitness`, the 24 highest-fitness survivors form the next population. The
diversity/biased-fitness implementation remains available but is inactive in
this bridge configuration.

### Improvement and stopping

`update_best` regards an individual as a strict global-best improvement only
when

\[
  \phi_{new}>\phi_{best}+10^{-12}.
\]

An improvement resets `generations_since_improvement` to zero; otherwise the
counter increments after the completed generation. C6-HGA-FULL stops when the
counter reaches 2,000. The generation-zero population is logged as generation
zero. Round 34 adds an observational elapsed-seconds sample after generation
zero and after each completed generation; the sample is not read by selection,
operators, decoder, improvement, or stopping logic.

### Extraction, re-decoding, and independent verification

After stopping, the bridge extracts only the best route sequences. It then
runs `nGreedyLU_RA_compact_full` once more to obtain the station operations,
converts them into original `RoutePlan` objects, and calls `verifySolution`.
The result is accepted only if it is feasible, the objective matches the
original recomputation, and there are no verification errors. The process
phase ledger separately timestamps generation-loop completion, extraction,
route decoding, and verification.

### Entry into C6

The verified objective is the initial minimization upper bound \(U\). It is
used to construct the improving Gini range and the safe objective cutoff rows,
to determine whether an interval remains relevant, to normalize child
disjunction gain, and to determine cutoff fathoming. It is not used as a lower
bound. Native exact-search incumbents may replace it only after independent
verification.

## Existing SIMPLE-START implementation

`runPaperPrimalHeuristic` in `src/main.cpp` already supports
`--primal-heuristic greedy`. In that mode it calls
`buildGreedyIncumbentRoutes` for exactly three deterministic general modes,
verifies every returned original route plan, and retains the best verified
objective. It does not enter the HGA, randomized-greedy, local-education, BPC
bridge, or later GA paths because those branches are conditional on
`hga-tgbc`/`best-of-all`.

This meets Round 34's definition of an existing general simple constructor;
it is not a new heuristic. Its viability still requires verifier-passed
development and official results.

## Possible future heuristic variants

The following are experiments, not current-mainline behavior:

- **HGA-LIGHT-1000:** every active HGA parameter above remains fixed, but the
  uniform stagnation count is 1,000. Historical Round 33 trajectories preserve
  FULL final fitness on 18/18 V10 identities at this count. Round 34 tests the
  full end-to-end exact consequence.
- **SIMPLE-START:** the three-mode deterministic verified constructor replaces
  HGA only as the upper-bound provider. The complete C6 exact phase remains
  unchanged.

No operator probability, population size, seed, mutation, crossover,
selection, decoder, or repair rule is tuned in Round 34. Neither exploratory
variant is promoted automatically. C6-HGA-FULL remains the validated Gurobi
mainline until a separate qualification round says otherwise.

## Trace fields

The current generation CSV is
`generation,elapsed_seconds,best_fitness,strict_improvement`. Result JSON also
records stop mode, total generations, generations since improvement,
improvement count, decoder calls, final HGA fitness, verified objective, HGA
wall time, and the log path. The process ledger is the source for extraction,
final decode, verifier, and downstream exact-phase timing.
