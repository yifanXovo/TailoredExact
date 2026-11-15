# Independent implementation and data review

Reviewer: independent Codex sub-agent `/root/implementation_review`, acting
under Round168 H.2. This is an agent review, not human peer review. No
Optimize, compiler invocation, production run, source edit or historical-file
mutation was performed. Only this review file is written by the reviewer.

Final disposition: **PASS for the implemented model/data/qualification,
all11 result positions and the15-call cost reconciliation.** The single
eligible Native lower fails the frozen quality gate and is correctly
rejected; this is an explicit result limitation, not a waived test.

The reviewed candidate source SHA256 is
`1f065e3eef524af337c771395358d359a37119b2714c8f3e5939bcbda05ce030`;
the bound executable SHA256 is
`d699f6d92e6a392d83d828bd015d13e9c79bf32fc35f8b61d654e9cf33024449`.
Both hashes were independently read from the actual files and match
`candidate_manifest.json`. The declared Gurobi13.0.2 DLL identity is the
specified `9b5fccef...ed6d18a88`, and the compiler/build/CMake option are
explicit. The new target is default OFF and links the standalone C++ source
with the inherited Parser/Evaluator/Result/SHA sources; it does not replace
the production B executable.

## Actual implementation inspection

Read the complete `src/round168_route_family.cpp`, transport/serialization
helper `scripts/round168_common.py`, new CMake option, and manifests.
Construction, family membership, whole-vehicle relabeling, stock embedding,
Start mapping, row/bound/type inspection, solution decoding, exhaustive tiny
enumeration, target stopping and substantive sequence/reuse all reside in
C++. There is one literal `GRBoptimize` call site. Python extracts specific
historical result/audit bytes and serializes their unchanged route data;
it does not generate an optimization matrix or call an old Python solver.

The station stock selector uses every integer0..C on old E and only b
outside. The shared objective retains every station, global pairwise
dispersion and common denominator, with the original S=0 convention. The
service links make p/d implicitly integer at integral stock/visit variables.
Order uses all forward skip arcs and original-prefix load constraints.
Owner/eligible use full permitted arc sets, rank acyclicity, source-zero
arc loads and exact station load balances. All scopes pay actual selected
arc travel and `(pickup_seconds+drop_seconds)*total_pickup`, which is the
correct station-plus-return handling identity for these uniform inputs.
The saved parent is mapped to every actual column; no old G domain,
contracted stock support or target cutoff row appears in the new compiler.

The callback does not trust a low modeled candidate: it decodes selected
stocks/arcs and uses the original physical checker before retaining HIT.
Final numerical exclusion separately gates finite lower, accepted status,
actual incumbent row/bound/type quality, successful decoding, model hash,
and the physical upper direction. Safe lower subtracts1e-7 and rounds
downward; lower values never enter production B. A physical upper can
remain valid even when the Native lower is unqualified.

## Independent archive and target check

Independently read all18 recovered final result/audit pairs, input files,
fleet text and original `complete_arms.json` / `matrix_frozen.json` records.
For every record, audit SHA matches the original complete-arm row, result
routes equal audit physical routes, input/fleet/member SHA bindings match,
and method, Seed, original T and lambda match the frozen campaign source.
All18 fleets retain all three labeled vehicles and unique nonzero one-way
services. The independent reviewer recomputed stock balance, every load
prefix, physical travel from original coordinates/speed1.5, station handling
and loaded-return unloading. All are feasible at the original T.

An independent rational recomputation of the stock ratios and objective
(using the actual binary64 weights/lambda as exact coefficients) differs
from the historical final F by at most `1.1102230246251565e-16`. Closed pools
contain exactly B/P times Seeds0/1/2 for each input. Their minima and owners
are C35 P Seed0 (`0.09331934374779818`), B35 B Seed1
(`0.167746351588456`) and X35 B Seed0 (`0.45747531701601785`). The C++
Evaluator's last-bit differences are below the predeclared1e-7 policy and
do not change target identity or any threshold decision.

