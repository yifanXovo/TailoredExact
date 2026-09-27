# Mathematical and attribution boundaries

## Original problem and independent upper bounds

The objective remains
\(Y_i=b_i+\sum_k(d_{ki}-p_{ki}), r_i=Y_i/D_i, S=\sum_i r_i\),
\(H=\sum_{i<j}|r_i-r_j|\), and
\(F=H/(nS)+0.15\sum_i\omega_i|r_i-1|\).
The existing zero-S convention is preserved. Original input weights use
the parser's legacy max-weight-10 normalization when applicable.

Vehicles depart empty, serve each selected station once with a positive
one-direction operation, obey every intermediate capacity bound, and may
return loaded. With station pickups P, station drops D and return load P-D,
handling is c_pick P + c_drop D + c_drop(P-D) = (c_pick+c_drop)P.
It is neither a station-total conservation law nor an empty-return rule.
Travel and this handling cost must fit the original mathematical T.

Simple start is exactly empty routes and Y=b. It is independently checked
and fails explicitly on an input where it is invalid; there is no HGA or
greedy construction fallback. Its verified U enters the same cutoff and
coverage logic as the stable algorithm. It is not a native Gurobi MIP start.
Frozen-state diagnostics use only an independently verified feasible U;
no historical optimum or lower bound is injected.

## Cutoff, decomposition, certificates

The actual current canonical row uses epsilon=0, F<=U. This is a closed
superset of strictly improving solutions. Calling it literally F<=U-epsilon
with positive epsilon would be inaccurate. We preserve this existing row
and the engineering certificate tolerance. A full certificate still needs
a verified original feasible U, a valid lower bound closing the gap, and
complete coverage of the improving Gini interval.

The stable K1 geometry is unchanged: K0=1, midpoint, tau=.08, and
\(\Delta=\max(U-B,\epsilon)\),
\(r_\pm=\operatorname{clip}((B_\pm-B)/\Delta,0,1)\),
\(\mathrm{score}=\tfrac12(r_-+r_+)\min(r_-,r_+)\).
K1-S changes the incumbent-generation input only. Single-S bypasses split
eligibility and the intermediate native-target action; it still pays for
one parent LP and follows the same exact-closure contract. At most one
integer optimization call is permitted, with all LP/MIP evidence on L0.
The analyzer checks that lifecycle rather than inferring it from a preset name.

A restricted diagnostic certificate, callback return, successful attribute
assignment or native optimal status alone is not counted as a full-instance
certificate. Fixed-state lower bounds never flow back to a formal arm.
All new solver behavior is request-local and default off.

## Optional pair support-duration rows

For A={a,b} and c=c_pick+c_drop, use
\[
c(p_{ka}+p_{kb})+t(A)(z_{ka}+z_{kb}-1)\le T.
\]
Compute t(A) as the cheaper depot-a-b-depot or depot-b-a-depot route in the
directed all-pairs shortest-path closure. Nonnegative finite travel times
are required and checked. Any original realized route visiting both
stations can be shortened in this closure, proving travel >=t(A), even
when the original travel matrix violates triangle inequalities.

If both are visited, pair pickup handling is bounded by total handling,
and total handling plus travel <=T proves the row. If at most one is
visited, its travel term is nonpositive and the existing total-operation
budget proves it. Hence the row is redundant for *every integer feasible
solution of the base model*, with no interval, incumbent or subtree
assumption. It is legal as an optional user cut. No necessary product,
objective or routing-feasibility constraint is removed.

For a relaxation satisfying the original operation budget, z_a+z_b<=1
is a necessary-condition rejection: the row cannot be violated. The
offline census applies this cheap filter before evaluation, records raw
and row-scaled violations, and inspects both root and nonroot samples.
The experiment deliberately avoids per-callback enumeration: it creates
the same bounded all-pair set once, as static rows or Lazy=-1 pool entries.
The attribute and count are read back; a failed setup rejects the run.
Lazy=-1 readback proves assignment, not which rows Gurobi later activates.

This is the existing conditional support-duration family with a robust
travel lower bound and matched execution experiment. It is not presented
as a novel inequality. Micro checks cover nonmetric directed distances,
loaded return, and a separately analyzed positive optimum 5/24.

## Native search and observation

MIPFocus=1 is a bounded primal-search policy diagnostic. It preserves all
mathematical rows and default branching, has no probing cost, and submits
no routes, hints or starts. The adapter writes and reads back the requested
parameter and rejects failure. Parameter changes are not a mathematical
contribution. Full in-search BRP candidate construction was considered,
but this adapter has no GRBcbsolution loading/mapping/validation path;
wiring a symbol alone would not safely produce valid route candidates.
The present independent mechanism therefore uses one native search setting.

Monitoring collects at most four optimal MIPNODE_REL vectors: first observed
node-count bands 0, 1–9, 10–99, >=100. Node counts describe processed-node
progress, not a public node identity or a branching decision. All values
are original model coordinates. Sampling overhead is timed separately;
the monitor/control pair also reports its common-budget solver trajectory.
The API exposes neither complete local models, native cut-pool membership,
nor internal branching scores.

Integer Y with fractional inventory bits can still have zprod != G*Y.
Recomputed Gini at a sampled Y is an inventory-only value, not an original
feasible objective unless legal routing/operations are verified. Fractional
route and visit variables can independently obstruct realization. Thus
the census diagnoses representation gaps; it does not uniquely apportion
all weak bounds to Gini or certify a sampled inventory as routable.
Any later structural experiment must confront both product and
inventory-operation-visit consistency, and retain the Round55 major control;
this census alone does not justify rerunning the old full VD-J block.
