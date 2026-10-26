# Conditional representation question — algebra only, no new model or run

The sustained goal permits replacing the decomposition when evidence warrants
it. This note preserves a possible alternative to investigate only after the
frozen long results. It is separate from the local-descent startup draft.

## Historical and literature scope

The repository's reference/equity_brp_tailored_exact_interim_report.tex already
describes t=1/S with binary-inventory products. Its early Python/HiGHS record
reports a negative partial result on V12_M1_average; it is not a paired result
for the current Gurobi build. The later formulation snapshot's
alternative_formulation_rejection_notes.csv lists unproved integrality and
denominator equivalence as the reason for excluding that implementation.
The old docs/official_benchmark_scope.md describes a CPLEX-era benchmark rule;
it does not replace this task's current original P-GRB contract. No historical
record is rewritten, and no alternative replaces the official baseline.

The scaling idea itself is classical, as documented by
[Charnes and Cooper (1962)](https://onlinelibrary.wiley.com/doi/10.1002/nav.3800090303).
The publisher's bibliographic record was checked; this note does not claim a
new general fractional transformation. The algebra below is a proposed
BRP-specific extension to audit, not an already qualified implementation.

## Prospective exact-value lifting

Keep every original route, operation, load and inventory constraint. For each
station with positive integral D_i and finite integral inventory domain
0<=Y_i<=C_i, use binary one-hot selectors d_iy, with sum_y d_iy=1 and
Y_i=sum_y y*d_iy. Do not scale the original integer or route variables.
Let binary z identify positive total final inventory. Because inventory is integral,

    z <= sum_i Y_i <= (sum_i C_i)*z.

If S_max is a valid upper bound on sum_i Y_i/D_i and is positive, use
z/S_max <= t <= D_max*z, where D_max=max_i D_i. Positive inventory implies
S>=1/D_max, so the upper bound is finite and valid. Any proved S_max=0 case
(including all-zero capacity or zero available stock) fixes z=t=0 algebraically,
without division by zero.

For each selector set a_iy=t*d_iy using the exact binary-continuous envelope
with global bounds 0<=t<=D_max:

    0 <= a_iy <= D_max*d_iy,
    a_iy <= t,
    a_iy >= t-D_max*(1-d_iy).

Define u_i=sum_y (y/D_i)*a_iy and impose sum_i u_i=z. Introduce
e_ij>=u_i-u_j and e_ij>=u_j-u_i, and minimize

    (1/n)*sum_{i<j} e_ij + lambda*sum_{i,y} w_i*abs(y/D_i-1)*d_iy.

At integral selectors and z=1, a=t*d, normalization gives t*S=1, and the
minimum epigraph extension equals H/(n*S)+lambda*P. At z=0, inventory and t
are zero, hence u=0 and the minimum epigraph extension gives the original
S=0 Gini convention and its unchanged penalty. Conversely, every feasible
physical solution has such an extension with identical objective. Epigraph
slack can overstate a nonoptimal model incumbent; optimal values coincide,
and returned routes still require independent physical objective evaluation.

This is a finite MILP lifting in exact arithmetic. It is not a strict rational
certificate from a floating-point solver, a proof of faster search, or a claim
that the previous unqualified implementation is repaired by this note.

## Structural bounds and open questions

Empty departure and loaded return give max(0,B-sum_k Q_k)<=sum_i Y_i<=B,
where B=sum_i b_i. Continuous allocation over inventory bounds gives valid
S extrema and can tighten t bounds on the positive branch. If the lower
stock bound is positive, z can be fixed to1 by mathematics. Otherwise the
zero branch must remain unless separately proved impossible. No instance ID,
known optimum, elapsed time or Work threshold enters these rules.

A research implementation would replace the previous Gini product block,
not stack duplicate formulations without explaining their roles. It needs
complete checks for inherited cuts, all supported weight/domain cases,
the S=0 branch, loaded return, full-vector native Starts and all bound scopes.
The unchanged original P-GRB remains the primary comparison. Any direct
single-MIP candidate also needs to retain the important K1 protection roles.
No proof that its LP projection is stronger than VD-S is asserted here.
The tighter denominator bounds and one-hot representation differ from the
old binary-scaling record, but only a bounded qualified study can establish
whether that difference matters. No such experiment has been opened.
