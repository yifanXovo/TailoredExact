# Round 39 final report

## Outcome

50 of 51 frozen rows converged
with strict original-problem certificates, 1 is candidly
unresolved, and there are zero false certificates. The 24 new V<=12 instances were selected and labelled
from structural data before any official P-GRB/LIGHT outcome was examined.
No C++ algorithm, geometry, scheduler, split, or certificate code changed.

| Stratum | Pairs | P-GRB wins | LIGHT wins | Ties | Unresolved | P-GRB shifted geomean | LIGHT shifted geomean |
|---|---:|---:|---:|---:|---:|---:|---:|
| easy | 8 | 8 | 0 | 0 | 0 | 0.654 s | 4.360 s |
| medium | 8 | 3 | 4 | 1 | 0 | 26.280 s | 22.069 s |
| hard | 8 | 2 | 5 | 0 | 1 | 24.766 s | 6.961 s |

P-GRB dominates the easy stratum because uniform HGA startup is fixed overhead.
The medium stratum is mixed, not a clean scalar crossover. LIGHT dominates the
hard stratum by pair wins and shifted geometric mean. The first observed LIGHT
win occurs at score 60.259; the
machine-readable crossover file records whether a uniform high-score suffix
exists after all outcomes are considered.

## Benchmark interpretation

The new set is more informative for the intended startup-overhead question:
it covers V8/V10/V12, M1/M2/M3, both Q values, and three nonoverlapping frozen
score strata. Only 1/24 new LIGHT rows closes with an empty
strict-improver region at startup, confined to easy; medium/hard have none.
The Round33 V10 context has 1/18 such rows. Round39 is not
claimed to be uniformly harder than the high-imbalance Round33 panel; the
value is controlled gradient and dimensional coverage. Historical rows remain
context only and are never mixed into official summaries.

## FULL guard and recommendation

The predeclared easy/medium/hard FULL guard reproduces LIGHT's verified startup
UB in 3/3
cases. When UB is equal, complete timing-free hashes show structurally
identical downstream paths in
3/3
cases. Exact startup, exact-phase, total-time, interval, LP, target/requeue,
split, closure, Work, and node evidence is in the companion CSVs.

LIGHT should not advance yet because one official LIGHT numerical endpoint remains unresolved despite a uniformly nonregressive FULL guard.
It is not promoted here. **C6-HGA-FULL, K=4, rho=0.01 remains the validated
default mainline.**

## Correctness

All completed rows pass the exactness audit: original-problem verification,
zero-gap strict
certificates, monotone valid C6 bounds, full root/parent-child coverage,
balanced solver lifecycle, one-thread commands, Seed 0, zero P-GRB gap
settings, and Round36/37 default-off policy isolation all hold. Round38 remains
outside this main-based branch. The final build/test and default-equivalence
gates are recorded separately after this analysis.
