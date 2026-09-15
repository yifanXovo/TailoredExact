# Long validation — completed frozen comparisons

The frozen D6 comparison gives every whole algorithm a3600s deadline; D7
uses1200s. All six long runs completed in the declared serial P/K1-R/VD-S
order. No candidate, gate, source or parameter was revised for these
measurements. The framework reserves the same finishing margin; reported
actual process wall includes HGA, every LP/MIP, construction, verification
and finalization. Unused deadline time is not counted as executed work.

## D6 completed endpoints

| Arm | Paid wall | Certified | Verified UB | Global LB | Signed gap | Relative gap |
|---|---:|---|---:|---:|---:|---:|
| P-GRB |3597.171|no|0.1572411758522922|0.15083561712763732|0.0064055587246548695|4.073716%|
| K1-R |3597.125|no|0.15708313110317415|0.14833271698935407|0.008750414113820076|5.570563%|
| VD-S |3597.141|no|0.15708313110317415|0.1531074523719963|0.003975678731177851|2.530939%|

Relative gap is (UB-LB)/abs(UB) for a finite nonzero UB. All three remain open.
P's physical route recomputes F0.15724117585229214; both candidates recompute
F0.15708313110317407. Full precision and numerical discrepancies are retained.

K1-R's slightly better UB cannot offset its weaker LB: its gap exceeds P by
0.002344855389165207 (36.6066%). This reproduces the historical long-window
P deficit on this original V30/M3/Q30/T18000 compact shortage role.
VD-S improves both UB and LB over P: UB falls0.00015804474911804145 and LB
rises0.0022718352443589773. Its gap falls0.0024298799934770188, or37.9339%.
Against K1-R, UB is unchanged and LB rises0.004774735382642226, reducing gap
54.5658%. Both VD-S comparisons meet the frozen material threshold. The
larger contribution versus P is the stronger bound, not the small UB change.
This is an observed long-window repair, with the timing qualification below;
it is not a certificate or a demonstration of stable family-wide dominance.

The three arms used1,7 and6 Optimize calls. VD-S used five LPs and one MIP;
K1-R used five LPs and two MIPs. K1-R's terminal MIP had no native incumbent,
so its independently verified HGA routes supply the legal outer UB. VD-S's
complete existing-witness Start is accepted in the native log and observed as
the full submitted vector in MIPSOL. Independent model bound/type/row/objective
checks and physical checks pass; proof coverage includes the full initial
range and the replaced parent's exact child union. No bound is clipped.
Endpoint checks are in endpoint_checks/11.json through13.json; full audits
are in start_checks.json, witness_model_checks.json and coverage_checks.csv.

## Within-run trajectory and scope

These are checkpoints of the same3600 runs, not separately restarted tests.

| Whole-run time | P gap | K1-R gap | VD-S gap |
|---:|---:|---:|---:|
|300|0.014008044|0.157083131|0.157083131|
|600|0.012255293|0.013858981|0.015116867|
|1200|0.010323024|0.011304511|0.008059710|
|1800|0.008383969|0.010217643|0.006414949|
|2400|0.007461993|0.009428287|0.005354949|
|3600|0.006405559|0.008750414|0.003975679|

At300 the candidate seed routes are already available by full-content HGA
event provenance, but exact initialization has not started; LB0 is the valid
nonnegative-objective bound. VD-S is worse at600 in this run, unlike its
separate Round68 short result. Its much longer measured startup reduces the
native proof time left at that checkpoint. From1200 onward these checkpoints
favor VD-S, and the complete endpoints establish the reported final gap gain.
The early negative result is retained; no single-window superiority is claimed.

P's intermediate UBs are native telemetry because complete intermediate vectors
were not retained. Candidate initial routes require full-content event linkage
and conservative generation-completion time. Final routes are never backdated.
Buffered frontier callbacks additionally receive a conservative setup/tail
time shift: VD-S3.3920681s, K1-R0.0233948s and0.0920984s for its two native
groups. These are upper bounds on missing setup plus unobserved tail, not
measurements of setup cost. They can understate early progress; full endpoints
are unaffected. See within_run_checkpoints.csv and checkpoint_provenance.md.

## D6 timing qualification

VD-S's completed HGA wall is550.5999342s versus323.7226881s for K1-R, a
70.0838% increase. Both report2071 generations and26383 uncached decoder
calls, identical per-generation best-fitness/improvement history, and the same
full retained initial routes. The complete offspring history was not retained.
These facts establish a large timing variation without establishing its cause.
See hga_timing_pairs.json and run13_startup_comparison.json.

A three-second CPU sample observed ExactEBRP using about one core alongside
GameDVR and ChatGPT activity. It does not establish sustained contention.
Windows reports mixed processor efficiency classes (logical0--15 class1,
16--19 class0); the read-only topology query cannot identify past placement.
No affinity, priority, service, solver setting, source or run was changed.
All actual delay remains paid. There is no discarded run, extra repeat or
counterfactual subtraction. The observed final gain remains useful evidence,
but this measurement alone cannot quantify a clean algorithm-only speed gain
or establish timing stability. A future uniform common-core protocol requires
newly matched controls and must not silently pool changed-affinity timings.

