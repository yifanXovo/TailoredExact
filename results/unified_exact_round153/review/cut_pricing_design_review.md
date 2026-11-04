# Independent design review: resource-relaxed cut price lower

Reviewer: `/root/independent_review`, 2026-11-04 (Asia/Shanghai).

Decision: **ACCEPT_DESIGN_FOR_IMPLEMENTATION_AND_SMALL_QUALIFICATION**.
The proposed construction is a valid offline price lower when implemented
with the exact arithmetic and evidence conditions below. A real-role probe
requires the new interface's static review and small qualification first.
No change to frozen production or substitution for queued deepening is
admitted by this design review. No computation, solver, enumeration,
compilation or historical evidence replay was run by the reviewer.

## Lagrangian inequality and scope

Write rho_i(y)=Fraction(actual_binary64_c_i)*y,
S=sum rho_i(Y_i), T=sum Y_i and A=sum_(i<j)|rho_i-rho_j|. The true Gini is
A/(nS) on S>0. Fix a positive slice [l,h], beta>=0, p,r real and eta>=0.
Every original feasible stock in that slice satisfies

`beta*f(Y) >= beta*A(Y)/(n*h)`,

and each of the following is nonpositive:

`p*T - max(p*Bminus,p*B)`,

`r*S - max(r*l,r*h)`,

`eta*(A - n*gamma_U*S)`.

Consequently the proposed price lower is correct, with

`alpha = beta/(n*h) + eta >= 0`,

`u_i(y) = d_i(y) + p*y + (r - eta*n*gamma_U)*rho_i(y)`,

`C = -max(p*Bminus,p*B) - max(r*l,r*h)`.

For every feasible stock in the slice, its true price is at least
`E(Y)=C+alpha*A(Y)+sum u_i(Y_i)`, which is at least the minimum of E over
the full Cartesian product of station states. Including zero, other S
values, hard-total violations and G-cap violations in this inner minimum
is a relaxation, not a scope error. Such an inner minimizer is not thereby
a feasible stock or a price upper. Only the original exact stock validator
may qualify it as an upper or a new inventory column.

The existing hard-total DP lower `beta*gamma_L + min_hard-T sum d` remains
valid and must be retained. There is no division by beta: beta=0, eta=0,
negative prices and arbitrary signs of p/r are all covered. Use exact
positive slice endpoints and actual support coefficients, not rounded
nominal ratios. Each input state remains available; do not replace full
supports with an existing stock pool.

## Ordered thresholds and the graph

Represent each station label by nested threshold bits z. For an ordered
support, any unary table is exactly a base constant plus successive
differences times threshold bits. For each pair, merge its exact ratio
breakpoints (including zero where appropriate), and use

`|rho_i-rho_j| = sum_k delta_k * |z_i(k)-z_j(k)|`.

The width is the next breakpoint minus the current one; there is no final
extra interval. Merge coincident breakpoints, not distinct original state
labels. Thresholds below or above an entire support are constants 1 or 0,
and their pair terms fold into unary terms or the constant. Retain full
unary label choices even if a ratio representation has repeated values.

With z=1 on the source side, each nonnegative pair coefficient uses two
directed arcs of that capacity. A residual reverse arc initialized at zero
is not the second original pair arc. An integer unary a*z uses node-to-sink
capacity a when a>=0; when a<0 it uses source-to-node capacity -a and adds
a to the constant. Nested bits require high-threshold to low-threshold
arcs. A finite sufficient chain capacity is

`M = 1 + sum(all non-chain capacities)`.

Every monotone cut costs at most that non-chain sum, whereas a cut that
breaks a chain costs at least M. This proves the minimum cut represents a
valid ordered label without a floating-point infinity. Use arbitrary-size
integers, or explicitly prove all capacity/flow totals fit the chosen
integer type. The existing double-capacity Dinic implementation is not
an exact integer certificate engine.

## Integer rounding and the independent certificate

Freeze a positive integer scale N. First form the exact rational energy
in its constant, unary-bit and nonnegative pair-disagreement terms. Then
replace each coefficient q with floor(N*q). Every binary monomial is
nonnegative, so the resulting integer energy divided by N is pointwise
no larger than E. Negative unary and constant coefficients require true
mathematical floor: conversion by truncation toward zero is unsafe.
Terminal conversion and constant offsets after rounding must be exact.
Repeated coefficients should be accumulated exactly before conversion.

Only a verified feasible flow supplies the desired lower direction.
Given the final graph offset C_int and a feasible integer flow of value v,

`(C_int + v)/N <= min_cut_energy/N <= min_Y E(Y)`.

