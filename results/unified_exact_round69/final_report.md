# Round69 — frozen VD-S validation

This stage changes no solver source, executable or algorithm parameter. It
tests the completed Round68 VD-S integration on a bounded public panel.
D3 is a design-point repeat; D6 is the original design-role long comparison.
E7/S12/N12/D7 are historical public validation, not sealed independent data.
The overall research goal remains unmet: E7/S12 startup losses persist.

Every arm uses Gurobi13.0.2, Threads1, Seed0, PresolveAuto, zero requested
gaps and the original numerical standards. P-GRB is the original compact
model with native defaults and no HGA, explicit external Start, added
cut or imported bound. K1-R contains only the defined reliability fixes
with full HGA/AM; VD-S is the unchanged one-hot/verified-Start candidate.
All required work and the same whole-run deadline are charged.

## Completed evidence

All 16 performance runs completed, with 63 experiment Optimize calls and
14580.595s paid process wall. No correctness micros or new CTest batch were run.
The identical binary inherits Round68's 45-test qualification; this is prior
qualification, not new cost. Six no-opt P exports took 0.641s separately.
No additional repeat, extension, replacement case or parameter change was opened.
See resource_status.json for final QA pass times, which are not a cumulative
account of all earlier read-only audit invocations.

| Role | Arm | Whole-run cap | Certified | Paid wall | Verified UB | Global LB | Signed absolute gap | HGA wall |
|---|---|---:|---|---:|---:|---:|---:|---:|
|D3|VD-S|300|True|84.687|0.045001550056|0.045001550056|7.633e-17|2.097|
|E7|P-GRB|120|True|1.313|0.020382503842|0.020382503842|3.469e-17|0.000|
|E7|K1-R|120|True|5.657|0.020382503842|0.020382503842|2.082e-17|4.300|
|E7|VD-S|120|True|5.657|0.020382503842|0.020382503842|0.000e+00|4.367|
|S12|P-GRB|120|True|5.156|0.058563973126|0.058563973126|4.163e-17|0.000|
|S12|K1-R|120|True|40.938|0.058563973126|0.058563973126|1.874e-16|38.412|
|S12|VD-S|120|True|39.672|0.058563973126|0.058563973126|2.706e-16|38.382|
|N12|P-GRB|120|True|3.906|0.804625519720|0.804625519720|-1.110e-16|0.000|
|N12|K1-R|120|True|7.203|0.804625519720|0.804625519720|3.220e-15|1.741|
|N12|VD-S|120|True|3.641|0.804625519720|0.804625519720|7.772e-16|1.748|
|D6|P-GRB|3600|False|3597.171|0.157241175852|0.150835617128|0.006405559|0.000|
|D6|K1-R|3600|False|3597.125|0.157083131103|0.148332716989|0.008750414|323.723|
|D6|VD-S|3600|False|3597.141|0.157083131103|0.153107452372|0.003975679|550.600|
|D7|P-GRB|1200|False|1197.109|0.277320865934|0.197286478715|0.080034387|0.000|
|D7|K1-R|1200|False|1197.141|0.215644075316|0.197729722520|0.017914353|560.423|
|D7|VD-S|1200|False|1197.078|0.215644075316|0.203880099142|0.011763976|547.108|

The underlying CSV preserves full floating-point precision, including tiny
negative signed gaps within the unchanged numerical tolerance. No bound is
silently clipped to manufacture a certificate or zero gap. HGA subtraction
is attribution only; formal comparisons always use the complete paid run.

## Frozen practical comparisons

| Role | Reference | Classification | VD-S minus reference wall | UB delta | LB delta | Gap delta | Bound relation |
|---|---|---|---:|---:|---:|---:|---|
|E7|K1-R|below_practical_threshold|0.000|0.000000000|0.000000000|-0.000000000|aligned_or_unchanged|
|E7|P-GRB|material_regression|4.344|0.000000000|0.000000000|-0.000000000|aligned_or_unchanged|
|S12|K1-R|below_practical_threshold|-1.266|0.000000000|-0.000000000|0.000000000|aligned_or_unchanged|
|S12|P-GRB|severe_regression|34.516|-0.000000000|-0.000000000|0.000000000|aligned_or_unchanged|
|N12|K1-R|material_improvement|-3.562|0.000000000|0.000000000|-0.000000000|aligned_or_unchanged|
|N12|P-GRB|below_practical_threshold|-0.265|0.000000000|-0.000000000|0.000000000|aligned_or_unchanged|
|D6|K1-R|material_improvement|0.016|0.000000000|0.004774735|-0.004774735|aligned_or_unchanged|
|D6|P-GRB|material_improvement|-0.030|-0.000158045|0.002271835|-0.002429880|aligned_or_unchanged|
|D7|K1-R|material_improvement|-0.063|0.000000000|0.006150377|-0.006150377|aligned_or_unchanged|
|D7|P-GRB|severe_improvement|-0.031|-0.061676791|0.006593620|-0.068270411|aligned_or_unchanged|

