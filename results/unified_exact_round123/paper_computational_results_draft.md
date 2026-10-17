# Computational evidence for the frozen M-B paper reference

## Design, complete methods and measurement

The first unified paper panel (Round122) compares cold P-GRB with three frozen complete methods: the default ENS-C, the existing M-B reference, and the separately evaluated MB-D1 candidate. It contains six prospectively fixed new Seed0 problems and two fixed Seed1 repeats, totaling 32 mandatory positions and 48 directed comparisons. The eight blocks are not eight independent problems. Round123 accepts the completed outcome **COMPLETE / BENCHMARK_MIXED_NO_NEW_PRIMARY_SELECTION**: M-B remains the existing paper reference, ENS-C remains default, and the D1 selection exercise ends without a new promotion. D0 is an ablation rather than a reserve algorithm; MB-PC remains stopped.

The two sources are the existing safe CITI station table (443 original rows,442 eligible physical stations; SHA256 `9f9aad24e61d661971c24c6f5ec78a69081edf01ffc433563e52a70b2eaca2d0`) and CABI's frozen response/safe table (865 stations; response SHA256 `d4e664c3ecb8c580e95d39541555be9cf592666a515cb854a857fb1d117ff0b8`, safe-table SHA256 `d982051e5871c575ecdf9df538605401bd98341ae9b3b48112482eff80d42ffa`). The generation recipe and full schedule were committed before the once-only six-input generation. Original four-anchor/hash selection, ties, target fractions 0.44–0.56, three-decimal coordinates, six-decimal max-normalized weights, centroid depot, inventory total/sign correction and predeclared Q vectors were retained. No difficulty screening, salt/replicate redraw, new acquisition or H/LP/MIP filtering selected those new inputs. Recorded station overlaps remain relevant to interpretation.

All roles use lambda 0.15, pickup/drop 60/60 and Euclidean/1.5 travel. Source, size, stock, geometry, Q, T and total weights vary together. This finite design cannot isolate their causal effects; it is neither a factorial design, six independent cities nor an IID population sample. In particular lambda times total weight varies, so changes in objective scale are not solely a size effect.

| New Seed0 role | Source | V/M | Geometry / stock | Q | physical T | produce cap | sum weights | lambda sum weights |
|---|---|---|---|---|---|---|---|---|
| PB-C20-B | CITI | 20/2 | compact / balanced | 30,30 | 3600 | 900 | 7.288265 | 1.09323975 |
| PB-B20-S | CABI | 20/2 | regional / shortage | 20,40 | 7200 | 900 | 7.284024 | 1.0926036 |
| PB-C35-U | CITI | 35/3 | regional / surplus | 20,25,30 | 10800 | 2400 | 11.590113 | 1.73851695 |
| PB-B35-B | CABI | 35/3 | compact / balanced | 25,25,25 | 7200 | 2400 | 14.72 | 2.208 |
| PB-C50-S | CITI | 50/4 | compact / shortage | 30,30,30,30 | 10800 | 3600 | 20.216045 | 3.03240675 |
| PB-B50-U | CABI | 50/4 | regional / surplus | 20,25,35,40 | 18000 | 3600 | 22.597221 | 3.38958315 |

Every method pays for its own applicable startup H, models, LP/MIP calls, Starts, online checks, callbacks, native cleanup and producer sealing. The frozen PE and DLL and all 216 source bindings are common. Threads=mip_threads=1, PresolveAuto, Seed0 or the prospectively fixed Seed1, MIPGap=MIPGapAbs=0, FeasibilityTol/OptimalityTol1e-6 and IntFeasTol1e-5 are retained. The floating evidence/closure policy is 1e-7. H uses the unchanged Seed 20260626 and full 24+1 construction/descent/closure/exchange procedure regardless of Gurobi Seed. Native epigraph objective and own replayed physical U are distinct.

