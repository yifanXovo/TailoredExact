# Independent limited review: complete C1 Seed0 AM panel

Disposition: **PASS within the stated scope**. Reviewer
`/root/independent_review`, 2026-10-28 (Asia/Shanghai), while the serial C2
queue remains active. This extends `C1_first_three_role_review.md`; it is not
final120, Seed1, rendered-paper or PDF acceptance.

Read the declared matrix, twelve small sealed endpoints, the three new K35
parameter/control/closeout JSONs, the small AM/all-child decision CSVs, and
the relevant authoring/analyzer source. Reused the earlier nine-observation
review and source-extracted only the existing pure `am_decisions` join with
stdlib CSV handling. No heavy reader import, native experiment, build,
LP/journal parsing, full aggregation, archive or PDF was performed. Only this
review file was written.

## New K35 observations

Selected by declared role/method: default position14 (`S2`, tau=.08),
position79 (`AM004`) and position80 (`AM016`). All three are qualified,
performance-eligible and open, with own U=.6928543586313136 and null T_cert.

| tau | Position | Qualified L | Production seconds |
| --- | ---: | ---: | ---: |
| .04 | 79 | .5658933785230834 | 2371.0239623694215 |
| .08 | 14 | .5657656814649950 | 2371.1518578070680 |
| .16 | 80 | .5661057354376344 | 2371.0279437834397 |

Each has exactly one joined child-decision row:
`FINITE_TERMINAL_NO_STRICT`, raw S_AM=1.4881893169531749e-17,
selected action `exact-close`, and `finite_score_gate=false`. Paired finite
child observations therefore exist, but the no-strict-improvement terminal
precedes the threshold gate. The stored numerical margins (approximately
-.039999824/-.079999824/-.159999824) do not turn these rows into actual tau
tests. An exact-close scheduling action does not supply a certificate; the
three sealed endpoints remain open.

The small parameter readbacks confirm actual post-preset .04/.08/.16,
all deletion flags false and `loaded_after_presets=true`. Control audit
readback hashes and pre-closeout checks match. Closeouts are complete and
their endpoint hashes match. The K35 runs share the pinned production
source779713ad and PE d6fd9e66, identical input SHA, lambda=.15,
T=10800, pickup/drop=60, Q=[20,25,30], cap=2400 and Seed0. Their independently
complete H semantic/fleet hashes are nonempty and match within this role.

## Full Seed0 counting and prose

There are twelve observations: eight additional C1 positions73-80 and four
shared, actual B1 defaults3/7/12/14. At each tau, the same four roles yield
two certificates (K15 and UC) and two open endpoints (K20 and K35).
Per-role input/PE/physical/cap/H hash comparisons pass across the three
thresholds. This is four roles observed three times, not twelve independent
inputs.

The small joined ledgers contain nine `FINITE_SCORE_GATE` rows, twelve
`FINITE_TERMINAL_NO_STRICT` rows and nine `LOGICAL_ONE_INFEASIBLE` rows.
The nine genuine gates are the already reviewed K15/K20/UC scores
.00035668721841524304/.00047846635674276053/.00031862963447695959,
each repeated at three thresholds and far below .04. UC's nine logical
splits have null finite score/margin and are counted separately. K35 adds no
finite gate.

The inspected Section6.1 source correctly restricts maximum-score table
cells to `finite_score_gate`, distinguishes K35 from both logical splitting
and missing child records, preserves open/null-certificate status, and
limits conclusions to observed states. The earlier K15/UC certificate-time
differences remain below the declared materiality rule. K20/K35 capped
lower-bound differences establish neither a general tau ranking nor general
threshold insensitivity. No scientific wording correction is required in
this narrow scope. Seed1 checks remain separate and were not reviewed here.

## Explicit deferred guard audit

Independently performed **stat only** for each of these twelve runs'
`audit.json`, `external/paper_leaf_ledger.csv` and
`external/split_decision_ledger.csv`: combined size **101292893 bytes**.
Their contents were not opened; this exceeds the 2MB light-review boundary.
Depth8/minimum-width1e-4 remain fixed policy parameters, not an independently
established absence of guard triggers. The AM rows cannot establish global
guard non-activation. The full recorded-guard/source-rejection/retained-epoch
audit remains deferred to formal analysis when native timing is idle.

Authoring source SHA at review:
`38b47743450b25f53e321d0efa6d848687f3f701fcbc9f57bccc9effedc91692`.
