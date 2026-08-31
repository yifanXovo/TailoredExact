# Round 56 final report

Status: **round56_complete**. Classification: **paper-candidate screening panel**; final-paper evidence: **no**.

## Final classifications

- Engineering: `scenario_identity_bug_fixed`
- Dataset: `paper_candidate_screen_complete`
- Route archive: `native_route_archive_complete`
- Time horizon: `mixed_t_sensitivity`
- Scale: `v8_v12_v20_v30_v50_screen_complete`
- Mainline: `corrected_k1_am_sf_retained`

## Engineering answers

No T-propagation or cache-identity defect was found: parent, midpoint-child, native-target, exact-parent, exact-child, movement-domain, valid-inequality, verifier, cache, artifact, and mathematical-instance paths use the requested operational T. Solver process caps are distinct run-identity metadata and do not alter the mathematical model.

The pre-run generator audit did find that its first draft calculated distances before rounding serialized coordinates; those inputs were discarded and regenerated before any optimizer result. The stable result format also lacked explicit T/process/service/distance/scenario/run identity fields; source-freeze commit `75e58521158aba8628ebc9444444ec3841415285` added them. Neither issue changes historical numerical evidence. Travel and service durations are seconds under the repository's frozen travel/service-time convention; no unsupported physical-speed interpretation is made.

All five landscapes and all 50 scenario identities were frozen before performance execution. M variants preserve station data and differ only in fleet metadata; Q variants differ only in vehicle capacities. The sole evaluated algorithm is the frozen corrected K1-AM-SF identity recorded in `final_decision.json`; no VD-P or other research candidate was enabled.

## Completion and certificate answers

All 40 Q=30 rows and all 10 Q=20 rows completed. Certified by 300/1200/3600 seconds: 32/38/40. Final certified rows: 40; additional post-3600 certificates from the predeclared 7200-second extensions: 0; capped noncertified rows: 10.

Verified incumbents: 50. Exact native packages: 40; nonexact incumbent packages: 10; archive-verification failures: 0. Correctness failures: 0; false certificates: 0.

## Exact objectives

The following values are claimed exact only because each row passed every strict certificate and independent original-solution check.