T_produce includes the complete online method and seal. Necessary post-seal verification has its own T_verify, and T_total is their sum. Cross-arm reconciliation is group cost; nested native Runtime is not added again. R122's producer caps were 900 seconds at V20, 2400 at V35 and 3600 at V50. Actual closed fees were 75202.98446220002 of 100000 outer seconds, including failures/recovery; qualification consumed 448.3212315000128 seconds. Fifty fee-level starts plus five distinct controllers were recorded. Engineering, review/publication and unknown human effort are not silently replaced by zero. Workspace/cleanup measures support execution and are not algorithmic improvements.

Comparisons retain the original certificate-first policy. A candidate-only qualified certificate wins; a control-only certificate is a severe loss. With both certified, the material production-time threshold is max(30 seconds,10% of the control time); a severe certified regression additionally requires at least twice the control time and 120 seconds excess. For two open endpoints, a_U=max(.001,.01|U_control|), a_gap=max(.001,.10|gap_control|). Material improvement without opposing deterioration is WIN, deterioration without opposing improvement is LOSS, opposing material effects are MIXED, and otherwise TIE. Severe open regression requires both U deterioration at least max(.001,.05|U_control|) and gap deterioration at least max(.005,.25|gap_control|). Missing necessary numeric evidence is UNEVALUABLE. Caps are censored windows, not final proof times; actual time ratios are reported only when both methods certify. Tiny signed gaps and every negative/mixed result remain visible.

## Complete 32-arm outcomes

The table gives each method's final own fleet objective U, qualified original-problem lower endpoint L and signed U-L. N means a clean nonzero numerical certificate; O means a qualified open result. No zero certificate or source-reduced result occurs in this R122 panel. The exact JSON authorities retain full precision and original proof categories. PB-B35-B Seed0 cold P uses the explicitly independent zero floor; its Seed1 native bound is the tiny positive 2.0271896642e-18, retained without changing its evidence category.

