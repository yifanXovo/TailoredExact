# Provisional next question — no measured implementation or experiment opened

The completed small validation separates two defects: VD-S repairs N12's
post-HGA proof cost, but leaves E7/S12's full generation-stagnation HGA startup.
S12's P native root relaxation is zero, so a simple relative-to-root-LB target
would not automatically recognize its good nonzero incumbent. An early event
with the eventual objective is not a usable stopping oracle.

One admissible direction to evaluate after this frozen stage is replacing the
evolutionary startup with a finite pool of constructive/local-descent seeds.
The existing 24 initial individuals and BRP decoder can be reused, with the
existing pickup-before-drop/tail-relocation neighborhood. Each seed descends
until a complete declared neighborhood has no strict decoded-objective gain;
this is a search-state termination, not a seconds/Work/generation allocation.
Population size retains its meaning as initialization diversity, not a timeout.

Code inspection identifies an important qualification: HybridGA.h's current
improve_once_guided filters candidates using approximate fitness and breaks
early. Calling it unchanged cannot establish local optimality over every
generated move. A future method must either state precisely that restricted
proxy-admissible neighborhood, or evaluate all declared neighbors and use the
proxy only to order them. The latter has a clearer termination definition but
may cost more. The deterministic cached full decoder has to be checked on the
actual path; no theorem about route optimality or runtime dominance follows.

Strict descent over finite route/order and integral-operation states terminates.
Original-problem exactness still comes from the complete MIP/frontier engine:
the seed supplies only a physically verified UB and Start. It must never remove
coverage, change capacity/handling/T semantics, or reuse a historical witness.
Improved startup can weaken the seed and widen the initial proof domain, so
D3/C2/D4 and the actual D6/D7 long results must guide the later bounded tests.

No measured solver source, binary or parameters have changed for Round69. No
new seed has been run, and no performance gain is claimed for this provisional idea.
These public validation observations become development evidence for any
revision they inform; that revision would need separate confirmation.

Further read-only implementation checks: the active bridge leaves
constructive_mode=0 and enable_tail_cross_route=false. Thus the current 24
initial individuals are random permutations with route separators, not
objective-aware constructive seeds. Reusing these seeds is the narrowest
initialization change; activating a constructor or cross-route moves would be
an additional declared choice. The full compact decoder returns negative F
as its maximizing fitness, ignores its historical max_iter argument, and
runs its operation descent to completion. Its compaction keeps active visits
from the travel-feasible prefix; it does not automatically bring untouched
tail stations into the rerun.

A future complete-neighborhood claim also requires a deterministic decode
map. Source checking confirms that the current positive-T cache key and the
greedy engine both stop at the same travel-prefix condition with epsilon
1e-12. The engine's compact rerun uses only active nodes from that prefix.
For valid HGA routes with every station assigned once, preserving this ordered
prefix per vehicle therefore preserves the decoder's input state; omitted
tails do not enter the computation. The cache itself adds no random choice.
A future test should still check cached versus fresh full decoding on the
new mode's actual path, especially empty routes and time boundaries. No
measured source was edited, and no invalid Round69 witness was found.

Narrow literature scope checked during the queue: Vidal's
[Hybrid Genetic Search for the CVRP](https://arxiv.org/abs/2012.10384)
already combines genetic search and local improvement. Local descent seeds
are therefore not claimed as a new general metaheuristic. The question here
is their BRP-specific initialization cost, witness quality and effect on the
full exact proof process; this remains unmeasured. The CVRP paper is not an
equivalence proof or a performance result for this Gini BRP.

While the frozen queue runs, isolated source copies and qualification-test
drafts were prepared under build/round70_draft, outside the measured source
tree and excluded from this stage's build. They implement the narrow random-
seed/intra-route version outlined above, but have not been compiled, tested,
or selected as a measured candidate. That directory's README records the
remaining qualification and integration steps. Round69 must still finish its
original plan and stage PR before a new performance stage is opened.
