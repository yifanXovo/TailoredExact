# Independent mathematical review of normalized integer pricing

Reviewer: `/root/independent_review`, 2026-11-04 (Asia/Shanghai).
Read-only theoretical review of the proposed structural revision. No
Optimize, enumeration, DP or other experimental program was run for this
note. This admits the mathematical design; implementation qualification
and observed performance remain separate.

**Disposition: ADMIT the proposed exact positive-denominator MILP.** Its
normalization is inherited from the standard transformation already studied
in R143, not a new general convexification theorem. The useful change here
is retaining the hard inventory and one-hot state integrality in a pricing
oracle, so no denominator-bin approximation is required.

## Positive-denominator equivalence

Use the original supported one-hot binary selectors x_iy and resource bounds
Bminus<=sum_(i,y) y*x_iy<=B. Let safe bounds cover every possible positive S:
0<S_min<=S(Y)<=S_max. Set t_L<=1/S_max and t_U>=1/S_min, with outward
conversion. For each station require

    t_L x_iy <= w_iy <= t_U x_iy,
    sum_y w_iy = t,
    t_L <= t <= t_U.

Binary one-hot x makes every unselected w zero and the selected w equal t.
Consequently normalized inventory U_i=sum_y y*w_iy equals t*Y_i exactly.
Introduce rbar_i=c_i U_i using the actual loaded c_i, and impose

    sum_i rbar_i = 1.

It follows that t*S(Y)=1 and t=1/S(Y)>0. Conversely every positive-S integer
inventory in the domain has the extension t=1/S(Y), w_i,Y_i=t and all other
w=0 within these safe bounds.

Let a_ij>=rbar_i-rbar_j and a_ij>=rbar_j-rbar_i. The minimum achievable
sum a is A(Y)/S(Y). The constraints

    sum a <= n*q,
    sum a <= n*gamma_U,
    q >= gamma_L

therefore admit an inventory exactly when G(Y)<=gamma_U, and the least q
is max(gamma_L,G(Y)). Minimizing

    q + sum_(i,y) (h_i(y)-pi_iy)*x_iy

gives exactly the positive-S pricing value in exact arithmetic. This proof
allows physical G below gamma_L; gamma_L is only the q lower bound. An
optional q<=gamma_U is also harmless when gamma_L<=gamma_U, because the
minimum legal completion always lies in that interval.

The inequalities Bminus*t<=sum_i U_i<=B*t are valid at each integer
extension and may strengthen the relaxation. They are the inherited scaled
stock information, not a new resource theorem. Binary x and the original
hard total rows must remain; scaled totals alone do not replace them.

## Zero inventory and full-domain coverage

Because c_i>0 and Y_i>=0, S=0 means Y=0. Normalization excludes it by design.
If all zero states are supported and the hard total permits zero, its exact
price gamma_L+sum h_i(0)-sum pi_i0 must still participate in the full-domain
minimum. A zero-only domain should skip the positive model entirely. If a
domain has positive supports but its positive integer resource set is empty,
only qualified model/DP infeasibility may remove that component.

For active-state pricing, use positive-S bounds valid for that active domain,
and keep the previously reviewed full-support complement DP. A normalized
active lower plus its complementary lower still gives a full-parent lower
through their minimum. Normalization does not authorize child-to-parent
transport by itself.

## Numerical and provenance boundaries

Read back the complete actual matrix and bounds after serialization. Use
separate normalized inventory variables with rbar_i=c_i U_i if this avoids
unnecessary rounded c_i*y coefficients. Upward transport of n*gamma_U
weakens its RHS safely; the n*q row has integer coefficient n. The unary
objective transport remains the existing exact per-station correction.

The MILP returns numerical, qualified lower bounds under the inherited
policy. A zero denominator-approximation error does not erase its MIP gap
or numeric guard. Native status qualification, rejected-result fallback,
and exact true-inventory rescoring for feasible pricing uppers remain
necessary. These are pricing uppers, not physical route incumbents.

Add the corresponding continuous RN and scaled-stock rows to the relevant
real strong reference to distinguish useful integer-epigraph information
from merely recovering old normalized LP information. Do not describe
this targeted control as every historical R143--R145 hull/disjunction.
The earlier three-station theorem retains its precisely declared reference;
it must not silently acquire an untested strictness claim over RN.

The appropriate focused qualification is equivalence on the already defined
finite inventory cases, including signed potentials, gamma_L above physical
G, positive/zero mixed domains and a zero-only domain, plus actual Native
matrix readback. Retain prior bin results and their paid costs as the
structural bottleneck evidence; do not overwrite them or compare their
intermediate bounds as if they were final values of the new model.

## Implementation and admission follow-up

The reviewer subsequently read `scripts/round152_normalized.py`,
`scripts/round152_global.py`, the updated `round152_lp.py`, and
`qualification_normalized/v1/result.json`, without running additional
computation. **The concrete offline normalized/full-support study is
admitted.** The code implements the above one-hot/common-t proof, retains
both hard and scaled stock, uses the exact actual ratio coefficients,
reads back the complete matrix, and retains zero as a separate component.
Finite Native bounds are accepted only for OPTIMAL/TIME_LIMIT; otherwise
the safe unary fallback remains. Feasible uppers are independently rescored
on the original integer inventory objective/domain. Negative prices are
preserved. No physical route incumbent is inferred.

The three qualification cases test 49, 7 and 1 feasible inventories. The
heterogeneous case contains its exact price between its saved lower and
upper but remains `UNDECIDED`, because the returned relative MIP tolerance
does not imply the separate absolute 1e-5 price-resolution condition. The
corrected fixture checks the configured relative/absolute gap plus the
declared guard; it does not change the algorithm or relabel that result.
Reusing the completed call for this corrected check is appropriate. The
earlier failed assertion and its charge remain retained.

The updated complete free LPs append historical continuous RN plus scaled
stock to `strongCP2`. They retain the actual original objective/rows and
all auxiliary freedom. Their qualified values are:

| Domain | strongCP2 | strongRN |
|---|---:|---:|
| N-B35-S | 0.3866980286738353 | 0.38673718656544753 |
| K-35-U | 0.2748619886989034 | 0.2788356429814587 |
| N-C20-U | 0.1744652677848382 | 0.17446526778483834 |

This control matters: the earlier small K35 cut-loop increment below the
strongRN value cannot be advertised as an increment beyond normalized old
information. The C20 difference is numerical equality. The small-domain
theorem retains its declared reference, which excludes RN; this follow-up
does not extend that theorem's reference silently.

The proposed next contrast uses full-support bounded residual potentials,
one anchored state per station, at most six master/pricing iterations and
120 seconds per normalized pricing call. Previously generated inventories
are admitted only after checking their actual current full domain and are
used as candidate-master constraints or upper candidates, never as reused
global lower bounds. Every final support intercept comes from new qualified
full-domain pricing and exact one-hot coefficient transport. The final row
enters a complete free LP, so point exclusion and optimized-value gain stay
distinct. This specifically tests whether weak complement lifting explains
earlier migration across a degenerate optimum face.

A sequence stopping on an unresolved 120-second pricing call remains
oracle-UNDECIDED for that direction. Six iterations are a finite search
budget, not an exhaustive theorem about all potentials or the whole
epigraph. Existing no-gain cells, costs and saved point separations remain
visible irrespective of the outcome of this stronger contrast.
