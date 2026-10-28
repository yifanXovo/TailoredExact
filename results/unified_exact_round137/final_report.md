# Round137 GI-TBC scientific stage report

All 120 registered positions are retained. This report closes the specified finite consolidation study; actual public recovery, Draft PR and final delivery have separate receipts. Prior R132/R134/R135 observations retain their original versions, proof policies and denominators.

## Accepted method and scope

GI-TBC means **Gini-interval tailored branch-and-cut**. The accepted configuration remains ms2 (historical S2), complete own H, M-B/VD-P shared states, uniform pair-only support, existing interval controller and R134 proof policy, AP off. The compatibility bare-CLI ENS-C identity remains. Explicit research-only single-group controls and actual post-preset AM threshold/readback are the minimal implementation changes; no instance/size/time dispatch is introduced. The zero-Optimize reference fixture matches the accepted R135 default-off matrix, while per-call current model contracts qualify the new runs. Current timings retain the actual newly instrumented PE/source identity.

| Item | Actual value |
|---|---|
| Production source commit | 779713ad9a0b01edc538ecb64df9438739127be3 |
| PE SHA256 | d6fd9e6687ac7d4377e2d7fd683d59bd3354d7dfb3a9e5b3723d0fe62b6c7fbd |
| DLL SHA256 | 9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88 |
| AM / depth / width | .08 /8 /1e-4 |
| H / Gurobi Seeds | 20260626 /0 main,1 limited repeat |
| Threads / affinity | 1 /mask4 |
| Physical conventions | Empty departure, loaded return/unloading, unique nonzero one-way service, prefix capacity, depot excluded |

## Breadth, startup and adverse/open results

| Panel | Method | Eligible certificates | Positions |
|---|---|---|---|
| B1 | P | 7 | 12 |
| B1 | PS | 7 | 12 |
| B1 | GI-TBC | 9 | 12 |
| B2 | P | 0 | 8 |
| B2 | PS | 0 | 8 |
| B2 | GI-TBC | 4 | 8 |
| B3 | P | 0 | 4 |
| B3 | PS | 0 | 4 |
| B3 | GI-TBC | 1 | 4 |
| D2-main | P | 1 | 4 |
| D2-main | PS | 1 | 4 |
| D2-main | GI-TBC | 3 | 4 |

The certificate/position rows count newly executed positions in each stage: B3 has four extra objective configurations per method. The complete weight comparison has six configurations per method after sharing the two actual rho1 B2 baselines; the paired summaries use those declared matching baselines. AM/mechanism views likewise differ from added-position counts, without adding independent inputs.

| Panel / contrast | n | Classes | Directions | Both-certified denominator / geometric ratio |
|---|---|---|---|---|
| B1/PS/P | 12 | {"BOTH_OPEN": 5, "BOTH_CERTIFIED": 7} | {"UNDETERMINED": 5, "Win": 6, "Lose": 1} | 7 /2.6870568 |
| B1/S2/P | 12 | {"LEFT_ONLY_CERTIFIED": 2, "BOTH_CERTIFIED": 7, "BOTH_OPEN": 3} | {"Win": 9, "UNDETERMINED": 3} | 7 /11.353394 |
| B1/S2/PS | 12 | {"LEFT_ONLY_CERTIFIED": 2, "BOTH_CERTIFIED": 7, "BOTH_OPEN": 3} | {"Win": 6, "Lose": 3, "UNDETERMINED": 3} | 7 /4.2252156 |
| B2/PS/P | 8 | {"BOTH_OPEN": 8} | {"UNDETERMINED": 8} | 0 /null |
| B2/S2/P | 8 | {"LEFT_ONLY_CERTIFIED": 4, "BOTH_OPEN": 4} | {"Win": 4, "UNDETERMINED": 4} | 0 /null |
| B2/S2/PS | 8 | {"LEFT_ONLY_CERTIFIED": 4, "BOTH_OPEN": 4} | {"Win": 4, "UNDETERMINED": 4} | 0 /null |
| B3/PS/P | 6 | {"BOTH_OPEN": 6} | {"UNDETERMINED": 6} | 0 /null |
| B3/S2/P | 6 | {"BOTH_OPEN": 4, "LEFT_ONLY_CERTIFIED": 2} | {"UNDETERMINED": 4, "Win": 2} | 0 /null |
| B3/S2/PS | 6 | {"BOTH_OPEN": 4, "LEFT_ONLY_CERTIFIED": 2} | {"UNDETERMINED": 4, "Win": 2} | 0 /null |
| D2-main/PS/P | 4 | {"BOTH_OPEN": 3, "BOTH_CERTIFIED": 1} | {"UNDETERMINED": 3, "Win": 1} | 1 /2.508264 |
| D2-main/S2/P | 4 | {"LEFT_ONLY_CERTIFIED": 2, "BOTH_CERTIFIED": 1, "BOTH_OPEN": 1} | {"Win": 3, "UNDETERMINED": 1} | 1 /76.712467 |
| D2-main/S2/PS | 4 | {"LEFT_ONLY_CERTIFIED": 2, "BOTH_CERTIFIED": 1, "BOTH_OPEN": 1} | {"Win": 3, "UNDETERMINED": 1} | 1 /30.583889 |

Geometric ratios condition on both methods certifying; they are not statistics for all open positions. Direction counts include nonmaterial differences, while substantive differences use the declared max(10s,10% of faster time) rule. Main Seed0, weight repeats and preselected Seed1 retain separate denominators.

Substantive comparator advantages and certificate reversals:

| Panel / role | Comparator | Class | GI-TBC Tcert | Comparator Tcert | GI-TBC U/L | Comparator U/L |
|---|---|---|---|---|---|---|
| B1/X-35-B | PS | BOTH_CERTIFIED | 17.904565 | 7.4501428 | 0 /0 | 0 /0 |

GI-TBC main-panel unresolved endpoints:

| Role | n | U | L | Signed gap | Offline positive floor | Status |
|---|---|---|---|---|---|---|
| K-20-S | 20 | 0.71680655 | 0.70535579 | 0.011450753 | 0.14765613 | open |
| K-35-U | 35 | 0.69285436 | 0.56576568 | 0.12708868 | 0 | open |
| N-B35-S | 35 | 0.4502915 | 0.3893106 | 0.060980902 | 0.21 | open |
| R-B35-S-T1 | 35 | 0.59151763 | 0.45590389 | 0.13561374 | 0.079726804 | open |
| R-B35-S-T2 | 35 | 0.34464263 | 0.21898595 | 0.12565668 | 0.079726804 | open |
| R-X35-S-T1 | 35 | 0.59219045 | 0.463358 | 0.12883245 | 0.097747095 | open |
| R-X35-S-T2 | 35 | 0.403272 | 0.21088702 | 0.19238498 | 0.097747095 | open |

Two-sided endpoint trade-offs (smaller gap alone is insufficient):

| Role / contrast | Left U / L | Right U / L |
|---|---|---|
| K-35-U S2/P | 0.69285436 /0.56576568 | 0.6647466 /0.33555562 |

Same-budget two-endpoint dominance among both-open pairs:

| Role / contrast | Better finite endpoints | Left U / L | Right U / L |
|---|---|---|---|
| K-15-S PS/P | P | 0.59226488 /0.52058344 | 0.59226488 /0.52766277 |
| K-20-S PS/P | P | 0.77521276 /0.54123324 | 0.72770243 /0.5418679 |
| K-20-S S2/P | S2 | 0.71680655 /0.70535579 | 0.72770243 /0.5418679 |
| K-20-S S2/PS | S2 | 0.71680655 /0.70535579 | 0.77521276 /0.54123324 |
| K-35-U PS/P | P | 0.7674566 /0.33192177 | 0.6647466 /0.33555562 |
| K-35-U S2/PS | S2 | 0.69285436 /0.56576568 | 0.7674566 /0.33192177 |
| N-C20-U PS/P | P | 0.25230857 /0.21473286 | 0.24855069 /0.21771891 |
| N-B35-S PS/P | PS | 0.48601332 /0.37334305 | 0.84487406 /0.3719078 |
| N-B35-S S2/P | S2 | 0.4502915 /0.3893106 | 0.84487406 /0.3719078 |
| N-B35-S S2/PS | S2 | 0.4502915 /0.3893106 | 0.48601332 /0.37334305 |
| R-B20-S-T1 PS/P | PS | 0.48663902 /0.36532417 | 0.54008463 /0.35815811 |
| R-B20-S-T2 PS/P | PS | 0.208465 /0.14620274 | 0.26909521 /0.14126239 |
| R-X20-S-T1 PS/P | PS | 0.64532503 /0.59035922 | 0.64532503 /0.58919686 |
| R-X20-S-T2 PS/P | P | 0.51971957 /0.28446967 | 0.47673074 /0.29110147 |
| R-B35-S-T1 PS/P | P | 0.63176549 /0.33451853 | 0.6063115 /0.33700238 |
| R-B35-S-T1 S2/P | S2 | 0.59151763 /0.45590389 | 0.6063115 /0.33700238 |
| R-B35-S-T1 S2/PS | S2 | 0.59151763 /0.45590389 | 0.63176549 /0.33451853 |
| R-B35-S-T2 S2/P | S2 | 0.34464263 /0.21898595 | 0.47163711 /0.15437565 |
| R-B35-S-T2 S2/PS | S2 | 0.34464263 /0.21898595 | 0.43829122 /0.15541566 |
| R-B35-S-T2 PS/P | PS | 0.43829122 /0.15541566 | 0.47163711 /0.15437565 |
| R-X35-S-T1 PS/P | PS | 0.59323123 /0.29883906 | 0.65571261 /0.29600876 |
| R-X35-S-T1 S2/P | S2 | 0.59219045 /0.463358 | 0.65571261 /0.29600876 |
| R-X35-S-T1 S2/PS | S2 | 0.59219045 /0.463358 | 0.59323123 /0.29883906 |
| R-X35-S-T2 PS/P | PS | 0.40456723 /0.2038174 | 0.49051747 /0.20128753 |
| R-X35-S-T2 S2/P | S2 | 0.403272 /0.21088702 | 0.49051747 /0.20128753 |
| R-X35-S-T2 S2/PS | S2 | 0.403272 /0.21088702 | 0.40456723 /0.2038174 |

These are feasible/qualified endpoint comparisons at the fixed budget; both-open certification direction remains UNDETERMINED. In particular a paid-start compact run may have a worse feasible objective and lower bound than cold P despite paying complete H. Such cases are retained as finite startup counterexamples, without inferring a distributional or eventual-proof-time ranking.

Current N-X20-B cold P retains its rejected native source and qualifies its own exact-zero certificate in 24.089238 s through the independently finalized full-domain nonnegative floor. Three source_bound_witness_contradiction records refer to its one returned native call. No rejected native bound is revived, no other method supplies the proof, and no historical R132 exclusion is retroactively recounted under this current policy.

Independent PS/GI-TBC startup comparisons: 28 matched role/Seed/objective configurations; complete H on both sides in 28, matching semantic trace in 28, matching fleet in 28. These are independently paid runs, not transferred Starts. P/PS measures the complete startup package; PS/GI-TBC measures the subsequent complete algorithm conditional on each defined own H. No H-seed grid is justified without a concrete mismatch/sensitivity witness.

The preselected K-15-S Seed1 triplet preserves own certification only for GI-TBC, with Seed0/1 certificate costs 112.7693/115.44409 s (nonmaterial difference). All six feasible objectives agree, but compact own proof statuses remain open. The final compact L ordering reverses: Seed0 P/PS=0.52766277/0.52058344, Seed1 P/PS=0.52911484/0.53227978. This is one matched finite repeat, separate from the main panel and from the other three preselected roles; no runtime-distribution inference or cross-run certificate transfer follows.

