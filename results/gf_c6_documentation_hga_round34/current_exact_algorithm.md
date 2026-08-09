# Current exact algorithm: frozen C6 tailored Gurobi

## Status, scope, and notation

This is an implementation-grounded description of the validated Gurobi
mainline called C6. The active selector is
`round31-nonblocking-native-bound`; its lifecycle is
`round31-open-native-bounded`. The current source is authoritative when an
older Round 28--33 narrative differs.

C6 solves the original EBRP minimization problem

\[
  z^*=\min_{x\in\mathcal X}
  F(x),\qquad F(x)=G(x)+\lambda P(x),\qquad \lambda=0.15,
\]

where \(\mathcal X\) is the original feasible route/operation set,
\(r_i=Y_i/\widehat Y_i\) is the final-to-target inventory ratio,

\[
  G=\frac{\sum_{i<j}|r_i-r_j|}{V\sum_i r_i},
  \qquad
  P=\sum_iw_i|r_i-1|.
\]

The algorithm decomposes the Gini dimension into exact fixed intervals and
uses complete LP relaxations, validity-gated native Gurobi dual bounds, and
exact terminal MIPs to prove a global bound. A primal heuristic supplies an
upper bound only.

## Frozen active parameters

| Component | Frozen C6-HGA-FULL value |
|---|---|
| incumbent | verified HGA-TGBC, seed 20260626 |
| HGA stop | 2,000 generations without strict global-best improvement |
| initial Gini cover | four adjacent intervals |
| scheduler | deterministic external best bound with rotating ties |
| native milestone | launch-frozen next strict open-leaf bound |
| child lookahead | lazy, two terminal-valid child LPs |
| split statistic | current normalized child-disjunction gain |
| split threshold | \(\rho=0.01\) |
| split geometry | binary midpoint |
| maximum depth | 8 |
| minimum interval width | \(10^{-4}\) |
| certificate tolerance | \(10^{-7}\) |
| row profile | full inherited static strengthened pack, deferred timing |
| exact Gurobi | one thread, Seed 0, presolve off in C6 interval backend, traditional search, zero exact gaps |
| warm/native start | disabled |
| exact-phase local re-decode | disabled |
| primary clock | process entry through final certificate |

Round 34 does not change these settings inside C6-HGA-FULL. Its HGA-LIGHT and
SIMPLE-START arms change only the verified incumbent provider and are research
ablations, not a C6 mainline update.

## End-to-end architecture

### 1. Input and preprocessing

`src/main.cpp` parses the instance and fixed run profile. The parser supplies
station capacities, initial and target inventories, weights, vehicle
capacities, travel metric, handling times, and route duration. General safe
preprocessing derives domains and model metadata. The exact model remains the
original compact EBRP formulation; no sample-specific dispatch is used.

### 2. Primal incumbent construction: heuristic

The frozen mainline runs HGA-TGBC. Individuals are separator encodings of
vehicle station sequences. A compact TGBC decoder assigns operations and
scores the negative original objective. The fixed population, crossover,
mutation, education, survivor, seed, and stagnation rules are described in
`hga_tgbc_current_algorithm.md`.

This phase is heuristic. It need not find \(z^*\), and it creates no valid
lower bound.

### 3. Independent verification

The best sequence is decoded into original `RoutePlan` objects and passed to
`verifySolution` in `src/Evaluator.cpp`. C6 continues only with an incumbent
whose original feasibility and objective recomputation pass with no errors.
Its objective is the initial upper bound \(U\).

The same rule applies to an improving incumbent returned later by Gurobi. This
is the boundary between heuristic/native proposals and proof-valid upper-bound
evidence.

### 4. Improving Gini range

The verified cutoff restricts attention to solutions that can strictly improve
the incumbent. The complete improving Gini range is constructed by the main
driver and passed to `solvePaperExternalGiniTree`. C6 covers it with four
adjacent initial intervals. The coverage flag is part of the strict certificate
gate; C6 cannot certify a partial range.

### 5. Canonical strengthened interval models

For each interval \(I=[\gamma_L,
\gamma_U]\), the shared deterministic writer builds the compact original model
and the static strengthened row pack. Despite its historical location in
`src/CplexBaseline.cpp`, `writeCanonicalCompactModel` is the canonical artifact
writer consumed by Gurobi as well as CPLEX.

The six named global families are inventory conservation, movement
reachability domains, visit-inventory linking, global handling capacity,
support duration, and transfer compatibility. The nine named interval families
are direct Gini cap/floor, interval-tight McCormick, objective-estimator cutoff,
penalty lower-bound closure, Gini spread, required movement, low-Gini centering,
variable-\(S\) centering, and the \(SP\)-product estimator. Exact formulas and
validity arguments appear in `cut_and_strengthening_catalog.md`.

