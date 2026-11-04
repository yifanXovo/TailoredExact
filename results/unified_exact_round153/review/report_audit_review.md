# Round153 reports and final audit: independent static review

Reviewer: independent nonimplementer. No Native call, compilation, model
replay, or evidence regeneration was performed. Inspected versions:

- `round153_reports.py`: `9408436b98ee6bcf7bc9b46dc6c58184a3c98cbdcfe0c149c9b94f03452187e3`.
- `round153_audit.py`: `ec98217c2079491ce0eb69ef7abcc3e2be009b6b783728112700e97b502106f7`.

Decision: accept the descriptive common-target design after the trace scope
is made explicit; the final arithmetic auditor needs the small provenance
and price reconstruction additions below before its PASS is described as
closing the segmented/refined certificate chain. These are reporting/auditor
changes, not evidence that an already qualified solver result is invalid.
The previously frozen production admission is unaffected.

## Trajectory scope and clock

`round108_reader.complete_cover` (lines 252--308) is the source of the saved
`qualified_cover.timeline`. For each CSV row it checks the arithmetic
`min(upper, active bound, other bound)`, monotonicity and basic consistency.
It independently supports the final live-leaf bounds and final physical U.
Its `recomputed_complete_cover_bound` field is the reported intermediate
number after this arithmetic check. Separately, `chronological_cover`
(lines 208--250) qualifies call/bound snapshots against their journal
sequences. Neither function joins every global-bound CSV row's time and
U/L pair to the exact physical witness and proof availability at that time.

Consequently, membership in a field named `qualified_cover` does not alone
make each intermediate row a separately qualified time-to-target witness.
The current reader is enough to describe the recorded guarded-controller
trajectory of a fully audited run. It is not enough to claim that every
plotted intermediate point has been independently qualified at its shown
time. The C++ writer also intentionally moves retrospective callback
observations to after native return; none should be called an exact native
first discovery.

Minimal correction: retain the raw recorded trajectory, explicitly mark its
intermediate rows as `recorded_controller_only` (no per-row proof-time
qualification), and mark only the separately sealed endpoint as qualified.
Rename the common-target time to an observed-controller-trace crossing time
and state that distinction in the exported table as well as JSON. If a
qualified target-availability column is wanted, use the sealed qualified
endpoint at T_produce when it meets that target, otherwise null. This can
coexist with the descriptive earlier observed crossing. There is no need to
replay every historical proof merely to produce a properly scoped diagnostic
table. `T_cert`, `T_verify` and `T_total` remain their inherited separately
reported quantities.

The proposed shift is conservative for the producer clock of an observed
event: writing `T_produce = before + process + after`, the last internal
trace time is no greater than the process duration, so
`T_produce - last_trace_time >= before`. Adding that full difference before
each internal event cannot make it earlier. This does not itself qualify
the bound at the event. Check finite, nonnegative, nondecreasing trace times
and retain the internal-clock endpoint discrepancy explicitly if using the
current 0.05-second allowance. The last row should not be earlier than a
previous one. Keep the endpoint as its own row, since the raw trace lower
can be clipped by its recorded U while the sealed endpoint retains the
qualified signed gap.

Selecting both arms' final U, L and gap values as shared targets is
acceptable as a posthoc descriptive comparison. The selection declaration
is already correct. A missing observed hit remains null; it does not imply
the target is unattainable or supply an imputed certificate time. No new
confirmatory performance conclusion follows from selecting these levels.

## Segmented price audit

The new recursive parent/child checks correctly require parent completeness,
child conditionality, adjacent closed intervals, matching scope and price
direction, exact true-stock feasibility and child S membership, and the
parent min-over-pieces/max-with-fallback algebra. However, the current
auditor trusts the saved `positive_S_bounds` and `fallback_exact`, and for a
leaf only hashes its model and checks that a return file exists. It does not
yet reconstruct that leaf's qualified price lower from its native return and
the stored scaling/guard/rounding transport. Thus its parent lower check is
currently a consistency check on already-produced child numbers, not an
independent arithmetic closure of their lower-bound chain.

