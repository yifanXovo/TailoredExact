# Round154 residual interface: independent source and qualification review

Reviewer: `/root/review_round154`. Date: 2026-11-05 (Asia/Shanghai).

Disposition: **ACCEPT_RESIDUAL_INTERFACE_V2** for the declared finite
new-interface qualification and mathematical lower-bound path. Selection of
expensive real directions and their cost/fairness freeze remain separate.
This does not admit E, any compiled production candidate or its full panel.

The reviewer read round154_residual.py and round154_qualify.py, v1/v2 saved
small qualification summaries and closed outer receipts, representative
actual MPS text, calls, LP/MIP returns and Native log excerpts. The review
also traced the reused outward/stock_value/s_bounds contracts. It started
no solver, Native model read, enumeration, compilation, new qualification
or performance run. The parent executed the saved tests; this is independent
source/evidence assessment, not an independent rerun.

## Actual model and safe coefficient direction

The model keeps all original supported one-hot x, explicit inventory Y,
ratio r_i=c_i*Y_i, S=sum r_i, both hard totals and physical Gupper. Four
binary-product inequalities per state are present together with station
sum Sx=S. The total-product pair is present by default.

The explicit Y/ratio factorization retains c_i as the declared binary64
coefficient instead of silently replacing its product with each integer y
by a separately rounded state coefficient. Product l and u are the safe
outward bounds of the inherited positive-denominator contract. The actual
MPS text confirms those directions and the one-hot/product equations.

For the two residual epigraphs, the implementation centers d by station
midpoints and writes every centered state coefficient, accumulated S
coefficient and beta/(n*scale) coefficient downward. z, S and A are
nonnegative. Hence at each legal inventory's minimal exact extension,
the written scaled epigraph RHS is no greater than its true scaled
residual. There is no adverse upper distortion to subtract for this
intentional relaxation. The physical Gupper coefficient is written
upward, so its row also admits every exact legal minimal extension.
This is not a claim that the rounded model's every integer inventory is
legal in the exact original domain; returned inventories still undergo
the original Fraction feasibility/Gini/price check.

The actual MPS has `FR BND1 residual_scaled`, coefficient 1 in the
objective, and coefficient 1 in both q rows. Negative residual values
are therefore allowed. For beta=0 the two epigraph rows coincide, but
the physical cap, hard totals, product block and supported state domain
remain. These rows were present in the inspected beta0 MPS.

A power-of-two residual scale includes the centered cost range times u,
the accumulated S coefficient, and the beta*A range. Its guard is

    scale * 1e-6 *
      [1 + u*sum_station max_y abs(written_centered_scaled_cost)
         + u*max(abs(written_S_floor),abs(written_S_G))
         + written_A_coeff*n*gamma_U*u].

It is paid before the sign-dependent denominator conversion, with
recorded scaled/original residual units. This is a Native numerical
qualification under the inherited accepted policy, not an exact rational
proof of an unseen MIP search tree. The reviewed code does not copy the
old RN price-unit constant into this new model.

Both parameter epigraph rows are removed/rebuilt when tau changes.
The separate LP diagnostic is not used as a qualified price lower.
Accepted interrupted MIP statuses require a finite bounded ObjBound;
unsupported/infeasible statuses retain DP and any previously qualified
information. A Native infeasible report does not delete the positive
branch.

## Lower composition and transport

recover() uses u for nonnegative qualified ell and l for negative ell.
It converts after residual transport/guard. The positive lower is
max(DP fallback,recovered residual). Legal zero is then taken by minimum.
Only afterward does a same-domain inherited full price lower strengthen
the complete result by maximum.

Each returned solution-pool stock is recomputed from original supported Y,
both hard resource bounds and true Gupper. Only legal true-price values
become uppers. An auxiliary q incumbent or nonminimal A is never the
authority for a price upper. No additional h term is added to Gamma pricing.

transport() subtracts max(delta*l,delta*u), so both increasing and decreasing
tau have the correct orientation. Reuse binds full scope and every exact
d value. An initial source review found that beta was held as a Fraction
but prior reuse compared only float(beta). Two distinct exact beta values
can round to the same binary64 display. The actual v2 repair adds
beta_exact to calls/results and requires exact equality for prior residual
reuse. This closes the identified interface identity problem. Real R153
directions already have binary64 beta, but the repair makes the new
Fraction-capable API internally consistent.

Inherited_lower is a caller-provided existing certificate; its scope and
coefficient source must therefore be bound by the frozen real-direction
driver. The low-level function cannot infer such provenance from a scalar.

## Saved finite evidence

The v2 summary reports PASS for three finite domains, beta=0 and beta=1.7,
two tau values on opposite sides of the positive price, legal-zero/mixed
and zero-only cases. For every legal positive inventory it checks every
actual written row and variable bound at the exact minimal extension.
The test source checks qualified residual lower against the enumerated
true residual minimum and verifies the recovered price lower does not
exceed true price. It checks positive and negative parameter movement,
and inherited full-price lower retention on the second target.

