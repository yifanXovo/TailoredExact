# `moderate_seed3301` root-cause classification

## Conclusion

The supported classification is **mixed mechanism (class 7), dominated by the
formulation-strength/throughput trade-off (class 6) and simplex work per node
(class 4)**.  F0 has a real, unusually wide depot-cycle circulation face, but
that is not a sufficient performance explanation: F1 removes every return-flow
column and F2 adds valid lower links and tighter upper links, yet both are worse
than F0 at 300 seconds.  F3 is the only normalized arm that recovers the target.
Its additional start coupling changes the fractional geometry and solver path,
cuts simplex work per node, and increases useful tree throughput.

Thus the causal statement is deliberately narrower than “circulation caused
the regression.”  Circulation is a proved structural defect and a contributor;
**circulation removal alone failed in F1, and the additional F2 normalization
also failed to recover the regression.  F3 helped because of start coupling and
the resulting throughput, not merely because return flow was deleted.**
Native-cut changes are a secondary mediator, and Gini queue delay remains an
amplifier rather than a solved mechanism.  Raw model dimension by itself is not
the cause.

At the conditional 3,600-second horizon, F3 ended at lower bound
`0.047358383204777726`, versus `0.04645929906778639` for F0 and
`0.04096078249212643` for plain CPLEX.  F3's independently verified-UB project
gap was 3.650206%, versus 5.479377% for F0 and 24.328100% for plain CPLEX.
All three were valid positive-gap time-limit rows, not strict certificates.

## Gap conventions and evidence scope

This note recomputes both gap conventions from the full-precision raw values:

\[
g_{\max 1}=\frac{\max(0,U-L)}{\max(1,|U|)},\qquad
g_{\mathrm{project}}=\frac{\max(0,U-L)}{|U|}.
\]

The checkpoint and time-to-threshold traces use `g_max1`; the serialized
top-level `gap` and `verified_incumbent_project_relative_gap` use the project
denominator.  They must not be conflated.  Here the Tailored verified upper
bound is `0.04915255266474515`, so `g_max1` is numerically the absolute
residual, whereas the project percentage is about 20.34 times larger.  For
example, F3 at 3,600 seconds has residual and `g_max1`
`0.0017941694599674235` (0.179417%), but project gap 3.650206%.

All fresh Tailored rows used the same frozen executable, one thread, presolve,
traditional search, parent-copy child estimates, full inherited rows, deferred
child rows, and no native MIP start.  Only the flow arm changes in Stage 1.
Stage 2--4 are fresh continuous solves at their stated horizons, not restarts
from earlier rows.  The global callback trace retains full-precision root and
final bound observations; intermediate CPLEX log values are rounded, so no
unobserved crossing time is inferred.

The Tailored endpoints have status 108 (`time limit exceeded, no integer
solution`) and native solution count zero.  Their upper bound is the separately
verified original-problem incumbent, so the reported residuals are
verified-UB-to-native-LB gaps, not an invented native incumbent gap.  Plain
CPLEX has status 107 (`time limit exceeded`) and a native incumbent.  Every
endpoint is classified `time_limit_valid_bound` with
`strict_certified_original_problem=false`.

## Mathematical and direct degeneracy evidence

The proof artifact establishes the canonical lift for an integral route
`0,v1,...,vs,0`: the used flow values are `s,s-1,...,1,0`.  In F0, adding the
same nonnegative constant to every used arc preserves every station balance
and the depot net balance until an upper link binds.  F1 deletes all return
columns and fixes the canonical return flow to zero; for a fixed integral
route this removes exactly that depot-cycle coordinate.  F2 adds the valid
non-return lower links and tighter internal upper links.  F3 adds linear
coupling between each departure flow and the visit count; its lower start row
can restrict fractional departure patterns.  The proved projection order is
`F3 subset F2 subset F1 -> F0`, while every original integral route retains a
canonical lift.  F1 does not claim to remove every cycle on a fractional
multi-arc support.

The diagnostic-only F0 solves fix the original objective to the same root
objective face (optimum `0.029559107138148355`, face tolerance `1e-9`) and vary
only auxiliary flow:

| Quantity on the fixed original-objective face | Minimum | Maximum | Range |
|---|---:|---:|---:|
| Total return-to-depot flow | 0 | 52.14171823360466 | 52.14171823360466 |
| Total connectivity flow | 7.858281766397566 | 429.21499139586626 | 421.3567096294687 |

