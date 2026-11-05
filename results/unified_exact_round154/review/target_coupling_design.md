# Independent static review of target-oriented full-Q iteration

Reviewer: `/root/review_round154`, independent of implementation.
Disposition: **ACCEPT_STATIC_DESIGN; RUNTIME_ADMISSION_PENDING**.
The goal-stop finite qualification and actual starting-result identities
remain prerequisites for expensive execution. No unrun iteration, bound,
column chain or final refresh is described as a measured PASS.

This review read round154_loop.py, the reused Master/support/dual-selection
and guarded target-oracle interfaces, and the prospective finite stop
qualification. It performed no Optimize, Native model load, enumeration,
compile, large pool read or performance experiment. The existing K35
fixed-cap long price was not modified or disturbed.

## Uniform object, current pool and bounds

The proposed K35/NC20 rule uses the same target residual oracle,
at most8 iterations,600 Native seconds per price,6000-second offline
phase allowance and absolute hull tolerance1e-4. Role-specific input
data and already paid prior result differ; there is no role/winner/size
branch in the iteration mechanism. RN_goal remains an explicitly
separate comparison implementation, not a timed component switch.

The loop binds its starting result to role, original Q SHA and scope.
It creates one original full Q/Master with every retained legal inventory
column, keeps all prior support records and current accumulated lower/
numerical full-hull upper, and does not narrow original supports or fix
route/load/time/auxiliary variables.

Every normal iteration first solves that complete current RMP and
requires the existing full Master primal qualification: original matrix,
lambda mass/nonnegativity, every marginal and true completion.
Only such a feasible complete RMP point may lower U. Its objective is
never substituted for a lower. Any previous qualified upper remains
valid as the pool grows, and new best points/stock weights are preserved
as upper witnesses.

The full Master already implies valid inventory-price support rows by
its legal-stock distribution and completion constraint. Carrying those
rows without explicitly appending them again to that RMP therefore
does not weaken the intended hull. A separate finite-support/free-Q
replay is still needed for attribution of the new supports.

## Each direction is independent and frozen before pricing

The selected zero-centered near-optimal dual remains a candidate only.
For that actual current RMP, the existing Master computes original-Q
residual support C_Q and true-column-corrected a_K. Its finite Q bounds
are derived before adding restricted columns.

Each iteration's d is derived from that selected pi, and its price
fallback is the same-direction hard-total DP plus beta*gamma_L.
No previous iteration's price lower, selected midpoint or another
direction's native bound is carried into this price. The only cross-
direction inheritance is the already valid accumulated hull lower.

The target is zeta=current qualified U-tolerance, with
tau=zeta-C_Q. The best four true initial price stocks are screened from
the complete current pool. The frozen single-certificate ceiling is
C_Q+min(a_K,initial_true_price_upper). The loop saves actual scope,
Q, beta/exact d, C_Q/a_K/tau/zeta, warm stocks, column count, fallback,
Q-bound source and provisional certificate before any price. It refuses
an expensive price if that ceiling is below zeta.

This is a fixed-direction feasibility check, not an assertion that the
full hull upper equals that ceiling. A returned stock below tau refutes
this iteration's target only and can supply a useful column for the
next complete master. Different iteration price values cannot be
plotted as monotone same-direction price convergence.

## Lower, support and column consumption

The returned lower is consumed through

    L_direction=C_Q+min(a_K,L_price),

and maximized with the accumulated old hull lower. The saved certificate
updates price lower, D_K, delta and coupled lower consistently while
retaining the same selected Q dual, beta/pi and true a_K. The old RMP
completion margin is not inserted into a lower certificate.

Every returned stock is reevaluated in the original scope and exact
price before Master.add. All true returned stocks are eligible for
the retained pool, including useful columns from a target-refuting
interrupted solve. Auxiliary q/A values are not price/column authority.
The current true upper and updated fixed-certificate ceiling are
recomputed from original price values.

The new support row uses the existing guarded full-domain price and
its previously qualified one-hot/G coefficient transport. Prior supports
remain, and source price/direction identities are recorded.

The reviewed source now counts a fresh negative column against the
true-column-corrected a_K and records
negative_column_reference=true_column_corrected_a_K. This closes the
initial reporting ambiguity of comparing to raw numerical convexity
multiplier a. It makes the stated negative-column continuation criterion
consistent with the corrected certificate. No unqualified tiny price
difference is relabelled as a universal family gain.

