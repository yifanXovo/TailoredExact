# Round122 frozen-method benchmark: complete result interpretation

The complete preregistered panel contains six new Seed0 problems and two
fixed Seed1 repeats: 32 once-only arms and 48 evaluable directed comparisons.
The single stage decision is **COMPLETE /
BENCHMARK_MIXED_NO_NEW_PRIMARY_SELECTION**. Retain **frozen M-B as the
existing paper reference**; ENS-C remains the unchanged project default,
and MB-D1 remains a separately reported research candidate. This is no
default replacement or new algorithm selection. This batch ends here.

D1/P has 5 WIN and 1 MIXED on the six new problems. Both fixed Seed1 D1/P
comparisons are WIN. The decisive unmet positive-selection condition is
incremental breadth: only one exposed new role supplies a material D1/M-B
gain or new certificate, below the registered requirement of two. There
is no severe comparison or unresolved proof-source rejection in this batch.

The complete numerical tables are [32 arms](all32_arms.csv) and
[48 pairs](all48_pairs.csv); [the final report](final_report.md) includes
all three clocks. Values below are rounded for readability; the JSON/CSV
evidence retains full precision, signed gaps and original proof categories.
Every comparison uses its own physical U, qualified L and the original
certificate-first materiality rules. Case discussions use Seed0 unless
explicitly marked Seed1. No open cap is interpreted as a final proof time.

## V20 certification and the incremental D1 comparison

On PB-C20-B, all four methods finish with the same physical upper bound
0.2246803118, comprising G=0.1052925937 and lambda*P=0.1193877181.
ENS-C, M-B and MB-D1 obtain clean nonzero numerical certificates; cold
P-GRB remains open with L=0.1765783752 and signed gap=0.0481019367.
Consequently, each integrated method is WIN against P-GRB by certificate
priority. P-GRB's open window does not provide a certification-time ratio.

MB-D1 certifies in T_produce=665.0688 seconds, compared with 395.8595 for
M-B and 430.5576 for ENS-C. These two certified-time comparisons are LOSS,
with D1/control ratios 1.68006 and 1.54467, respectively; neither is severe.
The common gain over the cold benchmark therefore coexists with an
unfavorable D1 increment. D1 is actually installed and executes two
expanded Optimize calls. Its final own U exceeds beta1=0.1348133925;
the observed result does not establish elimination of the right branch
through that incumbent threshold.

On PB-B20-S, all four methods certify the same nonzero objective
0.8631523206, comprising G=0.3598978293 and lambda*P=0.5032544912.
T_produce is 116.0328 seconds for cold P-GRB, 4.6224 for ENS-C, 2.6320
for M-B and 2.6984 for MB-D1. D1/P is WIN with an actual certified-time
ratio of 0.0232554. Both D1/M-B and D1/ENS-C are TIE under the fixed
30-second minimum time-materiality threshold. D1 is exposed, but this
role supplies no material incremental gain over M-B.

These are two differently constructed problems, not a controlled estimate
of a source effect. Inventory regime, geometry, Q and T also differ.

## V35 open endpoints and adverse tradeoffs

PB-C35-U remains open for all four complete methods. Every reported lower
bound is qualified and positive; no source reduction or proof-source
rejection occurs in this group.

| Method | Own U | Qualified L | Signed gap |
|---|---:|---:|---:|
| M-B | 0.1696364022 | 0.0839518543 | 0.0856845479 |
| MB-D1 | 0.1793004366 | 0.0835339935 | 0.0957664431 |
| P-GRB | 0.1747718876 | 0.0597029032 | 0.1150689844 |
| ENS-C | 0.1642374878 | 0.0815753938 | 0.0826620940 |

D1/P is MIXED: a materially worse own U accompanies a materially better
lower bound and smaller gap. M-B/P and ENS-C/P are WIN. D1/M-B,
D1/ENS-C and M-B/ENS-C are LOSS; none of this group's comparisons is
severe under the preregistered joint conditions.

For the following endpoint differences, dX means candidate minus control.
The identities dgap=dU-dL and dU=dG+d(lambda*P) retain their full precision
in the machine evidence; the displayed values are rounded.

