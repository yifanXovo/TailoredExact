# Independent runtime admission: qualified target stops and full-Q coupling

Disposition: **ACCEPT** the registered uniform residual_goal mechanism for
K35 and NC20, limited to at most8 iterations,600 Native seconds per price,
6000-second offline phase allowance and hull tolerance1e-4.
Reviewer: `/root/review_round154`, independent of implementation.

The reviewer read the actual23-case goal_stop_v1 result, representative
Native plans/logs/returns/counterexamples, generated source-file hashes,
the closed qualification receipt and the latest loop source. It executed
no Optimize, Native model load, enumeration, compile, new performance run
or large pool audit. The parent executed the finite qualification once
under the serial outer meter.

## Actual target-stop qualification

The saved finite result reports PASS for20 signed target cases, two
mixed-zero cases and one unsupported-return case. Beta0 and beta1.7
use the same finite state/resource domain and both RN/residual target
implementations.

| Case family | Actual return | Saved qualification |
| --- | --- | --- |
| prove and far_prove, both beta values and both implementations | USER_OBJ_LIMIT15 | Actual finite Native bound, paid original guard/correction and recovered full-price lower reach the target; no counterexample file. |
| reject and early_reject, both beta values and both implementations | INTERRUPTED11 | MIPSOL callback verifies an original legal true stock with exact price below tau, preserves it in the result and saves its scope/price/source. |
| at_true, both beta values and both implementations | OPTIMAL2 | Paid guard leaves qualified lower below exact tau, with no false target proof or counterexample. |
| mixed legal zero | RN no Native call; residual2 | Whole-domain lower/upper remain .2 below tau, despite the residual positive branch alone supporting a higher lower. |
| unsupported SolutionLimit | SOLUTION_LIMIT10 | No qualified Native bound; only the original DP lower remains. |

These statuses are actual saved observations, not inferred from a requested
parameter. Representative Native logs state user objective limit,
interruption and solution limit consistently with the return records.

For RN beta1.7/prove, the saved parameter is BestBdStop=-.059997325,
Native bound .0025000000000000022 and scale4. Restoring anchor/guard/
coefficient correction gives qualified price lower-2.9900107, above
tau about-3.24, while the retained true warm upper is about-.33.
This is a target proof with a wide remaining price interval, not an
exact minimum-price solve.

For residual beta1.7/reject, BestBdStop is guard_scaled=1.723375e-6.
The actual own MIPSOL stock is Y=(2,1), true f=3/10 and exact price
-134657628858377831/45035996273704960, strictly below its saved exact tau.
The interrupted finite residual bound is still separately converted
after the original residual guard; it is not replaced by that incumbent.

The at_true residual example has a negative qualified residual lower,
full price lower-2.9901088160000002, upper about-2.99 and both target
flags false. This confirms the relevant guard behavior at the exact
price threshold.

In the mixed-zero residual example, positive_lower=.5599914249999999
does not supersede legal zero_lower=.2. The full result remains .2
and target_proved=false. RN returns its exact DP-attained zero value
without inventing a Native stop.

The unsupported10 example reports native_bound=null,
bound_status_qualified=false, safe_DP_fallback and lower=fallback=-7.915.
Rejection of an unowned interruption remains explicitly a source-level
condition; it is not misrepresented as an independently executed
interruption test.

The finite fixture's Gupper=.31 supplies margin at exact G=3/10.
This avoids the identified binary64(.3) boundary artifact in the new
stop test without changing a real research scope or the inherited
accepted numerical policy.

The actual source-byte persistence check passes. The representative
saved target_stop_source.txt hashes equal the generated RN/residual
source hashes in the plan/result; UTF8 write_bytes preserves the exact
LF source on Windows. The core and strengthened mathematical models
remain the previously qualified ones.

The unique closed outer qualification receipt is exit0 with
1.305602699983865 seconds, no timeout or supervisor failure.
Native Runtime/Work is nested and is not added again. These finite
calls are not performance samples.

## Latest coupling source and bounded rule

The latest loop includes explicit checks that the goal wrapper and all
three core/strong/RN source hashes match this actual qualification.
It retains the independently reviewed full-Q/current-pool/dual/ceiling
and final-refresh logic in target_coupling_design.md.

Every new direction has its own selected beta/exact d and original-Q
C_Q/a_K. Its fallback is same-direction DP only. The old global lower
is retained by maximum, but no old different-direction price lower is
borrowed. Every direction and its target/true-stock ceiling are saved
before pricing. A ceiling below zeta prevents that expensive call.

Only qualified complete-RMP primals lower U. New lower information is
C_Q+min(a_K,L_price), with existing guarded support transport. All true
returned stocks are reevaluated before entering the full pool. A fresh
negative column is now defined relative to corrected true a_K and the
record states that convention.

The inherited pending-refresh flag is honored. A new stock after the
last current RMP reopens that obligation, and all ordinary stop paths
perform a final qualified complete RMP if needed. No RMP objective
becomes a lower certificate and no finite-support LP upper replaces
the full-hull upper.

This admission covers the same registered residual_goal rule on K35
and NC20. It is not an automatic comparison grid, a time-based switch to
RN or an extension of the old fixed K35 long window. A later implementation/
parameter expansion requires an explicit recorded decision.

Before each launch, bind its actual prior result in the phase plan,
check its Q/scope and reserve the whole offline allowance plus necessary
validation within remaining144000-second capacity. Actual outer elapsed
remains authoritative; nested diagnostics and the reserved600-second
LP/selection/final-refresh allowance are not separately added fees.

After each completed phase adds supports, execute the registered
complete free-Q all-support replay or identify saved qualified point/
dual evidence proving the same value. That is an outstanding next-step
obligation, not a claim that the target loop itself measured a finite-
support optimum.

## Relation to the prior long proof and E panel

The parent reports the original3600-second K35 stronger residual has
returned a legal price below its old target, so the original fixed
ceiling is reduced. Its conditional RN skip follows the already
registered plan. This admission does not infer an earlier exact discovery
time from an old negative Native q, and no skipped matched-long control
supports a speedup claim. Actual long-result/ingestion/coupled endpoints
remain for subsequent data review.

The separate frozen B/E/J complete producer/reader/helper chain remains
unchanged. It does not import this offline loop. Neither target-stop
qualification nor a later stock-hull result establishes complete-method
E effectiveness, default promotion or a physical routing incumbent.

## Exact bindings

- round154_loop.py:
  1e8fc630635cb9dffc9aca969456b207f2564adcaac9d802826abafb8950e57d.
- goal_stop_v1/result.json:
  f8b7998872b4dcfb7e0442a43fd2f8fd0a00ceb151c5b088f3f74aa24868330c.
- round154_goal_oracle.py:
  8952bd342b0d8ad6de92dbb5fcd70faedfa0b161df0fb56873bb2d8e9ac9bdbf.
- Generated RN body:
  e63c465a4a122e51135888a19817151358d187bb61ba4486ae94bb333108ecaa.
- Generated residual body:
  e862255f7672c3e8e0020723909c73b93964da24a9528b7b16331bd37db9b32a.

All core identities and the exact runtime limits are also bound in
target_coupling_admission.json. Measured loop results and final scientific/
scope/cost review remain pending.

