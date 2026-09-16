# Round81 original serial campaign active; twelve runs complete

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

Original driver exec24123 is active. The first nine runs are normal and valid.
S12 P/BDS-C/K1-R certify at5.640/1.797/40.594s. C2 BDS-C certifies at113.469s;
P/K1 finish open with gaps.058891893183/.032805674652. D4 BDS-C/K1 certify at
52.734/134.687s; P finishes open with gap.311831107997. D6 P-GRB also returns
normally/valid at3597.172s, U.1572411758522922, L.15078948840741413,
gap.006451687444878063, uncertified. D6 BDS-C also returns normally/valid at
3597.172s, U.15750980361456174, L.15578327977056106,
gap.0017265238440006825, uncertified: about73.2% lower gap than fresh P,
with worse U and stronger L. Its startup reports2 neutral and4 quantity moves,
exhausted with no verification failure. D7 P-GRB reaches the predeclared
whole-run hard stop at3598.062s, within3600, with235 physical witnesses and68
global bounds validated: U.2372849915487284, L.19858649317712468,
gap.03869849837160372. This is interrupted committed evidence, not normal
return or certification; one Optimize starts and does not return. No rerun.
D7 BDS-C is active and K1-R remains queued in the same original driver.
Read d7_p_termination.md. Joint stage replay is pending.
These are completed driver endpoints, pending the joint stage audit.
On recovery inspect campaign's
active_run.lock, active_experiment.json, summary.json and driver_completion.json.
Never invoke a producer again if campaign exists. No heavy audit or build while
the driver is active. After closure audit physical/scope/coverage/actual Starts,
all25 paths and prior-repeat identity, then package and publish independent
stage draft PR. No main merge. Diverse unadapted confirmation remains unadmitted
and necessary; overall goal unmet.40% weekly remaining, no reset consumed.
Owned E:/codes/ExactEBRP-round66; original dirty E:/codes/ExactEBRP untouched.

The source-grounded complete method is consolidated in unified_method.md;
reproduce.md describes the offline sequence and byte verifier. Analyze and
replication also check cross-run global-bound/physical-UB consistency without
pooling endpoints. These processors have not executed while optimization runs.
No extra build/test/native solve. The original driver remains the only active
optimizer; it must not be restarted.

Interim publication recovered through exact Git objects after three HTTPS
failures and four failed CLI API attempts plus one connector tree error. A verified
prefix first reached784fbd7b0, then directory-delta publication reached
2dd0ea993dba9fb25e1172f22c039a7fd329097c, with original hashes preserved and
non-force ref updates. publication_api/directory_deltas.json is the successful
receipt. A later incremental timeout is retained in d6_replication_progress.json;
d6_replication_recovery.json then verifies all three original commits and the
non-force remote update to b5951a3dc44ea4e7276090c73ac3a2b00125cbe4 in40.034784s.
The subsequent D7 interruption checkpoint also publishes successfully to
aaf8de23ceaef0620c825a48667aa81f6d67385a in27.938310s;
publication_api/d7_p_interruption.json preserves the exact-history receipt.
All publication sessions ended; the stage PR awaits campaign closure.