| Pair | dU | dL | dgap | dG | d(lambda*P) |
|---|---:|---:|---:|---:|---:|
| D1/P | +0.0045285490 | +0.0238310904 | -0.0193025413 | +0.0046846185 | -0.0001560695 |
| D1/M-B | +0.0096640344 | -0.0004178608 | +0.0100818952 | +0.0011295305 | +0.0085345039 |
| D1/ENS-C | +0.0150629488 | +0.0019585998 | +0.0131043490 | +0.0039806932 | +0.0110822556 |

Thus D1's worse U against P-GRB combines a higher physical G with a
slightly lower penalty term. Against M-B and ENS-C, both physical
objective components are higher. These are arithmetic endpoint
explanations, not proportions of an internal causal mechanism.

D1 installs once and executes one expanded native Optimize. The paid
root LP pair has beta0=0 and beta1=0.1158382125, with midpoint
0.1158383125. Installation takes 0.4243215 seconds. These endpoints and
exposure establish what formulation ran; they do not predict a benefit
or establish native h fixing or branching. Final own U remains above
beta1.

Each integrated method makes three returned LP calls and one returned
MIP call on this role. The recorded MIP partition is 2353.9320 to
2354.7640 seconds; H takes 6.7390 to 6.8072 seconds and the recorded LP
partition takes 1.3570 to 1.5580 seconds. The dominant recorded work is
the single native MIP search/proof request. This supports a cost location,
while the distinction between incumbent search and a proof tail requires
actual progress evidence. Nested timers are not added again, and this
observation does not attribute the D1 regression to an internal branch
event or establish a general need for a new cut.

PB-B35-B also remains open for all four methods. Its cold benchmark has
the explicitly independent lower floor L=0; this is not a positive native
bound. The three integrated methods have qualified positive bounds. No
proof-source rejection or source reduction occurs in this group.

| Method | Own U | Qualified L | Signed gap |
|---|---:|---:|---:|
| MB-D1 | 0.2345814099 | 0.0920079836 | 0.1425734262 |
| P-GRB | 0.3055557782 | 0.0000000000 | 0.3055557782 |
| ENS-C | 0.2465044704 | 0.1322879680 | 0.1142165024 |
| M-B | 0.2465044704 | 0.1276343018 | 0.1188701686 |

Each integrated method is WIN against P-GRB. D1/M-B and D1/ENS-C are
MIXED: D1's better physical U accompanies a weaker lower bound and a
larger gap. M-B/ENS-C is TIE under the fixed materiality rules; their
identical own U and the lower-bound difference do not reach the gap
threshold. None of this group's comparisons is severe.

| Pair | dU | dL | dgap | dG | d(lambda*P) |
|---|---:|---:|---:|---:|---:|
| D1/P | -0.0709743684 | +0.0920079836 | -0.1629823520 | -0.0214743684 | -0.0495000000 |
| D1/M-B | -0.0119230606 | -0.0356263182 | +0.0237032577 | -0.0044230606 | -0.0075000000 |
| D1/ENS-C | -0.0119230606 | -0.0402799844 | +0.0283569239 | -0.0044230606 | -0.0075000000 |

D1's own U comprises G=0.0815814099 and lambda*P=0.1530000000.
M-B and ENS-C finish with G=0.0860044704 and lambda*P=0.1605000000;
P-GRB finishes with G=0.1030557782 and lambda*P=0.2025000000.
Both physical components favor D1 in these three endpoint comparisons,
while the bound tradeoff against M-B and ENS-C prevents an incremental
WIN. The first four roles therefore contain common gains over P-GRB,
but no material D1/M-B WIN.

D1 installs once and executes one expanded Optimize, with two paid root
proofs, beta0=0 and beta1=0.1235266342. Final own U remains above beta1.
Installation takes 0.3716252 seconds. Each integrated method again makes
three returned LP calls and one returned MIP call. Their recorded MIP
partitions span 2360.6240 to 2361.7340 seconds, compared with 0.9062 to
0.9114 seconds for H and 1.2550 to 1.5480 seconds for LP. This locates
the dominant recorded cost in the MIP request, with the same limits on
internal causal attribution as PB-C35-U.

## V50 common gains without D1 exposure

PB-C50-S remains open for all four methods, each with a qualified positive
lower bound. No source reduction, proof-source rejection, damaged call or
severe comparison occurs. This role adds no V50 nonzero certificate.

| Method | Own U | Qualified L | Signed gap |
|---|---:|---:|---:|
| MB-D1 | 0.3723417755 | 0.3568747399 | 0.0154670356 |
| M-B | 0.3723417755 | 0.3568747399 | 0.0154670356 |
| ENS-C | 0.3723417755 | 0.3579807999 | 0.0143609756 |
| P-GRB | 0.4259500753 | 0.3492206958 | 0.0767293795 |

