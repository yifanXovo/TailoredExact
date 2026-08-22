# Round 46 final report

## Outcome

Round 46 is complete as a focused small/V20 C6 threshold screen. All mandatory rows completed with zero false certificates, one official executable, midpoint-only splits, and all forbidden mechanisms off.

- K4 classification: `k4_rho_001_retained`
- K1 classification: `k1_not_competitive`
- Combined classification: `rho_threshold_does_not_replace_gamma_information`
- Scale qualification: `v20_mixed`
- Best K4 rho: **0.01** (mainline retained)
- Best K1 rho: **0.15** (diagnostic/local repair only)

## Conclusions

1. Rho values at or above 0.12 rejected the observed K1/K4 startup/major immediate-split opportunities when their measured gain fell below threshold. The full-tree major repair was clearest for K1 at rho 0.15 and for K4 only at rho 0.50 in Stage 4; K4-r012 did not reproduce a performance gain in Stage 5.
2. Rho 0.15 behaved as expected for K1: it repaired the major witness (385.5 s, 843.46 work), but it did not make K1 competitive on the strong control or aggregate V20 evidence.
3. The high-imbalance seed3201 beneficial refinement was preserved by all Stage 4 finalists; K4 remained materially faster than K1.
4. No nonbaseline rho improved moderate_seed3301 consistently. K4-r012 used more Stage 5 work than K4-r001, and K1-r015 was worse again.
5. A split-gain interval can separate particular harmful and beneficial decisions, but that local separation did not yield a single robust runtime threshold.
6. Higher rho both reduced some immediate splits and shifted work into native-target MIPs; rho 0.50 was overconservative on multiple witnesses.
7. Pure C6-rho cannot replace gamma-veto information on this evidence. The paper-facing rho 0.01 preset remains unchanged.
8. P-GRB certified the major and strong witnesses at 1800 s but failed every V20 development and withheld confirmation row. C6 certified high seed3201 and two of three withheld V20 instances, preserving a substantial nontrivial advantage.

## Stage 5 key rows

| instance | arm | certificate | time_seconds | work | relative_gap | gi_300 | gi_1200 | gi_1800 | split_count | native_target_jobs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| high_imbalance_seed3201 | K1-r015 | True | 539.832 | 970.604 | 3.63501e-16 | 0.0757419 | 0.0255065 | 0.0170043 | 4 | 5 |
| high_imbalance_seed3201 | K4-r001 | True | 390.355 | 710.85 | 5.87235e-10 | 0.101995 | 0.0277233 | 0.0184822 | 1 | 3 |
| high_imbalance_seed3201 | K4-r012 | True | 381.503 | 710.85 | 5.87235e-10 | 0.102392 | 0.0273933 | 0.0182622 | 1 | 3 |
| high_imbalance_seed3201 | P-GRB | False | 1780.09 | 3581.44 | 0.114887 | 0.168423 | 0.149924 | 0.140164 | 0 | 0 |
| moderate_seed3301 | K1-r015 | False | 1780.04 | 3161.82 | 0.0241661 | 0.219544 | 0.0736341 | 0.0571448 | 1 | 2 |
| moderate_seed3301 | K4-r001 | False | 1780.03 | 2911.23 | 0.112342 | 0.240726 | 0.144438 | 0.133739 | 1 | 3 |
| moderate_seed3301 | K4-r012 | False | 1780.04 | 3055.54 | 0.112342 | 0.241695 | 0.14468 | 0.133901 | 1 | 3 |
| moderate_seed3301 | P-GRB | False | 1780.11 | 2813.21 | 0.0229227 | 0.0559358 | 0.031176 | 0.0284249 | 0 | 0 |
| round39_small_hard_V12_M3_Q30_slot08_seed1288546114 | K1-r015 | True | 417.065 | 740.634 | 4.08287e-08 | 0.211299 | 0.0640993 | 0.0427328 | 0 | 0 |
| round39_small_hard_V12_M3_Q30_slot08_seed1288546114 | K4-r001 | True | 78.8809 | 133.735 | 3.06968e-15 | 0.0709969 | 0.0177492 | 0.0118328 | 0 | 4 |
| round39_small_hard_V12_M3_Q30_slot08_seed1288546114 | K4-r012 | True | 76.841 | 133.735 | 3.06968e-15 | 0.0694693 | 0.0173673 | 0.0115782 | 0 | 4 |
| round39_small_hard_V12_M3_Q30_slot08_seed1288546114 | P-GRB | True | 1739.13 | 3152.23 | 5.70111e-09 | 0.65096 | 0.381339 | 0.283615 | 0 | 0 |
| round39_small_medium_V12_M3_Q30_slot08_seed1343324363 | K1-r015 | True | 385.476 | 843.456 | 1.54192e-15 | 0.203279 | 0.0594992 | 0.0396661 | 0 | 1 |
| round39_small_medium_V12_M3_Q30_slot08_seed1343324363 | K4-r001 | True | 1780.04 | 3898.15 | 1.38773e-14 | 0.260221 | 0.128934 | 0.0859558 | 1 | 4 |
| round39_small_medium_V12_M3_Q30_slot08_seed1343324363 | K4-r012 | True | 1780.03 | 4016.89 | 1.38773e-14 | 0.260243 | 0.124886 | 0.0832571 | 1 | 4 |
| round39_small_medium_V12_M3_Q30_slot08_seed1343324363 | P-GRB | True | 1009.05 | 1568.02 | 0 | 0.122178 | 0.0627485 | 0.0418323 | 0 | 0 |

## Remaining uncertainty

This is a bounded small/V20 screening study, not paper validation. Timing variability near hard caps is material, no V50 evidence was opened, and the best K1/K4 thresholds differ. The Round 45 gamma-veto comparison remains historical context only.
