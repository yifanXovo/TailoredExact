# Cut Ablation Time-Profile Report

`results/gf_compact_bc_timeprofile_round/cut_ablation_timeprofile.csv` is a
targeted configuration contrast, not a complete one-family-at-a-time ablation.

The round compares:

- balanced dynamic-root rows;
- static no-dynamic-root recovery rows.

Key observation: high_imbalance_seed3202 certified in the 1200s static recovery
row, while the 300s dynamic-root row remained open. This does not invalidate the
dynamic root loop, but it shows that the current hard-leaf separators are not
yet the decisive strengthening mechanism.