Each integrated method is WIN against cold P-GRB. All three comparisons
among MB-D1, M-B and ENS-C are TIE. D1 and M-B have identical qualified
endpoints. ENS-C's lower bound is higher by 0.0011060599, below the
applicable gap-materiality threshold for either comparison against it.
All four windows remain open, so no certification-time ratio applies.

| Pair | dU | dL | dgap | dG | d(lambda*P) |
|---|---:|---:|---:|---:|---:|
| D1/P | -0.0536082998 | +0.0076540441 | -0.0612623439 | -0.0526823704 | -0.0009259294 |
| D1/M-B | +0.0000000000 | +0.0000000000 | +0.0000000000 | +0.0000000000 | +0.0000000000 |
| D1/ENS-C | +0.0000000000 | -0.0011060599 | +0.0011060599 | +0.0000000000 | +0.0000000000 |

The three integrated methods finish with G=0.0501195842 and
lambda*P=0.3222221913. Cold P-GRB finishes with G=0.1028019545 and
lambda*P=0.3231481207. Thus both components favor the integrated methods,
with most of the observed U difference located in G. This is a physical
endpoint decomposition; it does not identify an internal search cause.
All recorded physical fleets contain all four vehicles.

The D1 flag is enabled, but the saved root pair is incomplete: one paid
root-LP-return event is retained, the not_exposed event records
pair_complete=false, and both installation and expanded Optimize counts
are zero. The original controller records three atomic_split events.
The first two preserve infeasible right children L0.1 and L0.0.1; the
third records adaptive_mass_score_reaches_tau. These are operations of
the original AM path. The observed common gains over P-GRB supply no
exposed D1 increment on this role. The valid unexposed observation
remains in the complete-method panel.

Each integrated method makes seven returned LP calls and one returned
MIP call. H takes 34.1420 to 34.3713 seconds, the recorded LP partition
26.8320 to 88.1210 seconds, and the MIP partition 3406.4330 to 3468.0830
seconds. The dominant recorded cost remains within the single MIP
request, alongside the observed LP and original AM work. These timings
do not establish counterfactual D1 overhead or an internal branch cause.
Nested timers are retained without adding them again. Post-seal
T_verify spans 40.0557 to 40.3518 seconds for the integrated methods
and is 1.5725 seconds for P-GRB, reported separately from T_produce.

## V50 open gains with actual D1 exposure

PB-B50-U remains open for all four methods, each with a qualified positive
lower bound. No source reduction, proof-source rejection, damaged call or
severe comparison occurs. This role adds no V50 nonzero certificate.

| Method | Own U | Qualified L | Signed gap |
|---|---:|---:|---:|
| P-GRB | 1.1769557585 | 0.0683793824 | 1.1085763761 |
| MB-D1 | 0.6772984190 | 0.4712348696 | 0.2060635494 |
| M-B | 0.6974735096 | 0.4553454000 | 0.2421281096 |
| ENS-C | 0.8325480152 | 0.4523603674 | 0.3801876478 |

All six directed comparisons are WIN. Alongside the common gains over
cold P-GRB, this is the first of the six new roles with an exposed,
material D1/M-B WIN. D1 also beats ENS-C, and M-B beats ENS-C. All four
windows remain open, so no certification-time ratio applies.

| Pair | dU | dL | dgap | dG | d(lambda*P) |
|---|---:|---:|---:|---:|---:|
| D1/P | -0.4996573395 | +0.4028554871 | -0.9025128267 | -0.0798656110 | -0.4197917286 |
| D1/M-B | -0.0201750906 | +0.0158894696 | -0.0360645602 | -0.0055917477 | -0.0145833429 |
| D1/ENS-C | -0.1552495962 | +0.0188745022 | -0.1741240984 | -0.0219163105 | -0.1333332857 |

D1's own U comprises G=0.1595900876 and lambda*P=0.5177083314.
M-B finishes with G=0.1651818353 and lambda*P=0.5322916743; ENS-C
with G=0.1815063981 and lambda*P=0.6510416171; and P-GRB with
G=0.2394556985 and lambda*P=0.9375000600. Both physical components
favor D1 in the three comparisons above, with the larger arithmetic
contribution located in the penalty term. These endpoint differences
do not establish an internal causal mechanism. All recorded physical
fleets contain the complete four vehicles, including the heterogeneous
Q vector [20,25,35,40].

