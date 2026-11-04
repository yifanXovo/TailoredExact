# Independent pre-experiment design review

Reviewer: `/root/independent_review`, 2026-11-04 (Asia/Shanghai).

Verdict: **ACCEPT_DESIGN_WITH_INTERFACE_GATES**. The declared mathematics and
the concrete reference-chain code reviewed below have no blocking defect.
The small reference construction may proceed. Expensive coupled runs remain
conditional on checking the new RMP/pricing interface and its targeted small
qualification; this report does not certify code that was not yet written.

This is a source/math review, not a rerun of historical evidence. No Optimize,
Native model load, compiler, enumerative checker or timed experiment was run
by this reviewer. Only source/document reads and authoring were performed.
The active `WORKSPACE_POLICY.md` was read and is inherited. No original
workspace, production source, historical carrier or user file was changed.

## Material inspected

- The adopted Round153 goal and `preanalysis.md`.
- `scripts/round145_math.py`: `joint_rows`, `safe_row`, finite-box transport.
- `scripts/round143_math.py` / `round143_lp.py`: RN rows, denominator bounds,
  full matrix residual and semantic identity conventions.
- `scripts/round152_math.py`, `round152_normalized.py`, `round152_discover.py`,
  `round152_projection.py`, `round152_cycle.py`, `round152_global.py`,
  `round152_lp.py`, and `round152_small.py`.
- R152 `review/exact_small_theorem.md` and `independent_exact_small.py`.
- The first implementation of `scripts/round153_lp.py` and
  `scripts/round153_reference.py` supplied during this review.

The external Round153 evidence ZIP is unavailable in Downloads. The goal
expressly permits reconstruction from fixed R152 evidence and its formulas.
No old performance experiment needs to be rerun for this reason.

## Old-reference chain and direct Gini rows

`joint_rows` retains NC1 and NC2 separately. It multiplies the old count
aggregate by the same positive reciprocal factor, using the actual supported
states and the actual binary64 RN bounds. The four TS slopes, endpoints,
signs and right-hand sides match the four McCormick inequalities in the goal.
The two existing scaled-stock rows are additional necessary information;
they are not substitutes for TS1--TS4.

The proposed finite caps are justified by existing rows, without decreasing
absolute-value auxiliaries: nonnegative `rn_h` and `sum(rn_h)<=n*G` imply
`rn_h<=n*gamma_U`; the RN mass/inventory rows imply
`rn_Y_i<=max(support_i)*U_t`. The actual implementation goes further and
derives missing bounds from the existing complete matrix with Fraction
arithmetic and outward rounding. These bounds do not change the model.
Its row propagation formula and use of both sides of equalities are valid.
If propagation cannot prove a required adverse endpoint, the dual remains
unqualified; an infinite endpoint is not silently replaced by a heuristic cap.

The reference implementation restores eight lifted supports, the final
full-support row and the applicable scalar floor by their fixed archive
member identities. It keeps every old total row, adds NC/TS and then adds
the independent direct-Gini rewrites. It checks the saved full point first,
and uses a qualified dual/point sandwich before avoiding a new Optimize.
New optimizations retain all original variables, bounds, objective, cutoff,
and rows; their original semantic fingerprint is checked.

For a stored total row `G+Pe-pi*s>=a`, the identity in its original pricing
certificate is `phi-pi*v=f-(pi-h)*v`. Thus the direct row is
`G+(h-pi)*s>=a`. It is not obtained by subtracting AP from an inequality.
`direct_row` uses the actual stored `-pi` coefficient and exact unary `h`,
then adds the sum of each station's minimum coefficient error to the RHS.
That is the correct one-hot transportation direction, including dropped
tiny coefficients. The stored total row is preserved. This argument does
not license replacing the total floor in the APoff pure-B carrier.