UC-B20-B retains all three own certificates at both Seeds. Its GI-TBC times are 4.1489743/4.0998967 s and P 315.40276/314.51319 s, while PS changes from 236.09051 to 125.39079 s. The PS descriptive clock shift exceeds the declared threshold; the P/GI-TBC shifts do not. The within-role integrated-method advantage persists, but stable certificate status does not imply all runtimes are stable. No distributional claim or replacement of Seed0 follows.

R-B20-S-T1 repeats GI-TBC-only own certification at Seed0/1, with costs 784.14348/656.73404 s; their descriptive shift exceeds the substantive rule. Seed1 PS reaches the same U=0.48073544 as GI-TBC but remains open with its own L=0.3674823. Cold P improves U from 0.54008463 to 0.49322447, while its L falls from 0.35815811 to 0.35462569. The stable certificate pattern does not imply stable clocks or ordered cross-Seed endpoints. No open proof time, transfer or runtime-distribution claim is inferred.

K-35-U keeps all six own runs open. Its Seed1 GI-TBC U/L=0.66835825/0.55477986 improve both endpoints over P 0.7588516/0.33057446 and PS 0.7126478/0.33509462. Seed0 retains the opposed P/GI-TBC endpoint result. The compact two-endpoint relation also flips from P better than PS at Seed0 to PS better than P at Seed1. GI-TBC improves its own U from 0.69285436 to 0.66835825 while its L weakens from 0.56576568 to 0.55477986. No smaller-gap summary replaces these separate endpoints; no own proof or certificate time is transferred.

| Method | Selected Seed0 certificates /4 | Seed1 certificates /4 |
|---|---|---|
| P | 1 | 1 |
| PS | 1 | 1 |
| GI-TBC | 3 | 3 |

Proof-status counts agree on these preselected roles, while clocks and endpoint orderings can change. The limited repeat does not estimate a runtime distribution and does not replace the main Seed0 panel.

## Physical resources and objective weights

| Base / T | Method | U | L | G / Pavg | Max duration / T | Returns |
|---|---|---|---|---|---|---|
| R-B20-S-T1 | P | 0.54008463 | 0.35815811 | 0.23941648 /0.30066815 | 0.99318625 | 0 |
| R-B20-S-T1 | PS | 0.48663902 | 0.36532417 | 0.22234801 /0.26429102 | 0.99178731 | 0 |
| R-B20-S-T1 | GI-TBC | 0.48073544 | 0.48073542 | 0.21644442 /0.26429102 | 0.99985053 | 0 |
| R-B20-S-T2 | PS | 0.208465 | 0.14620274 | 0.092652085 /0.11581292 | 0.99995123 | 0 |
| R-B20-S-T2 | GI-TBC | 0.19847345 | 0.19847345 | 0.081918139 /0.11655531 | 0.99981635 | 0 |
| R-B20-S-T2 | P | 0.26909521 | 0.14126239 | 0.11616276 /0.15293244 | 0.99200963 | 0 |
| R-X20-S-T1 | GI-TBC | 0.64532503 | 0.64532503 | 0.31465207 /0.33067296 | 0.99983365 | 1 |
| R-X20-S-T1 | P | 0.64532503 | 0.58919686 | 0.31465207 /0.33067296 | 0.99983365 | 1 |
| R-X20-S-T1 | PS | 0.64532503 | 0.59035922 | 0.31465207 /0.33067296 | 0.99983365 | 1 |
| R-X20-S-T2 | P | 0.47673074 | 0.29110147 | 0.22446154 /0.2522692 | 0.98221603 | 2 |
| R-X20-S-T2 | PS | 0.51971957 | 0.28446967 | 0.22989172 /0.28982785 | 0.99573904 | 0 |
| R-X20-S-T2 | GI-TBC | 0.43479563 | 0.43479563 | 0.20600061 /0.22879503 | 0.99764141 | 0 |
| R-B35-S-T1 | PS | 0.63176549 | 0.33451853 | 0.29372447 /0.33804103 | 0.97952287 | 0 |
| R-B35-S-T1 | GI-TBC | 0.59151763 | 0.45590389 | 0.28536728 /0.30615036 | 0.99410865 | 2 |
| R-B35-S-T1 | P | 0.6063115 | 0.33700238 | 0.30289458 /0.30341692 | 0.99714612 | 3 |
| R-B35-S-T2 | GI-TBC | 0.34464263 | 0.21898595 | 0.18154464 /0.16309799 | 0.99629072 | 3 |
| R-B35-S-T2 | P | 0.47163711 | 0.15437565 | 0.22471225 /0.24692485 | 0.98852712 | 0 |
| R-B35-S-T2 | PS | 0.43829122 | 0.15541566 | 0.21368983 /0.22460139 | 0.99581859 | 4 |
| R-X35-S-T1 | P | 0.65571261 | 0.29600876 | 0.25169104 /0.40402157 | 0.9960257 | 0 |
| R-X35-S-T1 | PS | 0.59323123 | 0.29883906 | 0.26917611 /0.32405512 | 0.99945638 | 1 |
| R-X35-S-T1 | GI-TBC | 0.59219045 | 0.463358 | 0.26813533 /0.32405512 | 0.99945638 | 1 |
| R-X35-S-T2 | PS | 0.40456723 | 0.2038174 | 0.194085 /0.21048222 | 0.99521018 | 0 |
| R-X35-S-T2 | GI-TBC | 0.403272 | 0.21088702 | 0.18254959 /0.22072241 | 0.998568 | 0 |
| R-X35-S-T2 | P | 0.49051747 | 0.20128753 | 0.2056543 /0.28486316 | 0.99904551 | 0 |

The eight configurations use four serialized shortage bases, all weights positive and rho1. The analytic floors are recomputed from the actual arrays and apply to every method. Dual T changes no other physical/objective field; the design uses depot radius and local supply/handling, not solver outcomes. Route utilization describes the attained feasible plans; it does not prove an optimum is resource-bound. Feasible-set inclusion orders true optimal values, but does not order these finite-budget U/L or runtime observations.

B3 adds two weights at fixed n20/n35 physical configurations and shares only the actual matching rho1 baseline. The full G/Pavg/S and vehicle records retain how weight affects operating choices. Uncertified points are not an exact optimal trade-off curve. Fixed rho removes total weight-scale variation, not geography/relative weights/stock/fleet variation; n-stratified performance is not a causal size experiment.