The interval model also receives \(\gamma_L\le G\le\gamma_U\), safe local
domains, and the verified improving row \(F\le U-\varepsilon\). Artifact,
domain, and row signatures bind every backend request to the intended model.

### 6. External best-bound scheduler

Every leaf owns exact Gini coverage and a valid lower bound. A final leaf is
relevant while \(\gamma_L<U-10^{-7}\); an open relevant leaf additionally has
bound below the cutoff. The global proof bound is

\[
  L=\min_{I\in\mathcal R}b_I.
\]

The scheduler selects all open leaves at the minimum bound within tolerance.
Ties are ordered by larger interval width, lower endpoints, upper endpoints,
then leaf ID, and rotated deterministically. Bound updates are max-merges, so a
leaf or global lower bound cannot decrease.

### 7. Complete parent LP

The first processing of a leaf solves its fixed-interval LP to terminal
validity. An incomplete LP cannot drive a decision. Complete LP infeasibility
empties the leaf. Otherwise the LP objective becomes a valid leaf bound. A
complete LP bound at or above the verified cutoff cutoff-fathoms that leaf.

### 8. Parent-native-first milestone processing

For active leaf \(I\), C6 examines the current valid bounds of all other
relevant open leaves. If one is now strictly below \(b_I\), the selection has
become stale and \(I\) is requeued without native work.

Otherwise define the next strict frontier

\[
  t_I=\min\{b_J:J\ne I, b_J>b_I+10^{-7}\}.
\]

If it exists and the current leaf has not already reached such a milestone,
C6 restores integer domains in the same leaf model and asks Gurobi to process
the native MIP until one of three proof-relevant events:

- native optimality/infeasibility closes the leaf exactly;
- a valid dual bound reaches the launch-frozen target, is merged, and the open
  parent is requeued; or
- the global deadline interrupts the phase, leaving the parent open.

The target is parameter-free in the sense relevant here: it depends only on
valid mathematical bounds and the certificate tolerance, not on seconds,
nodes, Work, CPU speed, or memory. It is frozen when launched, so later changes
to other leaves do not silently alter a running target.

### 9. Lazy child lookahead

Child LPs are considered only when the selected leaf has no unused higher
frontier milestone (including the single-leaf/flat-plateau case). C6 forms the
two midpoint interval models and solves both LPs completely before exposing a
child to the scheduler. This speculative pair may be cached for a later
re-evaluation of the same open parent.

Let \(b\) be the current parent bound and

\[
 b^+=\min\{b_L,b_R\},\qquad
 \eta=\frac{b^+-b}{\max(10^{-7},U-b)}.
\]

Infeasible children are handled as infinite disjunct bounds for the split
decision. With current bounds, C6:

- splits immediately on child infeasibility or \(\eta\ge0.01\);
- for a strict but smaller gain, runs a native parent target at \(b^+\), then
  requeues without a mandatory split when the target is reached; or
- with no strict gain, discards speculative child models and launches exact
  closure of the parent.

The “current” qualifier matters: after a native bound improvement, cached
children are re-evaluated against the stronger parent, so a once-useful split
need not remain useful.

### 10. Adaptive atomic splitting

An eligible interval is divided at its midpoint into exactly two children.
Eligibility requires depth below 8 and width above \(10^{-4}\). Before the
parent is replaced, `splitLeafAtomically` verifies child lineage, exact adjacent
endpoint coverage, and inheritance of the parent's latest bound. Only then is
the parent marked `Replaced` and the two children made visible. A complete
LP-infeasible child is immediately marked empty.

Round 32--33 ledgers show that child lookahead and splitting occur in real C6
runs, so this is an active mechanism. Those data do not justify a claim that
every split reduces runtime.

### 11. Exact closure

If geometry is terminal or the child decision finds no useful split milestone,
C6 launches the leaf's exact terminal MIP. The pure terminal decision accepts
closure only after attempted/available/finalized, correct-fingerprint,
zero-gap-round-trip, feasibility-consistency, and terminal-MIP gates pass.
Native optimality marks the leaf `Closed`; native infeasibility marks it
`Empty`. A deadline merges any already valid native bound but leaves the leaf
open.

Target attainment, a partial status, completed lookahead, and elapsed time are
never reinterpreted as exact closure.

### 12. Incumbent updates

A native target or terminal solve may return a better route plan. C6 lowers
\(U\) only after the original verifier passes. The scheduler then tightens all
leaf cutoffs monotonically. The better cutoff can make leaves irrelevant or
fathomable, tighten later interval rows, and change normalized proof gaps; it
does not weaken any stored lower bound.

