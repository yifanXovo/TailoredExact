# Independent preliminary mathematical review

Reviewer: `/root/independent_math_review`, separate from the principal implementation agent. Date: 2 November 2026 (Asia/Shanghai). This review reads the authorized Round145 goal, `WORKSPACE_POLICY.md`, the R140/R143 generators, the canonical stock/count writer and the existing mathematical analyses. It performs no Optimize, compile, historical replay or new enumeration. Production Round145 writer and actual Native readback remain to be reviewed separately when available.

**Disposition: the proposed NC, TS, NC-PC and fixed-selector parameter-family claims are mathematically sound in their stated scopes. No mathematical blocker was found.** The implementation conditions below are necessary for this disposition to extend to the actual source model.

## NC and the count generator

At an integer selector completion, positive reciprocal normalization gives `w=t*s`, `Yhat=t*Y` and `t*S=1`. The pair epigraph then satisfies `Hhat >= t*A`. Multiplying either integer-valid count lower bound `A >= b+sum(k*s)` by positive `t` proves `Hhat >= b*t+sum(k*w)`. The count constant becomes a coefficient of `rn_t`; it does not remain a right-hand constant.

R140 computes thresholds from the exact dyadic interpretations of the loaded positive binary64 ratio coefficients. It uses all distinct positive supported levels and starts from zero; this is the correct telescoping threshold identity even when some supported minima are positive. The ascending minimum-crossing costs give a necessary upper count under the physical inventory upper budget. The descending gains above each optional station's largest low state give a necessary lower count under the physical lower budget. Forced-high and forced-low stations are treated consistently. Support holes are allowed in this necessary-count construction. No claim that every count between the bounds is attainable is needed.

For each threshold, `(K-ell)*(u-K)>=0` gives the TC2 chord. Its difference from retained TC is `ell*(u-K)`; after homogenization this becomes `ell*(u*t-W)`. Fractional `w/t` need not satisfy the integer-derived upper count, so keeping both aggregates is correct. Negative TC2 slopes are legitimate. Clipping them, dropping the positive constant, or retaining only NC2 would change the proposed model.

The existing R140 generator rounds each signed coefficient and constant downward. Reusing those stored values in NC preserves validity because `w>=0` and `t>=0`; this applies to negative coefficients as well. The homogenized row may be slightly weaker than exact dyadic aggregation. That numerical difference should remain visible rather than being represented as a new exact symbolic equality.

The physical budget excludes the depot and comes from empty departure and loaded return: `Bminus=max(0,sum(initial)-sum(Q))`, `Bplus=sum(initial)`. It is not a bound on cumulative pickups. Intersecting with the sums of current supported minima and maxima is valid. An observed stock total, fleet witness or local optimum is not a new full-scope budget.

## TS signs, units and transport

The four rows follow respectively from the nonnegative products `(tau-Bminus)*(t-L)`, `(Bplus-tau)*(U-t)`, `(tau-Bminus)*(U-t)` and `(Bplus-tau)*(t-L)`. Thus their signs and constants in the goal are correct. Both `tau` and `tauhat` are physical inventory, while `sum(c_i*Yhat_i)=1` is the ratio normalization; these directions must remain distinct for heterogeneous targets.

Using original `Y_i` and existing `rn_Y_i` avoids new selector-coefficient multiplication. With `Ysum=sum(Y_i)` and `Yhatsum=sum(rn_Y_i)`, the exact stored-double row forms are:

| Row | Left side | Sense | Exact right side |
| --- | --- | --- | --- |
| TS1 | `Yhatsum-L*Ysum-Bminus*rn_t` | `>=` | `-L*Bminus` |
| TS2 | `Yhatsum-U*Ysum-Bplus*rn_t` | `>=` | `-U*Bplus` |
| TS3 | `Yhatsum-U*Ysum-Bminus*rn_t` | `<=` | `-U*Bminus` |
| TS4 | `Yhatsum-L*Ysum-Bplus*rn_t` | `<=` | `-L*Bplus` |