The max-return solution uses 16 positive return variables, with maximum value
12.16.  The max-total-flow solution still has return flow
29.21499139586624.  The original-objective optimizer happened to select zero
return flow, so the evidence is not that the production basis necessarily
used positive return flow; it is that a large positive-return face exists at
the identical original objective.  All 1,260 F0 connectivity columns had zero
reduced cost in that original-objective diagnostic basis.  The extreme-face
bases reached kappa values up to about `5.68e8`, consistent with a highly
degenerate and numerically awkward auxiliary face.

This return-flow freedom is unusually concentrated on the regression target.
The matched return-flow ranges are only about `9.49e-6` for
`tight_T_seed3101` and `1.35e-6` for `high_imbalance_seed3202`, although both
controls retain nontrivial total-flow ranges.  That contrast makes depot-cycle
circulation a relevant contributor for `moderate_seed3301`, but the formulation
ablation below prevents treating it as the sole finite-time cause.

## Stage 1: causal flow ablation

All arms share verified UB `0.04915255266474515`.

| Arm | Native LB | `g_max1` | Project gap | Nodes / open | Simplex/node | Nodes/s | Max sibling delay (s) | Max tree MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| off | 0.045434434834247 | 0.371812% | 7.564445% | 3,758 / 1,355 | 294.52 | 12.77 | 238.91 | 153.94 |
| F0 | 0.044988206325189 | 0.416435% | 8.472289% | 2,172 / 1,033 | 295.49 | 7.38 | 165.92 | 249.51 |
| F1 | 0.044599360639413 | 0.455319% | 9.263389% | 1,496 / 664 | 607.48 | 5.09 | 233.58 | 75.18 |
| F2 | 0.044651795925787 | 0.450076% | 9.156710% | 1,549 / 628 | 676.56 | 5.27 | 181.43 | 57.80 |
| F3 | 0.045430535435162 | 0.372202% | 7.572378% | 2,512 / 1,018 | 221.22 | 8.54 | 206.24 | 236.69 |

F0 reproduces the Round 20 regression: at 300 seconds its LB is
`0.000446228509058` below no-flow.  F3 recovers the no-flow endpoint to within
`3.899399085e-6`, while improving F0 by `0.000442329109974`.  By contrast:

* F1 removes 60 return columns but lowers the LB by `0.000388845685775`
  relative to F0, doubles simplex work per node, and reduces throughput by
  about 31%.
* F2 gives the strongest post-native-cut root value but remains below F0 at
  the finite horizon.  Its 676.56 simplex iterations per node are 129% above
  F0.  Thus lower links and tighter upper bounds strengthen the root without
  buying useful bound-per-wall-time convergence here.
* F3 uses the same 1,200 flow columns as F2 and adds only the 120 start-coupling
  rows.  Relative to F2 it raises the final LB by `0.000778739509376`, cuts
  simplex/node by 67%, and raises nodes/s by 62%.  Relative to F0 it cuts
  simplex/node by 25% and raises nodes/s by 16%.

The root/model facts explain why “strongest root” and “best finite solve” are
different:

| Arm | Full rows / cols / nz | Reduced rows / cols / nz | Post-cut root LB | Root LP / completion (s) | First Gini (s) | Cover / flow / MIR / implied cuts |
|---|---:|---:|---:|---:|---:|---:|
| off | 10,602 / 2,118 / 61,976 | 9,358 / 2,026 / 55,567 | 0.0347290398 | 0.16 / 2.53 | 2.55 | 31 / 33 / 40 / 664 |
| F0 | 11,925 / 3,378 / 67,136 | 10,695 / 3,283 / 60,749 | 0.0345379801 | 0.28 / 6.52 | 6.54 | 15 / 85 / 27 / 463 |
| F1 | 11,865 / 3,318 / 66,896 | 10,635 / 3,223 / 60,509 | 0.0344641919 | 0.33 / 5.58 | 5.60 | 3 / 52 / 18 / 458 |
| F2 | 13,065 / 3,318 / 69,296 | 11,835 / 3,223 / 62,963 | 0.0347725614 | 0.45 / 6.27 | 6.27 | 10 / 28 / 40 / 232 |
| F3 | 13,185 / 3,318 / 71,876 | 11,889 / 3,223 / 64,100 | 0.0347230454 | 0.47 / 5.06 | 5.08 | 18 / 19 / 18 / 342 |

