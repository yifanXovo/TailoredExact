# Static review of the finite audit and report generators

Reviewer: independent nonimplementer for the adopted Round154 goal, section H.
Scope: source and small retained metadata only. This review ran no Optimize,
compilation, enumeration, or performance task. The final audit, the nine full
confirmation arms, and the generated final scientific packet are not yet
accepted by this document.

## Sources inspected

| Source | SHA256 at this review |
| --- | --- |
| `scripts/round154_audit.py` | `2f6a81d21fc1c79f408092a230a25f7e164d5252c649875166e8436c4fd9e4b7` |
| `scripts/round154_reports.py` | `7d8841ac920fb13b2bd21e409b25d95227fcd2a8f9dbbcaf84a7a16e8ac8091e` |
| `scripts/round154_writeup.py` | `99ff5b20f0bc3c9f8098edeb7bb2d5749cb0ed219ca873c7f994d9bc74d0df4a` |

The audit was inspected together with the actual `exact_matrix`,
`independent_residual`, original-Q primal checker, current loop/coupling
writers, and the sealed complete-method endpoint writer. Earlier mathematical,
pricing, scope, and production admissions remain separate records.

## Corrections read back

The current audit substantively includes the concrete corrections requested in
this static review:

- The residual MPS check requires a zero objective constant, continuous
  non-state variables, negative-unbounded residual epigraph, and a free signed
  hard-cost product. All declared rows are checked against actual coefficients.
- Goal-stop plans bind the wrapper and generated body to the already successful
  stop qualification, in addition to their own saved hashes and thresholds.
- A support replay must contain the exact original free Q variables, objective,
  bounds, constant and rows, followed by precisely the declared support rows.
- Loop step lower/upper endpoints are recomputed from the prior endpoints,
  qualified Q certificate, corrected true-column intercept, price lower and RMP
  objective. The selected endpoint history recursively retains fixed R153
  hashes and newly certified contributions. Ingest preserves the old full-hull
  upper; finite-support replay does not replace it; full refresh uses the
  smaller qualified RMP upper.
- An inherited primal is checked by its explicit inventory distribution rather
  than reinterpreting old lambda indices in a newly sorted or enlarged pool.
  The checker validates the original-Q point, legal stock values, mass,
  marginals, completion and objective under the stated numerical policy. It
  expressly does not claim an exact rational primal.

These are source-level findings. They do not assert that the unrun finite audit
has passed on the eventual data.

## Two remaining small binding checks sent to the implementer

1. The final `science_state` support replay must be bound to the selected final
   scope/Q and all its supports, and to a replay certificate actually checked by
   this audit. Iterating over every existing support replay alone cannot prove
   that the last added support set was replayed. `spec.support_result` is
   presently reported but not consumed by the audit. This matters to the final
   prose claim that every accumulated support was replayed in the full free Q.
2. The nine reported endpoint tuples must be compared with
   `audit.json.endpoint`, not merely carry its correct SHA. Compare at least
   U/L/gap/certificate/T_produce/T_cert and arm/input/PE identity. Bind reported
   T_verify/T_total to `arm_total_receipt.json` and its existing clock chain.
   The sealed writer already saves these records, so this requires no raw
   replay or new solve.

No additional numerical qualification or production-source change is requested
by these findings.

## Report and claim inspection

The generators keep fresh prices separate from inherited same-direction
information, fixed-certificate ceilings separate from full-hull uppers,
finite-support uppers separate from RMP full-hull uppers, and LP-value uppers
separate from physical incumbents. They do not concatenate different directions
as a monotone price trajectory. The original K long true counterexample and
conditional RN-long skip are not presented as a matched-long speed result. The
failed first K stabilization is not presented as an inventory-pricing negative.

The intended writeup retains E as research-only/default OFF, stable B unchanged,
finite single-seed attribution limits, and no universal RN dominance or pricing
speed claim. The three nonzero-exit metered receipts presently present have both
stderr and per-run source snapshots; that specific retained-failure statement
has actual support at this point.

The generator's hardcoded successful-final-audit path must be set to the actual
successful label before generation. The eventual conclusion, all numerical
tables, endpoint identities, costs, last-refresh/replay obligations and manuscript
wording still require review against the actual completed outputs. This document
is a static implementation review, not final scientific approval.

## Follow-up readback: both remaining bindings implemented

The updated `scripts/round154_audit.py` SHA256 is
`6370de3853b2502b1b98aa1e64bea15e80e7a1e7ec238d1b3e84569c396ef037`.
The reports and writeup source hashes remain those in the table above.
This follow-up again consists only of static source and small metadata reads.

For a new final support replay, the code now requires the selected final scope,
Q hash and exact complete support list, the declared full-free-Q replay flag and
row count, and membership of its certificate in the list whose actual matrix
and certificate were independently checked earlier in the audit. This closes
the first outstanding binding.

The unchanged NB evidence legitimately uses its original R153 format instead.
I read `results/unified_exact_round153/support_LP/N-B35-S_floor_closed/result.json`
(SHA256 `950e8986a3deb151fe5a3054a59096c9a6531dde11722faf74a774e05bc64a1c`):
it contains `records` with the `all_supports` stage, `rows=9`, `coupled_source`,
and the original Q hash, without the newer `scope`/`support_replay` wrapper.
The adapter binds this exact inherited result through the fixed-member reuse
index, matches the coupled source scope and support list, and checks all nine
rows were replayed with original Q variables free. No NB rerun is needed for
that representation difference. The final science table separately binds its
lower/upper to the maximum/minimum of the selected result and the accepted R153
global endpoints. This is necessary because NB's older coupled result predates
its later support-replay lower gain.

For all nine new complete arms, the code now compares
U/L/gap/certificate/T_produce/T_cert/arm_id/PE/input with the sealed
`audit.json.endpoint`, binds the total-receipt SHA and its producer/closeout
hashes, and compares reported verification/total time with that receipt. It
also checks the frozen group identity SHA and candidate PE. This closes the
second outstanding binding without repeating the raw verification.

Disposition: no unresolved concrete defect from this static review of these
changes. The reuse index and final science state/report files must exist at the
actual audit invocation; they are not yet claimed to have passed. Successful
execution, the nine actual arms, final report claims and the independent final
scientific decision remain outstanding.