At the fixed n35 physical configuration, the rho2 saved GI-TBC plan has G/P_avg=0.14845888/0.18804694, both below the rho1 saved plan values 0.18254959/0.22072241. This post hoc component dominance is a concrete primal-search witness, not an exact optimal weight frontier. All own endpoints and certificate/open identities remain unchanged; no solution, bound or Start crossed production runs.

## AM, four mechanisms and the second Seed

### Seed0 main AM/mechanism comparisons

| Panel / variant | Comparisons | Classes | Directions | Material wins / losses |
|---|---|---|---|---|
| C1/AM004/S2 | 4 | {"BOTH_CERTIFIED": 2, "BOTH_OPEN": 2} | {"Lose": 2, "UNDETERMINED": 2} | 0 /0 |
| C1/AM016/S2 | 4 | {"BOTH_CERTIFIED": 2, "BOTH_OPEN": 2} | {"Lose": 1, "UNDETERMINED": 2, "Win": 1} | 0 /0 |
| C2/NO_AB/S2 | 4 | {"BOTH_CERTIFIED": 2, "BOTH_OPEN": 2} | {"Lose": 2, "UNDETERMINED": 2} | 0 /1 |
| C2/NO_CG/S2 | 4 | {"BOTH_CERTIFIED": 2, "BOTH_OPEN": 2} | {"Lose": 1, "Win": 1, "UNDETERMINED": 2} | 0 /1 |
| C2/NO_CR/S2 | 4 | {"BOTH_CERTIFIED": 2, "BOTH_OPEN": 2} | {"Win": 1, "Lose": 1, "UNDETERMINED": 2} | 1 /0 |
| C2/S2R/S2 | 4 | {"BOTH_CERTIFIED": 2, "BOTH_OPEN": 2} | {"Win": 2, "UNDETERMINED": 2} | 0 /0 |

### Seed1 limited AM/mechanism repeats

| Panel / variant | Comparisons | Classes | Directions | Material wins / losses |
|---|---|---|---|---|
| D2-AM/AM004/S2 | 2 | {"BOTH_CERTIFIED": 2} | {"Win": 2} | 0 /0 |
| D2-AM/AM016/S2 | 2 | {"BOTH_CERTIFIED": 2} | {"Lose": 1, "Win": 1} | 0 /0 |
| D2-mechanism/NO_AB/S2 | 2 | {"BOTH_CERTIFIED": 2} | {"Win": 1, "Lose": 1} | 1 /0 |
| D2-mechanism/NO_CG/S2 | 2 | {"BOTH_CERTIFIED": 2} | {"Win": 2} | 1 /0 |
| D2-mechanism/NO_CR/S2 | 2 | {"BOTH_CERTIFIED": 2} | {"Lose": 2} | 0 /1 |
| D2-mechanism/S2R/S2 | 2 | {"BOTH_CERTIFIED": 2} | {"Win": 2} | 0 /0 |

AM uses actual post-preset split_threshold=.04/.08/.16. The finite AM and all-child C6 ledgers are joined by decision sequence; finite score gates, no-strict-improvement terminals, logical one/both-child infeasibility and other actions remain separate, and an empty join has no recorded child decision. Per-decision scores and tolerance-adjusted margins apply only where finite, never to logical infeasibility. The R135 source trajectories were read prospectively: their finite scores are far below the three thresholds; no split was forced. An unchanged action or unexposed finite gate is a scoped sensitivity result, not proof of all parameter robustness. Final materialized-leaf depth/width, decision-parent depth and probed-child depth are distinct observations. Depth 8 / minimum width 1e-4 remain fixed. Recorded guard rows are joined to retained scheduler-epoch geometry; source-rejection reset, missing leaves or other gates remain unknown. Eligible work may stop before its row, so missing rows do not prove no attempted test. Depth failure short-circuits width; width that would also fail is recorded separately from an actual width rejection. A zero-width proof without a recorded guard is not called a width trigger. Offline replay beyond a first divergent action is not a complete runtime counterfactual.

| Role / Seed / method | Eligibility evaluations | Depth8 rejections | Width1e-4 rejections | Audit status |
|---|---|---|---|---|
| K-15-S /0 /S2 | 2 | 0 | 0 | RECORDED_GUARD_ROWS_AUDITED |
| UC-B20-B /0 /S2 | 5 | 0 | 0 | RECORDED_GUARD_ROWS_AUDITED |
| K-20-S /0 /S2 | 2 | 0 | 0 | RECORDED_GUARD_ROWS_AUDITED |
| K-35-U /0 /S2 | 1 | 0 | 0 | RECORDED_GUARD_ROWS_AUDITED |
| K-15-S /0 /AM004 | 2 | 0 | 0 | RECORDED_GUARD_ROWS_AUDITED |
| K-15-S /0 /AM016 | 2 | 0 | 0 | RECORDED_GUARD_ROWS_AUDITED |
| K-20-S /0 /AM004 | 2 | 0 | 0 | RECORDED_GUARD_ROWS_AUDITED |
| K-20-S /0 /AM016 | 2 | 0 | 0 | RECORDED_GUARD_ROWS_AUDITED |
| UC-B20-B /0 /AM004 | 5 | 0 | 0 | RECORDED_GUARD_ROWS_AUDITED |
| UC-B20-B /0 /AM016 | 5 | 0 | 0 | RECORDED_GUARD_ROWS_AUDITED |
| K-35-U /0 /AM004 | 1 | 0 | 0 | RECORDED_GUARD_ROWS_AUDITED |
| K-35-U /0 /AM016 | 1 | 0 | 0 | RECORDED_GUARD_ROWS_AUDITED |
| K-15-S /1 /S2 | 2 | 0 | 0 | RECORDED_GUARD_ROWS_AUDITED |
| UC-B20-B /1 /S2 | 5 | 0 | 0 | RECORDED_GUARD_ROWS_AUDITED |
| K-35-U /1 /S2 | 1 | 0 | 0 | RECORDED_GUARD_ROWS_AUDITED |
| K-15-S /1 /AM004 | 2 | 0 | 0 | RECORDED_GUARD_ROWS_AUDITED |
| K-15-S /1 /AM016 | 2 | 0 | 0 | RECORDED_GUARD_ROWS_AUDITED |
| UC-B20-B /1 /AM004 | 5 | 0 | 0 | RECORDED_GUARD_ROWS_AUDITED |
| UC-B20-B /1 /AM016 | 5 | 0 | 0 | RECORDED_GUARD_ROWS_AUDITED |

