# D6: completed four-arm development screen

Original V30 compact r1 shortage, M3/Q30/T18000. All fresh runs use the same
revision2 executable, Gurobi13.0.2 and inherited logical processor2/mask4.
The600s cap ends the whole algorithm. This is exposed development evidence.

|Arm|Paid wall|Verified UB|Global LB|Signed gap|Startup wall|
|---|---:|---:|---:|---:|---:|
|P-GRB|597.313|0.1572411758522922|0.14498588325431813|0.01225529259797406|0|
|VD-S|597.063|0.15708313110317415|0.14568020676209595|0.011402924341078202|319.1286111|
|DS|597.063|0.15708313110317415|0.15008706391847396|0.006996067184700194|5.510879|
|K1-R|597.078|0.15708313110317415|0.14334096616313421|0.013742164940039936|318.5083117|

All remain open. DS reduces gap by42.9% against P,38.6% against VD-S and49.1%
against K1-R; every difference exceeds the frozen absolute and relative
material thresholds. Against VD-S/K1 the final UB is unchanged and the gain
comes from LB. Against P both bounds improve. This is a useful short-window
result, not evidence of a3600s ranking or general runtime domination.

DS starts with a weaker verified UB0.16002728060440277. Its24 completed seeds
produce147 passes,579 neighbor checks (including cache hits), and601 uncached
decoder calls including initialization. All24 final passes exhaust their
generated neighborhoods. Its final objective/inventory is the same as the
HGA arms, but routes differ: maximum physical duration16815.2965 versus
17761.3085; both satisfy the unchanged18000 mathematical T. The objective
depends on inventories, so the shorter route is not itself a better UB.

The VD-S/K1 HGA pair has identical2071 generations,26383 uncached decodes,
best-fitness history and complete initial routes. Their paid startup times
differ by0.6203s here. Round69's much larger mismatch remains in its original
record; uniform affinity does not retrospectively identify its cause, and
this one pair does not establish timing stability. No time is corrected.

At300s, the conservative DS trace has retained-initial-witness gap0.0130892,
versus P native-telemetry gap0.0140080. This small difference does not meet
the frozen material threshold and the intermediate UB evidence differs.
The full-HGA arms have not entered exact proof at300s; their legal LB is0.
Eight300/600 records are in revision2/within_run_checkpoints.csv. Conservative
buffer/setup shifts may understate intermediate progress differently by arm;
final witnesses are never backdated and only endpoints enter paired tables.

All four endpoint physical witnesses and full interval unions pass. At this
29-run stage prefix:128 experiment Optimize calls,4408.907s paid process wall,
94 initial-witness/model checks (37 incompatible intervals,zero failures),
21 eligible/accepted/full-vector-observed Starts,477 compact artifacts.
Actual log headers for all128 calls read Gurobi13.0.2. Native observer claims
and replayable submitted-vector checks remain distinct. D7 was still running
at this prefix boundary; final_report.md now records the completed stage.
