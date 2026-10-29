# Independent Round139 placement selection review

Reviewer: `/root/round139_review`, independent of the principal implementer.
Date: 2026-10-29 (Asia/Shanghai). **ACCEPT the proposed selection and bounded
stop.** This is a review of the sealed six-position D2 pilot and existing
matched BASE/BOTH references. It is not final delivery acceptance.

The reviewed `reports/full.json` SHA256 is
`d89cdcd12d1ddd7b247876dfc8f56d3e689578bbafb85cd0721254da514f4b83`.
It reports complete=true, missing=[], six new Seed0 positions and no unclosed
fees. The endpoint snapshot and supporting hashes are in selection_review.json.
No Optimize, compilation or new computational experiment was started by the
reviewer.

## Decision and evidence

Stop expanding both new asymmetric placements. Retain the already measured
BOTH formulation as research-only, with R137 GI-TBC remaining stable.

- LP-only K15 certifies in 122.078543 s versus BASE 112.769303 s: the
  9.309240 s difference is below max(10 s, 11.276930 s), so it is not a
  substantive BASE regression under this goal. It materially loses BOTH's
  33.818227 s acceleration. LP-only K20 stays open at cap1200; T_cert is null.
  Keeping the stronger outer LP and initial exact-close action therefore
  does not preserve BOTH's principal certificate benefit.
- LP-only RB35-T2 gives U=0.36213682657245494 and
  L=0.21839259471625916. It improves U relative to BOTH by 0.0390633913,
  while losing 0.0107890049 in L. Relative to BASE, U is worse by
  0.0174942010 and L lower by 0.0005933549. It does not combine the desirable
  endpoints of the two references.
- MIP-only K15 and K20 certify in 34.697528 s and 100.706893 s.
  Their differences from BOTH, +0.879301 s and -0.928492 s, are not
  substantive. They preserve the principal benefits over BASE with BASE's
  initial explicit LP and initial native-target action. Subsequent control
  need not remain identical: K20's strengthened target return raises the
  parent bound before a later no-strict exact-close.
- MIP-only RB35-T2 returns exactly the same stored binary64 U and L as
  BOTH: 0.4012002178390506 and 0.22918159966432358. Both remain open.
  Removing stock from the outer LP does not improve this important Seed0
  regression in the completed comparison.

These results answer the placement question on the entered roles: integer-side
use retains the tested proof benefits; outer-LP use alone does not. Neither new
uniform role split delivers a useful improvement over BOTH in this panel.
This is not a general necessity/sufficiency or performance-dominance theorem.
Native row placement, role reconstruction, retained state and Start handling
remain part of each complete intervention, without an additive causal runtime
allocation. K20's benefit cannot be explained by saving its approximately
0.33 s baseline target call. Initial H equality removes initial-H quality as
an explanation for the paired differences.

## Why the conditional blocks can stop

D2 has three physical/objective roles and four actual cells per role: six new
asymmetric positions and six reused qualified BASE/BOTH positions. The other
five roles have historical BASE/BOTH cells only. Do not describe an eight-role
complete four-grid experiment or pool reused observations as fresh instances.
The overall inherited panel remains eight configurations on six base inputs.

D3 explicitly permits reuse when the retained candidate is existing BASE/BOTH,
and G permits stopping when neither new placement supplies useful incremental
value. Reuse BOTH's already completed eight-configuration panel; there is no
requirement to run five additional asymmetric positions after this decision.

No new configuration is selected for adoption, so D4 need not create new Seed1
runs. Matching R138 BASE/BOTH Seed1 records can remain historical, result-selected
context with their original source/PE and V1/V2 identities. They are not Seed1
confirmation of LP-only or MIP-only, and no such confirmation may be claimed.

E is optional. The placement question is now sufficiently resolved for this
round; no new TC matrix or unrelated search is required to consume unused
budget. The remaining question is whether a different, uniformly justified use
of resource information can retain proof gains while changing adverse native
search trajectories. This panel alone supplies no validated rule for doing so.

## Budget and outstanding closeout

The reviewed meter reports 6371.821015599417 s (1.7699502821 h) of new charged
computation: 6172.0360805997625 native seconds and 199.78493499965407
qualification/export/readback/setup-failure seconds. Nested H/LP/MIP are not
counted again. This is below the 57600 s limit; unused allowance is acceptable.
Offline analysis, build, document and delivery overhead remain separately
reported. Later pure checks or closeout metadata may legitimately update those
non-experiment totals.

Before final delivery acceptance, finish the already planned exact Counter
checks on every entered full matrix, all saved witness physical replays and
clear same-call/cross-call numeric matching, mathematical/local evidence
semantics, manuscript/PDF verification, evidence/source publication and bounded
public byte/member readback, English Draft PR readback, and current-round
cleanup receipt. Preserve failed setup attempts and the Git-maintenance timing
disclosure. Qualification cap90 timings are not performance samples.

If the full summary is regenerated, preserve this reviewed endpoint snapshot
and bind the final integration review to the final report hashes; a metadata
refresh does not justify new Optimize calls or relabelling this selection.

