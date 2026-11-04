# Independent static review of the registered queue

Reviewer: `/root/independent_review`, 2026-11-04 (Asia/Shanghai).

The sequence and accounting design are **ACCEPTED**. Before first launch,
close the two small receipt/identity checks below. This is only a static
review of the new orchestration and reporting connections; no computation,
Native, replay, compilation or heavy-I/O validation was performed.

Inspected `round153_followthrough.py` SHA256:
`01329948e85f5c12b1d6b262a866b3668535297258b884a960821f8ea3425c79`.
Inspected `round153_reports.py` SHA256:
`5e7d21026d52c9935cd390242688a41053dc5454751d498e17557bdeb701463e`.
Inspected working report SHA256:
`8f4b67c714db61679af87a8c776c0f8fbb3dfd6e597e1047c9f526c47ac499cf`.

The supervisor requires no open outer receipt and the completed K35 long
price predecessor. It then runs the graph qualification, both same-direction
graph probes, NC20 fixed-direction long price, K35 and NC20 zero_pool,
the two free-Q support closures, and the already frozen eight-position
campaign. All calls are synchronous. Research children each use one
`common.run` receipt; the campaign meters its own arms and is not wrapped
in another fee. A child failure raises before a successor starts. Existing
fee folders are never relaunched.

The data chain is correct: NC20 transport result feeds the graph probe,
whose complete state feeds the 1800-second fixed-direction refinement and
then zero_pool. K35's completed 3600-second refinement feeds its graph
probe and zero_pool. Both refinements retain previous bounds, supports and
legal columns. Both zero_pool continuations use the reviewed original full
Oracle, so this queue does not adopt graph pricing in the coupled solver
or in production. The final support closures use each continuation's
complete saved state.

The preflight reserves all unstarted research outer allowances plus the
16800-second frozen producer caps, 600 seconds per arm for verification,
and an additional 4800 seconds. The child and campaign meters continue to
enforce the actual remaining total before launches. The queue's final
state explicitly leaves scientific completion, final audit and delivery
open; it is not a goal-completion assertion. Campaign admission still
checks the frozen matrix and independent gate.

Two assertions requested before launch:

1. A receipt accepted for the predecessor or a skipped child should have
   zero exit code, observed exit, no timeout and no supervisor failure.
   The meter can return 124 or 1 because of the latter fields even when
   the recorded child exit code is zero; the resume predicate should match
   the meter's success condition.
2. Before labeling the inherited endpoint `source_commit` as a delivery
   base, assert it equals the frozen identity's `delivery_base_commit`.
   The new `candidate_measured_source_commit` field and PE hash correctly
   identify the measured implementation, and should remain separate.

The working report and cost output explicitly disclose untimed pre-launch
identity/source hashing, source snapshots and accounting bookkeeping as a
measurement gap. They do not estimate those costs, claim a complete wall
clock, or rerun producers to compensate. This is consistent with the
goal's disclosed-timing-gap provision. Necessary new graph/LP/flow and
scientific verification work remains inside its actual outer receipts.

No re-review of the unchanged frozen production implementation is needed
for this new serial connection. The graph qualification must still pass
with the source/core identities required by the refinement entry before
either real-role graph probe can run.

## Closed static gate

**ACCEPT_STATIC_REGISTERED_QUEUE**. The two requested checks are now
present. Both the K35 predecessor and every skipped research receipt must
have observed zero exit, no timeout and no supervisor failure. The complete
report checks the inherited endpoint source commit equals the frozen
identity's delivery base before making that attribution.

Final inspected hashes:

- `round153_followthrough.py`:
  `fa26afea93ea309d1c5fc929725afc0d9cb0fd9e18e5af254b7c57e311ed87ca`.
- `round153_reports.py`:
  `2b4a716d87cb5e67514dfef6fee11efda9060445e3d632c2887b289161babeec`.

The queue may start only after the current K35 outer receipt and result
are read and accepted under these checks. Graph qualification still gates
its two probes, and all subsequent original admission conditions remain
in force. This is static closure only; the reviewer did not launch or
execute the queue.