D1 obtains both paid root proofs, installs once and executes one expanded
Optimize. The saved interval endpoints are a=0, m=0.4578812999 and
b=0.9157625997; beta0=0.2305170541 and beta1=0.6464228399.
Installation takes 0.7887936 seconds. The original AM record selects
exact-close with reason adaptive_mass_no_strict_child_improvement;
there is no atomic_split event for this arm. Final own U=0.6772984190
remains above beta1, so these observations do not establish exclusion
of the right branch by an incumbent threshold. The last native sample
records objective=0.6772984168 and h=0, while its independently checked
physical F is 0.6772984190. Native h fixing or branching remains unknown;
the observed h value is not evidence of either event.

Each integrated method makes three returned LP calls and one returned
MIP call. H takes 1.7617 to 1.7660 seconds, the recorded LP partition
3.3000 to 4.0060 seconds, and the MIP partition 3548.7620 to 3551.1960
seconds. Cold P-GRB has one returned MIP call, recorded at 3569.0370
seconds. These locate the dominant recorded work in native MIP requests;
they do not distinguish incumbent search from proof effort or identify
the internal cause of the observed differences. Nested timers are not
added again. Post-seal T_verify spans 19.7309 to 25.6512 seconds for the
integrated methods and is 1.3026 seconds for P-GRB, separately reported
from T_produce.

## The complete six-role Seed0 layer

D1/P has five WIN and one MIXED, with no LOSS or severe comparison.
Both M-B/P and ENS-C/P have six WIN. D1/M-B and D1/ENS-C each have
one WIN, two LOSS, one MIXED and two TIE. M-B/ENS-C has one WIN,
one LOSS and four TIE. All 36 directed comparisons are evaluable.

D1 is exposed on five of the six new roles, including V35 and V50;
the valid unexposed PB-C50-S role remains in the panel. Clean nonzero
certificate counts are one for P-GRB and two each for ENS-C, M-B and
MB-D1. All these certificates occur at V20. None of the four methods
obtains a new V35 or V50 nonzero certificate on this Seed0 layer.

Only one exposed role supplies a material D1/M-B WIN, so the registered
condition requiring at least two such roles or new certificates is not
met. This is a finite candidate-selection condition, not a significance
test. Both mandatory Seed1 groups are now complete. Neither the proof-risk
priority nor either primary performance veto fires; the final stage and
one fixed existing paper reference are stated below.

## Fixed PB-B35-B Seed1 repeat

All four methods remain open, with qualified native lower endpoints.
There is no source reduction, proof-source rejection or damaged call.
The tiny positive P-GRB bound is retained explicitly below. It differs
from this same input's independent zero floor at Seed0; rounding the
Seed1 bound to zero must not change its evidence category.

| Method | Own U | Qualified L | Signed gap |
|---|---:|---:|---:|
| ENS-C | 0.2345814099 | 0.1146410114 | 0.1199403984 |
| P-GRB | 0.2797984344 | 2.0271896642e-18 | 0.2797984344 |
| MB-D1 | 0.2345814099 | 0.1383220420 | 0.0962593678 |
| M-B | 0.2465044704 | 0.0982245518 | 0.1482799186 |

Each integrated method is WIN against cold P-GRB. D1/M-B and D1/ENS-C
are also WIN. D1 and ENS-C have identical own U; D1's higher qualified
lower bound supplies their material gap improvement. M-B/ENS-C is LOSS,
with both a worse own U and a larger gap. It is not severe: its gap
worsening 0.0283395202 is below the joint severe gap threshold
0.0299850996, despite the U difference crossing the severe U threshold.
No certified-time ratio applies because all four windows remain open.

| Pair | dU | dL | dgap | dG | d(lambda*P) |
|---|---:|---:|---:|---:|---:|
| D1/P | -0.0452170246 | +0.1383220420 | -0.1835390666 | -0.0152170246 | -0.0300000000 |
| D1/M-B | -0.0119230606 | +0.0400974902 | -0.0520205508 | -0.0044230606 | -0.0075000000 |
| D1/ENS-C | +0.0000000000 | +0.0236810306 | -0.0236810306 | +0.0000000000 | +0.0000000000 |
| M-B/ENS-C | +0.0119230606 | -0.0164164596 | +0.0283395202 | +0.0044230606 | +0.0075000000 |

