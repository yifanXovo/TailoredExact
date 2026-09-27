# Round73: joint insertion for the remaining primal-quality deficit

Base Round72 closure branch codex/round72-vdsx-validation,
db7976fe94627c00d76d50c0adfed11223fbf646. Its substantive evidence commit is
fe8d856f2d7bf867c5ea292937effa66e953f613, draft PR133. Git HTTPS publication
failed three times and will be retried; local evidence is preserved. New
branch codex/round73-joint-insertion uses the owned ExactEBRP-round66 checkout.
No closed-stage evidence, stable preset or original dirty checkout is edited.

## Main hypothesis and exactness scope

Jointly selecting an unvisited station's insertion location and integer
operation quantity, including pickup-before-drop pairs, may use available
route duration more effectively than decoding and relocating permutations.
This addresses R71 D7's severe loss of K1's P-relative advantage. R72's long
baseline failed, so there is no completed long comparison; the previously
prospective note's wait-for-complete-long condition is superseded explicitly.
The existing1200s evidence is enough to motivate a separate bounded startup
experiment, not to assume a3600s ranking.

JI starts from the verified no-service route set, evaluates all admissible
new pickup/drop pairs and singles at all insertion positions and positive
integer quantities, and greedily selects actual original F improvement per
added physical route duration. Nonpositive duration additions form a separate
priority class; deterministic ties require no division by zero. Each accepted
step adds at least one previously unvisited station, at most V steps. Stop
on exhaustive absence of an improving motif or the one whole-run deadline.
No internal time/Work budget, restart, instance identity rule, known optimum
or imported route is allowed. Positive improvement tolerance1e-12 is a
heuristic acceptance threshold, not a change to certificate tolerances.

For fixed station(s)/quantity/vehicle, objective is independent of placement;
keeping the minimum-travel feasible placement preserves this local score.
Inventory deltas respect actual station bounds, load constraints apply to all
affected prefixes, and duration includes depot unloading under the original
handling convention. Cumulative pickups may exceed Q. Independent physical
verification is authoritative for every accepted route set and final UB.
This is a local search reduction, not a full-problem dominance theorem.
The exact phase remains the complete VD-S one-hot/AM Gurobi proof; only paid
startup changes. A new preset is isolated and remains default-off.

## Necessary execution prerequisite

R72 exposed a whole-run evidence gap: synchronous Gurobi Optimize can fail to
return before the supervisor kills it, losing buffered progress and final
physical route. Durable verified native witnesses and explicitly scoped bounds
must be qualified before another formal long comparison. Read-only observers
must not add a P-GRB Start, cut, heuristic setting or imported bound. They
may record snapshots; restricted bounds require a complete frontier before
global promotion. Incomplete/post-deadline writes are rejected, bad bounds
are not clipped, and killed execution is still charged and reported.
This is shared reliability/measurement work, not an optimization contribution.
Shared binary changes require fresh matched controls. Additional diagnosis
limits never become formal algorithm decisions.

## Initial resource tranche, declared before new execution

1. Implement JI and meaningful structural tests: same/distinct insertion legs,
   capacity prefixes, cumulative pickups above Q, loaded return, zero handling,
   actual inventory bounds, S=0, deadline and exhaustive tiny motif comparison.
   Build an isolated build/round73. Run the inherited49-test suite once after
   the first qualified implementation, plus new relevant tests. The inherited
   suite currently includes39 native calls; report actual test/native counts.
   Necessary repairs and failed qualification attempts are retained separately.
2. Up to10 fresh UB-only diagnostics, five roles D3/C2/D4/D6/D7 times DS-X/JI,
   each at most30s whole-run cap, maximum300s. Same original inputs/parameters
   and hardware affinity from R72/R71, fixed seed20260626 where applicable.
   These call method primal-heuristic and must launch zero native Optimize.
   Use deterministic JI, not a seed contest. Every diagnostic pays all startup
   work and independently validates its physical witness.
3. Up to6 native evidence/termination qualification experiments, each at most
   30s, maximum180s, separate from performance and any new CTest native cases.
   Record roles/commands before dispatch, including a deliberate forced kill
   only of the owned diagnostic child and incomplete snapshot rejection.

No formal performance panel, repeat,3600/7200s comparison or independent
confirmation is opened by this initial tranche. Declare a justified extension
after correctness, route-quality and persistence evidence is reviewed. Ordinary
usage is currently allowed,90% remaining; no reset was consumed. All cost and
failed launches must be retained; no concurrent optimizer/heavy compilation.

## Decision and publication

Report full physical F/G/P, serviced stations, quantities, load/duration,
initial route hash, all motif counts and paid time. Do not equate a stronger
startup UB with faster full proof. A poor D7 construction result can motivate
a general mechanism revision, but not an instance-specific switch.
The common frozen practical performance thresholds from R69-R72 remain in
force if formal experiments are later admitted. These exposed inputs are
development data. Final goal, long K1 protection and broad confirmation remain
unmet. Publish one new draft PR after substantive implementation/validation;
do not publish a logging-only stage or merge main.
