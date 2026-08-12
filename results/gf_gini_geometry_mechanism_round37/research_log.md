# Round 37 research log

## 2026-08-12 - Stage 0 and hypothesis freeze

- Consolidated Round 36 Stage B/Stage C chronology and live merged PR state.
- Removed 79 proven transient/intermediate top-level artifacts; restored the
  uncompressed trajectory after tests proved it remained an operational input.
- Audited 103 historical raw runs: all lifecycle, exactness, counter, timestamp,
  and certificate semantics passed.
- Fixed six-digit exact-ledger serialization; 18/18 contemporaneous old/new C6
  mechanism components remained equivalent.
- Forensics rejected a generic low-G skew. Frozen G1 as one deterministic
  weakest-complete-LP midpoint pre-refinement and froze the 12-row panel before
  any G1 result.

At this point no candidate performance conclusion had been drawn.

## Implementation and default-off gate

- Added the uniform `pilot-weakest-prefine` policy behind a default-off option.
- Added solver-neutral weakest-cell selection tests and exact midpoint-coverage
  tests. The selector has no instance, scenario, time, Work, node, hardware, or
  historical-outcome input.
- Rebuilt the official research executable and passed 16/16 C++ tests.
- Re-ran contemporaneous default-off C6 equivalence after implementation:
  18/18 components passed on the V12 target/requeue/lookahead case and V20/M2
  real-split witness.

## Exploratory smoke (180 seconds)

- Froze six balanced pairs before any candidate result: two V12, two V20, and
  two V50 witnesses.
- Completed 12/12 rows with zero false certificates and no coverage/lifecycle
  failure.
- G1 exposed on 5/6 pairs; the V50 moderate run reached the deadline during its
  complete initial LP census.
- All five exposed rows reproduced the prior weakest cell and had positive
  local LP gain. End-to-end result: one improvement, one regression, four ties.
- Decision: focused diagnostic, no rule change.

## Focused diagnostic (480 seconds)

- Froze the smoke-positive V20, censored V50 moderate, and regressing V50
  high-imbalance witnesses before medium results.
- Completed 6/6 rows with zero false certificates and all gates passing.
- All three pilots exposed with positive local gains. Final common-UB gaps:
  two improvements and one persistent V50 regression.
- Decision: confirm only the replicated positive and regression boundaries;
  exclude the weak unreplicated V50 moderate improvement.

## Selected confirmation (900 seconds)

- Froze exactly two pairs before confirmation results. No 3600-second run.
- Completed 4/4 rows with zero false certificates and all gates passing.
- V20 tight-T: gap improvement `0.112251`, AUC improvement `0.0972804`.
- V50 high-imbalance: gap regression `-0.0289641`, AUC regression
  `-0.0269819`, despite the larger local LP gain.

## Closed research decision

The geometry mechanism is real and localized, but G1 is not a uniform exact
performance improvement. Keep it default-off as a diagnostic. Do not promote
or broaden validation. C6-HGA-FULL remains mainline.