### 13. Deadline and finalization

The process clock starts before startup. Remaining time is propagated to every
LP, target, and terminal launch. At exhaustion C6 stops launching work,
preserves all unresolved coverage, releases all models/environments, verifies
the final route plan again, records the best valid bounds, and returns a
time-limit result. A time-limit row can be scientifically useful but is not a
strict certificate.

### 14. Original-problem certification

Finalization audits root and parent-child coverage, every relevant leaf's
closure, finite/monotone leaf and global bounds, the independently verified
upper bound, and symmetric backend lifecycle. The certificate is accepted
only when those gates hold and the valid global lower bound meets the verified
upper bound within \(10^{-7}\).

The exactness argument is short. The initial leaves cover every Gini value of
any strict improver. Atomic splitting preserves that cover. Every removed
relevant leaf is proved empty, unable to improve the verified cutoff, or solved
exactly. Every remaining partial/deadline leaf stays represented by a valid
bound and blocks certification. Thus, when all relevant leaves close and
\(L\ge U-10^{-7}\), no original feasible solution improves the independently
verified incumbent.

## Compact C6 pseudocode

```text
read and preprocess original instance
routes <- fixed HGA-TGBC
U <- independently verify routes; reject configuration if no valid seed
R <- complete improving Gini range under U
leaves <- four adjacent intervals covering R

while an open relevant leaf exists and process time remains:
    I <- deterministic rotating best-bound leaf
    complete I's LP if needed; merge valid bound
    close on complete LP infeasibility or legal cutoff fathom

    if another leaf is lower: requeue I
    else if a next strict frontier target exists and is unused:
        run native MIP to launch-frozen target
        merge validity-gated native bound
        close only if native exact; otherwise requeue on target reach
    else if midpoint children are structurally eligible:
        solve both child LPs completely, still hidden from scheduler
        evaluate current normalized child-disjunction gain
        split atomically if infeasible-child or gain >= rho
        else if gain is small positive: run child-bound target and requeue
        else: solve parent exactly
    else:
        solve parent exactly

    independently verify any improving native incumbent and tighten U

verify final routes; audit coverage, bounds, closures, and lifecycle
return strict original-problem certificate only if every gate passes
```

## What is heuristic and what is exact

| Component | Role |
|---|---|
| HGA-TGBC / SIMPLE-START | Heuristic feasible upper-bound provider. No lower bound or certificate. |
| Independent verifier | Exact validation of a proposed original route plan and its objective. |
| Interval coverage and rows | Exact restriction/strengthening of the original model over a Gini subdomain. |
| Complete LPs | Valid lower bounds and safe infeasibility/cutoff decisions. |
| Partial native target | Valid lower-bound harvesting and scheduling only; never closure by itself. |
| Adaptive split | Exact disjunction because children cover the parent atomically. |
| Terminal native MIP | Exact interval closure after engineering gates. |
| Global certificate | Exact original-problem claim after coverage, closure, bound, verifier, and lifecycle gates. |

## Paper-level algorithmic contributions

Relative to a standard one-model compact Gurobi solve, the defensible tailored
components are structural rather than claims of generic novelty:

1. an exact external decomposition of the improving Gini range into
   strengthened canonical interval models with auditable coverage;
2. a deterministic best-bound scheduler whose native milestones are the next
   strict mathematical proof frontier, enabling valid partial Gurobi dual-bound
   harvesting without blocking indefinitely on one leaf;
3. lazy two-child LP lookahead with a normalized current disjunction-gain rule,
   child-bound milestones, and no forced split after the parent catches up;
4. adaptive, exactly covering midpoint refinement with monotone inherited
   bounds and atomic parent replacement;
5. explicit separation of heuristic upper-bound construction from independent
   verification, exact lower-bound accounting, and a multi-gate
   original-problem certificate; and
6. a static global/interval strengthening pack whose formulas, scopes,
   signatures, and source boundaries are auditable.

The repository evidence supports that these mechanisms are implemented and
active and that C6 has same-solver advantages on many tested instances. It does
not by itself establish novelty for each individual inequality, universal
runtime dominance, or native tree reuse across leaves.

## Companion audit documents

- `exactness_invariants.md`: proof obligations and nonclosure rules.
- `c6_state_machine.md`: states, transitions, ordering, and pseudocode.
- `cut_and_strengthening_catalog.md`: formulas and validity of 15 families.
- `hga_tgbc_current_algorithm.md`: current heuristic implementation and
  future-only variants.
- `algorithm_source_map.md`: paper concept to source/function map.
