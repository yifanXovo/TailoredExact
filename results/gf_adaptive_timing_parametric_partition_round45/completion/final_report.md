# Round 45 completion report

Status: **complete**

- Timing classification: `bounded_negative_timing_mechanism`
- Point classification: `parametric_point_inconclusive_insufficient_true_split_evidence`
- Final algorithm classification: `bounded_systematic_negative_result`
- Scale qualification: `v20_v50_supported`
- Required runtime rows: 232/232
- Fresh true counterfactual parents: 30 development and 2 post-selection
- Development labels: 3 beneficial, 21 harmful, 4 neutral, 2 inconclusive
- Gamma-veto false splits / false retains: 7 / 2
- False certificates: 77
- Complex mandatory rows: 48/48

## Required questions

1. **Prior label:** withdrawn. The old strong-control L3 trajectory had zero
   full-instance splits and is not a verified split counterfactual.
2. **Fresh matched evidence:** 30 development
   and 2 post-selection parents, each with
   retain, midpoint, PMM, and FPMM arms.
3. **Development labels:** 3 beneficial,
   21 harmful, 4 neutral, and
   2 inconclusive.
4. **Gamma-veto beneficial action:** 1 true
   beneficial parents split.
5. **Major harmful action:** retained = False.
6. **Corrected D_R43:** false splits 6, false retains
   1, weighted oracle regret
   0.0120865; gamma-veto weighted regret
   1.32151.
7. **Gamma-veto versus no-adaptive on useful splits:** gamma weighted regret
   1.32151 versus no-adaptive
   1.34246.
8. **Point coverage:** all gamma-veto development split parents have all three
   split-point arms = True.
9. **Parametric improvement on beneficial parents:**
   0 material 15% improvements over midpoint.
10. **Implementation tested:** monotone-root PMM/FPMM only; live basis
    continuation was not used.
11. **Frozen complex matrix:** 48/48 mandatory
    rows and 6/6 D_R43 rows completed.
12. **Cap integrity:** 40 honest caps; every capped marker passed the
    3570-second minimum finalization-tolerance check.
13. **Common horizons:** 300s pgrb: 0/12 certificates, mean GI 0.356565; 300s c6: 2/12 certificates, mean GI 0.332884; 300s gamma-veto: 1/12 certificates, mean GI 0.337757; 300s no-adaptive: 1/12 certificates, mean GI 0.752308; 1200s pgrb: 0/12 certificates, mean GI 0.306271; 1200s c6: 4/12 certificates, mean GI 0.168222; 1200s gamma-veto: 4/12 certificates, mean GI 0.170776; 1200s no-adaptive: 4/12 certificates, mean GI 0.578983; 3600s pgrb: 0/12 certificates, mean GI 0.270136; 3600s c6: 6/12 certificates, mean GI 0.110016; 3600s gamma-veto: 5/12 certificates, mean GI 0.11471; 3600s no-adaptive: 6/12 certificates, mean GI 0.437903.
14. **C6 advantage retention at 3600 s:** high_imbalance_seed3201=1.001, high_imbalance_seed3202=0.9991, moderate_seed3301=-4.561e+10, moderate_seed3302=0.9984, round32_multi_m_high_imbalance_V50_M2_seed910922492=0.899, round32_multi_m_high_imbalance_V50_M4_seed163456187=0.9937, round32_multi_m_moderate_V50_M2_seed254020866=0.9178, round32_multi_m_moderate_V50_M4_seed721910669=0.9751, round32_multi_m_tight_T_V50_M2_seed104207248=0.8711, round32_multi_m_tight_T_V50_M4_seed1562257203=0.9959, tight_T_seed3101=0.897, tight_T_seed3102=0.9986.
15. **K1 beyond strong control:** 18/18 rows completed; K1 exact
    8/9 and K4 exact 9/9.
16. **Certificate scope:** 69 strict original-problem certificates,
    123 exact restricted-parent certificates, and 40
    honest capped rows; false certificates = 77.
17. **Timing conclusion:** `bounded_negative_timing_mechanism`.
18. **Point conclusion:** `parametric_point_inconclusive_insufficient_true_split_evidence`.
19. **What remains unproven:** the classification and scale qualification above
    delimit the evidence. Counterfactual exactness does not certify the original
    problem, and the point study does not claim live-basis continuation.

## Contemporaneous sentinels

- Major harmful witness: pgrb: Work 0, 1024.383 s, exact; c6: Work 4373.08, 1946.197 s, exact; gamma-veto: Work 1353.22, 614.165 s, exact; no-adaptive: Work 1349.61, 613.080 s, exact
- Strong K4 control: pgrb: Work 0, 1735.198 s, exact; c6: Work 133.735, 76.742 s, exact; gamma-veto: Work 168.805, 98.471 s, exact; no-adaptive: Work 164.063, 95.870 s, exact

All claims are derived from the sealed completion matrix and its gate audits.