A cut by itself is an upper on the graph minimum, not a lower. An
independent checker must reconstruct the capacities from scope, exact
direction, slice, parameters and scale; check every original arc's
capacity, integer flow and conservation; and recompute the source/sink
flow value. It must distinguish real antiparallel arcs from residual
reverse arcs. Recompute the saved cut's capacity and verify source/sink
membership. Equality of flow and cut proves the integer graph optimum;
chain satisfaction then gives an exact rounded-energy minimizer. A
nonmaximum feasible flow is still a safe lower, but not an optimality
claim. Never trust a saved scalar `flow_value` or solver cut value alone.

This chain is an exact rational lower for the declared actual-coefficient
price problem; it does not need the Native numerical guard for this new
bound. The surrounding Q/RMP numerical-primal policy is unchanged. Retain
the rational lower and convert outward only when a float is required.
For scale selection, a simple rounding-loss bound is fewer than
`(1 + number_of_unary_terms + number_of_pair_terms)/N` original units,
when those are the coefficients rounded once. This is a diagnostic bound,
not a reason to truncate signed coefficients unsafely.

## Candidate selection and full-domain aggregation

A box on p,r,eta is allowed solely for selecting candidates. It does not
restrict the original inventory domain and does not prove that the best
Lagrangian lower has been found. Each accepted parameter must have eta>=0
exactly, with beta/d/scope still equal to the saved direction. Any bundle
LP objective, status or multiplier is merely a selector until its resulting
candidate passes the integer flow certificate.

If bundle planes come from sampled label assignments, evaluate their
unrounded exact Lagrangian energy. Such planes bound the inner minimum
from above even if the assignment is not an exact inner minimizer. The
rounded-cut minimizer need not minimize the unrounded energy, so it must
not be advertised as an exact unrounded supergradient without an error
argument. If a Native LP selects parameters, record its Optimize calls and
cost: the experiment may have zero Native MIP calls while having Native LP
calls. All selection, graph construction, flow and verification costs are
inside the new metered outer process.

For each slice take the maximum of its proved candidate lowers and any
applicable already-qualified lower. The rational closed slices must cover
the complete positive S range. Unvisited or unresolved slices retain the
safe DP lower; an empty-looking slice is not discarded without a proof.
Take the minimum across all slices and a separately qualified legal-zero
value, then the maximum with the full-domain DP and previous qualified
same-direction full lower. The zero value is
`beta*gamma_L + sum_i d_i(0)`. The original zero-only case needs no division
by S. Complete-domain status requires this entire cover, not merely the
best slice or the best candidate.

The final price audit needs a dedicated exact-cut evidence branch. Its
existing no-Native default accepts only the DP fallback; do not weaken
that default globally. The new branch should verify the saved winning
flow/cut for every slice, all coverage and direction bindings, and the
max/min aggregation. It need not rerun max-flow or the candidate search.
The original C_Q/aK certificate and its single full-price correction are
then reused unchanged.

## Minimal meaningful qualification

Use a few existing small domains, including a legal zero and a G cap that
excludes a cheap Cartesian minimizer. The new checks should enumerate the
full Cartesian label product for the graph-energy identity, not only the
already resource-feasible stock list. For each selected small candidate:

1. Verify exact unary/CDF energy equality for every label assignment,
   pointwise downward rounding, and the independently checked flow=cut
   value against the rounded-energy enumeration.
2. For each positive slice, check the certified lower against every
   original feasible stock in that slice, then compare the assembled
   full-domain lower and a truly feasible upper with the exact true minimum.
3. Include beta=0, positive beta, signed unary values and both signs of
   p/r, eta>0, constant tails, shared breakpoints and endpoint overlap.
   A deliberately altered capacity/conservation record should fail the
   independent integer checker.

These are interface checks, not a broad performance campaign. After code
review and PASS, the proposed finite NC20 and K35 comparisons on their
already bound saved directions, up to 16 slices and 20 candidates per
slice, are reasonable probes of the observed pricing bottleneck. Keep
prior valid bounds and all legal stocks, charge every new computation,
and preserve the queued long-price and zero-center studies. A useful
probe would justify a separate decision about further research use;
neither this design nor a small PASS admits production changes.

## Historical boundary

R88's `round88_ot_math.py` and `round88_ot_epigraph.py` already supply the
merged-threshold absolute-CDF identity. R54's `InventoryRouteCuts.cpp`
and R63's `Round63TimeResource.cpp` already use maximum-closure/min-cut
separation via `include/DeterministicDinic.hpp`. Their current engine has
double capacities and a `1e-12` residual tolerance, so its output cannot
be relabeled as the new exact integer flow certificate.

