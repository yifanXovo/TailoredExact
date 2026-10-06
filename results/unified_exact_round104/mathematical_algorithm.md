# Objective certificates and their limits

Let P retain every old row, equality, variable bound and the objective
c^T x+c0. Add a finite valid pool a_j^T x<=b_j. Assume a feasible bounded
minimization LP and exact optimal primal/dual solutions, including the old
constraints and bounds. Only the new <= rows have multipliers lambda_j>=0
(Gurobi Pi_j=-lambda_j in this convention).

Set abar=sum lambda_j a_j and bbar=sum lambda_j b_j. The full-pool optimal
point satisfies abar^T x<=bbar. Consequently the compressed optimum is at
most LC. Weak duality for the original optimal dual certificate supplies
LC as a lower bound on the compressed model: the certificate uses the new
rows only through their nonnegative weighted sum. Keep the old dual terms,
including bounds, free equality multipliers and c0. Thus the compressed
optimum is LC. If every new multiplier is zero, the old certificate already
proves LC and no new row is required. The identical argument retains just
the exactly nonzero dual support (ACTIVE), or several sums partitioning that
support (GROUPED). This is an application of LP duality, not a new theorem.

The feasible sets and future branch bounds need not coincide. With x,y>=0,
minimize x+y and add x>=1,y>=1. The pool optimum is 2 and both multipliers
are one. The aggregate x+y>=2 also has optimum 2. After branching x>=2 the
pool bound is 3 and the aggregate bound is 2. Adding an unrelated binary
variable that implies x>=2 makes this a genuine descendant of a MIP tree.
No objective-bound row is substituted for a structural aggregate.

Every nonnegative combination of valid rows is valid, independent of dual
optimality. Floating Pi and small numerical residuals do not prove rational
dual optimality. The prototype retains every strictly negative new-row Pi
in ACTIVE, without a fitted epsilon; zero and wrong-sign cases are recorded.
The observed F2 ALL solution has twelve tiny positive new-row Pi values
(maximum about1.30e-10). Python repairs these to zero for nonnegative validity.
Its ACTIVE is therefore a repaired floating candidate, not the theorem's
exact nonzero optimal dual support. Each expression is reoptimized. Signed
objective differences must be interpreted with the recorded LP primal/dual
gap and residuals; they are not exact rational equalities.
GROUPED treats binary64 nonnegative multipliers as exact dyadic values and
accumulates products/sums exactly. For submitted coefficients ahat, set
bhat>=bbar+sum max((ahat_i-abar_i)*LB_i,(ahat_i-abar_i)*UB_i), rounding RHS
outward. Bounds must be globally valid and finite wherever the conversion
changes a coefficient. This formula handles both signs. Dropping a tiny
coefficient is a conversion and needs the same compensation. Conversion
overflow or unsupported bounds is a failure/UNKNOWN, never an unsafe row.

Repricing a quantized group direction on the full necessary domain gives a
safe support upper bound h(wbar)<=sum lambda_j h(w_j). Repricing can improve
a finite-pool optimum and is not equivalent compression. A safe upper
support requires the complete support algorithm; an attaining plan alone
only proves a maximum lower bound. Score/dimension failures remain UNKNOWN.
If the full necessary hull was solved exactly, a new valid support cannot
exceed its optimum. R103 within-tolerance closure is numerically qualified
and does not supply those exact premises.

Rows from different model scopes cannot be mixed. The original typed
matrix, old objective, physical Start and full-route witness contract remain
authoritative. Each compressed LP must be reoptimized and its actual signed
objective difference and primal/dual residuals saved. Native point objective
and native global bound are separate. A native LB above LH does not prove
that native cuts imply the necessary domain, or exclude possible synergy.
