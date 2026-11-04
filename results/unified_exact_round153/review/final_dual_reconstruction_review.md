# Independent review of final dual reconstruction

Reviewer: `/root/independent_review`, 2026-11-04 (Asia/Shanghai).

Decision at audit source SHA256
`26c960a4453716f4d73d17fbe103a8ccc2049acf7b2daa7a046150006007520b`:
**ACCEPT_MATHEMATICAL_DESIGN; FINAL_INTERFACE_PENDING_BINDING_FIXES**.
This review is static. No Native model read, Optimize, enumeration,
compilation or final evidence replay was performed by the reviewer.

## Exact Q residual

The proposed reconstruction has the correct signs. With sign-feasible
original-Q multipliers p, link multiplier pi, and beta >= 0, the original
variable residual is

`r = c - A_Q^T p + pi_on_state - beta_on_G`.

Use `C_Q = ObjCon + b_Q^T p + inf_box r^T x`, where the finite box is
derived only from original Q. The convexity RHS and the artificial
`1e-8` Gini margin do not enter this quantity. For every full-hull point,
the original objective is at least

`C_Q + beta G - pi^T state >= C_Q + min_R(beta f(Y) - pi^T v(Y))`.

Thus a qualified complete-domain price lower Lm implies the lower
`C_Q + Lm`. The stored single-correction form
`C_Q + min(aK, Lm)` is also safe. Independently reproducing the true
restricted-column minimum improves the audit of its RMP interpretation;
it is not necessary to make the preceding full-domain inequality safe for
an arbitrary finite aK. The final report should distinguish these claims.

The inspected `independent_residual` reconstructs all original column
residuals, row objective and bound contributions using exact fractions of
the actual binary64 matrix. It checks row multiplier signs, the repaired
Gini multiplier, non-anchor link multipliers and the omitted zero anchor.
It compares the full nonzero residual dictionary and exact support with
the saved certificate. A nonzero residual that needs an infinite endpoint
is rejected. `replay_q_bounds` validates each saved implication against
an actual Q row and already proved endpoints, including outward rounding.
This avoids trusting a bound derived from a restricted inventory master.

Two remaining bindings are required before claiming the final audit is
complete:

1. For every ordinary iteration, bind its actual price record to that
   iteration's scope and all states: `d_exact[i,y] == -pi.get((i,y), 0)`
   and equal beta. The current first pass checks beta but omits the price
   direction and scope comparison. Refined certificates already have this
   check. Correct C_Q and a correct price from a different direction do
   not compose into a lower bound.
2. The final `known` list presently admits `reference/direct/result.L`
   without independently reconstructing that reference certificate. Use
   the cached Q, replay `reference/implied_bounds.json.gz`, and check the
   reference `direct/dual_certificate.json.gz`, or omit that unverified
   value from the independently admitted list. No additional Native model
   read is needed. Also bind the selected scope to the reference domain.

The matrix reader should assert unique row and variable names and a
linear minimization model before converting rows into dictionaries. These
small checks make the complete-matrix assertion explicit.

## Actual restricted-column prefix

The proposed reconstruction from each phase's final `columns[:before]`
is justified by the inspected producer. A phase creates a Python ordered
dictionary from its initial sorted, deduplicated stocks. `Master.add`
only appends new stocks; Phase I removes artificial variables, not stock
columns. The certificate is made before that iteration's price stocks are
inserted. Each saved result preserves dictionary insertion order.
Therefore `columns_before`, or legacy `columns - added`, identifies the
column set used to form that certificate. Resuming in a different sorted
order starts a separate phase and does not invalidate an earlier phase's
prefix.

The replay recomputes each stock's exact f and its beta/pi price, then
requires equality with `true_column_min_exact` and
`a_true_RMP_exact = min(a_raw, minK)`. Recommended provenance assertions
are uniqueness of the final column list, first pre-add count equal to
`plan.initial_columns`, and continuity of adjacent recorded pre/post-add
counts, including Phase I price records. These reinforce the claim about
the actual RMP column set; the C_Q plus complete-price lower above remains
independent of that interpretation.

## Selected support-LP source

