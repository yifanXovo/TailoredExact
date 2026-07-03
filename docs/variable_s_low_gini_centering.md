# Variable-S Low-Gini Centering

For fixed interval upper bound `gamma_U`, the row

`(V-1) (r_max - r_min) <= V gamma_U sum_i r_i`

is valid because `H >= (V-1)(r_max-r_min)` and every original solution in the interval satisfies `H <= V gamma_U S`. The row is linear since `gamma_U` is constant. It is paper-safe under the current ratio/Gini definition and is active in `--compact-bc-low-gini-strengthening safe`.
