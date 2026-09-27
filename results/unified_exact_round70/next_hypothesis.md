# Next question: permit useful changes of vehicle allocation

D7's complete24-seed DS startup takes2.80s but supplies only U0.694563,
where full HGA already supplied a verified0.215644 route before its deadline.
The subsequent full one-hot MIP reaches0.331966/0.204077 at600, giving a
materially worse gap than P. This is a primal-quality loss, despite the
stronger LB, and cannot be presented as preservation of K1's long-run benefit.
It does not erase the actual small-instance repairs or D6 proof improvement.
The independently checked DS initial witness serves33 stations, picks144 and
drops127, legally returning17 units. HGA's retained witness serves all50,
with228 pickups and228 drops. This service-coverage difference motivates the
unused-tail relocation question; it is not a proof of its effectiveness.

The current finite descent preserves each seed's random station-to-vehicle
allocation. The shared guided-neighborhood implementation already has an
optional cross-route mechanism, currently disabled: take the first eligible
supply/demand node beyond each route's travel-feasible prefix and relocate it
to another vehicle's appropriate pickup/drop anchor. It changes allocation
and can expose otherwise unused service capacity. Full deterministic decoding
is still required to accept any improvement; the proxy only orders candidates.

The next bounded hypothesis is to enable this mechanism uniformly within the
same24-seed, full-neighborhood-exhaustion descent, leaving original DS as an
ablation and retaining the VD-S proof. No larger population, evolution,
construction heuristic, internal time/Work allowance or instance switch is
proposed. Every accepted move must be a strict decoded gain, so the same
finite-state termination and independently verified-UB correctness argument
applies. Cross-route candidates and accepted moves need actual trace counts;
a true option flag alone does not demonstrate execution or benefit.

This limited neighborhood can still miss useful moves between served nodes
and may cost more without improving the physical UB. It is a testable design
question, not a predicted solution or novelty claim. Qualification must cover
capacity/time/one-service semantics after relocation, cached/full agreement,
full terminal neighborhoods, true whole-run deadlines, zero retention and
the complete CLI/Start path. Protect the proven small startup repairs and D6
gain, and keep C2/D4/D3 tradeoffs visible in the declared screening panel.

Round70's K1-R run and full audit are now complete; finish its separate draft
PR before changing measured source. A next-stage resource plan and new freeze are
required before compiling/launching that candidate. The proposed independent
confirmation data remain unrun and are deferred until a candidate is ready.