Auditing only iteration certificates would leave a real gap: the selected
K35 cumulative lower `0.2818261599167829` comes from a free-Q LP containing
qualified support rows, above the best individual iteration lower at that
checkpoint. NB35 also uses a floor-to-free-Q transfer. These sources must
be audited before accepting the final selected lower.

The new support branch addresses this by loading the selected all-supports
model, requiring identical original variables, bounds, objectives,
constant and Q rows, and requiring that all additional rows equal the
rows reconstructed from qualified complete-price records. Its beta and
per-station coefficient errors use the correct lower transport direction.
The added-row name set is exact. The saved free-Q dual is independently
recomputed with the already proved Q box, and the saved free-Q primal is
checked under the inherited numerical policy. This LP's primal upper is
not substituted for a complete-hull or physical upper.

The selected complete-hull upper separately retains the full original-Q
primal check, lambda mass/nonnegativity/full marginals and exact true-f
completion check. It remains a numerical primal qualification, not a
rational certificate. The final cumulative lower must be bounded by a
maximum of independently admitted sources with the same Q/scope; no
unvalidated checkpoint number may become a source merely by inheritance.

The planned six cached Native model reads and zero Optimize calls are
consistent with this finite audit design. Their serial execution, full
fee and successful output remain required after the binding fixes; a
static admission is not a claim that the audit has already passed.

## Closed bindings and optional zero extension

Decision for audit source SHA256
`baf965fa15f7a65f3a24227871eade2cfe95e816380e239847868b9f874651ab`:
**ACCEPT_STATIC_FINAL_DUAL_RECONSTRUCTION_INTERFACE**.

The new ordinary-iteration pass requires complete state coverage, equal
scope/beta and exact `d = -pi` before recomputing C_Q. The selected scope
equals the reference domain. The reference bounds and direct certificate
are independently replayed against the cached actual Q, and `known` uses
that reconstructed reference lower. `exact_matrix` now rejects a model
with a different sense, nonlinear constraints/objective, discrete variables
or duplicate row/variable names. The phase audit requires unique stocks,
initial count from the plan, continuity of recorded pre/post-add counts,
and equality with the final stock count. These changes close the listed
static blockers without additional Optimize calls.

The proposed reuse of an earlier support dual by extending it with zero
multipliers on new support rows is also **mathematically admitted**. It
must be evaluated on the current independently validated support matrix
and a Q-only proved box. All nonzero row multipliers must have the correct
sign. With identical retained rows and the same box, the row objective and
every residual are unchanged. If rows or bounds differ, a fresh exact
recalculation may yield another value; it is that new value which proves
a lower on the current matrix.

Only the recomputed value may enter `known`. A previously reported lower
is covered only after comparison with the new valid value. Record the
source dual SHA, current model SHA, added zero-multiplier row names and the
new exact residual result. Describe this as a reused dual witness checked
on the current matrix, not a reread or resolve of the old LP. The added
rows have already been independently proved from full-domain prices, so
this introduces no extra domain assumption or Native model read.

This optional zero-extension path was a design proposal at this review
point and had not yet been inspected as code. The six-read/zero-Optimize
final audit still needs its serial metered execution and saved PASS
record. The new Pe-minus-H output is an observation of saved points, not
a presumption about the cause of any slack or gap.

## Implemented inherited-support witness gate

**ACCEPT_STATIC_ZERO_EXTENSION_INTERFACE** for audit SHA256
`444ef9e5078e826525360912187f8b9cd2e344ae32db7810011b85b2e9a97360`.

The implemented `inherited_support_checks` path first requires the same Q
SHA and exact equality of every previous support row with the current
independently qualified row dictionary. It requires the previous multiplier
keys to be exactly the original-Q rows plus those support rows. It then
sets only the newly added current rows' multipliers to zero, and passes the
extended witness through `independent_residual` on the actual current
matrix and Q-only box. The exact row objective, complete residual vector,
support and lower must still agree with the witness. This deliberately
accepts the identical-box/same-row case and rejects a changed certificate
value; it does not silently adopt a different old bound.

Only `recomputed` enters the final known-bound list, after checking that it
covers the previous reported support lower. The source dual SHA, current
model SHA, explicit zero rows and exact new value are recorded, with
`old_LP_not_reread=True`. The current implementation therefore meets the
admitted conservative reuse contract and adds no model read or Optimize.
