# Objective transfer and what initialization does not guarantee

For the unchanged physical input, feasibility is independent of the search
weight. Every returned full fleet is rechecked by the C++ original physical
verifier, including inventories, prefix loads, compressed travel and loaded
return unloading. Its original upper bound is G(x)+lambda P(x), never the
reported search objective G(x)+a P(x). Only the terminal best fleet actually
returned by each full H is recycled; original-objective intermediate bests
are not archived by this recipe.

With the same valid completed base-H in each pool, inclusion gives initial
U_M <= U_B and U_C <= U_B. The existing strict improvement tolerance 1e-10
retains base-first deterministic ties. This statement is conditional on
the same base result, and guarantees neither final U, qualified global L,
gap nor certification time under an equal cap. Extra H is paid and a new
Start can change the Native search trajectory. Report both
Delta_restart=F_B-F_M and Delta_weight=F_M-F_C; C beating B alone cannot
identify a weight-diversification benefit.

Each child uses a fresh base-H call and local decode cache. The persistent
greedy static cache contains unweighted penalty tables and ratio-universe
data, keyed by capacity/target/weight content and source signatures; it
contains no weighted F. Each HybridGA instance owns a new decode cache.
RAII restores global greedy lambda/scaling across child returns and
exceptions. The original verifier then rebuilds the selected verification.
No other-objective lower, cutoff, stock/g domain, tree, ledger or certificate
is transferred. The unchanged exact B setup receives only a valid original
UB/fleet and builds all original-objective state itself; its correctness
and numerical proof policy are inherited.

lambda=0 or all station penalty weights=0 uniformly skips extra calls.
An original-objective zero accepted by B's zero policy can stop the remaining
paths. The material E4 threshold max(1e-6,.001 max(F_B,1e-12)) is a research
spending rule only. It never rejects smaller valid online improvements.
Completeness, valid physical output and every skipped/interrupted path are
recorded. Same seeds give the same 24 initial random orders for M/C, while
constructed orders, descent paths, checks and CPU costs may differ.

The R166 G/P-dominating final fleet demonstrates a gap in old finite search,
not an improved point on a proven exact Pareto frontier. R168 restricted
family conclusions apply only to their bound input and final parent fleet.
The three properties here explain correctness, not novel OR theorems.
