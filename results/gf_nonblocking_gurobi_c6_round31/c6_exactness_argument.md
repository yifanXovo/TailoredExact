# C6 engineering-exactness argument

## Coverage

The root improving-Gini range is represented by four exact intervals. A split
uses deterministic binary midpoint children and replaces its parent only
after both complete child LP decisions are available and exact interval
coverage is verified. Replacement is atomic; an unresolved interval never
disappears.

## Bounds

Every relevant leaf begins with a valid inherited lower bound. LP bounds are
used only after terminal-valid optimal LP completion. Partial native bounds
are taken only from Gurobi's valid MIP objective-bound callback/final
attribute behind model-fingerprint, zero-gap, and feasibility gates. Bound
merges are monotone. The reported global lower bound is always the minimum
valid bound over all relevant nonreplaced leaves.

## Open native states

Reaching a next-frontier or child-disjunction target does not prove the leaf.
The parent interval remains relevant and open. Deadline interruption has the
same open semantics. A cached child pair is speculative until atomic
replacement.

## Incumbents and closure

Every incumbent used as a cutoff is independently mapped and verified in the
original problem. Coverage closes only on exact optimality, infeasibility, or
verified cutoff. Partial target status is explicitly rejected by the terminal
decision predicate.

## Termination without a process deadline

For each leaf, the directed state graph permits one parent LP, at most one
next-frontier target, one child-LP pair, at most one child target, and then an
exact closure or atomic split. No target can equal or fall below the current
bound. The split tree has finite depth and minimum width. Hence the number of
states and leaves is finite, and exact native phases eventually close every
remaining leaf.

## Strict certificate

Certification additionally requires root coverage, parent-child coverage,
all relevant leaves closed, finite valid bounds, monotone leaf/global
bounds, an independently verified global upper bound, complete model
lifecycle symmetry, and the feasibility-consistency gate. Failure of any
condition produces a rejected certificate with retained evidence.