Minimal additions, all in the separately metered pure audit:

- Recompute `s_bounds(scope)` and the hard-total DP fallback, or bind them
  to already independently audited exact values for that scope/direction.
  Require a nonempty positive interval cover whenever its exact upper is
  positive, and `0 <= child index < len(intervals)` with unique indices.
- For a leaf, bind call scope/beta/d to the result, return Status to the
  result's call, and the accepted offline statuses to the stored qualified
  bound flag. Reconstruct the same scale/anchor/guard/correction expression
  already used by `round153_read.floor_contract`, retaining the DP fallback
  on unsupported statuses and the independent zero branch only for a full
  parent domain. Check the published lower is outward/conservative.
- For a conditional leaf, check the declared restriction and actual t-bound
  metadata against its rational S interval, and bind the nested raw result
  to the conditional child result. DP attainment without a Native call must
  be supported by a true feasible in-slice stock; an absent call does not
  by itself establish the stronger branch.

The existing exact-stock upper checks are appropriate. This closes scalar
arithmetic/provenance under the admitted numerical policy; it does not turn
Native bounds into rational solver proofs or require re-solving any model.

## Refined certificate audit

The implemented one-convexity arithmetic is correct:
`L_m = max(all same-direction full-price lowers)`,
`delta = max(0, a_K - L_m)`, and `C_Q + a_K - delta`.
The source C_Q/a_K equality checks are useful. The missing link is that the
prices are only compared with one another, not with the source certificate's
direction and Q identity. Matching two scalar values does not establish that
link.

Require source and refined certificate qualification; equality of their
beta and pi; exact `d_exact = -pi` over the full pricing state set; and beta
agreement with every price. Recheck the refinement plan's stored source
certificate, source price and source-plan SHA values, its Q/scope identity,
and its prior-result SHA/lineage. Bind the source certificate to the already
audited iteration entry. These checks reproduce the safeguards already
present in the reviewed refinement generator, without a Native call or Q
re-optimization. Keep the source Q-only bounds and true-column a_K policy
unchanged.

## Static review of the first repair

The subsequent reports version SHA256
`1944c9fe5f54bca7536f29f9b8dbe958c5b377aa83b0fa914181475b3bd63814`
now marks every intermediate row `recorded_controller_only` and the sealed
endpoint `qualified_endpoint`, disclaims individual intermediate value/time
qualification, and separates observed shifted trace crossings from qualified
endpoint producer availability. Its target directions, null handling and
posthoc declaration are correct. The input trace time checks now reject
nonfinite, negative or decreasing times. This closes the substantive reporting
scope issue. The remaining 0.05-second end-time tolerance should be made
explicit or removed, since appending an endpoint at an earlier T_produce
would otherwise make the combined output rows slightly nonchronological.

The subsequent audit version SHA256
`65455855a7adbeedd5735285f617f9652d8fdd27cccf06da66d4e8cef6ece03c`
adds cached exact domain/DP reconstruction and full pricing-state coverage;
positive-domain/nonempty-cover and child index checks; call/result scope,
beta, price and return-status matching; exact centering and power-of-two
scaling; and reconstruction of the guard and coefficient transport from the
actual serialized MPS objective. Using `Fraction(float(MPS_token))` is
appropriate here because the certificate concerns the binary64 matrix loaded
by Native, with the producer's existing matrix readback check retained.
Unsupported statuses keep the exact DP fallback. Full-domain zero is
included independently while a positive-S child excludes it. The max/min
directions in the rebuilt price lower are correct.

Refined certificates now require qualified source/refinement, equal beta/pi,
price direction equal to negative source pi, matching Q/scope across source,
prior and new plans/results, and the source certificate, price and prior
result SHA values. A legacy first refinement without `source_plan_SHA` still
has its actual source plan Q/scope checked; this is an acceptable explicit
compatibility case and does not require modifying old raw evidence.