The first target has positive qualified residual lower; the second
has a negative Native residual incumbent. Thus positive/negative q and
both price conversion branches are exercised even when a stronger DP
bound dominates the reported final price lower.

Six nonminimal-A completions pass actual rows/bounds and are explicitly
not used as true prices. The zero-only case returns exactly -.75 without
a positive Native call. Exact finite arithmetic also checks the stated
Cartesian-McCormick strictness witness, the tighter-hard-total limitation
and its elimination by the total-product row. No normalized RN/full-Q
dominance is asserted.

Representative actual saved evidence includes:

| Item | Observation |
| --- | --- |
| fixture1_beta0.0_target1/model.mps | Six binaries; all physical/resource/product rows retained; q is free below. |
| fixture2_beta1.7_target1/call.json | Positive S interval [.1,2]; scale4; 29 variables,9 binaries,62 rows,191 nonzeros; original residual guard about1.00206e-5. |
| fixture2_beta1.7_target1/LP.json | Optimal numerical LP objective about-.12544444; diagnostic only. |
| fixture2_beta1.7_target1/return.json | Optimal MIP bound/incumbent about-.08277778 in scaled residual units; two true-stock candidates checked by the original price evaluator. |
| residual_qualification_v1/receipt.json | Exit0;1.1538779998663813 outer seconds; no timeout/supervisor failure. |
| residual_qualification_v2/receipt.json | Exit0;1.1882893000729382 outer seconds; no timeout/supervisor failure. |

These tiny qualification calls are not performance samples. Native Runtime
and helper work are nested in the unique outer receipts.

The simple dyadic test costs make centered state coefficient roundoff
zero in these fixtures; nontrivial S/A coefficients are exercised. A
single additional mixed-sign binary64-cost check with nonzero state
downward rounding was recommended as a useful targeted supplement.
The source's coefficient direction is already mathematically correct;
this observation does not reopen broad numerical qualification or
block a correctly frozen real-direction study.

## Boundaries for the next experiment

The real driver must freeze and retain Q identity, complete scope,
all original support, beta/d exact identity, C_Q/a_K, initial true-stock
information, target tau and same-direction inherited lower. Target
zeta cannot exceed its frozen true-stock ceiling. Construction, explicit
LP diagnostics, optimization, validation and necessary I/O belong to the
new outer charge. Inherited prior mathematical lower and current solver
improvement must be reported separately.

The eventual coupled consumer must use C_Q+min(a_K,L_price), preserve
all old columns/supports, replay useful new support rows in free Q and
refresh the RMP after a final new column when necessary. Neither a
numerical RMP objective nor a finite-support LP upper is a full-hull
lower certificate. Nothing in this interface review asserts that the
new residual LP dominates the retained RN oracle or is faster.

## Reviewed bindings

- round154_residual.py v2 SHA256:
  04bfa84774b7be4603ec08ae88ba015d6351d2bd3109a1d599fd4709f18bbc50.
- round154_qualify.py v2 SHA256:
  22cf7ef5191f83e7ae6c9987fe15c0dadf972bbdbb319b1df0c09de9a730dc19.
- Representative MPS mathematical matrix SHA256:
  f626bad1c8bc0b14b796023d063dfab2f3e56dbc6dace8e86f73cd67a771b646.

Later supplemental qualifications or drivers need their own byte bindings;
this report does not silently admit later changed source.

## Targeted signed-rounding supplement (v3)

The parent subsequently executed the single requested finite supplement on
existing fixture2: costs use declared binary64 -.3/.1/.7 plus station*.013.
The main residual source remains SHA04bfa84774b7be4603ec08ae88ba015d6351d2bd3109a1d599fd4709f18bbc50.
The reviewer read the changed qualification source, the saved v3 summary,
its representative call and receipt without executing a new check.

The actual state downward errors now include 1/144115188075855872 on
both endpoint states of each station. Every legal exact minimal extension
still passes every written row/bound, the qualified residual lower remains
below enumerated true residual, and both recovery/transport signs pass.
The v3 result reports PASS and the closed receipt records exit0,
0.8705603000707924 outer seconds, no timeout/supervisor failure.
This closes the identified finite state-coefficient coverage supplement.
There is no new numerical-engineering work implied by the review.

- Qualification source v3 SHA256:
  cc231facd85be0976f8aebc347b33c2cfa6b355dfed5697b3878603f20551bd9.
- qualification/residual_v3/result.json SHA256:
  3b1a945a27d0e810f8aed9082a8078473fa10993e0d8c33d0dd50d40531486fd.
- fixture2_beta1.7_target1/model.mps SHA256:
  fd819a2596f63938a5ee3b285cc8028de93e747c5d1bbe8e414d2a4a47181015.


