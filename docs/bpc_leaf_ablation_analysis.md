# BPC Leaf Ablation Analysis

The BPC repair round compares each frozen target leaf under a sequence of
certificate-safe variants:

- long baseline;
- domain transfer emphasis;
- RMP seeding;
- cut separation;
- dominance v2;
- completion bounds;
- route-skeleton/loading-DP decomposition;
- all improvements combined.

Every row is still a BPC-core diagnostic unless exact pricing closure is
reported.  The ablation matrix is stored in
`results/bpc_core_repair_round/bpc_leaf_ablation_matrix.csv`.

The central questions are:

- does the variant reduce route labels or operation DP states;
- does it find negative columns earlier or prove no negative column;
- does it improve the RMP bound;
- does it reach branch nodes;
- does any leaf close with exact pricing.

Rows with `diagnostic-aggressive` dominance, if present, are excluded from
certificate claims.