The four contrasts preserve own H and the physical problem: legal post-R130 full-root GI-TBC-R; deletion of only A/B; deletion of ordered supply and pair cover/conditional handling C_R; deletion of existing geometry/objective estimators and dedicated helpers C_G. Core state products, original domains, binary direction and integer final inventory remain. Continuous p/d stay implicitly integral without A/B. Old MR/MG were not selected and triples were not restored.

Same-domain deletion weakens or preserves an ideal LP bound, with other auxiliaries reoptimized. Complete search follows different native paths, so root/Work/node improvements do not guarantee full-method benefits or endpoint dominance. Root scope/objective/cutoff and complete model/H/LP/MIP costs are retained. Contributions are conditional and cannot be added as speed-up percentages. The limited Seed1 repeats remain preselected checks rather than population runtime statistics or replacements for adverse Seed0 observations.

| Contrast / role / Seed | Matched own H | Matched initial domain/objective/cutoff | Optimal-LP attribution exposed | Left-minus-full root LP |
|---|---|---|---|---|
| GI-TBC-R /K-15-S /0 | 1 | 1 | 1 | 0 |
| GI-TBC minus A/B /K-15-S /0 | 1 | 1 | 1 | -0.00012117288 |
| GI-TBC minus C_R /K-15-S /0 | 1 | 1 | 1 | -5.8286709e-16 |
| GI-TBC minus C_G /K-15-S /0 | 1 | 1 | 1 | -6.1062266e-16 |
| GI-TBC minus A/B /UC-B20-B /0 | 1 | 1 | 1 | 5.5511151e-17 |
| GI-TBC minus C_R /UC-B20-B /0 | 1 | 1 | 1 | 0 |
| GI-TBC minus C_G /UC-B20-B /0 | 1 | 1 | 1 | 5.5511151e-17 |
| GI-TBC-R /UC-B20-B /0 | 1 | 1 | 1 | 0 |
| GI-TBC minus C_R /K-20-S /0 | 1 | 1 | 1 | -1.6653345e-16 |
| GI-TBC minus C_G /K-20-S /0 | 1 | 1 | 1 | -1.6653345e-16 |
| GI-TBC-R /K-20-S /0 | 1 | 1 | 1 | 0 |
| GI-TBC minus A/B /K-20-S /0 | 1 | 1 | 1 | -0.001324148 |
| GI-TBC minus C_G /K-35-U /0 | 1 | 1 | 1 | 5.5511151e-17 |
| GI-TBC-R /K-35-U /0 | 1 | 1 | 1 | 0 |
| GI-TBC minus A/B /K-35-U /0 | 1 | 1 | 1 | 0 |
| GI-TBC minus C_R /K-35-U /0 | 1 | 1 | 1 | 0 |
| GI-TBC-R /K-15-S /1 | 1 | 1 | 1 | 0 |
| GI-TBC minus A/B /K-15-S /1 | 1 | 1 | 1 | -0.00012117288 |
| GI-TBC minus C_R /K-15-S /1 | 1 | 1 | 1 | -1.9428903e-16 |
| GI-TBC minus C_G /K-15-S /1 | 1 | 1 | 1 | -5.5511151e-17 |
| GI-TBC-R /UC-B20-B /1 | 1 | 1 | 1 | 0 |
| GI-TBC minus A/B /UC-B20-B /1 | 1 | 1 | 1 | 5.5511151e-17 |
| GI-TBC minus C_R /UC-B20-B /1 | 1 | 1 | 1 | -5.5511151e-17 |
| GI-TBC minus C_G /UC-B20-B /1 | 1 | 1 | 1 | 5.5511151e-17 |

All24 mechanism pairs meet common initial domain/objective/cutoff and complete-own-H conditions. A/B has visible initial-LP increments on K-15-S and K-20-S only (about.000121173 and.001324148); resource and geometry/objective groups show no initial objective increment above1e-7 on these four roles. Root-only reproduces the full initial LP. No visible initial-objective increment does not imply slack, inactive or redundant rows; the optimal face, later native search and final bounds can still differ.

### Complete method clocks and nested cost diagnostics

**Seed0 complete costs**

| Role / variant | Production s | Own certificate s | Postverification s | Total s |
|---|---|---|---|---|
| K-15-S / GI-TBC | 112.7693 | 112.7693 | 3.7703703 | 116.53967 |
| K-15-S / GI-TBC-R | 112.64892 | 112.64892 | 3.3459695 | 115.99489 |
| K-15-S / GI-TBC minus A/B | 128.32487 | 128.32487 | 3.6131221 | 131.93799 |
| K-15-S / GI-TBC minus C_R | 75.106399 | 75.106399 | 2.3999733 | 77.506373 |
| K-15-S / GI-TBC minus C_G | 143.15033 | 143.15033 | 4.4736276 | 147.62396 |
| UC-B20-B / GI-TBC | 4.1489743 | 4.1489743 | 2.3470005 | 6.4959748 |
| UC-B20-B / GI-TBC-R | 1.8720622 | 1.8720622 | 0.4078939 | 2.2799561 |
| UC-B20-B / GI-TBC minus A/B | 4.1861882 | 4.1861882 | 2.2482885 | 6.4344767 |
| UC-B20-B / GI-TBC minus C_R | 4.9177495 | 4.9177495 | 2.2885682 | 7.2063177 |
| UC-B20-B / GI-TBC minus C_G | 3.3491219 | 3.3491219 | 1.7032509 | 5.0523728 |
| K-20-S / GI-TBC | 1172.19 | null | 61.143828 | 1233.3338 |
| K-20-S / GI-TBC-R | 1172.2241 | null | 61.891907 | 1234.116 |
| K-20-S / GI-TBC minus A/B | 1172.1212 | null | 41.735794 | 1213.857 |
| K-20-S / GI-TBC minus C_R | 1171.9135 | null | 36.674475 | 1208.588 |
| K-20-S / GI-TBC minus C_G | 1171.9553 | null | 43.499818 | 1215.4551 |
| K-35-U / GI-TBC | 2371.1519 | null | 3.8000497 | 2374.9519 |
| K-35-U / GI-TBC-R | 2370.9937 | null | 6.5279735 | 2377.5217 |
| K-35-U / GI-TBC minus A/B | 2372.3786 | null | 3.7916157 | 2376.1702 |
| K-35-U / GI-TBC minus C_R | 2370.9698 | null | 3.5629073 | 2374.5327 |
| K-35-U / GI-TBC minus C_G | 2370.9783 | null | 2.6383525 | 2373.6167 |

