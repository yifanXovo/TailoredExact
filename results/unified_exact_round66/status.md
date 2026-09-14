# Round66 live recovery status

Stage is completed and audited; draft PR publication is next. Branch:
codex/round66-arc-load-replacement, based on Round65 112d6b2.
The initial Git fetch failed; a subsequent HTTP/1.1 fetch completed successfully.
The repository/API baseline agreement remains intact.

Frozen solver build_v1.json and driver are in use. 43/43 CTests passed. Two
native micro runs certified the original value 5/24; ARC exercised eight
splits. Micro runs are correctness evidence only. The initial performance plan
has 16 launches; resource_plan_update_1.json changes only the yet-unopened D6
three-arm complete-run deadline from 300 to 600 seconds, because its historical
paid HGA startup took 332 seconds. Initial worst-case total is now 4660 seconds.

Completed performance runs: E7/E8 P-GRB, K1-R and ARC; D4 K1-R and ARC.
E7/E8 certified in all arms. Current residual differences are mostly HGA;
the old Round39 C6 non-startup losses do not reproduce as large current K1
losses. This is reclassification evidence, not a repair due to ARC.
D4 certified in 129.391 seconds (K1-R) and 107.375 seconds (ARC), pending the
complete independent witness/model audit. This is a protection role; the main
CitiBike proof regression is still untested in this stage.

The D3 pair is complete: neither certified at 300 seconds. K1-R UB/LB are
0.04505416158053462 / 0.043897930276474664; ARC UB/LB are
0.04500155005562836 / 0.04409814829443625. Both components improve slightly;
the absolute gap change 0.00025283 is below the predeclared material threshold.
The independent audit passed for all first 12 runs (10 performance, 2 micro),
with 59 native LP/MIP calls and 860.688 seconds total paid process wall.

Completed queue: citibike_screen D6 P-GRB/K1-R/ARC at 600 seconds.
P-GRB and K1-R have completed: P UB/LB 0.1572411758522922 /
0.14498588325431813, wall 597.375 seconds; K1-R UB/LB
0.15708313110317415 / 0.14324936851841094, wall 597.078 seconds.
Both remain open. K1-R paid 321.286 seconds HGA and then made 5 LP plus
2 MIP calls. Its gap deficit versus P is reproduced in this 600-second
window, despite slightly better UB. ARC finished with the same UB as K1-R
and LB 0.14253008561721864; wall 597.062 seconds, HGA 321.570 seconds.
Its gap deficit versus P remains material (about 0.002298 / 18.75% larger
absolute gap), while its loss versus K1-R is below the predeclared material
threshold. This candidate has not repaired the primary proof target.
The enhanced independent interval-union, witness and model audit passed all
first 15 runs. No algorithm revision was made from these results.

All queues are complete; no solver session is running. C2 at300 has the same UB
.8299634131717752 in all arms; LB is .7714391643536709 P-GRB,
.7977242076215298 K1-R, and .8068141490968943 ARC. Q-PLUS D4 certifies in
152.766 seconds with the same paid initial routes. It makes a short native-target
call that ARC skips because LP numerical values differ near the controller gate;
do not attribute the full runtime difference to pure matrix cost.
All19 experiments pass the final audit and 216 compact evidence artifacts are
packed. See final_report.md. Resource cost is 3696.157 seconds, 94 experiment
optimizer calls; 17 performance and2 native micro launches, zero invalid runs.
Next: publish the new draft PR, then enter the inventory-state hypothesis with
ARC off and a fresh predeclared resource plan. Existing measured source files
still match build_v1.json; the source snapshot includes nested source/header files.
processes.jsonl and each completion.json are authoritative for launch status
and actual paid wall cost. Do not relaunch an existing destination.

No confirmation data have been opened; the broad research objective remains
unmet. Full paid startup is reported and the zero-stop repair is shared by
K1-R and ARC, so it is not counted again as a load-formulation contribution.
