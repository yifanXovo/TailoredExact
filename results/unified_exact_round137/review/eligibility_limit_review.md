# Independent review of recorded eligibility-limit reconstruction

Reviewer: `/root/independent_review`, 2026-10-27 (Asia/Shanghai).
Disposition: **the reconstruction is defensible for recorded rows with matched
leaf geometry**, subject to the coverage/epoch wording below. This is a narrow
source-only review during healthy serial production, not final aggregation,
native-result, PDF or public-recovery acceptance. No large raw replay, Optimize,
compilation, PDF/archive operation or native-library load was performed; only
this review file was written.

## Source chain and immutable fields

`legacyAdaptiveSplitEligible` in `src/GiniFrontierGeometry.cpp` returns exactly
`depth < max(0,max_depth) && upper-lower > min_width+1e-12`. The first-class
controller supplies depth8/width1e-4. In the registered ms2 variants, the other
fixed policy gates retain the accepted first-class configuration; `s2-root`
and original compact are correctly classified not applicable to adaptive
threshold/limit exposure.

The scheduler rejects duplicate leaf IDs on add and split. Ordinary add copies
the input geometry/depth. Splitting and contraction append new children with
depth=parent depth+1 and validated interval coverage, then update the old
parent's status/coverage fields. Bound merges, status changes, attempts and
cutoff tightening do not alter existing gamma endpoints or split depth. The
active external-controller accesses inspected via `findLeaf` are read-only
with respect to these fields. Temporary/local child/model-spec assignments
construct new objects rather than rewrite registered geometry.

Coalescing, which is outside the active ordinary ms2 policy, appends a distinct
union block and preserves the children. Its pop_back rolls back an uncommitted
new block; it does not erase a previously recorded registered parent. Thus
matching a normal retained leaf ID to the final leaf ledger recovers its
original guard geometry/depth. Seventeen-digit gamma serialization preserves
the binary64 endpoints used by the subtraction/limit rule.

The final ledger is written from `scheduler.leaves()` around
`PaperExternalGiniTree.cpp:9341`. An ineligible reached branch writes
`eligible=false` and reason `structurally_terminal` around 8217. A completed
eligible decision writes `eligible=true` around 7330. Joining those rows by
parent_id to final registered leaf IDs is therefore valid within the retained
scheduler epoch. The helper's explicit unknown classification for an absent
leaf is essential.

## Two qualifications to the source-premise wording

1. **A source-rejection reset replaces the scheduler epoch.**
   `ControllingLeafScheduler::abandonNativeSources` (around lines20-30) assigns
   a newly constructed scheduler to `*this`. The external controller invokes
   it after saving `round133_abandoned_control_state.csv` when a native source
   is rejected (around 9299-9320). Earlier parent IDs may then be absent from
   the final leaf ledger. The current `UNKNOWN_LEAF_GEOMETRY` behavior handles
   this conservatively, so no extra recovery or solve is required. State the
   premise as immutable geometry/depth **within the retained scheduler epoch**,
   not unconditional preservation of all historical leaves. The separate
   Round119 whole-scheduler transaction assignment is disabled by the current
   registered ms2 contract.

2. **The ledger does not record every attempted eligible test.**
   The eligible expression is computed around 6661, but its true ledger row
   is emitted only after child-LP work. A hard failure or deadline break may
   occur before that emission (for example around 7106). Therefore a missing
   row does not prove no guard was evaluated. Use a status such as
   `NO_RECORDED_ELIGIBILITY_EVALUATION` and describe the data as recorded guard
   rows/completed eligible decisions and reached ineligible branches.
   `RECORDED_GUARD_AUDIT_COMPLETE` is appropriate for successfully classified
   recorded rows; it must not be read as complete telemetry of every attempted
   loop evaluation. Correct the universal “writes every eligible/ineligible
   outcome” source-premise string before final reporting.

## Interpretation of the reconstructed counts

For a recorded ineligible row with matched geometry, depth>=8 or
width<=1e-4+1e-12 identifies a failing necessary guard condition. Both may hold;
report overlapping violated conditions rather than adding the counts or
claiming two independently executed causal rejection events. In particular,
the C++ conjunction can short-circuit at depth before evaluating width. The
offline width condition remains mathematically checkable from the matched
immutable endpoints, but should be worded “would also reject” when both fail.

Recorded eligible rows must satisfy both geometry tests, as the helper now
asserts. Missing geometry and ineligibility without a matched failing limit
remain unknown/other policy, rather than being assigned to depth or width.
Zero width, a zero-objective proof, missing AM decisions or root-only execution
alone must not be counted as an observed limit rejection. The helper correctly
does not infer a rejection solely from those facts.

The supplied tiny closed-observation receipt has two, one and five recorded
eligible rows for positions3/5/7, respectively, and no reconstructed depth or
width rejection. These rows are consistent with the inspected guard source and
their recorded depths/widths. This source-only review did not rerun those
saved-data checks or generalize them to unfinished positions.

The new both-open endpoint-dominance table is also correctly scoped: same-cap
P/PS observations can show better feasible U and qualified L on one side while
both-open certification direction remains UNDETERMINED. The cited K20 P
versus PS values support endpoint dominance under the declared1e-7 tolerance;
they do not establish a proof-time ranking or runtime distribution.

No change to the measured algorithm, graph or native queue is needed. Apply
the wording qualifications in offline metadata/prose and validate the full
saved-data aggregation after native production is idle.
