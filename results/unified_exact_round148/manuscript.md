# Shared total in state-conditioned low Gini deviations

Let r_i=c_i Y_i>=0, S=sum_i r_i>0, and
G=sum_{i<j}|r_i-r_j|/(n S). The physical objective remains g+lambda P,
with g>=G. All statements below concern the original integer feasible
set and its epigraph, including nonminimal g. They do not change routing,
physical time, penalty, Start or R134 numerical proof policy.

## Validity and finite oracle

The Gini–Hoover inequality gives

    G >= sum_i (1/n-r_i/S)_+.

For a selected state Y_i=y, the previously qualified necessary conditional
inventory/support bounds give 0<D^-_iy<=S<=D^+_iy. For any finite b_i,
shared by every state at station i, put

    phi_iy(t)=(1/n-c_i*y/t)_+,
    alpha_iy(b_i)=min_{D^-_iy<=t<=D^+_iy}(phi_iy(t)-b_i*t).

At any integer feasible point the selected state's deviation is at least
alpha_iy(b_i)+b_i*S. One-hot summation and then Gini–Hoover prove

    g >= sum_{i,y} alpha_iy(b_i) s_iy + (sum_i b_i) sum_j c_j Y_j.    (A)

Using Y_j=sum_y y*s_jy yields the exactly equivalent selector form

    g >= sum_{i,y} [alpha_iy(b_i)+(sum_j b_j)c_i*y] s_iy.            (B)

The beta contribution in (B) uses the sum of all station slopes, not
only b_i. A slope chosen separately for each state would not justify
(A). Negative intercepts and final RHS coefficients are legitimate.
Their omission toward zero can invalidate the row. A lower bound on G
also holds for every larger epigraph value g; Start does not require
g to equal the physical Gini value.

On t<=n*c_i*y, phi=0. On the remaining segment phi=1/n-c_i*y/t,
whose second derivative is -2*c_i*y/t^3<=0. After subtracting a linear
term, each segment is affine or concave. Hence the minimum is attained
at one of D^-, D^+, and the kink n*c_i*y when it lies in the interval.
Zero-stock and fixed intervals require no exception to this argument.
The high-deviation function is different and can have an interior
minimum after subtracting a linear term; this three-node oracle is
**low-only**. The old high GD row remains unchanged.

At a fractional point, Sbar=sum_i c_i*Ybar_i. For each station maximize

    H_i(b)=b*Sbar+sum_y sbar_iy*min_{t in T_iy}(phi_iy(t)-b*t).

For nonnegative state masses this is piecewise-linear concave. Its
breakpoints occur among secant slopes between the at most three nodes
of a state. Enumerating their union and zero finds a maximum whenever

    sum_y D^-_iy*sbar_iy <= Sbar <= sum_y D^+_iy*sbar_iy.            (C)

These conditions control both outer rays. Their failure means a missing
conditional first-moment consistency inequality, not infinite Gini
improvement. Each inequality in (C) is itself valid on the original
integer set. A uniformly selected finite moment row is a valid fallback.
At all five original diagnostic points (C) holds exactly for their actual
binary64 values interpreted as rationals. Subsequent finite candidate
rows need not be exact maximizers to remain valid.

## Local convexification, scope and strictness

For fixed station masses and a common first moment S, introduce node
weights lambda_iyk>=0 with sum_k lambda_iyk=s_iy and
sum_yk t_iyk*lambda_iyk=S. The minimum of
sum_yk phi_iy(t_iyk)*lambda_iyk is the station's lower convex envelope.
Concavity on each segment permits replacing any interior mass by
endpoint mass with the same mean and no greater cost. The finite
node LP dual is sup_b H_i(b). Independent station duals then sum to
the full family (A). This is a standard convexification/duality argument
applied to the project-specific conditional deviation block.

The family preserves the same S as a first moment in each station's
conditional mixture. It does not impose a common joint atomic
distribution across all stations, and does not describe the full routing
or integer-objective hull. Setting every b_i=0 recovers ideal low GD.
One nonzero-slope row alone need not dominate old GD everywhere;
retaining both old GD rows makes the finite appended relaxation
monotone in exact mathematics.

For n=2, c_1=c_2=1, support {1,2}, and total interval [2,4], state 1
has conditional interval [2,3] and state 2 has [3,4]. All old high/low
GD coefficients vanish. With a=s_11, d=s_21, S=4-a-d, station slopes
(1/6,0) give alpha_11=-1/3, alpha_12=-2/3, and alpha_21=alpha_22=0.
Thus (A) becomes g>=(a-d)/6. Exchanging stations yields g>=|a-d|/6.
At a=1/2,d=0 the lower bound is 1/12>0. All four integer points and
nonminimal epigraph values satisfy these rows. This proves strictness
relative to the isolated old GD block, including the positive-S/zero-GD
eligibility boundary. It is also the familiar two-station optimal
coupling bound, and is not a claim of superiority to R88 pair-CDF.

## Actual finite implementation

The diagnostic oracle uses exact Fractions of the saved binary64
ratios, conditional endpoints and primal point. Its single appended
row is transported by rounding every final selector RHS coefficient
downward. Since selectors are nonnegative this weakens the row.
For any nonzero coefficient of magnitude below 1e-12, use -1e-12,
including originally positive tiny coefficients. This prevents Native
tiny-coefficient erasure while preserving the direction. Exact zeros
are omitted. Bounds s<=1 give a sum-of-coefficient-loss upper bound.