D1 and ENS-C finish with G=0.0815814099 and lambda*P=0.1530000000.
M-B finishes with G=0.0860044704 and lambda*P=0.1605000000;
P-GRB with G=0.0967984344 and lambda*P=0.1830000000. Both components
therefore favor D1 against P-GRB and M-B. Conversely, both components
are worse for M-B against ENS-C, alongside its weaker lower bound.
All four physical fleets retain the complete three vehicles. These
are endpoint explanations, without an internal causal attribution.

D1 has both paid root proofs, one installation and one expanded Optimize.
Its saved endpoints are a=0, m=0.1235267342 and b=0.2470534685;
beta0=0 and beta1=0.1235266342. Installation takes 0.3657699 seconds.
The original AM record selects exact-close with reason
adaptive_mass_no_strict_child_improvement, with no atomic_split event.
Final own U=0.2345814099 remains above beta1. Native h fixing or
branching remains unknown; the threshold does not establish exclusion
of the right branch by this incumbent.

Each integrated method makes three returned LP calls and one returned
MIP call. H takes 0.8920 to 0.9070 seconds, the recorded LP partition
1.2680 to 1.7190 seconds, and the MIP partition 2360.5640 to 2361.7600
seconds. The dominant recorded cost is in the native MIP requests;
these partitions do not distinguish incumbent search from proof effort.
Post-seal T_verify spans 18.6405 to 22.4222 seconds for the integrated
methods and is 1.9798 seconds for P-GRB, separately from T_produce.
The later 43.9826-second group reconciliation is charged to the group,
not to the last method's T_verify. Nested timers are not added again.

At Seed0, D1/M-B and D1/ENS-C were MIXED and M-B/ENS-C was TIE.
At Seed1 these become WIN, WIN and LOSS, respectively; D1/P is WIN at
both Seeds. D1 retains the same physical U at both Seeds, while its
qualified L increases from 0.0920079836 to 0.1383220420. ENS-C improves
its U to match D1, while M-B retains its Seed0 U and has a weaker lower
bound. The original Seed0 tradeoffs remain visible. This repeat is not
an additional new role, an estimate of a population probability or a
reason to replace Seed0 with a preferred Seed. In particular, this
incremental Seed1 WIN does not satisfy the requirement for two distinct
exposed new Seed0 roles with an incremental gain. The final PB-C50-S
Seed1 group is retained separately below; neither repeat adds a new role.

## Fixed PB-C50-S Seed1 repeat

All four methods remain open with qualified positive lower bounds. No source reduction, rejected proof source, damaged call or severe comparison occurs. The complete four-vehicle fleets remain physically feasible. This repeat adds no V50 nonzero certificate.

| Method | Own U | Qualified L | Signed gap |
|---|---:|---:|---:|
| M-B | 0.3723417755 | 0.357008334 | 0.01533344153 |
| ENS-C | 0.3723417755 | 0.358161762 | 0.01418001348 |
| P-GRB | 0.3917805586 | 0.3494508596 | 0.04232969893 |
| MB-D1 | 0.3723417755 | 0.357008334 | 0.01533344153 |

D1/P, M-B/P and ENS-C/P are WIN. D1/M-B, D1/ENS-C and M-B/ENS-C are TIE. D1 and M-B have identical qualified endpoints; ENS-C has a higher L, but its 0.0011534280 gap advantage is below the applicable 0.0014180013 materiality threshold. All windows remain open, so no certification-time ratio applies.

| Pair | dU | dL | dgap | dG | d(lambda*P) |
|---|---:|---:|---:|---:|---:|
| MB-D1/P-GRB | -0.0194387831 | +0.0075574743 | -0.0269962574 | -0.0259202356 | +0.0064814525 |
| M-B/P-GRB | -0.0194387831 | +0.0075574743 | -0.0269962574 | -0.0259202356 | +0.0064814525 |
| ENS-C/P-GRB | -0.0194387831 | +0.0087109024 | -0.0281496854 | -0.0259202356 | +0.0064814525 |
| MB-D1/M-B | +0.0000000000 | +0.0000000000 | +0.0000000000 | +0.0000000000 | +0.0000000000 |
| MB-D1/ENS-C | +0.0000000000 | -0.0011534280 | +0.0011534280 | +0.0000000000 | +0.0000000000 |
| M-B/ENS-C | +0.0000000000 | -0.0011534280 | +0.0011534280 | +0.0000000000 | +0.0000000000 |

