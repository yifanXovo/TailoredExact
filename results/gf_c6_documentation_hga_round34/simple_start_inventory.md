# Inventory of existing simple primal starts

## Audit question

Round 34 searched the current repository for a general, non-instance-specific
constructor that returns an original route plan and is independently verified
before C6 uses its objective. No new heuristic was designed.

## Paths inspected

| Existing path | Source | General | Deterministic in audited mode | Independent verifier | SIMPLE-START decision |
|---|---|---:|---:|---:|---|
| Three-mode greedy route construction | `buildGreedyIncumbentRoutes`, `runPaperPrimalHeuristic` in `src/main.cpp` | yes | yes | yes | **Eligible** |
| Native HGA-TGBC initialization/search | `src/HgaTgbcRunner.cpp`, `include/hga_tgbc/HybridGA.h` | yes | fixed-seed, but evolutionary | yes | Baseline, not “simple” |
| Randomized greedy portfolio | `buildRandomizedGreedyIncumbentRoutes` and later branches in `runPaperPrimalHeuristic` | yes | seed-controlled | yes | Not selected: only entered by HGA/best-of-all and is not the audited simple branch |
| Local education / repair | `educateRoutePlan` calls in `src/main.cpp` | yes | seed-controlled | yes | Not selected: changes multiple search mechanisms |
| BPC-owned incumbent generator | `runBpcOwnedIncumbentGenerator` | yes | solver/search dependent | downstream verification | Not selected: complex exact-framework component, not a lightweight constructor |
| Route-pool/archive/import starts | incumbent import and archive paths in `src/main.cpp` | depends on external artifact | depends on artifact | yes | Not eligible as a self-contained general constructor |
| Empty/no incumbent | none | n/a | n/a | no verified cutoff | Invalid for C6 and not tested |

## Eligible constructor

With `--primal-heuristic greedy`, `runPaperPrimalHeuristic` executes only this
loop:

```text
for greedy_mode in 0, 1, 2:
    candidate <- buildGreedyIncumbentRoutes(instance, lambda, greedy_mode)
    verification <- verifySolution(instance, candidate, lambda)
    retain candidate only if original feasibility and objective checks pass
return the lowest-objective verified candidate
```

The flags `use_random` and `use_local` are false for mode `greedy`, and all
HGA, randomized, BPC bridge, and later GA branches are conditional on
`hga-tgbc` or `best-of-all`. Thus SIMPLE-START is a pre-existing deterministic
three-candidate constructor, not a truncated HGA and not a newly invented
algorithm.

The Round 34 development gate requires all seven predeclared identities to
produce a verifier-passed original solution. Only after that gate may the same
uniform `greedy` arm enter the 18-instance V10 and transfer matrices. Its exact
phase is the unchanged C6 phase; the upper bound may be weaker, which is why
the official outcome is ranked by total strict-certificate time rather than
constructor time.

## Measurement boundary

SIMPLE-START time begins at process entry and includes parsing, all three
constructors, all candidate verifications, choice of the best candidate, range
construction, interval model construction, exact C6 search, final verification,
and certificate serialization. A quick constructor with a slow downstream
proof is not considered a win.