The logged uncut root value rounds to 0.0328 for every arm.  The post-cut
values need not follow the proved formulation dominance because CPLEX
generates different native cut sets for different formulations.  F2's best
post-cut root and worst simplex/node result expose the core
strength/throughput trade-off.  F3 is larger than F0 in rows and nonzeros and
has only 60 fewer columns, yet is faster in the tree; raw dimension is
therefore not a sufficient explanation.

## Stage 2--4 convergence and search mechanics

The multi-horizon endpoints are:

| Nominal horizon | Arm | Native LB | Verified UB | `g_max1` | Project gap | Native status / class |
|---:|---|---:|---:|---:|---:|---|
| 900 | F0 | 0.045828658715859 | 0.049152552664745 | 0.332389% | 6.762404% | 108 / valid time-limit bound |
| 900 | F3 | 0.046443635802410 | 0.049152552664745 | 0.270892% | 5.511243% | 108 / valid time-limit bound |
| 900 | plain | 0.040568396762712 | 0.053603119966380 | 1.303472% | 24.317098% | 107 / valid time-limit bound |
| 1,800 | F0 | 0.046152142701887 | 0.049152552664745 | 0.300041% | 6.104281% | 108 / valid time-limit bound |
| 1,800 | F3 | 0.046936162793439 | 0.049152552664745 | 0.221639% | 4.509206% | 108 / valid time-limit bound |
| 1,800 | plain | 0.040714606912687 | 0.058536947520404 | 1.782234% | 30.446310% | 107 / valid time-limit bound |
| 3,600 | F0 | 0.046459299067786 | 0.049152552664745 | 0.269325% | 5.479377% | 108 / valid time-limit bound |
| 3,600 | F3 | 0.047358383204778 | 0.049152552664745 | 0.179417% | 3.650206% | 108 / valid time-limit bound |
| 3,600 | plain | 0.040960782492126 | 0.054129448918446 | 1.316867% | 24.328100% | 107 / valid time-limit bound |

The fresh plain runs have different independently verified incumbents, so
their project gaps across horizons are not a single monotone trajectory.  The
native LB trend is the clean comparison.  F3's LB advantage over F0 grows from
`0.0004423291` at 300 seconds to `0.0006149771` at 900,
`0.0007840201` at 1,800, and `0.0008990841` at 3,600.  The rounded Stage 4 log
shows F3 had already exceeded F0's final one-hour LB by roughly 1,100 seconds;
its advantage is not a last-checkpoint accident.  Both F0 and F3 record their
last full-precision LB observation at the final native callback (about 3,550
seconds), so neither is extrapolated to gap zero.

The matched tree mechanics are:

| Horizon | Arm | Nodes / open | Total simplex | Simplex/node | Nodes/s | Gini / ordinary branches | Max sibling delay (s) | Max tree MB |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 300 | F0 | 2,172 / 1,033 | 641,800 | 295.49 | 7.38 | 130 / 1,473 | 165.92 | 249.51 |
| 300 | F3 | 2,512 / 1,018 | 555,702 | 221.22 | 8.54 | 146 / 1,619 | 206.24 | 236.69 |
| 900 | F0 | 5,803 / 2,775 | 1,976,142 | 340.54 | 6.58 | 150 / 4,140 | 606.97 | 663.81 |
| 900 | F3 | 7,311 / 3,013 | 1,276,691 | 174.63 | 8.29 | 165 / 4,997 | 626.89 | 811.43 |
| 1,800 | F0 | 10,541 / 5,129 | 3,681,519 | 349.26 | 5.95 | 151 / 7,685 | 605.48 | 1,327.31 |
| 1,800 | F3 | 12,316 / 4,964 | 1,975,061 | 160.36 | 6.96 | 173 / 8,467 | 1,381.29 | 1,351.30 |
| 3,600 | F0 | 18,224 / 8,517 | 6,235,304 | 342.15 | 5.10 | 161 / 13,212 | 2,576.04 | 2,270.19 |
| 3,600 | F3 | 19,167 / 7,185 | 2,815,883 | 146.91 | 5.37 | 177 / 12,999 | 2,236.06 | 1,938.18 |