Production selects finite binary64 slopes from approximate secants.
After fixing those actual values, binary64 outward intervals enclose
every endpoint deviation, intercept, possible kink, slope sum and
final RHS coefficient. An uncertain kink is conservatively included;
adding an extra point can only lower a minimum. The final lower
endpoint is transported with the same tiny-coefficient policy. There
is no approximate tangent asserted as a global lower bound. Exact
Fraction checks of the actual compiled slopes verify each emitted
coefficient's direction. Production need not use the diagnostic
oracle's exact maximizing rational slope.

The default-off mechanism uses the arm's normal D root LP and named
primal, bound to its current call, immutable model SHA and scope. If
the uniformly selected row is violated by more than 1e-8, append one
immutable row, discard old backend/LP/cache state, and solve one new
root LP. A nonviolated row causes no empty reoptimization. The old
root evidence remains; only the new root bound is installed as formal
control. The old GD expected rows migrate to the new SHA without
being embedded twice. Compatible smaller supports inherit the same
row, with absent selectors fixed to zero; expanded supports, gamma
domains or physical inventory domains do not receive it. Eligibility
uses positive S and valid support bounds rather than the old GD row
count. H completion before any model retains the existing omission
semantics.

## Evidence levels

Validity/strictness, strict separation at saved points, reoptimized
complete fixed-domain LP values, and complete own-H algorithm
performance are separate claims. The five matches are three physical
instances. Their optimized gains are numerical values qualified under
the inherited 1e-6 LP quality policy, not exact rational certificates of
old or new LP optimality. Initial LP, Native root-after-cuts and final
external supported L must be reported separately. Complete conclusions
and actual costs are in final_report.md and cost_report.json. The tested
K35/RB35 implementation is research-only because of the important RB35
incumbent/signed-gap regression; LP results alone do not recommend adoption.

This is not a claim of new general fractional-programming theory or
literature priority. R88 pair-CDF, R133's integer objective gap,
R140's stronger historical TC/STOCK endpoints, R144 RN-P and R145
strict complementarity/root-preservation results remain valid context.


# Complete algorithm evidence

The same-new-PE K35 pair gives a real bound/incumbent tradeoff. D returns U/L .676798845196/.545729444783; the candidate returns .679917519727/.558283855657. Supported L rises .012554410874 (2.300483%), physical U is .003118674531 worse (.460798%), and relative gap falls from 19.366079% to 17.889473% (-1.476606 percentage points). The signed gap falls .009435736343. Both remain open. Their accepted T_total values are 2378.764522/2379.834894s; this 1.070373s difference is not convergence or certification speed. The complete comparison justified one RB35 pressure pair, not promotion.

RB35-T2 answers that pressure question adversely. D returns U/L .335883588950/.219663876370; the candidate returns .371420783400/.220898439927. L rises only .001234563557 (.562024%), while physical U is .035537194450 worse (10.580212%). The signed gap grows from .116219712580 to .150522343473 (+.034302630893, about 29.52%); relative gap grows from 34.601188% to 40.526096% (+5.924908 percentage points). Both remain open. The accepted complete totals are 2378.591470/2379.626412s; their small difference is not a speed result. This is a serious regression under the inherited double-open rule: U loss exceeds max(.001,5% of D U), and signed-gap loss exceeds max(.005,25% of D signed gap).

All four formal arms retain their full cap2400 windows, complete independent own H and Seed0/Threads1. The candidate pays its normal root, construction/transport and one added root LP. Both roles have zero committed outer splits; Native target/search paths, Work, simplex and nodes remain separate observations. K35 initial LP increases .204187028164 to .209568159043, whereas printed Native root-after-cuts values are .44681/.44808. RB35 own-root LP increases .135292103721 to .1365597514 (rounded log value). These layers do not imply a monotone final search bound or incumbent. Native/trajectory changes locate observed gains and losses, without uniquely attributing them to a static row, a particular branch or AM. Candidate final U is worse on both roles, so neither candidate trajectory ever beats the corresponding D final U; saved committed trajectories retain the chronology.

| Role | Method | U | External supported L | Gap % | T produce | T cert | T verify | T total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| K-35-U | D | 0.676798845196 | 0.545729444783 | 19.366079 | 2371.178974 | open | 7.585548 | 2378.764522 |
| K-35-U | D_SHARED_S | 0.679917519727 | 0.558283855657 | 17.889473 | 2371.124699 | open | 8.710195 | 2379.834894 |
| R-B35-S-T2 | D | 0.335883588950 | 0.219663876370 | 34.601188 | 2371.218436 | open | 7.373034 | 2378.591470 |
| R-B35-S-T2 | D_SHARED_S | 0.371420783400 | 0.220898439927 | 40.526096 | 2371.060045 | open | 8.566367 | 2379.626412 |


Retain as research only; do not recommend the current shared-S one-row root mechanism as a uniform paper enhancement. The common-first-moment family is valid, strictly stronger than isolated GD, and supplies clear reoptimized LP information on every saved diagnostic domain. K35 adds useful final bound/gap information at a small incumbent cost. However, the serious RB35 incumbent/signed-gap regression fails the required retention question and is not offset by its small L gain. Keep the default-off implementation and reproducible evidence as a completed research result. Preserve R147 standalone D as its previously limited paper candidate and R137 as the stable default. Do not replace defaults or merge automatically.

This closes the tested uniform one-row/one-added-own-root-LP implementation direction, not the entire mathematical common-S family. Two known Seed0 hard-role pairs are a finite selection study, not broad validation or a robustness claim. K20/RX20 complete proof pairs, extra seeds, more root cuts, high-deviation variants, RN/STOCK combinations and AM parameter rescues are not needed to overturn the observed important RB35 loss and are not queued. Unused experimental capacity is not unfinished work. The optional AM/no-strict information-retention question remains a separate possible future study; historical R47/R52 negative anchors and prior threshold experiments remain intact and are not rerun here.
