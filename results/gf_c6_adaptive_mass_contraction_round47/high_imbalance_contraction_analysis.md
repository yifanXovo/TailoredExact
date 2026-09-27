# high_imbalance_seed3201 contraction analysis

K4-AMC performed one exact contraction and certified with the same Work/model path as K4-AM in Stage 4; it did not independently improve that row. Both Stage 5 finalists certified and retained the useful refinement. The contraction benefit here is proof-bookkeeping exactness, not measured runtime improvement.

| algorithm | certificate | work | time_seconds | gap | gi_300 | gi_1200 | gi_1800 | contraction_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gamma-veto | True | 1138.0330315218748 | 589.9931994 | 3.002423720451883e-10 | 0.09773331541347871 | 0.02676883974250682 |  | 0 |
| no-adaptive | True | 1135.9892958215353 | 668.2827082 | 3.002423720451883e-10 | 0.780082354909332 | 0.4124235680469337 |  | 0 |
| K1-r015 | True | 970.6039194826874 | 539.8320984 | 3.635005563669461e-16 | 0.0757419473252554 | 0.025506474259755486 | 0.017004316173170324 | 0 |
| K4-r001 | True | 710.8503886196801 | 390.3545002 | 5.872351488108015e-10 | 0.10199468378173344 | 0.027723277689208025 | 0.018482185126138685 | 0 |
| K4-r050 | True | 710.8503886196801 | 381.8246935 | 5.872351488108015e-10 | 0.10143837537911995 | 0.02716538093350767 | 0.01811025395567178 | 0 |
| P-GRB | False | 3581.442796133532 | 1780.0888304 | 0.1148869902505325 | 0.16842320217850698 | 0.14992386106779754 | 0.14016361479485587 | 0 |
| K1-AM | True | 970.604 | 522.356 | 3.63501e-16 | 0.0754317 | 0.0249154 | 0.0166103 | 0 |
| K4-AMC | True | 710.85 | 380.823 | 5.87235e-10 | 0.100997 | 0.0270123 | 0.0180082 | 1 |
