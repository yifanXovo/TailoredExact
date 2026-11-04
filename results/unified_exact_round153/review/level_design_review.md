# Independent review of level dual selection

Reviewer: `/root/independent_review`, 2026-11-04 (Asia/Shanghai).

Verdict: **ACCEPT_FOR_K35_LEVEL_DEEPENING**. The implemented level rule is an
admissible way to select candidate multipliers. It does not change Q, the
inventory domain or the lower-bound qualification. The existing K35 columns
and qualified interval may be retained. This gate permits targeted offline
research; it does not certify improvement, convergence or a production arm.

This review used source reading, mathematical reasoning and the small saved
`qualification/level_v1/result.json` record. No solver, compilation, model
load, verification process or performance experiment was run by the reviewer.
The primary agent reports the serial metered qualification charge as 0.339 s.

## Reviewed state and evidence

The reviewed source SHA256 values are:

| File | SHA256 |
| --- | --- |
| `scripts/round153_coupled.py` | `8bd7487d171ff188e8c05c5223c8275dfa2e3fb57420d35b5f17c2bd75ce3e63` |
| `scripts/round153_stabilize.py` | `b2999db3f607d779c0f61db34d51e520f0731c92033c28535de3c7ffe23a053e` |
| `scripts/round153_qualify.py` | `f9466a976c44e457136d463e4fc6e6e25ca4d34021dcf6914a1f79ddf67a81c4` |
| `qualification/level_v1/result.json` | `d34c61686097af11d5dc49e5e3819493e22d4c85435983ef7b0c483762c654fe` |

The targeted fixture uses the independent full-column value `47/240`. Its
level-band width is `0.5479166716666668`, rather than the near-optimal `1e-7`.
It returns a qualified corrected lower `-0.352085650833334`, restricted-master
upper `1.291666676666667`, beta `1`, and a true negative reduced-cost witness
`-1.0958333333333334`. These satisfy the asserted bound direction and exercise
an actual low-level selection followed by full-domain pricing. The weak lower
is not evidence of useful improvement; the purpose of this control is the
validity of the changed candidate-selection path.

The fixture does not execute the entire continuation loop or the special
case of no new column with a higher qualified lower. Those control-flow
conditions were inspected in `run`; the review does not claim dynamic
coverage that the saved fixture does not provide.

## Candidate level and explicit-dual signs

Write `z_K` for the current restricted-master numerical objective, `L` for
the accumulated qualified lower, and `U` for the accumulated qualified
numerical primal upper, when one exists. The requested level is

`ell = (L + min(U,z_K))/2`.

Without a previous upper, the code uses `z_K` only to select the candidate
threshold. It does not thereby promote an unqualified current primal into
the upper-bound record. The code computes

`band = max(epsilon, z_K - ell)`,

where `epsilon = min(1e-7,tolerance/10)`. Thus the actual selection threshold
is `min(ell,z_K-epsilon)`. In the current K35 interval this is the requested
midpoint; near numerical closure the small deficit floor deliberately keeps
the candidate constraint feasible under the existing numerical policy.

The explicit dual has the same correct signs reviewed previously:
`A^T p + l + u = c`, nonnegative multipliers for primal `>=` rows,
nonpositive multipliers for primal `<=` rows, free equality multipliers,
`l>=0` for finite lower bounds and `u<=0` for finite upper bounds. The
candidate objective constraint includes `ObjCon` exactly as
`b*p + LB*l + UB*u >= z_K-band-ObjCon`.

The secondary objective remains the sum of absolute deviations of the
link prices from `h(anchor)-h(y)`, plus `abs(beta-1)`. This objective does not
restrict a potential to a prescribed radius. It is a numerical selection
criterion on the explicit RMP dual, not a statement that its center is a
feasible full-hull dual or that the selected point is RMP-optimal.

## Why the certified lower remains valid

The level enters only `select_dual`. It is absent from the final lower-bound
formula. The selected row multipliers are passed consistently to both the
pricing objective and `Master.certificate`; beta receives the same
nonnegative sign repair in both paths.

The certificate still recomputes every original-Q variable residual with
Fraction arithmetic and supports it using bounds derived before inventory
columns were added. It excludes lambda columns, the convexity RHS and the
artificial `1e-8` Gini completion margin from `C_Q`. No finite-column-derived
bound or explicit-dual bound multiplier is substituted for that calculation.

With true column values rather than upward-written column coefficients,

`a_K = min(a, min_{Y in K}(beta*f(Y)-pi*v(Y)))`.

For the qualified full-domain pricing lower `L_m`, the final value is still

`C_Q + a_K - max(0,a_K-L_m) = C_Q + min(a_K,L_m)`.