The three integrated methods retain G=0.0501195842 and lambda*P=0.3222221913, identical to their Seed0 physical endpoints. Cold P-GRB has G=0.0760398198 and lambda*P=0.3157407388. Their improvement in G therefore outweighs a larger penalty term; this differs from Seed0, where both components favored the integrated endpoints. These are arithmetic endpoint decompositions and do not identify an internal search cause.

D1 is enabled but naturally unexposed again: one paid root proof is retained, the pair is incomplete, installation and expanded Optimize counts are zero. The original AM path records three atomic splits. The first two preserve infeasible right children, followed by adaptive_mass_score_reaches_tau. The not_exposed record occurs on L0.0.0.0 at 177.8644658 process seconds. Neither a missing installation nor these original splits is an engineering failure. The full-method comparison retains this observation. A feasible own fleet outside a terminal leaf interval does not by itself establish that a Start was submitted, accepted or installed into that restricted model. Those stages require their own call/model/scope records.

Each integrated method makes seven returned LP calls and one returned MIP call. H takes 34.2260–34.5153 seconds, the recorded LP partition 26.0560–103.1310 seconds and the MIP partition 3391.5920–3468.6970 seconds. This locates the dominant recorded work in the MIP request, alongside actual multi-model LP costs. It does not separate incumbent search from a proof tail or establish counterfactual D1 overhead.

| Method | T_produce | T_verify | T_total |
|---|---:|---:|---:|
| M-B | 3572.6027840107 | 85.3058211000 | 3657.9086051107 |
| ENS-C | 3570.6597372000 | 84.4460346000 | 3655.1057718000 |
| P-GRB | 3570.6722910000 | 930.1450991000 | 4500.8173901000 |
| MB-D1 | 3572.5641813731 | 85.1722841000 | 3657.7364654731 |

The final D1 producer includes its continuation wrapper birth and imports. Its necessary verification takes 85.1722841 seconds; the subsequent 175.4091488-second four-arm reconciliation is charged to group management and is not attached to D1 T_verify. The 120-second management amount is a reference/reservation, not a hard group timeout. All actual fees remain below the unchanged 100000-second total limit.

Cold P-GRB returned normally but the legacy R86 auditor asserted that the final physical U must not exceed the best earlier committed physical U. Independently verified sequence217 has F=0.391713327901773; the final returned fleet has F=0.39178055857928196. Both are feasible, and every one of 64 native bounds remains below both. The assertion orders two valid upper bounds rather than detecting an erroneous lower bound. The frozen contract uses the final fleet, so recovery retains final U=0.39178055857928196, L=0.34945085964584033 and certificate=false. The stronger historical witness is not substituted.

A strictly hash-scoped, read-only adapter replaces only this ordering assertion in memory with explicit physical and bound checks. Every other finalizer statement remains identical, and the complete inherited source/model/Seed/return audit passes. Separate recovery sidecars preserve every original P byte, the original failed audit/traceback and formal08 exit1 fee. Actual T_verify=930.1450991000165 and T_total=4500.817390100012 include the failure, investigation and complete waiting interval; T_produce=3570.6722909999953 is unchanged. Independent admission preceded the fresh birth of the original never-started fourth D1 position. No already-produced arm was rerun. The recovery chain is disclosed in [the explanation](recovery/group08/recovery_explanation.md) and its bound closeout.

The Seed0 C50 comparisons were also WIN/WIN/WIN/TIE/TIE/TIE. Cold P-GRB improves its final physical U and L at Seed1 while the integrated physical U stays unchanged; this does not create a new role or justify choosing the better Seed. Both fixed Seed blocks remain beside their Seed0 results.

## Final candidate decision and fixed paper reference

The prioritized rule independently yields BENCHMARK_MIXED_NO_NEW_PRIMARY_SELECTION. All 32 positions and 48 pairs are valid and evaluable; no proof-source rejection or severe regression is present. The six new D1/P comparisons give 5 WIN/1 MIXED, five new roles actually expose D1 including V35/V50, D1 preserves the two M-B nonzero certificates, and both fixed Seed1 primary comparisons are WIN. Nevertheless, only PB-B50-U supplies an exposed new material D1/M-B WIN or new certificate. The required count is at least two. This alone prevents the positive freeze exit. The decision does not use ENS dominance as an additional hidden gate.