## Termination and last-column obligation

The loop can stop for requested hull accuracy, an insufficient chosen
ceiling, no new column, no new negative column, the finite iteration
allowance or the whole offline phase allowance. These are recorded
finite outcomes, not exhaustion claims or instructions to start an
automatic grid/long rerun.

The initial refreshed flag inherits the prior pending-column state.
Every completed qualified RMP evaluates all columns then present.
Every later new column makes refreshed=false. All ordinary break
paths then reach the common finalization: if any column remains
unevaluated, exactly one further complete RMP solve with qualified
Master primal is required before clearing the flag. Its feasible
upper may improve U; no lower is claimed from that solve.

Consequently a target proof followed by newly returned columns,
a final iteration with new columns, a no-negative-column stop, or an
early phase-budget stop cannot silently leave the last pool unassessed.
If no new column exists and the inherited pool was already assessed,
no duplicate refresh is required. Failed selected-dual or primal
qualification raises and leaves an explicit incomplete attempt rather
than a fabricated successful refresh.

The600-second reserve before starting a new price covers the planned
LP, dual selection and final-refresh allowance. Actual construction,
full-pool true-price sorting, validation and I/O must remain in the
unique outer elapsed receipt. The phase's configured allowance is
not a claim that nested capped Native durations exhaustively measure
wall time; the outer supervisor and remaining144000-second capacity
remain authoritative. This is normal offline allowance handling, not
an internal algorithm switch after k seconds.

The unconditional final last_columns_evaluated claim is justified only
by these successful control paths and trusted inherited refresh state.
An interrupted outer has no successful final record and must not be
reported as this completed phase.

## Separate support replay and later admission

After a completed loop appends supports, the parent retains the existing
complete free-Q all-support replay as a separate required next step,
unless a saved qualified point/dual already establishes the same result.
The lambda RMP is not a substitute for a finite-support LP attribution
measurement, and that replay's primal upper must not replace U_hull.

An unresolved no-new-negative-column endpoint still may have a useful
fixed ceiling and price interval. Any next long proof needs its concrete
target/cost rationale. An iteration cap alone does not support a negative
statement about the inventory family.

Before runtime admission, the actual goal-stop qualification must pass
and be read independently, actual starting result hashes must be frozen,
and the source/parameter rule must be recorded. A source-level gate
placeholder is not evidence that this has happened. The frozen E
complete chain remains unchanged and independent.

## Prospective finite stop qualification and source-byte addendum

The new finite qualification reuses the original small state/resource
domain with Gupper=.31. This preserves a true margin around the stock
(2,1), whose exact G is3/10 and would lie slightly above binary64(.3).
With the chosen cost it would otherwise be an especially attractive
Native tolerance-boundary stock. Moving this fixture cap avoids
mistaking inherited tiny boundary behavior for a new stop-interface
defect; it does not change any real research domain or numerical policy.

The prospective tests cover signed/beta0 target proof/refutation,
at-true guard behavior, early own-counterexample interruption, mixed
zero composition and an unsupported SOLUTION_LIMIT10 fallback.
The code requires observed USER_OBJ_LIMIT15 and INTERRUPTED11 somewhere
in the finite run; actual observation remains pending. Unowned
interruption rejection is explicitly static, not falsely claimed as
an executed failure test.

The wrapper now writes generated source with write_bytes(UTF8), so its
saved SHA corresponds exactly to the generated LF source on Windows.
Relative to the earlier target_stop_design.md source this is a byte-
persistence repair only; the guarded thresholds, callback legality and
status rules are unchanged.

Reviewed identities:

- round154_loop.py:
  65bb74b470329e1e9f55c28652bc842a067dbaf2eabc97b2c0907bdd08298dcf.
- round154_goal_oracle.py:
  8952bd342b0d8ad6de92dbb5fcd70faedfa0b161df0fb56873bb2d8e9ac9bdbf.
- prospective round154_goal_qualify.py:
  b9a01622d93025afb265340b473fcb96adaca3ffd62506a502cf59869df5c830.

Actual finite qualification, updated K35/NC20 tasks and measured coupled
results still require later independent review.

