# Direct state-conditioned Gini deviation rows

Let r_i=c_i Y_i>=0, S=sum_i r_i>0, A=sum_{i<j}|r_i-r_j| and G=A/(nS).
The original epigraph variable satisfies g>=G and the objective remains
g+lambda P, including its original penalty and constant.

For any station set J, the cross-pair contribution gives
A >= |J|S-n sum_{i in J}r_i. Choosing J={i:r_i/S<1/n} and using
sum_i r_i/S=1 yields

    G >= sum_i (1/n-r_i/S)_+ = sum_i (r_i/S-1/n)_+.

This is the classical Gini–Hoover/Pietra relation, not a new general
inequality. See Chen and Hooker, *A guide to formulating fairness in an
optimization model*, Annals of Operations Research 326 (2023), 581–619,
section 4.2, DOI 10.1007/s10479-023-05264-y. The project contribution studied
here is a cheap expression on the existing discrete inventory selectors.

With global bounds 0<Sminus<=S<=Splus, two integer-valid n-scaled rows use
coefficients (1-n*c_i*y/Sminus)_+ and (n*c_i*y/Splus-1)_+, respectively.
Each replaces one selected state's normalized deviation by a valid lower
bound. The following conditional construction tightens those denominators
while retaining the same two original-variable rows.

For each supported state Y_i=y, enclose S by Dminus_iy and Dplus_iy on the
necessary continuous inventory box with the physical total-stock interval
[Bminus,B]. Begin at all support minima, fix Y_i=y, then fill in increasing
c order for the minimum feasible total and decreasing c order for the
maximum feasible total. Positive or zero costs make those totals optimal.
Support holes only enlarge this continuous relaxation. Thus these are exact
box extrema, not claims of exact discrete-support extrema.

Because the low deviation increases with S and the high deviation decreases
with S, valid coefficients in n-scaled rows are

    a_iy=(1-n c_i y/Dminus_iy)_+,
    b_iy=(n c_i y/Dplus_iy-1)_+.
    n g >= sum_iy a_iy s_iy,
    n g >= sum_iy b_iy s_iy.

At an integer point each selected state's conditional bound holds at that
same point. Each term bounds one Hoover deviation; summing is valid. This
does not add independent full-Gini lower bounds. Conditioned domains are
subsets of the global domain, so their ideal coefficients dominate the
global-coefficient construction termwise. Infeasible necessary state boxes
receive zero coefficients; no state-removal mechanism is introduced.

If the whole root domain lacks a proved strictly positive S lower bound,
both rows are omitted, preserving the existing all-zero convention. A
zero c_i with globally positive S gives low coefficient one. Negative or
nonfinite ratios and unsupported exact-arithmetic ranges fail closed.

The production implementation uses existing R140 checked dyadic integers
for actual loaded binary64 c_i, inventory units, water-fill sums, and n*c_i*y.
Denominator lower and upper values are converted outwards. The low row uses
an upward numerator/denominator ratio and downward subtraction; the high
row uses a downward ratio and downward subtraction. Coefficients below
1e-12 are omitted, which only relaxes a row because selectors are nonnegative.
The G coefficient n and the low coefficient of any zero-stock state are
exact. There are at most two rows, no columns and no source optimization.

Root coefficients are generated once per complete run. Only an identical
input SHA, actual ratios and physical stock interval with a subset of the
root selectors can inherit them. Removed selectors have value zero and
their terms are deleted. Expanded support or changed input/ratios/stock is
rejected. The rows do not depend on an objective cutoff or a particular
g interval, so compatible restrictions of those domains need no regeneration.

For z zero-stock stations, zero–positive pairs give A>=zS and hence ng>=z.
This is contained in the low row. In the R145 equal-cost binary-support
family with fixed half/half selectors and stock in [1,n-1], it yields g>=1/2,
attaining the local integer Gini epigraph hull. R145's joint value
(3n-4)/(2n(n-1)) is thereby closed with a general original-variable row.
The earlier strict complementarity theorem remains true; its remaining
gap does not establish a need for a more elaborate joint integer hull.
This local closure is not a claim about the complete routing hull.

The supplied preliminary ZIP was unavailable locally. Independent exact
reconstruction of the four decision-relevant saved points uses the existing
fixed R145/compact carriers and reproduces the supplied values with no
Optimize. K20 joint is separated even with zero zero-stock selector mass.
K35 and RX20 joint optima satisfy both rows with slack, providing same-value
numerical witnesses; those two LP cells are not reoptimized. A violated
saved extension, exclusion of an original point, optimized value increment,
and complete algorithm improvement are reported as distinct evidence levels.
