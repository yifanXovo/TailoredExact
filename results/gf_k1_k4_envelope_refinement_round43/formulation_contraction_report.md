# Round 43 formulation-contraction report

All 12 mechanism-panel atlas rows were terminal-valid. The width measure is
the frozen sum of the normalized `G` interval width and every normalized
`G`-times-inventory-bit McCormick range width.

| depth | C range | D range | median tau | D CV | Spearman(D, old) |
|---:|---:|---:|---:|---:|---:|
| 1 | 0.5 to 0.5 | 0.112115 to 0.220282 | 0.519001 | 0.245946 | -0.40584 |
| 2 | 0.75 to 0.75 | 0.0821946 to 0.209814 | 0.747268 | 0.363591 | 0.0285714 |

`C_d` is constant within depth (`0.5` and `0.75`) and is rejected as a
secondary score. `D_d` is informative for both depths. Depth 2 is frozen as
the single Stage 2 primary because it has higher envelope capture while
retaining nontrivial cross-instance `D_d` variation. No runtime, Work, node,
memory, label, or historical winner entered this decision.
