# Round 47 final report

## Outcome

Round 47 completed the frozen lightweight C6 adaptive-mass screen and confirmation study: 40/40 Stage 3 rows, 40/40 Stage 4 rows, and 28/28 Stage 5 rows. There were 65 strict certificates, zero false certificates, 44 exact one-child contractions, and zero score-only LP or MIP queries. All rows used one executable and the common `tau=0.07915`.

- Gate: `adaptive_mass_gate_supported`
- Contraction: `single_child_contraction_supported`
- K4: `k4_amc_candidate_supported`; selected `K4-AMC`
- K1: `k1_am_pgrb_competitive`; selected `K1-AM`
- Combined: `unified_c6_lite_candidate_supported`
- Scale: `v20_mixed`
- Paper-facing default: unchanged original C6

## Structural result and frozen threshold

The actual K4 major critical parent state was `L2` with endpoints `0.024734341307209723` to `0.037101511960814584`, parent bound 0.03780275497702865, child bounds 0.03915480507982754 and 0.04195718808659905, and incumbent 0.04500155005562836. Its values were `eta=0.18781616757201625`, `mu=0.38245867205879625`, and `S_AM=0.07183192204076569`.

The four primary scores were H1=0.07183192204076569, H2=0.04934038507297367, B1=0.0864677355921028, and B2=0.14965605158606354. Because `H_max=0.07183192204076569 < B_min=0.0864677355921028` and 0.07 was outside that open interval, the deterministic midpoint was rounded inward to 0.07915. One common tau therefore rejected both harmful primary decisions and retained both useful K1 decisions.

## Runtime answers

1. AM/AMC used only the already-computed midpoint child LP outcomes; all 108 official rows report zero extra LP and MIP queries.
2. The old one-infeasible-child path was not operationally equivalent: it materialized two children and later discarded the infeasible sibling. AMC instead performed atomic exact one-child replacement and kept a separate contraction counter.
3. AMC produced 44 strict contractions. The frozen Stage 4 attribution test found a measurable proof-safe gain for K4=True and K1=False. On high_imbalance_seed3201, K4-AMC contracted once but had identical certified Work to K4-AM; on moderate_seed3301 it contracted once and reduced capped Work slightly. The evidence supports contraction, but the benefit is local rather than a broad performance win.
4. K4 preserved the strong-control certificate and high-imbalance certificate. K1 repaired the major witness and remained substantially ahead of historical P-GRB on the strong control, although it remained slower than K4 there.
5. Against historical K4-rho=0.50 and corrected gamma-veto, the adaptive-mass gate reproduced the desired major-tail behavior using no extra score solve. Comparisons are historical, paired by instance, Work, certificate, gap, and GI; wall time is contextual.
6. V20 is mixed: both finalists certify high_imbalance_seed3201 and the withheld high_imbalance_seed3202, while some tight/moderate rows still cap. This is screening evidence, not paper validation.
7. The same tau is viable for K1 and K4, but the selected variants differ: `K4-AMC` and `K1-AM`. Original C6 remains the default because the bounded mixed-scale study does not justify silent replacement.

## Key paired evidence