This derivation does not require the selected RMP dual to be optimal or to
attain its requested numerical level. Any numeric selection residual is
handled by the same Q residual support and one convexity correction. The
full-domain oracle, beta-aware numerical guard, true candidate checks and
upward-rounded column-value correction are unchanged. The level itself,
the selector's objective and the current RMP objective are never assigned
to the accumulated lower.

The original Q variables remain free in the original feasible region. The
selection LP is a separate multiplier model; it adds no primal objective
band, fixed marginal, inventory restriction or extra support cut to Q.
All inherited columns are retained. The original numerical primal checks
are still the sole route to updating U; U is a strengthened-LP upper, not
a physical routing incumbent or a rational primal certificate.

## Continuation, unresolved cases and accounting

After each completed price, the implementation sets
`lower=max(lower,certified_lower)`. If no new true negative-cost column is
added, level mode continues only when this accumulated lower improves by
more than `max(1e-8,tolerance/100)`. Therefore a successful full-dual lower
can raise the next level even with an unchanged column set. An unchanged
or merely last-bit-improved lower cannot create an unbounded empty loop.

Absence of a new witness does not prove nonnegative full-domain reduced
cost. In particular, a price interval straddling `a` remains unresolved.
The existing no-progress decision keeps that distinction. A price witness
already present in K also does not count as a newly useful column; the
true-column `a_K` correction still protects the bound in that situation.
Neither exhausted pricing nor exhausted selection is a negative result for
the full hull or for the proposed strengthening.

The requested level and the actual selected dual objective are recoverable
from the saved RMP objective, band and selector record. Reports should retain
the before/after accumulated interval and the actual price/correction and
column-addition records when explaining progress. An inverted interval from
numerical envelopes must be described as a numerical qualification issue,
not interpreted as a stronger exact theorem. Current K35 starts with a
strictly separated valid interval, so this is not a present admission issue.

The selector retains its bounded offline solve allocation and basic-dual
fallback. The cost of selection, any unsuccessful call, full-domain price,
serialization and checkpoint remains part of the same serial experimental
charge. The present gate gives no permission to book old columns as new
free solves or to copy this offline selection policy into the conditional
production candidate.

No additional source correction is required before the proposed K35 level
continuation. Its value must be judged from the resulting qualified interval
and complete additional cost; the low-level fixture establishes validity,
not anticipated effectiveness.

## Zero-center candidate-selection addendum

The primary agent proposed a second targeted candidate center after observing
tight pricing but persistent large convexity corrections and no upper-bound
movement under the AP-centered level run. Before executing that proposal,
the reviewer gives **ACCEPT_DESIGN_FOR_ZERO_CENTER_LEVEL_SELECTION**.

Replacing only the secondary selection objective by

`sum_{i,y != anchor_i} abs(pi_iy) + abs(beta)`

preserves every validity argument above. Since beta is nonnegative, its
absolute value is simply beta. The objective discourages coupling
multipliers in the same anchored link convention; it imposes no hard radius,
fixing, state deletion, primal restriction or full-domain price shortcut.
The level row and all explicit-dual signs must remain unchanged.

An original-Q dual can be embedded in the restricted-master dual with zero
link/Gini/convexity multipliers, so the zero center has a natural relation to
the Q-only lower. It does not imply that this exact numerical center attains
the current requested level. A level above the Q-only dual value generally
requires some coupling multipliers. Minimizing their L1 magnitude is a
candidate-selection heuristic, not a new theorem about hull value or
convergence and not a guarantee of better pricing.

The final qualification must still ignore the selector objective and its
requested level as bounds, retain the original Q-derived residual support,
correct upward-written column values through true `min_K`, and apply the
same full-domain pricing correction once. Beta=0 remains covered by the
existing oracle design and qualification; there is no implicit unary h term
when pricing the resulting direction.

Record the selected center (`ap` or `zero`), level/band, actual selected dual
objective and full pricing/correction result. Continue from the retained
columns and accumulated qualified interval; do not rerun completed old
loops. Costs and unresolved outcomes remain part of the same paid targeted
research.

The subsequent implementation was also statically reviewed. The CLI mode
`level_zero` selects zero link and beta centers in `select_dual`, records
`center='zero'`, and uses the same level continuation, price and certificate
paths. No original-row sign, variable-bound multiplier, price domain or
lower/upper qualification changed. This closes the implementation gate:
**ACCEPT_FOR_ZERO_CENTER_LEVEL_DEEPENING**. No new executed zero-center result
is claimed by this review.

Reviewed implementation SHA256 values are
`2ab44f6208832ac3f8ab3066fc74ed7c1776604006d771f746a6e6a962256549`
for `scripts/round153_stabilize.py` and
`2efae33c1d85a356ad84702906c154372930d2e7a4652375ef34e4bf3d7b6c19`
for `scripts/round153_coupled.py`.
