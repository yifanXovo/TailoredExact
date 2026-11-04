# Independent review of near-optimal dual selection

Reviewer: `/root/independent_review`, 2026-11-04 (Asia/Shanghai).

Verdict: **ACCEPT_FOR_TARGETED_DEEPENING**. The explicit dual construction,
price signs, candidate band, and final certificate connection are correct.
The saved small all-column control passes. The uniform optional selector may
be used on K35 or another observed pricing/degeneracy bottleneck without
restarting the earlier column-generation work. It is a discovery step, not
a new valid inequality or a substitute for all-domain pricing.

This reviewer only read the new sources and the small saved qualification
record. No new Optimize, Native load, compiler, large read or validation run
was started. The primary agent ran the qualification through its serial meter.

## Inspected implementation

- `scripts/round153_stabilize.py`, initially inspected SHA256
  `3a86f3f1241082060226c8d0a174a3aafb63e457130557942fc9de572500002d`.
- The optional `stabilize` path and supplied-multiplier certificate interface
  in `scripts/round153_coupled.py`, initially inspected SHA256
  `7cbaa54f809580581bebc81556ec11c16787f3adee1e130b24341ea12c0a21aa`.
- `stabilize_control` in `scripts/round153_qualify.py` and
  `qualification/stabilized_v1/result.json`, result SHA256
  `e2a27b59db7874e24ae35187326e8fca0e4f6193d1f1b8d694ccd141f390d76a`.

The parent was asked to include the selector's up-to-120-second call in the
outer reservation or pass its remaining cap, and to record the realized
candidate dual objective/band loss. These scheduling/reporting additions do
not alter the reviewed mathematics and do not require old experiments to be
rerun. Normal source snapshots must identify the actual run version.

## Explicit-dual signs

For the current minimization RMP with row multipliers p, lower-bound
multipliers l and upper-bound multipliers u, the constructed system is

`A^T p + l + u = c`,

with `p>=0` on a primal >= row, `p<=0` on a <= row, free p on equality rows,
`l>=0` for finite lower bounds and `u<=0` for finite upper bounds. Its dual
objective is

`ObjCon + b^T p + LB^T l + UB^T u`.

The code uses exactly these signs and includes every current RMP column and
row, including the lambda columns and their lower-bound multipliers. Infinite
bound endpoints do not receive multipliers. The requirement

`b^T p + LB^T l + UB^T u >= RMP_ObjVal - band - ObjCon`

therefore has the correct orientation and constant. In particular, a lambda
column gives `a + pi*v - beta*f_hat + l_lambda = 0`, so nonnegative
`l_lambda` enforces the intended written-column reduced cost
`beta*f_hat-pi*v-a>=0`.

The original Q is not altered. The selector creates a separate auxiliary
LP; its current-RMP band is not imposed on original x, G, s or routes. There
is no fixed marginal, primal face equality, or old .05 potential box.

## Candidate objective and its scope

With the omitted anchor state at each station, the center is
`pi_iy = h_i(anchor)-h_i(y)` and `beta=1`. This is the station-gauge version
of the floor direction `pi=-h`: its inventory price is phi minus a station
constant. It is a reasonable deterministic AP-based price center. It is
not automatically a feasible complete dual vector by itself; the auxiliary
LP finds a feasible near-optimal written-RMP dual closest to that center.

The secondary objective is the sum of absolute deviations from that center
plus `abs(beta-1)`. Its absolute-value linearization is correct. It does not
fix an instance-specific radius or discard a necessary part of the inventory
domain. Other Q and bound multipliers remain available to satisfy the full
column equations. The norm can improve price structure but does not prove
that any resulting full-domain price is easy or that the hull value improves.

RMP ObjVal is used only as a **candidate-selection threshold**. The band is
numerical and the selector's feasible-point check has a tolerance. It must
not be described as an exact optimal face or as a whole-face separation
certificate. If numerical infeasibility/status prevents selection, the code
falls back to the original RMP dual. Recording the realized dual objective
and achieved band residual will make the near-optimal description directly
auditable; no additional mathematical qualification depends on that label.

## Final-bound connection

When selection succeeds, the same selected row multipliers provide a, pi,
beta and the original-Q certificate. Gini-row beta is sign repaired in the
same way as the certificate. The selected bound multipliers are not blindly
accepted as all-domain restrictions: the final engine recomputes every
original-column residual and its support over bounds proved on Q before
finite columns existed.

The 1e-8 Gini margin is part of the written RMP used to choose a dual, but its
RHS contribution is still excluded from the final target-hull certificate.
True Fraction column values still correct the restricted intercept to a_K.
The full-domain true-price lower then causes one convexity correction. Thus
selection cannot turn RMP ObjVal or the auxiliary LP's objective into a full
hull lower, even if its numerical band is imperfect.

The existing support-row transport and beta=0 interpretation remain intact.
The implementation only invokes this selector outside Phase I. Phase I
continues to price its artificial objective directly and never produces a
normal strengthened-LP upper.

## Saved targeted control

`qualification/stabilized_v1/result.json` reports PASS. The test constructs
the known 49-inventory small domain, begins with a deliberately restricted
single column, selects the new dual, prices it over the full domain, and
qualifies the bound with the selected multipliers. It checks

`0.19583092083333287 <= 47/240 <= 1.291666676666667`.

The selected beta is 1 and the true-stock reduced cost is negative
(-1.0958333333333334), so the selected direction is correctly connected to
column discovery. The result explicitly records that no potential box or
primal-ObjVal-as-dual shortcut is used. This is an interface fixture, not a
performance observation. Its selector's nested time is not charged again
on top of the parent outer fee.

## Research gate and remaining interpretation

Reuse the completed K35 columns and RMP upper when applying this targeted
deepening. The new calculation should reveal whether a near-optimal dual
with simpler inventory costs produces a materially better certified lower
or identifies a narrower pricing bottleneck. It does not require the earlier
initial cycle to be rerun.

N-B35's near-closing scalar-floor bracket is a separate favorable structure.
Its proposed same-Q free-LP transfer must be checked before calling the
coupled interval closed. Neither that closure nor a successful stabilized
small fixture is evidence of complete B/J performance. The existing pure-B
floor decision and any later production qualifications retain their separate
cost and scope requirements.

No new mathematical blocker was found. The remaining conditions are the
existing full-domain pricing/primal qualification, honest unresolved status
when an interval stays wide, explicit outer-cost accounting including this
selector, and a result-based decision on further targeted depth.
