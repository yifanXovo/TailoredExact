# C6 exact-closure rule

An exact parent closure MIP is launched only when:

1. the parent is structurally terminal; or
2. no unused strictly higher frontier milestone exists and complete child
   LPs have no current strict disjunction gain; or
3. a previously reached child target has caught the cached child bound and
   the current re-evaluation has no strict gain.

The exact closure uses zero relative and absolute MIP gaps. Only native
optimality, native infeasibility, or an independently verified cutoff may
close coverage. A target callback termination, time limit, engineering
shutdown, or other interruption keeps the leaf open.

This rule is finite because each leaf can perform one frontier target and one
child target before closure or split; each split increases depth in a finite
binary geometry.
