# Round 44 envelope-injection ablation

All, violated-only, and active-one policies use the same frozen frontier-d2 profiles; exact proof cost decides the ablation.

| variant | witness | certified | Work/P-GRB | time/P-GRB | splits | terminal MIPs |
|---|---|---:|---:|---:|---:|---:|
| na-frontier-all | major_fragmentation_regression | True | 0.8395 | 0.6546 | 0 | 3 |
| na-frontier-all | strongest_k4_positive_control | True | 0.0162 | 0.0158 | 0 | 4 |
| overlay-frontier-all-parent | major_fragmentation_regression | True | 2.4708 | 1.9067 | 1 | 4 |
| overlay-frontier-all-parent | strongest_k4_positive_control | True | 0.0164 | 0.0157 | 0 | 3 |
| overlay-frontier-all-nested | major_fragmentation_regression | True | 2.4722 | 1.9091 | 1 | 4 |
| overlay-frontier-all-nested | strongest_k4_positive_control | True | 0.0164 | 0.0157 | 0 | 3 |
| overlay-frontier-violated-parent | major_fragmentation_regression | True | 2.4708 | 2.0124 | 1 | 4 |
| overlay-frontier-violated-parent | strongest_k4_positive_control | True | 0.0137 | 0.0141 | 0 | 3 |
| overlay-frontier-active-parent | major_fragmentation_regression | True | 4.4603 | 3.3890 | 1 | 4 |
| overlay-frontier-active-parent | strongest_k4_positive_control | True | 0.0137 | 0.0133 | 0 | 3 |
