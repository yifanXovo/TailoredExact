# C6 exactness invariants

## Scope and authority

This document describes the active `round31-nonblocking-native-bound` path in
`solvePaperExternalGiniTree`. The current source is authoritative. Historical
Round 28--33 documents explain how the path was developed, but they do not
override current code.

C6 minimizes

\[
  F(x)=G(x)+\lambda P(x), \qquad \lambda=0.15,
\]

over the original EBRP feasible set. Here \(G\) is the Gini term and
\(P=\sum_i w_i e_i\) is the weighted absolute-deviation penalty. HGA-TGBC or
the deterministic constructor supplies only a feasible upper bound. It never
supplies a lower bound or an exactness claim.

## I1. Verified-incumbent invariant

Every cutoff \(U\) used by C6 is the objective of a route plan accepted by
`verifySolution`: the plan is feasible for the original problem, its objective
is recomputed from the original variables, its components match, and the error
list is empty. A newly found native incumbent may lower \(U\) only after the
same independent verification.

Consequences:

- \(U\) is always a valid minimization upper bound.
- The improving row \(F\le U-\varepsilon\) cannot remove an unknown solution
  with objective below the verified incumbent.
- A weaker startup incumbent can affect work, but cannot invalidate the exact
  search.

## I2. Exact unresolved-range coverage

The improving Gini range is initially covered by four adjacent intervals.
Every active final leaf owns one closed interval \([\gamma_L,\gamma_U]\).
A parent is marked `Replaced` only inside `splitLeafAtomically`, after at least
two children have passed all of these checks:

1. the first child starts at the parent's lower endpoint;
2. adjacent endpoints coincide within \(10^{-7}\);
3. the last child ends at the parent's upper endpoint;
4. lineage and depth are correct; and
5. every child inherits at least the parent's valid lower bound.

Thus unresolved improving values do not disappear during splitting. A
deadline, partial solve, or failed engineering gate leaves the corresponding
leaf open.

## I3. Valid leaf-bound invariant

For every relevant leaf \(I\), C6 stores a finite lower bound \(b_I\). The only
accepted sources are:

- the complete LP relaxation of the leaf's exact interval model;
- a parent bound inherited by a covering child;
- a complete child LP bound merged with the inherited parent bound;
- a validity-gated Gurobi native MIP dual bound; or
- the dual bound of a complete exact terminal MIP.

The scheduler updates

\[
  b_I \leftarrow \max\{b_I,\widehat b_I\}.
\]

It never replaces a bound by a smaller value. Native bounds are accepted only
after model-identity, zero-gap-parameter round-trip, solver-finalization, and
feasibility-consistency gates pass.

## I4. Global lower-bound invariant

A final leaf is relevant when it is not replaced and
\(\gamma_L<U-10^{-7}\). With \({\cal R}\) the relevant final leaves,

\[
  L = \min_{I\in{\cal R}} b_I.
\]

Closed, empty, or cutoff-fathomed leaves remain represented by valid bounds;
replaced parents are excluded because their children cover them. If no
relevant leaf remains, the scheduler's serialized fallback is zero, while the
certificate separately requires all relevant leaves closed and a valid
verified upper bound. The scheduler audits both leaf-bound and global-bound
monotonicity.

## I5. Complete-LP invariant

A parent or speculative child LP influences a decision only when the backend
reports a terminal valid LP, exact zero-gap settings round-trip, the requested
model fingerprint matches, and the feasibility-consistency gate passes.
Interrupted or otherwise incomplete LPs do not produce a split or closure.

Complete LP infeasibility legally empties the leaf. A complete LP bound at or
above \(U-10^{-7}\) legally cutoff-fathoms the leaf.

## I6. Native-target invariant

A native target is a scheduling milestone, not a proof of leaf closure. During
a target phase, any valid native bound is merged monotonically. If Gurobi
reaches the launch-frozen target and terminates that phase, the parent remains
open and is requeued. Only native optimality or infeasibility, after all
engineering gates pass, closes it.