The RHS product must be rounded downward for the two lower rows and upward for the two upper rows. A finite positive power-of-two scale can then preserve tiny matrix terms through Native import. The Native coefficients, sense, RHS and finite bounds need actual readback. If TS instead expands `tau` into selectors, the additional `L*y`/`U*y` coefficient roundings need directed compensation; simple nearest rounding of those terms is not covered by the above argument.

## NC-PC

For arbitrary real station multipliers, station mass gives `b*t+sum(k*w)=Gamma*t+sum((k-lambda_i)*w)`, with `Gamma=b+sum(lambda_i)`. Minimizing each signed term over `L<=t<=U` and `L*s<=w<=U*s` yields exactly the NC-PC formula in the goal. This is valid for any multipliers; multiplier optimality is unnecessary. Positive violation therefore excludes every NC extension of that original `s,g` point, rather than only the particular saved `w,t`. It still does not establish reoptimized full-objective gain. The note that the listed historical points also violate old TC2 makes the strong-old-carrier comparison essential.

## Fixed-selector family, all n>=4

There is one positive threshold, at one. Its count interval is `[1,n-1]`, so retained TC is `K`, TC2 is the constant `n-1`, NC1 is `sum(w_1)=1` and NC2 is `(n-1)*t`.

The old variables in the goal give `J=(n-1)/n` and `H=n-1`, with `q_1=(n-1)/n^2`. Old TC2, Gini and the stock upper row imply `g>=1/n`. The proposed `q_0=g-q_1` is nonnegative and stays below the old product-box upper face at all four claimed optima. The other stock faces reduce to `g<=1/2`, `g>=((n-1)/n)*(4-n)/2` and `g<= (n-1)/n`; all hold for n>=4. The pair values `h=2/n` have total `n-1` and are compatible with the declared ordinary pair-difference block.

Normalization forces `sum(w_1)=1`. Station mass and zero-state lower product bounds imply `n*t-1>=n/(2*(n-1))`, hence `t>=t_N=(3*n-2)/(2*n*(n-1))`. NC2 then gives `g>=(3*n-2)/(2*n^2)`. The fourth TS face forces `t>=t_S=(3*n-4)/(2*(n-1)^2)`; adding NC2 gives `g>=(3*n-4)/(2*n*(n-1))`. These are the claimed lower bounds.

At `w_1=1/n`, `w_0=t-1/n`, all local product/mass faces hold at both proposed t values. Their difference is `t_S-t_N=(n-2)/(2*n*(n-1)^2)>0`. In the TS cells, its first and second faces give the same upper bound `t<=n/(2*(n-1))`, its third gives `t>=(4-n)/2`, and its fourth is tight at t_S. These hold for all n>=4. With no NC, `hhat=0` is feasible because normalized ratios are equal. With NC, assigning each pair `hhat=2*t/n` gives `Hhat=(n-1)*t`, satisfies NC1 as well as NC2, and respects each finite cap `hhat<=1`. The resulting four exact optima and the two strictly positive differences in the goal therefore follow. At n=4 they are 1/4, 1/4, 5/16 and 1/3. The common fixed state penalty n/2 adds the same `lambda*n/2` to every original objective.

For positive-inventory binary integer points, `G=(n-tau)/n`. Fixed one-state marginals 1/2 give expected tau n/2 in every representing mixture, hence expected minimal g exactly 1/2. The equal mixture of all n inventory-one vectors and their n complements realizes those marginals and attains the bound. Thus the complete integer Gini epigraph hull at those marginals has minimum 1/2. The joint relaxation is strictly stronger than O and still has an O(1/n) value. This is a meaningful remaining integer-objective gap.

These are fixed-selector local-block statements. Neither the 2n-point selector/pair mixture nor the old q assignment is asserted to be one joint mixture of complete routing, all g products and integer objective epigraph points. The family does not establish dominance over every R141/R142 conditional disjunction.

## Conditions to check in the Round145 implementation