Independently regenerated all11 target-fleet membership and stock-embedding
checks with compatible vehicle permutations, unique original owners and
relative-order tests. Every direct-member boolean, outside-E inventory
change list and embedded physical-feasibility boolean matches the C++
manifest. Nine ordered parents have distinct full parameter/ordered-sequence
signatures. Exactly B35 Seed1 and X35 Seed0 are free HITs. C35 Seed0 omits
station18 while its P target changes station18; that blocks that witness,
not the complete eligible family.

## Tiny qualification and actual matrices

Read the independent enumeration routine and frozen enumeration values:
it traverses all stock vectors, allowed assignments and permutations,
checks physical arithmetic independently of the matrix generator, and
labels its result floating-qualified complete enumeration. The six MIPs
use one call each and agree with the corresponding optima: A=.15 and B=0
in each scope. Structural-release witness membership is real even though
the minima happen to agree across scopes.

The reviewer independently parsed exported LP text, every Start CSV,
declared binary set, variable bounds and objective. All six tiny Starts and
the three current C35 Starts satisfy all exported rows/bounds/types and
match physical F; completed C35 order/owner solution vectors also pass.
The largest independently read-back solution residual at this stage is
`5.3068660577082483e-14`, well below1e-7. This check does not call Gurobi or
reuse the C++ row-auditing function. The review parser initially mishandled
the legal zero-term empty-car row `<=14`; its read-only parser was corrected
and all checks passed. This was a reviewer-reader error, not a model error
or a repeated Optimize.

For concrete actual-matrix structural checks, A's owner-but-not-order
witness uses arc4->3 on car0. `a_0_4_3` exists in owner and is absent from
order. A's eligible-but-not-owner witness serves station3 on car1;
`z_1_3` exists in eligible and is absent from owner. Q=[3,2] prevents
explaining this example by a compatible whole-vehicle relabel. Their
larger-domain mapped vectors have zero row residual in the C++ audit.

## Findings and dispositions

No blocking implementation or data defect was found in the inspected
scope. Two precision/record-keeping points should remain explicit:

* The frozen `B_zero.fleet` path is overwritten by the later eligible
  enumeration's legal zero-stock witness. That particular fleet crosses
  original owners, so the actual mapping record accepts it only in
  eligible and correctly rejects it in order/owner. The enumeration shows
  S=0 feasibility in the smaller scopes, but the saved mapping must not be
  described as mapping this same zero-stock fleet into all three scopes.
* The initial protected-status serializer stripped the first line's leading
  status space. The separate `protected_entry_correction.json` fixes the
  recording and includes the previously omitted first dirty-file hash.
  No protected-tree mutation or solver rerun is implicated. Do not silently
  replace the original initialization record.

The six qualification ledgers have one begin/end pair each and API return0.
Current substantive calls R168_S1/S2 likewise finalize successfully and
retain numerical EXCLUDED results. At this initial review checkpoint the
eligible call is still running; no final total, full11-row status summary
or all-campaign cost PASS is asserted yet. Those items require a final
readback, including any failure/unused slot and Runtime versus enclosing
wall-time accounting.

## CSV and scope preservation

The bounded CSV search is honest: the specified112-row UTF8-BOM master is
not available at the recorded attachment/known paths. The actual91-row
Desktop and103-row historical file have the same bytes/hashes as their
entry records, and neither is substituted for the missing authority.
No rows are synthesized from a desired total. The R168 artifacts are
restricted offline diagnostics, with zero new complete GI-TBC/P records.
The final closeout must preserve that zero-row statement and retain the
missing-master limitation.

## Final campaign readback and closure

The final readback was performed on15 November2026,03:53:13–03:55:43 UTC:
**150 measured seconds**, excluding the short review-file update. The first
review's separate duration was not measured. Both reviews occur inside the
root task's enclosing scientific/diagnostic wall window; do not add this
150s to that window again. No Optimize was run by this reviewer.

Read the completed root result JSON/CSV, all15 raw result/parameter/model/
Start/solution/Optimize records, `calls.json`, `cost_report.json`, independent
objective readback, and the updated12-record fleet-change analysis. The
source and PE still match the originally frozen candidate. All8 listed
production default sources/configurations remain byte-identical to HEAD.
The target/family identities and policy have not been changed to accommodate
a result.

