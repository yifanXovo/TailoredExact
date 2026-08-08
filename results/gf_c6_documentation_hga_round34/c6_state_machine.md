# C6 leaf state machine and scheduler

## State carried by a leaf

A leaf \(I\) stores its Gini interval \([\gamma_L^I,\gamma_U^I]\), lineage,
split depth, verified cutoff \(U\), base/inherited bound, current valid bound
\(b_I\), bound-source ledger, status, LP state, target milestones, cached child
LP state, and native lifecycle counters. The public scheduler status enum is
`Open`, `Closed`, `Fathomed`, `Empty`, `Invalid`, and `Replaced`. The following
paper-level substates refine `Open`; they are not additional enum values.

| Paper-level state | Stored condition | Permitted next events |
|---|---|---|
| Newly created / unprocessed | `Open`, no complete LP | complete parent LP |
| Complete LP-bounded | terminal-valid LP and finite merged \(b_I\) | LP prune, native frontier target, or child lookahead |
| Open native-bounded | one or more valid native bounds merged | deterministic requeue and reselection |
| Native-target processing | target launch is in progress | exact native closure, target-reached requeue, or deadline-open |
| Requeued | still `Open`; coverage unchanged | selection by current global bound |
| Child-lookahead-ready | no unused frontier milestone | solve two speculative child LPs completely |
| Child-bound-target | small positive child gain | native target at child-disjunction bound, then requeue or exact close |
| Atomically split parent | parent `Replaced`; both children installed | children become independently selectable |
| Closed optimal | `Closed` with native-optimal source | final accounting only |
| Infeasible / empty | `Empty` with complete LP or native-infeasible source | final accounting only |
| Cutoff-fathomed | `Fathomed`, bound at least cutoff | final accounting only |
| Deadline-open | still `Open`, possibly with a stronger bound | non-certified finalization |

`Invalid` is accepted by the scheduler as an open-relevant recovery state, but
the C6 production loop does not use it as a mathematical closure.

## Relevance and controlling set

A final leaf is relevant if it has not been replaced and
\(\gamma_L^I<U-10^{-7}\). It is open-relevant if its status is `Open` or
`Invalid` and \(b_I<U-10^{-7}\). The controlling set contains every
open-relevant leaf within \(10^{-7}\) of the smallest current bound.

Within a tied controlling set the actual `selectNextByBoundOnly` order is:

1. larger interval width first;
2. smaller \(\gamma_L\);
3. smaller \(\gamma_U\); and
4. lexicographically smaller leaf ID.

The scheduler rotates through this deterministic order. When the membership
or minimum bound changes, rotation restarts at position zero. No timing, Work,
node count, or prior effort participates.

## Transition diagram

```text
new Open leaf
  -> complete LP infeasible -------------------------------> Empty
  -> complete LP bound >= verified cutoff ----------------> Fathomed
  -> complete LP-bounded Open
       -> another leaf is now lower -----------------------> requeued Open
       -> next strict frontier exists
            -> native optimal -----------------------------> Closed
            -> native infeasible --------------------------> Empty
            -> target reached + valid dual bound ----------> requeued Open
            -> deadline -----------------------------------> deadline-open
       -> no unused strict-frontier milestone
            -> complete left and right child LP lookahead
                 -> child infeasible or normalized gain >= .01
                      -> atomic parent replacement --------> Replaced + children
                 -> small positive gain
                      -> child-bound native target
                           -> exact native closure ---------> Closed/Empty
                           -> target reached ---------------> requeued Open
                           -> deadline ---------------------> deadline-open
                 -> no strict gain
                      -> exact terminal parent MIP
                           -> native optimal ---------------> Closed
                           -> native infeasible ------------> Empty
                           -> deadline ---------------------> deadline-open
            -> geometry terminal
                 -> exact terminal parent MIP -------------> Closed/Empty/open
```

## Scheduler pseudocode