1. All source additions relative to formal stable BASE must be in one explicit block list used both by dual aggregation and Native coefficient auditing. RN, both NC rows and all four TS rows belong there. If stock/TC/TC2 are included in the source, their rows also belong there. A prefix-only R143 audit or the unchanged R144 loop over old RN rows is insufficient.
2. TS may produce original `Y_i` terms in the projected row. R144 currently allows only `G` and `state_*` and parses every other term as a selector during embedding. Those checks must be extended consistently if Y is retained. Current-support omission is valid only for absent selectors fixed to zero, not for Y terms.
3. The original RN proof that pair caps are projection-redundant reduces each hhat to its absolute-difference minimum. That particular argument does not directly survive NC, which can demand a larger sum. The caps remain integer-valid and the family satisfies them. Any stronger claim of redundancy in the joint model needs a separate redistribution argument: after choosing pair minima in [0,1], distribute the required sum in those boxes, using `n*g<=n-1<=number_of_pairs` on the usual Gini domain. A limited description as inherited integer-valid finite caps is sufficient for this round.
4. Same-root value preservation is a standard dual-aggregation result for the same actual source P, objective and finite boxes with zero objective on new columns. It is neither equality of full projections nor all-tree preservation. Outward arithmetic establishes validity; actual compact reoptimization measures information retained.
5. The source remains paid, restored/discarded and isolated from formal controller proof evidence. Source quality failure must not produce a supported bound or cutting row. Initial own H, full Start, support/G/cutoff compatibility and old zero-denominator behavior remain unchanged.

No new experiment or algorithm choice is authorized by this review alone. The finite matched LP results and the separately reviewed production writer determine whether route A or B is supported.

## Diagnostic writer addendum

The principal implementer subsequently supplied `scripts/round145_math.py` (SHA256 `a13e6c87d2351eb4201dc56e0a97584aa697ba4e9b05ef8a2fb4f53e3f46e0eb`) and `scripts/round145_lp.py` (SHA256 `ec472d7bb390b4ec7a0383d472d3e4d903a1b3ecb765bf12550baf3b9e0adad1`) for independent source inspection. The inspected math version already uses `sum(rn_Y_i)` in TS.

**Diagnostic arithmetic disposition: PASS on inspection.** `joint_rows` reuses the exact unbounded-Fraction count oracle with actual binary64 ratio interpretation, carries both signed NC aggregates and the NC2 constant into `rn_t`, and generates all four TS faces in the reviewed signs/units. Rather than rounding k and b separately as production R140 does, its `safe_row` starts from exact rational coefficients and compensates the entire converted row over actual finite bounds. If `a'=a+e`, then an exact lower row implies `a'x>=b+min_box(e*x)` and an exact upper row implies `a'x<=b+max_box(e*x)`. The implementation uses these respective min/max choices, directs the RHS outward, and only then applies the positive binary power scale. This is valid, including signed coefficients, dropped conversion-to-zero terms and the finite interval for `rn_t`.

The `project` routine repairs inequality multipliers to their legal signs, retains equality multipliers as signed, sums every passed row, eliminates each `rn_*` coefficient by its upper box support, and compensates original-variable conversion/deletion using the lower signed-box error. It allows Y and the other legitimate original columns potentially introduced by an O source. The routine is correct **provided its caller passes the complete source additions relative to formal BASE**. Completeness of a future production caller is a separate obligation; function inspection cannot establish it.

The LP driver checks the inherited source SHA, saved optimum residual and original objective value, RN expected rows and `rn_t` bounds, zero RN objective, unchanged full prior semantics, and actual readback of added rows after serialization. It explicitly uses Seed0, Threads1 and serial outer metering. No production writer or full run is accepted by these checks alone.

One metadata defect was sent to the principal implementer: the local `check` variable holding baseline residual is later overwritten by the new solution residual, so the inspected driver's `baseline_residual` field repeats the final residual. The baseline assertion itself executes correctly; retaining its value under a distinct variable is a zero-Optimize reporting correction. This defect does not invalidate the already checked numerical solution or mathematical row.

The already completed single K35 NC result is evidence only for that reoptimized matched NC model. This review does not infer the yet-unmeasured TS/joint increments, superiority over O, compact information retention, or complete algorithm benefit.