| Group / Seed | Role | Method | own U | qualified L | signed gap | Tier | T_produce | T_verify | T_total |
|---|---|---|---|---|---|---|---|---|---|
| 1 / 0 | PB-C20-B | P-GRB | 0.2246803118 | 0.1765783752 | 0.04810193667 | O | 872.58902 | 1.2301552 | 873.819175 |
| 1 / 0 | PB-C20-B | ENS-C | 0.2246803118 | 0.2246803118 | -1.110223025e-16 | N | 430.55759 | 3.2131804 | 433.770771 |
| 1 / 0 | PB-C20-B | M-B | 0.2246803118 | 0.2246803118 | 1.054711873e-15 | N | 395.859541 | 3.2497076 | 399.109249 |
| 1 / 0 | PB-C20-B | MB-D1 | 0.2246803118 | 0.2246803118 | 2.498001805e-16 | N | 665.068782 | 4.8507225 | 669.919504 |
| 2 / 0 | PB-B20-S | ENS-C | 0.8631523206 | 0.8631523206 | -2.220446049e-16 | N | 4.62243312 | 1.4472566 | 6.06968972 |
| 2 / 0 | PB-B20-S | M-B | 0.8631523206 | 0.8631523206 | -2.220446049e-16 | N | 2.6319677 | 1.5763652 | 4.2083329 |
| 2 / 0 | PB-B20-S | MB-D1 | 0.8631523206 | 0.8631523206 | -2.220446049e-16 | N | 2.6983887 | 2.1314255 | 4.8298142 |
| 2 / 0 | PB-B20-S | P-GRB | 0.8631523206 | 0.8631523206 | 1.110223025e-16 | N | 116.032776 | 1.0218656 | 117.054641 |
| 3 / 0 | PB-C35-U | M-B | 0.1696364022 | 0.08395185429 | 0.0856845479 | O | 2372.52643 | 8.951676 | 2381.47811 |
| 3 / 0 | PB-C35-U | MB-D1 | 0.1793004366 | 0.08353399353 | 0.09576644305 | O | 2370.6204 | 11.0386199 | 2381.65902 |
| 3 / 0 | PB-C35-U | P-GRB | 0.1747718876 | 0.05970290317 | 0.1150689844 | O | 2370.61617 | 1.0998746 | 2371.71604 |
| 3 / 0 | PB-C35-U | ENS-C | 0.1642374878 | 0.08157539377 | 0.08266209402 | O | 2370.59893 | 8.8968437 | 2379.49577 |
| 4 / 0 | PB-B35-B | MB-D1 | 0.2345814099 | 0.09200798362 | 0.1425734262 | O | 2372.44036 | 10.1910831 | 2382.63144 |
| 4 / 0 | PB-B35-B | P-GRB | 0.3055557782 | 0 | 0.3055557782 | O | 2370.55615 | 0.5180864 | 2371.07424 |
| 4 / 0 | PB-B35-B | ENS-C | 0.2465044704 | 0.132287968 | 0.1142165024 | O | 2370.55267 | 9.1507964 | 2379.70346 |
| 4 / 0 | PB-B35-B | M-B | 0.2465044704 | 0.1276343018 | 0.1188701686 | O | 2371.78616 | 8.1583865 | 2379.94455 |
| 5 / 0 | PB-C50-S | MB-D1 | 0.3723417755 | 0.3568747399 | 0.01546703556 | O | 3572.88123 | 40.0557249 | 3612.93696 |
| 5 / 0 | PB-C50-S | M-B | 0.3723417755 | 0.3568747399 | 0.01546703556 | O | 3570.59534 | 40.3517955 | 3610.94714 |
| 5 / 0 | PB-C50-S | ENS-C | 0.3723417755 | 0.3579807999 | 0.01436097562 | O | 3571.89539 | 40.0828359 | 3611.97823 |
| 5 / 0 | PB-C50-S | P-GRB | 0.4259500753 | 0.3492206958 | 0.07672937949 | O | 3583.02016 | 1.5724743 | 3584.59263 |
| 6 / 0 | PB-B50-U | P-GRB | 1.176955759 | 0.06837938241 | 1.108576376 | O | 3572.99105 | 1.3026014 | 3574.29365 |
| 6 / 0 | PB-B50-U | MB-D1 | 0.677298419 | 0.4712348696 | 0.2060635494 | O | 3570.56301 | 25.6511639 | 3596.21418 |
| 6 / 0 | PB-B50-U | M-B | 0.6974735096 | 0.4553454 | 0.2421281096 | O | 3571.86239 | 19.9168553 | 3591.77925 |
| 6 / 0 | PB-B50-U | ENS-C | 0.8325480152 | 0.4523603674 | 0.3801876478 | O | 3570.57309 | 19.7308828 | 3590.30397 |
| 7 / 1 | PB-B35-B | ENS-C | 0.2345814099 | 0.1146410114 | 0.1199403984 | O | 2372.97341 | 18.6435541 | 2391.61696 |
| 7 / 1 | PB-B35-B | P-GRB | 0.2797984344 | 2.027189664e-18 | 0.2797984344 | O | 2370.51169 | 1.9798215 | 2372.49151 |
| 7 / 1 | PB-B35-B | MB-D1 | 0.2345814099 | 0.138322042 | 0.09625936783 | O | 2370.61684 | 22.4221823 | 2393.03902 |
| 7 / 1 | PB-B35-B | M-B | 0.2465044704 | 0.0982245518 | 0.1482799186 | O | 2370.48956 | 18.640514 | 2389.13008 |
| 8 / 1 | PB-C50-S | M-B | 0.3723417755 | 0.357008334 | 0.01533344153 | O | 3572.60278 | 85.3058211 | 3657.90861 |
| 8 / 1 | PB-C50-S | ENS-C | 0.3723417755 | 0.358161762 | 0.01418001348 | O | 3570.65974 | 84.4460346 | 3655.10577 |
| 8 / 1 | PB-C50-S | P-GRB | 0.3917805586 | 0.3494508596 | 0.04232969893 | O | 3570.67229 | 930.145099 | 4500.81739 |
| 8 / 1 | PB-C50-S | MB-D1 | 0.3723417755 | 0.357008334 | 0.01533344153 | O | 3572.56418 | 85.1722841 | 3657.73647 |