The R152 CP optima are not automatically current optimal-face points. They
can seed inventory candidates, but comparisons or face claims require a
feasible extension through the complete current RN/NC/TS Q and the stated
objective band. The reference code's full-point checks respect this distinction.

## Coupled RMP, dual signs and true-column rounding

For the convention in the goal,

`L = F(x)+a(1-sum lambda)+pi*(s-sum lambda*v)+beta*(sum lambda*f-G)`,

the reduced cost is `beta*f-pi*v-a`, with `beta>=0`. A true-stock price is
an upper on its minimization oracle. Only a complete-domain price lower
`Lm` permits the convexity intercept change `a'=min(a,Lm)`. The resulting
loss is `max(0,a-Lm)` exactly once, because the mixture has total mass one.
The goal's directions and formulas (3)--(5) are correct.

If the Native rows are written as `sum lambda=1`,
`s-sum lambda*v=0`, and `G-sum lambda*f_hat>=0`, their solver multipliers
map to `a=Pi_mass`, `pi=-Pi_link`, `beta=Pi_Gini`. Reversing a link row changes
the corresponding sign. The new interface must verify this against at least
one explicitly negative reduced cost; formula inspection alone is insufficient.

An upward-rounded `f_hat>=f` makes the RMP an inner restriction of the true
coupled LP and protects its Gini completion direction. The dual correction
must nevertheless use the actual extracted `a,pi,beta` and a full-domain
lower for **true** `beta*f-pi*v`. This correction includes any reduced-cost
shortfall caused by replacing `f_hat` with `f`; a second arbitrary column
rounding subtraction is unnecessary if the complete true-price correction
has already been applied. The true and written column values and their
differences should be recorded, so this is demonstrable rather than assumed.

A clean certificate is obtained by evaluating the sign-repaired Q-row
multipliers and exact original-column residual support to get `C_Q`, keeping
the convexity constant separate, and then using

`C_Q + min(a,Lm)`.

The same calculation can expose a restricted dual lower `D_K<=C_Q+a`
(including the finite-K reduced-cost qualification) and report the requested
conservative `D_K-max(0,a-Lm)`. Neither value may be replaced by RMP ObjVal.
Bounds or multipliers associated only with finite-K lambda variables must
not be silently interpreted as full-domain restrictions.

The reviewed `dual_certificate` sign repairs, exact binary64 matrix/Pi
residuals, and bound-support signs are correct. For coupled runs, it must
receive bounds proved on **Q before adding finite columns or artificial
variables**. Calling its default bound propagation on a restricted RMP
could derive an original-x bound that depends on missing columns; that bound
would not support a full-hull lower. The parent was notified of this required
interface contract and agreed to pass the Q bounds explicitly.

`f_hat` protects only the Gini link. A usable numerical RMP upper also needs
the complete Q primal checks, lambda nonnegativity, mass/link residuals and
true completion. The parent has explicitly chosen the inherited numerical
primal qualification, not a rational primal certificate; reports must retain
that qualification and its observed residual envelope. If numerical lower
and primal values cross within that envelope, do not present an inverted
interval as exact. This is a new-interface qualification, not a requirement
to reopen all historical tiny-gap engineering.

## Pricing and Phase I gates

The normalized binary formulation remains equivalent on its positive-stock
part for every nonnegative beta. Its objective must be generalized to
`beta*q+sum d_i(y)*x_i_y`, with `d=-pi` in Gamma pricing and `d=h` for the
scalar floor. The hard-total DP lower is
`beta*gamma_L + min_hard_total sum d`; a legal zero vector has value
`beta*gamma_L+sum d_i(0)`. In particular beta=0 retains physical Gupper and
the entire support/resource domain, but contributes no gamma_L or unary h.
Negative prices and reduced costs remain meaningful and must not be clamped.

The old normalized oracle's objective/numerical guard was written for a unit
coefficient on q. Arbitrary beta requires the corresponding q coefficient
transport and beta-scaled numerical uncertainty; copying the old guard's
constant unit term unchanged is not enough for large beta. The Native model
readback must identify the actual objective coefficients used for its lower.
True-stock feasibility/value recomputation continues to qualify upper bounds.