On the six new roles, D1/M-B is 1 WIN/2 LOSS/1 MIXED/2 TIE. The PB-B35-B Seed1 WIN is a useful fixed-repeat observation but cannot replace a second new-role gain. Across all eight blocks, D1/P is 7 WIN/1 MIXED; D1/M-B and D1/ENS-C are each 2 WIN/2 LOSS/1 MIXED/3 TIE. These combined eight-block counts are descriptive and do not replace the registered six-problem denominator.

Retain frozen M-B as the one existing paper reference for the structured exact-method comparison. Its complete algorithm is already supported; it is WIN against cold P-GRB on all six new roles and both fixed repeats, obtains the same two new-role V20 nonzero certificates as D1, and captures the common gains without requiring the D1 breadth claim that failed here. ENS-C remains the implementation default and a full reported comparator. This reference recommendation is not an instance winner selector and does not claim M-B dominates ENS-C. M-B/ENS-C is 1 WIN/1 LOSS/4 TIE on new roles and 1 WIN/2 LOSS/5 TIE over all eight blocks. The PB-C35-U and PB-B35-B Seed1 losses remain explicit M-B limitations relative to ENS-C. Separately, historical R120 C2 Seed0 has severe D1/M-B LOSS (while M-B/P is WIN); its later Seed1 D1/M-B WIN does not erase the adverse Seed0 result.

The evidence supports completed finite benchmarking and open quality/bound improvements, with limited nonzero full-certification range. All new-role nonzero certificates occur at V20: P-GRB has one and each integrated method has two. No method obtains a new V35/V50 nonzero certificate, and no own-zero or source-reduced result is used to substitute for one. Both C50 D1-unexposed observations remain valid full-method results.

No new research problem is required to close this benchmark task. The batch ends without automatic extra inputs, Seeds, variants or algorithm changes. Any later mathematical research would need its own question and preregistration; these endpoint and cost observations do not establish a universal missing cut or an internal D1 branching mechanism. R121 remains COMPLETE / ADVANCE_FROZEN_D1_TO_PAPER_BENCHMARK as historical support, while this broader batch does not select a new primary. D0 remains an ablation and MB-PC remains stopped.

## Evidence, execution cost and claim limits

The canonical authorities are all eight current_core.json files, full 32/48 tables, proof_reliability, mechanism_account, own_fleets_and_objective_parts, Seed/source/scale layers, and the original call/model/epoch/cutoff/Seed/Start/return records. All 32 physical objectives and three clocks,48 exact typed pair records and the prioritized stage were actually recomputed by a different executor. The independent review is ACCEPT, covering all nine negative/mixed pairs, a complete V50 fleet and the actual exposed PB-B50-U D1 model4 (103428 rows/24522 columns), its base objective/types, all three D1 rows, outward endpoints/ObjCon and full Start/scope checks. No native Optimize was used for this review. The performed numerical checks are not a guarantee against every possible floating-point error.

The complete physically feasible fleets satisfy inventory, service direction/integrality, assigned-Q prefix/return loads and original time constraints. The open outcomes are not attributed to missing vehicles or incomplete physical solutions. Native MIP costs dominate the recorded large-role partitions; the evidence does not establish inventory/route assignment as a causal bottleneck or distinguish all search effort from proof effort. LP, H, installation, callbacks, closeout and post-seal verification remain separately visible, with no nested-time double counting. Actual certified-time ratios are reported only when both methods certify.

Observed outer fees are 75202.98446220002/100000 seconds, including every failed/recovery episode. Qualification uses 448.3212315000128/6000 seconds, below the3000-second soft plan; no soft-plan extension was needed. There are 50 fee-level observed/conservative starts plus5 distinct controllers,55 in total. Native component timers are nested. Read-only report/review/publication work has its own measured receipts and is not replaced by a human-time estimate.

The six problems are finite, non-IID and nonfactorial. The two station sources do not supply six cities; station overlaps remain recorded. Source, geography, stock, Q/T, weight totals and scale vary together, so their isolated causal effects are not estimated. Two Seeds do not estimate population probabilities. No best-of-Seed endpoint, across-instance winner dispatch or cross-round exact speedup is constructed. The algorithm/source identities, numerical policy, full denominators and adverse cases stay fixed. Workspace and storage measures support reliable execution and are not mathematical contributions.