All new-panel nonzero complete certificates occur on the two V20 problems. PB-C20-B has a common physical value 0.22468031182347922: ENS-C, M-B and D1 certify while cold P remains open. M-B and ENS-C producer times are395.8595 and430.5576 seconds; D1 takes665.0688, losing both incremental certified-time comparisons. On PB-B20-S all four certify 0.8631523206. Cold P takes116.0328 seconds and each integrated method takes under 5 seconds; the differences among integrated methods are below the fixed 30-second materiality floor. No V35 or V50 arm in the new Seed0 panel or fixed Seed1 layer certifies. Certificates on other historical instances are not discarded, but do not become certificates for this panel.

## All 48 comparisons, including every adverse or mixed outcome

| Group / Seed | Role | Pair | Classification | Severe |
|---|---|---|---|---|
| 1 / 0 | PB-C20-B | MB-D1/P-GRB | WIN | False |
| 1 / 0 | PB-C20-B | M-B/P-GRB | WIN | False |
| 1 / 0 | PB-C20-B | ENS-C/P-GRB | WIN | False |
| 1 / 0 | PB-C20-B | MB-D1/M-B | LOSS | False |
| 1 / 0 | PB-C20-B | MB-D1/ENS-C | LOSS | False |
| 1 / 0 | PB-C20-B | M-B/ENS-C | TIE | False |
| 2 / 0 | PB-B20-S | MB-D1/P-GRB | WIN | False |
| 2 / 0 | PB-B20-S | M-B/P-GRB | WIN | False |
| 2 / 0 | PB-B20-S | ENS-C/P-GRB | WIN | False |
| 2 / 0 | PB-B20-S | MB-D1/M-B | TIE | False |
| 2 / 0 | PB-B20-S | MB-D1/ENS-C | TIE | False |
| 2 / 0 | PB-B20-S | M-B/ENS-C | TIE | False |
| 3 / 0 | PB-C35-U | MB-D1/P-GRB | MIXED | False |
| 3 / 0 | PB-C35-U | M-B/P-GRB | WIN | False |
| 3 / 0 | PB-C35-U | ENS-C/P-GRB | WIN | False |
| 3 / 0 | PB-C35-U | MB-D1/M-B | LOSS | False |
| 3 / 0 | PB-C35-U | MB-D1/ENS-C | LOSS | False |
| 3 / 0 | PB-C35-U | M-B/ENS-C | LOSS | False |
| 4 / 0 | PB-B35-B | MB-D1/P-GRB | WIN | False |
| 4 / 0 | PB-B35-B | M-B/P-GRB | WIN | False |
| 4 / 0 | PB-B35-B | ENS-C/P-GRB | WIN | False |
| 4 / 0 | PB-B35-B | MB-D1/M-B | MIXED | False |
| 4 / 0 | PB-B35-B | MB-D1/ENS-C | MIXED | False |
| 4 / 0 | PB-B35-B | M-B/ENS-C | TIE | False |
| 5 / 0 | PB-C50-S | MB-D1/P-GRB | WIN | False |
| 5 / 0 | PB-C50-S | M-B/P-GRB | WIN | False |
| 5 / 0 | PB-C50-S | ENS-C/P-GRB | WIN | False |
| 5 / 0 | PB-C50-S | MB-D1/M-B | TIE | False |
| 5 / 0 | PB-C50-S | MB-D1/ENS-C | TIE | False |
| 5 / 0 | PB-C50-S | M-B/ENS-C | TIE | False |
| 6 / 0 | PB-B50-U | MB-D1/P-GRB | WIN | False |
| 6 / 0 | PB-B50-U | M-B/P-GRB | WIN | False |
| 6 / 0 | PB-B50-U | ENS-C/P-GRB | WIN | False |
| 6 / 0 | PB-B50-U | MB-D1/M-B | WIN | False |
| 6 / 0 | PB-B50-U | MB-D1/ENS-C | WIN | False |
| 6 / 0 | PB-B50-U | M-B/ENS-C | WIN | False |
| 7 / 1 | PB-B35-B | MB-D1/P-GRB | WIN | False |
| 7 / 1 | PB-B35-B | M-B/P-GRB | WIN | False |
| 7 / 1 | PB-B35-B | ENS-C/P-GRB | WIN | False |
| 7 / 1 | PB-B35-B | MB-D1/M-B | WIN | False |
| 7 / 1 | PB-B35-B | MB-D1/ENS-C | WIN | False |
| 7 / 1 | PB-B35-B | M-B/ENS-C | LOSS | False |
| 8 / 1 | PB-C50-S | MB-D1/P-GRB | WIN | False |
| 8 / 1 | PB-C50-S | M-B/P-GRB | WIN | False |
| 8 / 1 | PB-C50-S | ENS-C/P-GRB | WIN | False |
| 8 / 1 | PB-C50-S | MB-D1/M-B | TIE | False |
| 8 / 1 | PB-C50-S | MB-D1/ENS-C | TIE | False |
| 8 / 1 | PB-C50-S | M-B/ENS-C | TIE | False |