A both-open gap classification is not a claim that UB and LB individually
improve. Mixed bound changes and certificate status must be read alongside
the raw values. No per-point fastest-variant requirement is introduced.

## Repeat and startup scope

D3 certifies in 84.687s versus 84.172s in Round68,
with identical binary, initial routes, models/call sequence and final bounds.
This one repeat supports reproducibility of that design-point gain, not
statistical equivalence or a new independent confirmation sample.
E7 and S12 remain P regressions dominated by HGA startup. N12 retains a
material K1-R improvement while staying close to P. See small_validation.md.
A prospective local-descent source/test draft remains isolated under ignored
build/round70_draft; it was not applied, compiled or measured in this stage.

## D6 timing qualification

D6/VD-S spent about 550.595s in its HGA loop versus 323.719s for K1-R.
Both report 26383 uncached decoder calls, retain identical initial routes
and have the same 2071-generation best-fitness/improvement history.
The complete offspring history was not retained. This large variation
prevents attributing all observed long-window
differences to the algorithm alone. All actual time remains charged; no
counterfactual time correction, discarded run or extra repeat is used.
A brief CPU sample and a read-only mixed-core topology query do not prove
the cause. No affinity, priority, service or measured source was changed.
See long_validation.md and run13_startup_comparison.json for the completed
endpoint interpretation and the limits of this measurement. Any later
common-core protocol requires newly matched controls for every arm.

## Long-window results

D6 at3600 has VD-S gap0.003975678731177851 versus P0.0064055587246548695
and K1-R0.008750414113820076: reductions37.9339% and54.5658%. VD-S
improves both UB and LB over P; the larger contribution is its stronger
bound. The observed long-window P deficit is repaired in this run,
subject to the large startup timing variation above. Its within-run600
checkpoint is worse than P, so no uniform advantage across time is claimed.
D7 at1200 has VD-S gap0.011763976173360113 versus P0.08003438721943765
and K1-R0.017914352795947386: reductions85.3013% and34.3321%. The
important K1/P advantage is retained and strengthened. VD-S and K1-R
use identical initial routes and end at the same UB; their gap difference
comes from the stronger VD-S lower bound. All six long runs remain open.
D7 HGA wall is547.108s/560.423s for VD-S/K1-R, with matching2739
generations,41479 decoder calls and full retained routes. This smaller
timing difference is still paid. VD-S uses seven LP and two MIP calls
versus five LP and one MIP for K1-R; all extra work is charged.
See long_validation.md for original-problem terms, checkpoint limits
and the complete UB/LB interpretation.

## Starts, witnesses and time provenance

The audit covers 8 actual VD-S MIP Start decisions:
8 eligible,8 accepted in native logs, and
8 full submitted vectors observed in MIPSOL.
10 control runs were checked for absence of this explicit Start path.
Submitted/readback vectors are independently checked against all exported
bounds, types, rows and objective. Physical routes and complete interval
coverage are checked separately; zero requested gaps do not imply a rational certificate.
MIPSOL equality is evidence from the qualified C++ observer; complete
native event vectors were not separately retained for a second replay.
11/11 retained HGA initial routes have full-content event provenance.
A canonical route hash and a conservative generation-completion timestamp
establish historical availability; matching objective values alone do not.
Intermediate P incumbents remain native telemetry because their full vectors
were not retained. Synthetic final rows are excluded from earlier checkpoints.
Buffered frontier callbacks receive a conservative setup/tail time correction;
its recorded shifts can understate early progress. Main full-window conclusions
use completed endpoints and are unaffected by this timing limitation.
See within_run_checkpoints.csv and checkpoint_provenance.md.

## Scope and continuation

The integrated D6/D7 interpretation is in long_validation.md. This bounded stage cannot establish
general runtime dominance, remove the documented startup regressions, or
substitute for independent validation of a subsequently revised candidate.
A new draft PR preserves this stage; it does not complete the sustained goal.
Reproduction, frozen algorithm, source identity and raw/compact evidence
locations are documented in reproduce.md, algorithm.md and build_v1.json.