This is why partial native-MIP termination is exact: the valid dual-bound
improvement is retained, while unresolved interval coverage remains present.

## I7. Current-frontier invariant

For an active leaf with bound \(b_I\), the next-frontier target is the smallest
other relevant open-leaf bound strictly above \(b_I+10^{-7}\). If a different
leaf is now strictly lower, the stale selection is requeued without a native
launch. The target is frozen at launch and contains no elapsed-time, Work,
node, or machine-speed quantity. Tied minimum leaves are rotated in a
deterministic order.

## I8. Child-lookahead and split invariant

Child lookahead occurs only when the active leaf has no unused higher frontier
milestone. Both child LPs complete before either child is exposed to the
scheduler. Let \(b\) be the current parent bound, \(U\) the verified upper
bound, and

\[
  b^+ = \min\{b_L,b_R\}, \qquad
  \eta = \frac{b^+-b}{\max(10^{-7},U-b)}.
\]

The implemented current decision is:

- split immediately if a complete child LP is infeasible;
- split immediately if \(\eta\ge\rho\), with \(\rho=0.01\);
- if \(0<b^+-b\) but \(\eta<\rho\), run a parent native target at \(b^+\),
  merge the bound, and requeue without a forced split; or
- if there is no strict child-disjunction gain, discard the speculative child
  models and launch exact parent closure.

Midpoint children, maximum depth 8, and minimum width \(10^{-4}\) are fixed.
The atomic replacement checks preserve coverage and inherited bounds.

## I9. Legal closure invariant

A relevant leaf can cease being open only through one of these proof events:

- terminal-valid complete LP infeasibility (`Empty`);
- a terminal-valid complete LP bound no smaller than the verified cutoff
  (`Fathomed`);
- engineering-gated native MIP infeasibility (`Empty`); or
- engineering-gated native MIP optimality (`Closed`).

Target attainment, elapsed deadline, child lookahead completion, or a partial
solver status are not closure events.

## I10. Lifecycle invariant

The strict certificate requires a symmetric backend lifecycle: optimize counts
match the classified LP, partial-target, and terminal solves; terminal leaves
match terminal optimizations; all models and environments are released; same
leaf reuse counts agree; integer domains are restored after LP phases; and
there are no hidden fresh restarts, child restarts, or reset calls. C6 claims
same-leaf model-object retention, not LP-basis or native branch-tree reuse.

## I11. Deadline invariant

The primary clock begins at process entry. The global deadline covers parsing,
startup, independent verification, canonical model construction, native
solves, trace generation, and final certification. When time expires, C6
merges only already valid evidence, leaves unresolved leaves open, releases
resources, recomputes the incumbent with the verifier, and reports a
time-limited non-certificate. It does not reinterpret the deadline as proof.

## I12. Strict original-problem certificate

`evaluateExternalGiniTreeCertificate` accepts only when all of the following
hold:

- complete initial coverage;
- valid parent-child coverage;
- every relevant leaf closed;
- all leaf and global bounds valid and monotone;
- verified global upper bound and feasibility consistency;
- lifecycle complete; and
- \(L\ge U-10^{-7}\).

Because the leaves cover every solution that could improve the verified
incumbent, each leaf is either proved empty, proved unable to improve, or
solved exactly, and the final incumbent is independently feasible. Therefore
no original feasible solution has objective below \(U\), and the reported
incumbent is globally optimal within the declared engineering tolerance.

## Round 34 noninterference boundary

Round 34 adds elapsed-time observations to HGA generation logs and an explicit
startup-variant configuration gate. The startup flag is not an argument to
the frontier, split, terminal, scheduler, row-factory, or backend decision
functions. Whole-file and function-body hashes for the frozen components are
recorded in `frozen_c6_equivalence.csv`. `C6-HGA-FULL` remains the default and
still requires the Round 31--33 HGA seed and 2000-generation stagnation rule.