Two small source-to-evidence links remain to close this audit gate: compare
the child/result, raw call and restriction t-bound metadata with
`[down(1/S_hi), up(1/S_lo)]` and bind its nested raw result to the outer child
result; require the refinement source certificate to belong to the resolved
paths already audited in the iteration-certificate pass. These additions
need no Native call or new small-domain qualification. No mathematical error
in the newly added transport reconstruction was found by static inspection.

## Closed static interface gate

**ACCEPT_STATIC_REPORT_AND_AUDIT_INTERFACE.** The final inspected reports
SHA256 is `a3e67be9769ac58eb4705055d9f6f3676af969c0b62d1e5b93b5c3d8ac569fe8`
and audit SHA256 is
`524ca011ec139df31adeedcfdac4cdfa3da9b1ef323a3a58cde124911eed5789`.
Reports now require the last internal trace time to be no later than
T_produce. The conditional Native leaf check binds result/call/restriction
t-bound metadata to the exact outward reciprocals and requires its nested
raw result to equal the outer child result. A no-Native child retains only
the separately reconstructed safe DP lower. Refinement sources must belong
to the resolved iteration paths added only after successful iteration audit.
The previously listed interface blockers are closed.

This acceptance is a static code review, not a claim that the pending final
audit has executed or passed. Its serial metered execution and evidence
result remain required. The numerical policy and descriptive trajectory
scope above remain in force; no Native or evidence replay was run by this
reviewer.

## Direct outer receipts and retained partial phases

**ACCEPT_STATIC_PHASE_RECEIPT_REPORTING** at `round153_reports.py` SHA256
`7fe0a81824d7848abbdf870acf92e263dca5bcf3661f1a51b703e383471ddc81`.
This addendum reviews only the new postprocessing identity and display
fields. No report program, Native, Optimize, compilation, evidence replay
or heavy-I/O validation was executed.

`phase_receipts()` extracts the actual script and argv from each outer
launch. Its role/label mapping matches the entry signatures for coupled,
refine, overlay, primal_pool run, and attribution floor_close/support_close.
The latter use the role and final label and can create both a coupled
result and separately stored support-LP evidence under one direct fee.
The report retains the direct receipt label, SHA, observed-exit flag,
exit code, timeout, supervisor failure and charged G1 seconds. It does not
substitute a phase's possibly inherited `stored_seconds` for that fee.

The closed NB launch `coupled_NB_initial_02` was read as a small metadata
record. Its argv selects `N-B35-S initial_v2`; its receipt has observed
exit, code 1, no timeout or supervisor failure, and G1 seconds
`305.1443431000225`. Therefore its preserved raw `decision='RUNNING'`
must be presented with the closed retained-partial failure state, not as
an active phase or a normally completed scientific result. The new code
does so without rewriting the raw decision or any bound. Its failure
classification also honors timeout and supervisor-failure flags rather
than relying only on the child exit code.

A missing direct receipt match yields `NO_DIRECT_OUTER_MATCH`, and a
matched but unclosed outer yields `OUTER_NOT_CLOSED`. Neither is converted
to a zero fee or a claim that a process is currently alive. The combined
direct G1 field is populated only when all matched outers have observed
closure; the individual receipt records remain visible.

The initially ambiguous call counts were corrected to
`phase_directory_Optimize_call_artifacts` and
`phase_directory_calls_without_saved_return`. Their explicit scope is only
the coupled phase's own directory, excluding separately stored support_LP,
qualification and inherited artifacts. This is necessary because an
attribution phase may have its actual Optimize calls under support_LP.
The fields are not a total Native-call census or another fee total.

In particular, a call artifact without a saved return is only that: it
does not establish a completed Optimize, a qualified bound, or an active
process. The original interrupted NB pending call can be counted and
retained while its outer is known closed. Completed price evidence and
production Native counts remain in their separate tables, and the unique
outer ledger remains the authority for charged time.

No frozen experiment, raw failure, model, bound, producer or accounting
receipt changes as a result of this reporting addition.
