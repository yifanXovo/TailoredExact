# Round78: balanced physical descent repairs the exposed D7 screen

BDS-C materially improves both bounds against fresh P-GRB at the common
1200-second D7 cap, reducing absolute gap by 78.92%. Its gap is slightly smaller
than fresh K1-R's, below the frozen material-difference threshold, and it retains
the important K1 advantage relative to P. This is a promising complete-method
result on one exposed development role, not stable medium/large superiority or
independent confirmation. The overall research goal remains unmet.

Base: R77 final 88e963a1f10cc4ff9f1d3a17950f0a5708f68318 / draft PR138.
Branch: codex/round78-balanced-block-descent. The new default-off preset is
research-round78-vds-balanced-descent. Default configuration and main remain
unchanged. publication.json records this stage's independent draft PR.

## Complete matched result

D7 retains its original V50/M4/Q30 regional-shortage data, mathematical T18000,
handling 60/60 and lambda .15. Input SHA256 is
d7dbd018331b9d5f3d84c0fd6c907560ef1fa92a2f8c153ac7d81e46a6cd4e9c.
All three fresh serial arms use Gurobi 13.0.2, Threads 1, Seed 0, Presolve Auto,
zero requested gaps, original numerical tolerances and logical processor 2/mask
4 with checked restoration. Whole wall includes all startup, modeling, calls,
evidence persistence and exit. All return normally; none certifies optimality.

|Arm|Paid wall s|Physical U|Global L|Absolute gap|Relative gap|
|---|---:|---:|---:|---:|---:|
|P-GRB|1197.110|.277320865934|.197286478715|.080034387219|.288598505|
|BDS-C|1197.109|.219629792372|.202758088175|.016871704197|.076818832|
|K1-R|1197.125|.215644075316|.197357479228|.018286596087|.084799900|

Relative gap is (U-L)/abs(U). Against P, BDS-C improves U by .057691074 and
L by .005471609. Against K1, U is worse by .003985717 and L better by .005400609;
the gap gain .001414892 is about 7.74%, below the frozen 10% material rule.
The unclipped fraction of K1's P-relative gap advantage retained is 1.022914049.
This supports protection at this cap without requiring historical single-point
records. It does not imply statistical equivalence with K1 or a better UB.

|Actually available time s|P gap|BDS-C gap|K1-R gap|
|---|---:|---:|---:|
|300|.139455121|.097807595|No recorded physical U|
|600|.093231319|.020043601|No recorded physical U|
|900|.081833725|.016887891|.019312551|
|1200|.080034387|.016871704|.018286596|

Availability is the later of payload closure and completed observation. BDS-C's
startup U .300543518294 is observed at 10.297s, K1's .215644075316 at 610.516s.
Neither is backdated. K1 has no native MIPSOL witness; its verified current-run
HGA witness and complete-domain bound still give a valid endpoint. The final
normal-output LB may improve the last journal checkpoint and is used only once
normal completion is available. No bounds or tiny signed gaps are clipped.

## Mechanism and exactness

The new shared module first closes the inherited physical insertion/quantity
neighborhoods. It then enumerates every contiguous source block with zero net
pickup-minus-drop, every other vehicle (including unused vehicles) and every
target leg. It preserves block order and operations. Original prefix capacity,
station inventory, single visit and route time are checked. Loaded returns and
unequal vehicle capacities remain legal; balance alone is insufficient for a
block with negative relative prefixes. Both changed routes' travel is recomputed.

At unchanged inventory Y, choose the feasible move minimizing the full vector
of route durations sorted descending, provided that vector strictly decreases
in exact lexicographic order. Deterministic indices break ties. Then close the
strict neighborhoods again. Stop on joint exhaustion, mathematical F=0, or the
sole whole-run deadline. Every adopted move is fully reverified. There is no
private time/Work allocation, move cap or history-based instance switch.

Strict F decreases and neutral duration-tuple decreases form a finite-state
descent. This proves absence of cycles for the implemented search, not global
heuristic optimality or faster runtime. Exactness comes from unchanged complete
VD-S coverage and native proof. The existing 1e-10 outer handoff threshold can
retain the prior witness for neutral-only/tiny changes; actual handoff is audited.
The existing native mapper relabels vehicles only within equal-capacity classes.
The isolated operator handles nonmetric distances; the complete inherited VD-S
preset still requires its qualified symmetric metric travel scope.

The method can be summarized as:

```
w = best verified result of the 25 current-run JDS-X paths
repeat:
    w = inherited strict physical insertion/quantity closure(w)
    if whole deadline reached: end entire run with the verified witness
    if F(w) == 0: use the existing verified-zero exit
    b = best feasible balanced block relocation decreasing sorted durations
    if no b: stop
    w = fully verified b(w), with exactly unchanged Y and F
promote w under the existing incumbent rule
run unchanged complete VD-S proof with the verified incumbent/Start
```