| instance | algorithm | certificate | work | time_seconds | gap | gi_300 | gi_1200 | gi_1800 | contraction_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| high_imbalance_seed3201 | gamma-veto | True | 1138.0330315218748 | 589.9931994 | 3.002423720451883e-10 | 0.09773331541347871 | 0.02676883974250682 |  | 0 |
| high_imbalance_seed3201 | K4-r001 | True | 710.8503886196801 | 390.3545002 | 5.872351488108015e-10 | 0.10199468378173344 | 0.027723277689208025 | 0.018482185126138685 | 0 |
| high_imbalance_seed3201 | K4-r050 | True | 710.8503886196801 | 381.8246935 | 5.872351488108015e-10 | 0.10143837537911995 | 0.02716538093350767 | 0.01811025395567178 | 0 |
| high_imbalance_seed3201 | P-GRB | False | 3581.442796133532 | 1780.0888304 | 0.1148869902505325 | 0.16842320217850698 | 0.14992386106779754 | 0.14016361479485587 | 0 |
| high_imbalance_seed3201 | K1-AM | True | 970.604 | 522.356 | 3.63501e-16 | 0.0754317 | 0.0249154 | 0.0166103 | 0 |
| high_imbalance_seed3201 | K4-AMC | True | 710.85 | 380.823 | 5.87235e-10 | 0.100997 | 0.0270123 | 0.0180082 | 1 |
| moderate_seed3301 | gamma-veto | False | 6492.454849036278 | 3580.0764596 | 0.061589268575746446 | 0.2215057288023054 | 0.10156838363238635 |  | 0 |
| moderate_seed3301 | K4-r001 | False | 2911.2260925812884 | 1780.0343577 | 0.1123420662725595 | 0.24072587091960349 | 0.14443801743432053 | 0.13373936704706685 | 0 |
| moderate_seed3301 | K4-r050 | False | 2022.1846115019607 | 1180.0343519 | 0.1123420662725595 | 0.23882025789795255 | 0.14396161417890777 | 0.13342176487679167 | 0 |
| moderate_seed3301 | P-GRB | False | 2813.2073928664922 | 1780.1102671 | 0.02292271188532521 | 0.055935779911182544 | 0.031175978891789698 | 0.028424889889635017 | 0 |
| moderate_seed3301 | K1-AM | False | 3348.95 | 1780.05 | 0.0241661 | 0.216757 | 0.0727888 | 0.0565812 | 0 |
| moderate_seed3301 | K4-AMC | False | 3078.18 | 1780.03 | 0.112342 | 0.24144 | 0.144616 | 0.133858 | 1 |
| round39_small_hard_V12_M3_Q30_slot08_seed1288546114 | gamma-veto | True | 168.80494107524342 | 98.4825417 | 3.837100765558795e-14 |  |  |  | 0 |
| round39_small_hard_V12_M3_Q30_slot08_seed1288546114 | K4-r001 | True | 133.73490192498448 | 78.8809124 | 3.0696806124470356e-15 | 0.07099692172749544 | 0.01774923043187386 | 0.011832820287915907 | 0 |
| round39_small_hard_V12_M3_Q30_slot08_seed1288546114 | K4-r050 | True | 133.73490192498448 | 76.8689995 | 3.0696806124470356e-15 | 0.06923385982518042 | 0.017308464956295105 | 0.01153897663753007 | 0 |
| round39_small_hard_V12_M3_Q30_slot08_seed1288546114 | P-GRB | True | 3152.2339036687963 | 1739.1272517 | 5.701105555009818e-09 | 0.6509596068347505 | 0.3813393441214354 | 0.28361498587198525 | 0 |
| round39_small_hard_V12_M3_Q30_slot08_seed1288546114 | K1-AM | True | 740.634 | 408.96 | 4.08287e-08 | 0.211156 | 0.063204 | 0.042136 | 0 |
| round39_small_hard_V12_M3_Q30_slot08_seed1288546114 | K4-AMC | True | 133.735 | 76.7516 | 3.06968e-15 | 0.0691552 | 0.0172888 | 0.0115259 | 0 |
| round39_small_medium_V12_M3_Q30_slot08_seed1343324363 | gamma-veto | True | 1353.2173542119708 | 618.7428876 | 1.5419233104925857e-15 |  |  |  | 0 |
| round39_small_medium_V12_M3_Q30_slot08_seed1343324363 | K4-r001 | True | 3898.1509266770327 | 1780.0433176 | 1.3877309794433272e-14 | 0.26022138147536894 | 0.12893376245601398 | 0.08595584163734266 | 0 |
| round39_small_medium_V12_M3_Q30_slot08_seed1343324363 | K4-r050 | True | 1571.4256243238797 | 697.5631388 | 1.3877309794433272e-14 | 0.26019059137641276 | 0.12088527582720826 | 0.08059018388480552 | 0 |
| round39_small_medium_V12_M3_Q30_slot08_seed1343324363 | P-GRB | True | 1568.0170733870093 | 1009.0487443 | 0.0 | 0.12217803475016592 | 0.06274851900205322 | 0.041832346001368814 | 0 |
| round39_small_medium_V12_M3_Q30_slot08_seed1343324363 | K1-AM | True | 843.456 | 384.604 | 1.54192e-15 | 0.20309 | 0.0593538 | 0.0395692 | 0 |
| round39_small_medium_V12_M3_Q30_slot08_seed1343324363 | K4-AMC | True | 1571.43 | 694.616 | 1.38773e-14 | 0.260195 | 0.120389 | 0.0802593 | 0 |

## Remaining uncertainty

No V50 evidence was opened, timing near hard caps is noisy, historical comparators were not rerun, and contraction gains were sparse. The result supports a unified lightweight research candidate, not a validated paper algorithm or a default change.
