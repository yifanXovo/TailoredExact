# Low-Gini Strengthening Cuts

Cut admissibility follows [Diagnostic vs Paper-Safe Cuts](diagnostic_vs_paper_safe_cuts.md). This document records low-Gini families that are paper-safe when their stated model variables and assumptions are present.

## Subset Cross-H Centering

For a subset `A`, `R_A=sum_{i in A} r_i`, `S=sum_i r_i`, and `h_ij >= |r_i-r_j|`, the rows

`V R_A - |A| S <= sum_{i in A, j notin A} h_ij`

`|A| S - V R_A <= sum_{i in A, j notin A} h_ij`

are valid because the cross sum of pairwise absolute deviations dominates the signed deviation between subset average mass and global average mass. The new `--tailored-bc-subset-cross-h-separation-profile` flag changes only which valid subset rows are tried first.

## Local q-Centering

When the low-Gini L1 auxiliary `q_i` is present and represents absolute deviation from the global mean, `V q_i <= sum_{j != i} h_ij` is a valid strengthening row. It requires `--tailored-bc-low-gini-l1-centering true`.

## Compatible-Source Transfer Cutset

For receiver set `D` and vehicle `k`, positive net delivery into `D` must be sourced by pickups outside `D` that can reach at least one receiver under a conservative depot-source-receiver-depot duration test. The row preserves internal transfers in `D` by using net delivery `sum_{j in D} d[k,j] - sum_{j in D} p[k,j]`.

## Required External Source

If final inventory lower bounds require net delivery `R_D` into `D`, then aggregate pickups outside `D` must be at least `R_D`, under the empty-start/no-depot-source convention.

## S-Bucket and Denominator Rows

S-bucket denominator rows are conditional valid inequalities. A child bucket row can be paper-safe for the fixed child model only when the bucket bounds are enforced as model rows. Parent closure requires the separate S-bucket ledger audit proving exact S-domain coverage and valid closure of every bucket.

Bucket-tight `S*P` McCormick envelopes are valid on the enforced bucket box `[S_L,S_U] x [P_L,P_U]`. Diagnostic S buckets and aggressive denominator experiments must not close parent paper-core intervals.
