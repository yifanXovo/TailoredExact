# C6 source-to-paper map

The current source code, not a historical narrative, is the authority for this
map. “Active” means reachable under the frozen C6 command profile.

| Paper-level component | Authoritative implementation | Active responsibility |
|---|---|---|
| CLI and frozen option pack | `src/main.cpp`; `scripts/run_round28_experiments.py`; `scripts/run_round31_experiments.py` | Parses options and fixes the C6 profile: HGA, four intervals, static rows, geometry, one thread, S0/F0-style model choices, C6 selector/lifecycle. |
| Round 34 startup gate | `SolveOptions::round34_c6_startup_variant`; `round31C6FrozenOptionsValid` | Admits only FULL-2000, LIGHT-1000, or existing deterministic greedy startup. It is outside exact decisions. |
| Input and preprocessing | `src/Parser.cpp`; preprocessing invoked from `src/main.cpp` | Reads the original instance, distance/time/capacity/inventory/target data, and run configuration. |
| HGA bridge | `runHgaTgbcNative` in `src/HgaTgbcRunner.cpp` | Converts the instance, runs fixed HGA, extracts/decode routes, calls independent verifier, records phase events. |
| HGA population | `HybridGA_HGS::run` and helpers in `include/hga_tgbc/HybridGA.h` | Representation, initialization, tournament, crossover, mutation, education, deduplication, survivor selection, strict-improvement stopping. |
| TGBC decode | `nGreedyLU_RA_compact_full` and related HGA/TGBC sources under `include/hga_tgbc`, `src/hga_tgbc` | Assigns operations to route sequences and evaluates heuristic fitness. |
| Existing simple constructor | `runPaperPrimalHeuristic`, `buildGreedyIncumbentRoutes` in `src/main.cpp` | Constructs three deterministic candidates, verifies them, selects best verified route plan. |
| Original verifier | `verifySolution` in `src/Evaluator.cpp` (declared in `include/Evaluator.hpp`) | Replays routes and operations; checks original feasibility and recomputes \(G,P,F\). Sole authority for a usable incumbent. |
| Improving Gini range / mode dispatch | `src/main.cpp`; call into `solvePaperExternalGiniTree` | Passes the same-run verified seed and complete improving root Gini endpoints into C6. |
| Canonical compact writer | `writeCanonicalCompactModel` in `src/CplexBaseline.cpp` | Writes one deterministic LP formulation consumed by both Gurobi paths; despite filename, it is shared and solver-neutral at the artifact boundary. |
| Base exact model | `writeCanonicalCompactModel` in `src/CplexBaseline.cpp` | Routing/visit/order/load/operation/duration, inventory/ratio/deviation/Gini linearization, objective, variable domains. |
| Global strengthening | `writeCanonicalCompactModel`; registry in `buildRound18StaticIntervalRows` | Inventory conservation, movement domains, visit-inventory linking, global handling capacity, support-duration, transfer compatibility. |
| Interval row factory | `buildRound18StaticIntervalRows` in `src/IntervalRowFactory.cpp` | Interval bounds/domains and nine named active interval-local strengthening families; deterministic row/bound signatures. |
| Exact inherited row delta | `makeCanonicalInheritanceState`, `computeExactIncrementalDelta`, `mergeCanonicalInheritanceState` in `src/IntervalRowFactory.cpp` | Audits complete static migration and exact parent/child row inheritance. C6 profile attaches the full inherited pack. |
| Canonical artifact cache | artifact construction inside `solvePaperExternalGiniTree` | Generates each fixed-interval artifact, hashes it, records scope/signature, and reuses only identity-matching artifacts. |
| Fixed-interval Gurobi backend | implementation behind `makeFixedIntervalMipBackend`; `src/GurobiBaseline.cpp` | Reads canonical LP, switches LP/MIP domains, runs complete LPs, native-bound targets, terminal MIPs, callbacks, and engineering gates. |
| Leaf record and scheduler | `ControllingLeaf`, `ControllingLeafScheduler` in `include/ControllingLeafScheduler.hpp`, `src/ControllingLeafScheduler.cpp` | Coverage, statuses, monotone bounds, relevance, cutoff, deterministic controlling set, atomic split, lifecycle accounting. |
| C6 frontier target | `evaluateC6FrontierDecision` in `src/PaperExternalGiniTree.cpp` | Pure next-strict-frontier decision, stale-selection requeue, and child-lookahead admission. |
| Child-disjunction decision | `evaluateC5BoundTargetSplitDecision`, wrapped by `evaluateC6CurrentSplitDecision` | Computes post-child lower bound, normalized gain, immediate split, child-bound target, or exact parent closure. |
| Split geometry | `legacyAdaptiveSplitEligible`, `splitLegacyFrontierInterval`, `exactIntervalCoverage` in the Gini frontier geometry module | Binary midpoint split, depth/width eligibility, exact endpoint coverage. |
| Atomic replacement | `ControllingLeafScheduler::splitLeafAtomically` | Verifies lineage, adjacent cover, endpoints, and inherited bounds before replacing parent. |
| Native target execution | `runC6NativeTarget` lambda inside `solvePaperExternalGiniTree` | Launch-frozen target request, native callback trace, bound merge, exact closure, requeue, deadline handling. |
| Exact terminal closure | terminal section of `solvePaperExternalGiniTree`; `evaluatePaperTerminalMipDecision` | Allows close only after engineering-gated native optimality/infeasibility; interruption leaves leaf open. |
| Incumbent update during exact search | native outcome handling in `solvePaperExternalGiniTree` | Independently verifies improving native route plans, lowers global cutoff, updates stored best routes. |
| Global lower bound | `ControllingLeafScheduler::globalLowerBound`, `mergeValidLowerBound`, `setStatus` | Minimum valid bound over relevant final leaves, with max-merges and monotonicity audit. |
| Deadline | process-clock helpers; backend remaining-time requests; `stopAtDeadline` | Process-entry cap, no new launch after exhaustion, open coverage retained, graceful non-certificate finalization. |
| Certificate decision | `evaluateExternalGiniTreeCertificate` in external-tree certificate module; assembly in `solvePaperExternalGiniTree` | Coverage, closure, bounds, verifier, lifecycle, and gap gate for strict original-problem certification. |
| Result serialization | `src/Result.cpp`; `include/Result.hpp` | Serializes strict status, bounds, counts, lifecycle, row families, timing, startup variant, and trace paths. |
| Process phases | `src/ProcessPhaseLedger.cpp`; calls from main/HGA/Gurobi/C6 | Process-entry chronology for startup, verification, model construction, first events, solves, and finalization. |
| Exact-tree traces | CSV writers in `solvePaperExternalGiniTree` | Global bound, leaves, LPs, parent-child bounds, splits, targets, model lifecycle, row signatures, and coverage. |
| Plain Gurobi comparator | `solveGurobiBaseline` in `src/GurobiBaseline.cpp`; `round34_common.plain_command` | Complete compact original MILP, same canonical formulation, one thread, Seed 0, no HGA or interval decomposition. |

## Active versus legacy boundaries

The C6 production selector is `round31-nonblocking-native-bound` with lifecycle
`round31-open-native-bounded`. Earlier paper-event, C3, C4, and C5 branches are
retained for historical evidence and tests but are not part of current C6.
CPLEX callback-specific cut machinery and the accepted S0/F0-CPLEX algorithm
remain separate solver-specific mainlines. C6 does not claim CPLEX callback
behavior, LP basis reuse, native Gurobi branch-tree continuation across leaves,
or a selector-variable single-tree formulation.

The static row factory registers interval bounds and the verified-incumbent
row in addition to the 15 named strengthening families. Round 34 reports the
15 requested global/interval strengthening families separately so row-family
counts are not inflated by structural interval bounds or the safe incumbent
cutoff.
