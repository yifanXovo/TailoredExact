# Family C: C6 terminal sibling coalescing

Family C leaves the validated C6 launch geometry, initial LP census,
strict-frontier native-bound targets, requeues, midpoint lookahead, adaptive
splits, incumbent verification, and global bound logic intact. It changes only
integer terminal closure.

## Structural trigger

A leaf becomes `TerminalReady` only after the unchanged C6 logic reaches the
point that would launch its one terminal MIP. If its exact live binary sibling
has not reached that point, the first leaf remains an explicit unresolved
coverage object while the normal open-leaf scheduler progresses. When both
siblings are terminal-ready, their ordered, possibly unequal intervals form one
generalized two-segment Core block. Initial K4 leaves receive deterministic
virtual pair lineage `(L0,L1)` and `(L2,L3)`; adaptive children already carry
real parent IDs and binary child indices.

If a mate is pruned, closed, infeasible, or otherwise ceases to be live, a
pending singleton is deterministically returned to the ordinary terminal path.
No unnecessary union is forced.

## Atomic semantics

The native block is built and validated while both original leaves still
exist. Only a technically valid native outcome permits atomic replacement:
the children become `Coalesced`, and one union leaf with the minimum inherited
child bound replaces them without changing the global lower bound. A native
union bound is merged only into that union object. It is never copied to either
child.

An exact optimum or infeasibility closes the union once. An interrupted block
remains one open unresolved union with its valid native lower bound. Model
construction, fingerprint, parameter, or terminal-status failure reopens the
original leaves and disables that pair's block retry, preserving the ordinary
C6 fallback.

## Uniform refinement

`core-factored` applies exact common-row factoring to every accepted sibling
block. The trigger is unchanged and uses no runtime threshold. Both base and
refined modes are explicit and default-off.