The light search of current round scripts and mainline indices found no
existing implementation of this particular resource-relaxed Gini price
bound. That is not an exhaustive all-history novelty result. The proposed
combination uses classical Lagrangian relaxation and ordered-label cut
optimization; it is a new application path in this study, not a new general
CDF identity, graph-cut theorem or complete inventory hull. The R88/R89
limits and the current unsuccessful Native CDF probes remain in the record.

## Concrete implementation gate

Decision: **ACCEPT_FOR_SERIAL_SMALL_INTERFACE_QUALIFICATION**.
Inspected source identities are:

- `round153_graphcut.py` SHA256
  `6cb2fa990c259e15d5faf696c4626f1c86165dbef55489de3ab9a72f3ca986c4`.
- `round153_refine.py` SHA256
  `2b639cc0df99adcc41f644633694978361adf7b7b9f3d7223fc8795ae16d136e`.
- `round153_audit.py` SHA256
  `79551481340f7c268ecf3147e8e2662aecdf15d0e40d6c996bec6626b8a4ae8b`.
- `round153_reports.py` SHA256
  `dc2db48ad5563d31eb057daae55fb94d7761e253a89b916570d07536f47c1866`.

The source was read statically. No Python parser, import, enumeration,
max-flow, LP, Native model read or compilation was executed by this
reviewer. No syntax problem was apparent by inspection; executed syntax
and interface qualification remain part of the pending paid control.

`Thresholds` preserves every sorted distinct station state, uses exact
products of positive c and integer y, and maps a merged ratio threshold
to the correct `Y > threshold` label bit. Constant tails, unary differences
and pair widths have the required signs. The current recorded hard totals
and state supports are integers, so the network construction remains in
Fraction/integer arithmetic. Mathematical floor is used even for negative
coefficients, with exact terminal offsets. Two original pair arcs are
distinct from the residual reverse arcs. Chain capacity is one plus the
total non-chain capacity. The Python-integer Dinic uses integer residuals;
its independent verifier checks unique arc identifiers, integral positive
flows, capacities, all conservation equations, source/sink value, cut
membership and exact flow/cut equality below the chain capacity. The
reconstructed ordered label is checked against the saved one.

The candidate LP only returns finite proposed p/r and a nonnegative eta.
It uses sampled labels' true energy planes and the two resource support
functions. Its coefficients and stop comparison may be numerical because
no LP objective or status becomes a price lower or upper. Every accepted
lower comes from the separately reconstructed integer flow. The selector
box appears nowhere in the inventory domain or flow validity argument.

`GraphOracle` starts all slices at the exact hard-total DP fallback, saves
each completed flow proof and selects its greatest lower, and includes the
separate legal zero. Unvisited slices remain covered by DP. Its exact
DP/feasible-stock equality early exit is valid. Every graph label is passed
through the original stock validator before it can enter `stocks` or the
inventory upper. All full-domain max/min directions are correct.

The graph audit independently reconstructs every saved network, verifies
its integer proof, binds source/core SHA values, rechecks rational coverage
and zero/DP, and recomputes the winning slice and full-domain lowers. It
also binds candidate-LP call/model/return metadata without replaying an
Optimize. The generic price audit still performs its true-stock upper
checks. Only the explicit graph branch bypasses the old no-Native=DP
fallback rule. Refinement requires a passing graph qualification with
matching source/core hashes and retains the old Q/scope/direction and
single-correction checks.

Two review corrections were applied before qualification: the tamper
test now uses `arc_index` instead of overwriting the outer slice index,
and the full Cartesian loop explicitly equates the unrounded threshold A
representation to the direct pairwise absolute sum before its rounding
checks. The standalone graph audit now checks beta>=0, and bound metadata
comparison normalizes JSON keys. Reports distinguish candidate LP calls
from full-price calls, add total Native calls, and label the new lower as
exact integer flow plus exact DP rather than a guarded Native price bound.

The pending qualifier covers three small domains with signed prices,
beta zero/positive, fixed and gapped supports, legal zero, multiple p/r/eta
sign cases, all Cartesian label energies and feasible-slice inequalities.
It compares the complete true minimum and rejects three altered flow
records. This is an appropriate first-run gate for the actual new interface;
do not run it concurrently with the active long Native price.

After the same-source control passes, the proposed NC20 and K35 saved-
direction probes at 16 positive slices, at most 20 candidates per slice
and 600 seconds of offline search are within the admitted finite design.
Their outer reservations must include construction, selection LPs, flow,
verification and writing; the search cap does not itself preempt an
individual integer max-flow call. Preserve all original research bounds,
queued long-price/zero-center work and the frozen eight-arm plan. A PASS
or a successful probe does not by itself authorize production adoption.
