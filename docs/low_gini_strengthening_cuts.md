# Low-Gini Strengthening Cuts

This round adds four paper-safe low-Gini strengthening families for fixed original intervals.

## Subset Cross-H Centering

For a subset `A`, `R_A=sum_{i in A} r_i`, `S=sum_i r_i`, and `h_ij >= |r_i-r_j|`, the rows

`V R_A - |A| S <= sum_{i in A, j notin A} h_ij`

`|A| S - V R_A <= sum_{i in A, j notin A} h_ij`

are valid because the cross sum of pairwise absolute deviations dominates the signed deviation between subset average mass and global average mass. They are enabled by `--tailored-bc-subset-cross-h-centering` and bounded by max-size/max-cuts guards.

## Local q-Centering

When the low-Gini L1 auxiliary `q_i` is present and represents absolute deviation from the global mean, `V q_i <= sum_{j != i} h_ij` is a valid strengthening row. It is enabled by `--tailored-bc-local-q-centering` and requires `--tailored-bc-low-gini-l1-centering true`.

## Compatible-Source Transfer Cutset

For receiver set `D` and vehicle `k`, positive net delivery into `D` must be sourced by pickups outside `D` that can reach at least one receiver under a conservative depot-source-receiver-depot duration test. The row preserves internal transfers in `D` by using net delivery `sum_{j in D} d[k,j] - sum_{j in D} p[k,j]`.

## Required External Source

If final inventory lower bounds require net delivery `R_D` into `D`, then aggregate pickups outside `D` must be at least `R_D`, under the empty-start/no-depot-source convention. The family is disabled unless `--tailored-bc-required-external-source-cuts true` is supplied.
