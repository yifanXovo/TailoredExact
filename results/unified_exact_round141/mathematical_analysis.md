# Threshold-count disjunctions and conditional objective information

This is a problem-specific use of integer cardinality, concave chords and a
standard scalar disjunctive formulation. Neither a binary variable nor the
convex-hull construction is presented as a new general theorem. The new
research question is whether the all-station ratio-count axis and its nested
propagation supply useful proof information beyond the existing Gini axis.
The numerical solver certificates retain the inherited R134 policy; they are
not exact rational LP optimality certificates.

## Exact supported thresholds and integer coverage

Only the n service stations enter the count. For the actual finite supports,
selectors satisfy sum_y s_iy=1 and Y_i=sum_y y s_iy. Interpret the loaded
binary64 ratio coefficient c_i in r_i=c_i Y_i as an exact dyadic number. Let
0=t_0<t_1<...<t_M be the distinct positive supported c_i y, Delta_j=t_j-t_(j-1),
and K_j=sum_i sum_(c_i y>=t_j) s_iy. No tolerance merging or decimal threshold
reconstruction is used. With integer selectors,

\[
A=\sum_{i<l}|r_i-r_l|=\sum_j\Delta_j K_j(n-K_j).
\]

Each pair is counted on exactly the threshold intervals separating its two
ratios. Summing their interval lengths proves the identity. The R140 lower
and upper count bounds use actual supports and the physical inventory budget
max(0,B-sum_k Q_k)<=tau<=B, intersected with supported minima/maxima. The
observed LP tau is never substituted for a physical budget.

Choose an integer pivot ell_j<=m<u_j. The two domains K_j<=m and K_j>=m+1
are mutually exclusive and cover every integer parent solution. Fractional
selector points with m<K_j<m+1 need belong to neither side. An integer K_j
at the parent LP point does not by itself remove the potential to strengthen
its fractional selector extension.

Monotonicity K_h<=K_j for t_h>=t_j gives u_h'=min(u_h,m) on the low side;
K_h>=K_j for t_h<=t_j gives ell_h'=max(ell_h,m+1) on the high side. Other
bounds are inherited. An ell_h'>u_h' is incompatibility, not a range to clamp.
Propagation compares physical thresholds. A frozen threshold need not remain
a member of a later supported threshold grid to define the same count.

## Conditional chords and the retained parent relaxation

For ell<=K<=u,

\[
K(n-K)-[(n-\ell-u)K+\ell u]=(K-\ell)(u-K)\ge0.
\]

The conditional aggregate uses the propagated ranges in the sum over all
thresholds. **The old TC and parent TC2 rows remain present**, and the child
aggregate is appended only to its corresponding count-side model. Integer
count bounds need not constrain every fractional parent point. Consequently
neither replacing the parent row nor copying a conditional row into the
unrestricted parent is justified.

For d=u-ell and m=ell+floor(d/2), each child's interval width is at most
floor(d/2). The selected term's continuous worst-case chord error drops from
Delta*d^2/4 to at most Delta*d^2/16. This is a one-term error bound, not a
fourfold objective, gap or runtime result. Other thresholds may strengthen
through monotonicity, but no additive attribution to full-objective gains is
claimed.

The offline diagnostic maximizes the exact rational weighted remainder at a
saved point, with the lower physical threshold as exact tie-break. The frozen
online implementation evaluates the same score using loaded primal values
and long-double accumulation, retaining the lower threshold on a tie. The
thresholds, membership, count construction and signed coefficient sums use
checked exact dyadic arithmetic; the online score itself is not described as
an exact rational maximization. A significant count-range violation takes
priority and is reported separately. Small out-of-range residuals are not
clipped or used as negative remainder scores. The pivot is uniformly
max(ell,min(u-1,floor(K_star))); no instance-specific pivot choice is used.

## Cutoff complements and two-sided floors

On a count-side improvement model F<=c_i, a qualified LP bound lambda_i
supports the physical side floor beta_i<=min(lambda_i,c_i). For a physical
solution with F<=c_i, its valid exact-G/selector/product extension is in the
source model, so F>=lambda_i. For F>c_i the cutoff complement itself gives
F>=c_i. This completes an objective lower bound, not an extension of the
source support or physical domain.

The inherited numerical floor is max(0,nextafter(min(lambda_i,c_i)-1e-7,-inf)).
Zero follows from objective nonnegativity. This fixed margin is not tuned.
The exact stored coefficients and endpoint guards are algebraic checks on
floating-point proof transport, not rational solver certification.

A qualified infeasible *improvement model* may give the cutoff floor; it does
not establish that the whole physical side is empty. No side is deleted and
no binary is manually fixed on that basis. Standalone diagnostic infeasible
statuses without independent Native qualification are not admitted as floors.
Unknown/limited returns do not supply a primal objective as a lower bound.
For an ordinary incomplete/unknown pair the existing parent proof remains
available; the inherited source-rejection and abandonment policy takes
precedence when evidence dependencies are revoked.

Complete integer coverage supports only

\[
B_{cover}=\min(\beta_0,\beta_1).
\]

Taking the stronger side, a mean, or an AM-selected score would not prove the
parent lower bound.

## D0, D1 and the exact scalar projection

Use one ordinary binary b and the same count links in both models:

\[
K\le m+(u-m)b,\qquad
K\ge\ell+(m+1-\ell)b.
\]

D0 adds F>=min(beta0,beta1). D1 adds

\[
F\ge\beta_0+(\beta_1-\beta_0)b.
\]

At integer b, the links assign the physical integer count to its unique side.
The floor is valid there by the corresponding proof or cutoff complement.
K depends on physical Y, not a virtual auxiliary G. F is the complete linear
objective, including ObjCon. The implementation reuses the R120 directed
objective-endpoint arithmetic with a distinct count-domain proof type; it
does not relax the existing R120/ms2 incompatibility rule.

For fixed K in [ell,u], a fractional b lies in

\[
\max\{0,(K-m)/(u-m)\}\le b\le
\min\{1,(K-\ell)/(m+1-\ell)\}.
\]

If beta1>=beta0, eliminating b gives F>=beta0 and
F>=beta0+(beta1-beta0)*(K-m)/(u-m). If beta0>beta1, it gives F>=beta1 and
F>=beta1+(beta0-beta1)*(m+1-K)/(m+1-ell). Together with ell<=K<=u, these are
the convex hull of the two *scalar interval epigraphs* [ell,m] x [beta0,infty)
and [m+1,u] x [beta1,infty). One can decompose K between the two intervals
exactly when the links hold, while any extra objective slack is vertical.
This is not the full BRP hull and does not imply that Native branches on b.

The exact scalar checks use ell=0,u=4,m=1,beta0=0,beta1=2. The point
(K,F,b)=(2,0,1/3) satisfies D0 but violates D1. The point (2,1,1/2) satisfies
continuous D1, yet no binary D1 extension exists because K=2 forces b=1 and
F>=2. These are scalar witnesses only. In particular, testing a chosen b
without minimizing over its feasible fractional interval is not a projection
separation test.

## Root implementation and evidence lifetime

The research switch is `--round141-count-proof off|d0|d1`, default off. The
separate entry explicitly requires BOTH stock + old TC + TC2. The stable R137
and historical R138/R139/R140 launchers and profiles keep their original bytes.
There is one root selection, after own H and the normal root LP and before
the first original integer request. Existing AM Gini lookahead may precede
installation; the same valid root information may enter a contained child.
Root closure, no admissible nondegenerate count, and incomplete proof pairs
retain the ordinary flow with explicit outcome metadata.

Formal root selector fields are copied from the already-required Native LP
return, bound to its model SHA and persisted separately. The optional R127
CSV is not an algorithm interface. R49 reduction is not enabled. Each count
probe has its own canonical artifact/request/Native call and count scope.
It never becomes a Gini leaf or scheduler proof piece. Original VTypes are
restored under the existing lifecycle contract, then the unique probe model
is discarded immediately; no additional Optimize or probe state reuse occurs.

Count settings bind the exact physical threshold, side, pivot, ratio and
support data and source hashes. Parameter readback preserves this metadata.
Independently recomputed final_inventory selects a witness side. An opposite
side's low-objective witness is not a contradiction; an actual same-side
contradiction revokes the source and dependent proof use. Count-local bounds
are explicitly refused by the global/Gini-cover promotion path. The pure
reader audits every actual call, then supplies only Gini obligations to the
inherited Gini coverage algebra. This is an in-memory view, not a raw edit or
an omission from parameter, quality, physical, matrix or resource checks.

Embedding requires the same input, a contained G interval, nonexpanded source
cutoff and supported-Y subsets. Membership is recomputed from the frozen
threshold on each artifact; no new threshold-array index substitutes for it.
Proof state is reset per solve, including when switching off. Own Start sets
b from independently verified integer inventory. Directed floor endpoints
include ObjCon and handle either sign of beta1-beta0. BranchPriority stays0;
there is no new branching callback, custom stop rule or timed mode switch.
All online construction, LP, validation, installation and ordinary Native
search consume the complete method's original clock.

## Historical boundaries and the return-upper-bound correction

R50/R51 studied variable-family priorities and sparse LP probing. R62 used
single-station service thresholds and vehicle compatibility; R88 used two-site
CDF transport envelopes. R120--R122 already implemented a one-binary Gini-axis
conditional objective floor, with mixed complete performance. This round's
distinction is all-station ratio counts, integer gaps between sides, nested
count propagation and conditional numerator chords. It does not rename any
of those standard disjunctive tools. General arc-load and primal-H redesigns
from R66 and later rounds are not reopened.

The supplied governing goal records an independently checked R138 K35
same-objective numerical witness satisfying both R_k<=Q_k and R_k<=Q_k a_k:
R'=(6.306613194,5.773547225,18.919839581) and
a'=(.324239517,.276789192,.632964241), with about1.82e-12 maximum residual in
23624 rows and10007 bounds. Its recorded source packet SHA is
98176d441008d0263644702b73574f782377b78c5d0541fe092e4086940739c0.
This study treats that supplied witness as superseding the R140 suggestion
to prioritize only return upper bounds. It is not a general heterogeneous-
vehicle symmetry theorem or a rational optimality certificate, and is not
reported as a new Round141 Optimize or newly repeated physical replay. No
return-bound/product complete benchmark is opened on its basis.

Optimized common-domain LP evidence, scalar projection separation and full
complete-method outcomes remain separate claims in the companion tables.