All15 actual Optimize calls have unique IDs, exactly one flushed begin/end
pair, API return0, the recorded model SHA and uniform actual parameter
readback. There are6 tiny calls Q1–Q6 and9 substantive calls S1–S9, no repair
calls, no duplicate-family reruns and no hidden extra ledger. All six tiny
calls return status2; eight substantive calls return status11 after their
evidence lower crossed the frozen threshold; eligible returns status9 at
the cap. The300.00699996948242s eligible Runtime overrun is retained in fees
and does not create more calls, another Seed or an extended query.

The independent LP-text parser was applied to every actual model, every
complete Start and every saved solution. It confirms the declared row,
column and binary counts. Maximum Start residual is
`1.0702549957386509e-13`. Across the qualifying saved solutions, the maximum
independently recomputed residual is `1.038388125484957e-13`.
For eligible S3, it independently finds residual
`7.912396934289552e-7` on `q_le_s_8_19`, matching the C++/Native observation
`7.912396935427779e-7` within1.2e-16. This exceeds the frozen1e-7 gate.
`bound_qualified=false` and safe L=0 are therefore correct. Its raw Native
bound `.033592546196099075` is preserved for audit and is not promoted into
a certificate. The Native parameter tolerances were not tightened/relaxed
after the event and no repair solve was purchased.

Independently rechecked all9 substantive raw physical fleets against their
original inputs, permitted service sets, appropriate owner/order condition,
unique one-way services, every prefix capacity, loaded return and full
physical duration. All pass. Exact ratio/binary-coefficient objective
arithmetic differs from the saved C++ physical F by at most
`1.5265566588595902e-16`. The original fleet remains the legal upper when
no better physical fleet is returned.

The11 summary rows reconcile exactly between JSON and CSV:

| Registered positions | Final verdict |
|---|---|
| Seven nontrivial ordered parents |7 EXCLUDED|
| B35 Seed1 and X35 Seed0 order |2 archive-witness HIT, zero new Optimize|
| C35 Seed0 owner |EXCLUDED|
| C35 Seed0 eligible |UNKNOWN|

This is8 EXCLUDED,2 HIT and1 UNKNOWN over11 positions from three physical
inputs, not11 independent test instances. Each displayed safe lower follows
the frozen outward guard or nonnegative-objective floor, and every verdict,
potential interval and obstacle interval recomputes from its saved threshold
and physical upper. No lower propagates in the wrong inclusion direction.

The eligible raw U is `.12724407070237156`; its stronger propagated U
`.11512886899258191` is the already verified owner fleet, with
`U_source=R163-C35-U_S0_owner`. Both fields are retained; the propagated
physical object equals the owner object's fleet. This is upward feasible
witness reuse, not a second new eligible Native discovery. The updated
`fleet_changes.json` retains11 propagated-position descriptions and a
separate `R163-C35-U_S0_eligible__raw` description. The latter changes stock23
from13 to12 and reorders car2, with F change
`-.0023223189495888696`; it is distinct from the larger owner improvement
inherited by the eligible summary. This closes the earlier raw/propagated
description risk without altering the actual query or its verdict.

Fees independently sum to **436.8279995918274s Native Runtime**,
**847.4033862839872 Native Work** and **437.2573462s recorded per-call outer
time**. Native splits are .10599946975708008s tiny and436.7220001220703s
substantive. The readback cost snapshot's enclosing diagnostic window is
791.7193863391876s; it is conservatively to be closed after final review.
It already contains the serial calls, construction/Start/checking and
interleaved management, so Native and reviewer subdurations must not be
added again. Four qualification repair slots remain unused, and no unused
capacity licenses more positions. The complete scientific elapsed window
and normal Git/public-recovery I/O remain separate closeout records.

Finally, the actual protected91/103-row CSV byte hashes remain unchanged.
The specified112-row authority remains absent at the bounded recorded
paths, and all summaries keep zero new complete-method samples/master rows.
There is no remaining blocking implementation/data finding in this review.