On the six new Seed0 roles, D1/P has 5 WIN and 1 MIXED, while M-B/P and ENS-C/P each have 6 WIN. D1/M-B and D1/ENS-C each have 1 WIN, 2 LOSS, 1 MIXED and 2 TIE. M-B/ENS-C has 1 WIN, 1 LOSS and 4 TIE. The retained reference therefore captures common finite-window gains over cold P, while the ENS comparison identifies genuine M-B limitations. M-B is not claimed to dominate ENS-C instance by instance.

All nine LOSS/MIXED observations are explicit above. PB-C35-U is open for all methods: D1/P is MIXED because a better lower endpoint and gap accompany a worse physical U, and D1 loses to both M-B and ENS-C. M-B also loses to ENS-C on this role. PB-B35-B Seed0 gives a different tradeoff: D1 has a better U than M-B and ENS-C but a sufficiently weaker bound/larger gap to make both comparisons MIXED. PB-C20-B supplies the two D1 certified-time losses. The ninth adverse comparison is M-B/ENS-C on PB-B35-B Seed1. None of these R122 pairs is severe; that does not erase their directions or tradeoffs.

At PB-B50-U, D1's U=.6772984190 and L=.4712348696 improve on M-B's.6974735096/.4553454000 and ENS-C's.8325480152/.4523603674; all remain open. This is the only exposed new role with a material D1/M-B WIN or a certificate absent from M-B. Five new roles expose D1, including V35/V50, but the fixed promotion condition requires at least two such incremental roles. The condition is not met and is not lowered after seeing results.

PB-C50-S illustrates common integrated-method gains without D1 exposure. At Seed0, all three integrated methods have U=.3723417754990474; M-B/D1 L=.35687473994133595 and ENS-C L=.3579807998830059, while P has U=.4259500752940563 and L=.3492206958008561. D1 naturally lacks a complete paid root pair and installs no selector; the original three atomic splits proceed. Its unexposed outcome stays in full-method comparisons. It is neither an engineering failure nor evidence that a conditional formulation changed this search. The final true Gini=.050119584194518584 lies in the sibling of the target-MIP leaf, explaining why an otherwise valid global fleet need not furnish that leaf an exact-g Start.

## Source and Seed layers

| Seed | Source | arms | distinct roles in layer | nonzero certified arms | open arms |
|---|---|---|---|---|---|
| 0 | CITI | 12 | 3 | 3 | 9 |
| 0 | CABI | 12 | 3 | 4 | 8 |
| 1 | CITI | 4 | 1 | 0 | 4 |
| 1 | CABI | 4 | 1 | 0 | 4 |

The two fixed Seed1 repeats remain a separate sensitivity layer. PB-B35-B changes D1/M-B and D1/ENS-C from MIXED to WIN, and M-B/ENS-C from TIE to LOSS; every method remains open. PB-C50-S retains WIN for the three integrated/P pairs and TIE for their mutual comparisons; all remain open and D1 is unexposed again. These repetitions neither increase the new-problem denominator nor substitute a preferred Seed1 WIN for a missing second incremental Seed0 role. Two Seeds do not estimate a population probability.

