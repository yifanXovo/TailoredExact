# Exactness argument for the Round 27 LP-event tree

Let the root Gini interval be the complete improving range \(I\), and let each
active leaf \(i\) represent the unchanged F0 mixed-integer formulation
restricted to interval \(I_i\). The four initial closed intervals cover \(I\)
without a gap. Every midpoint split replaces \(I_i\) atomically by two child
intervals whose union is exactly \(I_i\); no partial replacement is visible to
the scheduler.

The complete LP relaxation of a leaf is a relaxation of that leaf's complete
integer feasible set. An optimal LP objective is therefore a valid lower bound
for every feasible integer solution in the interval, and LP infeasibility
proves integer infeasibility. Each child starts with the maximum of its own LP
bound and all inherited valid parent bounds, so lower-bound validity and
monotonicity are preserved.

When both child LPs have terminal-valid statuses, C2 splits only if a child is
LP-infeasible or if the minimum bound among feasible children is strictly above
the parent LP bound by more than the existing certificate tolerance. This
criterion affects only the partition. If it is false, C2 does not prune the
parent: it solves the parent's complete original interval MIP. Thus a decision
not to split cannot remove any feasible solution.

Each terminal leaf MIP is launched at most once and runs until native
optimality, native infeasibility, or the remaining overall benchmark deadline.
Optimality or infeasibility closes the leaf. An interruption leaves the leaf
open and stops the entire external algorithm, so no partial MIP result is used
as an integer certificate and no other leaf is selected afterward.

At every observable scheduler state, the relevant leaves still form a complete
partition of \(I\), and the global lower bound is the minimum valid bound over
those leaves. Strict certification additionally requires exact root and
parent/child coverage, all leaf and global-bound validity/monotonicity gates,
an independently verified incumbent, complete resource lifecycle, and every
relevant leaf closed. Consequently neither LP lookahead nor deadline
interruption can create a false exact certificate.
