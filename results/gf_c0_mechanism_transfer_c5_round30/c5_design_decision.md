# C5 design decision

## Evidence-led mechanism selection

The completed C0 audit found 1,386 retained native leaf events. First native
processing produced 44.4888993 summed leaf-bound gain; repeated same-leaf
processing produced only 2.40885584 while consuming more observed Work.
Nevertheless, 307 of 517 repeated events materially improved their leaf
bound. Only 45 of 317 splits had an immediately observed material child gain.
This points to valid partial native-MIP bounds and best-bound interleaving as
the dominant transferable mechanisms, while direct splitting is valuable only
selectively.

C4's dominant limitation is blocking: after complete child lookahead, almost
every strict gain splits and unsplit parents enter a terminal MIP that can
consume the remaining process budget. It lacks an exact intermediate open
state carrying a native MIP bound. It also has no child basis transfer and no
native parent-to-child state continuation.

## Selected primary prototype

The sole prototype is **C5 dual-bound-target delayed split**. It is
algorithmically distinct from S0, C3, and C4.

For each selected parent, C5 obtains the same complete parent and two complete
child LP bounds as C4. Child infeasibility splits immediately. A normalized
child gain of at least `rho=0.01` splits immediately. No strict gain declines
the split and solves the exact parent MIP. A smaller positive gain defines the
mathematical native parent target equal to the post-split child lower bound.
The parent native MIP may stop only when a valid Gurobi MIP dual bound reaches
that target, it closes exactly, is proved infeasible, or the global deadline
interrupts. A target-reached parent is requeued, then split atomically on its
next best-bound selection.

This transfers C0's partial-bound harvesting and interleaving without time
quanta or attempt ordinals. The target is dimensionless in the decision rule
and objective-defined in the backend stop rule.

## Rejected directions

- **Native-root pass:** rejected because the Gurobi MIP callback does not
  expose an unambiguous event proving completion of the full root cut loop.
- **Proof-fraction ladder:** rejected because it adds policy states and can
  resemble an attempt ladder; the observed child bound supplies one direct
  mathematical milestone.
- **Always partial-process before lookahead:** rejected because no defensible
  stopping target exists before a child bound is known.
- **Parent-to-child basis transfer:** rejected for C5 because a complete
  row/column/basis mapping and equivalence proof are absent.
- **Native-tree continuation claim:** rejected; same model-object reuse alone
  is not evidence that Gurobi preserves presolve, cuts, or the search tree
  across callback termination and reoptimization.
- **New inequality family:** rejected because the forensics identify
  scheduling/blocking, not a missing coherent relaxation family, as the
  primary transferable issue.

No fallback prototype is used because the primary passed callback termination,
valid-bound merge, lifecycle, coverage, and Moderate4301 mechanical gates.

## State machine

`OPEN_UNBOUNDED` becomes `OPEN_LP_BOUNDED` after a complete valid parent LP.
An ineligible leaf becomes `TERMINAL_MIP`. An eligible leaf enters
`CHILD_LOOKAHEAD`, retaining the parent coverage while both children are
speculative. A decision then transitions to:

- `ATOMIC_SPLIT` for infeasibility or normalized gain at least `rho`;
- `TERMINAL_MIP` for no strict gain;
- `PARENT_BOUND_TARGET_MIP` for a small positive gain.

The target phase transitions to `CLOSED`, `EMPTY`,
`OPEN_SPLIT_PENDING`, or `OPEN_INTERRUPTED`. `OPEN_SPLIT_PENDING` remains in
the best-bound scheduler and becomes `ATOMIC_SPLIT` only on reselection.

## Frozen choices and expected mechanism

`rho=0.01`, tolerance `1e-7`, four initial intervals, binary midpoint
geometry, depth 8, minimum width `1e-4`, one solver thread, Gurobi seed zero,
and the Round 29 static F0 row pack are uniform. No threshold sweep was
performed. The expected benefit is an early valid native bound followed by
interleaving when a split's mathematical benefit is positive but small,
without spending the full run in one terminal parent MIP.

## Risks and fail-closed behavior

Gurobi may restart presolve/root work on reoptimization, so performance can
remain mixed. A target may never be reached before the overall deadline.
Child lookahead itself can be overhead. Any missing final dual bound,
unsupported status, callback failure, model fingerprint mismatch, invalid LP,
coverage failure, or verifier failure becomes a hard failure; the leaf is
never silently removed and no strict certificate is issued.
