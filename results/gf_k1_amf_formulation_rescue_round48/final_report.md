# Round 48 final report

## Outcome

Round 48 is complete on the contractually bounded-negative pathway. The primary offline gate failed because the frozen equal-weight AMF score retained B1 and B2. All eight Stage 3 diagnostic rows were completed; Stage 4/5 were correctly not entered. Structural classification is `amf_partial_structural_separation`; the K1 decision is `bounded_negative_k1_amf`.

## Direct answers

1. The formulation profile includes `Y`, `r`, `e`, `h`, `bit`, `prod`, `p`, `d`, and `W_SP`, with equal per-variable weight.
2. `G` and G-only aliases were fully excluded; every live decision logged one excluded G coordinate and zero G credit.
3. Exact `phi_L/phi_R` values for all H/B/U/T states are in `formulation_contraction_census.csv`; they range by formulation and state, not by tuned family policy.
4. No. The unchanged tau retains H1/H2 but also B1/B2; it splits B3/B4.
5. The harmful controls were retained; the major row had no action change, though it did not certify at 300 seconds.
6. No. Strong control had zero rescues and no Stage 3 certificate.
7. Yes. V10 M3 retained and certified exactly with historical Work 8.9915.
8. No. The numerical endpoint had no rescue and remained uncertified at gap 2.02e-7.
9. No. V12 M2 exactly reproduced Work 38.8087, while the matched midpoint replay needed Work 9.6512.
10. tight3102 has two exact common historical states; the first and only action divergence is byte-identical `L0.0`.
11. Yes. MIDPOINT was exact in 789.31 s/Work 1500.20; RETAIN capped in 1180.03 s/Work 2444.85/gap 0.07428.
12. No. AMF retained `L0.0` and logged no live rescue.
13. No. The Stage 3 tight3102 gap was 0.0983631021.
14. Not tested: only seed3201 was eligible for Stage 3 and it did not certify; seed3202 was behind the closed later stage.
15. moderate3301 was behaviorally preserved but its Stage 3 gap 0.0476286277 exceeded 0.025.
16. Formulation rescue decisions: 0 across 12 AMF decisions.
17. Invalid-profile AM fallbacks: 0.
18. Extra score solves: zero LP and zero MIP.
19. No adjustable parameter entered; tau remains 0.07915.
20. K1-AMF does not establish an advantage over P-GRB; classification is `k1_amf_pgrb_negative`.
21. It failed to recover the tight3102 split/certificate achieved historically by K1-r015.
22. It was behaviorally identical to K1-AM on all 12 observed decisions.
23. It remains materially behind K4-AMC on strong control, V12 M2, and tight3102 historical evidence.
24. The four additional instances were not opened because the offline gate failed; their P-GRB references remain hash-audited.
25. No. K1-AMF is not ready to become the main research algorithm.
26. Longer-horizon candidate behavior, the three existing V20 confirmation rows, and the four additional instances remain deliberately unproven because their entry conditions failed.

## Stage 3

| instance | certificate | work | time_seconds | relative_gap | split_count | formulation_rescue_count | invalid_profile_fallback_count |
|---|---|---|---|---|---|---|---|
| round39_small_medium_V12_M3_Q30_slot08_seed1343324363 | False | 608.1906833850892 | 280.1459382 | 0.061236860738835275 | 0 | 0 | 0 |
| round39_small_hard_V12_M3_Q30_slot08_seed1288546114 | False | 501.2736815547833 | 280.1429555 | 0.16025130118073339 | 0 | 0 | 0 |
| round39_small_hard_V10_M3_Q20_slot04_seed1145042375 | True | 8.991485297269257 | 6.8888414 | 4.400898038348613e-16 | 0 | 0 | 0 |
| round39_small_hard_V12_M3_Q20_slot07_seed621538683 | False | 188.18035718118418 | 98.6550938 | 2.0161571633704306e-07 | 0 | 0 | 0 |
| round39_small_hard_V12_M2_Q20_slot06_seed258908503 | True | 38.80867136188028 | 24.4513781 | 1.886388367463341e-15 | 0 | 0 | 0 |
| high_imbalance_seed3201 | False | 496.39875876404045 | 280.1753366 | 0.03638375732777625 | 4 | 0 | 0 |
| moderate_seed3301 | False | 452.5965038170597 | 280.1338084 | 0.04762862766232296 | 1 | 0 | 0 |
| tight_T_seed3102 | False | 534.3143530811973 | 280.1377518 | 0.09836310212986069 | 1 | 0 | 0 |

No entered-stage row is missing. There were 2/8 strict certificates and zero false certificates. Artifact hash audit: PASS.