The historical adverse evidence remains relevant. R120 C2 Seed0 had a severe D1/M-B loss and an ordinary D1/P loss despite M-B/P winning; its R121 Seed1 D1 WIN does not erase those results. F2 D0/M-B changes from Seed0 WIN to Seed1 LOSS, so D0 is not a fallback selection. R121's three new problems provided D1/P 3 WIN and D1/M-B TIE/WIN/TIE, with all three open; Q50 was naturally unexposed. R121's advancement into paper benchmarking remains its historical result, while the broader R122 benchmark does not select a new primary.

## Objective, proof and clock interpretation

For any comparable open pair, d(gap)=dU-dL, and dU=dG+d(lambda P). These are arithmetic endpoint identities, not percentages of an internal cause. For C50 Seed0 the common integrated U decomposes into G=.0501195842 and lambda P=.3222221913. In the Seed1 comparison with cold P, the integrated fleet has a better Gini but a larger penalty term; its net objective is still lower. At PB-B50-U both physical components favor D1 over M-B, while the lower endpoint also improves. Such observations locate primal and bound changes but do not establish native selector fixing, a particular branch event, a universal missing cut, or that a primal plateau is optimal.

R122 group08 cold P retained its original final U=.39178055857928196 although an earlier independently replayed journal fleet had F=.391713327901773. Both fleets are legal and all 64 native bounds lie below both. The legacy verification assertion ordered these two upper bounds and failed; it was not a lower-bound counterexample. A receipt-scoped read-only recovery preserved the final-fleet endpoint and every original producer byte. Original T_produce=3570.6722909999953, T_verify=930.1450991000165 and T_total=4500.817390100012 include the failed audit, investigation and full waiting interval. No producer was rerun and no historical best replaced the formal endpoint. Round123 generalizes only that post-seal semantic guard and tests it against the saved case and contradictory-bound fixtures; production mathematics and endpoint selection remain frozen.

The actual two R122 V35 saved D1 matrices also satisfy a stronger offline redundancy boundary: nonnegative penalty gives f>=g, and their actual serialized/native lower-link endpoints dominate the conditional objective-row endpoints over h in[0,1]. Binary h can be reselected for every original-variable model point. The paper_methods_draft.md proof and exact-fraction receipts distinguish this projection equality from R120's original extended-space nonredundancy. Representation can still affect solver search; neither the local theorem nor two old repaired h witnesses predicts time invariance or invalidates every D1 setting. No new D1 mechanism, conditional activation or selection task follows.

## A separate finite long-window study on one known V50 role

Round123 asks whether the frozen methods can complete a nonzero original-problem numerical certificate on PB-C50-S within one longer, predeclared window. This is a deliberately selected known role, chosen for strict positive-objective eligibility, a previously tight but unclosed bound, and actual multiple-leaf obligations. It is not an additional independent problem or a retry of a failed R122 producer. The input SHA256 is `3e17bd07ae0abbfebfd8264540e6f5bd737a0d4506c4b6e96950936153db9992`; V/M=50/4, Q=[30,30,30,30], physical T 10800 and pickup/drop 60/60 remain fixed. Its service totals 495 versus 562 imply a shortage 67. The explanatory exact-decimal lower bounds 0.24814831875 and 0.26064825 establish positivity; they are weaker than R122's qualified bounds and are not inserted into the production models.

The preregistered order is cold P-GRB, M-B, ENS-C, all Seed0 and each independently paying a fresh 18000-second producer window. No old route, bound, cutoff, basis, tree or cache is loaded. The native time-limit argument 17994, process cap 18000, original reserve 30 and single deadline are checked separately from physical T 10800. Changing the total cap can change the complete search path, so the new 3600-second slice is not assumed to reproduce R122 second by second. Only this three-arm group supports the new same-window comparisons; different old/new caps are displayed without a cross-round exact speedup.