The following values are nested diagnostic spans/counters; they are not additional budget charges.

| Role / variant | H search span s (end status) | Canonical generation s: cumulative / first span | Explicit LP Runtime s: L0 / non-L0 | MIP Runtime sum s | Gurobi Work sum | Native B&B nodes sum |
|---|---|---|---|---|---|---|
| K-15-S / GI-TBC | 0.2826448 (complete) | 0.4144385 / 0.1408732 | 0.082999945 / 0.11299992 | 110.549 | 160.9257 | 48701 |
| K-15-S / GI-TBC-R | 0.279114 (complete) | 0.1416099 / 0.1417478 | 0.060000181 / 0 | 110.807 | 160.1566 | 48700 |
| K-15-S / GI-TBC minus A/B | 0.2824764 (complete) | 0.4131218 / 0.1396676 | 0.052000046 / 0.10800004 | 126.181 | 186.18313 | 55424 |
| K-15-S / GI-TBC minus C_R | 0.2789574 (complete) | 0.3913022 / 0.1293898 | 0.065999985 / 0.11200023 | 73.048 | 109.31029 | 29036 |
| K-15-S / GI-TBC minus C_G | 0.2835653 (complete) | 0.2711729 / 0.0891051 | 0.065000057 / 0.10400009 | 141.108 | 204.70034 | 68560 |
| UC-B20-B / GI-TBC | 0.0437166 (complete) | 2.0289301 / 0.2248529 | 0 / 0.12799978 | 0.46600008 | 0.95944409 | 2 |
| UC-B20-B / GI-TBC-R | 0.0437707 (complete) | 0.225006 / 0.2251427 | 0.025000095 / 0 | 0.58399987 | 0.72897559 | 1 |
| UC-B20-B / GI-TBC minus A/B | 0.0445509 (complete) | 2.0352406 / 0.225356 | 0.023000002 / 0.10200024 | 0.61400008 | 0.94241499 | 2 |
| UC-B20-B / GI-TBC minus C_R | 0.0439979 (complete) | 2.0023174 / 0.2209729 | 0.0089998245 / 0.13100004 | 1.2949998 | 2.0596289 | 314 |
| UC-B20-B / GI-TBC minus C_G | 0.0463914 (complete) | 1.0932279 / 0.1190578 | 0.018000126 / 0.1400001 | 0.74399996 | 1.1841183 | 2 |
| K-20-S / GI-TBC | 0.3361249 (complete) | 0.7658647 / 0.2538181 | 0.14199996 / 0.21399999 | 1168.312 | 1906.6075 | 449570 |
| K-20-S / GI-TBC-R | 0.3375304 (complete) | 0.2547667 / 0.2548933 | 0.13499999 / 0 | 1169.152 | 1835.2704 | 444833 |
| K-20-S / GI-TBC minus A/B | 0.3361725 (complete) | 0.7542771 / 0.2512451 | 0.071000099 / 0.171 | 1168.456 | 1912.8886 | 399850 |
| K-20-S / GI-TBC minus C_R | 0.3369718 (complete) | 0.7266129 / 0.2425207 | 0.1170001 / 0.19499993 | 1168.378 | 1950.9894 | 407600 |
| K-20-S / GI-TBC minus C_G | 0.3358285 (complete) | 0.4358518 / 0.1445851 | 0.12699986 / 0.20799994 | 1168.707 | 2034.3654 | 386408 |
| K-35-U / GI-TBC | 0.5504967 (complete) | 3.2182494 / 1.0761385 | 0.3440001 / 0.59899998 | 2364.584 | 5050.8926 | 18922 |
| K-35-U / GI-TBC-R | 0.5471255 (complete) | 1.0760951 / 1.0762733 | 0.33899999 / 0 | 2367.657 | 5060.1151 | 18980 |
| K-35-U / GI-TBC minus A/B | 0.5469245 (complete) | 3.2198339 / 1.0721097 | 0.24300003 / 0.43300009 | 2364.851 | 5095.0912 | 19670 |
| K-35-U / GI-TBC minus C_R | 0.5461507 (complete) | 3.0743675 / 1.0227311 | 0.35100007 / 0.76800013 | 2364.545 | 5076.7862 | 17918 |
| K-35-U / GI-TBC minus C_G | 0.5458935 (complete) | 1.5228871 / 0.5071439 | 0.30400014 / 0.40299988 | 2366.763 | 5109.7284 | 19335 |

**Seed1 limited-repeat complete costs**