```text
U <- objective of independently verified startup incumbent
cover improving Gini range with four adjacent Open leaves
give each leaf a valid base bound and cutoff U

while an open relevant leaf exists and process deadline remains:
    C <- leaves at minimum valid bound (within certificate tolerance)
    I <- next leaf in deterministic rotating tie order

    if I has no complete LP:
        solve its exact interval LP to terminal validity
        if infeasible: mark I Empty; continue
        merge LP bound by max
    if b[I] >= U - tolerance:
        mark I Fathomed; continue

    if some other relevant bound < b[I] - tolerance:
        requeue I without native work; continue

    t <- smallest other relevant bound > b[I] + tolerance
    if I has not reached a frontier milestone and t exists:
        launch native MIP with launch-frozen target t
        merge every validity-gated native dual bound
        if native optimal/infeasible: close I exactly; continue
        if target reached: remember milestone; requeue I; continue
        if deadline: leave I open; stop

    if midpoint split is structurally eligible:
        construct both exact child interval models
        solve both child LPs completely before exposing children
        evaluate current normalized child-disjunction gain
        if child infeasible or normalized gain >= 0.01:
            atomically replace I with the two covering children
            close any LP-infeasible child; continue
        if gain is positive but below 0.01:
            launch native target at the child-disjunction bound
            merge valid bound
            if native optimal/infeasible: close I exactly; continue
            if target reached: retain child LP cache; requeue I; continue
            if deadline: leave I open; stop
        discard speculative children when gain is not strict

    launch the one exact terminal MIP for I
    merge a validity-gated final bound
    independently verify any improving native incumbent and tighten U
    close I only on native optimality or infeasibility
    on deadline, leave I open and stop

recompute final incumbent with original verifier
audit coverage, bound monotonicity, lifecycle, and all relevant closures
certify only if the complete certificate gate accepts
```

## Next-strict-frontier target

For the selected leaf \(I\), define other open-relevant bounds
\({\cal B}_{-I}\). At the instant of launch,

\[
  t_I=\min\{b\in{\cal B}_{-I}:b>b_I+10^{-7}\}.
\]

If the set is empty, C6 proceeds to lazy child lookahead. If a member of
\({\cal B}_{-I}\) is already below \(b_I-10^{-7}\), the selection is stale
and \(I\) is simply requeued. Once a target is launched, \(t_I\) is frozen;
later scheduler changes do not alter it. Target reach makes the leaf no longer
the unique reason the global proof frontier is stuck, but it does not prove
the leaf solved.

## Child decision and re-evaluation

Let a complete child LP be interpreted as \(+\infty\) when infeasible; the
post-split disjunction lower bound is the minimum feasible child bound, never
below the inherited current parent bound. The normalized gain denominator is
the current proof gap \(\max(10^{-7},U-b_I)\), so the decision is re-evaluated
against the latest parent bound after each requeue. A child-bound target may
therefore make a formerly useful split unnecessary. C6 retains the complete
child LP pair for valid lookahead reuse, but does not expose those children
until atomic replacement succeeds.

## Closure and deadline rules

`setStatus` requires a nonempty proof source for `Closed`, `Fathomed`, and
`Empty`. A fathom is rejected if the stored bound is below the cutoff. A split
is rejected unless coverage and inherited bounds are exact. At deadline the
backend is asked to finalize, any already valid dual bound is merged, and the
leaf remains `Open`. Consequently the final leaf ledger can explain every unit
of original improving-range coverage even in a non-certified run.

## Implementation anchors

- Scheduler state and transitions: `include/ControllingLeafScheduler.hpp`,
  `src/ControllingLeafScheduler.cpp`.
- Frontier milestone pure decision: `evaluateC6FrontierDecision`.
- Current child-gain pure decision: `evaluateC6CurrentSplitDecision`.
- Terminal close pure decision: `evaluatePaperTerminalMipDecision`.
- Production loop, ledgers, and certificate assembly:
  `solvePaperExternalGiniTree` in `src/PaperExternalGiniTree.cpp`.
- Geometry: `legacyAdaptiveSplitEligible`, `splitLegacyFrontierInterval`, and
  `exactIntervalCoverage` in the Gini frontier geometry module.