| Scenario | V | M | Q | T | Exact objective | Wall s |
|---|---|---|---|---|---|---|
| r56_V08_M01_Q30_T01800_seed1760458116 | 8 | 1 | 30 | 1800 | 0.8253299456049881 | 0.6127782 |
| r56_V08_M01_Q30_T03600_seed1760458116 | 8 | 1 | 30 | 3600 | 0.16718733824082452 | 2.290729 |
| r56_V08_M01_Q30_T10800_seed1760458116 | 8 | 1 | 30 | 10800 | 0.05068723780300001 | 7.4526475 |
| r56_V08_M01_Q30_T18000_seed1760458116 | 8 | 1 | 30 | 18000 | 0.05068723780300001 | 7.5651894 |
| r56_V08_M02_Q30_T01800_seed1760458116 | 8 | 2 | 30 | 1800 | 0.7460790560242729 | 2.6557413 |
| r56_V08_M02_Q30_T03600_seed1760458116 | 8 | 2 | 30 | 3600 | 0.05068723780300001 | 2.4984084 |
| r56_V08_M02_Q30_T10800_seed1760458116 | 8 | 2 | 30 | 10800 | 0.05068723780300001 | 8.4621011 |
| r56_V08_M02_Q30_T18000_seed1760458116 | 8 | 2 | 30 | 18000 | 0.05068723780300001 | 8.8176395 |
| r56_V12_M02_Q30_T01800_seed1330133768 | 12 | 2 | 30 | 1800 | 1.1340891813875853 | 2.6998879 |
| r56_V12_M02_Q30_T03600_seed1330133768 | 12 | 2 | 30 | 3600 | 0.021036848059428515 | 29.6911617 |
| r56_V12_M02_Q30_T10800_seed1330133768 | 12 | 2 | 30 | 10800 | 0 | 11.2981433 |
| r56_V12_M02_Q30_T18000_seed1330133768 | 12 | 2 | 30 | 18000 | 0 | 11.6385193 |
| r56_V12_M03_Q30_T01800_seed1330133768 | 12 | 3 | 30 | 1800 | 1.092965682480849 | 26.9533946 |
| r56_V12_M03_Q30_T03600_seed1330133768 | 12 | 3 | 30 | 3600 | 0 | 3.0048033 |
| r56_V12_M03_Q30_T10800_seed1330133768 | 12 | 3 | 30 | 10800 | 0 | 10.9357348 |
| r56_V12_M03_Q30_T18000_seed1330133768 | 12 | 3 | 30 | 18000 | 0 | 11.7157553 |
| r56_V20_M02_Q30_T01800_seed1716808955 | 20 | 2 | 30 | 1800 | 0.7934466380778933 | 19.114083 |
| r56_V20_M02_Q30_T03600_seed1716808955 | 20 | 2 | 30 | 3600 | 0.3717255766344526 | 975.0792485 |
| r56_V20_M02_Q30_T10800_seed1716808955 | 20 | 2 | 30 | 10800 | 0.09017647944383858 | 74.4388098 |
| r56_V20_M02_Q30_T18000_seed1716808955 | 20 | 2 | 30 | 18000 | 0.09017647944383858 | 123.8000057 |
| r56_V20_M03_Q30_T01800_seed1716808955 | 20 | 3 | 30 | 1800 | 0.6751180048294522 | 1702.8114703 |
| r56_V20_M03_Q30_T10800_seed1716808955 | 20 | 3 | 30 | 10800 | 0.09017647944383858 | 96.8407944 |
| r56_V20_M03_Q30_T18000_seed1716808955 | 20 | 3 | 30 | 18000 | 0.09017647944383858 | 118.30144 |
| r56_V30_M03_Q30_T01800_seed913438282 | 30 | 3 | 30 | 1800 | 1.0068964255293749 | 638.2994079 |
| r56_V30_M03_Q30_T10800_seed913438282 | 30 | 3 | 30 | 10800 | 0 | 85.7778883 |
| r56_V30_M03_Q30_T18000_seed913438282 | 30 | 3 | 30 | 18000 | 0 | 92.0740594 |
| r56_V30_M04_Q30_T10800_seed913438282 | 30 | 4 | 30 | 10800 | 0 | 69.8236999 |
| r56_V30_M04_Q30_T18000_seed913438282 | 30 | 4 | 30 | 18000 | 0 | 59.230436 |
| r56_V50_M04_Q30_T10800_seed811442003 | 50 | 4 | 30 | 10800 | 0.000806920182961692 | 463.9906435 |
| r56_V50_M04_Q30_T18000_seed811442003 | 50 | 4 | 30 | 18000 | 0.000806920182961692 | 292.1502432 |
| r56_V50_M05_Q30_T10800_seed811442003 | 50 | 5 | 30 | 10800 | 0.000806920182961692 | 372.4075655 |
| r56_V50_M05_Q30_T18000_seed811442003 | 50 | 5 | 30 | 18000 | 0.000806920182961692 | 566.0676471 |
| r56_V08_M01_Q20_T03600_seed1760458116 | 8 | 1 | 20 | 3600 | 0.16718733824082452 | 2.2778345 |
| r56_V08_M01_Q20_T18000_seed1760458116 | 8 | 1 | 20 | 18000 | 0.05068723780300001 | 6.6481174 |
| r56_V12_M02_Q20_T03600_seed1330133768 | 12 | 2 | 20 | 3600 | 0.026944794628078462 | 18.2972343 |
| r56_V12_M02_Q20_T18000_seed1330133768 | 12 | 2 | 20 | 18000 | 0 | 5.2119334 |
| r56_V20_M02_Q20_T03600_seed1716808955 | 20 | 2 | 20 | 3600 | 0.37419399786877516 | 1595.6422119 |
| r56_V20_M02_Q20_T18000_seed1716808955 | 20 | 2 | 20 | 18000 | 0.09075714169047969 | 110.9910695 |
| r56_V30_M03_Q20_T18000_seed913438282 | 30 | 3 | 20 | 18000 | 0.006455267165005543 | 90.2137009 |
| r56_V50_M04_Q20_T18000_seed811442003 | 50 | 4 | 20 | 18000 | 0.06129717814315671 | 375.1900755 |

## Sensitivity and native routes

Exact monotonicity violations for T/M/Q: 0/0/0. The plateau table records the first tested plateau T only for fully certified series; noncertified endpoints are excluded from exact claims. Objective and final-inventory changes from T=3600 to T=10800 and T=18000 are recorded directly in `final_inventory_transition.csv`.

Native route durations, T utilization, vehicle use, visited stations, pickup/drop/depot-unload counts, and bicycle handling are reported in `paper_candidate_route_table.csv`. They describe exactly one native final solver witness per scenario. No post-certificate or objective-equivalent route optimization was performed; none of these durations is a shortest-route or minimum-duration claim.

V30/V50 results form the large-scale screening regime and are retained at both the common 3600-second comparison and prescribed final caps. The later replicated dataset should retain every structural V/M/Q/T stratum and add multiple independently frozen base landscapes per V; it must not select cells according to Round 56 convergence or favorable outcomes.

## What remains unproven

One base landscape per V cannot support final statistical generalization, universal scalability, or causal claims about all instances. Capped rows remain nonoptimal even when they have verified native incumbents. Route-witness duration is not the minimum duration compatible with the objective. Round 56 therefore is not ready to be called final paper evidence.