| Role / variant | Production s | Own certificate s | Postverification s | Total s |
|---|---|---|---|---|
| K-15-S / GI-TBC | 115.44409 | 115.44409 | 4.1755562 | 119.61964 |
| K-15-S / GI-TBC-R | 113.58025 | 113.58025 | 3.7870712 | 117.36732 |
| K-15-S / GI-TBC minus A/B | 93.699712 | 93.699712 | 2.954242 | 96.653954 |
| K-15-S / GI-TBC minus C_R | 132.47474 | 132.47474 | 4.4950812 | 136.96982 |
| K-15-S / GI-TBC minus C_G | 99.600618 | 99.600618 | 2.391807 | 101.99242 |
| UC-B20-B / GI-TBC | 4.0998967 | 4.0998967 | 2.2886625 | 6.3885592 |
| UC-B20-B / GI-TBC-R | 1.9540785 | 1.9540785 | 0.4161838 | 2.3702623 |
| UC-B20-B / GI-TBC minus A/B | 4.4664624 | 4.4664624 | 2.2871384 | 6.7536008 |
| UC-B20-B / GI-TBC minus C_R | 4.6028355 | 4.6028355 | 2.2466693 | 6.8495048 |
| UC-B20-B / GI-TBC minus C_G | 2.9587732 | 2.9587732 | 1.7039552 | 4.6627284 |

The following values are nested diagnostic spans/counters; they are not additional budget charges.

| Role / variant | H search span s (end status) | Canonical generation s: cumulative / first span | Explicit LP Runtime s: L0 / non-L0 | MIP Runtime sum s | Gurobi Work sum | Native B&B nodes sum |
|---|---|---|---|---|---|---|
| K-15-S / GI-TBC | 0.2792684 (complete) | 0.4150979 / 0.1418928 | 0.070999861 / 0.095999956 | 113.257 | 161.82767 | 42579 |
| K-15-S / GI-TBC-R | 0.2800991 (complete) | 0.1446676 / 0.1448295 | 0.072999954 / 0 | 111.79 | 161.11174 | 42578 |
| K-15-S / GI-TBC minus A/B | 0.2800482 (complete) | 0.4117279 / 0.140339 | 0.059999943 / 0.089999914 | 91.513 | 136.51416 | 36628 |
| K-15-S / GI-TBC minus C_R | 0.27983 (complete) | 0.3920493 / 0.1288144 | 0.071000099 / 0.10600019 | 130.239 | 194.15951 | 52342 |
| K-15-S / GI-TBC minus C_G | 0.2793849 (complete) | 0.2738483 / 0.0895389 | 0.067000151 / 0.1329999 | 97.652 | 150.97831 | 36896 |
| UC-B20-B / GI-TBC | 0.0437328 (complete) | 2.0502473 / 0.2269808 | 0.020999908 / 0.12700009 | 0.43299985 | 0.87248001 | 2 |
| UC-B20-B / GI-TBC-R | 0.0436324 (complete) | 0.2259536 / 0.2260922 | 0.024000168 / 0 | 0.63699985 | 0.75012051 | 1 |
| UC-B20-B / GI-TBC minus A/B | 0.0436685 (complete) | 2.0484047 / 0.2281078 | 0.0069999695 / 0.10900044 | 0.84700012 | 1.1859914 | 3 |
| UC-B20-B / GI-TBC minus C_R | 0.0475519 (complete) | 2.0125151 / 0.2248949 | 0.0050001144 / 0.12400031 | 0.95600009 | 1.6078102 | 212 |
| UC-B20-B / GI-TBC minus C_G | 0.0445098 (complete) | 1.0910047 / 0.1186639 | 0.016000032 / 0.11899996 | 0.39599991 | 0.78217308 | 2 |

H search spans hga_start to decoded_descent_complete with matching labels and ordered events; it excludes earlier instance/configuration work and later log/final-candidate/Start handling. Its recorded end status is shown separately from complete-H qualification. The first canonical-model phase and cumulative artifact-generation timer overlap; neither includes all Gurobi loading, conversion, model management and Start preparation. L0 Runtime can include several explicit LP calls; MIP Runtime already includes its own internal relaxations/presolve/branching/callbacks. Work is not seconds, and summed native B&B nodes are neither outer interval nodes nor cross-call deduplicated nodes. Missing phase pairs stay null with their recorded status. Compact P/PS result counters have a distinct source when no paper ledger exists; zero explicit LP calls do not imply that a MIP had no root relaxation. No time residual is labelled net controller overhead.

All three K-15-S row-deletion time directions reverse in the preselected Seed1 repeat. Its full cost is 115.44409 s, versus 93.699712/132.47474/99.600618 s for A/B, resource and geometry/objective deletion. All six within-Seed comparisons are substantive: full beats A/B and geometry deletion at Seed0 but loses at Seed1; resource deletion wins at Seed0 and loses at Seed1. The corresponding MIP/Work/node counters, stable initial-LP patterns and matching own H delimit attribution. Two Seeds do not supply stable component rankings, an additive decomposition or evidence for selecting per-instance variants.

The K-35-U row-deletion pattern is consistent across all three groups: each deletion improves its own verified feasible objective and weakens its qualified final lower bound relative to full GI-TBC. All five variants remain open. Root-only has the same U and slightly higher final L. The four-role Seed0 outer-package check shows no substantive full-over-root certificate-cost advantage on the two easier certified roles; both harder roles remain open with root-only retaining the higher final L. These bounded adverse/limited incremental findings coexist with the integrated-method gains over compact controls and the separately preserved post-R130 history. No additive contribution or per-instance selection follows.

Observed Seed0 mechanism decisions are recorded separately from native solver nodes and from the AM threshold panel:

| Role / variant | Finite score gates | No-strict terminals | Logical infeasibility splits | Observed actions |
|---|---|---|---|---|
| K-15-S / GI-TBC | 1 | 1 | 0 | {"native-target": 1, "exact-close": 1} |
| K-15-S / GI-TBC-R | 0 | 0 | 0 | {} |
| K-15-S / GI-TBC minus A/B | 0 | 1 | 0 | {"exact-close": 1} |
| K-15-S / GI-TBC minus C_R | 1 | 1 | 0 | {"native-target": 1, "exact-close": 1} |
| K-15-S / GI-TBC minus C_G | 1 | 1 | 0 | {"native-target": 1, "exact-close": 1} |
| UC-B20-B / GI-TBC | 1 | 1 | 3 | {"split": 3, "native-target": 1, "exact-close": 1} |
| UC-B20-B / GI-TBC-R | 0 | 0 | 0 | {} |
| UC-B20-B / GI-TBC minus A/B | 1 | 1 | 3 | {"split": 3, "native-target": 1, "exact-close": 1} |
| UC-B20-B / GI-TBC minus C_R | 1 | 1 | 3 | {"split": 3, "native-target": 1, "exact-close": 1} |
| UC-B20-B / GI-TBC minus C_G | 1 | 1 | 3 | {"split": 3, "native-target": 1, "exact-close": 1} |
| K-20-S / GI-TBC | 1 | 1 | 0 | {"native-target": 1, "exact-close": 1} |
| K-20-S / GI-TBC-R | 0 | 0 | 0 | {} |
| K-20-S / GI-TBC minus A/B | 0 | 1 | 0 | {"exact-close": 1} |
| K-20-S / GI-TBC minus C_R | 1 | 1 | 0 | {"native-target": 1, "exact-close": 1} |
| K-20-S / GI-TBC minus C_G | 1 | 1 | 0 | {"native-target": 1, "exact-close": 1} |
| K-35-U / GI-TBC | 0 | 1 | 0 | {"exact-close": 1} |
| K-35-U / GI-TBC-R | 0 | 0 | 0 | {} |
| K-35-U / GI-TBC minus A/B | 0 | 1 | 0 | {"exact-close": 1} |
| K-35-U / GI-TBC minus C_R | 0 | 1 | 0 | {"exact-close": 1} |
| K-35-U / GI-TBC minus C_G | 0 | 1 | 0 | {"exact-close": 1} |

In particular A/B deletion on K-15-S/K-20-S reaches only the no-strict terminal, whereas full/C_R-deleted/C_G-deleted versions also have a finite native-target gate. The same configured policy may therefore realize different actions after a formulation change. No same-trajectory or MIP-only causal interpretation is inferred from a single-group switch.

## Stage decision and next research

Retain the accepted GI-TBC configuration, tau=.08, pair-only and AP off. This finite consolidation does not select a new mechanism or per-instance setting. Earlier R132 breadth, R134 confirmation and R135 mixed/negative AP results remain scientifically usable with their original identities. The fixed-denominator R133 original-objective gap precludes attributing all hard cases to a changing denominator; R132 strict service-coordinate evidence and R134 TC/AP comparisons are prior results, not unstudied gaps.

1. **Positive-objective primal/dual bottlenecks under physical resources.** Witnesses: R-X20-S-T1 has the same verified U=0.64532503 for all three methods, but only GI-TBC certifies; K-35-U has P U/L=0.6647466/0.33555562 and GI-TBC 0.69285436/0.56576568; R-X35-S-T2 remains open for GI-TBC at U/L=0.403272/0.21088702, and its saved rho1 incumbent is dominated in G/P_avg by the saved rho2 feasible plan at the same physical input/T (0.14845888/0.18804694 versus 0.18254959/0.22072241). The first is a dual-proof gap without a missing best feasible objective, the second is an opposed primal/dual endpoint result, and the third retains both a substantial positive-resource gap and an offline witness that its own saved incumbent can improve. These post hoc comparisons do not replace production endpoints or transfer starts. Hypothesis: uniformly valid inventory/service/resource information can improve proof progress while a separate incumbent-search deficit persists on some hard configurations. Minimal next step: inspect saved root-to-final bound and route progress on one retained n35 dual-T pair and K-35-U; separate a primal deficit from a dual deficit before formulating one uniform structural modification. These are research witnesses chosen from the completed study, not new validation positions or a reason for immediate long convergence runs.

2. **Integer inventory and original-objective epigraph information.** R133 J2/J3 retains a 1/4 original-objective gap at fixed S=3 even with the complete tiny joint-service hull; R134 threshold-count (TC) strengthening closes 3/16 on its stated reference but leaves 1/16; its two saved real roots show no reliable further objective increment. Hypothesis: joint integer stock/epigraph/resource information can matter beyond marginal state penalties and labelled service compatibility. Minimal next step: one full-universe valid witness/extension on the saved tiny reference, followed by an explicit real-domain validity interface before production. Do not transplant a four-station support bound after deleting outside suppliers.

3. **AM child information versus complete proof cost.** Witness: K-35-U has decision-state U=0.7674566, parent bound 0.20017766 and child bounds 0.20017766/0.54526678. The weaker side gives no strict minimum-bound improvement, so the rule schedules exact-close before a finite threshold comparison; the three Seed0 thresholds retain this terminal class and the final runs remain open. This is not a failed tau crossing. Together with the paired complete-cost records and prior R47/R52 examples, it motivates the hypothesis that structural child asymmetry can distinguish proof effort beyond a scalar two-sided improvement summary. Minimal next step: one bounded saved-state comparison using the same valid child information and exact coverage, explicitly separating eligibility/no-strict terminal logic from a proposed structural score or continuation. Do not use elapsed machine time to switch algorithm or leaf policy.

## Budget, manuscript and remaining facts

New native outer computation: **118955.400563 s (33.043167 h)** out of 216000 s; remaining 97044.599437 s. Planned caps total 174600 s, with 41400 s reserve. Nested H/LP/MIP/Work are not added. Pure verification/build/analysis/PDF/transport have separate measured clocks; elapsed repair delay is preserved in its own row rather than hidden or charged as a repeated solve. The first P postverification AP-contract compatibility error was corrected by pure replay; its producer/result/observations/launch/seal hashes and original production clock did not change. No native retry was used.

No general stability grid is required merely because some components have limited contribution, gates do not change action, Seeds differ, or n35 remains open. The registered main comparisons and limited repeat checks answer the finite questions; unused budget is not a requirement to add tests. Actual source/qualification errors would still require a directed repair, not relabelling as a negative result.

The maintained R135 body/model/algorithm appendices, supplement and references form the current formal draft, with new experiments organized by question. Actual PDF export/visual QA and final independent integration are recorded separately before delivery. Remaining author facts: HGA-TGBC current authors/affiliations/status; this paper's author order/affiliations; old CITI443 capture URL/date/selection provenance. No author fact is invented, and no email/submission is performed.