At one hour F3 performs 55% fewer simplex iterations and 57% fewer iterations
per node, processes 5% more nodes, leaves 16% fewer open nodes, and uses 15%
less peak tree memory.  Its project gap is 1.829 percentage points smaller.
The native cut totals are also lower: F0 records cover/flow/MIR/implied counts
`137/175/42/2685`, while F3 records `75/43/43/1523`.  F3's better LB therefore
does not come from generating more cuts; the explicit start rows alter the
relaxation, bases, cut mix, and downstream node LPs.

Gini queue interaction is not eliminated.  F3 reaches the first Gini branch
earlier (about 5.1 versus 6.4 seconds) and reaches more Gini branches at every
horizon, but its maximum sibling delay is slightly worse at 300 and 900
seconds and much worse at 1,800 seconds before becoming better at one hour.
F3 improves the bound despite those earlier delay regressions.  Queue delay is
therefore a remaining amplifier, not the primary explanation of recovery.

Plain CPLEX at one hour processes 274,400 nodes, leaves 131,610 open, and peaks
at 10,229.86 MB of native tree memory, yet its LB remains far below both
Tailored arms.  Its final API result does not retain a simplex counter; the
last displayed CPLEX log counter is 11,441,540 iterations at node 274,100
(about 41.7 per displayed node), so it is reported as log evidence rather than
an exact final API metric.  Plain's high node count is not comparable evidence
of a stronger search.

## Mechanism-by-mechanism classification

| Requested mechanism | Finding | Role |
|---|---|---|
| 1. Depot-cycle circulation degeneracy | Proved, all F0 flow columns have zero reduced cost on the diagnostic objective basis, and the same-objective return range is 52.14.  F1 deletion nevertheless worsens the solve. | Real contributor; rejected as a sole cause. |
| 2. Excess continuous-variable dimension after normalization | F1/F2/F3 all use 1,200 flow columns.  F1 and F2 fail, while the larger-row F3 wins. | Not primary; dimension alone cannot explain the ordering. |
| 3. Weaker or different native cuts | Cut families and counts change markedly; post-cut root values are not monotone with finite-time performance.  F3 wins with fewer flow and implied-bound cuts. | Secondary mediator, not a “more cuts is better” effect. |
| 4. Higher simplex work per node | F1/F2 roughly double F0's work; F3 cuts work below F0 at every horizon and by 57% at one hour. | Major supported mechanism. |
| 5. Gini queue interaction | Long sibling delays persist and are sometimes worse under F3, although F3 reaches more Gini branches and eventually has fewer open nodes. | Residual amplifier, not the recovery cause. |
| 6. Formulation strength/throughput trade-off | F2 has the best post-cut root but poor bound per wall time; F3 gives a slightly lower post-cut root and much better tree throughput/LB. | Dominant supported mechanism. |
| 7. Mixed mechanism | Geometry, cut path, simplex work, and queue/memory interact. | Overall classification. |

## Implication

For `moderate_seed3301`, F3 removes the genuine Round 20 F0 regression at the
300-second causal horizon and maintains an increasing LB advantage through
900, 1,800, and 3,600 seconds.  It beats plain CPLEX decisively on valid native
LB convergence.  It still does not reach strict closure, and no time to gap
zero is inferred.

This target recovery alone is not a basis for instance-dependent activation or
default promotion.  In the 900-second eight-instance matrix F3 improves F0 on
`moderate_seed3301`, `moderate_seed3302`, and `high_imbalance_seed3201`, ties
the two V12 controls, but regresses on `high_imbalance_seed3202`,
`tight_T_seed3101`, and `tight_T_seed3102`; the selected 1,800-second controls
remain mixed.  The defensible Round 21 conclusion is therefore: F3 is the
causally supported normalized variant for this regression target, but root
flow should remain optional pending broader held-out validation and further
work on formulation/queue throughput.

Source artifacts are `root_connectivity_flow_normalization_proof.md`,
`flow_degeneracy_diagnostics.csv`, `flow_model_size_and_presolve.csv`,
`flow_variant_300s_ablation.csv`, `matched_900s_comparison.csv`,
`selected_1800s_convergence.csv`, the Stage 4 raw JSON files, and their
complete logs and traces.
