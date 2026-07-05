# Low-Gini Strengthening Cuts

Implemented paper-safe local station centering rows:

`V r_i - S <= sum_{j != i} h_ij`

`S - V r_i <= sum_{j != i} h_ij`

Proof sketch: `sum_j |r_i-r_j|` is at least both `V r_i-S` and `S-V r_i`; each `h_ij` upper-bounds `|r_i-r_j|` in the compact model, so the two rows are valid relaxations for every original feasible route. They are exposed with `--tailored-bc-local-centering true` and logged as `local_centering` in static and callback cut counters.
