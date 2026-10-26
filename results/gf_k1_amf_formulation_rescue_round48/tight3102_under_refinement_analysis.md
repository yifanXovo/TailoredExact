# tight3102 under-refinement analysis

Instance: `tight_T_seed3102`. Historical terminal Work/time may use longer caps; GI(300) is the common-horizon field where available.

| algorithm | certificate | work | time_seconds | gap | gi_300 |
|---|---|---|---|---|---|
| K1-AMF (300s) | False | 534.3143530811973 | 280.1377518 | 0.09836310212986069 | 0.19948422116092715 |
| K1-AM (historical) | False | 3788.5503848518583 | 1780.0436949 | 0.06518359542931032 |  |
| K1-r015 (historical) | True | 1306.2494797021486 | 680.7626373 | 0.0 | 0.19882415144314974 |
| K4-AMC (historical) | True | 1306.4235957628575 | 657.7708206 | 0 |  |
| K4-r001 (historical) | True | 1306.4235957628575 | 671.3993915 | 0.0 | 0.18282115900543314 |
| P-GRB (historical) | False | 3525.038650246663 | 1780.0985846 | 0.1430227469394783 | 0.5909249034782592 |

At byte-identical state L0.0, one-step MIDPOINT completed exact in 789.31 s (Work 1500.20) while RETAIN capped at 1180.03 s (Work 2444.85, gap 0.07428). AMF nevertheless retained and the Stage 3 row had no rescue or certificate.
