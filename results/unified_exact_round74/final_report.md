# Round74: JDS-X fails the D7 protection screen

JDS-X improves the initial physical witness but ends with51.2% more absolute
gap than original P-GRB and28.6% more than DS-X at the common1200s allowance.
This meets the predeclared severe-P-regression threshold. Fresh K1-R retains
a large P advantage, so its important protection is also lost. R73's D3 gain
does not offset this negative medium/large-role evidence. This validation
stage is complete as a research result; the overall goal remains unmet.

Base: R73 final8c4129b58592d35c34f56a4beddbf18cacacbf81, draft PR134.
Branch: codex/round74-jdsx-protection. Independent draft PR publication is
recorded in publication.json when available. No main merge or default change.

## Matched complete outcomes

All four fresh D7 runs use the unchanged qualified R73 v6 source
4ba09609cf3fb92ef29598dce8201231668324f9 and executable SHA256
90d7bd2f84744b87958ff19a6e35bed76722cf680964a04ad6331135f5ff9029.
D7 is CitiBike regional V50/M4/Q30 shortage, T18000, pickup/drop60/60,
lambda0.15. Full input hash and commands are in campaign/identity.json.
It is exposed development data; real station geometry/capacities coexist
with constructed inventories, targets and planning assumptions.

|Arm|Paid wall s|Original UB|Global LB|Absolute gap|Relative gap|
|---|---:|---:|---:|---:|---:|
|P-GRB|1197.109|0.277320865934|0.197286478715|0.080034387219|28.86%|
|DS-X|1197.110|0.298231227790|0.204146294626|0.094084933164|31.55%|
|JDS-X|1197.078|0.325801574773|0.204770622380|0.121030952393|37.15%|
|K1-R|1197.140|0.215644075316|0.197729722520|0.017914352796|8.31%|

All remain uncertified. Absolute gap is UB-LB; relative gap is (UB-LB)/abs(UB)
for a nonzero available UB. Signed values are retained. JDS-X's stronger LB
does not compensate for its worse UB. Its P-relative gap-advantage retention
against current K1-R is-0.65996, left unclipped: JDS-X is worse than P itself.
This is not a comparison against a selected historical fastest K1 variant.

Gurobi13.0.2, Threads1, Seed0, PresolveAuto, requested gaps0 and original
numeric tolerances are unchanged. P uses original compact/native defaults,
with fresh canonical model/fingerprint binding and no external Start, cuts
or imported bounds. Every owned launcher/child used logical2/mask4 and restored
affinity. All startup, construction, probes, native work, verification,
observation and exit are paid. The sole process deadline and shutdown reserve
end the entire run; no internal resource slice or fallback is introduced.

The same-run absolute-gap trajectory is:

|Observed process time|P-GRB|DS-X|JDS-X|K1-R|
|---|---:|---:|---:|---:|
|300s|0.139455|0.222179|0.176539|UB unavailable|
|600s|0.093231|0.131756|0.176003|0.215644, analytical L0|
|900s|0.081834|0.099852|0.134991|0.019311|
|1200s|0.080034|0.094085|0.121031|0.017914|

The JDS-X/DS-X ordering reverses after300s. K1's startup witness is first
observed at598.125s; its earlier internal HGA state is not backdated into300s.
These are completed-observation checkpoints, not buffered native-runtime
timestamps. No unseen receipt or incomplete payload was found. This single
paired screen does not establish statistical significance, all-budget ordering,
or causality for differences from older builds/instrumentation.

## Mechanism and original-objective interpretation

DS-X and JDS-X finish startup at process9.914/10.260s before proof. Their
physical initial objectives are0.544511 and0.380774. The first24 complete
logical descent paths match exactly. The25th seed performs41 full decodes,
accepts2 intra-route moves and generates0 cross-route candidates. The full
DS-X neighborhood still executes298 cross-route checks and178 accepted moves
in both arms. Both actual native Starts are eligible, submitted, read back,
independently row/vector checked and accepted by Gurobi. This is an active
mechanism with a negative complete result, not an untriggered feature.

Both candidates use three LP probes and one terminal parent MIP. Their AM
decisions retain the parent because the lower child provides no strict bound
gain. K1-R uses five LPs and one target MIP after598.042s HGA/2739 generations.
These counts and retained scopes describe the different paths, not a causal
runtime decomposition or a new time-based controller.

The final P/DS-X/JDS-X routes serve47/47/49 stations and move209/210/213 bikes.
More service or volume therefore does not explain better F. K1's228-bike
witness has G0.038723 and deviation P1.179476; original P-GRB has G0.099891
and deviation P1.182864. Most of that UB difference is the Gini term. A future
quantity or fleet-allocation repair must score the complete coupled objective,
not a stationwise penalty or coverage proxy. algorithm.md describes the
unchanged method and symmetric-metric strengthening scope.

## Supervisor exception and independent evidence

All four optimizer processes returned normally within cap. The frozen driver
exited1 after rejecting K1-R because it demanded a native MIPSOL physical
witness. K1's target MIP reports Solution count0, while its same-run verified
HGA route remains a legitimate original UB. That route is also feasible in
the actual active interval model: the independent map checks23563 columns
and103581 rows, with maximum row residual1.11e-16. It was not a native
MIPSOL observation. Legal full-cover native bounds provide the independent LB.

campaign/supervisor_scope_correction.json records the narrow offline correction.
Every original physical, bound/coverage, settings, input/build, deadline and
affinity gate was rechecked. The failed raw audit, driver, summary and all run
files remain byte-identical; postprocessing applies the correction in memory.
No native witness is invented, no original criterion is weakened, and no run
is repeated. The first correction script incorrectly assumed the HGA witness
was outside the interval; actual bounds disproved that assertion. Its failed
version is retained. A separate duplicate-key aggregation error in the Start
audit is likewise retained and repaired. Neither is a solver correctness failure.

Independent replay checks339 physical witnesses and189 full-domain native-bound
events across562 committed events, including final-witness consistency against
earlier bounds. Full-cover/numeric certification remains distinct from strict
rational proof; no certificate is claimed for these open endpoints.

## Cost, delivery and next decision

Four full runs cost4788.437s with15 actual Optimize calls. No new CTest, build
or native fixture ran;54 passing tests are inherited from R73 v6. The fresh
no-Optimize P export costs0.297s inside0.356s preflight. Timed postprocessing
retains0.565s driver replay,1.101s supervisor-scope replay,0.743s independent
analysis,4.062s mechanism checks,2.466s across two failed offline commands,
12.926s packaging and0.504s read-only delivery verification. These separate
QA costs are never subtracted from algorithm time; interactive inspection and
publication time are not claimed as a complete machine-time census.

All1251 raw files are retained in5 lossless bundles:196409146 original bytes,
28970548 compressed bytes. Every member passed length/SHA256 verification.
The original raw tree and binary remain local. See reproduce.md for the
portable no-extraction hash check and full-replay path limitations.

Do not extend this unchanged candidate to the proposed3600s or confirmation
panel on the strength of its starter or small-role gain. Preserve it as a
default-off research facility and retain R73's positive D3/D4 evidence. The
next hypothesis concerns finite physical quantity revision and joint served-node
reassignment, with original-objective scoring and prefix-load checks. The
targeted literature/reassessment notes explain both precedent and limitations;
no new mechanism or experiments are admitted by this report. Publish this
independent stage, then declare the next bounded implementation/qualification
plan. C2/D6 new-build full comparison, D7 repair and broader independent
confirmation remain necessary for the overall goal.
