# Conditional structural review during the frozen campaign

This is read-only design work while the three admitted complete runs execute.
It admits no additional optimizer, fixed-state experiment, implementation or
parameter change. No conclusion about the unfinished JDS-C run is made here.

## The next comparison need not preserve the strengthened representation

The current chain uses the improved physical starter with VD-S's inventory
state representation and external proof organization. R74's parent MIP has
already demonstrated a complete-method failure despite stronger native bounds.
R76 improves the actual starter, but this by itself cannot identify whether
the remaining loss is route/quantity search, native formulation cost or their
interaction. Continuing only to tune local neighborhoods would not answer
that architectural question.

Targeted local code review confirms that GurobiBaseline.cpp already contains
an original-compact HGA Start ablation. It runs runHgaTgbcNative, maps verified
nonempty routes with mapVerifiedRoutesToCanonicalModel over the full Gini
range, and submits a complete Start array. R31's report records seven such
ablation rows. This is an existing experimental entry point, not evidence that
JDS-C is already integrated there or that it will improve performance.

The old entry point constructs its own HGA options. It does not run R73's
constructive-seeded startup and R76 physical closure. It also does not provide
the entire R68 actual-row/readback/persistence acceptance chain merely by
calling the shared semantic mapper. A future direct-compact JDS-C candidate
would first need a shared paid current-run starter and verified native-array
integration, while retaining the original compact domain, settings and full
native search. The official P control would continue to receive no Start.
This could test representation/organization with the same independently
generated starter rather than import an archived optimum or use time slicing.

R59 already cautions against assuming every removal helps: simple-start
Single-S removed child probes and external splitting but often behaved much
like the same-state K1-S parent MIP. Removing HGA did not resolve D6/D7 native
primal/proof difficulty. The D4 loss also occurred with no splitting. These
observations motivate inspecting the actual model and full native trajectory,
not attributing every loss to AM or to startup seconds. They do not rule out
the new current-witness direct-compact comparison.

## A distinct physical hypothesis also remains available

R76 D7 JDS-C startup uses three vehicles (17/23/10/0 stops) with the first
two durations near T18000. The historical R74 K1 witness uses four vehicles
(11/12/13/14 stops). This is an observed structural difference, not proof that
unused fleet is the cause or that moving a particular operation is feasible.
All stations are now served, so unvisited insertion is exhausted. Strict
single/pair quantity descent does not change the current vehicle assignment
unless an operation disappears and can later be reinserted.

A future neutral relocation rule would need to preserve exactly the original
inventory vector and prove finite descent through a separate route potential.
For example, a balanced contiguous block has zero signed net load; removing
it leaves load prefixes outside the block unchanged. Its insertion still
needs every target prefix and exact travel/handling time checked. Local block
prefixes can be negative relative to their entry load, so zero net load alone
does not make that block feasible on an empty vehicle. A lexicographic route
potential could prevent neutral cycles over finite route/operation states,
but neither its neighborhood completeness nor performance is established.
This remains a different hypothesis, not a new stage's selected mechanism.

A direct conservation restriction is already clear from the inspected R76
witness: each used route has equal total pickup and drop (92/92,67/67,30/30),
so all return loads are zero. For an R75 cross-vehicle pair on routes k and l,
the signed-operation changes are +t and -t. Their new return loads would be
t and -t, respectively. For nonzero t, one is negative. Thus no cross-vehicle
R75 pair is physically feasible at any state where both affected routes return
empty. This does not rely on time limits, prefix details or the objective.
The observed R76 pair moves stay within one vehicle and retain empty returns,
so this restriction persists along that recorded trajectory. It is a simple
conservation consequence, not new theory or proof of the sole performance
cause. Loaded-return states can admit such pairs (and R75 tests exercise them).
Balanced relocations or at least two coordinated changes on each affected
empty-return route would address a different declared neighborhood; their
feasibility and benefit still require their own implementation and evidence.

After the fresh P/JDS-C/K1 results and actual model/Start audits are complete,
choose the next question from the observed deficit. Preserve this note as a
prospective review, keep closed-stage results unchanged, and declare a new
bounded plan before implementing or running any of these alternatives.
