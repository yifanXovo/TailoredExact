# Round 44 lookahead-policy ablation

Fixed-d1, frontier-d2, and the fixed-d2 causal reference are compared under the sealed Stage 2 solver contract.

| variant | witness | certified | Work/P-GRB | time/P-GRB | splits | terminal MIPs |
|---|---|---:|---:|---:|---:|---:|
| na-d1-all | major_fragmentation_regression | True | 1.0397 | 0.7963 | 0 | 3 |
| na-d1-all | strongest_k4_positive_control | True | 0.0158 | 0.0151 | 0 | 4 |
| na-frontier-all | major_fragmentation_regression | True | 0.8395 | 0.6546 | 0 | 3 |
| na-frontier-all | strongest_k4_positive_control | True | 0.0162 | 0.0158 | 0 | 4 |
| overlay-d1-all-parent | major_fragmentation_regression | True | 2.1310 | 1.6429 | 1 | 4 |
| overlay-d1-all-parent | strongest_k4_positive_control | True | 0.0158 | 0.0149 | 0 | 3 |
| overlay-frontier-all-parent | major_fragmentation_regression | True | 2.4708 | 1.9067 | 1 | 4 |
| overlay-frontier-all-parent | strongest_k4_positive_control | True | 0.0164 | 0.0157 | 0 | 3 |
| overlay-frontier-all-nested | major_fragmentation_regression | True | 2.4722 | 1.9091 | 1 | 4 |
| overlay-frontier-all-nested | strongest_k4_positive_control | True | 0.0164 | 0.0157 | 0 | 3 |
| overlay-frontier-violated-parent | major_fragmentation_regression | True | 2.4708 | 2.0124 | 1 | 4 |
| overlay-frontier-violated-parent | strongest_k4_positive_control | True | 0.0137 | 0.0141 | 0 | 3 |
| overlay-frontier-active-parent | major_fragmentation_regression | True | 4.4603 | 3.3890 | 1 | 4 |
| overlay-frontier-active-parent | strongest_k4_positive_control | True | 0.0137 | 0.0133 | 0 | 3 |
| overlay-d2-all-reference | major_fragmentation_regression | True | 2.4708 | 1.9058 | 1 | 4 |
| overlay-d2-all-reference | strongest_k4_positive_control | True | 0.0164 | 0.0157 | 0 | 3 |
