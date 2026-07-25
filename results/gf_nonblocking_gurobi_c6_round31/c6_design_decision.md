# C6 design decision

## Selected algorithm

C6 is the single primary `OPEN_NATIVE_BOUNDED` prototype. No fallback
prototype was needed. It preserves the C5 mathematical model, F0
connectivity, static inherited row pack, exact four-interval binary geometry,
and independently verified HGA incumbent. The change is a solver-neutral
ordering and state-machine change:

1. Select the relevant leaf with minimum valid bound using the frozen
   `(bound, lower endpoint, upper endpoint, id)` order.
2. Complete its parent LP if that exact LP status is not already available.
3. Close an infeasible LP leaf, or prune a leaf whose valid bound meets the
   verified cutoff.
4. If completion of that LP made another open leaf strictly lower, retain and
   requeue the parent without child lookahead or native work.
5. Otherwise, before any child LP, target the smallest strictly higher valid
   bound among other relevant leaves. Ties are ignored. This launch-frozen
   mathematical target is used at most once in the leaf's
   `OPEN_LP_BOUNDED -> OPEN_NATIVE_BOUNDED` transition.
6. Optimality or infeasibility during that native phase closes the leaf.
   Reaching the target merges the validity-gated native bound and requeues
   the still-open parent. Deadline interruption also leaves it open.
7. When the strengthened parent again controls, or when no higher frontier
   target exists, compute both complete child LPs lazily and atomically.
8. Split immediately only for a complete infeasible child or when the
   *current* normalized child-disjunction gain reaches the frozen
   `rho=0.01`.
9. For a strict positive gain below rho, process the parent to the complete
   child-disjunction bound. Reaching that bound keeps the parent open,
   retains the complete child-LP pair, and requeues it. It does not schedule
   a delayed split.
10. On reselection, compare the cached children with the current strengthened
    parent bound. If their current strict gain has disappeared, discard the
    speculative child models and launch exact parent closure.
11. A no-gain parent and a structurally terminal parent launch exact closure
    only after no unused higher scheduling milestone remains.

## Why parent-native-first

Round 30 evidence contains 55 explicit parent selections after complete LPs.
Thirty were already no longer strictly controlling, so a child-first policy
would spend 60 avoidable child-LP calls. The other 25 had a finite,
parameter-free higher frontier target. Across the primary C5 evidence the
deferred child calls account for 184.373211 Work. Meanwhile, 86 of 94 C5
child-target phases reached their target and then forced a split even though
the current child gain was zero. Those delayed splits produced zero immediate
global-bound gain.

Parent-native-first therefore attacks the observed waste directly without a
time, Work, node, attempt, or instance-class rule.

## No-gain and forced-split rules

A no-gain decision never creates an equal or vanishing native target. If the
leaf still has an unused strictly higher frontier milestone, it reaches that
milestone first. Once the leaf is again controlling, no-gain launches exact
closure.

A reached child target never forces a split. The cached child LPs are
re-evaluated against the current parent bound. Only current child gain can
split.

## Parameters

C6 adds no strategy parameter. The only policy threshold remains rho=0.01.
The certificate tolerance, geometry, depth, width, HGA seed/stop rule, solver
thread count, solver seed, and engineering deadline margin are unchanged.

## Eventual exactness

Each leaf has one finite parent-LP transition, at most one finite
next-frontier target transition, at most one child-lookahead pair, and at
most one child-bound target transition. It then closes exactly or is replaced
by two exact children. Binary depth is bounded by eight and width by the
frozen structural limit, so only finitely many leaves can exist. With no
process deadline, every native target solve either reaches its fixed target,
proves optimality/infeasibility, or continues until one of those conditions.
Thus no artificial target ladder or infinite retry sequence exists.

## Rejected alternatives

- C5 child-first with mandatory delayed split: contradicted by the observed
  zero current gain after 86 target attainments.
- Repeated unrestricted frontier target ladders: attractive for interleaving
  but lacks the finite state-transition proof required here.
- Fixed native time, Work, node, solution, attempt, or retry budgets:
  hardware/execution dependent and prohibited.
- New inequalities: Phase A identified scheduling and continuation failures,
  not a coherent shared missing row family.
- LP basis transfer: unnecessary for the chosen mechanism and unsupported by
  frozen equivalence evidence.

## Expected mechanism and failure handling

C6 should avoid child work when a parent LP or native target already balances
the external frontier, avoid C5's obsolete delayed splits, and expose valid
native bounds from difficult parents before a final blocking closure. Any
invalid LP status, nonfinite relevant bound, failed model-identity gate,
invalid partial status, bound-merge failure, or lifecycle mismatch fails
closed as an engineering error. The overall deadline finalizes all ledgers
and retains unresolved intervals as open.
