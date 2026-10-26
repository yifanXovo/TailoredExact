# Round 49 final report — K1 LP primal-dual rescue

## Outcome

Round 49 is complete on the bounded-negative pathway. The mandatory offline gate failed before runtime, so exactly one diagnostic `D-RCD` arm completed all 8 Stage 3 rows; Stage 4 and Stage 5 were not eligible. Classification: `rc_domain_partial_separation`, `bounded_negative_rc_rescue`, `bounded_negative_k1_am_rc`, `k1_am_rc_pgrb_mixed`, `small_only`.

## Stage 3 summary

| instance | certificate | work | time_seconds | relative_gap | gi_300 | rc_decision_count | rc_rescue_count | invalid_profile_fallback_count | primitive_variable_count |
|---|---|---|---|---|---|---|---|---|---|
| round39_small_medium_V12_M3_Q30_slot08_seed1343324363 | False | 572.9717930762271 | 280.3558027 | 0.17246527268384873 | 0.1980374905410892 | 10 | 10 | 0 | 660 |
| round39_small_hard_V12_M3_Q30_slot08_seed1288546114 | False | 493.9431664197442 | 280.1618599 | 0.16025130118073339 | 0.21180867663098216 | 1 | 0 | 0 | 660 |
| round39_small_hard_V10_M3_Q20_slot04_seed1145042375 | True | 8.991485297269257 | 6.9979185 | 4.400898038348613e-16 | 0.009565543581811402 | 1 | 0 | 0 | 490 |
| round39_small_hard_V12_M3_Q20_slot07_seed621538683 | False | 188.18035718118418 | 100.3381352 | 2.0161571633704306e-07 | 0.10046507030661964 | 1 | 0 | 0 | 660 |
| round39_small_hard_V12_M2_Q20_slot06_seed258908503 | True | 38.80867136188028 | 24.7879502 | 1.886388367463341e-15 | 0.013179526979404284 | 1 | 0 | 0 | 444 |
| high_imbalance_seed3201 | False | 502.630437458964 | 280.2432995 | 0.028232984417279963 | 0.06864324324110552 | 7 | 5 | 0 | 1580 |
| moderate_seed3301 | False | 469.2980239636761 | 280.1428221 | 0.05025585833078519 | 0.22475427271092074 | 2 | 1 | 0 | 1580 |
| tight_T_seed3102 | False | 493.9675765661061 | 280.2747903 | 0.06849765680838411 | 0.15679419587394652 | 9 | 8 | 0 | 1580 |

## Required questions

1. **Primitive variables:** routing arcs `x`, visit selections `z`, operation modes `mode`, pickup `p`, drop `d`, vehicle loads `load`, and final inventories `Y`.
2. **Duplicate/auxiliary exclusion:** yes; bit expansions, products/McCormick variables, selectors, Gini variables/aliases, duplicated semantics, continuous, and diagnostic variables were excluded by the frozen positive registry.
3. **Reduced costs without extra solves:** yes. All 32/32 live profiles used primal/RC/basis attributes copied after already-required LP optimizes; extra LP/MIP count was 0/0.
4. **Mandatory RC domains:** H1 and H3 contracted enough to trigger harmful rescues; H2/B1/B2/U1 remained full; B3/B4 retained their AM splits; T1 contracted and was rescued. Exact counts are in `reduced_cost_domain_census.csv`.
5. **D/H separation:** no. D and H produced identical mandatory actions and could not separate H1 from T1.
6. **Exact child separation:** no additional useful information; RCDS matched RCD on every mandatory state.
7. **Offline iterations:** two—D with RCD/RCDS, then H with RCD/RCDS. No other formula was attempted.
8. **Stage 3 revision:** no.
9. **Major and V10 M3:** V10 M3 was retained and certified; the major root was wrongly rescued and capped.
10. **Strong control:** not rescued; no intended improvement.
11. **Numerical endpoint:** not rescued; no intended improvement.
12. **V12 M2:** no rescue; exact Work 38.8087, behaviorally identical to K1-AM.
13. **tight3102:** the L0.0 beneficial split was recovered, but the 300-second row remained capped.
14. **High imbalance:** the existing AM root split was preserved; five later rescues altered 3201, which remained capped; 3202 was not opened.
15. **moderate3301:** root behavior was preserved, one later rescue occurred, and the 300-second row remained capped.
16. **RC rescues:** 24 across 32 decisions.
17. **Invalid fallbacks:** 0.
18. **Extra solves:** none—0 LP and 0 MIP/root-processing scoring solves.
19. **New adjustable parameters:** none; tau remains 0.07915.
20. **Versus K1-r015:** the direct table retains paired historical evidence, but the candidate is not promoted because mandatory action gates failed.
21. **Versus K1-AM:** identical on strong, V10, numerical, and V12 M2; different but harmful on major; mixed downstream changes on V20; locally beneficial at tight3102.
22. **Versus P-GRB:** historical advantage is mixed and not requalified at longer horizons.
23. **Versus K4-AMC:** the candidate remains materially behind on V12 M2 and lacks longer-horizon V20 qualification.
24. **V20:** 0/3 entered V20 rows certified at 300 seconds; the other 3 conditional rows were not opened, so no aggregate promotion claim is valid.
25. **Four unopened confirmations:** no live candidate rows by design; no confirmation claim.
26. **Sufficiency of LP primal-dual information:** not sufficient for a reliable K1 rescue within the bounded D/H, RCD/RCDS class.
27. **Ready as main research algorithm:** no; K1-AM is retained.
28. **Unproven:** longer-horizon effects of the locally useful tight3102 rescue and whether a different, pre-frozen parameter-free primal-dual invariant can separate H1 from T1.

## Integrity

All 8 entered rows are present and sealed, 2 strictly certified and 6 honestly non-certified/capped, with zero false certificates and zero artifact-hash failures. The official executable is `f73b40a12590ab432abc201f95fbcea70ba499337239f31175fba589ab0d8ed5`. Pre-existing tracked modifications and untracked user paths were not staged or altered by Round 49.
