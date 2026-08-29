# Active formulation families

The machine-readable source of truth is the Round 54
`active_family_manifest.csv`/`.json`, generated against
`paper-k1-am-sf`. The active set contains 17 families:

- interval Gini bounds and direct Gini cap/floor;
- interval-tight G-times-binary McCormick hull;
- final-inventory penalty and movement-reachability domains;
- inventory conservation and visit--inventory links;
- verified-incumbent objective row, objective lower estimator, and penalty
  lower-bound closure;
- W_SP McCormick rows and its paper-safe objective estimator;
- pair and triple support-duration covers;
- connectivity-flow extended formulation;
- iterative domain propagation and tight denominator bounds.

The representative D1 fixed-interval model contains 3,764 rows, 1,404 columns,
16,888 nonzeros, and zero exhaustive subset-duration rows. Some domain and
propagation counts are exposed as bound bundles rather than individual model
rows; the manifest states that limitation instead of inventing telemetry.

Inactive families include the exhaustive subset-duration block, Gini-spread,
required-movement, transfer-cutset, subset-inventory, dynamic support-duration,
all tailored dynamic user cuts, inventory--route root closure, custom branching
priorities, and symmetry research. No family is claimed novel without a
completed literature review; unverified candidates are explicitly marked
pending.