Generic block relocation and quantity search are established ideas. R74's
primary literature review remains applicable. This increment is the original-
objective/prefix/time-checked finite composition and its measured behavior;
correctness, design rationale and performance are separate claims.

## Structural and startup evidence

Seven independent structural cases cover negative block prefixes, unequal Q,
loaded return, nonmetric source deletion, exact T, source-route removal and
empty input. Additional checks cover zero/deadline behavior, invalid physical
input, deterministic ties and an earlier tiny lexicographic increase. The
production structural fixture requires a neutral move followed by strict
quantity improvement. All selected production controller paths are real calls.

The fixed-witness diagnostic improves D6 from .160027280604 to .157849712515
through two neutral moves and four quantity moves, and D7 from .331621561270 to
.300543518294 through four neutral moves and 39 quantity moves. Every enumerated
placement count and chosen minimum tuple agrees with an independent Python
oracle; all strict steps pass original physical replay. The exact prototype
source is archived separately from later production integration.

Ten fresh startup processes use their own current-run paths. D3/C2/D4 retain
identical routes and U; D6/D7 reproduce the improved diagnostic inventories.
All 25 underlying paths match paired controls. Production D7 starts from JDS-X,
so its total is four neutral moves, two insertions and 44 quantity moves. It
uses all four vehicles and serves 49 stations after one zero-operation removal,
with 206 pickup/drop units and maximum duration 13547.574s. Both declared
neighborhoods exhaust; no failure or internal limit ends them. All actual outer
handoffs match the final module witnesses. These startup facts do not establish
full timing on the five other roles.

## Native integration, cost and delivery

Production source 4a0561e0f8193e3e874c1bd0bfa8bc381fb66f5e builds
build/round78/v1/ExactEBRP.exe, SHA256
3fae847a75c3c9d07d8f5f0444daeafb73559865e6bffb816746802b9e2f43ab.
The single qualification passes 60/60 tests with 147 actual Optimize calls in
103.905918s. Actual BDS-C and inherited JDS-C tiny Starts pass complete-vector,
model-row, readback and native acceptance checks and certify 5/24 numerically.

The full campaign uses 11 Optimize calls, all returned: P 1, BDS-C 4, K1 6.
BDS-C uses three LP calls and one parent MIP, without an extra MIP restart.
Its actual Start has 25943 columns/104726 rows; the independent maximum row
violation is 3.37e-14, with zero readback difference and native acceptance.
Its parent MIP records 582 nodes, 1665701 simplex iterations and 1170.05 native
seconds. P records 2274 nodes and 1196.70 native seconds; K1's target MIP records
264 nodes and 563.54 native seconds after its paid HGA. These rounded diagnostics
are not causal performance proofs and cannot replace end-to-end costs.

P remains the original 35618-row/13360-column compact model with no added Start,
cut or imported bound. Canonical SHA256 is
4cd7967ea4d65804e6ab7ae8913033454ba495766ff9eb03529bd935f6e0bace,
fingerprint -373258443. Independent audits validate 232 physical witnesses
(230 native and two startup), 115 global-bound events and all 372 committed
events, plus scope/coverage, settings, final endpoints and actual Start vectors.
Numerical certificates remain distinct from strict rational proofs.

The fixed diagnostic costs 3.890512s including compilation and replay, zero
Optimize. Fresh startup costs 32.482s plus .301509s offline. Full runs total
3591.344s plus .436195s replay; reference export .375s is nested in .564073s
preflight. Final analysis costs .485364s, mechanism audit 2.009778s, packaging
and verification 10.312731s, and separate byte verification .651556s. Additional
qualification/native offline checks are in resource_summary.json. Total actual
stage Optimize count is 158. No qualification repair, solver failure, supervisor
exception, solver rerun, extra seed or reset credit occurs. Interactive work
is not claimed as a complete machine-time census.

Eight lossless bundles contain 1686 files, 148153245 raw bytes and 21936238
compressed bytes. Every member length and SHA256 verifies. Raw models, logs,
receipts, witnesses, traces, native Start vectors and build/test artifacts are
retained; executables remain local with hashes. See reproduce.md.

## Decision and remaining work

The architecture is admissible and this complete D7 screen passes its primary
and protection questions. Historical R77 JDS-C gap .115532282 is useful context,
not a fresh same-build ablation proving that the new neighborhood alone caused
the full improvement. The structural/startup evidence establishes the actual
mechanism; the fresh P/K1 comparisons establish this candidate's end-to-end
result at 1200s. Replication and longer windows remain necessary.

Preserve the candidate unchanged for broader full-method validation, beginning
with the exposed small/nonzero panel described in prospective_validation.md.
D6/D7 common 3600-second comparisons and sufficiently diverse unadapted
confirmation are still outstanding. No further run is admitted by this report;
declare the next bounded stage after publication. Do not mark the overall goal
complete or replace it with this single positive result.
