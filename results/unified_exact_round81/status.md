# Round81 original serial campaign active; S12 repeats complete

Base R80 final634cf03982e71849079699848ceecc3cd19ecb72 / draft PR141,
verified open/draft/unmerged. Branch codex/round81-bdsc-long-protection-replication.
Read plan.md, R80 final_report.md/status.md and R79 final_report.md.
No C++/parameter/default change; qualified R78 source4a0561e0/build/round78/v1.

Order S12 P/BDS/K1 common120, C2 P/BDS/K1 common300, D4 P/BDS/K1 common300,
D6 P/BDS common3600, D7 P/BDS/K1 common3600. Exactly14 runs, maximum20160
process seconds, five zero-Optimize reference exports. No build/test/micro.
Stop on a validity failure, no automatic rerun. Same seed0/Threads1/core2mask4,
whole deadline only. All original/repeated results retained; no best-repeat
selection. D6 has no new K1 arm, so do not import R80 K1 into its fresh pair.
D7 is a fresh longer-cap experiment, not identical-cap replication of R78.

Original driver exec24123 is active. S12 P/BDS-C/K1-R all normal, valid and
certified at5.640/1.797/40.594s. C2 P-GRB is active at this snapshot; the other
original scheduled arms remain in the same driver. On recovery inspect campaign's
active_run.lock, active_experiment.json, summary.json and driver_completion.json.
Never invoke a producer again if campaign exists. No heavy audit or build while
the driver is active. After closure audit physical/scope/coverage/actual Starts,
all25 paths and prior-repeat identity, then package and publish independent
stage draft PR. No main merge. Diverse unadapted confirmation remains unadmitted
and necessary; overall goal unmet.47% weekly remaining, no reset consumed.
Owned E:/codes/ExactEBRP-round66; original dirty E:/codes/ExactEBRP untouched.