Missing-column infeasibility is an RMP property. Artificial link/Gini slack
can establish Phase I, or further legal columns can restore feasibility.
An artificial objective is never an ordinary strengthened-LP upper. After
artificials reach the accepted feasibility threshold, remove/fix them to zero
and qualify a normal RMP solution before publishing `U_K`. All original x
remain free. An old marginal distribution alone does not establish a valid
completion through the original cutoff and auxiliary relationships.

Targeted tests should cover the actual added interfaces: a small all-column
control, missing-column Phase I, beta=0, negative reduced cost, true-price
correction for upward f, and the support-row coefficient transport. Existing
R152 oracle/zero/nonminimal/source-matrix qualifications need not be rerun.

Projection compatibility and expected-Gini cost should be reported separately.
A beta=0 support has a clear projection interpretation. A compatible saved
point proves only that point's projection feasibility. Neither a finite set
of compatible points nor a beta>0 direction alone quantifies the whole-face
projection contribution. Any additional projection-only comparison must use
the same Q and a qualified complete-domain bound or a feasible witness.

## Reconstructing the strengthened fixed-marginal example

The existing independent R152 checker supplies the 117-row, 46-variable
reference matrix and rational extension. Add 44 RN rows, two scaled-stock
rows, two NC rows and four TS rows: 169 rows. Add t, three rn_Y coordinates,
15 rn_w coordinates and three rn_h coordinates: 68 variables.

At the stated marginal, let `u=w_22`, `v=w_33`. RN mass and normalization give
`2t+u/2+v/4=1`. Both NC aggregates at this marginal reduce to
`Hhat>=t/2+u/2+v/4=1-3t/2`. The two differences against station 1 give
`Hhat>=t-u/2-v/4=3t-1`. Weighting these bounds by 2/3 and 1/3 yields
`Hhat>=1/3`, so `g>=1/9`.

The proposed `t=4/9`, `u=1/9`, `v=2/9`,
`rn_Y=(4/9,5/9,10/9)` and `rn_h=(1/6,1/6,0)` attain this bound.
Scale the old G/state_g/zprod extension by 10/9 and retain its other old
coordinates. A single Fraction check of all 169 rows and 68 bounds on this
new extension is the appropriate remaining computational verification; it
requires no new Optimize. It should be serially charged as new verification.

The unique three-column common distribution and `Gamma=161/1080` are unchanged,
so the strengthened fixed-marginal gap is `161/1080-1/9=41/1080` and its
reference objective is `59/288`. These are inventory-block, fixed-marginal
statements. The older `1/480` global-floor gap is not inherited, and no full
route extension or universal historical-hull domination follows.

## Research and production decisions

The planned three-domain intervals, conditional targeted deepening and
separate K35 pure-B floor test match the goal. An initial 1e-4 target for the
35-station roles and 1e-5 for N-C20 is reasonable subject to actual numerical
envelopes and the observed scientific increment. Fixed small iteration counts
are process controls, not a sufficient negative research conclusion.

No production claim or complete B/J arm follows from these diagnostic values.
Any later candidate needs a frozen uniform rule, own-H/current-domain pricing
and its actual full cost, with stable R137 retained. The preanalysis preserves
the serial 115200-second accounting and conditional panel capacities.

## Required next review

Review the concrete RMP/pricing code and the targeted qualification output
before expensive coupled/deepening runs. The two concrete interface points
to close are Q-only finite-bound provenance and beta-aware price qualification.
The reference-chain code as reviewed has no blocker for the initial finite
reference experiment.

The subsequent [concrete interface review](interface_review.md) closes these
implementation gates after the TS coefficient-transport correction and targeted
small qualifications, and accepts the declared three-domain research stage.