| Method | own final U | qualified L | signed gap | nonzero cert | T_produce | T_verify | T_total |
|---|---|---|---|---|---|---|---|
| P-GRB | 0.377641708550208 | 0.3503779330408163 | 0.02726377550939169 | False | 17971.7113 | 1.9661194 | 17973.67742 |
| M-B | 0.3723417754990474 | 0.3580114855518426 | 0.01433028994720481 | False | 17970.57258 | 40.964555 | 18011.53713 |
| ENS-C | 0.3723417754990474 | 0.3589436661677159 | 0.01339810933133145 | False | 17970.87514 | 58.2420274 | 18029.11717 |

| Pair | Class | Severe | dU | dL | d(gap) | certified time ratio |
|---|---|---|---|---|---|---|
| M-B/P-GRB | WIN | False | -0.005299933051 | 0.007633552511 | -0.01293348556 | unknown |
| ENS-C/P-GRB | WIN | False | -0.005299933051 | 0.008565733127 | -0.01386566618 | unknown |
| M-B/ENS-C | TIE | False | 0 | -0.0009321806159 | 0.0009321806159 | unknown |

The complete three-method evidence yields **FINITE_LONG_WINDOW_PROOF_LIMIT_RECORDED**. All three methods return ordinary qualified open outcomes within their independent windows. The label does not imply that M-B is faster than a certified reference, works on every V50 input, or replaces ENS-C as default. Every paired outcome, including any LOSS, MIXED or UNEVALUABLE result, remains in the table. An open cap is not time-to-optimal.

The final fleet defines the main endpoint. The separate historical-minimum table in proof_limit_report.md retains every lower legal observed F, without selecting a retrospective best-of-observations endpoint. Existing journal records alone supply the five requested checkpoints; absent exact observations use the last prior sourced legal fleet and qualified bound, or unknown. Raw process times and conservative arm-origin availability upper times are both retained under observation_clock_contract.json. Each early finished run has one actual endpoint and certificate availability, with later requested points explicitly uncomputed. The complete cover, own fleet/leaf compatibility and unresolved obligations are reported in proof_limit_report.md and the typed current core.

The ENS-C observation-clock conversion fails the prospectively fixed 1-second consistency test. Its four pre-end checkpoint entries remain unknown. In ENS-C the recorded origin spread is 1.5845544376352336 seconds and wall-versus-producer-QPC duration difference is -1.5585018387646414 seconds; all raw records and times are retained. Final sealed U/L and QPC producer/verification clocks are qualified separately. The seal-time upper bound for its early startup record is deliberately loose and does not imply that H first formed at sealing. No clock-correction cause is invented and no threshold is enlarged to recover a favorable trajectory.

The additional physical, pair, checkpoint, coverage and claim review and actual public recovery have separate receipts. Their completed scope is stated in final_report.md; the formal core by itself does not attest publication or third-party replication. No extra Seed, input, mechanism, group or extension follows this finite result.

## Evidence boundaries and reproducibility

The R122 tables here are inherited from the exact pinned public research head `f3363d9ddede2725496e4a3e0466bbf4d1cec089`, with its scientific commit `9ed88cf9da87c3ceb7aebc43694f865eacbc86a7`, original own-fleet/proof/call/clock evidence and completed extra review. Round123 verifies their finite table identities and uses compact necessary references; it does not claim to repeat the entire 32-arm native campaign. All 32/48 full-precision source hashes and the nine negative/mixed records are indexed in paper_table_sources.json. The new experiment, its own paid costs and its own raw/proof evidence remain separately identified.

The evidence supports this defined static objective, exact serialized instances, finite windows and the stated floating numerical policy. It does not verify operational optimality across cities, rental/return service outcomes, stable certification of all V50 problems, eventual convergence within a predicted additional time, or a universal performance probability. Unfinished literature positioning is not replaced by a novelty claim. The finite study ends regardless of certificate success; further mathematics or a broader experiment would require a separate justified question and plan.