## D7 completed protection comparison

Original V50 regional r1 shortage, M4/Q30/T18000; public historical validation.

| Arm | Paid wall | Certified | Verified UB | Global LB | Signed gap | Relative gap |
|---|---:|---|---:|---:|---:|---:|
| P-GRB |1197.109|no|0.27732086593398886|0.1972864787145512|0.08003438721943765|28.859850%|
| K1-R |1197.141|no|0.21564407531579505|0.19772972251984766|0.017914352795947386|8.307371%|
| VD-S |1197.078|no|0.21564407531579505|0.20388009914243493|0.011763976173360113|5.455274%|

K1-R's exact bounds reproduce the Round65 K1-H endpoint. VD-S retains the
important K1/P advantage and strengthens its LB by0.0061503766225872725
at the same UB, reducing gap34.3321% against K1-R. Against P, UB improves
0.06167679061819381 and LB improves0.006593620427883723, reducing gap
0.06827041104607753 (85.3013%). The former is a material improvement and
the latter reaches the frozen larger-effect threshold. No K1 protection is
lost on this role. All three remain open; none is presented as certified.

P's final routes serve47 stations, collect/drop209 bikes and have maximum
duration17978.256445183477. Both candidates retain the same50-station
routes, collect/drop228 bikes, and have maximum duration17975.490961810894.
All satisfy the original18000 horizon. Candidate Gini is0.03872267378877319
versus P0.09989121031469565, while penalty P is1.179476010180145 versus
1.1828643707952866. Thus most of the candidate UB gain over P comes from
fairness. VD-S's additional gain over K1-R comes from its lower bound, not
another heuristic or a better initial/final UB.

K1-R and VD-S complete the same2739 HGA generations and41479 uncached
decoder calls, with identical best-fitness/improvement history and full initial
routes. Complete HGA wall is560.4226016s and547.1080094s respectively;
VD-S is2.3758% faster in that phase. This variation is paid and not removed.
Both seed route arrays and full event hashes match. This does not establish
complete internal offspring history or universal timing stability.

VD-S uses seven LP calls and two MIPs: a child-bound target solve followed
by the required terminal solve. K1-R uses five LP calls and one next-leaf
target MIP. Every extra lookahead, model operation and native call remains
charged. Both VD-S MIPs use the same exported25943-column/104726-row model
with724951 nonzeros and fingerprint0x9d22532c. Both explicit Starts are
eligible, accepted and fully observed; submitted/readback vectors pass the
independent actual-row/type/bound/objective audit. K1-R's native terminal
log reports zero solutions, so its HGA routes supply the legal outer UB.
Final proof coverage contains one root, two replaced parents and complete
child unions. Physical/settings/frontier/model checks all pass.

| Within-run time | P gap | K1-R gap | VD-S gap |
|---:|---:|---:|---:|
|300|0.139583377|0.215644075|0.215644075|
|600|0.093231319|0.033159274|0.025410279|
|1200|0.080034387|0.017914353|0.011763976|

At300 both candidates have a verified seed but have not begun exact search;
LB0 is the mathematical nonnegative bound. The same intermediate-UB scope
and conservative timestamp rules described above apply. K1-R's buffered
native group shifts44.4403204s; VD-S's groups shift0.1183607s and
106.9852981s. These include unobserved tails and can understate early
progress differently for different arms. Therefore no precise early speed
ranking is inferred from these conservative checkpoints. Complete1200
endpoints are unaffected and support the principal protection conclusion.

## Completed stage evidence and remaining limits

All16 performance runs are audited:14580.595s paid process wall,63 experiment
Optimize calls, zero failures. Six no-opt P exports took.641s separately.
Eight actual Starts are eligible, accepted and fully observed; ten controls
omit the explicit new Start. The43 offline initial-witness model checks
include16 incompatible intervals and zero failures. All11 retained HGA routes
have full-content event linkage. The compact package contains236 artifacts.
The final full witness-model scan took9.922s and the actual-Start scan4.968s;
these are final-pass QA timings, not a cumulative total of earlier analysis.
No new compilation, CTest batch or native qualification was run; qualification
is inherited from the identical Round68 binary and its45-test result.

The frozen integration is useful: D3 repeats its gain, N12 repairs a non-startup
small-role loss, D6 improves the long-window P deficit with an explicit timing
qualification, and D7 preserves and strengthens an important protection role.
E7/S12 startup losses remain material/severe, so the overall goal is unmet.
Neither these development/public historical roles nor the single long D6
measurement establish general dominance. If these data steer a new startup
rule, they become development data for it; its confirmation must use other
roles not used for that revision.

The prospective decoded-descent source/test draft remains isolated, unapplied,
uncompiled and untested at this stage's end. It is not a Round69 component.
After this evidence is committed and a new draft PR is created, the next stage
should address startup with a separately frozen admissible rule and newly
matched measurement controls. No additional experiment was added to Round69.
