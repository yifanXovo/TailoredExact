# Proof of exact incremental row inheritance

CPLEX child-local rows and bounds are inherited by all descendants. For each
created Gini child, Round 20 stores the complete canonical row and effective
bound state associated with its native child UID. The state is immutable and
reference-counted. Gini children use copy-on-write only when their interval
adds canonical rows or bounds; ordinary native integer children share the
deepest verified state having the same local Gini bounds. This removes the
Round 19 memory failure caused by copying thousands of coefficient maps into
every open-node record without changing any constraint.

For a complete factory child pack, a row is omitted only when its canonical
signature already maps to an exactly equal normalized row: same variable
coefficients, sense, right-hand side, scope, and dependency metadata. A bound
is omitted only when the same variable, direction, and value is already
effective. Signature collisions with unequal content fail closed. No
coefficient/RHS dominance rule is used; `dominance_omissions` is required to
remain zero.

Let `P` be the inherited constraint set, `C` the complete child factory set,
and `D=C\P` under exact equality. Because constraints in `P` remain active in
the child, `P union D = P union C`. Thus attaching `D` yields exactly the same
child feasible region as attaching the complete pack while retaining inherited
weaker endpoint rows. Stronger endpoint-dependent rows remain in `D` and are
added.

Ordinary CPLEX integer children do not expose their IDs through the custom
branch-creation call. Their inherited canonical state is recovered only from a
previously verified deepest node with exactly the same local Gini bounds. If no
such state exists, the callback fails closed. If equally deep candidates have
different immutable state pointers, the match is ambiguous and the callback
also fails closed. Native parent identity may be recorded as unavailable, but
no constraint state is guessed.
